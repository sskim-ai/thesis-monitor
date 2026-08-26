from __future__ import annotations

from decimal import Decimal

from app.services.price_structure_v3_family_consensus_service import (
    FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY,
    FamilyStability,
    apply_family_consensus_feedback,
    build_wave_hypothesis_equivalence_classes,
    equivalence_class_members,
    evaluate_fib_family_consensus,
    selection_consensus_universe,
    validate_fib_family_dependency_registry,
)
from app.services.price_structure_wave_fibonacci_v3_service import (
    MonthlyWaveHypothesis,
    PriceStructureWaveFibV3Result,
    TechnicalZone,
    WaveEndpoint,
    WaveHypothesisSelection,
    WaveSelectionStatus,
    ZoneSource,
    calculate_wave_fibonacci,
    validate_wave_hypothesis_selection,
)


def _hypothesis(
    identifier: str,
    *,
    ticker: str = "TEST",
    degree: str = "PRIMARY_CURRENT_CYCLE",
    state: str = "W4_CANDIDATE_W5_UNCONFIRMED",
    prices: tuple[int, ...] = (100, 200, 150, 400, 260),
    refs: tuple[str, ...] | None = None,
    statuses: tuple[str, ...] | None = None,
) -> MonthlyWaveHypothesis:
    labels = ("W0", "W1", "W2", "W3", "W4", "W5")[: len(prices)]
    refs = refs or tuple(f"{identifier}:{label}" for label in labels)
    statuses = statuses or tuple("CONFIRMED" for _ in labels)
    endpoints = tuple(
        WaveEndpoint(
            label=label,  # type: ignore[arg-type]
            pivot_ref=ref,
            date=f"202{index + 1}-01-01",
            price=Decimal(price),
            status=status,  # type: ignore[arg-type]
        )
        for index, (label, ref, price, status) in enumerate(
            zip(labels, refs, prices, statuses, strict=True)
        )
    )
    return MonthlyWaveHypothesis(
        hypothesis_id=identifier,
        ticker=ticker,
        source_degree=degree,  # type: ignore[arg-type]
        status=(
            "VALID_PROVISIONAL"
            if "PROVISIONAL" in statuses
            else "VALID_CONFIRMED"
        ),
        wave_state=state,  # type: ignore[arg-type]
        endpoints=endpoints,
        hard_rules={"fixture": True},
        score=Decimal("1"),
        score_components={"fixture": Decimal("1")},
    )


def _selection(
    hypothesis: MonthlyWaveHypothesis,
    *,
    alternative: str | None = None,
) -> WaveHypothesisSelection:
    return WaveHypothesisSelection(
        status=WaveSelectionStatus.SELECTED,
        hypothesis_id=hypothesis.hypothesis_id,
        alternative_hypothesis_id=alternative,
        confidence="MEDIUM",
        reason_categories=("STRUCTURE_FIT",),
        ticker=hypothesis.ticker,
        source_degree=hypothesis.source_degree,
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
        endpoint_refs=tuple(point.pivot_ref for point in hypothesis.endpoints),
    )


def _family(evaluation, family: str, method: str):
    return next(
        item
        for item in evaluation.families
        if item.family == family and item.method_family == method
    )


def _result(hypotheses: tuple[MonthlyWaveHypothesis, ...]) -> PriceStructureWaveFibV3Result:
    maps: dict[str, tuple[TechnicalZone, ...]] = {}
    for timeframe in ("monthly", "weekly", "daily"):
        source = ZoneSource(
            source_id=f"pivot:{timeframe}",
            evidence_type="PIVOT",
            evidence_family=f"PIVOT_{timeframe.upper()}",
            method_family="LOCAL_EXTREMA",
            source_timeframe=timeframe,  # type: ignore[arg-type]
            source_degree=f"{timeframe.upper()}_PRICE_STRUCTURE",
            confluence_target_timeframe=timeframe,  # type: ignore[arg-type]
            price=Decimal("300"),
            status="CONFIRMED",
        )
        maps[timeframe] = (
            TechnicalZone(
                zone_id=f"zone:{timeframe}",
                ticker="TEST",
                timeframe=timeframe,  # type: ignore[arg-type]
                low=Decimal("299"),
                high=Decimal("301"),
                center=Decimal("300"),
                current_role="RESISTANCE",
                structural_importance=10,
                proximity_pct=Decimal("0.2"),
                evidence_family_score=Decimal("1"),
                confirmation_quality=Decimal("1"),
                reaction_count=1,
                last_meaningful_interaction=None,
                sources=(source,),
            ),
        )
    return PriceStructureWaveFibV3Result(
        ticker="TEST",
        security_id="TEST:NASDAQ",
        market="US",
        currency="USD",
        adjustment_basis="adjusted_close",
        as_of="2026-08-26",
        current_price=Decimal("250"),
        coverage={},
        pivots={},
        sr_maps=maps,  # type: ignore[arg-type]
        primary_monthly_hypotheses=hypotheses,
        selected_hypothesis_id=None,
        primary_hypothesis_status="AMBIGUOUS",
        fibonacci=(),
        timeframe_zone_maps=maps,  # type: ignore[arg-type]
        cross_timeframe_confluence=(),
        shadow_render="baseline",
        computation_ms=Decimal("1"),
    )


def test_dependency_registry_covers_every_current_formula() -> None:
    hypothesis = _hypothesis("A")
    references = calculate_wave_fibonacci(
        hypothesis,
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
    )
    keys = {
        f"{item.family}:{item.method_family}"
        for item in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY
    }
    assert {
        f"{item.family}:{item.method_family}" for item in references
    } == keys
    assert validate_fib_family_dependency_registry(references) == ()
    assert all(item.required_endpoint_labels for item in references)


def test_unknown_family_and_formula_version_fail_closed() -> None:
    reference = calculate_wave_fibonacci(
        _hypothesis("A"), ticker="TEST", currency="USD", as_of="2026-08-26"
    )[0]
    unknown = reference.model_copy(update={"family": "UNKNOWN"})
    stale = reference.model_copy(update={"calculation_version": "stale-version"})
    assert validate_fib_family_dependency_registry((unknown,)) == (
        "unknown_family:UNKNOWN:WAVE1_RETRACEMENT",
    )
    assert validate_fib_family_dependency_registry((stale,)) == (
        f"formula_version_mismatch:{stale.fib_id}",
    )


def test_w0_only_ambiguity_preserves_w0_independent_families() -> None:
    shared = ("a:w1", "a:w2", "a:w3", "a:w4")
    first = _hypothesis("A", refs=("a:w0", *shared))
    second = _hypothesis("B", prices=(80, 200, 150, 400, 260), refs=("b:w0", *shared))
    evaluation = evaluate_fib_family_consensus(
        (first, second),
        (first.hypothesis_id, second.hypothesis_id),
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
        current_price=Decimal("250"),
    )
    assert _family(evaluation, "CURRENT_REBOUND", "CURRENT_REBOUND").stability == (
        FamilyStability.EXACT_INVARIANT
    )
    assert _family(evaluation, "WAVE3_RETRACEMENT", "WAVE3_RETRACEMENT").eligible
    assert not _family(
        evaluation, "PRIMARY_CYCLE_RETRACEMENT", "PRIMARY_CYCLE_RETRACEMENT"
    ).eligible
    assert not _family(evaluation, "WAVE5_PROJECTION", "WAVE1_MULTIPLE").eligible
    assert _family(evaluation, "WAVE5_PROJECTION", "WAVE3_MULTIPLE").eligible


def test_price_equivalent_uses_existing_tolerance_without_exact_match() -> None:
    first = _hypothesis("A")
    second = _hypothesis(
        "B",
        prices=(100, 200, 150, 402, 260),
        refs=("A:W0", "A:W1", "A:W2", "B:W3", "A:W4"),
    )
    evaluation = evaluate_fib_family_consensus(
        (first, second),
        ("A", "B"),
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
        current_price=Decimal("100"),
    )
    assert _family(evaluation, "CURRENT_REBOUND", "CURRENT_REBOUND").stability == (
        FamilyStability.PRICE_EQUIVALENT
    )


def test_confirmation_status_difference_is_not_price_equivalent() -> None:
    first = _hypothesis("A")
    second = _hypothesis(
        "B",
        refs=tuple(point.pivot_ref for point in first.endpoints),
        statuses=("CONFIRMED", "CONFIRMED", "CONFIRMED", "PROVISIONAL", "CONFIRMED"),
    )
    evaluation = evaluate_fib_family_consensus(
        (first, second),
        ("A", "B"),
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
        current_price=Decimal("250"),
    )
    assert _family(evaluation, "CURRENT_REBOUND", "CURRENT_REBOUND").stability == (
        FamilyStability.MATERIAL_VARIATION
    )


def test_equivalence_classes_never_merge_degrees_or_active_conflicts() -> None:
    first = _hypothesis("A")
    same_active = _hypothesis(
        "B",
        prices=(80, 200, 150, 400, 260),
        refs=("B:W0", "A:W1", "A:W2", "A:W3", "A:W4"),
    )
    grand = _hypothesis("G", degree="GRAND_CYCLE")
    conflict = _hypothesis("C", prices=(100, 200, 150, 500, 300))
    classes = build_wave_hypothesis_equivalence_classes(
        (first, same_active, grand, conflict)
    )
    assert any(set(item.member_hypothesis_ids) == {"A", "B"} for item in classes)
    assert all(not ({"A", "G"} <= set(item.member_hypothesis_ids)) for item in classes)
    assert all(not ({"A", "C"} <= set(item.member_hypothesis_ids)) for item in classes)


def test_ambiguous_candidate_ids_validate_and_backend_never_selects_member() -> None:
    first = _hypothesis("A")
    second = _hypothesis(
        "B",
        prices=(80, 200, 150, 400, 260),
        refs=("B:W0", "A:W1", "A:W2", "A:W3", "A:W4"),
    )
    classes = build_wave_hypothesis_equivalence_classes((first, second))
    class_id = next(
        item.equivalence_class_id for item in classes if len(item.member_hypothesis_ids) == 2
    )
    selection = WaveHypothesisSelection(
        status=WaveSelectionStatus.AMBIGUOUS,
        competing_hypothesis_ids=("A", "B"),
        equivalence_class_id=class_id,
        confidence="HIGH",
        reason_categories=("MULTIPLE_VALID",),
        ticker="TEST",
        source_degree="PRIMARY_CURRENT_CYCLE",
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
    )
    validation = validate_wave_hypothesis_selection(
        selection,
        (first, second),
        ticker="TEST",
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
        strict_context=True,
        equivalence_class_members=equivalence_class_members(classes),
    )
    assert validation.valid
    optional_context = selection.model_copy(
        update={"source_degree": None, "cutoff": None, "adjustment_basis": None}
    )
    assert validate_wave_hypothesis_selection(
        optional_context,
        (first, second),
        ticker="TEST",
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
        strict_context=True,
        equivalence_class_members=equivalence_class_members(classes),
    ).valid
    ids, errors = selection_consensus_universe(
        (selection,),
        (first, second),
        ticker="TEST",
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
        classes=classes,
    )
    assert ids == ("A", "B")
    assert errors == ()
    applied = apply_family_consensus_feedback(_result((first, second)), (selection,))
    assert applied.selected_hypothesis_id is None
    assert applied.primary_hypothesis_status == "AMBIGUOUS"


def test_invalid_ambiguity_ids_degree_and_class_are_rejected() -> None:
    current = _hypothesis("A")
    grand = _hypothesis("G", degree="GRAND_CYCLE")
    selection = WaveHypothesisSelection(
        status=WaveSelectionStatus.AMBIGUOUS,
        competing_hypothesis_ids=("A", "G"),
        confidence="LOW",
        reason_categories=("MULTIPLE_VALID",),
        ticker="TEST",
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
    )
    validation = validate_wave_hypothesis_selection(selection, (current, grand))
    assert "competing_degree_mismatch" in validation.errors
    unknown = selection.model_copy(update={"competing_hypothesis_ids": ("A", "NOPE")})
    assert "unknown_competing_hypothesis_id" in validate_wave_hypothesis_selection(
        unknown, (current, grand)
    ).errors

    other_ticker = _hypothesis("O", ticker="OTHER")
    wrong_ticker = selection.model_copy(
        update={"competing_hypothesis_ids": ("A", "O")}
    )
    assert "competing_ticker_mismatch" in validate_wave_hypothesis_selection(
        wrong_ticker, (current, other_ticker)
    ).errors

    classes = build_wave_hypothesis_equivalence_classes((current, grand))
    current_class = next(
        item for item in classes if item.member_hypothesis_ids == ("A",)
    )
    wrong_class = selection.model_copy(
        update={"equivalence_class_id": current_class.equivalence_class_id}
    )
    assert "competing_equivalence_class_mismatch" in validate_wave_hypothesis_selection(
        wrong_class,
        (current, grand),
        equivalence_class_members=equivalence_class_members(classes),
    ).errors


def test_insufficient_structure_needs_no_candidate_ids() -> None:
    selection = WaveHypothesisSelection(
        status=WaveSelectionStatus.INSUFFICIENT_STRUCTURE,
        confidence="HIGH",
        reason_categories=("NO_VALID_STRUCTURE",),
    )
    validation = validate_wave_hypothesis_selection(selection, ())
    assert validation.valid and validation.valid_abstention


def test_tsla_true_active_conflict_stays_material_and_fib_is_filtered() -> None:
    first = _hypothesis("A")
    second = _hypothesis("B", prices=(60, 260, 120, 600, 180))
    selections = (_selection(first), _selection(second))
    applied = apply_family_consensus_feedback(_result((first, second)), selections)
    audit = applied.family_consensus_audit
    assert audit is not None
    assert audit["full_hypothesis_stability"] == "MATERIAL_VARIATION"
    assert all(item.family_stability is not None for item in applied.fibonacci)
    assert not any(
        source.evidence_type == "FIBONACCI" and source.family_stability is None
        for zones in applied.timeframe_zone_maps.values()
        for zone in zones
        for source in zone.sources
    )
    assert any(
        source.evidence_type == "PIVOT"
        for zones in applied.timeframe_zone_maps.values()
        for zone in zones
        for source in zone.sources
    )


def test_tsm_w3_conflict_contaminates_only_w3_dependent_families() -> None:
    first = _hypothesis("A")
    second = _hypothesis(
        "B",
        prices=(100, 200, 150, 800, 260),
        refs=("A:W0", "A:W1", "A:W2", "B:W3", "A:W4"),
    )
    evaluation = evaluate_fib_family_consensus(
        (first, second),
        ("A", "B"),
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
        current_price=Decimal("250"),
    )
    assert not _family(evaluation, "WAVE3_RETRACEMENT", "WAVE3_RETRACEMENT").eligible
    assert not _family(evaluation, "CURRENT_REBOUND", "CURRENT_REBOUND").eligible
    assert _family(evaluation, "WAVE1_RETRACEMENT", "WAVE1_RETRACEMENT").eligible


def test_grand_cycle_is_monthly_long_horizon_context_only() -> None:
    grand = _hypothesis("G", degree="GRAND_CYCLE")
    evaluation = evaluate_fib_family_consensus(
        (grand,),
        ("G",),
        ticker="TEST",
        currency="USD",
        as_of="2026-08-26",
        current_price=Decimal("250"),
    )
    assert {item.confluence_target_timeframe for item in evaluation.eligible_fibonacci} == {
        "monthly"
    }
    assert all(
        item.user_role == "LONG_HORIZON_CONTEXT"
        for item in evaluation.families
        if item.eligible
    )


def test_stable_selection_remains_stable_and_abstention_is_not_forced() -> None:
    hypothesis = _hypothesis("A")
    stable = apply_family_consensus_feedback(_result((hypothesis,)), (_selection(hypothesis),))
    assert stable.family_consensus_audit is not None
    assert stable.family_consensus_audit["full_hypothesis_stability"] == "STABLE"
    assert stable.fibonacci

    abstention = WaveHypothesisSelection(
        status=WaveSelectionStatus.INSUFFICIENT_STRUCTURE,
        confidence="HIGH",
        reason_categories=("NO_VALID_STRUCTURE",),
    )
    abstained = apply_family_consensus_feedback(_result((hypothesis,)), (abstention,))
    assert abstained.selected_hypothesis_id is None
    assert abstained.fibonacci == ()
    assert abstained.family_consensus_audit is not None
    assert abstained.family_consensus_audit["full_hypothesis_stability"] == (
        "VALID_ABSTENTION"
    )
