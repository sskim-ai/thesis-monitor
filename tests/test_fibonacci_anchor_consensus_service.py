from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.services.fibonacci_anchor_consensus_service import (
    CANDIDATE_LIMITS,
    PACKET_CONTRACT,
    CanonicalSwingStructureCandidate,
    ConsensusStabilityClass,
    VariableAISwingConsensusOutput,
    VariableSwingStructureSelection,
    audit_consensus_packet_egress,
    build_price_only_ai_swing_consensus_packet,
    classify_swing_structure_consensus,
    execute_variable_swing_consensus_selector,
    generate_canonical_swing_structure_candidates,
    validate_variable_ai_swing_consensus_output,
)
from app.services.multi_timeframe_price_structure_service import (
    PivotEvidence,
    build_price_structure_evidence_packet,
)
from app.services.variable_ai_anchor_selection_service import (
    build_price_only_ai_anchor_packet,
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


def _zone(timeframe: str, pivot_type: str, low: float, high: float) -> dict:
    return {
        "zone_low": low,
        "zone_high": high,
        "center": (low + high) / 2,
        "pivot_type": pivot_type,
        "pivot_dates": ["2025-01-01"],
        "pivot_prices": [(low + high) / 2],
        "timeframe": timeframe,
        "strength": "Strong",
        "score": 9,
    }


def _structure(*, future_daily: bool = False) -> dict:
    daily_confirmed = "2026-09-01" if future_daily else "2026-08-20"
    return {
        "algorithm_version": "ohlcv-structure-v2",
        "as_of_date": "2026-08-25",
        "price_basis": "adjusted_close",
        "all_zones": [
            _zone("monthly", "low", 90, 100),
            _zone("monthly", "high", 190, 200),
            _zone("weekly", "low", 125, 130),
            _zone("weekly", "high", 170, 175),
            _zone("daily", "low", 145, 147),
            _zone("daily", "high", 155, 157),
        ],
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


def _bars() -> dict[str, list[dict[str, object]]]:
    dates = {
        "monthly": ["2020-01-01", "2023-01-01", "2024-01-01", "2026-08-01"],
        "weekly": ["2025-01-06", "2025-10-06", "2026-02-02", "2026-08-24"],
        "daily": ["2026-05-01", "2026-07-01", "2026-08-01", "2026-08-25"],
    }
    return {
        timeframe: [
            {
                "date": date,
                "open": 100 + index * 10,
                "high": 110 + index * 10,
                "low": 90 + index * 10,
                "close": 105 + index * 10,
                "volume": 1_000 + index * 100,
                "trading_value": 100_000 + index * 10_000,
            }
            for index, date in enumerate(items)
        ]
        for timeframe, items in dates.items()
    }


def _base_packet(*, future_daily: bool = False):
    source = build_price_structure_evidence_packet(
        ticker="TEST",
        security_id="security:test",
        currency="USD",
        current_price=150,
        structure=_structure(future_daily=future_daily),
        cutoff="2026-08-25",
        compact=False,
    )
    return build_price_only_ai_anchor_packet(source, _bars(), market="US")


def _packet(*, future_daily: bool = False):
    return build_price_only_ai_swing_consensus_packet(
        _base_packet(future_daily=future_daily)
    )


def _selected(candidate: CanonicalSwingStructureCandidate) -> VariableSwingStructureSelection:
    return VariableSwingStructureSelection(
        status="SELECTED",
        swing_structure_id=candidate.swing_structure_id,
        confidence="MEDIUM",
        reason_categories=("MAJOR_BASE",),
        evidence_refs=tuple(
            item
            for item in (
                candidate.low_pivot_id,
                candidate.high_pivot_id,
                candidate.correction_low_pivot_id,
            )
            if item is not None
        ),
        concise_reason="Canonical candidate fits the bounded timeframe role.",
    )


def _output(packet=None) -> VariableAISwingConsensusOutput:
    packet = packet or _packet()
    values = {}
    for timeframe in ("monthly", "weekly", "daily"):
        candidates = getattr(packet, timeframe).swing_structure_candidates
        values[timeframe] = (
            _selected(candidates[0])
            if candidates
            else VariableSwingStructureSelection(
                status="INSUFFICIENT_STRUCTURE",
                confidence="LOW",
                reason_categories=("AMBIGUOUS_COMPETING_SWINGS",),
            )
        )
    return VariableAISwingConsensusOutput(ticker=packet.ticker, **values)


def _select_candidate(packet, output, timeframe: str, candidate):
    changed = _selected(candidate)
    return output.model_copy(update={timeframe: changed})


def test_packet_contains_deterministic_sr_and_bounded_canonical_candidates() -> None:
    packet = _packet()

    assert packet.contract == PACKET_CONTRACT
    for timeframe in ("monthly", "weekly", "daily"):
        value = getattr(packet, timeframe)
        assert value.deterministic_sr.owner == "DETERMINISTIC_BACKEND"
        assert value.deterministic_sr.primary_support_zone_id is not None
        assert value.swing_structure_candidates
        assert len(value.swing_structure_candidates) <= CANDIDATE_LIMITS[timeframe]
        assert value.candidate_audit.valid_structure_count >= len(
            value.swing_structure_candidates
        )


def test_stage_one_output_schema_has_no_sr_anchor_or_numeric_fields() -> None:
    schema = VariableSwingStructureSelection.model_json_schema()
    properties = schema["properties"]

    assert "support_zone_id" not in properties
    assert "resistance_zone_id" not in properties
    assert "low_pivot_id" not in properties
    assert "high_pivot_id" not in properties
    assert "anchor_price" not in properties
    with pytest.raises(ValidationError):
        VariableSwingStructureSelection.model_validate(
            {
                **_selected(_packet().daily.swing_structure_candidates[0]).model_dump(),
                "support_zone_id": "forbidden",
            }
        )


def test_candidate_generation_is_deterministic_and_extension_is_distinct() -> None:
    packet = _base_packet()
    first, first_audit = generate_canonical_swing_structure_candidates(packet, "monthly")
    second, second_audit = generate_canonical_swing_structure_candidates(packet, "monthly")

    assert first == second
    assert first_audit == second_audit
    assert {item.mode_eligibility for item in first} == {"RETRACEMENT", "BOTH"}
    assert len({item.swing_structure_id for item in first}) == len(first)


def test_future_unconfirmed_pivot_never_enters_candidate_set() -> None:
    packet = _packet(future_daily=True)

    assert all(
        "2026-08-01" not in candidate.chronology
        for candidate in packet.daily.swing_structure_candidates
    )


def test_valid_structure_id_is_accepted_and_backend_calculates_fibonacci() -> None:
    packet = _packet()
    output = _output(packet)
    result = execute_variable_swing_consensus_selector(packet, lambda _: output)

    assert validate_variable_ai_swing_consensus_output(packet, output).valid is True
    assert result.status == "PASS"
    assert result.shadow.fibonacci["monthly"]
    assert result.selection.monthly.support_zone_id == (
        packet.monthly.deterministic_sr.primary_support_zone_id
    )


def test_invalid_structure_id_rejects_only_affected_timeframe() -> None:
    packet = _packet()
    output = _output(packet)
    invalid = output.daily.model_copy(update={"swing_structure_id": "unknown"})
    result = execute_variable_swing_consensus_selector(
        packet,
        lambda _: output.model_copy(update={"daily": invalid}),
    )

    assert result.validation.timeframe_status == {
        "monthly": "PASS",
        "weekly": "PASS",
        "daily": "REJECTED",
    }
    assert result.shadow.fibonacci["monthly"]
    assert result.shadow.fibonacci["weekly"]
    assert result.shadow.fibonacci["daily"] == ()
    assert result.selection.daily.support_zone_id is not None


@pytest.mark.parametrize("status", ("AMBIGUOUS", "INSUFFICIENT_STRUCTURE"))
def test_schema_valid_abstention_preserves_sr_and_is_not_rejected(status: str) -> None:
    packet = _packet()
    output = _output(packet)
    abstention = VariableSwingStructureSelection(
        status=status,
        confidence="LOW",
        reason_categories=("AMBIGUOUS_COMPETING_SWINGS",),
        evidence_refs=(packet.daily.evidence.pivots[0].pivot_id,),
        concise_reason="Competing structures remain unresolved.",
    )
    result = execute_variable_swing_consensus_selector(
        packet,
        lambda _: output.model_copy(update={"daily": abstention}),
    )

    assert result.status == "PASS"
    assert result.validation.timeframe_status["daily"] == "VALID_ABSTENTION"
    assert result.selection.daily.support_zone_id is not None
    assert result.shadow.fibonacci["daily"] == ()


def test_abstention_with_structure_id_is_true_semantic_rejection() -> None:
    packet = _packet()
    output = _output(packet)
    invalid = output.daily.model_copy(update={"status": "AMBIGUOUS"})
    validation = validate_variable_ai_swing_consensus_output(
        packet,
        output.model_copy(update={"daily": invalid}),
    )

    assert validation.timeframe_status["daily"] == "REJECTED"
    assert "daily:abstention_primary_structure_present" in validation.errors


def test_abstention_evidence_ref_must_belong_to_same_timeframe() -> None:
    packet = _packet()
    output = _output(packet)
    invalid = VariableSwingStructureSelection(
        status="AMBIGUOUS",
        confidence="LOW",
        reason_categories=("AMBIGUOUS_COMPETING_SWINGS",),
        evidence_refs=(packet.monthly.evidence.pivots[0].pivot_id,),
    )
    validation = validate_variable_ai_swing_consensus_output(
        packet,
        output.model_copy(update={"daily": invalid}),
    )

    assert validation.timeframe_status["daily"] == "REJECTED"
    assert "daily:evidence_ref_invalid" in validation.errors


@pytest.mark.parametrize(
    "selector",
    (
        lambda _: (_ for _ in ()).throw(TimeoutError()),
        lambda _: "not-json",
        lambda _: {"contract": "wrong"},
    ),
)
def test_malformed_or_failed_runtime_preserves_all_deterministic_sr(selector) -> None:
    result = execute_variable_swing_consensus_selector(_packet(), selector)

    assert result.status == "FAIL_CLOSED"
    assert result.packet_continues is True
    assert result.fallback_timeframes == ("monthly", "weekly", "daily")
    assert all(
        getattr(result.selection, timeframe).support_zone_id is not None
        for timeframe in result.fallback_timeframes
    )
    assert all(not result.shadow.fibonacci[timeframe] for timeframe in result.fallback_timeframes)


def test_deterministic_sr_is_identical_across_different_ai_structures() -> None:
    packet = _packet()
    output = _output(packet)
    candidates = packet.monthly.swing_structure_candidates
    first = execute_variable_swing_consensus_selector(packet, lambda _: output)
    second = execute_variable_swing_consensus_selector(
        packet,
        lambda _: _select_candidate(packet, output, "monthly", candidates[-1]),
    )

    assert first.selection.monthly.support_zone_id == second.selection.monthly.support_zone_id
    assert first.selection.monthly.resistance_zone_id == (
        second.selection.monthly.resistance_zone_id
    )


@pytest.mark.parametrize("run_count", (3, 5))
def test_repeated_same_structure_is_stable(run_count: int) -> None:
    packet = _packet()
    output = _output(packet)
    runs = [
        execute_variable_swing_consensus_selector(packet, lambda _: output)
        for _ in range(run_count)
    ]
    decision = classify_swing_structure_consensus(packet, runs)

    assert decision.monthly.classification == ConsensusStabilityClass.STABLE
    assert decision.monthly.consensus_structure_id is not None
    assert decision.price_structure_eligibility.monthly.fib == "ELIGIBLE"


def _packet_with_extra_low(packet, timeframe: str, *, price: str):
    source = getattr(packet, timeframe).evidence
    original = next(item for item in source.pivots if item.kind == "low")
    extra = PivotEvidence(
        pivot_id=f"{original.pivot_id}:alternate:{price}",
        ticker=original.ticker,
        timeframe=original.timeframe,
        kind="low",
        date="2020-02-01" if timeframe == "monthly" else "2026-05-02",
        confirmed_at="2020-03-02" if timeframe == "monthly" else "2026-05-16",
        price=Decimal(price),
        adjustment_basis=original.adjustment_basis,
        source_ref=f"{original.source_ref}:alternate",
    )
    base = _base_packet().model_copy(
        update={timeframe: source.model_copy(update={"pivots": (*source.pivots, extra)})}
    )
    return build_price_only_ai_swing_consensus_packet(base), extra


def _candidate_for_low(packet, timeframe: str, low_id: str):
    return next(
        item
        for item in getattr(packet, timeframe).swing_structure_candidates
        if item.low_pivot_id == low_id and item.mode_eligibility == "RETRACEMENT"
    )


def test_equivalent_structures_use_existing_tolerance_and_are_minor() -> None:
    packet, extra = _packet_with_extra_low(_packet(), "monthly", price="50.1")
    output = _output(packet)
    original = next(item for item in packet.monthly.evidence.pivots if item.kind == "low")
    first_output = _select_candidate(
        packet,
        output,
        "monthly",
        _candidate_for_low(packet, "monthly", original.pivot_id),
    )
    second_output = _select_candidate(
        packet,
        output,
        "monthly",
        _candidate_for_low(packet, "monthly", extra.pivot_id),
    )
    runs = [
        execute_variable_swing_consensus_selector(packet, lambda _: first_output),
        execute_variable_swing_consensus_selector(packet, lambda _: second_output),
    ]
    decision = classify_swing_structure_consensus(packet, runs)

    assert decision.monthly.classification == ConsensusStabilityClass.MINOR_VARIATION
    assert decision.price_structure_eligibility.monthly.fib == "ELIGIBLE"


def test_material_structure_variation_is_omitted_without_removing_sr() -> None:
    packet, extra = _packet_with_extra_low(_packet(), "monthly", price="80")
    output = _output(packet)
    original = next(item for item in packet.monthly.evidence.pivots if item.kind == "low")
    outputs = [
        _select_candidate(
            packet,
            output,
            "monthly",
            _candidate_for_low(packet, "monthly", original.pivot_id),
        ),
        _select_candidate(
            packet,
            output,
            "monthly",
            _candidate_for_low(packet, "monthly", extra.pivot_id),
        ),
    ]
    runs = [
        execute_variable_swing_consensus_selector(packet, lambda _, value=value: value)
        for value in outputs
    ]
    decision = classify_swing_structure_consensus(packet, runs)

    assert decision.monthly.classification == ConsensusStabilityClass.MATERIAL_VARIATION
    assert decision.price_structure_eligibility.monthly.fib == "OMIT_UNSTABLE"
    assert decision.price_structure_eligibility.monthly.sr == "ELIGIBLE"
    assert decision.unstable_fib_user_visible_eligible == 0
    assert decision.price_structure_eligibility.weekly.fib == "ELIGIBLE"


def test_selected_and_abstention_mix_is_safe_valid_abstention() -> None:
    packet = _packet()
    output = _output(packet)
    abstention = output.model_copy(
        update={
            "daily": VariableSwingStructureSelection(
                status="AMBIGUOUS",
                confidence="LOW",
                reason_categories=("AMBIGUOUS_COMPETING_SWINGS",),
            )
        }
    )
    runs = [
        execute_variable_swing_consensus_selector(packet, lambda _: output),
        execute_variable_swing_consensus_selector(packet, lambda _: abstention),
    ]
    decision = classify_swing_structure_consensus(packet, runs)

    assert decision.daily.classification == ConsensusStabilityClass.VALID_ABSTENTION
    assert decision.price_structure_eligibility.daily.fib == "OMIT_AMBIGUOUS"
    assert decision.price_structure_eligibility.daily.sr == "ELIGIBLE"


def test_candidate_limit_records_every_omission() -> None:
    base = _base_packet()
    evidence = base.daily
    original_low = next(item for item in evidence.pivots if item.kind == "low")
    extras = tuple(
        original_low.model_copy(
            update={
                "pivot_id": f"extra-low-{index}",
                "date": f"2026-05-{index + 2:02d}",
                "confirmed_at": f"2026-05-{index + 16:02d}",
                "price": Decimal(120 + index),
            }
        )
        for index in range(8)
    )
    expanded = base.model_copy(
        update={"daily": evidence.model_copy(update={"pivots": (*evidence.pivots, *extras)})}
    )
    candidates, audit = generate_canonical_swing_structure_candidates(expanded, "daily")

    assert len(candidates) == CANDIDATE_LIMITS["daily"]
    assert audit.omitted_structure_count > 0
    assert len(audit.omitted_structures) == audit.omitted_structure_count


def test_kr_and_us_share_the_same_consensus_contract() -> None:
    us = _packet()
    kr = us.model_copy(update={"market": "KR", "currency": "KRW"})

    assert set(us.model_dump()) == set(kr.model_dump())
    assert audit_consensus_packet_egress(kr)["status"] == "PASS"
