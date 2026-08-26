from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from app.services.ohlcv_structure_service import Timeframe
from app.services.price_structure_wave_fibonacci_v3_service import (
    CALCULATION_VERSION,
    CONFLUENCE_PCT,
    FIB_FAMILY_DEPENDENCY_CONTRACT,
    FAMILY_CONSENSUS_CONTRACT,
    TIMEFRAME_ORDER,
    FibonacciReference,
    FrozenModel,
    MonthlyWaveHypothesis,
    PriceStructureWaveFibV3Result,
    WaveHypothesisSelection,
    WaveSelectionStatus,
    ZoneSource,
    _fib_source,
    _stable_id,
    build_cross_timeframe_confluence,
    calculate_wave_fibonacci,
    merge_zone_sources,
    render_shadow_v3,
    validate_wave_hypothesis_selection,
)


GRAND_CYCLE_USER_ROLE_POLICY = "grand-cycle-long-horizon-context-v1"
AMBIGUITY_SET_CONTRACT = "price-structure-v3-ambiguity-set-v1"
EQUIVALENCE_CLASS_CONTRACT = "wave-hypothesis-equivalence-class-v1"


class FamilyStability(StrEnum):
    EXACT_INVARIANT = "EXACT_INVARIANT"
    PRICE_EQUIVALENT = "PRICE_EQUIVALENT"
    MATERIAL_VARIATION = "MATERIAL_VARIATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INSUFFICIENT = "INSUFFICIENT"


class FibFamilyDependency(FrozenModel):
    contract: str = FIB_FAMILY_DEPENDENCY_CONTRACT
    dependency_id: str
    family: str
    method_family: str
    wave_state_applicability: tuple[str, ...]
    required_endpoint_labels: tuple[str, ...]
    formula: str
    formula_version: str = CALCULATION_VERSION
    source_degree: str = "MONTHLY_WAVE_DEGREE"

    @property
    def key(self) -> str:
        return f"{self.family}:{self.method_family}"


def _dependency(
    family: str,
    method: str,
    labels: tuple[str, ...],
    formula: str,
) -> FibFamilyDependency:
    return FibFamilyDependency(
        dependency_id=_stable_id(
            "v3-fib-dependency",
            family,
            method,
            labels,
            formula,
            CALCULATION_VERSION,
        ),
        family=family,
        method_family=method,
        wave_state_applicability=(
            "W4_CANDIDATE_W5_UNCONFIRMED",
            "W5_CANDIDATE",
        ),
        required_endpoint_labels=labels,
        formula=formula,
    )


FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY: tuple[FibFamilyDependency, ...] = (
    _dependency(
        "WAVE1_RETRACEMENT",
        "WAVE1_RETRACEMENT",
        ("W0", "W1"),
        "W1-(W1-W0)*ratio",
    ),
    _dependency(
        "WAVE3_RETRACEMENT",
        "WAVE3_RETRACEMENT",
        ("W2", "W3"),
        "W3-(W3-W2)*ratio",
    ),
    _dependency(
        "PRIMARY_CYCLE_RETRACEMENT",
        "PRIMARY_CYCLE_RETRACEMENT",
        ("W0", "W3"),
        "W3-(W3-W0)*ratio",
    ),
    _dependency(
        "CURRENT_REBOUND",
        "CURRENT_REBOUND",
        ("W3", "W4"),
        "W4+(W3-W4)*ratio",
    ),
    _dependency(
        "WAVE5_PROJECTION",
        "WAVE1_MULTIPLE",
        ("W0", "W1", "W4"),
        "W4+(W1-W0)*ratio",
    ),
    _dependency(
        "WAVE5_PROJECTION",
        "WAVE3_MULTIPLE",
        ("W2", "W3", "W4"),
        "W4+(W3-W2)*ratio",
    ),
    _dependency(
        "WAVE5_PROJECTION",
        "SPAN03_MULTIPLE",
        ("W0", "W3", "W4"),
        "W4+(W3-W0)*ratio",
    ),
)

_DEPENDENCY_BY_KEY = {item.key: item for item in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY}


class WaveHypothesisEquivalenceClass(FrozenModel):
    contract: str = EQUIVALENCE_CLASS_CONTRACT
    equivalence_class_id: str
    ticker: str
    source_degree: str
    wave_state: str
    member_hypothesis_ids: tuple[str, ...]
    shared_endpoint_refs: dict[str, str]
    divergent_endpoint_labels: tuple[str, ...]
    active_structure_signature: tuple[str, ...]
    family_dependency_status: dict[str, Literal["SHARED", "DIVERGENT", "MISSING"]]


class FibFamilyConsensus(FrozenModel):
    family_key: str
    family: str
    method_family: str
    required_endpoint_labels: tuple[str, ...]
    candidate_hypothesis_ids: tuple[str, ...]
    endpoint_refs_by_hypothesis: dict[str, tuple[str, ...]]
    calculated_values_by_hypothesis: dict[str, tuple[str, ...]]
    visible_zone_by_timeframe: dict[Timeframe, tuple[str, str]]
    stability: FamilyStability
    eligible: bool
    reason: str
    source_degree: str | None = None
    user_role: Literal["PRIMARY_CURRENT_RESISTANCE", "LONG_HORIZON_CONTEXT"] | None = None


class FamilyConsensusEvaluation(FrozenModel):
    contract: str = FAMILY_CONSENSUS_CONTRACT
    ambiguity_contract: str = AMBIGUITY_SET_CONTRACT
    consensus_set_id: str
    ticker: str
    candidate_hypothesis_ids: tuple[str, ...]
    equivalence_classes: tuple[WaveHypothesisEquivalenceClass, ...]
    full_hypothesis_stability: Literal[
        "STABLE", "MATERIAL_VARIATION", "VALID_ABSTENTION"
    ]
    family_level_price_structure: Literal["PASS", "PARTIAL", "FAIL"]
    families: tuple[FibFamilyConsensus, ...]
    eligible_fibonacci: tuple[FibonacciReference, ...]
    omitted_unstable_family_count: int
    validation_errors: tuple[str, ...] = ()


def _endpoint_map(hypothesis: MonthlyWaveHypothesis) -> dict[str, object]:
    return {point.label: point for point in hypothesis.endpoints}


def _active_labels(hypothesis: MonthlyWaveHypothesis) -> tuple[str, ...]:
    available = {point.label for point in hypothesis.endpoints}
    preferred = (
        ("W3", "W4", "W5")
        if hypothesis.wave_state == "W5_CANDIDATE"
        else ("W1", "W2", "W3", "W4")
    )
    return tuple(label for label in preferred if label in available)


def build_wave_hypothesis_equivalence_classes(
    hypotheses: Sequence[MonthlyWaveHypothesis],
) -> tuple[WaveHypothesisEquivalenceClass, ...]:
    grouped: dict[tuple[object, ...], list[MonthlyWaveHypothesis]] = defaultdict(list)
    for hypothesis in hypotheses:
        endpoints = _endpoint_map(hypothesis)
        labels = _active_labels(hypothesis)
        signature = tuple(
            f"{label}:{endpoints[label].pivot_ref}:{endpoints[label].status}"  # type: ignore[union-attr]
            for label in labels
        )
        grouped[
            (
                hypothesis.ticker,
                hypothesis.source_degree,
                hypothesis.wave_state,
                signature,
            )
        ].append(hypothesis)

    classes: list[WaveHypothesisEquivalenceClass] = []
    for (ticker, degree, wave_state, signature), members in sorted(
        grouped.items(), key=lambda item: str(item[0])
    ):
        members = sorted(members, key=lambda item: item.hypothesis_id)
        endpoint_maps = [_endpoint_map(item) for item in members]
        labels = sorted({label for mapping in endpoint_maps for label in mapping})
        shared: dict[str, str] = {}
        divergent: list[str] = []
        for label in labels:
            values = {
                (mapping[label].pivot_ref, mapping[label].status)  # type: ignore[union-attr]
                for mapping in endpoint_maps
                if label in mapping
            }
            if len(values) == 1 and all(label in mapping for mapping in endpoint_maps):
                shared[label] = next(iter(values))[0]
            else:
                divergent.append(label)
        family_status: dict[str, Literal["SHARED", "DIVERGENT", "MISSING"]] = {}
        for dependency in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY:
            if not all(
                all(label in mapping for label in dependency.required_endpoint_labels)
                for mapping in endpoint_maps
            ):
                family_status[dependency.key] = "MISSING"
            elif all(label in shared for label in dependency.required_endpoint_labels):
                family_status[dependency.key] = "SHARED"
            else:
                family_status[dependency.key] = "DIVERGENT"
        member_ids = tuple(item.hypothesis_id for item in members)
        classes.append(
            WaveHypothesisEquivalenceClass(
                equivalence_class_id=_stable_id(
                    "v3-wave-equivalence",
                    ticker,
                    degree,
                    wave_state,
                    signature,
                    member_ids,
                ),
                ticker=str(ticker),
                source_degree=str(degree),
                wave_state=str(wave_state),
                member_hypothesis_ids=member_ids,
                shared_endpoint_refs=shared,
                divergent_endpoint_labels=tuple(divergent),
                active_structure_signature=tuple(signature),  # type: ignore[arg-type]
                family_dependency_status=family_status,
            )
        )
    return tuple(classes)


def equivalence_class_members(
    classes: Sequence[WaveHypothesisEquivalenceClass],
) -> dict[str, tuple[str, ...]]:
    return {item.equivalence_class_id: item.member_hypothesis_ids for item in classes}


def validate_fib_family_dependency_registry(
    references: Sequence[FibonacciReference] = (),
) -> tuple[str, ...]:
    errors: list[str] = []
    for reference in references:
        dependency = _DEPENDENCY_BY_KEY.get(
            f"{reference.family}:{reference.method_family}"
        )
        if dependency is None:
            errors.append(f"unknown_family:{reference.family}:{reference.method_family}")
            continue
        if reference.calculation_version != dependency.formula_version:
            errors.append(f"formula_version_mismatch:{reference.fib_id}")
        if reference.formula != dependency.formula:
            errors.append(f"formula_mismatch:{reference.fib_id}")
        if reference.required_endpoint_labels and (
            reference.required_endpoint_labels != dependency.required_endpoint_labels
        ):
            errors.append(f"endpoint_dependency_mismatch:{reference.fib_id}")
    return tuple(errors)


def selection_consensus_universe(
    selections: Sequence[WaveHypothesisSelection],
    hypotheses: Sequence[MonthlyWaveHypothesis],
    *,
    ticker: str,
    cutoff: str,
    adjustment_basis: str,
    classes: Sequence[WaveHypothesisEquivalenceClass],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    members = equivalence_class_members(classes)
    candidate_ids: set[str] = set()
    errors: list[str] = []
    for index, selection in enumerate(selections):
        validation = validate_wave_hypothesis_selection(
            selection,
            hypotheses,
            ticker=ticker,
            cutoff=cutoff,
            adjustment_basis=adjustment_basis,
            strict_context=False,
            equivalence_class_members=members,
        )
        if not validation.valid:
            errors.extend(f"selection_{index}:{value}" for value in validation.errors)
            continue
        if selection.status == WaveSelectionStatus.SELECTED:
            if selection.hypothesis_id is not None:
                candidate_ids.add(selection.hypothesis_id)
            if selection.alternative_hypothesis_id is not None:
                candidate_ids.add(selection.alternative_hypothesis_id)
        elif selection.status == WaveSelectionStatus.AMBIGUOUS:
            candidate_ids.update(selection.competing_hypothesis_ids)
    return tuple(sorted(candidate_ids)), tuple(errors)


def _family_references(
    hypothesis: MonthlyWaveHypothesis,
    dependency: FibFamilyDependency,
    *,
    ticker: str,
    currency: str,
    as_of: str,
) -> tuple[FibonacciReference, ...]:
    return tuple(
        item
        for item in calculate_wave_fibonacci(
            hypothesis,
            ticker=ticker,
            currency=currency,
            as_of=as_of,
        )
        if item.family == dependency.family
        and item.method_family == dependency.method_family
    )


def _price_role(value: Decimal, current_price: Decimal) -> str:
    if value < current_price:
        return "SUPPORT"
    if value > current_price:
        return "RESISTANCE"
    return "CURRENT_ZONE"


def _price_equivalent(
    references_by_hypothesis: Mapping[str, Sequence[FibonacciReference]],
    *,
    current_price: Decimal,
) -> tuple[bool, dict[Timeframe, tuple[str, str]]]:
    grouped: dict[tuple[Timeframe, str], list[Decimal]] = defaultdict(list)
    expected = len(references_by_hypothesis)
    for references in references_by_hypothesis.values():
        seen: set[tuple[Timeframe, str]] = set()
        for reference in references:
            key = (reference.confluence_target_timeframe, reference.ratio)
            if key in seen:
                return False, {}
            seen.add(key)
            grouped[key].append(reference.calculated_price)
    zones: dict[Timeframe, tuple[str, str]] = {}
    for (timeframe, _ratio), values in grouped.items():
        if len(values) != expected:
            return False, {}
        low, high = min(values), max(values)
        center = sum(values) / Decimal(len(values))
        if center <= 0 or high - low > center * CONFLUENCE_PCT[timeframe]:
            return False, {}
        if len({_price_role(value, current_price) for value in values}) != 1:
            return False, {}
        existing = zones.get(timeframe)
        if existing is None:
            zones[timeframe] = (str(low), str(high))
        else:
            zones[timeframe] = (
                str(min(Decimal(existing[0]), low)),
                str(max(Decimal(existing[1]), high)),
            )
    return True, zones


def evaluate_fib_family_consensus(
    hypotheses: Sequence[MonthlyWaveHypothesis],
    candidate_hypothesis_ids: Sequence[str],
    *,
    ticker: str,
    currency: str,
    as_of: str,
    current_price: Decimal,
) -> FamilyConsensusEvaluation:
    classes = build_wave_hypothesis_equivalence_classes(hypotheses)
    hypothesis_map = {item.hypothesis_id: item for item in hypotheses}
    ids = tuple(dict.fromkeys(candidate_hypothesis_ids))
    selected = [hypothesis_map[value] for value in ids if value in hypothesis_map]
    validation_errors = tuple(
        f"unknown_hypothesis_id:{value}" for value in ids if value not in hypothesis_map
    )
    consensus_set_id = _stable_id("v3-family-consensus", ticker, ids, CALCULATION_VERSION)
    if not selected:
        return FamilyConsensusEvaluation(
            consensus_set_id=consensus_set_id,
            ticker=ticker,
            candidate_hypothesis_ids=ids,
            equivalence_classes=classes,
            full_hypothesis_stability="VALID_ABSTENTION",
            family_level_price_structure="PASS",
            families=(),
            eligible_fibonacci=(),
            omitted_unstable_family_count=0,
            validation_errors=validation_errors,
        )

    full_stability = "STABLE" if len(selected) == 1 else "MATERIAL_VARIATION"
    family_results: list[FibFamilyConsensus] = []
    eligible_references: list[FibonacciReference] = []
    degree_set = {item.source_degree for item in selected}
    candidate_classes = [
        item
        for item in classes
        if set(ids).issubset(item.member_hypothesis_ids)
    ]
    class_id = candidate_classes[0].equivalence_class_id if candidate_classes else None

    for dependency in FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY:
        endpoint_refs_by_hypothesis: dict[str, tuple[str, ...]] = {}
        endpoint_status_by_hypothesis: dict[str, tuple[str, ...]] = {}
        references_by_hypothesis: dict[str, tuple[FibonacciReference, ...]] = {}
        missing = False
        for hypothesis in selected:
            endpoint_map = _endpoint_map(hypothesis)
            if hypothesis.wave_state not in dependency.wave_state_applicability:
                missing = True
                continue
            if not all(label in endpoint_map for label in dependency.required_endpoint_labels):
                missing = True
                continue
            endpoint_refs_by_hypothesis[hypothesis.hypothesis_id] = tuple(
                endpoint_map[label].pivot_ref  # type: ignore[union-attr]
                for label in dependency.required_endpoint_labels
            )
            endpoint_status_by_hypothesis[hypothesis.hypothesis_id] = tuple(
                endpoint_map[label].status  # type: ignore[union-attr]
                for label in dependency.required_endpoint_labels
            )
            references_by_hypothesis[hypothesis.hypothesis_id] = _family_references(
                hypothesis,
                dependency,
                ticker=ticker,
                currency=currency,
                as_of=as_of,
            )

        if missing or len(references_by_hypothesis) != len(selected):
            stability = FamilyStability.INSUFFICIENT
            reason = "required_endpoint_or_applicability_missing"
            zones: dict[Timeframe, tuple[str, str]] = {}
        elif len(degree_set) != 1:
            stability = FamilyStability.MATERIAL_VARIATION
            reason = "source_degree_conflict"
            zones = {}
        elif len(set(endpoint_refs_by_hypothesis.values())) == 1 and len(
            set(endpoint_status_by_hypothesis.values())
        ) == 1:
            stability = FamilyStability.EXACT_INVARIANT
            reason = "required_endpoint_refs_and_status_invariant"
            zones = {}
        elif len(set(endpoint_status_by_hypothesis.values())) != 1:
            stability = FamilyStability.MATERIAL_VARIATION
            reason = "required_endpoint_confirmation_status_conflict"
            zones = {}
        else:
            equivalent, zones = _price_equivalent(
                references_by_hypothesis,
                current_price=current_price,
            )
            stability = (
                FamilyStability.PRICE_EQUIVALENT
                if equivalent
                else FamilyStability.MATERIAL_VARIATION
            )
            reason = (
                "existing_confluence_tolerance_and_price_role_match"
                if equivalent
                else "required_endpoints_change_visible_price_zone_or_role"
            )
        eligible = stability in {
            FamilyStability.EXACT_INVARIANT,
            FamilyStability.PRICE_EQUIVALENT,
        }
        degree = next(iter(degree_set)) if len(degree_set) == 1 else None
        user_role = (
            "LONG_HORIZON_CONTEXT"
            if degree == "GRAND_CYCLE"
            else "PRIMARY_CURRENT_RESISTANCE"
            if degree is not None
            else None
        )
        family_results.append(
            FibFamilyConsensus(
                family_key=dependency.key,
                family=dependency.family,
                method_family=dependency.method_family,
                required_endpoint_labels=dependency.required_endpoint_labels,
                candidate_hypothesis_ids=ids,
                endpoint_refs_by_hypothesis=endpoint_refs_by_hypothesis,
                calculated_values_by_hypothesis={
                    key: tuple(str(item.calculated_price) for item in values)
                    for key, values in references_by_hypothesis.items()
                },
                visible_zone_by_timeframe=zones,
                stability=stability,
                eligible=eligible,
                reason=reason,
                source_degree=degree,
                user_role=user_role,
            )
        )
        if not eligible:
            continue
        if stability == FamilyStability.EXACT_INVARIANT:
            first_id = sorted(references_by_hypothesis)[0]
            candidates = references_by_hypothesis[first_id]
        else:
            candidates = tuple(
                reference
                for candidate_id in sorted(references_by_hypothesis)
                for reference in references_by_hypothesis[candidate_id]
            )
        for reference in candidates:
            if degree == "GRAND_CYCLE" and reference.confluence_target_timeframe != "monthly":
                continue
            eligible_references.append(
                reference.model_copy(
                    update={
                        "required_endpoint_labels": dependency.required_endpoint_labels,
                        "family_stability": stability.value,
                        "consensus_set_id": consensus_set_id,
                        "consensus_candidate_ids": ids,
                        "equivalence_class_id": class_id,
                    }
                )
            )

    dependency_errors = validate_fib_family_dependency_registry(eligible_references)
    all_errors = validation_errors + dependency_errors
    relevant = [item for item in family_results if item.stability != FamilyStability.NOT_APPLICABLE]
    eligible_count = sum(item.eligible for item in relevant)
    family_level = "PASS" if eligible_count else "FAIL"
    omitted = sum(item.stability == FamilyStability.MATERIAL_VARIATION for item in relevant)
    return FamilyConsensusEvaluation(
        consensus_set_id=consensus_set_id,
        ticker=ticker,
        candidate_hypothesis_ids=ids,
        equivalence_classes=classes,
        full_hypothesis_stability=full_stability,
        family_level_price_structure=family_level,
        families=tuple(family_results),
        eligible_fibonacci=tuple(eligible_references),
        omitted_unstable_family_count=omitted,
        validation_errors=all_errors,
    )


def _deterministic_sources(
    result: PriceStructureWaveFibV3Result,
    timeframe: Timeframe,
) -> tuple[ZoneSource, ...]:
    sources: dict[str, ZoneSource] = {}
    for zone in result.timeframe_zone_maps.get(timeframe, ()):
        for source in zone.sources:
            if source.evidence_type != "FIBONACCI":
                sources[source.source_id] = source
    return tuple(sources[key] for key in sorted(sources))


def apply_family_consensus_feedback(
    result: PriceStructureWaveFibV3Result,
    selections: Sequence[WaveHypothesisSelection],
) -> PriceStructureWaveFibV3Result:
    classes = build_wave_hypothesis_equivalence_classes(result.primary_monthly_hypotheses)
    candidate_ids, selection_errors = selection_consensus_universe(
        selections,
        result.primary_monthly_hypotheses,
        ticker=result.ticker,
        cutoff=result.as_of,
        adjustment_basis=result.adjustment_basis,
        classes=classes,
    )
    evaluation = evaluate_fib_family_consensus(
        result.primary_monthly_hypotheses,
        candidate_ids,
        ticker=result.ticker,
        currency=result.currency,
        as_of=result.as_of,
        current_price=result.current_price,
    )
    if selection_errors:
        evaluation = evaluation.model_copy(
            update={
                "validation_errors": evaluation.validation_errors + selection_errors,
                "eligible_fibonacci": (),
                "family_level_price_structure": "FAIL",
            }
        )

    maps: dict[Timeframe, tuple] = {}
    for timeframe in TIMEFRAME_ORDER:
        sources = list(_deterministic_sources(result, timeframe))
        sources.extend(
            _fib_source(reference)
            for reference in evaluation.eligible_fibonacci
            if reference.confluence_target_timeframe == timeframe
        )
        maps[timeframe] = merge_zone_sources(
            sources,
            ticker=result.ticker,
            timeframe=timeframe,
            current_price=result.current_price,
        )
    cross = build_cross_timeframe_confluence(
        maps,
        ticker=result.ticker,
        current_price=result.current_price,
    )
    hypothesis_map = {
        item.hypothesis_id: item for item in result.primary_monthly_hypotheses
    }
    selected_hypotheses = tuple(
        hypothesis_map[value] for value in candidate_ids if value in hypothesis_map
    )
    if len(selected_hypotheses) == 1:
        primary_status = selected_hypotheses[0].status
        selected_id = selected_hypotheses[0].hypothesis_id
    elif selected_hypotheses:
        primary_status = "AMBIGUOUS"
        selected_id = None
    else:
        primary_status = "NONE"
        selected_id = None
    render = render_shadow_v3(
        result_maps=maps,
        hypotheses=selected_hypotheses,
        primary_status=primary_status,
        cross=cross,
        currency=result.currency,
    )
    if len(selected_hypotheses) > 1 and evaluation.eligible_fibonacci:
        render += (
            "\n• 장기 파동 가설은 복수지만, 표시된 Fib 구간은 후보 간 "
            "동일하거나 기존 가격대 허용범위에서 일치합니다."
        )
    audit = evaluation.model_dump(mode="json")
    audit["selection_validation_errors"] = list(selection_errors)
    audit["unstable_fib_source_in_confluence"] = sum(
        source.evidence_type == "FIBONACCI" and source.family_stability is None
        for zone in cross
        for source in zone.sources
    )
    return result.model_copy(
        update={
            "selected_hypothesis_id": selected_id,
            "primary_hypothesis_status": primary_status,
            "fibonacci": evaluation.eligible_fibonacci,
            "timeframe_zone_maps": maps,
            "cross_timeframe_confluence": cross,
            "shadow_render": render,
            "family_consensus_audit": audit,
        }
    )
