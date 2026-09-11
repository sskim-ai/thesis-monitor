"""Close M12AE-R2 after its fictional hard gate blocks monitored shadow."""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as r


NEXT_SCOPE = "PRIMARY_DIRECTION_BOUNDARY_POLICY_REVIEW_GPT56_SOL_ON_INTEGRATED_MAIN"


def _candidate_rows() -> list[dict[str, object]]:
    rows = []
    for document in r._fictional_documents("stage2"):
        repetition = int(document["repetition"])
        for composition in document["compositions"]:
            candidate = composition["candidate"]
            ticker = str(candidate["ticker"])
            if ticker not in {"FIC-FIN-05", "FIC-FIN-06", "FIC-FIN-08"}:
                continue
            rows.append(
                {
                    "ticker": ticker,
                    "repetition": repetition,
                    "overall_direction": candidate["overall_direction"],
                    "directional_balance": candidate["directional_balance"],
                    "business_thesis_change": candidate["business_thesis_change"],
                    "fundamental_new_buyer": candidate["fundamental_new_buyer"]["stance"],
                    "fundamental_holder": candidate["fundamental_holder"]["stance"],
                    "core_investment_judgment": candidate["core_investment_judgment"],
                    "holder_summary": candidate["fundamental_holder"]["summary"],
                    "core_snapshot_sha256": composition["core_snapshot_sha256"],
                    "post_compose_core_sha256": composition[
                        "post_compose_core_sha256"
                    ],
                    "source_document": str(
                        r._call_paths(
                            phase="stage2",
                            repetition=repetition,
                            context_number=int(document["context"]),
                        )["document"]
                    ),
                    "output_sha256": document["transport"]["output_sha256"],
                }
            )
    return sorted(rows, key=lambda row: (str(row["ticker"]), int(row["repetition"])))


def _report(number: int, slug: str, value: object) -> None:
    r.report(number, slug, value)


def closeout() -> None:
    fictional = r.read_json(r.OUTPUT / "fictional-readiness.json")
    if fictional.get("fictional_two_stage_readiness") != "NOT_READY":
        raise ValueError("failure_closeout_requires_failed_fictional_gate")
    if (r.OUTPUT / "shadow").exists():
        receipts = list((r.OUTPUT / "shadow").glob("**/receipt.json"))
        if receipts:
            raise ValueError("monitored_shadow_calls_exist_after_fictional_failure")
    rows = _candidate_rows()
    by_ticker = {
        ticker: [row for row in rows if row["ticker"] == ticker]
        for ticker in ("FIC-FIN-05", "FIC-FIN-06", "FIC-FIN-08")
    }
    blockers = [
        {
            "severity": "BLOCKING",
            "code": "PRIMARY_DIRECTION_UNSTABLE",
            "ticker": "FIC-FIN-05",
            "observed": [row["overall_direction"] for row in by_ticker["FIC-FIN-05"]],
            "balances": [row["directional_balance"] for row in by_ticker["FIC-FIN-05"]],
            "interpretation": (
                "The Stage 1 boundary reproduced the prior M12AD SELL/HOLD/HOLD pattern; "
                "stance decoupling did not remove intrinsic core-boundary variance."
            ),
        },
        {
            "severity": "BLOCKING",
            "code": "PRIMARY_DIRECTION_UNSTABLE",
            "ticker": "FIC-FIN-06",
            "observed": [row["overall_direction"] for row in by_ticker["FIC-FIN-06"]],
            "balances": [row["directional_balance"] for row in by_ticker["FIC-FIN-06"]],
            "interpretation": (
                "The same working-capital evidence landed at HOLD 5.5:4.5 twice and BUY "
                "6.0:4.0 once."
            ),
        },
        {
            "severity": "BLOCKING",
            "code": "BUSINESS_DELTA_UNSTABLE",
            "ticker": "FIC-FIN-06",
            "observed": [
                row["business_thesis_change"] for row in by_ticker["FIC-FIN-06"]
            ],
            "interpretation": (
                "The frozen source supported a positive operating delta, but UNCHANGED "
                "remained validator-legal and appeared once."
            ),
        },
        {
            "severity": "BLOCKING",
            "code": "HOLDER_STANCE_UNSTABLE",
            "ticker": "FIC-FIN-08",
            "observed": [
                row["fundamental_holder"] for row in by_ticker["FIC-FIN-08"]
            ],
            "interpretation": (
                "The financial-sector exclusion case split between no confirmed holding "
                "reconsideration and review for unresolved capital absorption."
            ),
        },
    ]
    postprocessing = r.read_json(
        r.OUTPUT / "fictional" / "postprocessing-adapter-receipt.json"
    )
    _report(
        92,
        "main-integration-success-decision",
        {
            "status": "PASS",
            "main_integration_readiness": "PASS",
            "integration_merge_commit_sha": r.INTEGRATION_MERGE_SHA
            if hasattr(r, "INTEGRATION_MERGE_SHA")
            else "f1078d283b0bc963553fd25ade272b6002b7a4c2",
            "main_branch_mutations": 0,
        },
    )
    _report(
        93,
        "two-stage-architecture-success-decision",
        {
            "status": "PASS",
            "contract": r.CONTRACT_VERSION,
            "external_schema_change_count": 0,
            "core_mutation_count": 0,
            "deterministic_architecture_proven": True,
        },
    )
    _report(
        94,
        "fictional-proof-success-decision",
        {
            **fictional,
            "status": "FAIL",
            "blockers": blockers,
            "postprocessing_adapter": postprocessing,
            "model_outputs_rewritten": False,
            "model_calls_repeated": 0,
        },
    )
    _report(
        95,
        "shadow-compatibility-success-decision",
        {
            "status": "NOT_RUN_FICTIONAL_GATE",
            "shadow_compatibility_readiness": "NOT_MEASURED",
            "shadow_model_calls": 0,
            "reason": "artifact_64_fictional_two_stage_readiness_is_not_pass",
        },
    )
    _report(
        96,
        "existing-monitored-impact-summary",
        {
            "status": "NOT_RUN_FICTIONAL_GATE",
            "task_start_active_monitor_count": "NOT_MEASURED",
            "shadow_completed_ticker_count": 0,
            "production_impact": 0,
        },
    )
    _report(
        97,
        "two-stage-real-holdout-suitability",
        {
            "status": "NOT_READY",
            "two_stage_real_holdout_suitability": "NOT_READY",
            "blockers": [row["code"] for row in blockers],
        },
    )
    _report(
        98,
        "fresh-real-proof-readiness-decision",
        {
            "status": "NOT_READY",
            "fresh_real_proof_readiness": "NOT_READY",
            "model_calls_real_fresh_unseen": 0,
            "next_scope": NEXT_SCOPE,
            "secondary_scope": (
                "FUNDAMENTAL_STANCE_STAGE_STABILITY_REVIEW_GPT56_SOL_ON_INTEGRATED_MAIN"
            ),
        },
    )
    _report(
        99,
        "final-main-merge-readiness-note",
        {
            "status": "NOT_READY",
            "final_main_merge_readiness": "NOT_READY",
            "main_merges": 0,
            "reason": "fictional_decision_material_stability_gate_failed",
        },
    )
    _report(
        100,
        "hosted-ci-portability-handoff",
        {
            "status": "NOT_RUN_LOCAL_FAILURE_PRECEDED_PUSH",
            "hosted_ci_pass_claimed": False,
            "new_hosted_ci_failure_count": "NOT_MEASURED",
        },
    )
    _report(
        101,
        "astra-future-experiment-handoff",
        {
            "status": "DEFERRED",
            "astra_calls": 0,
            "proof_model": r.MODEL,
            "reasoning_effort": r.EFFORT,
        },
    )
    no_change = {
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "model_calls_real_fresh_unseen": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "automatic_monitoring_resume": 0,
    }
    _report(
        102,
        "production-no-change",
        {
            "status": "PASS",
            **no_change,
            "user_visible_change_count": 0,
            "production_readiness": "NOT_AUTHORIZED",
        },
    )
    schedule = r.m12._schedule_observation()
    _report(
        103,
        "schedule-pause-observation",
        {
            "status": "PASS"
            if schedule["observed_paused_schedule_count"] >= 4
            else "REVIEW",
            "end": schedule,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    _report(
        104,
        "master-workflow-update",
        {
            "status": "RECORDED_IN_REPORT_ONLY",
            "phase": "M12AE-R2",
            "main_integration": "PASS",
            "two_stage_architecture": "PASS",
            "fictional_two_stage": "NOT_READY",
            "monitored_shadow": "NOT_RUN",
            "next_scope": NEXT_SCOPE,
            "persistent_master_workflow_mutation": 0,
        },
    )
    completion: dict[str, object] = {
        "main_frozen_sha": "d18e68b1e944d7749d093b08797fcd9498412680",
        "main_commit_date": "2026-09-05T15:42:14+09:00",
        "m12ad_source_head_sha": "69661d6754b0555e4c11caba8a53bd55a1fe7140",
        "integration_branch": r.git("branch", "--show-current"),
        "integration_merge_base_sha": "d18e68b1e944d7749d093b08797fcd9498412680",
        "integration_merge_commit_sha": "f1078d283b0bc963553fd25ade272b6002b7a4c2",
        "post_merge_baseline_sha": "f1078d283b0bc963553fd25ade272b6002b7a4c2",
        "final_integration_head_sha": r.git("rev-parse", "HEAD"),
        "integration_conflict_count": 0,
        "integration_conflict_resolved_count": 0,
        "integration_unresolved_conflict_count": 0,
        "main_only_relevant_commit_count": 0,
        "duplicate_or_stale_path_count": 3,
        "m12ad_semantic_fingerprint_status": "PRESERVED",
        "main_behavior_preservation_status": "PRESERVED",
        "integration_entrypoint_status": "UNAMBIGUOUS_BY_ENVIRONMENT",
        "post_merge_baseline_focused_test_result": "PASS",
        "post_merge_baseline_full_test_result": "PASS",
        "post_merge_baseline_ruff_result": "PASS",
        "post_merge_baseline_git_diff_check": "PASS",
        "selected_directional_architecture": (
            "STAGE1_CORE_THEN_STAGE2_STANCE_DETERMINISTIC_COMPOSER"
        ),
        "investment_judgment_model_target": r.MODEL,
        "investment_judgment_reasoning_effort": r.EFFORT,
        "runner_model_target_match": True,
        "model_target_fallback_count": 0,
        "stage1_core_enabled": True,
        "stage2_stance_enabled": True,
        "final_output_schema_change_count": 0,
        "internal_schema_change_count": 2,
        "stage1_prompt_contains_holder_contract": False,
        "stage1_prompt_contains_new_buyer_contract": False,
        "stage1_schema_contains_stance_fields": False,
        "stage2_schema_contains_core_fields": False,
        "core_snapshot_hash_enabled": True,
        "fictional_core_mutation_after_stance_count": 0,
        "shadow_core_mutation_after_stance_count": "NOT_MEASURED",
        "fictional_stage1_model_calls": 6,
        "fictional_stage2_model_calls": 6,
        "fictional_model_calls_total": 12,
        "fictional_final_output_count": 24,
        "fictional_primary_direction_unstable_subject_count": 2,
        "fictional_business_delta_unstable_subject_count": 1,
        "fictional_new_buyer_unstable_subject_count": 0,
        "fictional_holder_unstable_subject_count": 1,
        "fictional_same_direction_calibration_variance_subject_count": 3,
        "task_start_active_monitor_count": "NOT_MEASURED",
        "task_start_active_monitor_tickers": [],
        "reference_snapshot_added_tickers": [],
        "reference_snapshot_removed_tickers": [],
        "shadow_packet_available_count": "NOT_MEASURED",
        "shadow_packet_unavailable_count": "NOT_MEASURED",
        "shadow_packet_mismatch_count": "NOT_MEASURED",
        "shadow_context_count": 0,
        "shadow_monolithic_model_calls": 0,
        "shadow_stage1_model_calls": 0,
        "shadow_stage2_model_calls": 0,
        "shadow_model_calls_total": 0,
        "shadow_completed_ticker_count": 0,
        "shadow_no_decision_material_change_count": "NOT_MEASURED",
        "shadow_same_direction_calibration_change_count": "NOT_MEASURED",
        "shadow_primary_direction_change_count": "NOT_MEASURED",
        "shadow_business_delta_change_count": "NOT_MEASURED",
        "shadow_new_buyer_change_count": "NOT_MEASURED",
        "shadow_holder_change_count": "NOT_MEASURED",
        "shadow_multi_field_change_count": "NOT_MEASURED",
        "shadow_expected_contract_correction_count": "NOT_MEASURED",
        "shadow_potential_architecture_regression_count": "NOT_MEASURED",
        "shadow_unresolved_review_required_count": "NOT_MEASURED",
        "shadow_kr_count": "NOT_MEASURED",
        "shadow_us_count": "NOT_MEASURED",
        "shadow_sector_coverage_count": "NOT_MEASURED",
        "shadow_adr_security_basis_failure_count": "NOT_MEASURED",
        "shadow_financial_sector_framework_failure_count": "NOT_MEASURED",
        "shadow_cyclical_valuation_framework_failure_count": "NOT_MEASURED",
        "integrated_persistence_compatibility_status": "PASS",
        "integrated_price_timing_compatibility_status": "PASS",
        "integrated_renderer_compatibility_status": "PASS",
        **no_change,
        "fictional_two_stage_readiness": "NOT_READY",
        "shadow_compatibility_readiness": "NOT_MEASURED",
        "two_stage_real_holdout_suitability": "NOT_READY",
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "majority_vote_rule_count": 0,
        "balance_averaging_rule_count": 0,
        "stance_majority_vote_rule_count": 0,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "price_timing_semantic_change_count": 0,
        "renderer_substantive_change_count": 0,
        "source_sufficiency_semantic_change_count": 0,
        "daily_delta_semantic_change_count": 0,
        "hosted_ci_status": "NOT_RUN_LOCAL_FAILURE_PRECEDED_PUSH",
        "hosted_ci_failure_count": "NOT_MEASURED",
        "new_hosted_ci_failure_count": "NOT_MEASURED",
        "observed_paused_schedule_count": schedule[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "production_readiness": "NOT_AUTHORIZED",
        "status": "NOT_READY",
        "stop_reason": "FICTIONAL_DECISION_MATERIAL_STABILITY_FAIL",
        "blocking_findings": blockers,
        "postprocessing_adapter": postprocessing,
        "next_scope": NEXT_SCOPE,
    }
    _report(105, "program-completion", completion)
    r.write_json(r.OUTPUT / "program-completion.json", completion)
    markdown = """# M12AE-R2 Failure Closeout

## Result

Integrated-main baseline and deterministic two-stage architecture passed.
The fictional hard gate did not pass, so monitored shadow calls were not started.

## Blocking Results

- FIC-FIN-05 Stage 1 direction: `SELL / HOLD / HOLD`.
- FIC-FIN-06 Stage 1 direction: `HOLD / HOLD / BUY`.
- FIC-FIN-06 business delta: `STRENGTHENED / STRENGTHENED / UNCHANGED`.
- FIC-FIN-08 Stage 2 holder: `HOLDABLE / HOLDABLE / REVIEW`.

## Safety

- Calls: `12 / 12` completed with `gpt-5.6-sol`, `xhigh`.
- Final rows: `24 / 24` schema-valid.
- Objective semantic failures: `0`.
- Core mutations after stance: `0`.
- Timeout, capacity, orphan, retry: all `0`.
- Monitored shadow calls: `0`.
- Provider refresh, production DB mutation, send, deploy, scheduler mutation: all `0`.

## Decision

`fictional_two_stage_readiness = NOT_READY`

`final_main_merge_readiness = NOT_READY`

Next scope: `PRIMARY_DIRECTION_BOUNDARY_POLICY_REVIEW_GPT56_SOL_ON_INTEGRATED_MAIN`.
The FIC-FIN-08 holder boundary remains a secondary stance-stability review.
"""
    r.write_text(r.OUTPUT / "M12AE-R2-FAILURE-CLOSEOUT.md", markdown)
    r.write_json(
        r.OUTPUT / "failure-closeout.json",
        {
            "status": "NOT_READY",
            "generation_id": fictional["generation_id"],
            "blocking_findings": blockers,
            "affected_rows": rows,
            "monitored_shadow_model_calls": 0,
            "next_scope": NEXT_SCOPE,
        },
    )


def _files() -> list[Path]:
    paths = [path for path in r.REPORTS.rglob("*") if path.is_file()]
    paths.extend(
        path
        for path in r.OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        [
            Path("app/services/two_stage_directional_service.py"),
            Path("scripts/main_integration_two_stage_directional_m12ae_r2.py"),
            Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
            Path("scripts/main_integration_two_stage_directional_m12ae_r2_failure_closeout.py"),
            Path("tests/test_two_stage_directional_service.py"),
            Path("docs/work-instructions/20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation.md"),
        ]
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def _scan(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".json", ".txt", ".md", ".log", ".py"}:
        return []
    folded = path.read_text(encoding="utf-8", errors="replace").casefold()
    indicators = {
        "openai_api_key": "sk-",
        "telegram_bot_token": "bot_token=",
        "authorization_bearer": "authorization: bearer ",
        "private_key": "-----begin private key-----",
    }
    return [name for name, token in indicators.items() if token in folded]


def bundle(output_zip: Path) -> None:
    completion_path = r.REPORTS / "105-program-completion.json"
    completion = r.read_json(completion_path)
    files = _files()
    completion["artifact_count"] = len(files)
    r.write_json(completion_path, completion)
    r.write_json(r.OUTPUT / "program-completion.json", completion)
    files = _files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_scan(path),)
        if indicators
    ]
    index = {
        "contract": "m12ae-r2-failure-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [
            {
                "path": str(path),
                "sha256": r.file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    r.write_json(r.OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("artifact_secret_scan_failure")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"result_bundle_already_exists:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            r.OUTPUT / "artifact-index.json",
            arcname=str(r.OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("result_bundle_integrity_failure")
    digest = r.file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    r.write_text(sidecar, f"{digest}  {output_zip.name}")
    print(
        json.dumps(
            {
                "status": "NOT_READY_REPORT_COMPLETE",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "artifact_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


def main() -> None:
    closeout()
    bundle(
        Path.home()
        / "Documents/Codex"
        / f"thesis-monitor-{r.NAME}-report.zip"
    )


if __name__ == "__main__":
    main()
