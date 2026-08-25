from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.services.multi_timeframe_price_structure_service import (
    CONTRACT_VERSION,
    ConfluenceContributor,
    FibonacciLevel,
    MultiTimeframeSelection,
    PivotEvidence,
    PriceStructureEvidencePacket,
    TimeframeEvidence,
    TimeframeSelection,
    ZoneEvidence,
    build_price_structure_evidence_packet,
    build_shadow_price_structure_result,
    calculate_multi_timeframe_confluence,
    calculate_timeframe_fibonacci,
    reference_select_price_structure,
    render_shadow_price_structure,
    select_relevant_fibonacci_levels,
    validate_price_structure_selection,
)


def _swing(timeframe: str, kind: str, date: str, price: float, confirmed_at: str) -> dict:
    return {
        "index": 1,
        "date": date,
        "price": price,
        "kind": kind,
        "timeframe": timeframe,
        "threshold": 1,
        "atr": 1,
        "pct_threshold": 0.1,
        "bars_since_previous": 3,
        "confirmed_at": confirmed_at,
    }


def _zone(
    timeframe: str,
    pivot_type: str,
    low: float,
    high: float,
    *,
    strength: str = "Medium",
    score: int = 6,
) -> dict:
    return {
        "zone_low": low,
        "zone_high": high,
        "center": (low + high) / 2,
        "pivot_type": pivot_type,
        "pivot_dates": ["2025-01-01"],
        "pivot_prices": [(low + high) / 2],
        "timeframe": timeframe,
        "strength": strength,
        "score": score,
    }


def _structure(*, future_daily: bool = False, weak_extra: bool = False) -> dict:
    daily_confirmed = "2026-09-01" if future_daily else "2026-08-20"
    zones = [
        _zone("monthly", "low", 90, 100, strength="Strong", score=10),
        _zone("monthly", "high", 190, 200, strength="Strong", score=9),
        _zone("weekly", "low", 125, 130, strength="Strong", score=8),
        _zone("weekly", "high", 170, 175, strength="Medium", score=7),
        _zone("daily", "low", 145, 147, strength="Medium", score=6),
        _zone("daily", "high", 155, 157, strength="Medium", score=6),
    ]
    if weak_extra:
        zones.append(_zone("daily", "low", 149, 149.5, strength="Weak", score=12))
    return {
        "algorithm_version": "ohlcv-structure-v2",
        "as_of_date": "2026-08-25",
        "price_basis": "adjusted_close",
        "all_zones": zones,
        "major_swings": {
            "by_timeframe": {
                "monthly": [
                    _swing("monthly", "low", "2020-01-01", 50, "2020-03-01"),
                    _swing("monthly", "high", "2023-01-01", 180, "2023-03-01"),
                    _swing("monthly", "low", "2024-01-01", 110, "2024-03-01"),
                ],
                "weekly": [
                    _swing("weekly", "low", "2025-01-06", 100, "2025-01-27"),
                    _swing("weekly", "high", "2025-10-06", 165, "2025-10-27"),
                    _swing("weekly", "low", "2026-02-02", 125, "2026-02-23"),
                ],
                "daily": [
                    _swing("daily", "low", "2026-05-01", 130, "2026-05-15"),
                    _swing("daily", "high", "2026-07-01", 160, "2026-07-15"),
                    _swing("daily", "low", "2026-08-01", 145, daily_confirmed),
                ],
            }
        },
    }


def _packet(*, compact: bool = True, future_daily: bool = False, weak_extra: bool = False):
    return build_price_structure_evidence_packet(
        ticker="TEST",
        security_id="security:test",
        currency="USD",
        current_price=150,
        structure=_structure(future_daily=future_daily, weak_extra=weak_extra),
        cutoff="2026-08-25",
        compact=compact,
    )


def test_evidence_packet_keeps_timeframe_ownership_and_hierarchy() -> None:
    packet = _packet()

    assert packet.contract == CONTRACT_VERSION
    assert packet.monthly.analytical_role == "PRIMARY_STRUCTURAL_ZONE"
    assert packet.weekly.analytical_role == "INTERMEDIATE_ZONE"
    assert packet.daily.analytical_role == "NEAREST_TACTICAL_ZONE"
    for timeframe in ("monthly", "weekly", "daily"):
        evidence = getattr(packet, timeframe)
        assert all(item.timeframe == timeframe for item in evidence.pivots)
        assert all(item.timeframe == timeframe for item in evidence.sr_candidates)


def test_evidence_hash_is_deterministic_and_mode_sensitive() -> None:
    assert _packet().evidence_sha256 == _packet().evidence_sha256
    assert _packet().evidence_sha256 != _packet(compact=False).evidence_sha256


def test_compact_omits_weak_noise_without_changing_selection() -> None:
    compact = _packet(compact=True, weak_extra=True)
    full = _packet(compact=False, weak_extra=True)

    assert compact.daily.omitted_candidate_count == 1
    assert reference_select_price_structure(compact).daily == reference_select_price_structure(full).daily


def test_lookahead_pivot_is_excluded_before_selection() -> None:
    packet = _packet(future_daily=True)

    assert all(item.date != "2026-08-01" for item in packet.daily.pivots)
    assert all(item.confirmed_at <= packet.cutoff for item in packet.daily.pivots)


def test_reference_selection_is_independent_and_stable() -> None:
    packet = _packet()
    runs = [reference_select_price_structure(packet) for _ in range(3)]

    assert runs[0] == runs[1] == runs[2]
    assert runs[0].monthly.low_pivot_id != runs[0].weekly.low_pivot_id
    assert runs[0].weekly.low_pivot_id != runs[0].daily.low_pivot_id
    assert runs[0].synthesis.primary_structural_timeframe == "monthly"
    assert runs[0].synthesis.tactical_timeframe == "daily"


def test_validator_rejects_cross_timeframe_anchor_without_invalidating_other_slots() -> None:
    packet = _packet()
    selection = reference_select_price_structure(packet)
    invalid = selection.model_copy(
        update={
            "daily": selection.daily.model_copy(
                update={"low_pivot_id": selection.monthly.low_pivot_id}
            )
        }
    )

    result = validate_price_structure_selection(packet, invalid)

    assert result.valid is False
    assert result.timeframe_status["monthly"] == "PASS"
    assert result.timeframe_status["weekly"] == "PASS"
    assert result.timeframe_status["daily"] == "REJECTED"


def test_validator_rejects_invalid_chronology_and_missing_correction() -> None:
    packet = _packet()
    selection = reference_select_price_structure(packet)
    invalid = selection.model_copy(
        update={
            "weekly": selection.weekly.model_copy(
                update={
                    "low_pivot_id": selection.weekly.high_pivot_id,
                    "high_pivot_id": selection.weekly.low_pivot_id,
                    "fib_mode": "EXTENSION",
                    "correction_low_pivot_id": None,
                }
            )
        }
    )

    result = validate_price_structure_selection(packet, invalid)

    assert "weekly:fib_anchor_kind_invalid" in result.errors
    assert "weekly:extension_correction_missing" in result.errors


@pytest.mark.parametrize("timeframe", ("monthly", "weekly", "daily"))
def test_retracement_and_extension_are_calculated_per_timeframe(timeframe: str) -> None:
    packet = _packet()
    selection = reference_select_price_structure(packet)
    levels = calculate_timeframe_fibonacci(packet, selection)[timeframe]

    assert {item.mode for item in levels} == {"RETRACEMENT", "EXTENSION"}
    assert all(item.timeframe == timeframe for item in levels)
    assert all(item.calculation_version == "deterministic-fibonacci-v2" for item in levels)
    assert all(item.low_anchor_ref and item.high_anchor_ref for item in levels)


def test_fibonacci_exact_formulas_and_provenance() -> None:
    packet = _packet()
    selection = reference_select_price_structure(packet)
    levels = calculate_timeframe_fibonacci(packet, selection)["daily"]
    indexed = {(item.mode, item.ratio): item for item in levels}

    assert indexed[("RETRACEMENT", "0.500")].calculated_price == Decimal("145.000000")
    assert indexed[("EXTENSION", "1.000")].calculated_price == Decimal("175.000000")
    assert indexed[("EXTENSION", "1.000")].correction_anchor_ref
    assert indexed[("EXTENSION", "1.000")].formula == "C + (H-L) * ratio"


def test_invalid_timeframe_fibonacci_fails_closed() -> None:
    packet = _packet()
    selection = reference_select_price_structure(packet)
    invalid = selection.model_copy(
        update={
            "daily": selection.daily.model_copy(
                update={"low_pivot_id": selection.monthly.low_pivot_id}
            )
        }
    )

    levels = calculate_timeframe_fibonacci(packet, invalid)

    assert levels["daily"] == ()
    assert levels["monthly"]
    assert levels["weekly"]


def test_relevant_fibonacci_is_limited_to_two_per_timeframe() -> None:
    packet = _packet()
    levels = calculate_timeframe_fibonacci(packet, reference_select_price_structure(packet))

    selected = select_relevant_fibonacci_levels(levels, packet.current_price)

    assert all(len(items) <= 2 for items in selected.values())


def _direct_packet() -> PriceStructureEvidencePacket:
    empty = {
        timeframe: TimeframeEvidence(
            timeframe=timeframe,
            analytical_role=role,
            status="AVAILABLE",
            as_of="2026-08-25",
        )
        for timeframe, role in (
            ("monthly", "PRIMARY_STRUCTURAL_ZONE"),
            ("weekly", "INTERMEDIATE_ZONE"),
            ("daily", "NEAREST_TACTICAL_ZONE"),
        )
    }
    return PriceStructureEvidencePacket(
        ticker="TEST",
        security_id="security:test",
        currency="USD",
        current_price=100,
        as_of="2026-08-25",
        cutoff="2026-08-25",
        adjustment_basis="adjusted_close",
        evidence_mode="COMPACT",
        evidence_sha256="a" * 64,
        monthly=empty["monthly"],
        weekly=empty["weekly"],
        daily=empty["daily"],
    )


def _fib(ref: str, timeframe: str, price: str) -> FibonacciLevel:
    return FibonacciLevel(
        level_id=ref,
        ticker="TEST",
        timeframe=timeframe,
        ratio="0.618",
        mode="RETRACEMENT",
        calculated_price=Decimal(price),
        currency="USD",
        adjustment_basis="adjusted_close",
        as_of="2026-08-25",
        low_anchor_ref=f"{ref}:low",
        high_anchor_ref=f"{ref}:high",
        formula="H - (H-L) * ratio",
    )


def _empty_selection() -> MultiTimeframeSelection:
    none = TimeframeSelection(status="SELECTED")
    return MultiTimeframeSelection(
        selection_source="test",
        monthly=none,
        weekly=none,
        daily=none,
    )


def test_cross_timeframe_fibonacci_confluence_uses_bounded_tolerance() -> None:
    packet = _direct_packet()
    selected = {
        "monthly": (_fib("m", "monthly", "100"),),
        "weekly": (_fib("w", "weekly", "101.5"),),
        "daily": (_fib("d", "daily", "101.7"),),
    }

    result = calculate_multi_timeframe_confluence(packet, _empty_selection(), selected)

    assert len(result) == 1
    assert result[0].timeframes == ("monthly", "weekly", "daily")
    assert result[0].tolerance_pct == Decimal("0.0175")
    assert result[0].zone_high - result[0].zone_low == Decimal("1.7")


def test_complete_link_prevents_transitive_giant_confluence() -> None:
    packet = _direct_packet()
    selected = {
        "monthly": (_fib("m", "monthly", "100"),),
        "weekly": (_fib("w", "weekly", "101.6"),),
        "daily": (_fib("d", "daily", "103.2"),),
    }

    result = calculate_multi_timeframe_confluence(packet, _empty_selection(), selected)

    assert all(item.zone_high - item.zone_low < Decimal("2") for item in result)
    assert not any(len(item.timeframes) == 3 for item in result)


def test_isolated_fibonacci_remains_isolated() -> None:
    packet = _direct_packet()
    selected = {
        "monthly": (_fib("m", "monthly", "80"),),
        "weekly": (_fib("w", "weekly", "100"),),
        "daily": (_fib("d", "daily", "120"),),
    }

    assert calculate_multi_timeframe_confluence(packet, _empty_selection(), selected) == ()


def test_renderer_order_density_and_semantic_safety() -> None:
    packet = _packet()
    selection = reference_select_price_structure(packet)
    result = build_shadow_price_structure_result(packet, selection)
    text = result.shadow_render

    assert text.index("월봉(구조)") < text.index("주봉(중기)") < text.index("일봉(전술)")
    assert text.rindex("종합:") > text.index("일봉(전술)")
    assert all(text.count(label) <= 3 for label in ("0.382", "0.5", "0.618", "1.618"))
    for prohibited in ("매수", "매도", "목표가", "손절", "사업 논리 강화"):
        assert prohibited not in text
    assert result.user_visible is False
    assert result.official_assessment_mutation is False


def test_each_timeframe_can_be_independently_insufficient() -> None:
    structure = _structure()
    structure["all_zones"] = [
        item for item in structure["all_zones"] if item["timeframe"] != "daily"
    ]
    structure["major_swings"]["by_timeframe"]["daily"] = []
    packet = build_price_structure_evidence_packet(
        ticker="TEST",
        security_id="security:test",
        currency="USD",
        current_price=150,
        structure=structure,
        cutoff="2026-08-25",
    )
    selection = reference_select_price_structure(packet)

    assert selection.monthly.status == "SELECTED"
    assert selection.weekly.status == "SELECTED"
    assert selection.daily.status == "INSUFFICIENT_STRUCTURE"
    assert validate_price_structure_selection(packet, selection).valid is True


def test_typed_contract_rejects_invalid_timeframe() -> None:
    with pytest.raises(ValidationError):
        PivotEvidence(
            pivot_id="x",
            ticker="TEST",
            timeframe="quarterly",
            kind="low",
            date="2026-01-01",
            confirmed_at="2026-01-02",
            price=1,
            adjustment_basis="adjusted_close",
            source_ref="x",
        )


def test_render_function_does_not_require_production_renderer() -> None:
    packet = _packet()
    selection = reference_select_price_structure(packet)
    levels = calculate_timeframe_fibonacci(packet, selection)
    selected = select_relevant_fibonacci_levels(levels, packet.current_price)

    text = render_shadow_price_structure(packet, selection, selected, ())

    assert text.endswith("독립 시간축 근거의 유의미한 가격 중첩은 확인되지 않았습니다.")


def test_confluence_contributor_is_price_fact_only() -> None:
    contributor = ConfluenceContributor(
        ref_id="level:1",
        timeframe="weekly",
        kind="FIBONACCI",
        price=Decimal("100"),
    )

    assert contributor.model_dump() == {
        "ref_id": "level:1",
        "timeframe": "weekly",
        "kind": "FIBONACCI",
        "price": Decimal("100"),
    }


def test_zone_and_selection_models_are_frozen() -> None:
    zone = ZoneEvidence(
        zone_id="z",
        ticker="TEST",
        timeframe="daily",
        role="SUPPORT",
        low=1,
        high=2,
        center=1.5,
        strength="Medium",
        score=5,
        relation_to_current="BELOW",
    )

    with pytest.raises(ValidationError):
        zone.center = Decimal("2")  # type: ignore[misc]
