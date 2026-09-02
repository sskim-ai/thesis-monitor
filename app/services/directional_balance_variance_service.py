from __future__ import annotations

from enum import StrEnum
from itertools import combinations

from pydantic import model_validator

from app.services.cross_market_decision_engine_service import Decision, FrozenModel
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_matches_decision,
)


CONTRACT_VERSION = "v2-same-evidence-balance-variance-v1"
MATERIAL_BALANCE_DISTANCE = 1.5


class BalanceVarianceClass(StrEnum):
    MINOR_VARIANCE = "MINOR_VARIANCE"
    MODERATE_VARIANCE = "MODERATE_VARIANCE"
    MATERIAL_VARIANCE = "MATERIAL_VARIANCE"


class LabelVarianceClass(StrEnum):
    LABEL_STABLE = "LABEL_STABLE"
    LABEL_BOUNDARY_CROSS = "LABEL_BOUNDARY_CROSS"


class SameEvidenceBalanceObservation(FrozenModel):
    run_id: str
    ticker: str
    packet_id: str
    evidence_sha256: str
    candidate_input_sha256: str
    candidate_decision: Decision
    candidate_directional_balance: DirectionalBalance
    accepted_decision: Decision
    accepted_directional_balance: DirectionalBalance
    adjudication_required: bool
    valid_adjudication: bool
    adjudication_id: str | None = None

    @model_validator(mode="after")
    def validate_label_balance_pairs(self) -> "SameEvidenceBalanceObservation":
        if not directional_balance_matches_decision(
            self.candidate_directional_balance, self.candidate_decision
        ):
            raise ValueError("candidate_decision_balance_mismatch")
        if not directional_balance_matches_decision(
            self.accepted_directional_balance, self.accepted_decision
        ):
            raise ValueError("accepted_decision_balance_mismatch")
        return self


class SameEvidenceBalanceVarianceAudit(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    run_count: int
    identities_consistent: bool
    candidate_max_balance_distance: float
    candidate_variance: BalanceVarianceClass
    candidate_label_variance: LabelVarianceClass
    candidate_label_boundary_cross_count: int
    accepted_max_balance_distance: float
    accepted_variance: BalanceVarianceClass
    accepted_label_variance: LabelVarianceClass
    accepted_label_boundary_cross_count: int
    unexplained_same_evidence_accepted_drift: int
    production_model_majority_voting: bool = False
    status: str
    errors: tuple[str, ...]


def balance_distance(left: DirectionalBalance, right: DirectionalBalance) -> float:
    return abs(left.buy - right.buy)


def classify_balance_variance(distance: float) -> BalanceVarianceClass:
    if distance <= 0.5:
        return BalanceVarianceClass.MINOR_VARIANCE
    if distance == 1.0:
        return BalanceVarianceClass.MODERATE_VARIANCE
    return BalanceVarianceClass.MATERIAL_VARIANCE


def requires_directional_balance_adjudication(
    *,
    prior_decision: Decision,
    prior_balance: DirectionalBalance | None,
    prior_evidence_sha256: str,
    candidate_decision: Decision,
    candidate_balance: DirectionalBalance,
    current_evidence_sha256: str,
    major_thesis_condition_conflict: bool = False,
) -> bool:
    if candidate_decision != prior_decision or major_thesis_condition_conflict:
        return True
    return bool(
        prior_balance is not None
        and prior_evidence_sha256 == current_evidence_sha256
        and balance_distance(prior_balance, candidate_balance) >= MATERIAL_BALANCE_DISTANCE
    )


def _max_distance(balances: tuple[DirectionalBalance, ...]) -> float:
    return max(
        (balance_distance(left, right) for left, right in combinations(balances, 2)),
        default=0.0,
    )


def _boundary_cross_count(decisions: tuple[Decision, ...]) -> int:
    return sum(left != right for left, right in combinations(decisions, 2))


def audit_same_evidence_balance_variance(
    observations: tuple[SameEvidenceBalanceObservation, ...],
) -> SameEvidenceBalanceVarianceAudit:
    if not observations:
        raise ValueError("same_evidence_observations_missing")
    first = observations[0]
    identities = {
        (row.ticker, row.packet_id, row.evidence_sha256, row.candidate_input_sha256)
        for row in observations
    }
    identities_consistent = len(identities) == 1
    candidate_balances = tuple(row.candidate_directional_balance for row in observations)
    accepted_balances = tuple(row.accepted_directional_balance for row in observations)
    candidate_distance = _max_distance(candidate_balances)
    accepted_distance = _max_distance(accepted_balances)
    candidate_crosses = _boundary_cross_count(tuple(row.candidate_decision for row in observations))
    accepted_crosses = _boundary_cross_count(tuple(row.accepted_decision for row in observations))
    errors: list[str] = []
    if len(observations) < 3:
        errors.append("fewer_than_three_fresh_executions")
    if not identities_consistent:
        errors.append("same_evidence_identity_mismatch")
    if any(row.adjudication_required and not row.valid_adjudication for row in observations):
        errors.append("required_adjudication_missing_or_invalid")
    unexplained_accepted_drift = int(
        accepted_crosses > 0 or accepted_distance >= MATERIAL_BALANCE_DISTANCE
    )
    if unexplained_accepted_drift:
        errors.append("unexplained_same_evidence_accepted_drift")
    return SameEvidenceBalanceVarianceAudit(
        ticker=first.ticker,
        run_count=len(observations),
        identities_consistent=identities_consistent,
        candidate_max_balance_distance=candidate_distance,
        candidate_variance=classify_balance_variance(candidate_distance),
        candidate_label_variance=(
            LabelVarianceClass.LABEL_BOUNDARY_CROSS
            if candidate_crosses
            else LabelVarianceClass.LABEL_STABLE
        ),
        candidate_label_boundary_cross_count=candidate_crosses,
        accepted_max_balance_distance=accepted_distance,
        accepted_variance=classify_balance_variance(accepted_distance),
        accepted_label_variance=(
            LabelVarianceClass.LABEL_BOUNDARY_CROSS
            if accepted_crosses
            else LabelVarianceClass.LABEL_STABLE
        ),
        accepted_label_boundary_cross_count=accepted_crosses,
        unexplained_same_evidence_accepted_drift=unexplained_accepted_drift,
        status="PASS" if not errors else "FAIL",
        errors=tuple(errors),
    )
