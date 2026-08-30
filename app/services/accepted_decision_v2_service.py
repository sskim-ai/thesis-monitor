from __future__ import annotations

import hashlib
import json
import re
from enum import StrEnum
from typing import Literal

from app.services.cross_market_decision_engine_service import (
    Decision,
    DecisionEvidencePacket,
    EvidenceClaim,
    FrozenModel,
)
from app.services.evidence_maturity_pricing_service import (
    EvidenceMaturity,
    PricingRequirement,
)
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionCandidate,
)
from app.services.scenario_asymmetry_service import Asymmetry


CONTRACT_VERSION = "v2-accepted-decision-ownership-v1"
VALIDATOR_CONTRACT = "v2-accepted-decision-validator-v1"


class AcceptedDecisionStatus(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class AcceptedDecisionSource(StrEnum):
    CANDIDATE = "CANDIDATE"
    ADJUDICATION_KEEP_V1 = "ADJUDICATION_KEEP_V1"
    ADJUDICATION_KEEP_V2 = "ADJUDICATION_KEEP_V2"


class AdjudicationRecommendation(StrEnum):
    KEEP_V1 = "KEEP_V1"
    KEEP_V2 = "KEEP_V2"
    NEEDS_REPAIR = "NEEDS_REPAIR"


class AcceptedV2Adjudication(FrozenModel):
    ticker: str
    v1_decision: Decision
    v2_decision: Decision
    accepted_decision: Decision
    recommendation: AdjudicationRecommendation
    v1_overrequired_confirmation: Literal["YES", "NO", "UNCERTAIN"]
    v2_underweighted_execution_risk: Literal["YES", "NO", "UNCERTAIN"]
    v1_ignored_confirmation_cost: Literal["YES", "NO", "UNCERTAIN"]
    v2_overstated_favorable_asymmetry: Literal["YES", "NO", "UNCERTAIN"]
    valuation_or_expectation_misuse: Literal[
        "V1", "V2", "BOTH", "NEITHER", "UNCERTAIN"
    ]
    data_quality_comparison_safe: bool
    decisive_basis: EvidenceClaim
    bounded_repair: str


class AcceptedDecisionPlan(FrozenModel):
    contract: str = CONTRACT_VERSION
    status: AcceptedDecisionStatus
    ticker: str
    candidate_decision_id: str
    candidate_decision: Decision
    candidate_evidence_fingerprint: str
    material_disagreement: bool
    adjudication_id: str | None
    adjudication_status: str
    adjudication_recommendation: AdjudicationRecommendation | None
    adjudication_reason: EvidenceClaim | None
    accepted_decision_id: str | None
    accepted_decision: Decision | None
    accepted_source: AcceptedDecisionSource | None
    accepted_evidence_fingerprint: str | None
    accepted_as_of: str | None
    accepted_reason: EvidenceClaim | None
    accepted_overall_maturity: EvidenceMaturity | None
    accepted_pricing_requirement: PricingRequirement | None
    accepted_asymmetry: Asymmetry | None
    accepted_preconfirmation_buy: bool
    accepted_postconfirmation_hold: bool
    accepted_confirmation_cost_basis: EvidenceClaim | None
    accepted_upgrade_condition: EvidenceClaim | None
    accepted_downgrade_condition: EvidenceClaim | None
    denial_reason: str | None


class AcceptedDecisionValidationResult(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]


_ORDER_LANGUAGE = re.compile(
    r"시장가|지정가|(?:매수|매도)\s*주문|주문\s*실행|전량\s*(?:매도|매수)|"
    r"포지션\s*크기|buy\s+now|sell\s+now",
    re.IGNORECASE,
)
_EXACT_NUMBER = re.compile(
    r"(?<![A-Za-z])[-+]?\d[\d,.]*(?:\.\d+)?\s*(?:%|원|달러|USD|KRW|배|주|MW|GW)"
)


def _canonical_fingerprint(prefix: str, value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()}"


def _not_ready_plan(
    *,
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate,
    candidate_decision_id: str,
    material_disagreement: bool,
    adjudication_id: str | None,
    adjudication_status: str,
    adjudication: AcceptedV2Adjudication | None,
    denial_reason: str,
) -> AcceptedDecisionPlan:
    return AcceptedDecisionPlan(
        status=AcceptedDecisionStatus.NOT_READY,
        ticker=packet.ticker,
        candidate_decision_id=candidate_decision_id,
        candidate_decision=candidate.decision,
        candidate_evidence_fingerprint=packet.evidence_sha256,
        material_disagreement=material_disagreement,
        adjudication_id=adjudication_id,
        adjudication_status=adjudication_status,
        adjudication_recommendation=(adjudication.recommendation if adjudication else None),
        adjudication_reason=(adjudication.decisive_basis if adjudication else None),
        accepted_decision_id=None,
        accepted_decision=None,
        accepted_source=None,
        accepted_evidence_fingerprint=None,
        accepted_as_of=None,
        accepted_reason=None,
        accepted_overall_maturity=None,
        accepted_pricing_requirement=None,
        accepted_asymmetry=None,
        accepted_preconfirmation_buy=False,
        accepted_postconfirmation_hold=False,
        accepted_confirmation_cost_basis=None,
        accepted_upgrade_condition=None,
        accepted_downgrade_condition=None,
        denial_reason=denial_reason,
    )


def resolve_accepted_v2_decision(
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate,
    *,
    v1_decision: Decision,
    material_disagreement: bool,
    adjudication: AcceptedV2Adjudication | None,
) -> AcceptedDecisionPlan:
    candidate_payload = candidate.model_dump(mode="json")
    candidate_decision_id = _canonical_fingerprint(
        "v2-candidate",
        {
            "ticker": packet.ticker,
            "evidence_fingerprint": packet.evidence_sha256,
            "candidate": candidate_payload,
        },
    )
    adjudication_id = (
        _canonical_fingerprint("v2-adjudication", adjudication.model_dump(mode="json"))
        if adjudication is not None
        else None
    )

    if candidate.ticker != packet.ticker:
        return _not_ready_plan(
            packet=packet,
            candidate=candidate,
            candidate_decision_id=candidate_decision_id,
            material_disagreement=material_disagreement,
            adjudication_id=adjudication_id,
            adjudication_status="INVALID",
            adjudication=adjudication,
            denial_reason="candidate_ticker_mismatch",
        )

    if not material_disagreement:
        accepted_decision = candidate.decision
        accepted_source = AcceptedDecisionSource.CANDIDATE
        accepted_reason = candidate.decisive_reason
        adjudication_status = "NOT_REQUIRED"
    else:
        if adjudication is None:
            return _not_ready_plan(
                packet=packet,
                candidate=candidate,
                candidate_decision_id=candidate_decision_id,
                material_disagreement=True,
                adjudication_id=None,
                adjudication_status="MISSING_REQUIRED",
                adjudication=None,
                denial_reason="material_disagreement_without_final_adjudication",
            )
        if adjudication.recommendation == AdjudicationRecommendation.NEEDS_REPAIR:
            return _not_ready_plan(
                packet=packet,
                candidate=candidate,
                candidate_decision_id=candidate_decision_id,
                material_disagreement=True,
                adjudication_id=adjudication_id,
                adjudication_status="NEEDS_REPAIR",
                adjudication=adjudication,
                denial_reason="adjudication_not_final",
            )
        expected = (
            v1_decision
            if adjudication.recommendation == AdjudicationRecommendation.KEEP_V1
            else candidate.decision
        )
        if (
            adjudication.ticker != packet.ticker
            or adjudication.v1_decision != v1_decision
            or adjudication.v2_decision != candidate.decision
            or adjudication.accepted_decision != expected
        ):
            return _not_ready_plan(
                packet=packet,
                candidate=candidate,
                candidate_decision_id=candidate_decision_id,
                material_disagreement=True,
                adjudication_id=adjudication_id,
                adjudication_status="INVALID",
                adjudication=adjudication,
                denial_reason="adjudication_decision_mismatch",
            )
        accepted_decision = expected
        accepted_source = (
            AcceptedDecisionSource.ADJUDICATION_KEEP_V1
            if adjudication.recommendation == AdjudicationRecommendation.KEEP_V1
            else AcceptedDecisionSource.ADJUDICATION_KEEP_V2
        )
        accepted_reason = adjudication.decisive_basis
        adjudication_status = "FINAL"

    accepted_preconfirmation_buy = bool(
        accepted_decision == "BUY"
        and candidate.decision == accepted_decision
        and candidate.pre_confirmation_buy
    )
    accepted_postconfirmation_hold = bool(
        accepted_decision == "HOLD"
        and candidate.decision == accepted_decision
        and candidate.post_confirmation_hold
    )
    accepted_asymmetry = (
        Asymmetry.UNKNOWN
        if accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1
        else candidate.asymmetry.asymmetry
    )
    accepted_evidence_fingerprint = _canonical_fingerprint(
        "v2-accepted-evidence",
        {
            "packet": packet.evidence_sha256,
            "candidate_decision_id": candidate_decision_id,
            "adjudication_id": adjudication_id,
            "accepted_reason_refs": accepted_reason.evidence_refs,
        },
    )
    accepted_decision_id = _canonical_fingerprint(
        "v2-accepted-decision",
        {
            "ticker": packet.ticker,
            "accepted_decision": accepted_decision,
            "accepted_source": accepted_source,
            "accepted_evidence_fingerprint": accepted_evidence_fingerprint,
            "accepted_as_of": packet.assessment_date,
        },
    )
    return AcceptedDecisionPlan(
        status=AcceptedDecisionStatus.READY,
        ticker=packet.ticker,
        candidate_decision_id=candidate_decision_id,
        candidate_decision=candidate.decision,
        candidate_evidence_fingerprint=packet.evidence_sha256,
        material_disagreement=material_disagreement,
        adjudication_id=adjudication_id,
        adjudication_status=adjudication_status,
        adjudication_recommendation=(adjudication.recommendation if adjudication else None),
        adjudication_reason=(adjudication.decisive_basis if adjudication else None),
        accepted_decision_id=accepted_decision_id,
        accepted_decision=accepted_decision,
        accepted_source=accepted_source,
        accepted_evidence_fingerprint=accepted_evidence_fingerprint,
        accepted_as_of=packet.assessment_date,
        accepted_reason=accepted_reason,
        accepted_overall_maturity=candidate.overall_maturity.maturity,
        accepted_pricing_requirement=candidate.pricing_requirement.requirement,
        accepted_asymmetry=accepted_asymmetry,
        accepted_preconfirmation_buy=accepted_preconfirmation_buy,
        accepted_postconfirmation_hold=accepted_postconfirmation_hold,
        accepted_confirmation_cost_basis=(
            candidate.confirmation_cost.basis if accepted_preconfirmation_buy else None
        ),
        accepted_upgrade_condition=candidate.upgrade_condition,
        accepted_downgrade_condition=candidate.downgrade_condition,
        denial_reason=None,
    )


def validate_accepted_v2_decision(
    packet: DecisionEvidencePacket,
    plan: AcceptedDecisionPlan,
) -> AcceptedDecisionValidationResult:
    errors: list[str] = []
    if plan.status != AcceptedDecisionStatus.READY:
        errors.append(plan.denial_reason or "accepted_decision_not_ready")
        return AcceptedDecisionValidationResult(valid=False, errors=tuple(errors))
    if plan.ticker != packet.ticker:
        errors.append("accepted_ticker_mismatch")
    if not plan.accepted_decision or not plan.accepted_decision_id or not plan.accepted_source:
        errors.append("accepted_identity_missing")
    if not plan.accepted_evidence_fingerprint or not plan.accepted_as_of:
        errors.append("accepted_lineage_missing")
    if plan.accepted_preconfirmation_buy and plan.accepted_decision != "BUY":
        errors.append("rejected_preconfirmation_buy_leaked_to_accepted")
    if plan.accepted_postconfirmation_hold and plan.accepted_decision != "HOLD":
        errors.append("postconfirmation_hold_decision_mismatch")
    if plan.accepted_decision == "SELL" and plan.accepted_asymmetry == Asymmetry.FAVORABLE:
        errors.append("accepted_decision_reason_conflict")
    if (
        plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1
        and plan.accepted_decision == plan.candidate_decision
    ):
        errors.append("keep_v1_did_not_replace_candidate")
    claims = tuple(
        claim
        for claim in (
            plan.accepted_reason,
            plan.accepted_confirmation_cost_basis,
            plan.accepted_upgrade_condition,
            plan.accepted_downgrade_condition,
        )
        if claim is not None
    )
    allowed_refs = {row.ref_id for row in packet.evidence}
    for claim in claims:
        if _ORDER_LANGUAGE.search(claim.text):
            errors.append("order_command_language")
        if _EXACT_NUMBER.search(claim.text):
            errors.append("adjudication_introduced_unregistered_numeric")
        for ref_id in claim.evidence_refs:
            if ref_id not in allowed_refs:
                errors.append(f"unknown_accepted_evidence_ref:{ref_id}")
    return AcceptedDecisionValidationResult(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
    )
