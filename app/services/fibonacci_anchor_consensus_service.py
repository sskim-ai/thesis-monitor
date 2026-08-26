from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.services.multi_timeframe_price_structure_service import (
    TIMEFRAME_ORDER,
    MultiTimeframeSelection,
    PivotEvidence,
    ShadowPriceStructureResult,
    SynthesisSelection,
    TimeframeSelection,
    build_shadow_price_structure_result,
    reference_select_price_structure,
)
from app.services.ohlcv_structure_service import LOCAL_CONFIG, Timeframe
from app.services.variable_ai_anchor_selection_service import (
    PriceOnlyAIAnchorPacket,
    ReasonCategory,
    TimeframeAnchorEvidence,
    audit_price_only_evidence_egress,
    to_price_structure_evidence_packet,
)


PACKET_CONTRACT = "price-only-ai-swing-consensus-packet-v1"
OUTPUT_CONTRACT = "variable-ai-swing-structure-consensus-v1"
OUTPUT_BATCH_CONTRACT = "variable-ai-swing-structure-consensus-batch-v1"
CONSENSUS_CONTRACT = "ai-anchor-consensus-policy-v1"

CANDIDATE_LIMITS: dict[Timeframe, int] = {
    "monthly": 8,
    "weekly": 10,
    "daily": 12,
}

SelectionStatus = Literal["SELECTED", "AMBIGUOUS", "INSUFFICIENT_STRUCTURE"]
ValidationStatus = Literal["PASS", "VALID_ABSTENTION", "REJECTED"]
FibEligibility = Literal[
    "ELIGIBLE",
    "OMIT_AMBIGUOUS",
    "OMIT_UNSTABLE",
    "OMIT_INSUFFICIENT",
    "OMIT_INVALID",
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DeterministicSROwnership(FrozenModel):
    owner: Literal["DETERMINISTIC_BACKEND"] = "DETERMINISTIC_BACKEND"
    primary_support_zone_id: str | None = None
    primary_resistance_zone_id: str | None = None


class CanonicalSwingStructureCandidate(FrozenModel):
    swing_structure_id: str
    ticker: str
    timeframe: Timeframe
    mode_eligibility: Literal["RETRACEMENT", "BOTH"]
    low_pivot_id: str
    high_pivot_id: str
    correction_low_pivot_id: str | None = None
    chronology: tuple[str, ...]
    anchor_prices: tuple[Decimal, ...]
    adjustment_basis: str
    structural_role_candidate: Literal[
        "BASE_TO_EXPANSION_HIGH",
        "BASE_HIGH_CORRECTIVE_HIGHER_LOW",
    ]
    segment_refs: tuple[str, ...] = ()
    candle_neighborhood_refs: tuple[str, ...] = ()
    current_regime_relation: str
    magnitude_pct: Decimal
    rank: int


class OmittedSwingStructure(FrozenModel):
    swing_structure_id: str
    reason: Literal["BOUNDED_CANDIDATE_LIMIT"] = "BOUNDED_CANDIDATE_LIMIT"


class CandidateStructureAudit(FrozenModel):
    eligible_pivot_count: int
    valid_retracement_count: int
    valid_extension_count: int
    valid_structure_count: int
    included_structure_count: int
    omitted_structure_count: int
    omitted_structures: tuple[OmittedSwingStructure, ...] = ()


class ConsensusTimeframeEvidence(FrozenModel):
    timeframe: Timeframe
    deterministic_sr: DeterministicSROwnership
    evidence: TimeframeAnchorEvidence
    swing_structure_candidates: tuple[CanonicalSwingStructureCandidate, ...] = ()
    candidate_audit: CandidateStructureAudit


class PriceOnlyAISwingConsensusPacket(FrozenModel):
    contract: str = PACKET_CONTRACT
    stage: Literal["SWING_STRUCTURE_SELECTION"] = "SWING_STRUCTURE_SELECTION"
    ticker: str
    security_id: str
    market: Literal["KR", "US"]
    currency: str
    current_price: Decimal
    as_of: str
    cutoff: str
    adjustment_basis: str
    evidence_mode: Literal["COMPACT_RICH", "FULL_DEBUG"]
    source_packet_contract: str
    source_evidence_sha256: str
    evidence_sha256: str
    monthly: ConsensusTimeframeEvidence
    weekly: ConsensusTimeframeEvidence
    daily: ConsensusTimeframeEvidence


class VariableSwingStructureSelection(FrozenModel):
    status: SelectionStatus
    swing_structure_id: str | None = None
    alternative_swing_structure_id: str | None = None
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
    reason_categories: tuple[ReasonCategory, ...] = Field(min_length=1, max_length=3)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=16)
    concise_reason: str = Field(default="", max_length=240)


class VariableAISwingConsensusOutput(FrozenModel):
    contract: Literal["variable-ai-swing-structure-consensus-v1"] = OUTPUT_CONTRACT
    ticker: str
    monthly: VariableSwingStructureSelection
    weekly: VariableSwingStructureSelection
    daily: VariableSwingStructureSelection


class VariableAISwingConsensusBatchOutput(FrozenModel):
    contract: Literal["variable-ai-swing-structure-consensus-batch-v1"] = (
        OUTPUT_BATCH_CONTRACT
    )
    selections: tuple[VariableAISwingConsensusOutput, ...]


class SwingConsensusValidation(FrozenModel):
    valid: bool
    errors: tuple[str, ...] = ()
    timeframe_status: dict[Timeframe, ValidationStatus]


class TimeframePriceStructureEligibility(FrozenModel):
    sr: Literal["ELIGIBLE", "UNAVAILABLE"]
    fib: FibEligibility


class PriceStructureEligibility(FrozenModel):
    monthly: TimeframePriceStructureEligibility
    weekly: TimeframePriceStructureEligibility
    daily: TimeframePriceStructureEligibility


class VariableSwingExecutionResult(FrozenModel):
    status: Literal["PASS", "FAIL_CLOSED"]
    failure_reason: str | None = None
    output: VariableAISwingConsensusOutput | None = None
    validation: SwingConsensusValidation
    selection: MultiTimeframeSelection
    shadow: ShadowPriceStructureResult
    price_structure_eligibility: PriceStructureEligibility
    fallback_timeframes: tuple[Timeframe, ...] = ()
    packet_continues: bool = True


class ConsensusStabilityClass(StrEnum):
    STABLE = "STABLE"
    MINOR_VARIATION = "MINOR_VARIATION"
    MATERIAL_VARIATION = "MATERIAL_VARIATION"
    VALID_ABSTENTION = "VALID_ABSTENTION"


class ConsensusSelectionState(StrEnum):
    CONSENSUS_SELECTED = "CONSENSUS_SELECTED"
    VALID_ABSTENTION = "VALID_ABSTENTION"
    UNSTABLE = "UNSTABLE"


class TimeframeConsensusStability(FrozenModel):
    timeframe: Timeframe
    classification: ConsensusStabilityClass
    consensus_state: ConsensusSelectionState
    run_count: int
    exact_signature_count: int
    status_frequency: dict[str, int]
    structure_frequency: dict[str, int]
    alternative_frequency: dict[str, int]
    valid_abstention_count: int
    semantic_rejection_count: int
    structure_equivalent: bool
    consensus_structure_id: str | None = None


class StockConsensusDecision(FrozenModel):
    contract: str = CONSENSUS_CONTRACT
    ticker: str
    monthly: TimeframeConsensusStability
    weekly: TimeframeConsensusStability
    daily: TimeframeConsensusStability
    price_structure_eligibility: PriceStructureEligibility
    eligible_fib_timeframes: tuple[Timeframe, ...] = ()
    omitted_unstable_timeframes: tuple[Timeframe, ...] = ()
    omitted_ambiguous_timeframes: tuple[Timeframe, ...] = ()
    omitted_insufficient_timeframes: tuple[Timeframe, ...] = ()
    omitted_invalid_timeframes: tuple[Timeframe, ...] = ()
    unstable_fib_user_visible_eligible: int = 0


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _stable_id(prefix: str, *parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _regime(
    current_price: Decimal,
    low: PivotEvidence,
    high: PivotEvidence,
    correction: PivotEvidence | None,
) -> str:
    if correction is not None and current_price >= correction.price:
        return "UPTREND_PULLBACK_HELD"
    if current_price > high.price:
        return "ABOVE_CONFIRMED_SWING_HIGH"
    if low.price <= current_price <= high.price:
        return "RETRACEMENT_WITHIN_CONFIRMED_SWING"
    return "BELOW_CONFIRMED_SWING_LOW"


def _candidate(
    packet: PriceOnlyAIAnchorPacket,
    evidence: TimeframeAnchorEvidence,
    low: PivotEvidence,
    high: PivotEvidence,
    correction: PivotEvidence | None,
) -> CanonicalSwingStructureCandidate:
    mode = "BOTH" if correction is not None else "RETRACEMENT"
    anchors = (low, high, correction) if correction is not None else (low, high)
    anchor_refs = {item.pivot_id for item in anchors if item is not None}
    segment_refs = tuple(
        item.segment_id
        for item in evidence.swing_segments
        if item.start_pivot_ref in anchor_refs or item.end_pivot_ref in anchor_refs
    )
    neighborhood_refs = tuple(
        item.center_bar_id
        for item in evidence.candidate_neighborhoods
        if item.pivot_id in anchor_refs
    )
    structure_id = _stable_id(
        "swing-structure",
        packet.ticker,
        evidence.timeframe,
        mode,
        low.pivot_id,
        high.pivot_id,
        correction.pivot_id if correction else "NONE",
        packet.adjustment_basis,
    )
    return CanonicalSwingStructureCandidate(
        swing_structure_id=structure_id,
        ticker=packet.ticker,
        timeframe=evidence.timeframe,
        mode_eligibility=mode,
        low_pivot_id=low.pivot_id,
        high_pivot_id=high.pivot_id,
        correction_low_pivot_id=correction.pivot_id if correction else None,
        chronology=tuple(item.date for item in anchors if item is not None),
        anchor_prices=tuple(item.price for item in anchors if item is not None),
        adjustment_basis=packet.adjustment_basis,
        structural_role_candidate=(
            "BASE_HIGH_CORRECTIVE_HIGHER_LOW"
            if correction is not None
            else "BASE_TO_EXPANSION_HIGH"
        ),
        segment_refs=segment_refs,
        candle_neighborhood_refs=neighborhood_refs,
        current_regime_relation=_regime(packet.current_price, low, high, correction),
        magnitude_pct=_rounded((high.price - low.price) / low.price * Decimal(100)),
        rank=0,
    )


def _candidate_sort_key(
    timeframe: Timeframe,
    candidate: CanonicalSwingStructureCandidate,
) -> tuple[object, ...]:
    end_date = candidate.chronology[-1]
    if timeframe == "monthly":
        return (-candidate.magnitude_pct, end_date, candidate.swing_structure_id)
    return (end_date, candidate.magnitude_pct, candidate.swing_structure_id)


def _bounded_candidate_selection(
    timeframe: Timeframe,
    ranked: Sequence[CanonicalSwingStructureCandidate],
) -> tuple[CanonicalSwingStructureCandidate, ...]:
    limit = CANDIDATE_LIMITS[timeframe]
    retracements = [item for item in ranked if item.mode_eligibility == "RETRACEMENT"]
    extensions = [item for item in ranked if item.mode_eligibility == "BOTH"]
    priority: list[CanonicalSwingStructureCandidate] = []

    def add(item: CanonicalSwingStructureCandidate | None) -> None:
        if item is not None and all(
            existing.swing_structure_id != item.swing_structure_id for existing in priority
        ):
            priority.append(item)

    for group in (retracements, extensions):
        add(max(group, key=lambda item: item.magnitude_pct, default=None))
        add(
            max(
                group,
                key=lambda item: (
                    item.chronology[-1],
                    item.chronology[0],
                    item.magnitude_pct,
                ),
                default=None,
            )
        )
    correction_refs = sorted(
        {
            item.correction_low_pivot_id
            for item in extensions
            if item.correction_low_pivot_id is not None
        },
        key=lambda ref: max(
            item.chronology[-1]
            for item in extensions
            if item.correction_low_pivot_id == ref
        ),
        reverse=True,
    )
    for correction_ref in correction_refs:
        group = [
            item
            for item in extensions
            if item.correction_low_pivot_id == correction_ref
        ]
        add(max(group, key=lambda item: item.magnitude_pct, default=None))
        add(
            max(
                group,
                key=lambda item: (item.chronology[0], item.magnitude_pct),
                default=None,
            )
        )
    high_refs = sorted(
        {item.high_pivot_id for item in retracements},
        key=lambda ref: max(
            item.chronology[-1] for item in retracements if item.high_pivot_id == ref
        ),
        reverse=True,
    )
    for high_ref in high_refs:
        group = [item for item in retracements if item.high_pivot_id == high_ref]
        add(max(group, key=lambda item: item.magnitude_pct, default=None))
        add(
            max(
                group,
                key=lambda item: (item.chronology[0], item.magnitude_pct),
                default=None,
            )
        )
    for item in ranked:
        add(item)
    return tuple(
        item.model_copy(update={"rank": index})
        for index, item in enumerate(priority[:limit], 1)
    )


def generate_canonical_swing_structure_candidates(
    packet: PriceOnlyAIAnchorPacket,
    timeframe: Timeframe,
) -> tuple[tuple[CanonicalSwingStructureCandidate, ...], CandidateStructureAudit]:
    evidence: TimeframeAnchorEvidence = getattr(packet, timeframe)
    pivots = tuple(
        item
        for item in evidence.pivots
        if item.ticker == packet.ticker
        and item.timeframe == timeframe
        and item.adjustment_basis == packet.adjustment_basis
        and item.date <= packet.cutoff
        and item.confirmed_at <= packet.cutoff
    )
    lows = tuple(item for item in pivots if item.kind == "low")
    highs = tuple(item for item in pivots if item.kind == "high")
    retracements: list[CanonicalSwingStructureCandidate] = []
    extensions: list[CanonicalSwingStructureCandidate] = []
    for low in lows:
        for high in highs:
            if not (low.date < high.date and low.price < high.price):
                continue
            retracements.append(_candidate(packet, evidence, low, high, None))
            for correction in lows:
                if correction.date > high.date and correction.price > low.price:
                    extensions.append(_candidate(packet, evidence, low, high, correction))
    values = [*retracements, *extensions]
    reverse = timeframe != "monthly"
    ranked = sorted(values, key=lambda item: _candidate_sort_key(timeframe, item), reverse=reverse)
    ranked = [item.model_copy(update={"rank": index}) for index, item in enumerate(ranked, 1)]
    included = _bounded_candidate_selection(timeframe, ranked)
    included_ids = {item.swing_structure_id for item in included}
    omitted = tuple(
        OmittedSwingStructure(swing_structure_id=item.swing_structure_id)
        for item in ranked
        if item.swing_structure_id not in included_ids
    )
    return included, CandidateStructureAudit(
        eligible_pivot_count=len(pivots),
        valid_retracement_count=len(retracements),
        valid_extension_count=len(extensions),
        valid_structure_count=len(ranked),
        included_structure_count=len(included),
        omitted_structure_count=len(omitted),
        omitted_structures=omitted,
    )


def build_price_only_ai_swing_consensus_packet(
    packet: PriceOnlyAIAnchorPacket,
) -> PriceOnlyAISwingConsensusPacket:
    reference = reference_select_price_structure(to_price_structure_evidence_packet(packet))
    values: dict[Timeframe, ConsensusTimeframeEvidence] = {}
    for timeframe in TIMEFRAME_ORDER:
        selected: TimeframeSelection = getattr(reference, timeframe)
        candidates, audit = generate_canonical_swing_structure_candidates(packet, timeframe)
        values[timeframe] = ConsensusTimeframeEvidence(
            timeframe=timeframe,
            deterministic_sr=DeterministicSROwnership(
                primary_support_zone_id=selected.support_zone_id,
                primary_resistance_zone_id=selected.resistance_zone_id,
            ),
            evidence=getattr(packet, timeframe),
            swing_structure_candidates=candidates,
            candidate_audit=audit,
        )
    material = {
        "contract": PACKET_CONTRACT,
        "ticker": packet.ticker,
        "security_id": packet.security_id,
        "market": packet.market,
        "currency": packet.currency,
        "current_price": str(packet.current_price),
        "as_of": packet.as_of,
        "cutoff": packet.cutoff,
        "adjustment_basis": packet.adjustment_basis,
        "evidence_mode": packet.evidence_mode,
        "source_packet_contract": packet.contract,
        "source_evidence_sha256": packet.evidence_sha256,
        **{key: value.model_dump(mode="json") for key, value in values.items()},
    }
    return PriceOnlyAISwingConsensusPacket(
        ticker=packet.ticker,
        security_id=packet.security_id,
        market=packet.market,
        currency=packet.currency,
        current_price=packet.current_price,
        as_of=packet.as_of,
        cutoff=packet.cutoff,
        adjustment_basis=packet.adjustment_basis,
        evidence_mode=packet.evidence_mode,
        source_packet_contract=packet.contract,
        source_evidence_sha256=packet.evidence_sha256,
        evidence_sha256=_canonical_hash(material),
        monthly=values["monthly"],
        weekly=values["weekly"],
        daily=values["daily"],
    )


def _to_base_packet(packet: PriceOnlyAISwingConsensusPacket) -> PriceOnlyAIAnchorPacket:
    return PriceOnlyAIAnchorPacket(
        ticker=packet.ticker,
        security_id=packet.security_id,
        market=packet.market,
        currency=packet.currency,
        current_price=packet.current_price,
        as_of=packet.as_of,
        cutoff=packet.cutoff,
        adjustment_basis=packet.adjustment_basis,
        evidence_mode=packet.evidence_mode,
        source_evidence_sha256=packet.source_evidence_sha256,
        evidence_sha256=packet.source_evidence_sha256,
        monthly=packet.monthly.evidence,
        weekly=packet.weekly.evidence,
        daily=packet.daily.evidence,
    )


def audit_consensus_packet_egress(
    packet: PriceOnlyAISwingConsensusPacket,
) -> dict[str, object]:
    base_audit = audit_price_only_evidence_egress(_to_base_packet(packet))
    payload = packet.model_dump(mode="json")
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    banned = {
        "user",
        "user_id",
        "account",
        "account_id",
        "portfolio",
        "private_notes",
        "thesis",
        "telegram",
        "token",
        "secret",
        "password",
        "api_key",
        "auth_header",
    }
    violations: list[str] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                child = f"{path}.{key}" if path else str(key)
                if str(key).casefold() in banned:
                    violations.append(child)
                visit(item, child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")

    visit(payload, "")
    return {
        "contract": "price-only-swing-consensus-egress-audit-v1",
        "status": "PASS" if base_audit["status"] == "PASS" and not violations else "FAIL",
        "private_field_egress": len(violations),
        "secret_egress": sum(
            any(value in item for value in ("token", "secret", "password", "api_key", "auth"))
            for item in violations
        ),
        "unrelated_thesis_egress": sum("thesis" in item for item in violations),
        "precomputed_fibonacci_fields": 0,
        "violations": tuple(sorted(violations)),
        "serialized_bytes": len(serialized),
    }


def validate_variable_ai_swing_consensus_output(
    packet: PriceOnlyAISwingConsensusPacket,
    output: VariableAISwingConsensusOutput,
) -> SwingConsensusValidation:
    if output.ticker != packet.ticker:
        return SwingConsensusValidation(
            valid=False,
            errors=("ticker:mismatch",),
            timeframe_status={timeframe: "REJECTED" for timeframe in TIMEFRAME_ORDER},
        )
    errors: list[str] = []
    statuses: dict[Timeframe, ValidationStatus] = {}
    for timeframe in TIMEFRAME_ORDER:
        source: ConsensusTimeframeEvidence = getattr(packet, timeframe)
        selected: VariableSwingStructureSelection = getattr(output, timeframe)
        candidates = {
            item.swing_structure_id: item for item in source.swing_structure_candidates
        }
        valid_evidence_refs = {
            item.pivot_id for item in source.evidence.pivots
        } | {item.bar_id for item in source.evidence.bars} | {
            item.segment_id for item in source.evidence.swing_segments
        }
        timeframe_errors: list[str] = []
        if any(ref not in valid_evidence_refs for ref in selected.evidence_refs):
            timeframe_errors.append(f"{timeframe}:evidence_ref_invalid")
        if selected.status != "SELECTED":
            if selected.swing_structure_id is not None:
                timeframe_errors.append(f"{timeframe}:abstention_primary_structure_present")
            if selected.alternative_swing_structure_id is not None:
                timeframe_errors.append(f"{timeframe}:abstention_alternative_structure_present")
            statuses[timeframe] = (
                "REJECTED" if timeframe_errors else "VALID_ABSTENTION"
            )
            errors.extend(timeframe_errors)
            continue
        if selected.swing_structure_id is None:
            timeframe_errors.append(f"{timeframe}:selected_structure_missing")
        elif selected.swing_structure_id not in candidates:
            timeframe_errors.append(f"{timeframe}:selected_structure_invalid")
        alternative = selected.alternative_swing_structure_id
        if alternative is not None and alternative not in candidates:
            timeframe_errors.append(f"{timeframe}:alternative_structure_invalid")
        if alternative is not None and alternative == selected.swing_structure_id:
            timeframe_errors.append(f"{timeframe}:alternative_matches_primary")
        if not selected.evidence_refs:
            timeframe_errors.append(f"{timeframe}:selected_evidence_missing")
        statuses[timeframe] = "REJECTED" if timeframe_errors else "PASS"
        errors.extend(timeframe_errors)
    return SwingConsensusValidation(
        valid=not errors,
        errors=tuple(errors),
        timeframe_status=statuses,
    )


def _selection_and_eligibility(
    packet: PriceOnlyAISwingConsensusPacket,
    output: VariableAISwingConsensusOutput | None,
    validation: SwingConsensusValidation,
) -> tuple[MultiTimeframeSelection, PriceStructureEligibility, tuple[Timeframe, ...]]:
    base = _to_base_packet(packet)
    reference = reference_select_price_structure(to_price_structure_evidence_packet(base))
    values: dict[Timeframe, TimeframeSelection] = {}
    eligibility: dict[Timeframe, TimeframePriceStructureEligibility] = {}
    fallback: list[Timeframe] = []
    for timeframe in TIMEFRAME_ORDER:
        source: ConsensusTimeframeEvidence = getattr(packet, timeframe)
        reference_value: TimeframeSelection = getattr(reference, timeframe)
        sr_state = (
            "ELIGIBLE"
            if any(
                (
                    source.deterministic_sr.primary_support_zone_id,
                    source.deterministic_sr.primary_resistance_zone_id,
                )
            )
            else "UNAVAILABLE"
        )
        selected = getattr(output, timeframe) if output is not None else None
        status = validation.timeframe_status[timeframe]
        if selected is not None and status == "PASS":
            candidates = {
                item.swing_structure_id: item for item in source.swing_structure_candidates
            }
            candidate = candidates[selected.swing_structure_id or ""]
            refs = tuple(
                dict.fromkeys(
                    item
                    for item in (
                        source.deterministic_sr.primary_support_zone_id,
                        source.deterministic_sr.primary_resistance_zone_id,
                        candidate.low_pivot_id,
                        candidate.high_pivot_id,
                        candidate.correction_low_pivot_id,
                    )
                    if item is not None
                )
            )
            values[timeframe] = TimeframeSelection(
                status="SELECTED",
                support_zone_id=source.deterministic_sr.primary_support_zone_id,
                resistance_zone_id=source.deterministic_sr.primary_resistance_zone_id,
                fib_mode=candidate.mode_eligibility,
                low_pivot_id=candidate.low_pivot_id,
                high_pivot_id=candidate.high_pivot_id,
                correction_low_pivot_id=candidate.correction_low_pivot_id,
                regime=candidate.current_regime_relation,  # type: ignore[arg-type]
                confidence=selected.confidence.casefold(),  # type: ignore[arg-type]
                evidence_refs=refs,
                concise_reason=selected.concise_reason,
            )
            eligibility[timeframe] = TimeframePriceStructureEligibility(
                sr=sr_state,
                fib="ELIGIBLE",
            )
            continue
        fallback.append(timeframe)
        values[timeframe] = reference_value.model_copy(
            update={
                "fib_mode": "NONE",
                "low_pivot_id": None,
                "high_pivot_id": None,
                "correction_low_pivot_id": None,
                "regime": "RANGE_OR_INSUFFICIENT",
                "evidence_refs": tuple(
                    item
                    for item in (
                        source.deterministic_sr.primary_support_zone_id,
                        source.deterministic_sr.primary_resistance_zone_id,
                    )
                    if item is not None
                ),
                "concise_reason": "deterministic SR preserved; Fibonacci omitted",
            }
        )
        fib_state: FibEligibility = "OMIT_INVALID"
        if selected is not None and status == "VALID_ABSTENTION":
            fib_state = (
                "OMIT_AMBIGUOUS"
                if selected.status == "AMBIGUOUS"
                else "OMIT_INSUFFICIENT"
            )
        eligibility[timeframe] = TimeframePriceStructureEligibility(
            sr=sr_state,
            fib=fib_state,
        )
    return (
        MultiTimeframeSelection(
            selection_source="variable_ai_canonical_swing_structure_consensus",
            monthly=values["monthly"],
            weekly=values["weekly"],
            daily=values["daily"],
            synthesis=SynthesisSelection(
                timeframe_agreement=reference.synthesis.timeframe_agreement,
                concise_summary=(
                    "deterministic SR with validated variable-AI swing structure IDs"
                ),
            ),
        ),
        PriceStructureEligibility(
            monthly=eligibility["monthly"],
            weekly=eligibility["weekly"],
            daily=eligibility["daily"],
        ),
        tuple(fallback),
    )


def execute_variable_swing_consensus_selector(
    packet: PriceOnlyAISwingConsensusPacket,
    selector: Callable[[dict[str, object]], object],
) -> VariableSwingExecutionResult:
    audit = audit_consensus_packet_egress(packet)
    raw_output: object
    if audit["status"] != "PASS":
        raw_output = ValueError("price_only_egress_failed")
    else:
        try:
            raw_output = selector(packet.model_dump(mode="json"))
        except (TimeoutError, ConnectionError, RuntimeError, ValueError, TypeError) as exc:
            raw_output = exc
    output: VariableAISwingConsensusOutput | None = None
    failure_reason: str | None = None
    if isinstance(raw_output, Exception):
        failure_reason = type(raw_output).__name__
    else:
        try:
            if isinstance(raw_output, str):
                raw_output = json.loads(raw_output)
            output = VariableAISwingConsensusOutput.model_validate(raw_output)
        except (ValidationError, json.JSONDecodeError, TypeError, ValueError) as exc:
            failure_reason = type(exc).__name__
    if output is None:
        validation = SwingConsensusValidation(
            valid=False,
            errors=(f"runtime:{failure_reason or 'unavailable'}",),
            timeframe_status={timeframe: "REJECTED" for timeframe in TIMEFRAME_ORDER},
        )
    else:
        validation = validate_variable_ai_swing_consensus_output(packet, output)
        if not validation.valid:
            failure_reason = "invalid_swing_structure_output"
    selection, eligibility, fallback = _selection_and_eligibility(
        packet,
        output,
        validation,
    )
    shadow = build_shadow_price_structure_result(
        to_price_structure_evidence_packet(_to_base_packet(packet)),
        selection,
    )
    return VariableSwingExecutionResult(
        status="PASS" if output is not None and validation.valid else "FAIL_CLOSED",
        failure_reason=failure_reason,
        output=output,
        validation=validation,
        selection=selection,
        shadow=shadow,
        price_structure_eligibility=eligibility,
        fallback_timeframes=fallback,
    )


def _frequency(values: Sequence[str | None]) -> dict[str, int]:
    return dict(sorted(Counter(value or "NONE" for value in values).items()))


def _visible_structure_equivalent(
    timeframe: Timeframe,
    first: VariableSwingExecutionResult,
    second: VariableSwingExecutionResult,
) -> bool:
    left_selection = getattr(first.selection, timeframe)
    right_selection = getattr(second.selection, timeframe)
    if left_selection.regime != right_selection.regime:
        return False
    left = sorted(
        (item.mode, item.ratio, item.calculated_price)
        for item in first.shadow.fibonacci[timeframe]
    )
    right = sorted(
        (item.mode, item.ratio, item.calculated_price)
        for item in second.shadow.fibonacci[timeframe]
    )
    if len(left) != len(right):
        return False
    tolerance = Decimal(str(LOCAL_CONFIG[timeframe].merge_pct))
    return all(
        left_mode == right_mode
        and left_ratio == right_ratio
        and abs(left_price - right_price)
        <= ((left_price + right_price) / Decimal(2)) * tolerance
        for (left_mode, left_ratio, left_price), (
            right_mode,
            right_ratio,
            right_price,
        ) in zip(left, right)
    )


def _timeframe_consensus(
    timeframe: Timeframe,
    runs: Sequence[VariableSwingExecutionResult],
) -> TimeframeConsensusStability:
    statuses: list[str] = []
    structures: list[str | None] = []
    alternatives: list[str | None] = []
    selected_runs: list[VariableSwingExecutionResult] = []
    abstentions = 0
    rejections = 0
    signatures: list[tuple[str, str | None, str | None]] = []
    for run in runs:
        validation_status = run.validation.timeframe_status[timeframe]
        output = getattr(run.output, timeframe) if run.output is not None else None
        output_status = output.status if output is not None else "RUNTIME_FAILURE"
        statuses.append(output_status)
        structures.append(output.swing_structure_id if output is not None else None)
        alternatives.append(
            output.alternative_swing_structure_id if output is not None else None
        )
        signatures.append(
            (
                output_status,
                output.swing_structure_id if output is not None else None,
                output.alternative_swing_structure_id if output is not None else None,
            )
        )
        if validation_status == "PASS":
            selected_runs.append(run)
        elif validation_status == "VALID_ABSTENTION":
            abstentions += 1
        else:
            rejections += 1
    exact_count = max(Counter(signatures).values(), default=0)
    selected_ids = [
        getattr(run.output, timeframe).swing_structure_id
        for run in selected_runs
        if run.output is not None
    ]
    equivalent = bool(selected_runs)
    for index, first in enumerate(selected_runs):
        for second in selected_runs[index + 1 :]:
            equivalent = equivalent and _visible_structure_equivalent(
                timeframe,
                first,
                second,
            )
    if rejections:
        classification = ConsensusStabilityClass.MATERIAL_VARIATION
        consensus_state = ConsensusSelectionState.UNSTABLE
    elif abstentions or not selected_runs:
        classification = ConsensusStabilityClass.VALID_ABSTENTION
        consensus_state = ConsensusSelectionState.VALID_ABSTENTION
    elif len(set(selected_ids)) == 1:
        classification = ConsensusStabilityClass.STABLE
        consensus_state = ConsensusSelectionState.CONSENSUS_SELECTED
    elif equivalent:
        classification = ConsensusStabilityClass.MINOR_VARIATION
        consensus_state = ConsensusSelectionState.CONSENSUS_SELECTED
    else:
        classification = ConsensusStabilityClass.MATERIAL_VARIATION
        consensus_state = ConsensusSelectionState.UNSTABLE
    consensus_id: str | None = None
    if consensus_state == ConsensusSelectionState.CONSENSUS_SELECTED:
        frequencies = Counter(value for value in selected_ids if value is not None)
        if frequencies:
            consensus_id = sorted(frequencies, key=lambda value: (-frequencies[value], value))[0]
    return TimeframeConsensusStability(
        timeframe=timeframe,
        classification=classification,
        consensus_state=consensus_state,
        run_count=len(runs),
        exact_signature_count=exact_count,
        status_frequency=_frequency(statuses),
        structure_frequency=_frequency(structures),
        alternative_frequency=_frequency(alternatives),
        valid_abstention_count=abstentions,
        semantic_rejection_count=rejections,
        structure_equivalent=equivalent,
        consensus_structure_id=consensus_id,
    )


def classify_swing_structure_consensus(
    packet: PriceOnlyAISwingConsensusPacket,
    runs: Sequence[VariableSwingExecutionResult],
) -> StockConsensusDecision:
    values = {
        timeframe: _timeframe_consensus(timeframe, runs)
        for timeframe in TIMEFRAME_ORDER
    }
    eligibility: dict[Timeframe, TimeframePriceStructureEligibility] = {}
    eligible: list[Timeframe] = []
    unstable: list[Timeframe] = []
    ambiguous: list[Timeframe] = []
    insufficient: list[Timeframe] = []
    invalid: list[Timeframe] = []
    for timeframe in TIMEFRAME_ORDER:
        source: ConsensusTimeframeEvidence = getattr(packet, timeframe)
        value = values[timeframe]
        sr = (
            "ELIGIBLE"
            if any(
                (
                    source.deterministic_sr.primary_support_zone_id,
                    source.deterministic_sr.primary_resistance_zone_id,
                )
            )
            else "UNAVAILABLE"
        )
        fib: FibEligibility
        if value.classification in {
            ConsensusStabilityClass.STABLE,
            ConsensusStabilityClass.MINOR_VARIATION,
        }:
            fib = "ELIGIBLE"
            eligible.append(timeframe)
        elif value.classification == ConsensusStabilityClass.MATERIAL_VARIATION:
            fib = "OMIT_UNSTABLE"
            unstable.append(timeframe)
        else:
            statuses = value.status_frequency
            if statuses.get("AMBIGUOUS", 0):
                fib = "OMIT_AMBIGUOUS"
                ambiguous.append(timeframe)
            else:
                fib = "OMIT_INSUFFICIENT"
                insufficient.append(timeframe)
        if value.semantic_rejection_count:
            fib = "OMIT_INVALID"
            if timeframe in unstable:
                unstable.remove(timeframe)
            invalid.append(timeframe)
        eligibility[timeframe] = TimeframePriceStructureEligibility(sr=sr, fib=fib)
    return StockConsensusDecision(
        ticker=packet.ticker,
        monthly=values["monthly"],
        weekly=values["weekly"],
        daily=values["daily"],
        price_structure_eligibility=PriceStructureEligibility(
            monthly=eligibility["monthly"],
            weekly=eligibility["weekly"],
            daily=eligibility["daily"],
        ),
        eligible_fib_timeframes=tuple(eligible),
        omitted_unstable_timeframes=tuple(unstable),
        omitted_ambiguous_timeframes=tuple(ambiguous),
        omitted_insufficient_timeframes=tuple(insufficient),
        omitted_invalid_timeframes=tuple(invalid),
        unstable_fib_user_visible_eligible=0,
    )
