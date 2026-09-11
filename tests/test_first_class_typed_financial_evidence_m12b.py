from __future__ import annotations

from scripts import first_class_typed_financial_evidence_m12b as m12b
from scripts import financial_boundary_calibration_m12e as m12e
from scripts import financial_exclusion_expectation_m12u as m12u


def test_projection_is_selected_only_first_class_and_catalog_ordered() -> None:
    audit = m12b._projection_audit("m12b-test-generation")

    assert audit["status"] == "PASS"
    assert audit["selected_typed_financial_ref_count"] == 15
    assert audit["first_class_typed_financial_projection_count"] == 15
    assert audit["suppressed_typed_projection_count"] == 0
    assert audit["alias_renumber_count"] == 0
    assert audit["duplicate_alias_count"] == 0
    assert audit["catalog_order_failure_count"] == 0
    assert audit["neutral_financial_statement_count"] == 15
    assert audit["raw_json_statement_count"] == 0
    assert audit["verdict_statement_count"] == 0
    assert audit["financial_decision_context_detail_removed_count"] == 0


def test_fic_fin_06_and_negative_controls_match_frozen_contract() -> None:
    audit = m12b._projection_audit("m12b-test-generation")
    rows = {row["ticker"]: row for row in audit["rows"]}

    assert {"E03", "E04"} <= set(rows["FIC-FIN-06"]["first_class_aliases"])
    assert rows["FIC-FIN-07"]["first_class_typed_count"] == 0
    assert rows["FIC-FIN-07"]["before"] == rows["FIC-FIN-07"]["after"]
    assert rows["FIC-FIN-08"]["first_class_typed_count"] == 0


def test_old_and_corrected_financial_grounding_regressions_are_preserved() -> None:
    regressions = m12b._historical_regressions()

    assert regressions["old_fic_fin_03_regression_status"] == "PASS"
    assert regressions["old_fic_fin_06_regression_status"] == "PASS"
    assert regressions["fic06"]["row"]["status"] == "FAIL"
    assert {
        "material_financial_anchor_not_used",
        "working_capital_checkpoint_not_used",
        "narrative_substitution_failure",
    } <= set(regressions["fic06"]["row"]["errors"])
    assert regressions["corrected_fic_fin_06_status"] == "PASS"


def test_frozen_semantic_surfaces_remain_unchanged() -> None:
    from scripts import business_delta_alias_balance_confidence_m12z as z

    frozen = m12b._frozen_surfaces()

    # Historical changes plus the M12AG source-ownership full-file hash.
    assert all(
        row["status"] == "PASS"
        for name, row in frozen.items()
        if name
        not in {"calibration", "financial_validator", "core_prompt", "output_schema"}
    )
    scope = m12u.scope_audit()
    assert scope["status"] == "FAIL"
    assert [key for key, value in scope["checks"].items() if not value] == [
        "unrelated_files_unchanged",
        "one_appended_paragraph",
        "helper_unrelated_ast_unchanged",
    ]
    assert scope["unexpected_file_changes"] == [
        "app/services/directional_financial_context_service.py"
    ]
    assert z.without_m12z_prompt(scope["after_prompt"]).startswith(scope["before_prompt"])
    assert m12e.without_prompt(m12b._git_file(m12b.BASE_SHA, m12e.SERVICE)) == (
        m12e.without_prompt(m12e.Path(m12e.SERVICE).read_text())
    )
    assert frozen["core_prompt"]["change_count"] == 1
    assert frozen["timing_prompt"]["change_count"] == 0
    assert frozen["selector"]["change_count"] == 0
    assert frozen["financial_validator"]["change_count"] == 1
    assert frozen["output_schema"]["status"] == "FAIL"
    assert frozen["qtd_ytd_validator"]["change_count"] == 0
    assert frozen["alias_builder"]["change_count"] == 0


def test_typed_projection_cannot_leak_price_technical_supply_or_sector_context() -> None:
    projection = m12b._projection_audit("m12b-test-generation")
    non_leak = m12b._non_leak_audit(projection)

    assert non_leak["status"] == "PASS"
    assert non_leak["typed_financial_price_ref_count"] == 0
    assert non_leak["typed_financial_technical_ref_count"] == 0
    assert non_leak["typed_financial_supply_ref_count"] == 0
    assert non_leak["financial_sector_generic_financial_context_leak_count"] == 0


def test_authoritative_m12a_bundle_remains_integrity_clean() -> None:
    integrity = m12b._latest_result_integrity()

    assert integrity["status"] == "PASS"
    assert integrity["checksum_match"]
    assert integrity["indexed_payload_count"] == 46
    assert integrity["artifact_hash_mismatch_count"] == 0
    assert integrity["artifact_size_mismatch_count"] == 0
    assert integrity["artifact_secret_scan_failure_count"] == 0
