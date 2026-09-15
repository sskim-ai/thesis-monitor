from __future__ import annotations

import re

from scripts import typed_financial_delta_direction_m12aj as task


def test_required_artifact_names_are_complete_and_unique() -> None:
    assert set(task.SLUGS) == set(range(1, 92))
    assert len(set(task.SLUGS.values())) == 91


def test_authoritative_result_and_source_packet_roles_are_separate() -> None:
    assert task.LATEST_BUNDLE_SHA256 == (
        "1b50214ac313dcae0ba9241248eeb55c659cdf17d18aca6b59f7aebf00f8154c"
    )
    assert task.LATEST_INDEXED_PAYLOADS == 114
    assert task.LATEST_ZIP_ENTRIES == 115
    assert task.LATEST_NAME != task.SOURCE_NAME
    assert "business-delta-evidence-capability" in task.LATEST_NAME
    assert "financial-claim-temporal-scope" in task.SOURCE_NAME


def test_model_and_topology_remain_frozen() -> None:
    assert (task.MODEL, task.EFFORT, task.TIMEOUT_SECONDS) == (
        "gpt-5.6-sol",
        "xhigh",
        1800,
    )
    assert task.FICTIONAL_MODEL_CALLS == 12
    assert task.FICTIONAL_OUTPUT_COUNT == 24
    assert task.EXPECTED_ACTIVE_COUNT == 22
    assert task.EXPECTED_SHADOW_MODEL_CALLS == 18


def test_legacy_report_mapping_covers_every_runtime_artifact() -> None:
    expected = set(range(26, 56)) | set(range(57, 84))
    assert expected <= set(task.REPORT_MAP)
    assert 56 not in task.REPORT_MAP
    assert set(task.REPORT_MAP.values()) == set(range(33, 92)) - {50, 70}


def test_runner_contains_no_override_score_or_majority_rule() -> None:
    source = task.RUNNER.read_text(encoding="utf-8")
    assert re.search(r'candidate\["business_thesis_change"\]\s*=(?!=)', source) is None
    assert re.search(r"\.business_thesis_change\s*=(?!=)", source) is None
    assert 'model_copy(update={"business_thesis_change"' not in source
    assert "def majority_vote" not in source
    assert "def delta_score" not in source
    assert "ticker_specific_delta" not in source


def test_production_firewall_is_explicit_in_completion_paths() -> None:
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
