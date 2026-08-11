import json
from datetime import date, datetime, timezone

import httpx
import pytest
from sqlmodel import Session, select

from app.database import engine, init_db
from app.macro.impact import migrate_macro_exposure_channels
from app.macro.regime import assess_macro_regime
from app.macro.theses import update_macro_theses
from app.models.macro import MacroThesis
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.schemas.thesis import PriceContext, PricePeriodSummary, PriceRulesInput
from app.services.ohlcv_client import OhlcvClient
from app.services.thesis_evaluation_service import evaluate_thesis
from app.services.valuation_snapshot_service import ValuationSnapshotService


def _base_thesis(ticker: str = "ACCURACY") -> InvestmentThesis:
    return InvestmentThesis(
        ticker=ticker,
        version=1,
        core_thesis="새로운 실적과 현금흐름 근거가 기업가치를 결정한다.",
        valuation_framework=json.dumps({"primary_method": "forward P/E"}),
        market_expectations=json.dumps({"level": "balanced"}),
    )


def _previous(**updates: object) -> ThesisAssessment:
    values: dict[str, object] = {
        "ticker": "ACCURACY",
        "thesis_version": 1,
        "assessment_date": date(2055, 1, 1),
        "status": "no_material_change",
        "business_thesis_change": "no_material_change",
        "valuation_change": "neutral",
        "summary": "previous",
        "new_buyer_view": "previous",
        "holder_view": "previous",
        "price_view": "previous",
        "risk_level": "normal",
        "confidence": 0.8,
    }
    values.update(updates)
    return ThesisAssessment(**values)


def test_configured_valuation_signals_do_not_trigger_without_new_match() -> None:
    thesis = _base_thesis()
    thesis.multiple_expansion_signals = json.dumps(["new customer order"])
    thesis.multiple_compression_signals = json.dumps(["margin deterioration"])

    result = evaluate_thesis(thesis, [], PriceContext())

    assert result.valuation_context.impact == "neutral"
    assert result.valuation_context.configured_expansion_signals == ["new customer order"]
    assert result.valuation_context.matched_expansion_signals == []
    assert result.valuation_context.matched_compression_signals == []


def test_speculative_expectation_preserves_elevated_structural_risk_without_new_event() -> None:
    thesis = _base_thesis("TSLA")
    thesis.core_thesis = "현재 자동차 마진 저하와 FCF 적자가 이어지고 Robotaxi 경제성은 미증명 상태다."
    thesis.market_expectations = json.dumps({"level": "speculative"})
    thesis.valuation_framework = json.dumps(
        {"primary_method": "scenario", "valuation_caveats": ["Robotaxi 단위경제성 미증명"]}
    )

    result = evaluate_thesis(thesis, [], PriceContext())

    assert result.status == "no_material_change"
    assert result.structural_risk_level == "elevated"
    assert result.daily_change_severity == "none"
    assert result.new_warnings == []
    assert result.open_warnings == []
    assert any("미증명" in item for item in result.persistent_watch_risks)


def test_open_warning_remains_without_explicit_resolution() -> None:
    previous = _previous(
        open_warnings=json.dumps(["FCF 흑자 전환 미확인"]),
        warning_states=json.dumps(
            [{"warning": "FCF 흑자 전환 미확인", "status": "open"}]
        ),
    )

    result = evaluate_thesis(
        _base_thesis(),
        [],
        PriceContext(),
        previous_assessment=previous,
    )

    assert result.new_warnings == []
    assert result.open_warnings == ["FCF 흑자 전환 미확인"]
    assert result.warning_states[0]["status"] == "open"


def test_registered_price_rules_create_separate_observer_and_holder_checks() -> None:
    thesis = _base_thesis()
    thesis.price_rules = PriceRulesInput(
        currency="USD",
        confirmation_price=110,
        support_zone_low=95,
        support_zone_high=100,
        warning_price=90,
        invalidation_price=80,
    ).model_dump_json(exclude_none=True)
    context = PriceContext(
        available=True,
        periods={
            "daily": PricePeriodSummary(
                requested_count=500,
                actual_count=500,
                latest_date="2055-01-02",
                previous_close=101,
                latest_close=98,
                latest_low=97,
                range_position_pct=40,
            )
        },
    )

    result = evaluate_thesis(thesis, [], context)

    assert "$95~$100" in result.new_buyer_price_view
    assert "110" in result.new_buyer_price_view
    assert "90" in result.holder_price_view
    assert "80" in result.holder_price_view
    assert context.decision.registered_rules_available is True


def test_missing_price_rules_never_invent_price_levels() -> None:
    context = PriceContext(
        available=True,
        periods={
            "daily": PricePeriodSummary(
                requested_count=500,
                actual_count=50,
                latest_date="2055-01-02",
                latest_close=42,
            )
        },
    )

    result = evaluate_thesis(_base_thesis(), [], context)

    assert result.new_buyer_price_view == (
        "등록된 구조적 확인 가격이 없습니다. 투자 논리 조건과 실적 데이터를 우선 확인합니다."
    )
    assert context.decision.new_observer_checks == []
    assert context.decision.holder_checks == []


@pytest.mark.anyio
async def test_intraday_daily_bar_is_marked_provisional() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "periods": {
                    "daily": [
                        {"date": "2026-08-10", "close": 100, "high": 102, "low": 98}
                    ]
                }
            },
        )

    client = OhlcvClient(transport=httpx.MockTransport(handler))
    client.settings = client.settings.model_copy(update={"monitor_retry_attempts": 1})

    context = await client.fetch_price_context(
        "TSLA",
        as_of=datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc),
    )

    assert context.decision.market_session == "open"
    assert context.decision.assessment_state == "provisional"
    assert context.decision.price_basis == "intraday"


@pytest.mark.anyio
async def test_missing_and_negative_earnings_multiples_are_not_invented() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/stock/metric"
        return httpx.Response(
            200,
            json={
                "metric": {
                    "epsTTM": -1.2,
                    "peTTM": None,
                    "forwardPE": None,
                    "pbQuarterly": 2.1,
                }
            },
        )

    service = ValuationSnapshotService(transport=httpx.MockTransport(handler))
    service.settings = service.settings.model_copy(update={"finnhub_api_key": "test"})
    context = PriceContext(
        available=True,
        periods={
            "daily": PricePeriodSummary(
                requested_count=500,
                actual_count=500,
                latest_date="2055-01-02",
                latest_close=10,
            )
        },
    )

    snapshot = await service.fetch("RXRX", "NASDAQ", context)

    assert snapshot.trailing_pe is None
    assert snapshot.trailing_pe_status == "not_meaningful"
    assert snapshot.forward_pe is None
    assert snapshot.forward_pe_status == "unavailable"
    assert snapshot.quality == "partial"
    assert any("기준일" in warning for warning in snapshot.warnings)


@pytest.mark.anyio
async def test_stale_forward_multiple_is_flagged() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "metricAsOf": "2054-10-01",
                "metric": {"epsTTM": 2.0, "peTTM": 20.0, "forwardPE": 18.0},
            },
        )

    service = ValuationSnapshotService(transport=httpx.MockTransport(handler))
    service.settings = service.settings.model_copy(
        update={"finnhub_api_key": "test", "valuation_snapshot_max_age_days": 7}
    )

    snapshot = await service.fetch(
        "IBM",
        "NYSE",
        PriceContext(),
        as_of=datetime(2055, 1, 2, tzinfo=timezone.utc),
    )

    assert snapshot.forward_pe == 18.0
    assert snapshot.quality == "stale"
    assert any("오래" in warning for warning in snapshot.warnings)


def test_single_day_soxx_signal_does_not_change_ai_capex_persistent_state() -> None:
    init_db()
    run_date = date(2055, 2, 1)
    with Session(engine) as session:
        thesis = session.exec(
            select(MacroThesis)
            .where(MacroThesis.thesis_key == "ai_capex_cycle")
            .order_by(MacroThesis.version.desc())
        ).first()
        if thesis is not None:
            thesis.status = "intact"
            session.add(thesis)
            session.commit()
        regime = assess_macro_regime(
            session,
            run_date,
            as_of=datetime(2055, 2, 1, 22, 0, tzinfo=timezone.utc),
        )
        regime.earnings_momentum = -1
        regime.persistence_days = 1
        regime.provisional = False
        session.add(regime)
        session.commit()

        updated = update_macro_theses(session, regime)
        ai = next(item for item in updated if item.thesis_key == "ai_capex_cycle")

        assert ai.status == "intact"
        assert ai.today_signal == "negative"
        assert "실제 CAPEX" in ai.today_signal_rationale


def test_macro_exposure_channel_migration_keeps_thesis_version() -> None:
    init_db()
    with Session(engine) as session:
        thesis = session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == "MIGRATION",
                InvestmentThesis.version == 7,
            )
        ).first() or InvestmentThesis(
            ticker="MIGRATION", version=7, core_thesis="migration test"
        )
        thesis.macro_exposures = json.dumps(
            [
                {
                    "factor": "market_volatility",
                    "direction": "negative",
                    "weight": 3,
                    "channel": "liquidity",
                }
            ]
        )
        session.add(thesis)
        session.commit()

        result = migrate_macro_exposure_channels(session)
        session.refresh(thesis)

        assert result["exposures"] >= 1
        assert thesis.version == 7
        assert json.loads(thesis.macro_exposures)[0]["channel"] == "risk_appetite"
