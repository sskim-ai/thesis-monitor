from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.services.ohlcv_structure_service import (
    analyze_chart_structure,
    build_price_zones,
    detect_local_pivots,
    score_price_zones,
    select_nearest_meaningful_zones,
)


def _reaction_bars(count: int, timeframe: str) -> list[dict[str, object]]:
    step_days = {"daily": 1, "weekly": 7, "monthly": 30}[timeframe]
    offsets = {
        "daily": (30, 18, 6),
        "weekly": (20, 12, 4),
        "monthly": (18, 10, 3),
    }[timeframe]
    reaction_indexes = {count - offset for offset in offsets}
    return [
        {
            "date": (date(2020, 1, 1) + timedelta(days=index * step_days)).isoformat(),
            "open": 100.0,
            "high": 101.0,
            "low": 90.0 if index in reaction_indexes else 99.0,
            "close": 100.0,
            "volume": 100.0,
        }
        for index in range(count)
    ]


def _flat_daily_bars() -> list[dict[str, object]]:
    # Supply a current price without adding daily support or confluence points.
    return [
        {
            "date": (date(2026, 1, 1) + timedelta(days=index)).isoformat(),
            "open": 100.0,
            "high": 100.1,
            "low": 99.9,
            "close": 100.0,
            "volume": 100.0,
        }
        for index in range(30)
    ]


def _reaction_zone(zones: list[dict[str, object]], timeframe: str) -> dict[str, object]:
    matches = [
        zone
        for zone in zones
        if zone["timeframe"] == timeframe
        and zone["pivot_type"] == "low"
        and zone["center"] == 90.0
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize("weekly_count", [80, 120, 121, 128, 155, 156, 180])
def test_weekly_recent_reactions_use_local_window_without_shortening_major_history(
    weekly_count: int,
) -> None:
    weekly = _reaction_bars(weekly_count, "weekly")
    result = analyze_chart_structure({"daily": _flat_daily_bars(), "weekly": weekly})
    zone = _reaction_zone(result["all_zones"], "weekly")

    assert zone["reaction_count"] == 3
    assert zone["recency_score"] == 2
    assert zone["score"] == 5
    assert zone["strength"] == "Medium"
    assert zone["latest_reaction_date"] == weekly[-4]["date"]
    low_pivots = [
        pivot
        for pivot in result["local_pivots"]["weekly"]
        if pivot["kind"] == "low" and pivot["price"] == 90.0
    ]
    assert max(pivot["index"] for pivot in low_pivots) == min(weekly_count, 120) - 4

    support, _ = select_nearest_meaningful_zones(result["zones"])
    assert support is not None
    assert support["timeframe"] == "weekly"
    assert support["center"] == 90.0
    canonical = result["major_swings"]["canonical_series"]
    assert canonical["source_count"] == weekly_count
    assert canonical["actual_count"] == min(weekly_count, 156)
    assert canonical["lookback_start_date"] == weekly[-min(weekly_count, 156)]["date"]

    if weekly_count >= 128:
        # Reproduce the previous count mismatch with these same actual pivots.
        # The recent reaction used to appear 11–39 bars old and become Weak.
        previous_zones = score_price_zones(
            {
                "weekly": build_price_zones(
                    detect_local_pivots(weekly, "weekly"),
                    "weekly",
                    bar_count=min(weekly_count, 156),
                )
            }
        )
        assert _reaction_zone(previous_zones, "weekly")["strength"] == "Weak"


def test_weekly_recency_counts_valid_sorted_bars_in_a_short_history() -> None:
    weekly = _reaction_bars(80, "weekly")
    invalid_rows = [
        {**weekly[0], "date": "invalid-date"},
        {**weekly[0], "low": 102.0},
        {**weekly[0], "close": None},
    ] * 40
    result = analyze_chart_structure(
        {"daily": _flat_daily_bars(), "weekly": list(reversed(weekly + invalid_rows))}
    )
    zone = _reaction_zone(result["all_zones"], "weekly")

    assert zone["latest_reaction_date"] == weekly[-4]["date"]
    assert zone["recency_score"] == 2
    assert zone["score"] == 5
    assert zone["strength"] == "Medium"
    canonical = result["major_swings"]["canonical_series"]
    assert canonical["source_count"] == 200
    assert canonical["actual_count"] == 80
    assert canonical["lookback_start_date"] == weekly[0]["date"]


@pytest.mark.parametrize(
    ("timeframe", "count", "lookback", "latest_offset"),
    [("daily", 80, 300, 6), ("daily", 330, 300, 6),
     ("monthly", 40, 60, 3), ("monthly", 80, 60, 3)],
)
def test_daily_and_monthly_recency_keep_their_existing_window(
    timeframe: str, count: int, lookback: int, latest_offset: int,
) -> None:
    bars = _reaction_bars(count, timeframe)
    result = analyze_chart_structure({timeframe: bars})
    zone = _reaction_zone(result["all_zones"], timeframe)

    assert zone["reaction_count"] == 3
    assert zone["recency_score"] == 2
    assert zone["score"] == 5
    assert zone["strength"] == "Medium"
    assert zone["latest_reaction_date"] == bars[-latest_offset]["date"]
    low_pivots = [
        pivot
        for pivot in result["local_pivots"][timeframe]
        if pivot["kind"] == "low" and pivot["price"] == 90.0
    ]
    assert max(pivot["index"] for pivot in low_pivots) == min(count, lookback) - latest_offset
