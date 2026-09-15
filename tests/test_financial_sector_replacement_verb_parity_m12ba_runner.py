from __future__ import annotations

from scripts import financial_sector_replacement_verb_parity_m12ba as m12ba


def test_m12ba_report_sequence_is_exact() -> None:
    assert len(m12ba.SLUGS) == 157
    assert len(set(m12ba.SLUGS.values())) == 157
    assert m12ba.SLUGS[1] == "repository-provenance"
    assert m12ba.SLUGS[24] == "m12az-completed-40-row-offline-reaudit"
    assert m12ba.SLUGS[60] == "new-fictional-model-call-gate"
    assert m12ba.SLUGS[79] == "fictional-financial-sector-replacement-verb-audit"
    assert m12ba.SLUGS[109] == "shadow-financial-sector-replacement-verb-audit"
    assert m12ba.SLUGS[157] == "program-completion"


def test_m12ba_frozen_runtime_contract() -> None:
    assert m12ba.MODEL == "gpt-5.6-sol"
    assert m12ba.EFFORT == "xhigh"
    assert m12ba.TIMEOUT_SECONDS == 1800
    assert m12ba.EXPECTED_FICTIONAL_CALLS == 12
    assert m12ba.EXPECTED_FICTIONAL_ROWS == 24
    assert m12ba.EXPECTED_SHADOW_CALLS == 18
    assert m12ba.EXPECTED_ACTIVE_COUNT == 22
    assert m12ba.WORK_INSTRUCTION_COMMIT == (
        "e428ceb087d5a94d562eecaea23168dfc899b91e"
    )


def test_m12ba_replacement_code_audit_is_bounded() -> None:
    audit = m12ba._replacement_code_audit()

    assert audit["status"] == "PASS"
    assert audit["replacement_verb_family_definition_count"] == 1
    assert audit["replacement_verb_family_reference_count"] == 2
    assert audit["interpret_verb_enabled"] is True
    assert audit["interpret_formal_verb_enabled"] is True
    assert audit["negative_interpret_predicate_present"] is False
    assert audit["changed_function_definitions"] == []


def test_m12ba_fixture_gate_preserves_positive_and_negative_boundaries() -> None:
    audit = m12ba._fixture_audits()

    assert audit["status"] == "PASS"
    assert audit["historical"]["status"] == "PASS"
    assert len(audit["positive"]) == 6
    assert len(audit["negative"]) == 5
    assert audit["negative_interpret_predicate_false_accept_count"] == 0
    assert audit["unknown_replacement_concept_false_accept_count"] == 0
    assert audit["financial_sector_true_misuse_false_accept_count"] == 0


def test_m12ba_completion_field_manifest_is_unique_and_complete() -> None:
    assert len(m12ba._COMPLETION_FIELDS) == len(set(m12ba._COMPLETION_FIELDS))
    for field in (
        "replacement_application_verb_contract_version",
        "m12az_40_row_reaudit_status",
        "fictional_replacement_verb_false_reject_count",
        "shadow_replacement_verb_false_reject_count",
        "fresh_real_proof_readiness",
        "production_readiness",
    ):
        assert field in m12ba._COMPLETION_FIELDS


def test_m12ba_output_is_local_only() -> None:
    assert m12ba.NEXT_SCOPE == (
        "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
    )
    assert m12ba.OUTPUT.parts[0] == "artifacts"
    assert m12ba.REPORTS.parts[:2] == ("docs", "reports")
