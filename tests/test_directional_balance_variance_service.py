from __future__ import annotations

from app.services.directional_balance_service import DirectionalBalance
from app.services.directional_balance_variance_service import (
    BalanceVarianceClass,
    LabelVarianceClass,
    SameEvidenceBalanceObservation,
    audit_same_evidence_balance_variance,
    classify_balance_variance,
    requires_directional_balance_adjudication,
)


def _observation(
    run_id: str,
    *,
    candidate_buy: float,
    candidate_decision: str,
    accepted_buy: float = 6,
    accepted_decision: str = "BUY",
    adjudication_required: bool = False,
    valid_adjudication: bool = False,
) -> SameEvidenceBalanceObservation:
    return SameEvidenceBalanceObservation(
        run_id=run_id,
        ticker="GOOGL",
        packet_id="run-51-frozen",
        evidence_sha256="same-evidence",
        candidate_input_sha256="same-input",
        candidate_decision=candidate_decision,
        candidate_directional_balance=DirectionalBalance(
            buy=candidate_buy, sell=10 - candidate_buy
        ),
        accepted_decision=accepted_decision,
        accepted_directional_balance=DirectionalBalance(buy=accepted_buy, sell=10 - accepted_buy),
        adjudication_required=adjudication_required,
        valid_adjudication=valid_adjudication,
        adjudication_id=(f"adj-{run_id}" if valid_adjudication else None),
    )


def test_variance_distance_classes_follow_contract_boundaries() -> None:
    assert classify_balance_variance(0.5) == BalanceVarianceClass.MINOR_VARIANCE
    assert classify_balance_variance(1.0) == BalanceVarianceClass.MODERATE_VARIANCE
    assert classify_balance_variance(1.5) == BalanceVarianceClass.MATERIAL_VARIANCE


def test_boundary_candidate_variance_can_resolve_to_stable_accepted_outcome() -> None:
    audit = audit_same_evidence_balance_variance(
        (
            _observation("run-1", candidate_buy=6, candidate_decision="BUY"),
            _observation(
                "run-2",
                candidate_buy=5.5,
                candidate_decision="HOLD",
                adjudication_required=True,
                valid_adjudication=True,
            ),
            _observation("run-3", candidate_buy=6, candidate_decision="BUY"),
        )
    )

    assert audit.status == "PASS"
    assert audit.candidate_variance == BalanceVarianceClass.MINOR_VARIANCE
    assert audit.candidate_label_variance == LabelVarianceClass.LABEL_BOUNDARY_CROSS
    assert audit.candidate_label_boundary_cross_count == 2
    assert audit.accepted_label_variance == LabelVarianceClass.LABEL_STABLE
    assert audit.unexplained_same_evidence_accepted_drift == 0
    assert audit.production_model_majority_voting is False


def test_material_same_evidence_accepted_drift_blocks_readiness() -> None:
    audit = audit_same_evidence_balance_variance(
        (
            _observation("run-1", candidate_buy=8, candidate_decision="BUY", accepted_buy=8),
            _observation(
                "run-2",
                candidate_buy=5,
                candidate_decision="HOLD",
                accepted_buy=5,
                accepted_decision="HOLD",
            ),
            _observation("run-3", candidate_buy=8, candidate_decision="BUY", accepted_buy=8),
        )
    )

    assert audit.status == "FAIL"
    assert audit.accepted_variance == BalanceVarianceClass.MATERIAL_VARIANCE
    assert audit.accepted_label_variance == LabelVarianceClass.LABEL_BOUNDARY_CROSS
    assert audit.unexplained_same_evidence_accepted_drift == 1
    assert "unexplained_same_evidence_accepted_drift" in audit.errors


def test_same_evidence_identity_and_fresh_execution_count_are_enforced() -> None:
    first = _observation("run-1", candidate_buy=6, candidate_decision="BUY")
    second = _observation("run-2", candidate_buy=6, candidate_decision="BUY").model_copy(
        update={"candidate_input_sha256": "different-input"}
    )
    audit = audit_same_evidence_balance_variance((first, second))

    assert audit.status == "FAIL"
    assert "fewer_than_three_fresh_executions" in audit.errors
    assert "same_evidence_identity_mismatch" in audit.errors


def test_adjudication_trigger_ignores_minor_ratio_movement() -> None:
    prior = DirectionalBalance(buy=6, sell=4)

    assert (
        requires_directional_balance_adjudication(
            prior_decision="BUY",
            prior_balance=prior,
            prior_evidence_sha256="same",
            candidate_decision="BUY",
            candidate_balance=DirectionalBalance(buy=6.5, sell=3.5),
            current_evidence_sha256="same",
        )
        is False
    )
    assert (
        requires_directional_balance_adjudication(
            prior_decision="BUY",
            prior_balance=prior,
            prior_evidence_sha256="same",
            candidate_decision="BUY",
            candidate_balance=DirectionalBalance(buy=7.5, sell=2.5),
            current_evidence_sha256="same",
        )
        is True
    )
    assert (
        requires_directional_balance_adjudication(
            prior_decision="BUY",
            prior_balance=prior,
            prior_evidence_sha256="different",
            candidate_decision="BUY",
            candidate_balance=DirectionalBalance(buy=6, sell=4),
            current_evidence_sha256="current",
            major_thesis_condition_conflict=True,
        )
        is True
    )
    assert (
        requires_directional_balance_adjudication(
            prior_decision="BUY",
            prior_balance=prior,
            prior_evidence_sha256="same",
            candidate_decision="HOLD",
            candidate_balance=DirectionalBalance(buy=5.5, sell=4.5),
            current_evidence_sha256="different",
        )
        is True
    )
