from __future__ import annotations

from pathlib import Path

from scripts import financial_sector_exclusion_scope_m12aq as runner


def test_report_contract_is_complete_and_unique() -> None:
    assert len(runner.SLUGS) == 130
    assert set(runner.SLUGS) == set(range(1, 131))
    assert len(set(runner.SLUGS.values())) == 130
    assert runner.SLUGS[42] == "new-fictional-model-call-gate"
    assert runner.SLUGS[59] == "fictional-financial-sector-scope-audit"
    assert runner.SLUGS[85] == "shadow-financial-sector-scope-audit"
    assert runner.SLUGS[130] == "program-completion"


def test_execution_topology_and_local_only_model_contract_are_frozen() -> None:
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.TIMEOUT_SECONDS == 1800
    assert runner.EXPECTED_FICTIONAL_CALLS == 12
    assert runner.EXPECTED_FICTIONAL_ROWS == 24
    assert runner.EXPECTED_SHADOW_CALLS == 18
    assert runner.EXPECTED_ACTIVE_COUNT == 22
    assert runner.OUTPUT.name == runner.NAME
    assert runner.REPORTS.name == runner.NAME


def test_deterministic_scope_fixture_and_classifier_audits_pass() -> None:
    assert runner._classifier_code_audit()["status"] == "PASS"
    fixture = runner._fixture_audit()
    assert fixture["status"] == "PASS"
    assert fixture["positive_count"] == 6
    assert fixture["negative_count"] == 5
    assert runner._prior_exclusion_audit()["status"] == "PASS"
    assert runner._mixed_current_claim_audit()["status"] == "PASS"


def test_financial_sector_scope_audit_uses_shared_application_roles() -> None:
    safe = {
        "ticker": "FIC-FIN-08",
        "errors": [],
        "financial_framework_roles": {
            "application_count": 0,
            "claims": [
                {
                    "framework": "net_debt",
                    "role": "CONTRASTIVE_REPLACEMENT",
                },
                {
                    "framework": "working_capital",
                    "role": "CONTRASTIVE_REPLACEMENT",
                },
            ],
        },
        "financial_semantics": {"errors": []},
    }
    unsafe = {
        **safe,
        "financial_framework_roles": {
            "application_count": 1,
            "claims": [
                {
                    "framework": "net_debt",
                    "role": "ASSERTED_STATE",
                }
            ],
        },
    }
    safe_audit = runner._framework_scope_audit(
        (("stage1", [safe]),), financial_sector_tickers={"FIC-FIN-08"}
    )
    unsafe_audit = runner._framework_scope_audit(
        (("stage1", [unsafe]),), financial_sector_tickers={"FIC-FIN-08"}
    )
    assert safe_audit["status"] == "PASS"
    assert safe_audit["shared_application_scope_consistency"] == "PASS"
    assert safe_audit["financial_sector_exclusion_false_reject_count"] == 0
    assert unsafe_audit["status"] == "FAIL"
    assert unsafe_audit["financial_sector_true_misuse_count"] == 1


def test_bundle_inventory_keeps_local_proof_material_in_scope() -> None:
    assert runner.RUNNER in runner.CRITICAL_CODE_PATHS
    assert runner.SHADOW_MANIFEST_MODULE in runner.CRITICAL_CODE_PATHS
    assert runner.ARCHITECTURE.name == (
        "FINANCIAL_SECTOR_EXCLUSION_CONNECTIVE_SCOPE.md"
    )
    assert runner.WORK_INSTRUCTION.name.endswith("full-shadow.md")
    required = runner._required_report_files()
    assert len(required) == 130
    assert required[41].name.startswith("42-new-fictional-model-call-gate")
    assert required[-1].name.startswith("130-program-completion")


def test_shadow_manifest_is_canonicalized_and_verified_before_model_calls() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")

    assert "canonicalize_shadow_manifest_state(" in source
    assert "allow_legacy=False" in source
    assert "_canonical_shadow_verifier(state, subject=\"SHADOW\")" in source
    assert "capability._verify_frozen_state = _canonical_shadow_verifier" in source
