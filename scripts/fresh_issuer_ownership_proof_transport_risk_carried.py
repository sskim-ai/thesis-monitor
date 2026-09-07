from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

from app.config import get_settings
from scripts import bounded_fictional_websocket_reconnect_diagnostic as diagnostic
from scripts import monitoring_pause_completion_fresh_issuer_ownership_proof as prior
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import synthetic_canary_fixture_repair_ownership_resume as guarded
from scripts import websocket_timeout_runtime_review_first_a_closeout as closeout
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "fresh-issuer-ownership-proof-transport-risk-carried-v1"
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260907-fresh-issuer-ownership-proof-with-unresolved-transport-risk-carried.md"
)
WORK_INSTRUCTION_SHA256 = "7c3c5cc7a214d40278ce6b052a9ada8094e67db03ab14cf82d90702cc605c752"
DIAGNOSTIC_ZIP_NAME = (
    "thesis-monitor-20260907-bounded-fictional-websocket-reconnect-"
    "observability-diagnostic-report.zip"
)
DIAGNOSTIC_ZIP_SHA256 = "1546b6830ab350f7d7cee68f8b2732806aa5e53b3a5cde8ed4648ee1223d49ec"
DIAGNOSTIC_MEMBER_COUNT = 84
DIAGNOSTIC_INDEXED_PAYLOAD_COUNT = 83
PREDECESSOR_ZIP_NAME = (
    "thesis-monitor-20260907-websocket-timeout-runtime-review-first-a-evidence-closeout-report.zip"
)
PREDECESSOR_ZIP_SHA256 = "1ddf30ac6b1420eed68f6e44e7f19ef455ca3e6619588b45be537e1d385612b3"
PREDECESSOR_MEMBER_COUNT = 329
PREDECESSOR_INDEXED_PAYLOAD_COUNT = 328
PRIOR_EXCLUSION_COUNT = 101
CURRENT_EXPOSED_COUNT = 16
EXCLUSION_COUNT = PRIOR_EXCLUSION_COUNT + CURRENT_EXPOSED_COUNT
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
EXPECTED_CONTEXTS_PER_RUN = 8
EXPECTED_TOTAL_CONTEXTS = 32
EXPECTED_STAGE_ROWS = 128
EXPECTED_RENDERED_ROWS = 64
QUALITY_GATE_ROLE = "ADVISORY_NOT_INCLUDED_IN_RUN_STATUS_OR_PROGRESS_SEQUENCE"
CARRIED_RUNTIME_RISK = "UNRESOLVED_RUNTIME_RELIABILITY_NOT_ESTABLISHED"
REPORT_DIRECTORY = "20260907-fresh-issuer-ownership-proof-transport-risk-carried"
COMPACT_REPORT_NAMES = (
    "01-input-provenance-pause",
    "02-selection-and-source-readiness",
    "03-source-lock-and-execution-precommit",
    "04-attempt-runtime-and-preservation",
    "05-per-run-hard-gates",
    "06-advisory-message-quality",
    "07-stability-and-generalization",
    "08-exposure-retirement-and-counters",
    "09-production-and-policy-no-change",
    "10-program-completion",
)
ARTIFACT_SECRET_PATTERNS = {
    **runner.SECRET_PATTERNS,
    "openai_key": re.compile(rb"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}"),
}

_BASE_ARCHITECTURE_HASHES = prior.architecture_hashes
_BASE_TRANSPORT_HASHES = prior.transport_topology_hashes
_BASE_INVOKE_MODEL_CONTEXT = runner.invoke_model_context


def read_json(path: Path) -> dict[str, Any]:
    return prior.read_json(path)


def write_json(path: Path, value: object) -> None:
    prior.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    prior.write_text(path, value)


def file_sha256(path: Path) -> str:
    return prior.file_sha256(path)


def canonical_sha256(value: object) -> str:
    return runner.canonical_sha256(value)


def scan_artifact_secrets(paths: Sequence[Path]) -> dict[str, object]:
    counts: Counter[str] = Counter()
    for path in paths:
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for name, pattern in ARTIFACT_SECRET_PATTERNS.items():
            counts[name] += len(pattern.findall(payload))
    total = sum(counts.values())
    return {
        "category_counts": {
            name: counts[name] for name in ARTIFACT_SECRET_PATTERNS
        },
        "secret_exposure_count": total,
        "secret_scan_status": "PASS" if total == 0 else "FAIL",
    }


def git_value(*args: str) -> str:
    return prior.git_value(*args)


def _configure_prior_module() -> None:
    prior.PROGRAM_CONTRACT = PROGRAM_CONTRACT
    prior.WORK_INSTRUCTION_PATH = WORK_INSTRUCTION_PATH
    prior.WORK_INSTRUCTION_SHA256 = WORK_INSTRUCTION_SHA256
    prior.REPORT_DIRECTORY = REPORT_DIRECTORY
    prior.PauseAwareWorkloadObserver = diagnostic.PausedScheduleProcessObserver
    prior.architecture_hashes = architecture_hashes
    prior.transport_topology_hashes = transport_topology_hashes
    prior._source_blocked = _source_blocked


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    return {
        **_BASE_ARCHITECTURE_HASHES(repo_root),
        "risk_carried_orchestrator": file_sha256(Path(__file__).resolve()),
    }


def transport_topology_hashes() -> dict[str, str]:
    return {
        **_BASE_TRANSPORT_HASHES(),
        "PausedScheduleProcessObserver": runner.source_sha256(
            diagnostic.PausedScheduleProcessObserver
        ),
        "SingleObservationWorkloadGuard": runner.source_sha256(
            diagnostic.SingleObservationWorkloadGuard
        ),
        "runtime_event_classifier": runner.source_sha256(closeout.classify_runtime_receipt),
        "risk_carried_adapter": runner.source_sha256(RiskCarriedTransportAdapter),
        "runtime_context_augmenter": runner.source_sha256(augment_runtime_context),
    }


def _verify_zip(
    path: Path,
    *,
    expected_name: str,
    expected_sha256: str,
    expected_members: int | None = None,
    expected_indexed: int | None = None,
) -> dict[str, object]:
    result = prior.verify_bundle(
        path,
        expected_name=expected_name,
        expected_sha256=expected_sha256,
    )
    checks = dict(result["checks"])
    if expected_members is not None:
        checks["member_count"] = result["member_count"] == expected_members
    if expected_indexed is not None:
        checks["indexed_payload_count"] = result["indexed_payload_count"] == expected_indexed
    result["checks"] = checks
    result["status"] = "PASS" if all(checks.values()) else "FAIL"
    if result["status"] != "PASS":
        raise ValueError(f"input_bundle_count_mismatch:{path.name}")
    return result


def _zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    return prior.zip_json(archive, member)


def _zip_jsonl(archive: zipfile.ZipFile, member: str) -> list[dict[str, Any]]:
    return prior.zip_jsonl(archive, member)


def _current_exposed_state(predecessor_zip: Path) -> dict[str, Any]:
    with zipfile.ZipFile(predecessor_zip) as archive:
        state = _zip_json(archive, "historical-input/experiment/program-state.json")
        exposure = _zip_json(
            archive,
            "reports/proofs/08-exposure-retirement-measurement-mapping.json",
        )
    cohort = [str(value) for value in state.get("ordered_cohort") or []]
    if len(cohort) != CURRENT_EXPOSED_COUNT or len(set(cohort)) != len(cohort):
        raise ValueError("predecessor_exposed_cohort_count_mismatch")
    if state.get("holdout_output_exposure_state") != "FULLY_EXPOSED":
        raise ValueError("predecessor_cohort_not_fully_exposed")
    if (
        exposure.get("derived_measured_scope_state", {}).get("future_unseen_holdout_reuse_allowed")
        != 0
    ):
        raise ValueError("predecessor_exposure_reuse_gate_mismatch")
    return state


def merge_exposure_registry(
    prior_101: Mapping[str, object],
    *,
    exposed_state: Mapping[str, object],
    references: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    prior_rows = [dict(row) for row in prior_101.get("rows") or [] if isinstance(row, Mapping)]
    if len(prior_rows) != PRIOR_EXCLUSION_COUNT:
        raise ValueError(f"prior_registry_count_mismatch:{len(prior_rows)}")
    rows_by_key = {
        str(row["canonical_issuer_key"]): row
        for row in prior_rows
        if row.get("canonical_issuer_key")
    }
    if len(rows_by_key) != len(prior_rows):
        raise ValueError("prior_registry_duplicate_or_missing_issuer_key")
    references_by_ticker = {str(row.get("display_symbol")): row for row in references}
    aliases_by_issuer: dict[str, set[str]] = {}
    for row in references:
        key = str(row.get("canonical_issuer_key") or "")
        ticker = str(row.get("display_symbol") or "")
        if key and ticker:
            aliases_by_issuer.setdefault(key, set()).add(ticker)
    appended = []
    generation_id = str(exposed_state.get("program_generation_id") or "")
    for ticker in exposed_state.get("ordered_cohort") or []:
        reference = references_by_ticker.get(str(ticker))
        if reference is None:
            raise ValueError(f"exposed_ticker_missing_reference:{ticker}")
        key = str(reference.get("canonical_issuer_key") or "")
        if not key or key in rows_by_key:
            raise ValueError(f"exposed_issuer_duplicate_or_missing:{ticker}:{key}")
        row = {
            "actual_output_exposure": True,
            "actual_real_model_spawn": True,
            "canonical_issuer_key": key,
            "exclusion_reasons": ["INCOMPLETE_A_B_C_AFTER_FULL_COHORT_EXPOSURE"],
            "lineage": [
                {
                    "experiment_class": (
                        "monitoring-pause-completion-fresh-issuer-ownership-proof"
                    ),
                    "exposure_class": "REAL_MODEL_OUTPUT",
                    "generation_id": generation_id,
                    "ticker": ticker,
                    "usable_output_exists": True,
                }
            ],
            "market": reference.get("market"),
            "security_aliases": sorted(aliases_by_issuer.get(key) or {str(ticker)}),
            "whole_cohort_retired": True,
            "retirement_reasons": ["INCOMPLETE_A_B_C_AFTER_FULL_COHORT_EXPOSURE"],
        }
        rows_by_key[key] = row
        appended.append(row)
    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    if len(appended) != CURRENT_EXPOSED_COUNT or len(rows) != EXCLUSION_COUNT:
        raise ValueError(f"reconciled_registry_count_mismatch:{len(appended)}:{len(rows)}")
    return {
        "contract": "canonical-exposure-registry-risk-carried-v1",
        "prior_registry_count": PRIOR_EXCLUSION_COUNT,
        "appended_exposed_issuer_count": len(appended),
        "reconciled_registry_count": len(rows),
        "exclusion_shrink_count": 0,
        "latest_exposed_generation_id": generation_id,
        "latest_cohort_issuer_exposure": "16/16",
        "latest_cohort_core_stage_coverage": "16/16",
        "latest_cohort_timing_stage_coverage": "16/16",
        "latest_complete_run_coverage": ["FIRST", "A"],
        "latest_failed_run": "B_CORE_01",
        "latest_retirement_reason": ("INCOMPLETE_A_B_C_AFTER_FULL_COHORT_EXPOSURE"),
        "rows": rows,
        "all_excluded_issuer_keys": sorted(rows_by_key),
        "status": "PASS",
    }


def _provenance(repo_root: Path) -> dict[str, object]:
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH)
    return {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": git_value("rev-parse", f"{instruction_commit}^"),
        "work_instruction_commit": instruction_commit,
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "work_instruction_sha256": file_sha256(repo_root / WORK_INSTRUCTION_PATH),
        "status": "PASS",
    }


def _candidate_manifest(
    market: str, target: int, rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    result = prior._candidate_manifest(market, target, rows)
    result["contract"] = f"risk-carried-fresh-{market}-candidate-manifest-v1"
    result["exclusion_registry_count"] = EXCLUSION_COUNT
    return result


def freeze_selection(args: argparse.Namespace) -> None:
    _configure_prior_module()
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_selection_freeze")

    diagnostic_integrity = _verify_zip(
        args.diagnostic_zip,
        expected_name=DIAGNOSTIC_ZIP_NAME,
        expected_sha256=DIAGNOSTIC_ZIP_SHA256,
        expected_members=DIAGNOSTIC_MEMBER_COUNT,
        expected_indexed=DIAGNOSTIC_INDEXED_PAYLOAD_COUNT,
    )
    predecessor_integrity = _verify_zip(
        args.predecessor_zip,
        expected_name=PREDECESSOR_ZIP_NAME,
        expected_sha256=PREDECESSOR_ZIP_SHA256,
        expected_members=PREDECESSOR_MEMBER_COUNT,
        expected_indexed=PREDECESSOR_INDEXED_PAYLOAD_COUNT,
    )
    historical_integrity = _verify_zip(
        args.historical_zip,
        expected_name=prior.HISTORICAL_ZIP_NAME,
        expected_sha256=prior.HISTORICAL_ZIP_SHA256,
    )
    expansion_integrity = _verify_zip(
        args.expansion_zip,
        expected_name=prior.EXPANSION_ZIP_NAME,
        expected_sha256=prior.EXPANSION_ZIP_SHA256,
    )
    with zipfile.ZipFile(args.expansion_zip) as archive:
        base_registry = _zip_json(archive, prior.PRIOR_REGISTRY_MEMBER)
        us_references = _zip_jsonl(archive, prior.REFERENCE_MEMBERS["us"])
        kr_references = _zip_jsonl(archive, prior.REFERENCE_MEMBERS["kr"])
        handoff = _zip_json(archive, prior.HANDOFF_MEMBER)
    with zipfile.ZipFile(args.historical_zip) as archive:
        historical_overlay = _zip_json(archive, prior.OVERLAY_MEMBER)
    prior_101 = prior.merge_exposure_registry(base_registry, historical_overlay)
    exposed_state = _current_exposed_state(args.predecessor_zip)
    registry = merge_exposure_registry(
        prior_101,
        exposed_state=exposed_state,
        references=[*us_references, *kr_references],
    )
    excluded = {str(value) for value in registry["all_excluded_issuer_keys"]}
    us_candidates = prior.filter_candidate_rows(
        handoff.get("deterministic_us_candidate_order") or (),
        us_references,
        excluded,
        market="us",
    )
    kr_candidates = prior.filter_candidate_rows(
        handoff.get("deterministic_kr_candidate_order") or (),
        kr_references,
        excluded,
        market="kr",
        limit=prior.KR_CANDIDATE_LIMIT,
    )
    if len(us_candidates) < TARGET_US or len(kr_candidates) < TARGET_KR:
        raise ValueError("candidate_universe_below_required_market_mix")

    pause = closeout.observe_pause_state()
    process_observation = diagnostic.PausedScheduleProcessObserver().observe()
    if pause.get("status") != "VERIFIED_PAUSED_COMPLETE":
        raise ValueError(f"monitoring_pause_not_verified:{pause.get('status')}")
    if process_observation.get("active_natural_job_count") or process_observation.get(
        "running_model_process_count"
    ):
        raise ValueError("unexpected_active_workload_before_selection_freeze")

    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    write_json(args.output_root / "selection-inputs" / "prior-101-registry.json", prior_101)
    write_json(args.output_root / "selection-inputs" / "latest-exposed-state.json", exposed_state)
    write_json(args.output_root / "selection-inputs" / "merged-registry.json", registry)
    write_json(args.output_root / "selection-inputs" / "expansion-handoff.json", handoff)
    prior.write_jsonl(args.output_root / "selection-inputs" / "us-candidates.jsonl", us_candidates)
    prior.write_jsonl(args.output_root / "selection-inputs" / "kr-candidates.jsonl", kr_candidates)
    candidate_identities = {
        "contract": "risk-carried-fresh-candidate-identities-v1",
        "us": us_candidates,
        "kr": kr_candidates,
        "status": "FROZEN",
    }
    write_json(args.output_root / "candidate-identities.json", candidate_identities)
    policy = {
        "contract": "fresh-issuer-risk-carried-selection-policy-v1",
        "status": "FROZEN_PRE_SOURCE_EVALUATION",
        "selection_salt": prior.SELECTION_SALT,
        "verified_reference_snapshot": handoff.get("verified_reference_snapshot"),
        "reference_snapshot_sha256": canonical_sha256({"us": us_references, "kr": kr_references}),
        "candidate_identities_sha256": canonical_sha256(candidate_identities),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "exclusion_registry_count": EXCLUSION_COUNT,
        "exclusion_shrink_count": 0,
        "market_targets": {"us": TARGET_US, "kr": TARGET_KR},
        "market_policies": {
            "us": {
                "candidate_order": [row["display_symbol"] for row in us_candidates],
                "bounded_evaluation_limit": len(us_candidates),
            },
            "kr": {
                "candidate_order": [row["display_symbol"] for row in kr_candidates],
                "bounded_evaluation_limit": len(kr_candidates),
            },
        },
        "selection_rule": (
            "reuse the verified supported-reference order; remove all canonical issuer "
            "keys in the reconciled 117-issuer exposure registry; accept the first "
            "source-eligible unique US4 and KR12"
        ),
        "objective_pre_model_replacement_only": True,
        "replacement_after_model_start": 0,
        "maximum_fresh_real_cohorts": 1,
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "context_size": runner.CONTEXT_SIZE,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "runs": list(runner.RUNS),
        "stages": list(runner.STAGES),
        "expected_invocations_per_run": EXPECTED_CONTEXTS_PER_RUN,
        "expected_total_invocations": EXPECTED_TOTAL_CONTEXTS,
        "retry_count": 0,
        "source_evaluation_performed": 0,
        "model_calls": 0,
    }
    provenance = _provenance(repo_root)
    runner.write_proof(args.report_dir, 1, provenance)
    runner.write_proof(
        args.report_dir,
        2,
        {
            "contract": "risk-carried-task-input-integrity-v1",
            "latest_diagnostic": diagnostic_integrity,
            "historical_predecessor": predecessor_integrity,
            "registry_overlay_source": historical_integrity,
            "supported_reference_source": expansion_integrity,
            "latest_diagnostic_next_scope": (
                "SEPARATELY_AUTHORIZED_REAL_PROOF_WITH_TRANSPORT_RISK_CARRIED"
            ),
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
            "status": "PASS",
        },
    )
    runner.write_proof(args.report_dir, 3, registry)
    runner.write_proof(
        args.report_dir,
        4,
        {
            "contract": "fresh-holdout-exclusion-continuity-v1",
            "prior_count": PRIOR_EXCLUSION_COUNT,
            "appended_count": CURRENT_EXPOSED_COUNT,
            "reconciled_count": EXCLUSION_COUNT,
            "excluded_issuer_keys": registry["all_excluded_issuer_keys"],
            "exclusion_shrink_count": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(args.report_dir, 5, policy)
    runner.write_proof(args.report_dir, 6, _candidate_manifest("us", TARGET_US, us_candidates))
    runner.write_proof(args.report_dir, 9, _candidate_manifest("kr", TARGET_KR, kr_candidates))
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "SELECTION_FROZEN",
        "branch": provenance["branch"],
        "base_sha": provenance["base_sha"],
        "work_instruction_commit": provenance["work_instruction_commit"],
        "selection_freeze_commit": "PENDING_COMMIT",
        "selection_policy_sha256": canonical_sha256(policy),
        "candidate_identities_sha256": canonical_sha256(candidate_identities),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "exclusion_registry_count": EXCLUSION_COUNT,
        "ordered_cohort": [],
        "model_invocation_count": 0,
        "production_scheduler_mutation": 0,
        "auto_resume_executed": 0,
        "production_send": 0,
        "initial_pause_observation": pause,
        "initial_process_observation": process_observation,
        "carried_runtime_risk": CARRIED_RUNTIME_RISK,
    }
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir)
    write_text(
        args.report_dir / "README.md",
        "# Fresh Issuer Ownership Proof with Transport Risk Carried\n\n"
        "This directory freezes the complete 117-issuer exclusion registry and the "
        "deterministic US/KR candidate order before source outcomes or model outputs.\n",
    )
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def _source_blocked(
    args: argparse.Namespace,
    *,
    state: dict[str, object],
    us_audit: Mapping[str, object],
    kr_audit: Mapping[str, object],
) -> None:
    reason = f"US={us_audit['source_target_status']};KR={kr_audit['source_target_status']}"
    configuration = _source_configuration_audit()
    configuration_blocked = configuration["status"] != "PASS"
    if configuration_blocked:
        reason = "REQUIRED_SOURCE_CONFIGURATION_UNAVAILABLE"
    readiness = (
        "NOT_READY_PREPARATION_CONFIGURATION_BLOCKED"
        if configuration_blocked
        else "NOT_READY_SOURCE_COVERAGE_BLOCKED"
    )
    next_scope = (
        "BOUNDED_EXISTING_SECRET_ENV_BINDING_REPAIR"
        if configuration_blocked
        else "BOUNDED_SOURCE_COVERAGE_REVIEW"
    )
    runner.write_proof(
        args.report_dir,
        15,
        {
            "contract": "fresh-holdout-selection-result-v1",
            "ordered_cohort": [],
            "status": "NOT_RUN_SOURCE_COVERAGE_BLOCKED",
        },
    )
    for run in runner.RUNS:
        runner.write_not_run(args, run, reason)
    _write_pre_model_terminal_proofs(
        args,
        state=state,
        reason=reason,
        configuration=configuration,
    )
    completion = {
        "contract": PROGRAM_CONTRACT,
        "proof_status": (
            "STOPPED_PRE_MODEL_PREPARATION_CONFIGURATION_FAILURE"
            if configuration_blocked
            else "STOPPED_PRE_MODEL_SOURCE_FAILURE"
        ),
        "us_source_target_status": us_audit["source_target_status"],
        "kr_source_target_status": kr_audit["source_target_status"],
        "run_results": {run: "NOT_RUN" for run in runner.RUNS},
        "real_model_invocation_count": 0,
        "formal_generalization": "NOT_MEASURED",
        "readiness": readiness,
        "stop_reason": reason,
        "next_scope": next_scope,
        "source_configuration": configuration,
        "status": "STOPPED",
    }
    runner.write_proof(args.report_dir, 60, completion)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "source_gate_only": True,
            "stop_reason": reason,
            "run_results": completion["run_results"],
            "readiness": completion["readiness"],
        }
    )
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir)


def _source_configuration_audit() -> dict[str, object]:
    settings = get_settings()
    required = {
        "SEC_USER_AGENT": bool(settings.sec_user_agent),
        "OPENDART_API_KEY": bool(settings.opendart_api_key),
    }
    missing = sorted(key for key, configured in required.items() if not configured)
    return {
        "contract": "risk-carried-source-configuration-audit-v1",
        "working_directory_env_file_present": (Path.cwd() / ".env").is_file(),
        "canonical_env_override_configured": bool(
            os.environ.get("THESIS_MONITOR_ENV_FILE")
        ),
        "required_setting_presence": required,
        "missing_required_settings": missing,
        "secret_values_recorded": 0,
        "diagnosis": (
            "EFFECTIVE_SOURCE_CONFIGURATION_AVAILABLE"
            if not missing
            else "EXECUTOR_ENV_BINDING_MISSING_REQUIRED_SOURCE_SETTINGS"
        ),
        "status": "PASS" if not missing else "FAIL",
    }


def _write_pre_model_terminal_proofs(
    args: argparse.Namespace,
    *,
    state: Mapping[str, object],
    reason: str,
    configuration: Mapping[str, object],
) -> None:
    configuration_blocked = configuration.get("status") != "PASS"
    readiness = (
        "NOT_READY_PREPARATION_CONFIGURATION_BLOCKED"
        if configuration_blocked
        else "NOT_READY_SOURCE_COVERAGE_BLOCKED"
    )
    next_scope = (
        "BOUNDED_EXISTING_SECRET_ENV_BINDING_REPAIR"
        if configuration_blocked
        else "BOUNDED_SOURCE_COVERAGE_REVIEW"
    )
    execution = {
        "contract": "risk-carried-execution-reconciliation-v1",
        "planned_contexts": EXPECTED_TOTAL_CONTEXTS,
        "attempted_contexts": 0,
        "terminal_contexts": 0,
        "successful_contexts": 0,
        "failed_contexts": 0,
        "not_run_contexts": EXPECTED_TOTAL_CONTEXTS,
        "per_run_stage_attempts": {},
        "per_run_stage_successes": {},
        "raw_output_document_count": 0,
        "raw_stage_rows": 0,
        "accepted_stage_rows": 0,
        "semantic_checked_rows": 0,
        "unique_issuer_output_count": 0,
        "unique_issuer_outputs": [],
        "composed_rows": 0,
        "rendered_rows": 0,
        "context_preservation_failures": 0,
        "wrapper_explicit_retry_count": 0,
        "observed_cli_retry_signal_count": 0,
        "observed_websocket_disconnect_signal_count": 0,
        "upstream_request_attempt_count": "NOT_APPLICABLE_NO_MODEL_SPAWN",
        "request_accepted_observability": "NOT_APPLICABLE_NO_MODEL_SPAWN",
        "disconnect_then_success_count": 0,
        "disconnect_then_timeout_count": 0,
        "explicit_capacity_count": 0,
        "explicit_context_failure_count": 0,
        "watchdog_timeout_count": 0,
        "orphan_count": 0,
        "distinct_session_count": 0,
        "distinct_namespace_count": 0,
        "status": "NOT_RUN_PRE_MODEL",
    }
    write_json(args.output_root / "execution-reconciliation.json", execution)
    write_json(args.output_root / "source-configuration-audit.json", configuration)
    for number in range(16, 26):
        runner.write_proof(
            args.report_dir,
            number,
            {
                "contract": f"{runner.PROOF_NAMES[number - 1]}-v1",
                "reason": reason,
                "model_subprocess_count": 0,
                "status": "NOT_RUN_PRE_MODEL",
            },
        )
    coexistence = (
        read_json(args.output_root / "live-workload-coexistence-audit.json")
        if (args.output_root / "live-workload-coexistence-audit.json").is_file()
        else {
            "contract": "risk-carried-live-workload-coexistence-audit-v1",
            "reason": "OBSERVATION_ARTIFACT_UNAVAILABLE",
            "status": "NOT_MEASURED",
        }
    )
    runner.write_proof(args.report_dir, 26, coexistence)
    runner.write_proof(
        args.report_dir,
        14,
        {
            "contract": "fresh-source-coverage-decision-v1",
            "real_model_execution_allowed": 0,
            "root_cause": configuration.get("diagnosis"),
            "missing_required_settings": configuration.get(
                "missing_required_settings", []
            ),
            "source_retry_executed": 0,
            "new_paid_dependency": 0,
            "new_source_route": 0,
            "readiness": readiness,
            "next_scope": next_scope,
            "status": "FAIL_CLOSED",
        },
    )
    runner.write_proof(
        args.report_dir,
        51,
        {
            "contract": "holdout-exposure-retirement-state-v1",
            "holdout_output_exposure_state": "UNEXPOSED",
            "holdout_semantic_revelation_state": "NOT_MEASURED",
            "holdout_retirement_state": "NOT_APPLICABLE_NO_LOCKED_COHORT",
            "future_unseen_holdout_reuse_allowed": (
                "SEPARATE_EXPLICIT_DECISION_REQUIRED"
            ),
            "same_cohort_architecture_tuning_rerun_allowed": 0,
            "exposed_subjects": [],
            "status": "STOPPED_PRE_MODEL",
        },
    )
    for number, contract in (
        (52, "directional-core-stability-audit-v1"),
        (53, "price-timing-stability-audit-v1"),
    ):
        runner.write_proof(
            args.report_dir,
            number,
            {
                "contract": contract,
                "counts": {
                    "STABLE": 0,
                    "BOUNDARY_UNCERTAINTY": 0,
                    "UNSTABLE": 0,
                },
                "reason": reason,
                "status": "NOT_MEASURED",
            },
        )
    runner.write_proof(
        args.report_dir,
        54,
        {
            "contract": "ownership-generalization-proof-v1",
            "final_direction_owner": "NOT_MEASURED",
            "ownership_generalization_verdict": "NOT_ESTABLISHED",
            "reason": reason,
            "status": "NOT_MEASURED",
        },
    )
    runner.write_proof(
        args.report_dir,
        55,
        {
            "contract": "renderer-ownership-proof-v1",
            "primary_user_action_wording_owner": "NOT_MEASURED",
            "ai_imperative_primary_action": "NOT_MEASURED",
            "renderer_ownership_violations": "NOT_MEASURED",
            "reason": reason,
            "status": "NOT_MEASURED",
        },
    )
    runner.write_proof(
        args.report_dir,
        56,
        {
            "contract": "hard-safety-regression-v1",
            "known_hard_safety_regression": "NOT_MEASURED",
            "reason": reason,
            "status": "NOT_MEASURED",
        },
    )
    _write_no_change_proofs(args)
    runner.write_proof(
        args.report_dir,
        59,
        {
            "contract": "monitoring-bootstrap-next-handoff-v1",
            "readiness": readiness,
            "next_scope": next_scope,
            "monitoring_registration_calls": 0,
            "bootstrap_production_mutation": 0,
            "status": "NOT_READY",
        },
    )
    write_json(args.output_root / "run-gate-summary.json", _run_gate_summary(args))
    write_json(
        args.output_root / "advisory-message-quality-summary.json",
        _quality_summary(args),
    )
    root_cause_text = (
        "The source preparation process did not receive the existing SEC/OpenDART "
        "configuration. The worktree had no local `.env`, and "
        "`THESIS_MONITOR_ENV_FILE` was not bound. US official-profile requests "
        "therefore failed and KR official profiles were unavailable."
        if configuration_blocked
        else "The bounded source evaluation completed without the required US4/KR12."
    )
    write_text(
        args.report_dir / "preparation-environment-root-cause.md",
        "# Preparation Root Cause\n\n"
        f"{root_cause_text} No secret value is recorded. The frozen candidate budget "
        "is not retried in this task, and no model subprocess was spawned.\n",
    )
    write_json(
        args.report_dir / "preparation-environment-root-cause.json",
        {
            **configuration,
            "model_subprocess_count": 0,
            "source_retry_executed": 0,
            "frozen_candidate_budget_reopened": 0,
            "selection_policy_sha256": state.get("selection_policy_sha256"),
            "status": "CONFIRMED_PRE_MODEL_BLOCKER",
            "readiness": readiness,
            "next_scope": next_scope,
        },
    )


def _acceptance_protocol() -> dict[str, object]:
    return {
        "run_gate_documents_sha256": runner.source_sha256(runner.run_gate_documents),
        "core_partial_audit_sha256": runner.source_sha256(runner.core_partial_audit),
        "timing_partial_audit_sha256": runner.source_sha256(runner.timing_partial_audit),
        "core_stability_sha256": runner.source_sha256(prior.frozen._core_stability),
        "timing_stability_sha256": runner.source_sha256(prior.frozen._timing_stability),
        "message_quality_sha256": runner.source_sha256(runner.structured_autonomy_message_quality),
        "quality_gate_role": QUALITY_GATE_ROLE,
        "status_mapping": {
            "hard_context_or_run_failure": "STOP_REMAINING_CALLS",
            "advisory_message_quality_failure": "REPORT_WITHOUT_PROGRESS_BLOCK",
            "four_valid_runs_required_for_stability": True,
        },
    }


def prepare(args: argparse.Namespace) -> None:
    _configure_prior_module()
    cli = diagnostic.cli_identity()
    if cli["status"] != "PASS":
        raise ValueError("signed_in_codex_cli_identity_mismatch")
    prior.prepare(args)
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") == "EVIDENCE_COMPLETE":
        return
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("unexpected_state_after_source_preparation")

    source_lock_path = args.output_root / "source-lock.json"
    source_lock = read_json(source_lock_path)
    source_lock.pop("source_lock_sha256", None)
    source_lock.update(
        {
            "contract": "fresh-issuer-risk-carried-executable-source-lock-v1",
            "exclusion_registry_count": EXCLUSION_COUNT,
            "frozen_evaluation_cutoff": state["as_of"],
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
        }
    )
    source_lock_hash = canonical_sha256(source_lock)
    write_json(
        source_lock_path,
        {**source_lock, "source_lock_sha256": source_lock_hash},
    )

    policy = read_json(runner.proof_path(args.report_dir, 5))
    pause = closeout.observe_pause_state()
    process_observation = diagnostic.PausedScheduleProcessObserver().observe()
    if pause.get("status") != "VERIFIED_PAUSED_COMPLETE":
        raise ValueError("monitoring_pause_not_verified_after_source_preparation")
    if process_observation.get("active_natural_job_count") or process_observation.get(
        "running_model_process_count"
    ):
        raise ValueError("unexpected_active_workload_after_source_preparation")
    precommit_path = args.output_root / "new-holdout-precommit.json"
    precommit = read_json(precommit_path)
    precommit.update(
        {
            "contract": "fresh-issuer-risk-carried-execution-precommit-v1",
            "source_lock_sha256": source_lock_hash,
            "exclusion_registry_count": EXCLUSION_COUNT,
            "exclusion_registry_sha256": state["exclusion_registry_sha256"],
            "reference_snapshot_sha256": policy["reference_snapshot_sha256"],
            "selection_policy_sha256": state["selection_policy_sha256"],
            "reserve_order_sha256": canonical_sha256(policy["market_policies"]),
            "frozen_evaluation_cutoff": state["as_of"],
            "signed_in_cli_identity": cli,
            "namespace_policy": (
                "one isolated signed-in Codex CLI subprocess, temporary working "
                "directory and runtime-state namespace per model context"
            ),
            "run_order": list(runner.RUNS),
            "stage_and_context_order": [
                "DIRECTIONAL_CORE_01",
                "DIRECTIONAL_CORE_02",
                "DIRECTIONAL_CORE_03",
                "DIRECTIONAL_CORE_04",
                "PRICE_TIMING_01",
                "PRICE_TIMING_02",
                "PRICE_TIMING_03",
                "PRICE_TIMING_04",
            ],
            "maximum_real_model_subprocess_attempts": EXPECTED_TOTAL_CONTEXTS,
            "new_fictional_model_calls": 0,
            "capacity_or_health_model_smoke_calls": 0,
            "wrapper_explicit_retries": 0,
            "failed_call_replacements": 0,
            "replacement_cohort_attempts": 0,
            "maximum_fresh_real_cohorts": 1,
            "stop_matrix": {
                "terminal_transport_failure": "STOP_ALL_REMAINING",
                "schema_identity_order_alias_failure": "STOP_ALL_REMAINING",
                "hard_semantic_or_safety_failure": "STOP_ALL_REMAINING",
                "preservation_failure": "STOP_ALL_REMAINING",
                "advisory_message_quality_failure": "REPORT_AND_CONTINUE",
            },
            "acceptance_protocol": _acceptance_protocol(),
            "acceptance_protocol_sha256": canonical_sha256(_acceptance_protocol()),
            "pause_observation": pause,
            "process_observation": process_observation,
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
            "runtime_reliability_status": "NOT_ESTABLISHED",
            "reconnect_path_exercised": "NOT_OBSERVED",
            "status": "FROZEN",
        }
    )
    precommit_hash = canonical_sha256(precommit)
    write_json(precommit_path, precommit)

    state.update(
        {
            "source_lock_sha256": source_lock_hash,
            "precommit_sha256": precommit_hash,
            "exclusion_registry_count": EXCLUSION_COUNT,
            "signed_in_cli_identity": cli,
            "acceptance_protocol_sha256": precommit["acceptance_protocol_sha256"],
            "quality_gate_role": QUALITY_GATE_ROLE,
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
            "production_scheduler_mutation": 0,
            "auto_resume_executed": 0,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    runner.write_proof(
        args.report_dir,
        19,
        {**source_lock, "source_lock_sha256": source_lock_hash},
    )
    runner.write_proof(args.report_dir, 20, precommit)
    transport = read_json(runner.proof_path(args.report_dir, 24))
    transport.update(
        {
            "hashes": transport_topology_hashes(),
            "signed_in_cli_identity": cli,
            "wrapper_explicit_retry_count": 0,
            "canonical_transport_mutation": 0,
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
        }
    )
    runner.write_proof(args.report_dir, 24, transport)
    unseen = read_json(runner.proof_path(args.report_dir, 25))
    unseen["exclusion_registry_count"] = EXCLUSION_COUNT
    runner.write_proof(args.report_dir, 25, unseen)
    runner.write_proof(
        args.report_dir,
        26,
        {
            "contract": "risk-carried-live-workload-coexistence-audit-v1",
            "pause": pause,
            "process_observation": process_observation,
            "scheduler_mutation": 0,
            "status": "PASS",
        },
    )
    runner.write_reports(args.report_dir)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def seal(args: argparse.Namespace) -> None:
    _configure_prior_module()
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_for_execution_seal")
    prior.verify_frozen(args, state)
    cli = diagnostic.cli_identity()
    if cli != state.get("signed_in_cli_identity") or cli.get("status") != "PASS":
        raise ValueError("signed_in_cli_identity_drift_before_seal")
    pause = closeout.observe_pause_state()
    process_observation = diagnostic.PausedScheduleProcessObserver().observe()
    if pause.get("status") != "VERIFIED_PAUSED_COMPLETE":
        raise ValueError("monitoring_pause_not_verified_at_execution_seal")
    if process_observation.get("active_natural_job_count") or process_observation.get(
        "running_model_process_count"
    ):
        raise ValueError("unexpected_active_workload_at_execution_seal")
    seal_document = {
        "contract": "fresh-issuer-risk-carried-execution-seal-v1",
        "final_precommit_commit": git_value("rev-parse", "HEAD"),
        "final_precommit_tree": git_value("rev-parse", "HEAD^{tree}"),
        "source_generation_id": state["source_generation_id"],
        "runtime_generation_id": state["program_generation_id"],
        "source_lock_sha256": state["source_lock_sha256"],
        "precommit_sha256": state["precommit_sha256"],
        "acceptance_protocol_sha256": state["acceptance_protocol_sha256"],
        "signed_in_cli_identity": cli,
        "pause_observation": pause,
        "process_observation": process_observation,
        "sealed_at": datetime.now(UTC).isoformat(),
        "carried_runtime_risk": CARRIED_RUNTIME_RISK,
        "status": "FROZEN",
    }
    write_json(args.output_root / "execution-freeze-seal.json", seal_document)
    state.update(
        {
            "state": "SEALED_FROZEN",
            "final_precommit_commit": seal_document["final_precommit_commit"],
            "final_precommit_tree": seal_document["final_precommit_tree"],
            "execution_seal_sha256": canonical_sha256(seal_document),
            "execution_sealed_at": seal_document["sealed_at"],
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


class RiskCarriedTransportAdapter(guarded.GuardedTransportAdapter):
    def invoke(self, **kwargs: object) -> dict[str, object]:
        stage = str(kwargs["stage"])
        batch_id = str(kwargs["batch_id"])
        subject_count = int(kwargs["subject_count"])
        invocation_id = str(kwargs["invocation_id"])
        context_dir = Path(str(kwargs["output"])).parent
        try:
            observation = self.preflight(
                stage=stage,
                batch_id=batch_id,
                subject_count=subject_count,
            )
            write_json(context_dir / "workload-observation.json", observation)
            if observation.get("status") != "PASS":
                raise guarded.LiveWorkloadObservationUnavailable(
                    "risk_carried_workload_preflight_not_clear"
                )
        except Exception as exc:
            if not (context_dir / "workload-observation.json").is_file():
                write_json(
                    context_dir / "workload-observation.json",
                    {
                        "contract": "prespawn-live-workload-guard-preflight-v1",
                        "status": "FAIL",
                        "safe_to_spawn": 0,
                        "root_exception": f"{type(exc).__name__}:{exc}",
                    },
                )
            lifecycle = {
                "failure_stage": "PRE_SPAWN_WORKLOAD_GUARD",
                "spawn_started": 0,
                "transport_receipt_expected": 0,
                "transport_receipt_created": 0,
                "root_exception_masked": 0,
                "root_exception": f"{type(exc).__name__}:{exc}",
                "invocation_id": invocation_id,
            }
            setattr(exc, "transport_lifecycle", lifecycle)
            raise
        return super().invoke(**kwargs)


def _runtime_artifact_manifest(context_dir: Path) -> dict[str, object]:
    required = (
        "prompt.txt",
        "schema.json",
        "identity-binding-lock.json",
        "actual-request-identity-preflight.json",
        "workload-observation.json",
    )
    rows = []
    failures = []
    for name in required:
        path = context_dir / name
        exists = path.is_file()
        rows.append(
            {
                "path": name,
                "exists": exists,
                "sha256": file_sha256(path) if exists else None,
                "byte_size": path.stat().st_size if exists else 0,
            }
        )
        if not exists:
            failures.append(f"missing:{name}")
    return {
        "contract": "risk-carried-context-preservation-v1",
        "rows": rows,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def _prior_session_values(output_root: Path, current: Path) -> tuple[set[str], set[str]]:
    sessions: set[str] = set()
    namespaces: set[str] = set()
    for path in sorted((output_root / "model-contexts").rglob("lifecycle-summary.json")):
        if path.parent == current:
            continue
        value = read_json(path)
        if value.get("session_id"):
            sessions.add(str(value["session_id"]))
        if value.get("runtime_state_namespace_hash"):
            namespaces.add(str(value["runtime_state_namespace_hash"]))
    return sessions, namespaces


def augment_runtime_context(
    *,
    args: argparse.Namespace,
    run: str,
    stage: str,
    batch_number: int,
    context_dir: Path,
    invocation_id: str,
    primary_error: BaseException | None,
) -> dict[str, object]:
    stderr_raw = context_dir / "stderr.raw.log"
    stderr_bytes = stderr_raw.read_bytes() if stderr_raw.is_file() else b""
    stderr_safe = diagnostic._redact_secrets(stderr_bytes)
    (context_dir / "stderr.safe.log").write_bytes(stderr_safe)
    stderr_text = stderr_safe.decode("utf-8", errors="replace")
    runtime_events = closeout.extract_runtime_events(stderr_text)
    sessions = closeout.SESSION_ID_RE.findall(stderr_text)
    session_id = sessions[0] if sessions else None
    receipt_path = context_dir / "transport_receipt.json"
    receipt = read_json(receipt_path) if receipt_path.is_file() else {}
    namespace = (
        receipt.get("transport_metadata", {}).get("runtime_state_namespace_hash")
        if isinstance(receipt.get("transport_metadata"), Mapping)
        else None
    )
    prior_sessions, prior_namespaces = _prior_session_values(args.output_root, context_dir)
    session_unique = bool(session_id) and session_id not in prior_sessions
    namespace_unique = bool(namespace) and str(namespace) not in prior_namespaces
    output_path = context_dir / "output.raw.json"
    output_json_valid = False
    if output_path.is_file():
        try:
            read_json(output_path)
            output_json_valid = True
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    preservation = _runtime_artifact_manifest(context_dir)
    classification = diagnostic.classify_attempt(
        receipt,
        stderr_text,
        schema_valid=output_json_valid,
        identity_valid=bool(receipt_path.is_file()),
        preservation_valid=preservation["status"] == "PASS",
        session_identity_valid=session_unique and namespace_unique,
    )
    runtime_document = {
        "contract": "runtime-only-event-extraction-v1",
        "source": "stderr.safe.log",
        "event_count": len(runtime_events),
        "events": [
            {
                "timestamp": event.timestamp,
                "level": event.level,
                "target": event.target,
                "message": event.message,
            }
            for event in runtime_events
        ],
        "quoted_prompt_or_output_lines_counted": 0,
    }
    write_json(context_dir / "runtime-events.json", runtime_document)
    lifecycle = {
        "contract": "risk-carried-model-context-lifecycle-v1",
        "run": run,
        "stage": stage,
        "batch_number": batch_number,
        "invocation_id": invocation_id,
        "session_id": session_id,
        "session_id_observation_count": len(sessions),
        "session_identity_unique": session_unique,
        "runtime_state_namespace_hash": namespace,
        "runtime_state_namespace_unique": namespace_unique,
        "receipt_status": receipt.get("status", "NOT_CREATED"),
        "exit_code": receipt.get("exit_code"),
        "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
        "input_bytes": receipt.get("input_bytes"),
        "stdout_bytes": receipt.get("stdout_bytes"),
        "stderr_bytes": receipt.get("stderr_bytes"),
        "output_bytes": receipt.get("output_bytes"),
        "termination_initiator": receipt.get("termination_initiator"),
        "child_cleanup_status": receipt.get("child_cleanup_status"),
        "orphan_model_process_count": receipt.get("orphan_model_process_count"),
        "root_exception": (
            f"{type(primary_error).__name__}:{primary_error}" if primary_error is not None else None
        ),
        "classification": classification,
        "stderr_original_sha256": hashlib.sha256(stderr_bytes).hexdigest(),
        "stderr_original_byte_size": len(stderr_bytes),
        "stderr_preserved_sha256": hashlib.sha256(stderr_safe).hexdigest(),
        "stderr_preserved_byte_size": len(stderr_safe),
        "stderr_exact_bytes": stderr_bytes == stderr_safe,
        "artifact_preservation": preservation,
    }
    write_json(context_dir / "artifact-preservation.json", preservation)
    write_json(context_dir / "lifecycle-summary.json", lifecycle)
    return lifecycle


@contextmanager
def _instrument_model_contexts() -> Iterator[None]:
    original = runner.invoke_model_context

    def instrumented(**kwargs: object):
        args = kwargs["args"]
        assert isinstance(args, argparse.Namespace)
        run = str(kwargs["run"])
        stage = str(kwargs["stage"])
        batch_number = int(kwargs["batch_number"])
        context_dir = runner.context_directory(args.output_root, run, stage, batch_number)
        primary_error: BaseException | None = None
        result = None
        try:
            result = original(**kwargs)
        except BaseException as exc:
            primary_error = exc
        lifecycle_error: BaseException | None = None
        lifecycle: dict[str, object] | None = None
        try:
            lifecycle = augment_runtime_context(
                args=args,
                run=run,
                stage=stage,
                batch_number=batch_number,
                context_dir=context_dir,
                invocation_id=str(
                    runner.runtime_identity.load_binding(
                        context_dir / "identity-binding-lock.json"
                    ).invocation_id
                ),
                primary_error=primary_error,
            )
            manifest_path = context_dir / "context_manifest.json"
            if manifest_path.is_file():
                manifest = read_json(manifest_path)
                manifest.update(
                    {
                        "runtime_events_path": "runtime-events.json",
                        "lifecycle_summary_path": "lifecycle-summary.json",
                        "artifact_preservation_path": "artifact-preservation.json",
                        "workload_observation_path": "workload-observation.json",
                        "passive_runtime_classification": lifecycle["classification"]["outcome"],
                    }
                )
                write_json(manifest_path, manifest)
                if result is not None:
                    result = (manifest, result[1])
            if primary_error is None and (
                lifecycle["artifact_preservation"]["status"] != "PASS"
                or not lifecycle["classification"]["usable"]
                or not lifecycle["session_identity_unique"]
                or not lifecycle["runtime_state_namespace_unique"]
            ):
                lifecycle_error = runner.SemanticStop(
                    f"runtime_context_gate_failed:{run}:{stage}:{batch_number}"
                )
        except BaseException as exc:
            lifecycle_error = exc
        if primary_error is not None:
            if lifecycle_error is not None:
                state = kwargs["state"]
                assert isinstance(state, dict)
                state["context_preservation_secondary_failure_count"] = (
                    int(state.get("context_preservation_secondary_failure_count") or 0) + 1
                )
                state["context_preservation_secondary_failure"] = (
                    f"{type(lifecycle_error).__name__}:{lifecycle_error}"
                )
                write_json(args.output_root / "program-state.json", state)
            raise primary_error
        if lifecycle_error is not None:
            raise lifecycle_error
        assert result is not None
        return result

    runner.invoke_model_context = instrumented
    try:
        yield
    finally:
        runner.invoke_model_context = original


def _persist_run_outputs(
    args: argparse.Namespace,
    run: str,
    document: Mapping[str, object],
    state: Mapping[str, object],
) -> dict[str, object]:
    source_lock = read_json(args.output_root / "source-lock.json")
    root = args.output_root / "issuer-results" / run.upper()
    rows = [row for row in document.get("rows") or [] if isinstance(row, Mapping)]
    for row in rows:
        ticker = str(row["ticker"])
        directory = root / ticker
        write_json(directory / "composed-state.json", row["composed"])
        write_text(directory / "rendered-message.txt", str(row["rendered_message"]))
        write_json(
            directory / "renderer-input-lineage.json",
            {
                "contract": "risk-carried-renderer-input-lineage-v1",
                "ticker": ticker,
                "run": run,
                "source_generation_id": state["source_generation_id"],
                "runtime_generation_id": state["program_generation_id"],
                "source_lock_sha256": state["source_lock_sha256"],
                "packet_sha256": source_lock["packet_sha256"][ticker],
                "core": row["core"],
                "timing": row["timing"],
                "ownership": row["ownership"],
                "status": row["status"],
            },
        )
    quality = document.get("message_quality")
    write_json(
        args.output_root / "run-artifacts" / run.upper() / "message-quality.json",
        {
            "contract": "risk-carried-advisory-message-quality-v1",
            "run": run,
            "gate_role": QUALITY_GATE_ROLE,
            "result": quality,
            "completed_message_count": len(rows),
            "status": "RECORDED",
        },
    )
    return {
        "run": run,
        "composed_state_count": len(list(root.rglob("composed-state.json"))),
        "rendered_message_count": len(list(root.rglob("rendered-message.txt"))),
        "renderer_lineage_count": len(list(root.rglob("renderer-input-lineage.json"))),
        "status": "PASS" if len(rows) == TARGET_TOTAL else "FAIL",
    }


def _scan_execution(args: argparse.Namespace) -> dict[str, object]:
    contexts = sorted((args.output_root / "model-contexts").rglob("context_manifest.json"))
    receipts = sorted((args.output_root / "model-contexts").rglob("transport_receipt.json"))
    lifecycle_paths = sorted((args.output_root / "model-contexts").rglob("lifecycle-summary.json"))
    outputs = sorted((args.output_root / "model-contexts").rglob("output.raw.json"))
    normalized = sorted((args.output_root / "model-contexts").rglob("output.normalized.json"))
    audits = sorted((args.output_root / "model-contexts").rglob("partial_semantic_audit.json"))
    lifecycle = [read_json(path) for path in lifecycle_paths]
    receipt_rows = [read_json(path) for path in receipts]
    raw_rows = 0
    exposed: set[str] = set()
    for path in outputs:
        document = read_json(path)
        candidates = document.get("candidates")
        if isinstance(candidates, list):
            raw_rows += len(candidates)
            for row in candidates:
                if isinstance(row, Mapping) and row.get("ticker"):
                    exposed.add(str(row["ticker"]))
    accepted_rows = sum(len(read_json(path).get("candidates") or []) for path in normalized)
    checked_rows = sum(len(read_json(path).get("rows") or []) for path in audits)
    classifications = [
        row.get("classification")
        for row in lifecycle
        if isinstance(row.get("classification"), Mapping)
    ]
    outcomes = Counter(str(row.get("outcome")) for row in classifications)
    run_stage_attempts: Counter[str] = Counter()
    run_stage_successes: Counter[str] = Counter()
    for manifest_path in contexts:
        manifest = read_json(manifest_path)
        key = f"{str(manifest.get('run_id')).upper()}:{manifest.get('stage')}"
        run_stage_attempts[key] += 1
        if manifest.get("status") == "PASS":
            run_stage_successes[key] += 1
    composed = len(list((args.output_root / "issuer-results").rglob("composed-state.json")))
    rendered = len(list((args.output_root / "issuer-results").rglob("rendered-message.txt")))
    preservation_failures = sum(
        row.get("artifact_preservation", {}).get("status") != "PASS" for row in lifecycle
    )
    return {
        "contract": "risk-carried-execution-reconciliation-v1",
        "planned_contexts": EXPECTED_TOTAL_CONTEXTS,
        "attempted_contexts": len(contexts),
        "terminal_contexts": len(receipts),
        "successful_contexts": sum(row.get("status") == "PASS" for row in receipt_rows),
        "failed_contexts": sum(row.get("status") != "PASS" for row in receipt_rows),
        "not_run_contexts": EXPECTED_TOTAL_CONTEXTS - len(contexts),
        "per_run_stage_attempts": dict(sorted(run_stage_attempts.items())),
        "per_run_stage_successes": dict(sorted(run_stage_successes.items())),
        "raw_output_document_count": len(outputs),
        "raw_stage_rows": raw_rows,
        "accepted_stage_rows": accepted_rows,
        "semantic_checked_rows": checked_rows,
        "unique_issuer_output_count": len(exposed),
        "unique_issuer_outputs": sorted(exposed),
        "composed_rows": composed,
        "rendered_rows": rendered,
        "context_preservation_failures": preservation_failures,
        "wrapper_explicit_retry_count": 0,
        "observed_cli_retry_signal_count": sum(
            int(row.get("observed_cli_retry_signal_count") or 0) for row in classifications
        ),
        "observed_websocket_disconnect_signal_count": sum(
            int(row.get("observed_websocket_disconnect_signal_count") or 0)
            for row in classifications
        ),
        "upstream_request_attempt_count": "UNKNOWN",
        "request_accepted_observability": "UNAVAILABLE",
        "disconnect_then_success_count": outcomes["DISCONNECT_THEN_SUCCESS_OBSERVED"],
        "disconnect_then_timeout_count": outcomes["DISCONNECT_THEN_WATCHDOG_TIMEOUT_OBSERVED"],
        "explicit_capacity_count": outcomes["EXPLICIT_CAPACITY_FAILURE_OBSERVED"],
        "explicit_context_failure_count": outcomes["EXPLICIT_CONTEXT_FAILURE_OBSERVED"],
        "watchdog_timeout_count": sum(
            outcome
            in {
                "DISCONNECT_THEN_WATCHDOG_TIMEOUT_OBSERVED",
                "TIMEOUT_WITHOUT_OBSERVED_DISCONNECT",
            }
            for outcome in outcomes.elements()
        ),
        "orphan_count": sum(int(row.get("orphan_model_process_count") or 0) for row in lifecycle),
        "distinct_session_count": len(
            {str(row["session_id"]) for row in lifecycle if row.get("session_id")}
        ),
        "distinct_namespace_count": len(
            {
                str(row["runtime_state_namespace_hash"])
                for row in lifecycle
                if row.get("runtime_state_namespace_hash")
            }
        ),
        "status": "PASS" if preservation_failures == 0 else "FAIL",
    }


def _write_no_change_proofs(args: argparse.Namespace) -> dict[str, object]:
    production = {
        "contract": "risk-carried-production-and-policy-no-change-v1",
        "production_scheduler_mutation": 0,
        "auto_resume_executed": 0,
        "production_db_mutation": 0,
        "production_send": 0,
        "main_merge_or_deployment": 0,
        "monitoring_registration_change": 0,
        "live_v2_or_structured_autonomy_activation": 0,
        "night_futures_change": 0,
        "paid_data_service_change": 0,
        "new_free_api_management_gate": 0,
        "canonical_transport_mutation": 0,
        "model_or_effort_change": 0,
        "timeout_increase": 0,
        "wrapper_explicit_retry_count": 0,
        "historical_b_or_c_resumed": 0,
        "status": "PASS",
    }
    runner.write_proof(args.report_dir, 57, production)
    runner.write_proof(
        args.report_dir,
        58,
        {
            "contract": "night-futures-no-change-v1",
            "night_futures_code_mutation": 0,
            "night_futures_decision_packet_injection": 0,
            "status": "PASS",
        },
    )
    return production


def _run_gate_summary(args: argparse.Namespace) -> dict[str, object]:
    rows = []
    for run in runner.RUNS:
        numbers = runner.RUN_PROOFS[run]
        execution = read_json(runner.proof_path(args.report_dir, numbers[0]))
        ownership = read_json(runner.proof_path(args.report_dir, numbers[3]))
        renderer = read_json(runner.proof_path(args.report_dir, numbers[4]))
        hard = read_json(runner.proof_path(args.report_dir, numbers[5]))
        rows.append(
            {
                "run": run,
                "execution": execution.get("status"),
                "validation_pass_count": execution.get("validation_pass_count"),
                "ownership": ownership.get("status"),
                "renderer": renderer.get("status"),
                "hard_safety": hard.get("status"),
            }
        )
    return {
        "contract": "risk-carried-per-run-hard-gate-summary-v1",
        "rows": rows,
        "status": (
            "PASS"
            if all(
                row[key] == "PASS"
                for row in rows
                for key in ("execution", "ownership", "renderer", "hard_safety")
            )
            else "INCOMPLETE_OR_FAILED"
        ),
    }


def _quality_summary(args: argparse.Namespace) -> dict[str, object]:
    rows = []
    for run in runner.RUNS:
        path = runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][0])
        document = read_json(path)
        quality = document.get("message_quality")
        if not isinstance(quality, Mapping):
            rows.append({"run": run, "status": "NOT_MEASURED"})
            continue
        repeated = quality.get("repeated_substantive_spans")
        rows.append(
            {
                "run": run,
                "status": quality.get("status"),
                "repeated_substantive_span_count": (
                    len(repeated) if isinstance(repeated, list) else None
                ),
                "quality": quality,
            }
        )
    return {
        "contract": "risk-carried-advisory-message-quality-summary-v1",
        "gate_role": QUALITY_GATE_ROLE,
        "rows": rows,
        "issuer_specific_evidence_omission_status": "NOT_MEASURED",
        "status": "RECORDED",
    }


def execute(args: argparse.Namespace) -> None:
    _configure_prior_module()
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "SEALED_FROZEN":
        raise ValueError("sealed_frozen_state_required")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_first_real_call")
    if git_value("rev-parse", "HEAD") != state.get("final_precommit_commit"):
        raise ValueError("final_precommit_commit_drift")
    prior.verify_frozen(args, state)
    cli = diagnostic.cli_identity()
    if cli != state.get("signed_in_cli_identity"):
        raise ValueError("signed_in_cli_identity_drift_before_execution")

    (
        state,
        cohort,
        _packets,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = runner.load_inputs(args)
    state["state"] = "EXECUTING"
    state["execution_started_at"] = datetime.now(UTC).isoformat()
    write_json(args.output_root / "program-state.json", state)
    guard = diagnostic.SingleObservationWorkloadGuard(
        args.output_root / "live-workload-coexistence-audit.json",
        observer=diagnostic.PausedScheduleProcessObserver(),
    )
    adapter = RiskCarriedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["program_generation_id"]),
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=engine._signed_in_codex_bin(),
    )
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    with _instrument_model_contexts():
        for run in runner.RUNS:
            if stop_reason is not None:
                runner.write_not_run(args, run, stop_reason)
                continue
            try:
                prior.verify_frozen(args, state)
                document = runner.execute_run(
                    args=args,
                    state=state,
                    adapter=adapter,
                    run=run,
                    cohort=cohort,
                    contexts=contexts,
                    evidence=evidence,
                    owned=owned,
                    core_aliases=core_aliases,
                    timing_aliases=timing_aliases,
                    price_maps=price_maps,
                    stocks=stocks,
                )
                document = prior._augment_run(args, run, document)
                preservation = _persist_run_outputs(args, run, document, state)
                document["deterministic_result_preservation"] = preservation
                document["message_quality_gate_role"] = QUALITY_GATE_ROLE
                runner.write_proof(args.report_dir, runner.RUN_PROOFS[run][0], document)
                required = (
                    "execution_status",
                    "identity_gate_status",
                    "ownership_gate_status",
                    "renderer_gate_status",
                    "hard_safety_gate_status",
                    "preservation_status",
                )
                if any(document.get(key) != "PASS" for key in required):
                    raise runner.SemanticStop(f"{run}_required_gate_failed")
                if preservation["status"] != "PASS":
                    raise runner.SemanticStop(f"{run}_deterministic_result_preservation_failed")
                documents[run] = document
                state["run_results"][run] = f"{document['validation_pass_count']}/{TARGET_TOTAL}"
                state["real_investment_model_invocation_count"] = adapter.model_call_count
                write_json(args.output_root / "program-state.json", state)
            except BaseException as exc:
                stop_reason = f"{type(exc).__name__}:{exc}"
                exposure = prior._scan_real_exposure(args.output_root, cohort)
                state["exposed_subjects"] = exposure["unique_exposed_issuers"]
                state["holdout_output_exposure_state"] = exposure["output_exposure_state"]
                state["stop_reason"] = stop_reason
                state["real_investment_model_invocation_count"] = adapter.model_call_count
                write_json(args.output_root / "program-state.json", state)
                runner.write_failed_run(args, run, stop_reason)
                for pending in runner.RUNS[runner.RUNS.index(run) + 1 :]:
                    runner.write_not_run(args, pending, stop_reason)
                break

    exposure = prior._scan_real_exposure(args.output_root, cohort)
    state["exposed_subjects"] = exposure["unique_exposed_issuers"]
    state["holdout_output_exposure_state"] = exposure["output_exposure_state"]
    state["model_invocation_count"] = adapter.model_call_count
    state["real_investment_model_invocation_count"] = adapter.model_call_count
    write_json(args.output_root / "program-state.json", state)
    runner.final_proofs(args=args, state=state, documents=documents, stop_reason=stop_reason)
    state = read_json(args.output_root / "program-state.json")
    execution = _scan_execution(args)
    write_json(args.output_root / "execution-reconciliation.json", execution)
    gate_summary = _run_gate_summary(args)
    quality = _quality_summary(args)
    write_json(args.output_root / "run-gate-summary.json", gate_summary)
    write_json(args.output_root / "advisory-message-quality-summary.json", quality)
    production = _write_no_change_proofs(args)
    completion_path = runner.proof_path(args.report_dir, 60)
    completion = read_json(completion_path)
    completion.update(
        {
            "input_zip_sha256": DIAGNOSTIC_ZIP_SHA256,
            "input_integrity_status": "PASS",
            "historical_predecessor_zip_sha256": PREDECESSOR_ZIP_SHA256,
            "exclusion_registry_count": EXCLUSION_COUNT,
            "frozen_evaluation_cutoff": state.get("as_of"),
            "precommit_hash": state.get("precommit_sha256"),
            "precommit_time": state.get("execution_sealed_at"),
            "first_spawn_time": min(
                (
                    str(row.get("started_at"))
                    for row in (
                        read_json(path)
                        for path in sorted(
                            (args.output_root / "model-contexts").rglob("transport_receipt.json")
                        )
                    )
                    if row.get("started_at")
                ),
                default=None,
            ),
            "acceptance_protocol_hash": state.get("acceptance_protocol_sha256"),
            "quality_gate_role": QUALITY_GATE_ROLE,
            "execution_reconciliation": execution,
            "per_run_gates": gate_summary,
            "message_quality": quality,
            "production_and_policy_change_ledger": production,
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
            "runtime_reliability_status": "NOT_ESTABLISHED",
            "reconnect_path_exercised": (
                "OBSERVED"
                if execution["observed_websocket_disconnect_signal_count"]
                else "NOT_OBSERVED"
            ),
            "status": (
                "PASS" if str(completion.get("readiness") or "").startswith("READY_") else "STOPPED"
            ),
        }
    )
    runner.write_proof(args.report_dir, 60, completion)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "execution_reconciliation": execution,
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
            "stop_reason": stop_reason,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir)
    _write_compact_reports(args)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _compact_documents(args: argparse.Namespace) -> list[dict[str, object]]:
    state = read_json(args.output_root / "program-state.json")

    def proof(number: int) -> dict[str, Any]:
        return read_json(runner.proof_path(args.report_dir, number))

    execution = (
        read_json(args.output_root / "execution-reconciliation.json")
        if (args.output_root / "execution-reconciliation.json").is_file()
        else {
            "planned_contexts": EXPECTED_TOTAL_CONTEXTS,
            "attempted_contexts": 0,
            "not_run_contexts": EXPECTED_TOTAL_CONTEXTS,
            "status": "NOT_RUN",
        }
    )
    return [
        {
            "contract": "risk-carried-input-provenance-pause-v1",
            "repository": proof(1),
            "inputs": proof(2),
            "pause": state.get("initial_pause_observation"),
            "latest_pause": closeout.observe_pause_state(),
            "carried_runtime_risk": CARRIED_RUNTIME_RISK,
            "status": "PASS",
        },
        {
            "contract": "risk-carried-selection-source-summary-v1",
            "registry": {
                "count": proof(3).get("reconciled_registry_count"),
                "sha256": state.get("exclusion_registry_sha256"),
            },
            "policy": proof(5),
            "us_source": proof(7),
            "kr_source": proof(10),
            "selection": proof(15),
            "status": proof(12).get("dual_market_source_status"),
        },
        {
            "contract": "risk-carried-source-lock-precommit-summary-v1",
            "source_lock": proof(19) if runner.proof_path(args.report_dir, 19).is_file() else None,
            "precommit": proof(20) if runner.proof_path(args.report_dir, 20).is_file() else None,
            "execution_seal": (
                read_json(args.output_root / "execution-freeze-seal.json")
                if (args.output_root / "execution-freeze-seal.json").is_file()
                else None
            ),
            "status": "FROZEN" if state.get("ordered_cohort") else "NOT_RUN",
        },
        execution,
        _run_gate_summary(args),
        _quality_summary(args),
        {
            "contract": "risk-carried-stability-generalization-summary-v1",
            "core_stability": proof(52),
            "timing_stability": proof(53),
            "ownership_generalization": proof(54),
            "status": proof(54).get("status"),
        },
        {
            "contract": "risk-carried-exposure-counter-summary-v1",
            "exposure_retirement": proof(51),
            "execution": execution,
            "status": proof(51).get("status"),
        },
        proof(57),
        proof(60),
    ]


def _write_compact_reports(args: argparse.Namespace) -> None:
    compact_root = args.report_dir / "compact"
    compact_root.mkdir(parents=True, exist_ok=True)
    for name, document in zip(COMPACT_REPORT_NAMES, _compact_documents(args), strict=True):
        write_json(compact_root / f"{name}.json", document)
        write_text(
            compact_root / f"{name}.md",
            runner.report_body(name, document),
        )


def close_reports(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    closeable_state = state.get("state") == "EVIDENCE_COMPLETE" or (
        state.get("source_gate_only") and state.get("state") == "READY_TO_PACKAGE"
    )
    if not closeable_state:
        raise ValueError("evidence_complete_state_required")
    if state.get("source_gate_only"):
        configuration = _source_configuration_audit()
        _write_pre_model_terminal_proofs(
            args,
            state=state,
            reason=str(state.get("stop_reason") or "SOURCE_PREPARATION_FAILED"),
            configuration=configuration,
        )
    completion_path = runner.proof_path(args.report_dir, 60)
    completion = read_json(completion_path)
    if state.get("source_gate_only"):
        us_audit = read_json(runner.proof_path(args.report_dir, 7))
        kr_audit = read_json(runner.proof_path(args.report_dir, 10))
        configuration = read_json(args.output_root / "source-configuration-audit.json")
        source_requests = {
            "us": dict(us_audit.get("provider_totals") or {}),
            "kr": dict(kr_audit.get("provider_totals") or {}),
        }
        configuration_blocked = configuration.get("status") != "PASS"
        readiness = (
            "NOT_READY_PREPARATION_CONFIGURATION_BLOCKED"
            if configuration_blocked
            else "NOT_READY_SOURCE_COVERAGE_BLOCKED"
        )
        next_scope = (
            "BOUNDED_EXISTING_SECRET_ENV_BINDING_REPAIR"
            if configuration_blocked
            else "BOUNDED_SOURCE_COVERAGE_REVIEW"
        )
        stop_reason = (
            "REQUIRED_SOURCE_CONFIGURATION_UNAVAILABLE"
            if configuration_blocked
            else str(state.get("stop_reason") or "SOURCE_COVERAGE_BLOCKED")
        )
        completion.update(
            {
                "base_sha": state.get("base_sha"),
                "work_instruction_commit": state.get("work_instruction_commit"),
                "implementation_commit": git_value("rev-parse", "HEAD"),
                "branch": state.get("branch"),
                "input_zip_sha256": DIAGNOSTIC_ZIP_SHA256,
                "input_integrity_status": "PASS",
                "historical_predecessor_zip_sha256": PREDECESSOR_ZIP_SHA256,
                "pause_observed_at": state.get("initial_pause_observation", {}).get(
                    "observed_at"
                ),
                "observed_paused_schedule_count": state.get(
                    "initial_pause_observation", {}
                ).get("observed_scheduler_object_count"),
                "unexpected_active_paths": state.get(
                    "initial_pause_observation", {}
                ).get("unexpected_active_paths", []),
                "selection_policy_hash": state.get("selection_policy_sha256"),
                "exclusion_registry_hash": state.get("exclusion_registry_sha256"),
                "exclusion_registry_count": state.get("exclusion_registry_count"),
                "source_generation_id": None,
                "source_lock": None,
                "ordered_issuers": [],
                "issuer_market_mix": {"us": 0, "kr": 0},
                "frozen_evaluation_cutoff": (
                    args.as_of.isoformat() if args.as_of is not None else None
                ),
                "source_configuration": configuration,
                "source_provider_totals": source_requests,
                "planned_contexts": EXPECTED_TOTAL_CONTEXTS,
                "attempted_contexts": 0,
                "terminal_contexts": 0,
                "successful_contexts": 0,
                "failed_contexts": 0,
                "not_run_contexts": EXPECTED_TOTAL_CONTEXTS,
                "raw_output_document_count": 0,
                "raw_stage_rows": 0,
                "accepted_stage_rows": 0,
                "checked_stage_rows": 0,
                "unique_issuer_output_count": 0,
                "composed_rows": 0,
                "rendered_rows": 0,
                "wrapper_retry_count": 0,
                "observed_cli_retry_signal_count": 0,
                "observed_disconnect_count": 0,
                "upstream_request_attempt_count": "NOT_APPLICABLE_NO_MODEL_SPAWN",
                "request_accepted_observability": "NOT_APPLICABLE_NO_MODEL_SPAWN",
                "orphan_count": 0,
                "exposure_state": "UNEXPOSED",
                "semantic_revelation_state": "NOT_MEASURED",
                "retirement_state": "NOT_APPLICABLE_NO_LOCKED_COHORT",
                "future_unseen_reuse_allowed": "SEPARATE_EXPLICIT_DECISION_REQUIRED",
                "same_cohort_tuning_rerun_allowed": 0,
                "core_stability": "NOT_MEASURED",
                "timing_stability": "NOT_MEASURED",
                "formal_generalization": "NOT_MEASURED",
                "quality_gate_role": QUALITY_GATE_ROLE,
                "open_message_quality_findings": "NOT_MEASURED",
                "carried_runtime_risk": CARRIED_RUNTIME_RISK,
                "runtime_reliability_status": "NOT_ESTABLISHED",
                "proof_status": (
                    "STOPPED_PRE_MODEL_PREPARATION_CONFIGURATION_FAILURE"
                    if configuration_blocked
                    else "STOPPED_PRE_MODEL_SOURCE_FAILURE"
                ),
                "readiness": readiness,
                "stop_reason": stop_reason,
                "next_scope": next_scope,
                "status": "STOPPED",
            }
        )
    completion.update(
        {
            "focused_tests": args.focused_tests,
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "validation_recorded_at": datetime.now(UTC).isoformat(),
        }
    )
    validation_pass = all(
        value == "PASS"
        for value in (
            args.focused_tests,
            args.full_tests,
            args.ruff,
            args.diff_check,
        )
    )
    if not validation_pass:
        completion["readiness"] = "NOT_READY_VALIDATION_FAILED"
        completion["next_scope"] = "BOUNDED_VALIDATION_REPAIR"
        completion["status"] = "STOPPED"
    runner.write_proof(args.report_dir, 60, completion)
    runner.write_reports(args.report_dir)
    _write_compact_reports(args)
    write_text(
        args.report_dir / "README.md",
        "# Fresh Issuer Ownership Proof with Transport Risk Carried\n\n"
        f"- Cohort: `{len(state.get('ordered_cohort') or [])}` issuers\n"
        f"- Source generation: `{state.get('source_generation_id')}`\n"
        f"- Runtime generation: `{state.get('program_generation_id')}`\n"
        f"- Real model subprocesses: `{state.get('model_invocation_count', 0)}`\n"
        f"- Readiness: `{completion.get('readiness')}`\n"
        f"- Runtime risk: `{CARRIED_RUNTIME_RISK}`\n\n"
        "The eight monitoring scheduler objects remain paused. This proof changes no "
        "production delivery, registration, database state, transport policy, model or "
        "timeout. The compact directory contains the ten-part completion report; proofs "
        "retain the detailed machine evidence.\n",
    )
    state["state"] = "READY_TO_PACKAGE"
    state["readiness"] = completion.get("readiness")
    state["stop_reason"] = completion.get("stop_reason")
    state["next_scope"] = completion.get("next_scope")
    state["validation"] = {
        "focused_tests": args.focused_tests,
        "full_tests": args.full_tests,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
    }
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file():
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def _safe_member(name: str) -> bool:
    return not (name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts)


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "READY_TO_PACKAGE":
        raise ValueError("ready_to_package_state_required")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_for_final_package")
    if args.bundle_root.exists() or args.zip_output.exists():
        raise ValueError("new_bundle_root_and_zip_required")
    args.bundle_root.mkdir(parents=True)
    _copy_tree(args.report_dir, args.bundle_root / "reports")
    _copy_tree(args.output_root, args.bundle_root / "experiment")
    shutil.copyfile(
        Path.cwd() / WORK_INSTRUCTION_PATH,
        args.bundle_root / "work-instruction.md",
    )
    with zipfile.ZipFile(args.diagnostic_zip) as archive:
        for member in (
            "completion.json",
            "experiment/historical-baseline-facts.json",
            "reports/08-program-completion.json",
        ):
            target = args.bundle_root / "historical" / "latest-diagnostic" / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    with zipfile.ZipFile(args.predecessor_zip) as archive:
        for member in (
            "completion.json",
            "reports/proofs/08-exposure-retirement-measurement-mapping.json",
            "reports/proofs/12-program-completion.json",
        ):
            target = args.bundle_root / "historical" / "predecessor" / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    completion = read_json(runner.proof_path(args.report_dir, 60))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "final_tree_sha": git_value("rev-parse", "HEAD^{tree}"),
            "branch": git_value("branch", "--show-current"),
            "worktree_clean_at_package": True,
            "packaged_at": datetime.now(UTC).isoformat(),
        }
    )
    write_json(args.bundle_root / "completion.json", completion)
    write_text(
        args.bundle_root / "README.md",
        (args.report_dir / "README.md").read_text(encoding="utf-8"),
    )
    payloads = sorted(
        path
        for path in args.bundle_root.rglob("*")
        if path.is_file() and path != args.bundle_root / "artifact-index.json"
    )
    rows = []
    for path in payloads:
        scan = scan_artifact_secrets([path])
        if scan["secret_scan_status"] != "PASS":
            raise ValueError(f"artifact_secret_scan_failed:{path}")
        rows.append(
            {
                "path": str(path.relative_to(args.bundle_root)),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "secret_scan_status": "PASS",
            }
        )
    index = {
        "contract": "risk-carried-fresh-proof-artifact-index-v1",
        "index_self_exclusion": "artifact-index.json",
        "all_payload_files_except_index_itself_individually_indexed": True,
        "indexed_payload_count": len(rows),
        "rows": rows,
        "status": "PASS",
    }
    write_json(args.bundle_root / "artifact-index.json", index)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.bundle_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(args.bundle_root))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        names = archive.namelist()
        archived_index = json.loads(archive.read("artifact-index.json"))
        indexed = {str(row["path"]): row for row in archived_index["rows"]}
        expected = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for name, row in indexed.items():
            payload = archive.read(name)
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row["sha256"]
            size_mismatches += len(payload) != row["byte_size"]
        failures = {
            "duplicate_members": len(names) - len(set(names)),
            "unsafe_members": sum(not _safe_member(name) for name in names),
            "crc_failure": archive.testzip(),
            "index_membership_mismatch": int(set(indexed) != expected),
            "hash_mismatches": hash_mismatches,
            "size_mismatches": size_mismatches,
        }
    if any(bool(value) for value in failures.values()):
        raise ValueError(f"final_zip_integrity_failure:{failures}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    state.update(
        {
            "state": "COMPLETE",
            "final_head_sha": completion["final_head_sha"],
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha,
            "zip_member_count": len(names),
            "indexed_payload_count": len(rows),
            "zip_integrity_mismatches": failures,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-selection", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--close-reports", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--diagnostic-zip", type=Path, required=True)
    parser.add_argument("--predecessor-zip", type=Path, required=True)
    parser.add_argument("--historical-zip", type=Path, required=True)
    parser.add_argument("--expansion-zip", type=Path, required=True)
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=runner.TIMEOUT_SECONDS)
    parser.add_argument("--focused-tests", default="NOT_RUN")
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument("--zip-output", type=Path, required=True)
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "bundle_root",
        "diagnostic_zip",
        "predecessor_zip",
        "historical_zip",
        "expansion_zip",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.freeze_selection:
        freeze_selection(args)
    elif args.prepare:
        prepare(args)
    elif args.seal:
        seal(args)
    elif args.execute:
        execute(args)
    elif args.close_reports:
        close_reports(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
