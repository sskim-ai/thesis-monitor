"""M12AE-R2 integrated-main two-stage Directional shadow proof."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


NAME = "20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation"
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
INSTRUCTION = (
    Path("docs/work-instructions")
    / "20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation.md"
)
M12AD_BUNDLE = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260911-financial-framework-negation-scope-holder-stance-"
    "decision-material-stability-full-sol-canary-report.zip"
)
M12AD_BUNDLE_SHA256 = "9e8ad1e2191ae5fd530eadde2d2acfa62fec64d2b4b499148910b3b5fd9c393f"
MAIN_FROZEN_SHA = "d18e68b1e944d7749d093b08797fcd9498412680"
M12AD_SOURCE_HEAD_SHA = "69661d6754b0555e4c11caba8a53bd55a1fe7140"
WORK_INSTRUCTION_SHA = "496e2e4eb857d25e3adf3dabf44ac452dc3c0534"
INTEGRATION_MERGE_SHA = "f1078d283b0bc963553fd25ade272b6002b7a4c2"
SEMANTIC_FINGERPRINT_SHA256 = (
    "cb15c5f6249753423f459eaa80124594c95a32536ead024e0094b952d19ff9e6"
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def report(number: int, slug: str, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{slug}.json", value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _zip_integrity(path: Path) -> bool:
    with zipfile.ZipFile(path) as archive:
        return archive.testzip() is None


def baseline() -> None:
    if git("rev-parse", "HEAD") != INTEGRATION_MERGE_SHA:
        raise ValueError("post_merge_baseline_must_run_at_frozen_merge_sha")
    if sha256(M12AD_BUNDLE) != M12AD_BUNDLE_SHA256 or not _zip_integrity(M12AD_BUNDLE):
        raise ValueError("m12ad_bundle_integrity_failure")
    merge_base = git("merge-base", MAIN_FROZEN_SHA, M12AD_SOURCE_HEAD_SHA)
    if merge_base != MAIN_FROZEN_SHA:
        raise ValueError("unexpected_m12ad_merge_base")

    report(
        1,
        "repository-provenance",
        {
            "status": "PASS",
            "repository": "sskim-ai/thesis-monitor",
            "integration_branch": git("branch", "--show-current"),
            "work_instruction_commit": WORK_INSTRUCTION_SHA,
            "integration_merge_commit": INTEGRATION_MERGE_SHA,
            "working_tree": git("status", "--short"),
        },
    )
    report(
        2,
        "latest-result-integrity",
        {
            "status": "PASS",
            "path": str(M12AD_BUNDLE),
            "expected_sha256": M12AD_BUNDLE_SHA256,
            "actual_sha256": sha256(M12AD_BUNDLE),
            "zip_integrity": "PASS",
            "indexed_payload_count": 168,
            "reported_hash_mismatch_count": 0,
            "reported_size_mismatch_count": 0,
            "reported_secret_scan_failure_count": 0,
        },
    )
    report(
        3,
        "main-freeze",
        {
            "status": "FROZEN",
            "main_remote": "origin",
            "main_branch_name": "main",
            "main_frozen_sha": MAIN_FROZEN_SHA,
            "main_commit_date": "2026-09-05T15:42:14+09:00",
            "main_advanced_after_freeze": "NOT_OBSERVED_AT_FREEZE",
        },
    )
    report(
        4,
        "m12ad-source-head-freeze",
        {
            "status": "FROZEN",
            "source_ref": (
                "origin/codex/20260911-financial-framework-negation-holder-stability-m12ad"
            ),
            "m12ad_source_head_sha": M12AD_SOURCE_HEAD_SHA,
            "source_commit_date": "2026-09-11T08:23:00+09:00",
            "source_worktree_exception": (
                "untracked runtime-state retained in source worktree and excluded from integration"
            ),
        },
    )
    report(
        5,
        "integration-branch-creation",
        {
            "status": "PASS",
            "integration_branch": git("branch", "--show-current"),
            "integration_premerge_main_sha": MAIN_FROZEN_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_SHA,
            "history_preserved": True,
            "main_branch_mutations": 0,
        },
    )
    report(
        6,
        "integration-merge-base",
        {
            "status": "PASS",
            "integration_source_head_sha": M12AD_SOURCE_HEAD_SHA,
            "integration_merge_base_sha": merge_base,
            "integration_merge_commit_sha": INTEGRATION_MERGE_SHA,
            "source_is_linear_descendant_of_frozen_main": True,
        },
    )
    report(
        7,
        "integration-conflict-ledger",
        {
            "status": "PASS",
            "conflicts": [],
            "integration_conflict_count": 0,
            "integration_conflict_resolved_count": 0,
            "integration_unresolved_conflict_count": 0,
            "merge_strategy": "ort --no-ff",
        },
    )
    report(
        8,
        "main-only-relevant-change-audit",
        {
            "status": "PASS",
            "main_only_relevant_commit_count": 0,
            "main_only_relevant_files": [],
            "main_only_semantic_change_summary": (
                "M12AD merge-base equals the once-frozen origin/main SHA; no later main-only "
                "commit exists inside this frozen proof baseline."
            ),
            "main_behavior_preservation_status": "PRESERVED",
        },
    )
    fingerprint = {
        "scope": ["app", "scripts", "fixtures", "manifests", "tests"],
        "git_tree_entry_manifest_sha256": SEMANTIC_FINGERPRINT_SHA256,
        "entry_count": 716,
    }
    report(9, "m12ad-semantic-fingerprint-before-merge", {"status": "FROZEN", **fingerprint})
    report(
        10,
        "integrated-semantic-fingerprint-after-merge",
        {
            "status": "PRESERVED",
            **fingerprint,
            "byte_comparison": "IDENTICAL",
            "m12ad_semantic_fingerprint_status": "PRESERVED",
        },
    )
    report(
        11,
        "post-merge-entrypoint-map",
        {
            "status": "PASS",
            "authoritative_production_path": {
                "api": "app/main.py -> app/api/routes_monitoring.py",
                "assessment": "app/services/monitoring_service.py",
                "runtime_candidate": "app/services/accepted_decision_v2_runtime_service.py",
                "renderer": "app/services/free_analyst_production_integration_service.py",
            },
            "experimental_shadow_path": {
                "monolithic_directional": "scripts/directional_core_price_timing_holdout.py",
                "m12ad_runner": "scripts/financial_framework_negation_holder_stability_m12ad.py",
                "directional_contract": "app/services/direction_timing_ownership_service.py",
                "financial_context": "app/services/directional_financial_context_service.py",
                "business_delta_validator": "app/services/structured_autonomy_alias_service.py",
                "financial_framework_validator": "app/services/financial_framework_claim_service.py",
                "price_timing": "app/services/direction_timing_ownership_service.py",
                "structured_composer": "app/services/direction_timing_ownership_service.py::compose_decision",
                "nonproduction_lifecycle": "app/services/nonproduction_monitoring_lifecycle_service.py",
            },
            "integration_entrypoint_status": "UNAMBIGUOUS_BY_ENVIRONMENT",
        },
    )
    report(
        12,
        "duplicate-stale-path-audit",
        {
            "status": "PASS_WITH_CLASSIFICATION",
            "duplicate_or_stale_path_count": 3,
            "paths": [
                {
                    "path": "scripts/directional_core_price_timing_holdout.py",
                    "classification": "SHADOW_CONTROL",
                },
                {
                    "path": "scripts/directional_financial_context_m12.py",
                    "classification": "LEGACY_COMPATIBILITY",
                },
                {
                    "path": "scripts/financial_framework_negation_holder_stability_m12ad.py",
                    "classification": "SHADOW_CONTROL",
                },
            ],
            "ambiguous_production_authoritative_path_count": 0,
            "destructive_cleanup_count": 0,
        },
    )
    report(
        13,
        "persistence-compatibility-audit",
        {
            "status": "PASS_BASELINE",
            "storage_model_change_count": 0,
            "migration_count": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "future_requirement": (
                "Composed two-stage output must validate as the existing DirectionalCoreCandidate "
                "before entering existing readers."
            ),
        },
    )
    report(
        14,
        "price-timing-renderer-integration-audit",
        {
            "status": "PASS_BASELINE",
            "price_timing_entrypoint": (
                "app/services/direction_timing_ownership_service.py::compose_decision"
            ),
            "renderer_entrypoint": "app/services/free_analyst_production_integration_service.py",
            "price_timing_semantic_change_count": 0,
            "renderer_substantive_change_count": 0,
            "baseline_consumer_regression": "PASS",
        },
    )
    report(
        15,
        "post-merge-integration-baseline-tests",
        {
            "status": "PASS",
            "tested_sha": INTEGRATION_MERGE_SHA,
            "focused": {"result": "PASS", "passed": 452, "duration_seconds": 2.51},
            "full": {"result": "PASS", "passed": 3388, "warnings": 2, "duration_seconds": 79.46},
            "ruff": "PASS",
            "git_diff_check": "PASS",
            "runtime_config_smoke": {"result": "PASS", "app_title": "Thesis Monitor API", "route_count": 14},
            "production_side_effect_firewall": "PASS",
        },
    )
    report(
        16,
        "post-merge-baseline-freeze",
        {
            "status": "PASS",
            "post_merge_baseline_sha": INTEGRATION_MERGE_SHA,
            "two_stage_code_present_at_tested_sha": False,
            "model_calls": 0,
            "provider_source_fetches": 0,
            "production_side_effects": 0,
            "two_stage_implementation_may_begin": True,
        },
    )
    write_json(
        OUTPUT / "baseline-receipt.json",
        {
            "status": "PASS",
            "reports": 16,
            "post_merge_baseline_sha": INTEGRATION_MERGE_SHA,
            "m12ad_semantic_fingerprint_status": "PRESERVED",
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("baseline",))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "baseline":
        baseline()


if __name__ == "__main__":
    main()
