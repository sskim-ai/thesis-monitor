from __future__ import annotations


CONTRACT_VERSION = "optional-semantic-audit-coverage-validity-v1"


def optional_semantic_audit_status(
    *,
    observed_claim_count: int,
    semantic_violation_count: int,
) -> dict[str, object]:
    if observed_claim_count < 0 or semantic_violation_count < 0:
        raise ValueError("optional_semantic_audit_count_must_be_nonnegative")

    semantic_status = "PASS" if semantic_violation_count == 0 else "FAIL"
    coverage_status = (
        "OBSERVED" if observed_claim_count else "NO_OBSERVED_CLAIMS"
    )
    result: dict[str, object] = {
        "contract": CONTRACT_VERSION,
        "observed_claim_count": observed_claim_count,
        "semantic_violation_count": semantic_violation_count,
        "coverage_status": coverage_status,
        "semantic_status": semantic_status,
        "readiness_blocking": semantic_violation_count > 0,
        "status": semantic_status,
    }
    return result
