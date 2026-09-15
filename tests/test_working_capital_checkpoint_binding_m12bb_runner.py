from __future__ import annotations

from scripts import directional_financial_context_m12g as grounding
from scripts import working_capital_checkpoint_binding_m12bb as m12bb


def test_m12bb_report_sequence_is_exact() -> None:
    assert len(m12bb.SLUGS) == 164
    assert len(set(m12bb.SLUGS.values())) == 164
    assert m12bb.SLUGS[1] == "repository-provenance"
    assert m12bb.SLUGS[63] == "new-fictional-model-call-gate"
    assert m12bb.SLUGS[83] == "fictional-working-capital-checkpoint-binding-audit"
    assert m12bb.SLUGS[115] == "shadow-working-capital-checkpoint-binding-audit"
    assert m12bb.SLUGS[164] == "program-completion"


def test_m12bb_frozen_runtime_contract() -> None:
    assert m12bb.MODEL == "gpt-5.6-sol"
    assert m12bb.EFFORT == "xhigh"
    assert m12bb.TIMEOUT_SECONDS == 1800
    assert m12bb.EXPECTED_FICTIONAL_CALLS == 12
    assert m12bb.EXPECTED_FICTIONAL_ROWS == 24
    assert m12bb.EXPECTED_SHADOW_CALLS == 18
    assert m12bb.EXPECTED_ACTIVE_COUNT == 22
    assert m12bb.WORK_INSTRUCTION_COMMIT == (
        "22a6c15457e61d9e107e2970ee5c421dbe5247b9"
    )


def test_m12bb_checkpoint_surface_matches_existing_hard_validator() -> None:
    assert m12bb.CHECKPOINT_FIELDS == tuple(grounding._CHECKPOINT_PATH_MARKERS)
    assert "risk_context" in m12bb.CHECKPOINT_FIELDS
    assert "buy_drivers" in m12bb.CHECKPOINT_FIELDS
    assert "sell_drivers" in m12bb.CHECKPOINT_FIELDS


def test_m12bb_uses_one_generic_binding_rule_without_case_exceptions() -> None:
    prompt = m12bb.WC_BINDING_PROMPT

    assert "metric_to_typed_aliases" in prompt
    assert "same claim" in prompt
    assert "current output schema" in prompt
    assert "Narrative/context refs may supplement but never substitute" in prompt
    assert "FIC-FIN-06" not in prompt
    assert "inventory" in prompt
    assert "trade-receivables" in prompt
    assert "trade-payables" in prompt


def test_m12bb_schema_and_external_contract_remain_unchanged() -> None:
    assert m12bb.WC_BINDING_CONTRACT == (
        "working-capital-checkpoint-typed-ref-binding-v1"
    )
    assert m12bb.WC_BINDING_VIEW_CONTRACT == (
        "working-capital-checkpoint-binding-view-v1"
    )
    assert m12bb.WC_BINDING_PROMPT.count("WORKING_CAPITAL_CHECKPOINT_BINDING") == 1
    assert m12bb.NEXT_SCOPE == (
        "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
    )


def test_m12bb_binding_validation_starts_after_upstream_preflight(monkeypatch) -> None:
    monkeypatch.setattr(
        m12bb.capability,
        "_stage1_audit",
        m12bb._ORIGINAL_STAGE1_AUDIT,
    )
    monkeypatch.setattr(
        m12bb.capability,
        "_full_audit",
        m12bb._ORIGINAL_FULL_AUDIT,
    )

    m12bb._install_model_input_hooks()
    assert m12bb.capability._stage1_audit is m12bb._ORIGINAL_STAGE1_AUDIT
    assert m12bb.capability._full_audit is m12bb._ORIGINAL_FULL_AUDIT

    m12bb._install_validation_hooks()
    assert m12bb.capability._stage1_audit is m12bb._patched_stage1_audit
    assert m12bb.capability._full_audit is m12bb._patched_full_audit


def test_m12bb_output_is_local_only() -> None:
    assert m12bb.OUTPUT.parts[0] == "artifacts"
    assert m12bb.REPORTS.parts[:2] == ("docs", "reports")
    assert m12bb.CRITICAL_CODE_PATHS[-2:] == (
        m12bb.ARCHITECTURE,
        m12bb.WORK_INSTRUCTION,
    )


def test_m12bb_completion_field_manifest_is_unique_and_complete() -> None:
    assert len(m12bb._COMPLETION_FIELDS) == len(set(m12bb._COMPLETION_FIELDS))
    for field in (
        "wc_checkpoint_binding_architecture",
        "schema_conditional_binding_supported",
        "fictional_wc_grounding_failure_count",
        "shadow_metric_specific_ref_mismatch_count",
        "remote_push_count",
        "production_readiness",
    ):
        assert field in m12bb._COMPLETION_FIELDS
