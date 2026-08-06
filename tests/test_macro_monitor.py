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
from app.macro.service import run_macro_monitor
from app.main import app
from app.models.macro import MacroBriefing, MacroShockAssessment, ThesisMacroImpact
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
        assert len(delivery_payload["messages"]) == 3
        assert delivery_payload["messages"][0]["title"] == "[시장환경 점검] 주요 시장"
        assert delivery_payload["messages"][1]["title"].startswith(
            "[시장환경 점검] 레짐"
        )
        assert delivery_payload["messages"][2]["title"] == "[시장환경 점검] 투자 해석"

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
