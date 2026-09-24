from datetime import date, datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import exchange_calendars
import httpx
import pytest

from app.jobs import monitor_daily
from app.services.market_session import korea_market_session
from app.services.ohlcv_client import OhlcvClient


KST = ZoneInfo("Asia/Seoul")
HOLIDAY = date(2026, 9, 24)


@pytest.mark.parametrize("day", [24, 25, 26, 27])
def test_chuseok_and_adjacent_weekend_are_calendar_closed(day):
    at = datetime(2026, 9, day, 16, 5, tzinfo=KST)
    calendar = exchange_calendars.get_calendar("XKRX")
    state = korea_market_session(at)
    assert not calendar.is_session(at.date())
    assert state.session == "closed"
    assert state.latest_completed_regular_session_date == date(2026, 9, 23)
    assert calendar.date_to_session(at.date(), direction="next").date() == date(2026, 9, 28)


@pytest.mark.anyio
@pytest.mark.parametrize("hour", [8, 11, 16, 17, 23])
async def test_holiday_kr_gate_precedes_all_stateful_and_paid_work(monkeypatch, hour):
    session = Mock()
    blocked = []
    for name in (
        "_analysis_decision", "market_preflight_onboarding_resume",
        "run_kr_close_market_briefing", "run_daily_monitor", "run_macro_monitor",
        "collect_and_persist_kiwoom_market_context", "try_write_ai_review_packet",
        "queue_daily_monitor_notifications", "hold_ai_assisted_pilot_session",
    ):
        guard = Mock(side_effect=AssertionError("holiday downstream work: " + name))
        monkeypatch.setattr(monitor_daily, name, guard)
        blocked.append(guard)
    output = await monitor_daily._run_market_job(
        session, HOLIDAY, "kr", as_of=datetime(2026, 9, 24, hour, 5, tzinfo=KST)
    )
    assert output["analysis_action"] == output["delivery_action"] == "safe_noop"
    assert output["skip_reason"] == "no_valid_role_target"
    assert output["producer_role_target"]["production_eligible"] is False
    assert all(guard.call_count == 0 for guard in blocked)
    assert session.mock_calls == []


@pytest.mark.anyio
@pytest.mark.parametrize("scope,day", [("all", 24), ("us", 24), ("kr", 23), ("all", 23)])
async def test_whole_system_holiday_skips_kr_but_keeps_us_eligible(monkeypatch, scope, day):
    reached = []

    class ReachedEligibleBranch(Exception):
        pass

    def probe(session, run_date, cutoff, market_scope):
        reached.append(market_scope)
        raise ReachedEligibleBranch

    monkeypatch.setattr(monitor_daily, "_analysis_decision", probe)
    with pytest.raises(ReachedEligibleBranch):
        await monitor_daily._run_market_job(
            Mock(), date(2026, 9, day), scope,
            as_of=datetime(2026, 9, day, 16, 5, tzinfo=KST),
        )
    assert reached == ["us" if scope == "all" and day == 24 else scope]


@pytest.mark.anyio
async def test_holiday_previous_session_prices_keep_dates_and_adjustment():
    requests = []

    def handler(request):
        period = request.url.params["periods"]
        adjusted = request.url.params["adjusted"] == "true"
        requests.append((period, adjusted))
        bars = [dict(date="2026-09-23", open=100, high=102, low=99,
                     close=101 if adjusted else 102, volume=1000)]
        return httpx.Response(200, json={"periods": {period: bars}, "meta": {"adjusted": adjusted}})

    context = await OhlcvClient(transport=httpx.MockTransport(handler)).fetch_price_context(
        "005930", as_of=datetime(2026, 9, 24, 11, 0, tzinfo=KST)
    )
    assert context.decision.market_session == "closed"
    assert context.decision.price_basis == "close"
    assert context.chart.price_basis == "adjusted_close"
    assert context.decision.price_as_of == "2026-09-23"
    assert context.decision.latest_completed_regular_session_date == "2026-09-23"
    assert context.decision.current_price == 101
    assert context.valuation_history[0].close == 102
    assert all(point.date == date(2026, 9, 23) for point in context.daily_history)
    assert ("weekly", False) in requests


@pytest.mark.anyio
async def test_all_run_reports_kr_noop_without_retry_or_us_suppression(monkeypatch):
    original = monitor_daily._run_market_job
    calls = []
    session = Mock()

    async def branch(session, run_date, scope, *, as_of):
        calls.append(scope)
        if scope == "kr":
            return await original(session, run_date, scope, as_of=as_of)
        assert scope == "us"
        return {"market_scope": "us", "analysis_action": "eligible_us_test_sentinel"}

    monkeypatch.setattr(monitor_daily, "_run_market_job", branch)
    result = await original(session, HOLIDAY, "all", as_of=datetime(2026, 9, 24, 16, 5, tzinfo=KST))
    assert calls == ["kr", "us"]
    assert result["markets"]["kr"]["delivery_action"] == "safe_noop"
    assert result["markets"]["kr"]["analysis_run_status"] == "not_started"
    assert result["markets"]["us"]["analysis_action"] == "eligible_us_test_sentinel"
    assert session.mock_calls == []


@pytest.mark.anyio
async def test_source_proof_gate_has_no_generation_or_persistence_calls():
    from scripts.kr_holiday_source_proof import calendar_receipt, suppression_receipt

    at = datetime(2026, 9, 24, 16, 5, tzinfo=KST)
    calendar = calendar_receipt(at)
    result = await suppression_receipt(at, ["005930", "000660"])
    assert calendar["weekday_fallback_used"] is False
    assert calendar["active_session"] is False
    assert result["model_calls"] == result["persistence_calls"] == result["send_calls"] == 0
    assert len(result["stocks"]) == 2
    assert all(not row["eligible"] for row in result["stocks"])


@pytest.mark.anyio
async def test_readonly_observer_rejects_account_or_order_endpoints(tmp_path):
    from scripts.kr_holiday_source_proof import ReadOnlyTransport

    transport = ReadOnlyTransport(tmp_path)
    try:
        with pytest.raises(ValueError, match="allowlist"):
            await transport.handle_async_request(httpx.Request("POST", "https://api.kiwoom.com/api/dostk/ordr"))
        assert transport.rows == []
        assert transport.auth_calls == 0
    finally:
        await transport.aclose()


def test_holiday_descendant_requires_exact_reviewed_bytes_and_ancestry(monkeypatch):
    from pathlib import Path
    from scripts import approved_scope_descendants as provenance

    receipt = provenance.approved_descendant(provenance.KR_HOLIDAY_PATH)
    assert receipt and receipt["exact_blob_verified"]
    assert receipt["sha256"] == provenance.KR_HOLIDAY_AFTER
    observed = Path(provenance.KR_HOLIDAY_PATH).read_bytes()
    assert provenance._kr_holiday_approval(observed + b"\n") is None
    monkeypatch.setattr(provenance, "_ancestor", lambda commit: False)
    assert provenance._kr_holiday_approval(observed) is None
