from __future__ import annotations

from scripts import prospective_condition_nominalization_m12aw as m12aw


def test_m12aw_report_sequence_is_complete() -> None:
    assert len(m12aw.SLUGS) == 150
    assert m12aw.SLUGS[1] == "repository-provenance"
    assert m12aw.SLUGS[27] == "m12av-completed-40-row-offline-reaudit"
    assert m12aw.SLUGS[72] == "fictional-nominal-condition-scope-audit"
    assert m12aw.SLUGS[102] == "shadow-nominal-condition-scope-audit"
    assert m12aw.SLUGS[150] == "program-completion"


def test_m12aw_nominal_condition_fixture_gate_passes() -> None:
    audit = m12aw._m12aw_nominal_condition_fixtures()
    assert audit["status"] == "PASS"
    assert len(audit["positive"]) == 5
    assert len(audit["current_negative"]) == 5
    assert len(audit["no_configured_support"]) == 2
    assert audit["same_clause_current"]["status"] == "PASS"
    assert audit["same_field_separate"]["status"] == "PASS"


def test_m12aw_model_facing_surfaces_are_unchanged() -> None:
    audit = m12aw._semantic_surface_hashes()
    assert audit["status"] == "PASS"
    assert audit["total_semantic_change_count"] == 0


def test_m12aw_local_safety_controls_pass() -> None:
    audit = m12aw._m12av_clause_scope_fixtures()
    assert audit["status"] == "PASS"
