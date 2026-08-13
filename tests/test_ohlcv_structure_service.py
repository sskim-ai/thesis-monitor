from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.schemas.thesis import InvestorSupplyContext
from app.services.ohlcv_structure_service import (
    LocalPivot,
    MajorSwing,
    analyze_chart_structure,
    build_price_zones,
    build_tentative_elliott_count,
    calc_wilder_atr,
    calculate_fibonacci_sets,
    calculate_invalidation,
    calculate_risk_reward,
    classify_price_zones,
    classify_supply_context,
    detect_boxes,
    detect_local_pivots,
    detect_major_swings,
    detect_major_swings_from_normalized_bars,
    determine_chart_state,
    normalize_bar_series,
    normalize_structure_bars,
    score_price_zones,
    select_nearest_meaningful_zones,
    select_major_anchors,
    validate_anchor_alignment,
)


def _bars_from_closes(
    closes: list[float],
    *,
    start: date = date(2025, 1, 1),
    spread: float = 1.0,
    step_days: int = 1,
) -> list[dict[str, object]]:
    return [
        {
            "date": (start + timedelta(days=index * step_days)).isoformat(),
            "open": close,
            "high": close + spread,
            "low": close - spread,
            "close": close,
            "volume": 1_000 + index,
        }
        for index, close in enumerate(closes)
    ]


def _segment(start: float, end: float, count: int) -> list[float]:
    return [start + (end - start) * index / count for index in range(count)]


def _major_swing(
    index: int,
    price: float,
    kind: str,
    *,
    timeframe: str = "weekly",
) -> MajorSwing:
    return MajorSwing(
        index=index,
        date=(date(2025, 1, 1) + timedelta(days=index * 7)).isoformat(),
        price=price,
        kind=kind,  # type: ignore[arg-type]
        timeframe=timeframe,  # type: ignore[arg-type]
        threshold=12,
        atr=4,
        pct_threshold=0.12,
        bars_since_previous=5,
        confirmed_at=(date(2025, 1, 1) + timedelta(days=(index + 4) * 7)).isoformat(),
    )


def _zone(
    low: float,
    high: float,
    *,
    strength: str = "Medium",
    pivot_type: str = "low",
    timeframe: str = "daily",
    distance_pct: float = 5,
    support_rank: int = 1,
) -> dict[str, object]:
    return {
        "zone_low": low,
        "zone_high": high,
        "center": (low + high) / 2,
        "strength": strength,
        "pivot_type": pivot_type,
        "timeframe": timeframe,
        "distance_pct": distance_pct,
        "support_rank": support_rank,
    }


def test_wilder_atr_uses_initial_mean_then_recursive_smoothing_and_gap_tr() -> None:
    bars = _bars_from_closes([10.0] * 14)
    bars.append(
        {
            "date": "2025-01-15",
            "open": 20,
            "high": 21,
            "low": 19,
            "close": 20,
            "volume": 1_000,
        }
    )

    atr = calc_wilder_atr(bars)

    assert atr[:13] == [None] * 13
    assert atr[13] == pytest.approx(2.0)
    assert atr[14] == pytest.approx((2 * 13 + 11) / 14)


def test_wilder_atr_insufficient_bars_returns_null_series() -> None:
    assert calc_wilder_atr(_bars_from_closes([10.0] * 5)) == [None] * 5
    assert calc_wilder_atr([]) == []


@pytest.mark.parametrize(
    ("timeframe", "left", "right"),
    (("daily", 5, 5), ("weekly", 3, 3), ("monthly", 2, 2)),
)
def test_local_pivot_windows_and_prominence(timeframe: str, left: int, right: int) -> None:
    closes = [110.0] * 40
    pivot_index = 20
    closes[pivot_index] = 80
    bars = _bars_from_closes(closes)

    pivots = detect_local_pivots(bars, timeframe)  # type: ignore[arg-type]

    low = next(item for item in pivots if item.kind == "low")
    assert low.index == pivot_index
    assert low.prominence >= low.min_required
    assert pivot_index >= left
    assert pivot_index + right < len(bars)


def test_equal_price_local_pivot_prefers_highest_volume_then_middle() -> None:
    closes = [110.0] * 45
    bars = _bars_from_closes(closes)
    for index in (20, 21, 22):
        bars[index].update({"open": 81, "high": 82, "low": 80, "close": 81, "volume": 1_000})
    bars[21]["volume"] = 5_000

    pivots = detect_local_pivots(bars, "daily")

    tied_lows = [item for item in pivots if item.kind == "low" and item.price == 80]
    assert [item.index for item in tied_lows] == [21]


def test_local_pivot_rejects_low_prominence_and_uses_larger_atr_or_percent_threshold() -> None:
    quiet = _bars_from_closes([100 + (0.2 if index % 2 else 0) for index in range(45)], spread=0.1)
    quiet[22].update({"open": 99.8, "high": 100, "low": 99.7, "close": 99.8})
    assert not [item for item in detect_local_pivots(quiet, "daily") if item.index == 22]

    closes = [100.0] * 45
    closes[22] = 80
    pivot = next(item for item in detect_local_pivots(_bars_from_closes(closes), "daily") if item.kind == "low")
    assert pivot.min_required == pytest.approx(max(pivot.price * 0.02, pivot.atr))


def test_zone_merge_uses_median_padding_and_splits_excess_width() -> None:
    pivots = [
        LocalPivot(index, f"2025-01-{index + 1:02d}", price, "low", "daily", 10, 2, 1, 1_000)
        for index, price in enumerate((88.5, 89.1, 89.7, 94.5))
    ]

    zones = build_price_zones(pivots, "daily", bar_count=100)

    assert len(zones) == 2
    assert zones[0]["center"] == pytest.approx(89.1)
    assert zones[0]["pivot_count"] == 3
    assert zones[0]["zone_low"] < 88.5
    assert zones[0]["zone_high"] > 89.7

    wide = [
        LocalPivot(index, f"2025-02-{index + 1:02d}", price, "low", "daily", 30, 20, 20, 1_000)
        for index, price in enumerate((100, 104))
    ]
    assert len(build_price_zones(wide, "daily", bar_count=100)) == 2


def test_zone_strength_and_current_price_classification_keep_distance_order() -> None:
    daily = [_zone(90, 92), _zone(105, 107, pivot_type="high")]
    for item in daily:
        item.update({"reaction_score": 3, "recency_score": 2, "atr": 2})
    weekly = [_zone(91, 93)]
    weekly[0].update({"reaction_score": 2, "recency_score": 2, "atr": 3})

    scored = score_price_zones(
        {"daily": daily, "weekly": weekly, "monthly": []},
        bollinger_values=[91.5],
        fibonacci_values=[91.0],
    )
    classified = classify_price_zones(scored, 100)

    assert [item["zone_high"] for item in classified["support"]] == [93, 92]
    assert classified["resistance"][0]["zone_low"] == 105
    assert next(item for item in scored if item["center"] == 91)["strength"] == "Strong"


@pytest.mark.parametrize(
    ("subject", "others", "expected_score", "expected_lower"),
    (
        ("daily", ("weekly",), 2, 0),
        ("daily", ("monthly",), 2, 0),
        ("daily", ("weekly", "monthly"), 3, 0),
        ("weekly", ("daily",), 0, 1),
        ("weekly", ("monthly",), 2, 0),
        ("monthly", ("daily",), 0, 1),
        ("monthly", ("weekly",), 0, 1),
    ),
)
def test_zone_strength_counts_only_true_higher_timeframes(
    subject: str,
    others: tuple[str, ...],
    expected_score: int,
    expected_lower: int,
) -> None:
    zones: dict[str, list[dict[str, object]]] = {
        "daily": [],
        "weekly": [],
        "monthly": [],
    }
    for timeframe in (subject, *others):
        zone = _zone(99, 101, timeframe=timeframe)
        zone.update({"reaction_score": 1, "recency_score": 0, "atr": 1})
        zones[timeframe].append(zone)

    scored = score_price_zones(zones)
    result = next(item for item in scored if item["timeframe"] == subject)

    assert result["higher_timeframe_score"] == expected_score
    assert result["lower_timeframe_overlap_count"] == expected_lower


def test_zone_inside_current_price_is_active_with_two_sided_distances() -> None:
    classified = classify_price_zones([_zone(98, 102)], 100)
    assert classified["active"][0]["distance_to_lower_pct"] == 2
    assert classified["active"][0]["distance_to_upper_pct"] == 2
    assert classified["active"][0]["support_rank"] == 1

    with_higher_old_low = classify_price_zones(
        [_zone(98, 102), _zone(110, 112)],
        100,
    )
    assert with_higher_old_low["active"][0]["support_rank"] == 1


def test_box_requires_width_inside_ratio_and_two_boundary_reactions() -> None:
    bars = []
    for index in range(20):
        bars.append(
            {
                "date": (date(2025, 1, 1) + timedelta(days=index)).isoformat(),
                "open": 100,
                "high": 105 if index % 2 else 103,
                "low": 95 if index % 3 == 0 else 97,
                "close": 99 if index % 2 else 101,
                "volume": 1_000,
            }
        )
    zones = [
        {**_zone(94, 96), "atr": 2},
        {**_zone(104, 106, pivot_type="high"), "atr": 2},
    ]

    boxes = detect_boxes(bars, zones, "daily")

    assert boxes[0]["inside_close_ratio"] == 1
    assert boxes[0]["lower_reactions"] >= 2
    assert boxes[0]["upper_reactions"] >= 2
    assert detect_boxes(bars[:10], zones, "daily") == []
    assert detect_boxes(
        bars,
        [{**zone, "pivot_type": "low"} for zone in zones],
        "daily",
    ) == []


def test_major_swing_engine_uses_raw_bars_and_remains_sparser_than_local_pivots() -> None:
    closes = [
        *_segment(100, 140, 15),
        *_segment(140, 95, 15),
        *_segment(95, 150, 15),
        *_segment(150, 105, 15),
        *_segment(105, 160, 15),
        *_segment(160, 115, 15),
    ]
    bars = _bars_from_closes(closes)
    local = detect_local_pivots(bars, "daily")
    major = detect_major_swings(bars, "daily")

    assert len(major) >= 3
    assert len(major) <= len(local)
    assert all(isinstance(item, MajorSwing) for item in major)
    with pytest.raises(TypeError, match="raw bar mappings"):
        detect_major_swings(local, "daily")  # type: ignore[arg-type]


def test_major_swing_updates_extreme_and_respects_minimum_leg() -> None:
    closes = [
        *_segment(100, 150, 20),
        *_segment(150, 151, 3),
        *_segment(151, 110, 20),
        *_segment(110, 160, 20),
    ]
    swings = detect_major_swings(_bars_from_closes(closes), "daily")
    highs = [item for item in swings if item.kind == "high"]
    assert highs
    assert highs[0].price >= 151
    assert highs[0].bars_since_previous >= 10
    assert all(item.bars_since_previous >= 10 for item in swings)


def test_major_swing_300_to_156_uses_canonical_series_indexes() -> None:
    prefix = [75.0 + index * 0.1 for index in range(144)]
    selected = [
        *_segment(100, 145, 20),
        *_segment(145, 90, 20),
        *_segment(90, 155, 20),
        *_segment(155, 100, 20),
        *_segment(100, 165, 20),
        *_segment(165, 110, 20),
        *_segment(110, 170, 20),
        *_segment(170, 130, 16),
    ]
    raw = _bars_from_closes(prefix + selected, start=date(2019, 1, 1), step_days=7)
    series = normalize_bar_series(raw, "weekly", lookback=156)
    swings = detect_major_swings_from_normalized_bars(series)

    assert series.source_count == 300
    assert series.actual_count == 156
    assert swings
    assert all(series.bars[swing.index].date == swing.date for swing in swings)
    assert select_major_anchors(swings, series)["alignment"]["valid"] is True  # type: ignore[index]


def test_anchor_indexes_share_the_same_truncated_weekly_coordinate_system() -> None:
    selected_closes = [100] * 10 + [80] + list(range(81, 161)) + [160] * 65
    raw = _bars_from_closes(
        [70.0] * 144 + selected_closes,
        start=date(2019, 1, 1),
        step_days=7,
    )
    series = normalize_bar_series(raw, "weekly", lookback=156)

    def swing(index: int, price: float, kind: str) -> MajorSwing:
        return MajorSwing(
            index=index,
            date=series.bars[index].date,
            price=price,
            kind=kind,  # type: ignore[arg-type]
            timeframe="weekly",
            threshold=12,
            atr=4,
            pct_threshold=0.12,
            bars_since_previous=5,
            confirmed_at=series.bars[min(index + 4, 155)].date,
        )

    swings = [
        swing(5, 120, "high"),
        swing(10, 80, "low"),
        swing(20, 135, "high"),
        swing(25, 90, "low"),
        swing(35, 150, "high"),
        swing(40, 110, "low"),
        swing(50, 165, "high"),
    ]
    anchors = select_major_anchors(swings, series)

    for name in ("major_base_low", "breakout_start", "first_higher_low"):
        anchor = anchors[name]
        assert isinstance(anchor, dict)
        assert series.bars[anchor["index"]].date == anchor["date"]
    assert validate_anchor_alignment(anchors, series)["valid"] is True


def test_weekly_primary_and_daily_fallback_are_explicit() -> None:
    daily = _bars_from_closes([100 + 20 * ((index // 15) % 2) for index in range(90)])
    weekly_short = _bars_from_closes([100 + index for index in range(40)])
    monthly = _bars_from_closes([100 + index for index in range(30)])

    result = analyze_chart_structure(
        {"daily": daily, "weekly": weekly_short, "monthly": monthly}
    )
    assert result["major_swings"]["primary_timeframe"] == "daily"
    assert result["major_swings"]["fallback_used"] is True

    weekly_long = _bars_from_closes([100 + 20 * ((index // 6) % 2) for index in range(70)])
    result = analyze_chart_structure(
        {"daily": daily, "weekly": weekly_long, "monthly": monthly}
    )
    assert result["major_swings"]["primary_timeframe"] == "weekly"


def test_major_anchor_selection_and_fibonacci_provenance_use_major_swings_only() -> None:
    swings = [
        _major_swing(5, 120, "high"),
        _major_swing(10, 80, "low"),
        _major_swing(20, 135, "high"),
        _major_swing(25, 90, "low"),
        _major_swing(35, 150, "high"),
        _major_swing(40, 110, "low"),
        _major_swing(50, 165, "high"),
    ]
    bars = _bars_from_closes(
        [100] * 10 + [80] + list(range(81, 161)),
        step_days=7,
    )
    series = normalize_bar_series(bars, "weekly", lookback=156)
    anchors = select_major_anchors(swings, series)
    fib = calculate_fibonacci_sets(anchors, series)

    assert anchors["major_base_low"]["price"] == 80  # type: ignore[index]
    assert anchors["major_base_low"]["confidence"] == "medium"  # type: ignore[index]
    assert anchors["major_base_low"]["blocking_unknowns"] == [  # type: ignore[index]
        "pre_base_regime_unverified"
    ]
    assert anchors["breakout_start"]["confidence"] == "medium"  # type: ignore[index]
    assert anchors["breakout_start"]["selection_reason"] == [  # type: ignore[index]
        "20_week_close_breakout",
        "volume_not_confirmed",
    ]
    assert anchors["breakout_confirmation"]["volume_confirmation"] == "volume_not_confirmed"  # type: ignore[index]
    assert fib["long_term"]["source"] == "major_swing_engine"
    assert fib["long_term"]["usable_as_context"] is True
    assert fib["long_term"]["usable_as_sole_core_reason"] is False
    assert fib["long_term"]["low_price"] == 80
    assert fib["long_term"]["retracements"]["0.5"] == pytest.approx(122.5)
    assert fib["long_term"]["extensions"]["1.618"] == pytest.approx(217.53)


@pytest.mark.parametrize(
    ("breakout_volume", "remove_history", "expected_confidence", "expected_status"),
    (
        (1_500.0, False, "high", "volume_confirmed"),
        (1_000.0, True, "medium", "volume_unknown"),
    ),
)
def test_breakout_start_confidence_reflects_volume_confirmation(
    breakout_volume: float,
    remove_history: bool,
    expected_confidence: str,
    expected_status: str,
) -> None:
    bars = _bars_from_closes([100.0] * 20 + [130.0] + [130.0] * 19, step_days=7)
    for bar in bars:
        bar["volume"] = None if remove_history else 1_000.0
    bars[20]["volume"] = None if remove_history else breakout_volume
    series = normalize_bar_series(bars, "weekly", lookback=156)
    swing = MajorSwing(
        index=10,
        date=series.bars[10].date,
        price=95,
        kind="low",
        timeframe="weekly",
        threshold=12,
        atr=4,
        pct_threshold=0.12,
        bars_since_previous=5,
        confirmed_at=series.bars[14].date,
    )

    anchors = select_major_anchors([swing], series)

    assert anchors["breakout_start"]["confidence"] == expected_confidence  # type: ignore[index]
    assert anchors["breakout_confirmation"]["volume_confirmation"] == expected_status  # type: ignore[index]
    if remove_history:
        assert anchors["breakout_start"]["blocking_unknowns"] == [  # type: ignore[index]
            "historical_volume_confirmation_unavailable"
        ]


def test_breakout_volume_is_not_applicable_without_a_price_breakout() -> None:
    series = normalize_bar_series(
        _bars_from_closes([100.0] * 40, step_days=7),
        "weekly",
        lookback=156,
    )
    swing = MajorSwing(
        index=10,
        date=series.bars[10].date,
        price=95,
        kind="low",
        timeframe="weekly",
        threshold=12,
        atr=4,
        pct_threshold=0.12,
        bars_since_previous=5,
        confirmed_at=series.bars[14].date,
    )

    anchors = select_major_anchors([swing], series)

    assert anchors["breakout_start"] is None
    assert anchors["breakout_confirmation"]["price_condition"] == "not_found"  # type: ignore[index]
    assert anchors["breakout_confirmation"]["volume_confirmation"] == "not_applicable"  # type: ignore[index]


def test_fibonacci_fails_closed_on_anchor_index_mismatch_and_gates_confidence() -> None:
    series = normalize_bar_series(
        _bars_from_closes([100 + index for index in range(40)], step_days=7),
        "weekly",
        lookback=156,
    )
    anchors: dict[str, object] = {
        "major_base_low": {
            "anchor_type": "major_base_low",
            "index": 5,
            "date": series.bars[5].date,
            "price": 105,
            "timeframe": "weekly",
            "confidence": "low",
            "source": "major_swing_engine",
            "blocking_unknowns": ["pre_base_regime_unverified"],
        },
        "dominant_major_high": {
            "anchor_type": "dominant_major_high",
            "index": 30,
            "date": series.bars[30].date,
            "price": 130,
            "timeframe": "weekly",
            "confidence": "high",
            "source": "major_swing_engine",
            "blocking_unknowns": [],
        },
    }
    fib = calculate_fibonacci_sets(anchors, series)
    assert fib["long_term"]["confidence"] == "low"
    assert fib["long_term"]["usable_as_context"] is False
    assert fib["long_term"]["audit_only"] is True

    anchors["major_base_low"] = {
        **anchors["major_base_low"],  # type: ignore[dict-item]
        "index": 6,
    }
    assert validate_anchor_alignment(anchors, series)["reason"] == "anchor_index_mismatch"
    assert calculate_fibonacci_sets(anchors, series) == {}


def test_elliott_wave2_failure_rejects_and_wave4_overlap_lowers_confidence() -> None:
    invalid = [
        _major_swing(0, 100, "low"),
        _major_swing(5, 130, "high"),
        _major_swing(10, 95, "low"),
        _major_swing(15, 150, "high"),
    ]
    anchors = {
        "major_base_low": {
            "index": invalid[0].index,
            "date": invalid[0].date,
            "price": 100,
            "timeframe": "weekly",
            "confidence": "high",
        }
    }
    assert build_tentative_elliott_count(invalid, anchors)["reason"] == "wave2_broke_wave1_start"

    overlap = [
        _major_swing(0, 100, "low"),
        _major_swing(5, 130, "high"),
        _major_swing(10, 110, "low"),
        _major_swing(15, 160, "high"),
        _major_swing(20, 125, "low"),
        _major_swing(25, 170, "high"),
    ]
    anchors["major_base_low"]["index"] = overlap[0].index  # type: ignore[index]
    anchors["major_base_low"]["date"] = overlap[0].date  # type: ignore[index]
    result = build_tentative_elliott_count(overlap, anchors)
    assert result["tentative_count"] is True
    assert result["possible_diagonal"] is True
    assert result["confidence"] == "low"
    assert result["usable_in_core"] is False


def test_supply_classification_never_invents_us_supply() -> None:
    assert classify_supply_context(None)["classification"] == "unavailable"
    joint = classify_supply_context(
        InvestorSupplyContext(
            available=True,
            foreign_net_buy_qty_20=100,
            institution_net_buy_qty_20=200,
            individual_net_buy_qty_20=-300,
        )
    )
    assert joint == {
        "classification": "strong_joint",
        "horizon": "20d",
        "confidence": "high",
        "foreign": 100.0,
        "institution": 200.0,
        "individual": -300.0,
    }


def test_invalidation_distinguishes_two_close_accelerated_and_wick_only() -> None:
    support = _zone(90, 92)
    normal = _bars_from_closes([95, 94])
    result = calculate_invalidation(
        support,
        current_price=95,
        daily_atr=2,
        weekly_atr=3,
        daily_bars=[],
        weekly_bars=[],
        volume_ratio=1,
        supply_classification="mixed",
    )
    assert result["price"] == pytest.approx(89.0)

    structure = analyze_chart_structure({"daily": normal, "weekly": [], "monthly": []})
    assert "invalidation" in structure

    below = normalize_structure_bars(_bars_from_closes([88, 88]))
    hard = calculate_invalidation(
        support,
        current_price=95,
        daily_atr=2,
        weekly_atr=3,
        daily_bars=below,
        weekly_bars=[],
        volume_ratio=1,
        supply_classification="mixed",
    )
    assert hard["status"] == "hard_invalid"

    accelerated = calculate_invalidation(
        support,
        current_price=95,
        daily_atr=2,
        weekly_atr=3,
        daily_bars=below[-1:],
        weekly_bars=[],
        volume_ratio=1.3,
        supply_classification="distribution",
    )
    assert accelerated["status"] == "accelerated_invalid"

    wick_bars = normalize_structure_bars(
        [{"date": "2025-01-01", "open": 91, "high": 93, "low": 88, "close": 91, "volume": 1_000}]
    )
    wick = calculate_invalidation(
        support,
        current_price=95,
        daily_atr=2,
        weekly_atr=3,
        daily_bars=wick_bars,
        weekly_bars=[],
        volume_ratio=0.8,
        supply_classification="mixed",
    )
    assert wick["status"] == "wick_only_review"


def test_weekly_invalidation_uses_weekly_atr_and_buffer() -> None:
    support = _zone(90, 92, timeframe="weekly")
    result = calculate_invalidation(
        support,
        current_price=95,
        daily_atr=2,
        weekly_atr=4,
        daily_bars=[],
        weekly_bars=[],
        volume_ratio=1,
        supply_classification="mixed",
    )

    assert result["timeframe"] == "weekly"
    assert result["buffer"] == pytest.approx(max(4 * 0.5, 91 * 0.015))


def test_monthly_nearest_support_withholds_invalidation_and_rr_without_fallback() -> None:
    monthly = _zone(94, 96, timeframe="monthly")
    farther_daily = _zone(85, 88, timeframe="daily")
    resistance = _zone(105, 107, pivot_type="high")
    support, selected_resistance = select_nearest_meaningful_zones(
        {
            "active": [],
            "support": [monthly, farther_daily],
            "resistance": [resistance],
        }
    )

    assert support is monthly
    invalidation = calculate_invalidation(
        support,
        current_price=100,
        daily_atr=2,
        weekly_atr=4,
        daily_bars=[],
        weekly_bars=[],
        volume_ratio=1,
        supply_classification="mixed",
    )
    rr = calculate_risk_reward(
        current_price=100,
        resistance=selected_resistance,
        invalidation=invalidation,
        support=support,
    )

    assert invalidation == {
        "available": False,
        "reason": "monthly_invalidation_contract_undefined",
        "timeframe": "monthly",
        "nearest_support_preserved": True,
    }
    assert rr["available"] is False
    assert rr["blocking_reason"] == "monthly_invalidation_contract_undefined"


def test_risk_reward_uses_passed_nearest_resistance_and_scenario_midpoint() -> None:
    invalidation = {"available": True, "price": 88}
    nearest = _zone(105, 107, pivot_type="high")
    rr = calculate_risk_reward(
        current_price=100,
        resistance=nearest,
        invalidation=invalidation,
        support=_zone(90, 92),
    )
    assert rr["current_price"]["target"] == 105  # type: ignore[index]
    assert rr["current_price"]["ratio"] == pytest.approx(5 / 12)  # type: ignore[index]
    assert rr["support_entry"]["entry"] == 91  # type: ignore[index]
    assert calculate_risk_reward(
        current_price=100,
        resistance=None,
        invalidation=invalidation,
    )["available"] is False


def _state(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "current_price": 100.0,
        "classified_zones": {
            "support": [_zone(90, 92)],
            "resistance": [_zone(110, 112, pivot_type="high")],
            "active": [],
        },
        "all_zones": [],
        "invalidation": {"available": True, "status": "intact", "price": 88},
        "risk_reward": {
            "available": True,
            "current_price": {"ratio": 2},
            "support_entry": {"ratio": 2},
        },
        "daily_bars": normalize_structure_bars(_bars_from_closes([99, 100])),
        "volume_ratio": 1.0,
        "upper_wick_pct": 10.0,
        "close_location_pct": 80.0,
        "supply": {"classification": "mixed"},
        "bollinger_values": {},
        "fibonacci_sets": {},
        "major_swing_count": 3,
    }
    values.update(overrides)
    return determine_chart_state(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("expected", "overrides"),
    (
        ("INVALID", {"invalidation": {"available": True, "status": "hard_invalid"}}),
        (
            "TRIM",
            {
                "bollinger_values": {"24_month": 101},
                "volume_ratio": 1.6,
                "upper_wick_pct": 40,
            },
        ),
        (
            "CONFIRM_ENTRY",
            {
                "current_price": 110.0,
                "all_zones": [_zone(98, 100, pivot_type="high")],
                "daily_bars": normalize_structure_bars(_bars_from_closes([105, 110])),
                "volume_ratio": 1.3,
                "supply": {"classification": "strong_joint"},
            },
        ),
        (
            "SECOND_SUPPORT_ENTRY",
            {
                "classified_zones": {
                    "support": [],
                    "resistance": [_zone(110, 112, pivot_type="high")],
                    "active": [_zone(98, 102, support_rank=2)],
                }
            },
        ),
        (
            "SUPPORT_ENTRY",
            {
                "classified_zones": {
                    "support": [],
                    "resistance": [_zone(110, 112, pivot_type="high")],
                    "active": [_zone(98, 102)],
                }
            },
        ),
        ("HOLD", {}),
        (
            "WAIT",
            {"risk_reward": {"available": True, "current_price": {"ratio": 1.0}, "support_entry": None}},
        ),
    ),
)
def test_chart_state_machine_states_and_priority(
    expected: str,
    overrides: dict[str, object],
) -> None:
    assert _state(**overrides)["state"] == expected


def test_invalid_state_beats_trim_and_confirm_collisions() -> None:
    result = _state(
        invalidation={"available": True, "status": "accelerated_invalid"},
        bollinger_values={"24_month": 100},
        volume_ratio=2,
        upper_wick_pct=50,
    )
    assert result["state"] == "INVALID"


def test_confirm_entry_rejects_weak_breakout_zone() -> None:
    result = _state(
        current_price=110.0,
        all_zones=[_zone(98, 100, pivot_type="high", strength="Weak")],
        daily_bars=normalize_structure_bars(_bars_from_closes([105, 110])),
        volume_ratio=1.3,
        supply={"classification": "strong_joint"},
    )

    assert result["state"] != "CONFIRM_ENTRY"


def test_full_structure_contract_keeps_local_and_major_outputs_separate() -> None:
    closes = [
        *_segment(100, 140, 15),
        *_segment(140, 95, 15),
        *_segment(95, 150, 15),
        *_segment(150, 105, 15),
        *_segment(105, 160, 15),
        *_segment(160, 115, 15),
    ]
    result = analyze_chart_structure(
        {
            "daily": _bars_from_closes(closes),
            "weekly": _bars_from_closes(closes[:70]),
            "monthly": _bars_from_closes(closes[:60]),
        },
        timeframe_contexts={
            "daily": {
                "candle": {"upper_wick_pct": 10, "close_location_pct": 80},
                "volume_ratio_20": 1.0,
                "bollinger_upper": {},
            }
        },
    )

    assert result["algorithm_version"] == "ohlcv-structure-v2"
    assert result["price_basis"] == "adjusted_close"
    assert result["local_pivots"] is not result["major_swings"]
    for fib in result["fibonacci"].values():
        assert fib["source"] == "major_swing_engine"
