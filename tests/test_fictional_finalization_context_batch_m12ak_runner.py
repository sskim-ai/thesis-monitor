from __future__ import annotations

import re

from app.services.direction_timing_ownership_service import DirectionalCoreBatch
from scripts import fictional_finalization_context_batch_m12ak as task


def test_required_artifact_names_are_complete_and_unique() -> None:
    assert set(task.SLUGS) == set(range(1, 116))
    assert len(set(task.SLUGS.values())) == 115


def test_authoritative_m12aj_bundle_is_frozen() -> None:
    assert task.LATEST_BUNDLE_SHA256 == (
        "684db3efb089c05d03c51dfcee7c45c14ba804be136848a9bfa6d5eb0d2deb18"
    )
    assert task.LATEST_INDEXED_PAYLOADS == 184
    assert task.LATEST_ZIP_ENTRIES == 185
    assert task.M12AJ_STOP_REASON == (
        "FICTIONAL_FINALIZATION_BATCH_SIZE_CONTRACT_FAILURE"
    )


def test_model_and_topology_remain_frozen() -> None:
    assert (task.MODEL, task.EFFORT, task.TIMEOUT_SECONDS) == (
        "gpt-5.6-sol",
        "xhigh",
        1800,
    )
    assert task.FICTIONAL_REPETITIONS == 3
    assert task.FICTIONAL_MODEL_CALLS == 12
    assert task.FICTIONAL_OUTPUT_COUNT == 24
    assert task.EXPECTED_ACTIVE_COUNT == 22
    assert task.EXPECTED_SHADOW_CONTEXTS == 6
    assert task.EXPECTED_SHADOW_MODEL_CALLS == 18


def test_directional_core_batch_max_items_remains_four() -> None:
    schema = DirectionalCoreBatch.model_json_schema()
    candidates = schema["properties"]["candidates"]
    assert candidates["maxItems"] == 4
    assert task.MAX_CONTEXT_CANDIDATES == 4


def test_legacy_report_mapping_preserves_required_new_artifacts() -> None:
    assert task.LEGACY_REPORT_MAP[28] == 42
    assert set(task.LEGACY_REPORT_MAP[number] for number in range(29, 41)) == set(
        range(45, 57)
    )
    assert set(task.LEGACY_REPORT_MAP[number] for number in range(50, 57)) == set(
        range(69, 76)
    )
    assert set(task.LEGACY_REPORT_MAP[number] for number in range(57, 84)) == (
        set(range(76, 105)) - {80, 83}
    )


def test_runner_contains_no_semantic_override_or_majority_rule() -> None:
    source = task.RUNNER.read_text(encoding="utf-8")
    assert re.search(r'candidate\["business_thesis_change"\]\s*=(?!=)', source) is None
    assert re.search(r"\.business_thesis_change\s*=(?!=)", source) is None
    assert 'model_copy(update={"business_thesis_change"' not in source
    assert "def majority_vote" not in source
    assert "def delta_score" not in source
    assert "ticker_specific_delta" not in source


def test_local_only_firewall_is_explicit() -> None:
    source = task.RUNNER.read_text(encoding="utf-8")
    for field in (
        "provider_source_fetches",
        "production_db_mutations",
        "monitoring_registrations",
        "monitoring_stops",
        "assessment_persistence_mutations",
        "warning_mutations",
        "notification_queue_writes",
        "production_sends",
        "remote_push_count",
        "raw_model_artifact_remote_push_count",
        "main_branch_mutations",
        "main_merges",
        "deployments",
        "automatic_monitoring_resume",
    ):
        assert f'"{field}": 0' in source


def test_readiness_remains_not_ready() -> None:
    source = task.RUNNER.read_text(encoding="utf-8")
    assert '"fresh_real_proof_readiness": "NOT_READY"' in source
    assert '"final_main_merge_readiness": "NOT_READY"' in source
    assert '"production_readiness": "NOT_READY"' in source


def test_m12ak_freeze_detects_the_later_m12am_stage2_matcher_change() -> None:
    fixture = task._fixture()
    assert set(fixture["semantic_file_sha256"]) == {
        str(path) for path in task.SEMANTIC_PATHS
    }
    audit = task._semantic_hash_audit()
    assert audit["status"] == "FAIL"
    assert audit["mismatches"] == [
        "app/services/business_delta_evidence_service.py",
        "app/services/structured_autonomy_alias_service.py",
        "scripts/business_delta_evidence_capability_m12ai.py",
        "scripts/directional_financial_context_m12.py",
        "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"
    ]
