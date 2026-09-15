from __future__ import annotations

from app.services.optional_semantic_audit_service import (
    CONTRACT_VERSION,
    optional_semantic_audit_status,
)
from scripts import prospective_monitoring_obligation_m12ax as monitoring


def test_zero_optional_claim_coverage_is_semantically_valid_and_nonblocking() -> None:
    result = optional_semantic_audit_status(
        observed_claim_count=0,
        semantic_violation_count=0,
    )

    assert result == {
        "contract": CONTRACT_VERSION,
        "observed_claim_count": 0,
        "semantic_violation_count": 0,
        "coverage_status": "NO_OBSERVED_CLAIMS",
        "semantic_status": "PASS",
        "readiness_blocking": False,
        "status": "PASS",
    }


def test_observed_semantic_violation_remains_blocking() -> None:
    result = optional_semantic_audit_status(
        observed_claim_count=1,
        semantic_violation_count=1,
    )

    assert result["coverage_status"] == "OBSERVED"
    assert result["semantic_status"] == "FAIL"
    assert result["readiness_blocking"] is True
    assert result["status"] == "FAIL"


def test_monitoring_audit_zero_observation_uses_nonblocking_contract() -> None:
    result = monitoring._monitoring_audit([], {})

    assert result["status"] == "PASS"
    assert result["monitoring_claim_count"] == 0
    assert result["observed_claim_count"] == 0
    assert result["semantic_violation_count"] == 0
    assert result["coverage_status"] == "NO_OBSERVED_CLAIMS"
    assert result["semantic_status"] == "PASS"
    assert result["readiness_blocking"] is False
    assert result["coverage_note"] == "NO_MONITORING_OBLIGATION_CLAIMS_OBSERVED"


def test_monitoring_audit_observed_valid_claim_has_coverage() -> None:
    ref = monitoring._configured_ref()
    candidate = {
        "risk_context": {
            "text": "순부채 증가 여부를 감시해야 한다.",
            "evidence_refs": [ref.ref_id],
        }
    }
    result = monitoring._monitoring_audit(
        [("fixture", "FIXTURE", candidate, "PASS")],
        {"FIXTURE": (ref,)},
    )

    assert result["status"] == "PASS"
    assert result["observed_claim_count"] == 1
    assert result["semantic_violation_count"] == 0
    assert result["coverage_status"] == "OBSERVED"
    assert result["readiness_blocking"] is False
