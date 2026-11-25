"""Current support comparisons are not evidence of a historical break."""
from copy import deepcopy
import json
import socket

import pytest

from app.services.ohlcv_structure_service import (
    StructureBar, calculate_invalidation, determine_chart_state,
)
from tests import test_c50_chart_statement as complete_fixture


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("C54_STRUCTURE_EXTERNAL_IO_DENIED")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def bars(*pairs):
    return [StructureBar(index, day, close, close + 0.1, close - 0.1, close, 100)
            for index, (day, close) in enumerate(pairs)]


def assessment(timeframe="daily", *, current=10, previous=10, weekly_close=7,
               weekly_date="2026-11-16", volume=1, supply="mixed", daily=None):
    return calculate_invalidation(
        dict(timeframe=timeframe, zone_low=9, zone_high=11), current_price=current,
        daily_atr=2, weekly_atr=2,
        daily_bars=daily if daily is not None else bars(("2026-11-20", previous), ("2026-11-23", current)),
        weekly_bars=bars((weekly_date, weekly_close)),
        volume_ratio=volume, supply_classification=supply)


@pytest.mark.parametrize("weekly_date", ["2026-11-16", "2026-11-20"])
def test_older_weekly_close_is_context_for_current_daily_support(weekly_date):
    result = assessment(weekly_date=weekly_date)
    assert result["price"] == 8 and result["buffer"] == 1
    assert result["status"] == "intact"
    assert result["hard_weekly"] is True and result["hard_daily"] is False
    assert result["weekly_close"] == 7 and result["latest_daily_close"] == 10
    assert result["weekly_bar_date"] == weekly_date
    assert result["comparison_basis"] == "CURRENT_SELECTED_SUPPORT"
    assert result["historical_break_evidence"] == "NOT_ESTABLISHED"
    assert result["trigger_timeframe"] is None and result["trigger_dates"] == []


@pytest.mark.parametrize("weekly_close", [7, 10])
def test_selected_daily_two_close_condition_still_invalidates(weekly_close):
    result = assessment(current=7, previous=7, weekly_close=weekly_close)
    assert result["status"] == "hard_invalid"
    assert result["trigger_timeframe"] == "daily"
    assert result["trigger_dates"] == ["2026-11-20", "2026-11-23"]
    assert result["price"] == 8


def test_selected_daily_accelerated_condition_keeps_its_actual_trigger():
    result = assessment(current=7, previous=10, volume=1.3, supply="distribution")
    assert result["status"] == "accelerated_invalid"
    assert result["hard_daily"] is False and result["accelerated"] is True
    assert result["trigger_timeframe"] == "daily"
    assert result["trigger_dates"] == ["2026-11-23"]


def test_daily_wick_warning_is_not_hidden_by_old_weekly_comparison():
    daily = bars(("2026-11-20", 10)) + [StructureBar(1, "2026-11-23", 10, 11, 7, 10, 100)]
    result = assessment(daily=daily)
    assert result["hard_weekly"] is True
    assert result["status"] == "wick_only_review"
    assert result["trigger_timeframe"] == "daily"
    assert result["trigger_dates"] == ["2026-11-23"]


@pytest.mark.parametrize("current,expected", [(10, "recovered_review"), (8.5, "recovered_review"), (7, "hard_invalid")])
def test_selected_weekly_condition_keeps_weekly_confirmation_requirement(current, expected):
    result = assessment("weekly", current=current)
    assert result["status"] == expected
    assert result["trigger_timeframe"] == "weekly"
    assert result["trigger_dates"] == ["2026-11-16"]
    assert result["historical_break_evidence"] == "NOT_ESTABLISHED"


def test_old_weekly_comparison_does_not_override_supported_daily_setup():
    result = determine_chart_state(
        current_price=10,
        classified_zones={"active": [dict(pivot_type="low", strength="Medium", zone_low=9, zone_high=11)],
                          "support": [], "resistance": []},
        all_zones=[], invalidation=assessment(),
        risk_reward={"available": True, "current_price": {"ratio": 2}, "support_entry": {"ratio": 2}},
        daily_bars=bars(("2026-11-20", 10), ("2026-11-23", 10)),
        volume_ratio=1, upper_wick_pct=10, close_location_pct=80,
        supply={"classification": "mixed"}, bollinger_values={}, fibonacci_sets={}, major_swing_count=3,
    )
    assert result["state"] == "SUPPORT_ENTRY"
    assert result["user_semantics"] == "support_scenario_not_order"


@pytest.mark.parametrize("market", ["kr", "us"])
def test_comparison_semantics_survive_real_fact_and_b_input_projection(monkeypatch, market):
    chart = complete_fixture.chart_input("daily")
    chart["timeframes"]["weekly"]["candle"]["close"] = 7
    chart["structure"]["invalidation"] = assessment(weekly_date="2026-11-20")
    monkeypatch.setattr(complete_fixture, "chart_input", lambda _: deepcopy(chart))
    case = complete_fixture.produced_case(market, "daily")
    _, _, _, stock, _, _ = case
    context, _, _ = complete_fixture.bound_b_input(case)
    fact = next(row for row in stock["fact_catalog"] if row["fact_id"] == "chart:structure:invalidation")
    evidence = next(row for row in context["decision_evidence"]
                    if row["ref_id"] == "canonical:chart:structure:invalidation")
    assert json.loads(evidence["statement"]) == fact["fields"]
    assert fact["fields"]["comparison_basis"] == "CURRENT_SELECTED_SUPPORT"
    assert fact["fields"]["historical_break_evidence"] == "NOT_ESTABLISHED"
    assert fact["fields"]["weekly_close"] == 7
    assert fact["fields"]["latest_daily_close"] == 10
    assert fact["fields"]["status"] == "intact"
