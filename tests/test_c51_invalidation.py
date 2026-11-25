"""Selected-timeframe invalidation and recovery; all OHLCV inputs are fictional."""
from copy import deepcopy
import json

import pytest

from app.services import production_message_renderer as renderer
from app.services.detailed_stock_message_v2 import _buyer_action
from app.services.ohlcv_structure_service import (
    StructureBar, calculate_invalidation,
)
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests import test_c50_chart_statement as complete_fixture
from tests.test_ohlcv_structure_service import _state


def bars(*pairs):
    return [StructureBar(index, day, close, close + 0.1, close - 0.1, close, 100)
            for index, (day, close) in enumerate(pairs)]


def invalidation(timeframe="daily", *, current=10, previous=10,
                 daily_date="2026-11-23", weekly_date="2026-11-16", weekly_close=7,
                 volume=1, supply="mixed"):
    return calculate_invalidation(
        dict(timeframe=timeframe, zone_low=9, zone_high=11), current_price=current,
        daily_atr=2, weekly_atr=2,
        daily_bars=bars(("2026-11-20", previous), (daily_date, current)),
        weekly_bars=bars((weekly_date, weekly_close)),
        volume_ratio=volume, supply_classification=supply)


@pytest.mark.parametrize("weekly_date", ["2026-11-16", "2026-11-20"])
def test_prior_weekly_comparison_does_not_veto_selected_daily_support(weekly_date):
    result = invalidation(weekly_date=weekly_date)
    assert result["price"] == 8
    assert result["status"] == "intact"
    assert result["hard_weekly"] is True and result["hard_daily"] is False
    assert result["current_recovery"] == "support_reclaimed"
    assert result["trigger_timeframe"] is None
    assert result["trigger_dates"] == []
    assert result["weekly_bar_date"] == weekly_date
    assert result["historical_break_evidence"] == "NOT_ESTABLISHED"
    assert result["evaluation_date"] == "2026-11-23"


@pytest.mark.parametrize("current,status,recovery", [
    (10, "recovered_review", "support_reclaimed"),
    (8.5, "recovered_review", "invalidation_reclaimed"),
    (7, "hard_invalid", "not_reclaimed"),
])
def test_weekly_break_current_recovery_is_separate_from_weekly_confirmation(current, status, recovery):
    result = invalidation("weekly", current=current)
    assert result["status"] == status
    assert result["current_recovery"] == recovery
    assert result["trigger_timeframe"] == "weekly"
    assert result["hard_weekly"] is True


def test_later_day_in_week_label_period_is_not_post_week_recovery():
    result = invalidation("weekly", daily_date="2026-11-20", weekly_date="2026-11-16")
    assert result["status"] == "hard_invalid"
    assert result["current_recovery"] == "not_reclaimed"


def test_weekly_recovery_compares_week_year_at_year_boundary():
    result = invalidation("weekly", daily_date="2027-01-04", weekly_date="2026-12-28")
    assert result["status"] == "recovered_review"


def test_daily_break_on_weekly_support_remains_early_warning():
    result = invalidation("weekly", current=7, previous=7, weekly_close=10)
    assert result["status"] == "lower_timeframe_review"
    assert result["hard_weekly"] is False and result["hard_daily"] is True
    assert result["trigger_timeframe"] == "daily"
    assert result["trigger_dates"] == ["2026-11-20", "2026-11-23"]


@pytest.mark.parametrize("volume,supply,status,dates", [
    (1, "mixed", "hard_invalid", ["2026-11-20", "2026-11-23"]),
    (1.3, "distribution", "accelerated_invalid", ["2026-11-23"]),
])
def test_active_daily_invalidation_keeps_existing_thresholds(volume, supply, status, dates):
    result = invalidation(current=7, previous=7, volume=volume, supply=supply)
    assert result["status"] == status
    assert result["price"] == 8 and result["buffer"] == 1
    assert result["trigger_timeframe"] == "daily" and result["trigger_dates"] == dates


def test_monthly_support_is_not_given_an_undefined_daily_or_weekly_invalidation():
    result = invalidation("monthly", current=7, previous=7)
    assert result == dict(available=False, reason="monthly_invalidation_contract_undefined",
                          timeframe="monthly", nearest_support_preserved=True)


@pytest.mark.parametrize("status", ["higher_timeframe_review", "lower_timeframe_review", "recovered_review"])
def test_warning_state_cannot_be_promoted_by_positive_structure(status):
    result = _state(invalidation=dict(available=True, status=status, price=8))
    assert result["state"] == "WAIT" and result["reasons"] == [status]
    assert result["user_semantics"] == "price_structure_wait_not_sell_command"


@pytest.mark.parametrize("relation,quality", [("BELOW", "CAUTION"), ("INSIDE", "BLOCKED")])
def test_business_wait_reason_survives_structural_action(relation, quality):
    assert _buyer_action("WAIT", relation, quality, reason_class="VALUATION_UNRESOLVED") == (
        "가치평가 자료 확인 대기 · 지지 이탈 구조 재검토")
    assert _buyer_action("AVOID", relation, quality, reason_class="ACTIVE_ADVERSE_UNCOMPENSATED") == "신규 매수 회피"


@pytest.mark.parametrize("market", ["kr", "us"])
@pytest.mark.parametrize("timeframe", ["daily", "weekly"])
def test_real_fact_statement_b2_and_renderer_keep_warning_without_false_current_invalidation(monkeypatch, market, timeframe):
    chart = complete_fixture.chart_input(timeframe)
    # The fixture chart producer labels its completed week by Friday, while the
    # unit cases also cover a provider labelling the same period by Monday.
    chart["timeframes"]["weekly"]["candle"]["close"] = 7
    chart["structure"]["invalidation"] = invalidation(timeframe, weekly_date="2026-11-20")
    monkeypatch.setattr(complete_fixture, "chart_input", lambda _: deepcopy(chart))
    case = complete_fixture.produced_case(market, timeframe)
    session, ticker, source, stock, packet, _ = case
    context, entries, _ = complete_fixture.bound_b_input(case)
    ref = "canonical:chart:structure:invalidation"
    row = next(row for row in context["decision_evidence"] if row["ref_id"] == ref)
    fact = next(row for row in stock["fact_catalog"] if row["fact_id"] == "chart:structure:invalidation")
    assert json.loads(row["statement"]) == fact["fields"]
    assert fact["fields"]["hard_weekly"] is True
    assert fact["fields"]["evaluation_date"] == "2026-11-23"
    assert fact["fields"]["trigger_dates"] == ([] if timeframe == "daily" else ["2026-11-20"])
    accepted, b2_row, request = complete_fixture.renderer_case(case, context, entries["tactical_candidates"][0])
    before = deepcopy((source, context, b2_row, request))
    monkeypatch.setattr(renderer, "stock_plan", lambda *args: accepted)
    message = renderer.stock_message(session, ticker, b2_row, execution_profile=SOL_HIGH_V1)
    text = message["text"]
    assert "지지 구간 안" in text
    assert "완료 주봉(기준일 2026-11-20)" in text
    assert "하단 회복" not in text and "이탈 후" not in text
    if timeframe == "daily":
        assert "최종 신규매수 행동: 신규 매수 검토 가능" in text
        assert "과거 지지 이탈 여부 미확인" in text
    else:
        assert "최종 신규매수 행동: 다음 완료 주봉 종가가 선택 지지 무효화선 이상인지 확인 대기" in text
        assert "신규 매수 검토 가능" not in text
    assert "차트 무효화 조건 충족" not in text
    assert message["NO_SEND"] is True
    assert (source, context, b2_row, request) == before
