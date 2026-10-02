from copy import deepcopy
from datetime import date, timedelta

import pytest

from app.services import ohlcv_structure_service as structure
from app.services.ohlcv_feature_engine_service import _feature_facts, _normalize_bars
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_stock_anomaly_scope import (
    ConsumerRows, assess_consumer, materialize_source_components, role_consumers,
)


def bars(count=400):
    return [{"date": (date(2026, 9, 26) - timedelta(days=count - i)).isoformat(),
             "open": 10, "high": 12, "low": 9, "close": 11 + (i % 2) / 10,
             "volume": 100 + i, "value": 1100} for i in range(count)]


def bad(rows, index):
    rows[index].update(open=16.35, high=15.8, low=15.43, close=15.66)
    return rows


def consume(rows, *, selected=None, fields=("high", "low", "close"), unknown=False):
    dates = tuple(row["date"] for row in (rows if selected is None else selected))
    return assess_consumer(rows, timeframe="daily", cutoff=date(2026, 9, 25),
        consumer=ConsumerRows("test", "test-owner", "explicit unit-test row set",
            None if unknown else dates, frozenset(fields), "OPTIONAL_COMPONENT"))


@pytest.mark.parametrize("values,violation", [
    ({"high": 9.5}, "HIGH_LT_OPEN"), ({"low": 10.5}, "LOW_GT_OPEN"),
    ({"high": 10.5}, "HIGH_LT_CLOSE"), ({"low": 11.5}, "LOW_GT_CLOSE"),
    ({"low": 13}, "LOW_GT_HIGH"),
])
def test_integrity_never_repaired(values, violation):
    rows = bars(3)
    rows[0].update(values)
    before = deepcopy(rows)
    result = consume(rows)
    assert any(i["violation"] == violation for i in result["anomalies"])
    assert result["source_integrity"] == "SOURCE_ANOMALY_PRESERVED"
    assert rows == before


def test_outside_inside_unknown_and_current():
    rows = bad(bars(), 30)
    assert consume(rows, selected=rows[-20:])["eligible"]
    assert not consume(rows)["eligible"]
    assert consume(rows, unknown=True)["reason"] == "SOURCE_ANOMALY_RELEVANCE_UNKNOWN"
    bad(rows, -1)
    result = consume(rows, selected=rows[-1:], fields=("close",))
    assert result["reason"] == "CURRENT_SNAPSHOT_SOURCE_ANOMALY"
    assert not result["eligible"]


def test_close_only_historical_unrelated_field_not_blanket_poisoned():
    rows = bad(bars(), 30)
    result = consume(rows, fields=("date", "close"))
    assert result["eligible"]
    assert result["anomalies"][0]["row_relevance"] == "CONSUMED"
    assert not result["anomalies"][0]["affected_fields_required"]
    rows[30]["close"] = 19
    assert not consume(rows, fields=("close",))["eligible"]


@pytest.mark.parametrize("mutation", ["invalid_date", "future", "duplicate", "ordering"])
def test_structural_uncertainty_blocks_all_windows(mutation):
    rows = bars(4)
    if mutation == "invalid_date":
        rows[0]["date"] = "bad"
    elif mutation == "future":
        rows[0]["date"] = "2027-01-01"
    elif mutation == "duplicate":
        rows[0]["date"] = rows[1]["date"]
    else:
        rows[0], rows[1] = rows[1], rows[0]
    assert not consume(rows, selected=rows[-1:], fields=("close",))["eligible"]


def test_actual_legacy_window_shared_with_owner(monkeypatch):
    original = structure.normalize_structure_bars
    seen = []

    def trace(raw, **kwargs):
        seen.append(kwargs.get("lookback"))
        return original(raw, **kwargs)

    monkeypatch.setattr(structure, "normalize_structure_bars", trace)
    structure.detect_local_pivots(bars(), timeframe="daily")
    assert structure.LOCAL_PIVOT_LOOKBACKS["daily"] in seen
    matrix = role_consumers(bad(bars(), 20), role="adjusted_daily", timeframe="daily",
        cutoff=date(2026, 9, 25), market="us", observed_at="2026-09-26T07:54:00+00:00")
    by = {item["consumer"]: item for item in matrix}
    assert by["legacy_local_pivots"]["eligible"]
    assert len(by["legacy_local_pivots"]["selected_dates"]) == structure.LOCAL_PIVOT_LOOKBACKS["daily"]
    assert not by["period_range_position"]["eligible"]
    assert not by["v3_long_cycle"]["eligible"]
    assert by["current_price"]["eligible"]


def test_actual_feature_audit_does_not_change_values():
    rows = bad(bars(), 20)
    normalized = _normalize_bars(rows, date(2026, 9, 25))
    args = ("TEST", "daily", normalized.bars, "adjusted_close", normalized.invalid_dates)
    expected = _feature_facts(*args)
    audit = []
    actual = _feature_facts(*args, dependency_audit=audit)
    assert actual == expected
    by = {d["semantic"]: d for d in audit}
    assert by["sma_20"]["dependency_bar_count"] == 20
    assert by["sma_20"]["classification"] == "SAFE_INDEPENDENT_OF_BAD_ROW"
    assert by["rsi_14"]["classification"] == "UNSAFE_DEPENDS_ON_BAD_ROW"
    assert by["atr_14"]["classification"] == "UNSAFE_DEPENDS_ON_BAD_ROW"


def project(rows):
    return materialize_source_components(ticker="TEST", market="us", cutoff=date(2026, 9, 25),
        observed_at="2026-09-26T07:54:00+00:00", roles={
            "adjusted_daily": rows, "adjusted_weekly": deepcopy(rows),
            "adjusted_monthly": deepcopy(rows), "unadjusted_weekly_valuation": deepcopy(rows)})


def test_components_deterministic_optional_failure_not_current_price_failure():
    rows = bad(bars(), 20)
    before = deepcopy(rows)
    result = project(rows)
    assert result == project(rows)
    assert result["current_price_eligible"]
    assert not result["mandatory_current_price_failure"]
    assert not result["complete_stock_packet"]
    assert result["stock_packet_sha256"] is None
    assert result["observed_business_union_status"].startswith("NOT_REACHED")
    assert "rsi_14" in result["features"]["daily"]["owner_blocked_features"]
    assert any(f["semantic"] == "sma_20" for f in result["features"]["daily"]["facts"])
    assert rows == before
    assert not inspect_normalized_ohlcv_rows(rows, timeframe="daily").valid


def test_current_bad_blocks_snapshot_and_does_not_emit_historical_substitute():
    result = project(bad(bars(), -1))
    assert result["mandatory_current_price_failure"]
    assert result["current_price"] is None
    assert result["features"]["daily"]["facts"] == []
    assert project(bars())["current_price_eligible"]


def test_exact_roles_fail_closed():
    with pytest.raises(ValueError, match="exact_four"):
        materialize_source_components(ticker="TEST", market="us", cutoff=date(2026, 9, 25),
            observed_at="2026-09-26T07:54:00+00:00", roles={})


def test_empty_role_not_zero_price():
    result = project([])
    assert result["current_price"] is None
    assert result["mandatory_current_price_failure"]


def test_stale_daily_not_current_substitute():
    result = project(bars()[:-1])
    assert not result["current_price_eligible"]
    assert result["current_price"] is None
    assert result["features"]["daily"]["facts"] == []


def test_unprovable_date_scope_blocks_component_without_selector_exception():
    rows = bars()
    rows[20]["date"] = "invalid"
    result = project(rows)
    assert not result["current_price_eligible"]
    assert result["features"]["daily"]["facts"] == []
    assert all(not c["eligible"] for c in result["role_consumer_matrix"]["adjusted_daily"])


def test_native_current_month_not_promoted_to_completed_feature():
    rows = bars()
    before = deepcopy(rows)
    result = project(rows)
    states = result["analysis_view_finality"]["monthly"]["rows"]
    assert states[-1]["bar_state"] == "PARTIAL"
    assert all(f["as_of"] < "2026-09-01" for f in result["features"]["monthly"]["facts"])
    assert rows == before
