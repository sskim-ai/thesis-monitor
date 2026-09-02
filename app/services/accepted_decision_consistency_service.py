from __future__ import annotations

from enum import StrEnum

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionBaseline,
    AcceptedV2ProductionBlock,
)
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionPlan,
    AcceptedDecisionSource,
    AcceptedDecisionStatus,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    FrozenModel,
)


CONTRACT_VERSION = "accepted-decision-consistency-v1"


class MaterialEvidenceDelta(StrEnum):
    NO_PRIOR = "NO_PRIOR"
    NOT_DETECTED = "NOT_DETECTED"
    FINGERPRINT_CHANGED_UNCLASSIFIED = "FINGERPRINT_CHANGED_UNCLASSIFIED"


class AcceptedDecisionConsistencyDiagnostic(FrozenModel):
    ticker: str
    evidence_fingerprint: str
    prior_evidence_fingerprint: str | None
    prior_accepted: str | None
    fresh_candidate: str
    adjudication_status: str
    adjudication_recommendation: str | None
    fresh_accepted: str | None
    evidence_fingerprint_changed: bool | None
    material_evidence_delta: MaterialEvidenceDelta
    valid_adjudication: bool
    accepted_decision_changed: bool
    explained: bool
    errors: tuple[str, ...]


class AcceptedDecisionConsistencyAudit(FrozenModel):
    contract: str = CONTRACT_VERSION
    status: str
    diagnostics: tuple[AcceptedDecisionConsistencyDiagnostic, ...]
    unexplained_accepted_decision_drift: int
    raw_candidate_used_as_final: int
    daily_review_overrides_valid_v2_accepted: int


def _valid_adjudication(plan: AcceptedDecisionPlan) -> bool:
    if plan.adjudication_status != "FINAL" or plan.adjudication_id is None:
        return False
    if plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1:
        return str(plan.adjudication_recommendation) == "KEEP_V1"
    if plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V2:
        return str(plan.adjudication_recommendation) == "KEEP_V2"
    return False


def audit_accepted_decision_consistency(
    *,
    evidence_packets: tuple[DecisionEvidencePacket, ...],
    prior_accepted: tuple[AcceptedV2ProductionBaseline, ...],
    accepted_plans: tuple[AcceptedDecisionPlan, ...],
    blocks: tuple[AcceptedV2ProductionBlock, ...],
) -> AcceptedDecisionConsistencyAudit:
    packets = {row.ticker: row for row in evidence_packets}
    prior = {row.ticker: row for row in prior_accepted}
    plans = {row.ticker: row for row in accepted_plans}
    rendered = {row.ticker: row for row in blocks}
    diagnostics: list[AcceptedDecisionConsistencyDiagnostic] = []
    raw_candidate_used_as_final = 0
    accepted_ownership_overrides = 0

    for ticker in packets:
        packet = packets[ticker]
        baseline = prior.get(ticker)
        plan = plans[ticker]
        block = rendered.get(ticker)
        fingerprint_changed = (
            None
            if baseline is None
            else baseline.evidence_sha256 != packet.evidence_sha256
        )
        material_delta = (
            MaterialEvidenceDelta.NO_PRIOR
            if baseline is None
            else (
                MaterialEvidenceDelta.FINGERPRINT_CHANGED_UNCLASSIFIED
                if fingerprint_changed
                else MaterialEvidenceDelta.NOT_DETECTED
            )
        )
        accepted_changed = bool(
            baseline is not None
            and plan.accepted_decision is not None
            and plan.accepted_decision != baseline.accepted_decision
        )
        valid_adjudication = _valid_adjudication(plan)
        errors: list[str] = []
        if accepted_changed and not valid_adjudication:
            errors.append("accepted_decision_change_without_valid_adjudication")
        if accepted_changed and not fingerprint_changed:
            errors.append("same_evidence_accepted_decision_drift")
        if block is not None and block.decision != plan.accepted_decision:
            accepted_ownership_overrides += 1
            errors.append("final_block_does_not_match_accepted_plan")
        if (
            block is not None
            and plan.candidate_decision != plan.accepted_decision
            and block.decision == plan.candidate_decision
        ):
            raw_candidate_used_as_final += 1
            errors.append("raw_candidate_used_as_final")
        if plan.status == AcceptedDecisionStatus.READY and block is None:
            errors.append("ready_accepted_plan_missing_final_block")
        if plan.status != AcceptedDecisionStatus.READY and block is not None:
            errors.append("not_ready_accepted_plan_visible")
        diagnostics.append(
            AcceptedDecisionConsistencyDiagnostic(
                ticker=ticker,
                evidence_fingerprint=packet.evidence_sha256,
                prior_evidence_fingerprint=(
                    baseline.evidence_sha256 if baseline is not None else None
                ),
                prior_accepted=(baseline.accepted_decision if baseline is not None else None),
                fresh_candidate=plan.candidate_decision,
                adjudication_status=plan.adjudication_status,
                adjudication_recommendation=(
                    str(plan.adjudication_recommendation)
                    if plan.adjudication_recommendation is not None
                    else None
                ),
                fresh_accepted=plan.accepted_decision,
                evidence_fingerprint_changed=fingerprint_changed,
                material_evidence_delta=material_delta,
                valid_adjudication=valid_adjudication,
                accepted_decision_changed=accepted_changed,
                explained=not errors,
                errors=tuple(errors),
            )
        )

    unexplained = sum(not row.explained for row in diagnostics)
    return AcceptedDecisionConsistencyAudit(
        status=(
            "PASS"
            if unexplained == 0
            and raw_candidate_used_as_final == 0
            and accepted_ownership_overrides == 0
            else "FAIL"
        ),
        diagnostics=tuple(diagnostics),
        unexplained_accepted_decision_drift=unexplained,
        raw_candidate_used_as_final=raw_candidate_used_as_final,
        daily_review_overrides_valid_v2_accepted=accepted_ownership_overrides,
    )
