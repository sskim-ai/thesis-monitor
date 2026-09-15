from __future__ import annotations

from scripts import fcf_claim_temporal_scope_m12az as m12az


def test_m12az_report_sequence_is_complete() -> None:
    assert len(m12az.SLUGS) == 170
    assert m12az.SLUGS[1] == "repository-provenance"
    assert m12az.SLUGS[28] == "m12ay-completed-36-row-offline-reaudit"
    assert m12az.SLUGS[62] == "new-fictional-model-call-gate"
    assert m12az.SLUGS[81] == "fictional-fcf-local-temporal-scope-audit"
    assert m12az.SLUGS[115] == "shadow-fcf-local-temporal-scope-audit"
    assert m12az.SLUGS[170] == "program-completion"


def test_m12az_polarity_and_span_fixture_gate_passes() -> None:
    audit = m12az._polarity_and_span_fixtures()

    assert audit["status"] == "PASS"
    assert len(audit["positive"]) == 4
    assert len(audit["negative"]) == 5
    assert len(audit["local_positive"]) == 2
    assert len(audit["local_negative"]) == 2
    assert len(audit["english"]) == 2


def test_m12az_model_facing_surface_is_unchanged() -> None:
    audit = m12az._m12az_semantic_surface_hashes()

    assert audit["status"] == "PASS"
    assert audit["total_semantic_change_count"] == 0
    assert audit["two_stage_semantic_change_count"] == 0


def test_m12az_frozen_runtime_contract() -> None:
    assert m12az.MODEL == "gpt-5.6-sol"
    assert m12az.EFFORT == "xhigh"
    assert m12az.TIMEOUT_SECONDS == 1800
    assert m12az.EXPECTED_FICTIONAL_CALLS == 12
    assert m12az.EXPECTED_SHADOW_CALLS == 18
    assert m12az.EXPECTED_ACTIVE_COUNT == 22
    assert m12az.WORK_INSTRUCTION_COMMIT == (
        "1a48271aee4494eb3a0c04b2c2ef0065360d9a79"
    )


def test_m12az_completion_field_manifest_is_complete() -> None:
    assert len(m12az._COMPLETION_FIELDS) == len(set(m12az._COMPLETION_FIELDS))
    assert "fcf_temporal_claim_span_contract_version" in m12az._COMPLETION_FIELDS
    assert "fictional_negated_fulfillment_false_current_count" in (
        m12az._COMPLETION_FIELDS
    )
    assert "shadow_affirmative_current_fulfillment_false_negative_count" in (
        m12az._COMPLETION_FIELDS
    )
