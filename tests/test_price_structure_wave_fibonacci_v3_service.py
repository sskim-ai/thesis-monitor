from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.services.price_structure_wave_fibonacci_v3_service import (
    HISTORY_REQUESTS,
    FibonacciReference,
    MonthlyWaveHypothesis,
    PivotPoint,
    PriceBar,
    WaveEndpoint,
    WaveHypothesisSelection,
    WaveSelectionStatus,
    ZoneSource,
    _source_score,
    build_cross_timeframe_confluence,
    build_pivot_zones,
    build_price_structure_wave_fib_v3,
    calculate_wave_fibonacci,
    classify_wave_selection_consensus,
    detect_pivots,
    generate_primary_monthly_hypotheses,
    merge_zone_sources,
    normalize_completed_bars,
    prepare_long_history,
    validate_wave_hypothesis_selection,
    wave_hypothesis_packet,
)


def _raw(date: str, close: float, *, spread: float = 2.0) -> dict[str, object]:
    return {
        "date": date,
        "open": close,
        "high": close + spread,
        "low": max(close - spread, 0.1),
        "close": close,
        "volume": 1000,
        "value": 100_000,
    }


def _bar(index: int, close: float, *, year: int = 2020) -> PriceBar:
    month = index % 12 + 1
    adjusted_year = year + index // 12
    return PriceBar(
        date=f"{adjusted_year:04d}-{month:02d}-01",
        open=Decimal(str(close)),
        high=Decimal(str(close + 2)),
        low=Decimal(str(close - 2)),
        close=Decimal(str(close)),
        volume=Decimal(1000),
    )


def _pivot(
    label: str,
    date: str,
    price: int,
    kind: str,
    *,
    timeframe: str = "monthly",
    status: str = "CONFIRMED",
) -> PivotPoint:
    return PivotPoint(
        pivot_id=f"pivot:{label}",
        ticker="TEST",
        timeframe=timeframe,
        bar_date=date,
        confirmation_date=date if status == "CONFIRMED" else None,
        kind=kind,
        price=Decimal(price),
        atr14=Decimal(5),
        status=status,
        adjustment_basis="adjusted_close",
        source_ref=f"ohlcv:{timeframe}:{date}",
    )


def _hypothesis(identifier: str = "wave:1") -> MonthlyWaveHypothesis:
    points = (
        WaveEndpoint(label="W0", pivot_ref="p0", date="2023-01-01", price=Decimal(100), status="CONFIRMED"),
        WaveEndpoint(label="W1", pivot_ref="p1", date="2023-06-01", price=Decimal(200), status="CONFIRMED"),
        WaveEndpoint(label="W2", pivot_ref="p2", date="2023-09-01", price=Decimal(140), status="CONFIRMED"),
        WaveEndpoint(label="W3", pivot_ref="p3", date="2024-06-01", price=Decimal(320), status="PROVISIONAL"),
        WaveEndpoint(label="W4", pivot_ref="p4", date="2024-09-01", price=Decimal(230), status="PROVISIONAL"),
    )
    return MonthlyWaveHypothesis(
        hypothesis_id=identifier,
        ticker="TEST",
        status="VALID_PROVISIONAL",
        wave_state="W4_CANDIDATE_W5_UNCONFIRMED",
        endpoints=points,
        hard_rules={"all": True},
        score=Decimal("12.5"),
        score_components={"hard": Decimal(10)},
    )


def test_history_contract_uses_1200_600_300_and_reports_provider_cap() -> None:
    assert HISTORY_REQUESTS == {"daily": 1200, "weekly": 600, "monthly": 300}
    start = date(2023, 1, 1)
    raw = [
        _raw((start + timedelta(days=index)).isoformat(), 100 + index)
        for index in range(1000)
    ]
    bars, coverage = prepare_long_history(
        raw,
        timeframe="daily",
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
    )
    assert len(bars) <= 1000
    assert coverage.requested_count == 1200
    assert coverage.status == "PARTIAL"
    assert coverage.provider_limit_hit is True
    assert coverage.denial_reason == "provider_limit"


def test_short_listing_is_safe_partial_without_padding() -> None:
    raw = [_raw(f"2026-{month:02d}-01", 100 + month) for month in range(1, 9)]
    bars, coverage = prepare_long_history(
        raw,
        timeframe="monthly",
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
    )
    assert len(bars) == 8
    assert coverage.actual_count == 8
    assert coverage.history_complete_to_listing is True
    assert coverage.status == "PARTIAL"


def test_future_and_invalid_bars_are_excluded() -> None:
    bars = normalize_completed_bars(
        [
            _raw("2026-08-25", 100),
            _raw("2026-08-27", 110),
            {"date": "2026-08-24", "open": 100, "high": 90, "low": 95, "close": 98},
        ],
        cutoff="2026-08-26",
    )
    assert [bar.date for bar in bars] == ["2026-08-25"]


def test_pivot_confirmation_uses_required_right_bars() -> None:
    bars = tuple(_bar(index, close) for index, close in enumerate([10, 12, 15, 20, 14, 11, 16]))
    pivots = detect_pivots(
        bars,
        ticker="TEST",
        timeframe="monthly",
        adjustment_basis="adjusted_close",
    )
    high = next(pivot for pivot in pivots if pivot.kind == "HIGH" and pivot.bar_date == bars[3].date)
    assert high.status == "CONFIRMED"
    assert high.confirmation_date == bars[5].date


def test_recent_endpoint_can_be_provisional_without_lookahead() -> None:
    bars = tuple(_bar(index, close) for index, close in enumerate([10, 12, 14, 16, 20]))
    pivots = detect_pivots(
        bars,
        ticker="TEST",
        timeframe="monthly",
        adjustment_basis="adjusted_close",
    )
    latest = next(pivot for pivot in pivots if pivot.bar_date == bars[-1].date)
    assert latest.status == "PROVISIONAL"
    assert latest.confirmation_date is None


def test_pivot_zone_uses_atr_padding_and_current_role() -> None:
    zones = build_pivot_zones(
        (
            _pivot("a", "2024-01-01", 100, "LOW"),
            _pivot("b", "2024-03-01", 101, "LOW"),
        ),
        ticker="TEST",
        timeframe="monthly",
        current_price=Decimal(150),
    )
    assert len(zones) == 1
    assert zones[0].low < Decimal(100)
    assert zones[0].high > Decimal(101)
    assert zones[0].current_role == "SUPPORT"
    assert zones[0].reaction_count == 2


def test_wave_hard_rules_generate_no_forced_impulse() -> None:
    bars = tuple(_bar(index, 100 + index) for index in range(24))
    assert generate_primary_monthly_hypotheses(bars, (), (), ticker="TEST") == ()


def test_wave_candidate_respects_running_max_and_deepest_low() -> None:
    closes = [100, 105, 120, 160, 200, 180, 145, 170, 240, 320, 280, 230, 260]
    bars = tuple(_bar(index, close) for index, close in enumerate(closes))
    pivots = (
        _pivot("w0", bars[0].date, 98, "LOW"),
        _pivot("w1", bars[4].date, 202, "HIGH"),
        _pivot("w2", bars[6].date, 143, "LOW"),
        _pivot("w3", bars[9].date, 322, "HIGH", status="PROVISIONAL"),
        _pivot("w4", bars[11].date, 228, "LOW", status="PROVISIONAL"),
    )
    hypotheses = generate_primary_monthly_hypotheses(bars, pivots, (), ticker="TEST")
    assert hypotheses
    assert hypotheses[0].wave_state == "W4_CANDIDATE_W5_UNCONFIRMED"
    assert hypotheses[0].status == "VALID_PROVISIONAL"
    assert all(hypotheses[0].hard_rules.values())


def test_fibonacci_families_keep_monthly_source_and_target_separate() -> None:
    references = calculate_wave_fibonacci(
        _hypothesis(),
        ticker="TEST",
        currency="KRW",
        as_of="2026-08-26",
    )
    families = {reference.family for reference in references}
    assert families == {
        "WAVE1_RETRACEMENT",
        "WAVE3_RETRACEMENT",
        "PRIMARY_CYCLE_RETRACEMENT",
        "CURRENT_REBOUND",
        "WAVE5_PROJECTION",
    }
    weekly = next(
        reference
        for reference in references
        if reference.family == "CURRENT_REBOUND"
        and reference.confluence_target_timeframe == "weekly"
        and reference.ratio == "0.382"
    )
    assert weekly.source_timeframe == "monthly"
    assert weekly.source_degree == "PRIMARY_MONTHLY_CYCLE"
    assert weekly.status == "PROVISIONAL"
    assert weekly.calculated_price == Decimal("264.380000")


def test_wave5_projection_is_labeled_projection() -> None:
    references = calculate_wave_fibonacci(
        _hypothesis(),
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
    )
    projections = [reference for reference in references if reference.family == "WAVE5_PROJECTION"]
    assert projections
    assert all(reference.status == "PROJECTION" for reference in projections)
    assert {reference.method_family for reference in projections} == {
        "WAVE1_MULTIPLE",
        "WAVE3_MULTIPLE",
        "SPAN03_MULTIPLE",
    }


def test_correlated_fib_ratios_do_not_inflate_independent_score() -> None:
    common = {
        "evidence_type": "FIBONACCI",
        "evidence_family": "CURRENT_REBOUND",
        "method_family": "CURRENT_REBOUND",
        "source_timeframe": "monthly",
        "source_degree": "PRIMARY_MONTHLY_CYCLE",
        "confluence_target_timeframe": "weekly",
        "status": "PROVISIONAL",
    }
    first = ZoneSource(source_id="f1", price=Decimal(100), **common)
    second = ZoneSource(source_id="f2", price=Decimal(101), **common)
    assert _source_score((first, second)) == Decimal("1.400000")


def test_cross_timeframe_confluence_preserves_source_timeframes() -> None:
    monthly_source = ZoneSource(
        source_id="m",
        evidence_type="FIBONACCI",
        evidence_family="CURRENT_REBOUND",
        method_family="CURRENT_REBOUND",
        source_timeframe="monthly",
        source_degree="PRIMARY_MONTHLY_CYCLE",
        confluence_target_timeframe="weekly",
        price=Decimal(100),
        status="PROVISIONAL",
    )
    weekly_source = ZoneSource(
        source_id="w",
        evidence_type="PIVOT",
        evidence_family="PIVOT_WEEKLY",
        method_family="PIVOT_GROUP",
        source_timeframe="weekly",
        source_degree="WEEKLY_PRICE_STRUCTURE",
        confluence_target_timeframe="weekly",
        price=Decimal(101),
        status="CONFIRMED",
    )
    weekly_map = merge_zone_sources(
        (monthly_source, weekly_source),
        ticker="TEST",
        timeframe="weekly",
        current_price=Decimal(90),
    )
    cross = build_cross_timeframe_confluence(
        {"monthly": (), "weekly": weekly_map, "daily": ()},
        ticker="TEST",
        current_price=Decimal(90),
    )
    assert cross
    assert {source.source_timeframe for source in cross[0].sources} == {"monthly", "weekly"}


def test_valid_abstention_requires_null_ids() -> None:
    valid = WaveHypothesisSelection(
        status=WaveSelectionStatus.AMBIGUOUS,
        reason_categories=("MULTIPLE_VALID",),
    )
    invalid = WaveHypothesisSelection(
        status=WaveSelectionStatus.AMBIGUOUS,
        hypothesis_id="wave:1",
        reason_categories=("MULTIPLE_VALID",),
    )
    assert validate_wave_hypothesis_selection(valid, (_hypothesis(),)).valid_abstention is True
    assert validate_wave_hypothesis_selection(invalid, (_hypothesis(),)).valid is False


def test_consensus_classification() -> None:
    selected = WaveHypothesisSelection(
        status=WaveSelectionStatus.SELECTED,
        hypothesis_id="wave:1",
        reason_categories=("HARD_RULE_FIT",),
    )
    abstain = WaveHypothesisSelection(
        status=WaveSelectionStatus.INSUFFICIENT_STRUCTURE,
        reason_categories=("INSUFFICIENT",),
    )
    assert classify_wave_selection_consensus((selected,) * 5, (_hypothesis(),)) == "STABLE"
    assert classify_wave_selection_consensus((abstain,) * 3, (_hypothesis(),)) == "VALID_ABSTENTION"
    assert classify_wave_selection_consensus((selected, abstain), (_hypothesis(),)) == "MATERIAL_VARIATION"


def test_end_to_end_shadow_has_zero_mutation_and_hierarchical_render() -> None:
    raw = [_raw(f"{2020 + index // 12:04d}-{index % 12 + 1:02d}-01", 100 + index) for index in range(80)]
    result = build_price_structure_wave_fib_v3(
        ticker="TEST",
        security_id="TEST",
        market="US",
        currency="USD",
        adjustment_basis="adjusted_close",
        cutoff="2026-08-26",
        raw_by_timeframe={"daily": raw, "weekly": raw, "monthly": raw},
        provider_limit=None,
    )
    assert result.user_visible is False
    assert result.business_thesis_mutation is False
    assert result.official_assessment_mutation is False
    monthly = result.shadow_render.index("월봉 — 구조")
    weekly = result.shadow_render.index("주봉 — 중기")
    daily = result.shadow_render.index("일봉 — 단기")
    summary = result.shadow_render.index("종합")
    assert monthly < weekly < daily < summary


def test_ai_packet_has_no_fibonacci_or_sr_prices() -> None:
    result = build_price_structure_wave_fib_v3(
        ticker="TEST",
        security_id="TEST",
        market="KR",
        currency="KRW",
        adjustment_basis="adjusted_close",
        cutoff="2026-08-26",
        raw_by_timeframe={"daily": (), "weekly": (), "monthly": ()},
    )
    packet = wave_hypothesis_packet(result, monthly_bars=(), weekly_pivots=())
    serialized = str(packet).lower()
    assert "calculated_price" not in serialized
    assert "zone_low" not in serialized
    assert "zone_high" not in serialized
    assert "fibonacci" in serialized  # prohibition is explicit, no numeric output exists.


def test_fibonacci_reference_requires_source_degree_and_target() -> None:
    reference = FibonacciReference(
        fib_id="fib:1",
        ticker="TEST",
        currency="USD",
        source_timeframe="monthly",
        source_degree="PRIMARY_MONTHLY_CYCLE",
        confluence_target_timeframe="daily",
        wave_hypothesis_id="wave:1",
        family="CURRENT_REBOUND",
        method_family="CURRENT_REBOUND",
        ratio="0.382",
        endpoint_refs=("p3", "p4"),
        formula="W4+(W3-W4)*ratio",
        calculated_price=Decimal(100),
        status="PROVISIONAL",
        as_of="2026-08-26",
    )
    assert reference.source_timeframe == "monthly"
    assert reference.confluence_target_timeframe == "daily"
