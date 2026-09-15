from __future__ import annotations

from pathlib import Path

import pytest

from app.services.financial_framework_claim_service import (
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
)
from scripts import boundary_band_application_scope_m12aa as audit


def test_required_artifact_names_are_complete_and_unique():
    assert set(audit.SLUGS) == set(range(1, 82))
    assert len(set(audit.SLUGS.values())) == 81


def test_latest_authoritative_bundle_integrity_is_independently_verified():
    if not audit.LATEST.is_file():
        pytest.skip("authoritative predecessor bundle is a local evidence artifact")
    result = audit.latest_result_integrity()
    assert result["status"] == "PASS", result
    assert result["sha256"] == audit.LATEST_SHA
    assert result["zip_entry_count"] == 193
    assert result["duplicate_member_count"] == 0
    assert result["secret_scan_failures"] == []


def test_stop_policy_distinguishes_hard_failures_from_observations():
    result = audit.canary_stop_fixture_audit()
    assert result["status"] == "PASS", result
    assert all(row["observed"]["stop_generation"] for row in result["rows"][:3])
    assert not any(row["observed"]["stop_generation"] for row in result["rows"][3:])


def test_fic_fin_05_boundary_band_is_a_non_stopping_calibration_contract():
    result = audit.band_fixture_audit()
    assert result["status"] == "PASS", result
    rows = {row["id"]: row for row in result["rows"]}
    assert rows["BAND-01"]["observed"]["status"] == "PASS"
    assert rows["BAND-02"]["observed"]["status"] == "PASS"
    assert rows["BAND-03"]["observed"]["status"] == "OBSERVATION"
    assert rows["BAND-04"]["observed"]["status"] == "OBSERVATION"
    assert not any(row["observed"]["stop_generation"] for row in rows.values())


def test_framework_application_scope_fixtures_have_zero_false_decisions():
    positive = audit.application_scope_fixture_audit("positive")
    negative = audit.application_scope_fixture_audit("negative")
    assert positive["status"] == "PASS", positive
    assert negative["status"] == "PASS", negative
    assert positive["false_reject_count"] == 0
    assert negative["false_accept_count"] == 0


def test_exact_m12z_fic_fin_08_output_passes_without_rewrite():
    result = audit.exact_m12z_fic_fin_08_replay()
    assert result["status"] == "PASS", result
    assert result["historical_raw_output_rewritten"] is False
    assert result["actual_industrial_framework_misuse_count"] == 0
    assert {row["role"] for row in result["reference_roles"]} == {
        "CONTRASTIVE_REPLACEMENT"
    }


def test_m12z_business_delta_replay_remains_closed():
    result = audit.z.exact_m12y_delta_replay()
    assert result["status"] == "PASS", result
    assert result["validator_false_reject_count"] == 0
    assert result["validator_false_accept_count"] == 0


def test_cross_field_exclusion_and_application_is_contradictory_mixed_use():
    candidate = {
        "sector_interpretation": {
            "text": "순부채 틀 대신 규제자본을 본다.",
            "evidence_refs": [],
        },
        "sell_drivers": [
            {
                "text": "하지만 순부채가 높아서 SELL이다.",
                "evidence_refs": [],
            }
        ],
    }
    claims = candidate_financial_framework_claims(candidate)
    assert claims
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRADICTORY_MIXED_USE
    }


def test_ambiguous_material_application_fails_closed_as_unresolved():
    candidate = {
        "core_investment_judgment": {
            "text": "순부채가 부담일 수 있다.",
            "evidence_refs": [],
        }
    }
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.role for claim in claims} == {FrameworkReferenceRole.UNRESOLVED}


def test_prompt_threshold_and_runtime_contracts_are_frozen():
    root = audit.read(audit.ROOT)
    assert audit._freeze_paths(("app/services/directional_balance_service.py",))["status"] == "PASS"
    assert root["production_freeze"]["buy_threshold"] == 6.0
    assert root["production_freeze"]["sell_threshold"] == 6.0
    assert root["production_freeze"]["increment"] == 0.5
    assert (
        root["runtime"]["model"],
        root["runtime"]["effort"],
        root["runtime"]["timeout_seconds"],
        root["runtime"]["subjects_per_context"],
        root["runtime"]["wrapper_retry_count"],
    ) == ("gpt-5.6-sol", "xhigh", 1800, 4, 0)


def test_canary_refuses_failed_gate_and_existing_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "OUTPUT", tmp_path)
    audit.write(tmp_path / "phase-a-receipt.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="m12aa_phase_a_not_passed"):
        audit.run()

    audit.write(
        tmp_path / "phase-a-receipt.json",
        {
            "status": "PASS",
            "code_file_sha256": {},
            "config_file_sha256": {},
            "model_inputs": {"contexts": []},
        },
    )
    audit.write(tmp_path / "canary-stop.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="whole_generation_retry_forbidden"):
        audit.run()


def test_no_production_prompt_or_runtime_surface_is_changed_by_m12aa():
    for path in (
        "app/services/directional_balance_service.py",
        "app/services/daily_monitor_service.py",
        "app/services/daily_digest_renderer.py",
        "app/services/current_price_context_service.py",
    ):
        assert Path(path).is_file()
        assert audit._freeze_paths((path,))["status"] == "PASS"
