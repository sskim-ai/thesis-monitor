from __future__ import annotations

import inspect

from scripts import market_expectation_independence_m12ap as runner


def test_m12ap_runner_freezes_required_local_only_contract() -> None:
    assert len(runner.SLUGS) == 128
    assert tuple(runner.SLUGS) == tuple(range(1, 129))
    assert len(set(runner.SLUGS.values())) == 128
    assert len(runner._required_report_files()) == 128
    assert (runner.MODEL, runner.EFFORT, runner.TIMEOUT_SECONDS) == (
        "gpt-5.6-sol",
        "xhigh",
        1800,
    )
    assert runner.EXPECTED_FICTIONAL_CALLS == 12
    assert runner.EXPECTED_FICTIONAL_ROWS == 24
    assert runner.EXPECTED_SHADOW_CALLS == 18
    assert runner.EXPECTED_ACTIVE_COUNT == 22
    assert runner.ICLOUD.name == "Thesis Monitor"


def test_m12ap_fictional_projection_is_complete_and_conservative() -> None:
    manifest = runner._projection_manifest("m12ap-test")
    assert manifest["status"] == "PASS"
    assert manifest["subject_count"] == 8
    assert manifest["expectation_ref_count"] == 8
    assert manifest["expectation_view_projection_mismatch_count"] == 0
    assert manifest["conditional_context_only_count"] == 1
    assert manifest["independence_unknown_count"] == 7
    assert manifest["independent_directional_support_count"] == 0
    fic_fin_05 = next(
        row for row in manifest["rows"] if row["ticker"] == "FIC-FIN-05"
    )
    assert fic_fin_05["view"]["expectations"][0] == {
        "ref": "E07",
        "role": "CONDITIONAL_CONTEXT_ONLY",
        "material_anchor_eligible": False,
        "dominant_evidence_eligible": False,
        "reason": "STRUCTURED_DEPENDENCY_ON_UNRESOLVED_CONDITION",
        "independence_basis_refs": [],
        "dependency_refs": ["E08"],
    }


def test_m12ap_dynamic_schema_restricts_only_anchor_owned_fields() -> None:
    audit = runner._schema_audit("m12ap-test")
    assert audit["status"] == "PASS"
    assert "E07" not in audit["material_anchor_aliases"]
    assert "E07" not in audit["dominant_evidence_aliases"]
    assert "E07" in audit["context_aliases"]
    assert audit["context_only_alias"] == "E07"


def test_m12ap_runner_preserves_hard_stop_and_no_hotfix_contract() -> None:
    fictional_source = inspect.getsource(runner.run_fictional)
    shadow_source = inspect.getsource(runner.run_shadow)
    completion_source = inspect.getsource(runner.closeout)
    assert "m12ao.run_fictional" in fictional_source
    assert "m12ao.run_shadow" in shadow_source
    for field in (
        "remote_push_count",
        "raw_model_artifact_remote_push_count",
        "main_branch_mutations",
        "main_merges",
        "deployments",
        "production_sends",
        "fresh_real_proof_readiness",
        "production_readiness",
    ):
        assert field in completion_source


def test_m12ap_prompt_contract_is_already_present_without_prompt_edit() -> None:
    audit = runner._prompt_audit()
    assert audit["status"] == "PASS"
    assert audit["unchanged_from_base"] is True
    assert audit["existing_contract_present"] is True
    assert audit["model_prompt_semantic_change_count"] == 0
