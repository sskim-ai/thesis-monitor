import json
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine, init_db
from app.macro.providers.base import (
    CollectedObservation,
    MacroProviderResult,
)
from app.macro.impact import assess_thesis_macro_impacts
from app.macro.service import run_macro_monitor
from app.main import app
from app.models.macro import (
    MacroBriefing,
    MacroObservation,
    MacroShockAssessment,
    ThesisMacroImpact,
)
from app.models.thesis import NotificationDelivery
from app.schemas.thesis import MacroExposureInput, MonitoringItemCreate
from app.services.monitoring_service import register_monitoring_item


class FakeMacroProvider:
    name = "fake_macro"

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        def observation(
            series_code: str,
            value: float,
            day: int,
            category: str = "market_index",
        ) -> CollectedObservation:
            return CollectedObservation(
                series_code=series_code,
                category=category,
                observed_at=datetime(2031, 3, day, tzinfo=timezone.utc),
                value=value,
                unit="index",
                frequency="daily",
                source_url=f"https://example.com/{series_code}",
            )

        return MacroProviderResult(
            provider=self.name,
            observations=[
                observation("SPY", 500, 4),
                observation("SPY", 505, 5),
                observation("QQQ", 440, 4),
                observation("QQQ", 446, 5),
                observation("IWM", 200, 4),
                observation("IWM", 202, 5),
                observation("SOXX", 600, 4, "sector"),
                observation("SOXX", 615, 5, "sector"),
                observation("VIXCLS", 15, 4, "volatility"),
                observation("VIXCLS", 14, 5, "volatility"),
                observation("DCOILWTICO", 70, 4, "commodities"),
                observation("DCOILWTICO", 75, 5, "commodities"),
            ],
        )


class RecoveringMacroProvider:
    name = "recovering_macro"

    def __init__(self) -> None:
        self.calls = 0

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        self.calls += 1
        return MacroProviderResult(
            provider=self.name,
            warnings=["temporary network error"] if self.calls == 1 else [],
        )


@pytest.mark.anyio
async def test_macro_monitor_builds_briefing_impacts_and_dedupes() -> None:
    init_db()
    run_date = date(2031, 3, 5)
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="MCR2031",
                company_name="Macro Test Airline",
                core_thesis="항공 여객 수요와 운임 개선이 이익을 지지한다.",
                weaken_signals=["유가 급등", "원화 약세"],
                invalidation_signals=["구조적 수요 붕괴"],
                macro_exposures=[
                    MacroExposureInput(
                        factor="wti",
                        direction="negative",
                        weight=4,
                        channel="cost",
                        condition="Jet fuel cost is a material share of operating expenses",
                    )
                ],
            ),
        )
        result = await run_macro_monitor(
            session,
            run_date=run_date,
            force=True,
            providers=[FakeMacroProvider()],
            as_of=datetime(2031, 3, 5, 23, tzinfo=timezone.utc),
            dispatch_notifications=False,
        )

        assert result.status == "ready"
        assert result.briefing is not None
        assert result.briefing.kakao_text.startswith("[시장환경 점검]")
        assert result.briefing.regime_summary["growth_momentum"] is not None
        assert result.briefing.regime_summary["earnings_momentum"] is not None
        soft_landing = next(
            item
            for item in result.briefing.macro_theses
            if item["thesis_key"] == "us_soft_landing_disinflation"
        )
        assert "daily_signal" in soft_landing
        assert "발생 확률이 아님" in soft_landing["confidence_meaning"]
        assert result.observation_count == 12
        assert result.impact_count >= 1
        impact = session.exec(
            select(ThesisMacroImpact).where(
                ThesisMacroImpact.ticker == "MCR2031",
                ThesisMacroImpact.assessment_date == run_date,
            )
        ).one()
        assert impact.direction == "weaken"
        assert impact.magnitude >= 3
        shock = session.exec(
            select(MacroShockAssessment).where(
                MacroShockAssessment.assessment_date == run_date,
                MacroShockAssessment.shock_type == "supply_inflation:DCOILWTICO",
            )
        ).one()
        assert shock.magnitude >= 3
        delivery = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker == "__MACRO__",
                NotificationDelivery.assessment_date == run_date,
            )
        ).one()
        assert delivery.status == "pending"
        delivery_payload = json.loads(delivery.payload)
        assert delivery_payload["presentation"] == "long_text"
        assert delivery_payload["analysis_context"]["analysis_type"] == "macro"
        assert "🎯 오늘 한 줄" in delivery_payload["text"]
        assert "📈 오늘 가장 중요한 변화" in delivery_payload["text"]
        assert "🧭 현재 시장 상황" in delivery_payload["text"]
        assert "🏢 주요 종목 전달 경로" in delivery_payload["text"]
        assert "6축 점수" not in delivery_payload["text"]

        rerun = await run_macro_monitor(
            session,
            run_date=run_date,
            providers=[FakeMacroProvider()],
            dispatch_notifications=False,
        )
        assert rerun.status == "already_completed"
        assert len(
            session.exec(
                select(MacroBriefing).where(MacroBriefing.briefing_date == run_date)
            ).all()
        ) == 1


@pytest.mark.anyio
async def test_partial_macro_run_is_retried_until_ready() -> None:
    init_db()
    provider = RecoveringMacroProvider()
    run_date = date(2031, 3, 6)
    with Session(engine) as session:
        first = await run_macro_monitor(
            session,
            run_date=run_date,
            providers=[provider],
            dispatch_notifications=False,
        )
        second = await run_macro_monitor(
            session,
            run_date=run_date,
            providers=[provider],
            dispatch_notifications=False,
        )

    assert first.status == "partial"
    assert second.status == "ready"
    assert provider.calls == 2


def test_macro_action_routes_require_auth_and_return_latest_briefing() -> None:
    with TestClient(app) as client:
        assert client.get("/macro/provider-status").status_code == 401
        response = client.get(
            "/macro/provider-status",
            headers={"X-Action-API-Key": "test-action-key"},
        )
        assert response.status_code == 200
        assert {item["name"] for item in response.json()} >= {
            "fred",
            "eia",
            "ecos",
            "ohlcv_analyst",
        }

        briefing = client.get(
            "/macro/briefings/latest",
            headers={"X-Action-API-Key": "test-action-key"},
        )
        assert briefing.status_code == 200
        assert briefing.json()["briefing_type"] == "morning"


def test_macro_impacts_separate_overall_and_valuation_channels() -> None:
    init_db()
    run_date = date(2048, 1, 5)
    with Session(engine) as session:
        for ticker, exposures in [
            (
                "CHANNEL2048",
                [
                    MacroExposureInput(
                        factor="market_volatility",
                        direction="negative",
                        weight=4,
                        channel="liquidity",
                    ),
                    MacroExposureInput(
                        factor="us_10y_real_yield",
                        direction="negative",
                        weight=4,
                        channel="discount_rate",
                    ),
                ],
            ),
            (
                "LOWWEIGHT2048",
                [
                    MacroExposureInput(
                        factor="us_10y_real_yield",
                        direction="negative",
                        weight=2,
                        channel="discount_rate",
                    )
                ],
            ),
        ]:
            register_monitoring_item(
                session,
                MonitoringItemCreate(
                    ticker=ticker,
                    company_name=ticker,
                    core_thesis="Structured macro channel test",
                    macro_exposures=exposures,
                ),
            )
        session.add_all(
            [
                MacroObservation(
                    dedupe_key="vix-channel-2048",
                    series_code="VIXCLS",
                    category="volatility",
                    provider="test",
                    observed_at=datetime(2048, 1, 5, tzinfo=timezone.utc),
                    value=14,
                    previous_value=16,
                    change_value=-2,
                    change_pct=-12.5,
                    source_url="https://example.com/vix",
                ),
                MacroObservation(
                    dedupe_key="real-yield-channel-2048",
                    series_code="DFII10",
                    category="real_rates",
                    provider="test",
                    observed_at=datetime(2048, 1, 5, tzinfo=timezone.utc),
                    value=2.5,
                    previous_value=2.44,
                    change_value=0.06,
                    change_pct=2.46,
                    source_url="https://example.com/real-yield",
                ),
            ]
        )
        session.commit()

        impacts = assess_thesis_macro_impacts(session, run_date)
        by_ticker = {item.ticker: item for item in impacts}

        assert by_ticker["CHANNEL2048"].direction == "strengthen"
        assert by_ticker["CHANNEL2048"].valuation_effect == "mixed"
        assert by_ticker["CHANNEL2048"].earnings_effect == "neutral"
        channel_evidence = json.loads(by_ticker["CHANNEL2048"].evidence)
        assert any(
            item["exposure"]["channel"] == "risk_appetite"
            for item in channel_evidence
            if item.get("factor") == "market_volatility"
        )
        assert by_ticker["LOWWEIGHT2048"].direction == "neutral"
        assert by_ticker["LOWWEIGHT2048"].valuation_effect == "neutral"
        assert "저가중치" in by_ticker["LOWWEIGHT2048"].rationale
