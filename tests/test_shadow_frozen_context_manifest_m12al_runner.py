from __future__ import annotations

import json
from pathlib import Path

from scripts import shadow_frozen_context_manifest_m12al as runner
from scripts.shadow_frozen_context_manifest import (
    CANONICAL_CONTEXT_KEY,
    CONTRACT_VERSION,
    LEGACY_CONTEXT_KEY,
    MAX_CONTEXT_TICKERS,
)


def _fixture() -> dict[str, object]:
    return json.loads(runner.FIXTURE_FILE.read_text(encoding="utf-8"))


def test_runner_contract_constants_match_fixture() -> None:
    fixture = _fixture()

    assert CONTRACT_VERSION == fixture["contract_version"]
    assert CANONICAL_CONTEXT_KEY == fixture["canonical_context_key"]
    assert LEGACY_CONTEXT_KEY == fixture["legacy_context_key"]
    assert MAX_CONTEXT_TICKERS == fixture["max_context_tickers"]
    assert runner.MODEL == fixture["model"]
    assert runner.EFFORT == fixture["reasoning_effort"]
    assert runner.EXPECTED_ACTIVE_COUNT == fixture["expected_active_count"]
    assert runner.EXPECTED_CONTEXTS == fixture["expected_context_count"]
    assert runner.EXPECTED_MODEL_CALLS == fixture["expected_model_calls"]


def test_required_report_contract_is_complete_and_unique() -> None:
    fixture = _fixture()

    assert len(runner.SLUGS) == fixture["required_report_count"]
    assert set(runner.SLUGS) == set(range(1, 86))
    assert len(set(runner.SLUGS.values())) == 85


def test_authoritative_m12ak_identity_is_frozen() -> None:
    fixture = _fixture()

    assert runner.M12AK_BUNDLE_SHA256 == fixture["m12ak_bundle_sha256"]
    assert (
        runner.M12AK_FICTIONAL_GENERATION_ID
        == fixture["m12ak_fictional_generation_id"]
    )


def test_m12al_writer_normalizes_legacy_output_before_freeze() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")

    assert "canonicalize_shadow_manifest_state(" in source
    assert 'allow_legacy=False' in source
    assert "_m12al_frozen_state_verifier" in source


def test_m12al_freeze_detects_the_later_m12am_stage2_matcher_change() -> None:
    audit = runner._semantic_hash_audit()

    assert audit["status"] == "FAIL"
    assert audit["legacy_model_facing_function_mismatches"] == [
        "_batch_schema",
        "_enriched_contexts",
        "_full_audit",
        "_stage1_audit",
    ]
    assert not {
        "_monolithic_prompt",
        "_stage1_prompt",
        "_views",
    }.intersection(audit["legacy_model_facing_function_mismatches"])
    assert audit["semantic_file_mismatches"] == [
        "app/services/business_delta_evidence_service.py",
        "app/services/structured_autonomy_alias_service.py",
        "scripts/directional_financial_context_m12.py",
        "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"
    ]
    assert audit["base_model_facing_function_mismatches"] == ["_stage2_audit"]
    assert audit["context_preserving_finalizer_change_count"] == 0


def test_formal_fictional_proof_is_reusable_without_new_calls() -> None:
    proof = runner._m12ak_fictional_proof()

    assert proof["status"] == "PASS"
    assert proof["reuse_status"] == "REUSE_AUTHORIZED"
    assert proof["model_calls"] == 12
    assert proof["final_compositions"] == 24


def test_shadow_topology_is_six_contexts_and_eighteen_calls() -> None:
    tickers = tuple(f"T{index:02d}" for index in range(1, 23))
    groups = runner._expected_groups(tickers)

    assert tuple(map(len, groups)) == (4, 4, 4, 4, 4, 2)
    assert len(groups) == 6
    assert len(groups) * 3 == 18
