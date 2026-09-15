from __future__ import annotations

from scripts import configured_fcf_prospective_support_m12ay as m12ay


def test_m12ay_report_sequence_is_complete() -> None:
    assert len(m12ay.SLUGS) == 164
    assert m12ay.SLUGS[1] == "repository-provenance"
    assert m12ay.SLUGS[31] == "m12ax-first-call-four-row-offline-reaudit"
    assert m12ay.SLUGS[63] == "fictional-configured-financial-support-concept-manifest"
    assert m12ay.SLUGS[79] == "fictional-configured-fcf-support-audit"
    assert m12ay.SLUGS[112] == "shadow-configured-fcf-support-audit"
    assert m12ay.SLUGS[164] == "program-completion"


def test_m12ay_fcf_support_fixture_gate_passes() -> None:
    audit = m12ay._fcf_support_fixtures()

    assert audit["status"] == "PASS"
    assert audit["contract"] == "configured-financial-support-concept-v1"
    assert len(audit["positive"]) == 4
    assert len(audit["ocf_negative"]) == 2
    assert len(audit["ocf_ppe_negative"]) == 1
    assert len(audit["current_negative"]) == 2
    assert audit["mixed_fcf_net_debt"]["status"] == "PASS"


def test_m12ay_general_framework_surface_stays_closed_to_fcf() -> None:
    audit = m12ay._general_framework_surface_audit()

    assert audit["status"] == "PASS"
    assert audit["general_framework_application_surface_change_count"] == 0


def test_m12ay_model_facing_surface_is_unchanged() -> None:
    audit = m12ay._m12ay_semantic_surface_hashes()

    assert audit["status"] == "PASS"
    assert audit["total_semantic_change_count"] == 0


def test_m12ay_frozen_runtime_contract() -> None:
    assert m12ay.MODEL == "gpt-5.6-sol"
    assert m12ay.EFFORT == "xhigh"
    assert m12ay.TIMEOUT_SECONDS == 1800
    assert m12ay.EXPECTED_FICTIONAL_CALLS == 12
    assert m12ay.EXPECTED_SHADOW_CALLS == 18
    assert m12ay.EXPECTED_ACTIVE_COUNT == 22
    assert m12ay.NEXT_SCOPE == "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
