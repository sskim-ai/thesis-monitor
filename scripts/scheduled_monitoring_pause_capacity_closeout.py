from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
import zipfile
from collections import Counter
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any

from app.services.direction_timing_ownership_service import (
    DirectionalCoreCandidate,
    PriceTimingCandidate,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import new_issuer_holdout_selection_ownership_proof as proof_runner
from scripts import runtime_identity_binding as runtime_identity


CONTRACT = "scheduled-monitoring-pause-capacity-failure-closeout-v1"
HISTORICAL_ZIP_NAME = (
    "thesis-monitor-20260907-new-issuer-final-freeze-ownership-proof-"
    "existing-data-routes-report.zip"
)
HISTORICAL_ZIP_SHA256 = (
    "48f0ad3a82e332aaed61106717f8ca660a7cc297ff4353a283c5db0ca1c009fa"
)
SOURCE_GENERATION_ID = "20260907-new-issuer-source-20260907T055608Z-52f069785a77"
RUNTIME_GENERATION_ID = "20260907-new-issuer-proof-20260907T055608Z-0446826566f6"
SOURCE_LOCK_SHA256 = "fc4ef965e06e926f0b84bebc0716915e34080b692040e92e990e2517d01a21ea"
FAILED_INVOCATION_ID = (
    "20260907-new-issuer-proof-20260907T055608Z-0446826566f6:"
    "first:PRICE_TIMING:03"
)
CAPACITY_DIAGNOSTIC = "ERROR: Selected model is at capacity. Please try a different model."
COHORT = (
    "NVMI",
    "SKYH",
    "WKSP",
    "EROC",
    "373160",
    "452200",
    "389470",
    "380550",
    "008970",
    "047080",
    "068270",
    "475830",
    "033160",
    "079940",
    "103140",
    "278280",
)
REPORT_NAMES = (
    "01-input-integrity-and-repository-provenance",
    "02-us-kr-schedule-identity-and-before-state",
    "03-us-kr-pause-action-and-after-state",
    "04-restoration-reference-no-auto-resume",
    "05-capacity-error-lifecycle-classification",
    "06-preserved-partial-context-manifest",
    "07-offline-core16-timing8-audit",
    "08-composer-renderer-recovery-or-offline-derivatives",
    "09-failure-report-reconciliation",
    "10-targeted-tests-and-bounded-diff",
    "11-exposure-retirement-and-exclusion-update",
    "12-production-change-accounting",
    "13-program-completion-and-next-scope",
)
PRESERVED_CONTEXT_FILES = (
    "actual-request-identity-preflight.json",
    "context_manifest.json",
    "identity-binding-lock.json",
    "output-identity-validation.json",
    "output.normalized.json",
    "output.raw.json",
    "partial_semantic_audit.json",
    "prompt.txt",
    "receipt-identity-validation.json",
    "schema.json",
    "stderr.raw.log",
    "stdout.raw.log",
    "transport_log.raw.log",
    "transport_receipt.json",
)
AUTHORITY_MEMBERS = (
    "artifact-index.json",
    "experiment/program-state.json",
    "experiment/source-lock.json",
    "reports/proofs/03-prior-real-issuer-exposure-registry.json",
    "reports/proofs/04-new-holdout-exclusion-set.json",
    "reports/proofs/18-source-identity-audit.json",
    "reports/proofs/27-first-execution-summary.json",
    "reports/proofs/51-holdout-exposure-retirement-state.json",
    "reports/proofs/60-program-completion.json",
    "reports/proofs/61-existing-data-routes-final-freeze-ownership-proof-completion.json",
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def verify_historical_archive(path: Path) -> dict[str, object]:
    if path.name != HISTORICAL_ZIP_NAME:
        raise ValueError("historical_zip_name_mismatch")
    actual_sha = file_sha256(path)
    if actual_sha != HISTORICAL_ZIP_SHA256:
        raise ValueError("historical_zip_sha256_mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
        unsafe = sorted(
            name
            for name in names
            if name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts
        )
        crc_failure = archive.testzip()
        index = zip_json(archive, "artifact-index.json")
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("historical_index_rows_missing")
        indexed = {
            str(row["path"]): row
            for row in rows
            if isinstance(row, Mapping) and row.get("path")
        }
        payload_names = set(names) - {"artifact-index.json"}
        hash_mismatches = []
        size_mismatches = []
        for name in sorted(payload_names & set(indexed)):
            payload = archive.read(name)
            row = indexed[name]
            if bytes_sha256(payload) != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("byte_size"):
                size_mismatches.append(name)
        missing_index = sorted(payload_names - set(indexed))
        unexpected_index = sorted(set(indexed) - payload_names)
        completion = zip_json(
            archive,
            "reports/proofs/61-existing-data-routes-final-freeze-ownership-proof-"
            "completion.json",
        )
        source_lock = zip_json(archive, "experiment/source-lock.json")
        checks = {
            "zip_sha256": actual_sha == HISTORICAL_ZIP_SHA256,
            "member_count": len(names) == 912,
            "indexed_payload_count": len(rows) == 911,
            "crc": crc_failure is None,
            "duplicates": not duplicates,
            "safe_paths": not unsafe,
            "index_membership": not missing_index and not unexpected_index,
            "indexed_hashes": not hash_mismatches,
            "indexed_sizes": not size_mismatches,
            "source_generation": source_lock.get("source_generation_id")
            == SOURCE_GENERATION_ID,
            "runtime_generation": completion.get("runtime_generation_id")
            == RUNTIME_GENERATION_ID,
            "source_lock": source_lock.get("source_lock_sha256") == SOURCE_LOCK_SHA256,
        }
        if not all(checks.values()):
            failed = sorted(key for key, value in checks.items() if not value)
            raise ValueError(f"historical_archive_integrity_failed:{','.join(failed)}")
        return {
            "contract": "historical-closeout-input-integrity-v1",
            "path": str(path),
            "expected_sha256": HISTORICAL_ZIP_SHA256,
            "actual_sha256": actual_sha,
            "zip_member_count": len(names),
            "indexed_payload_count": len(rows),
            "index_self_exclusion": "artifact-index.json",
            "duplicate_member_count": len(duplicates),
            "unsafe_path_count": len(unsafe),
            "crc_failure": crc_failure,
            "unindexed_payload_count": len(missing_index),
            "unexpected_index_row_count": len(unexpected_index),
            "hash_mismatch_count": len(hash_mismatches),
            "size_mismatch_count": len(size_mismatches),
            "checks": checks,
            "status": "PASS",
        }


def _terminal_capacity_diagnostic_count(stderr: str) -> int:
    lines = [line.rstrip() for line in stderr.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    count = 0
    while lines and lines[-1] == CAPACITY_DIAGNOSTIC:
        count += 1
        lines.pop()
    return count


def classify_transport_failure(
    receipt: Mapping[str, object] | None,
    stderr: str,
    *,
    pre_spawn_guard_failure: bool = False,
) -> dict[str, object]:
    if pre_spawn_guard_failure:
        return {
            "failure_category": "PRE_SPAWN_GUARD_FAILURE",
            "failure_lifecycle": "PRE_SPAWN",
            "transport_receipt_expected": False,
            "status": "CLASSIFIED",
        }
    if receipt is None:
        return {
            "failure_category": "MISSING_TRANSPORT_RECEIPT",
            "failure_lifecycle": "UNKNOWN",
            "transport_receipt_expected": True,
            "status": "UNCLASSIFIED",
        }
    termination = str(receipt.get("termination_initiator") or "NONE")
    elapsed = receipt.get("elapsed_to_exit_seconds")
    configured = receipt.get("configured_timeout_seconds")
    timeout = termination not in {"", "NONE"} and "WATCHDOG" in termination.upper()
    if isinstance(elapsed, (int, float)) and isinstance(configured, (int, float)):
        timeout = timeout or elapsed >= configured
    capacity_count = _terminal_capacity_diagnostic_count(stderr)
    base = {
        "original_status": receipt.get("status"),
        "original_exit_code": receipt.get("exit_code"),
        "original_parse_error": receipt.get("parse_error"),
        "termination_initiator": termination,
        "termination_signal": receipt.get("termination_signal"),
        "configured_timeout_seconds": configured,
        "elapsed_to_exit_seconds": elapsed,
        "stdout_bytes": receipt.get("stdout_bytes"),
        "output_bytes": receipt.get("output_bytes"),
        "output_parsed": receipt.get("output_parsed"),
        "request_accepted_observability": receipt.get("request_accepted_observability"),
        "terminal_capacity_diagnostic_count": capacity_count,
        "watchdog_termination": timeout,
        "transport_receipt_expected": True,
    }
    if timeout:
        return {
            **base,
            "failure_category": "WATCHDOG_TIMEOUT",
            "failure_lifecycle": "POST_SPAWN_TIMEOUT_FAILURE",
            "status": "CLASSIFIED",
        }
    if capacity_count and receipt.get("exit_code") not in {None, 0}:
        return {
            **base,
            "failure_category": "CLI_REPORTED_MODEL_CAPACITY_FAILURE",
            "failure_lifecycle": "POST_SPAWN_NON_TIMEOUT_FAILURE",
            "diagnostic": CAPACITY_DIAGNOSTIC.removeprefix("ERROR: "),
            "status": "CLASSIFIED",
        }
    if receipt.get("exit_code") not in {None, 0}:
        return {
            **base,
            "failure_category": "GENERIC_POST_SPAWN_NONZERO_EXIT",
            "failure_lifecycle": "POST_SPAWN_NON_TIMEOUT_FAILURE",
            "status": "CLASSIFIED",
        }
    if receipt.get("parse_error") == "OUTPUT_FILE_MISSING" or not receipt.get(
        "output_parsed"
    ):
        return {
            **base,
            "failure_category": "OUTPUT_MISSING_WITHOUT_PRIMARY_DIAGNOSTIC",
            "failure_lifecycle": "POST_SPAWN_OUTPUT_OBSERVABILITY_FAILURE",
            "status": "CLASSIFIED",
        }
    return {
        **base,
        "failure_category": "NO_FAILURE_OBSERVED",
        "failure_lifecycle": "TERMINAL_SUCCESS",
        "status": "NOT_APPLICABLE",
    }


def classify_schedule_pause_action(
    *,
    enabled: bool,
    loaded: bool,
    running: bool,
    out_of_scope_dependency: bool = False,
) -> str:
    if out_of_scope_dependency:
        return "BLOCKED_OUT_OF_SCOPE_DEPENDENCY"
    if running:
        return "BLOCKED_ACTIVE_RUN"
    if not enabled and not loaded:
        return "ALREADY_PAUSED"
    return "PAUSED_BY_TASK"


def _context_prefixes(archive: zipfile.ZipFile) -> list[str]:
    suffix = "/transport_receipt.json"
    return sorted(
        name[: -len(suffix)]
        for name in archive.namelist()
        if name.startswith("experiment/model-contexts/FIRST/") and name.endswith(suffix)
    )


def reconcile_partial_execution(archive: zipfile.ZipFile) -> dict[str, object]:
    contexts = []
    stage_attempts: Counter[str] = Counter()
    stage_successes: Counter[str] = Counter()
    stage_rows: Counter[str] = Counter()
    exposed: set[str] = set()
    for prefix in _context_prefixes(archive):
        receipt = zip_json(archive, f"{prefix}/transport_receipt.json")
        manifest = zip_json(archive, f"{prefix}/context_manifest.json")
        stage = str(receipt.get("stage") or manifest.get("stage") or "UNKNOWN")
        stage_attempts[stage] += 1
        output_member = f"{prefix}/output.raw.json"
        usable = output_member in archive.namelist() and len(archive.read(output_member)) > 0
        row_count = 0
        output_tickers: list[str] = []
        if usable:
            output = zip_json(archive, output_member)
            candidates = output.get("candidates")
            if isinstance(candidates, list):
                row_count = len(candidates)
                output_tickers = [
                    str(row.get("ticker"))
                    for row in candidates
                    if isinstance(row, Mapping) and row.get("ticker")
                ]
            stage_successes[stage] += 1
            stage_rows[stage] += row_count
            exposed.update(output_tickers)
        artifacts = []
        for filename in PRESERVED_CONTEXT_FILES:
            member = f"{prefix}/{filename}"
            if member in archive.namelist():
                payload = archive.read(member)
                artifacts.append(
                    {
                        "member": member,
                        "sha256": bytes_sha256(payload),
                        "byte_size": len(payload),
                    }
                )
        contexts.append(
            {
                "prefix": prefix,
                "invocation_id": receipt.get("invocation_id"),
                "stage": stage,
                "batch": receipt.get("batch_id"),
                "receipt_status": receipt.get("status"),
                "subjects": manifest.get("subjects"),
                "usable_output": usable,
                "output_row_count": row_count,
                "output_tickers": output_tickers,
                "artifacts": artifacts,
            }
        )
    result = {
        "contract": "partial-first-execution-reconciliation-v1",
        "first_attempt_count": 1,
        "first_completed_run_count": 0,
        "first_status": "FAILED",
        "attempted_context_count": len(contexts),
        "terminal_context_count": len(contexts),
        "usable_output_context_count": sum(row["usable_output"] for row in contexts),
        "failed_context_count": sum(not row["usable_output"] for row in contexts),
        "per_stage": {
            stage: {
                "attempted_context_count": stage_attempts[stage],
                "successful_context_count": stage_successes[stage],
                "output_subject_count": stage_rows[stage],
            }
            for stage in sorted(stage_attempts)
        },
        "raw_stage_row_count": sum(stage_rows.values()),
        "unique_exposed_issuer_count": len(exposed),
        "unique_exposed_issuers": sorted(exposed),
        "contexts": contexts,
        "status": "PASS",
    }
    expected = {
        "attempted_context_count": 7,
        "usable_output_context_count": 6,
        "failed_context_count": 1,
        "raw_stage_row_count": 24,
        "unique_exposed_issuer_count": 16,
    }
    for key, value in expected.items():
        if result[key] != value:
            raise ValueError(f"partial_execution_count_mismatch:{key}")
    if result["per_stage"] != {
        "DIRECTIONAL_CORE": {
            "attempted_context_count": 4,
            "successful_context_count": 4,
            "output_subject_count": 16,
        },
        "PRICE_TIMING": {
            "attempted_context_count": 3,
            "successful_context_count": 2,
            "output_subject_count": 8,
        },
    }:
        raise ValueError("partial_execution_stage_counts_mismatch")
    return result


def _copy_archive_member(
    archive: zipfile.ZipFile, member: str, destination_root: Path
) -> dict[str, object]:
    payload = archive.read(member)
    destination = destination_root / member
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return {
        "source_member": member,
        "destination": str(destination.relative_to(destination_root)),
        "sha256": bytes_sha256(payload),
        "byte_size": len(payload),
        "provenance": "ORIGINAL_HISTORICAL_RAW_BYTES",
    }


def preserve_historical_evidence(
    archive: zipfile.ZipFile, destination_root: Path
) -> dict[str, object]:
    rows = []
    for prefix in _context_prefixes(archive):
        for filename in PRESERVED_CONTEXT_FILES:
            member = f"{prefix}/{filename}"
            if member in archive.namelist():
                rows.append(_copy_archive_member(archive, member, destination_root))
    for member in AUTHORITY_MEMBERS:
        rows.append(_copy_archive_member(archive, member, destination_root))
    return {
        "contract": "preserved-partial-context-manifest-v1",
        "source_zip_sha256": HISTORICAL_ZIP_SHA256,
        "artifact_count": len(rows),
        "rows": rows,
        "status": "PASS",
    }


def _extract_offline_inputs(archive: zipfile.ZipFile, root: Path) -> Path:
    experiment = root / "experiment"
    prefixes = (
        "experiment/base-contexts/",
        "experiment/packets/",
        "experiment/model-contexts/FIRST/",
    )
    singles = {"experiment/program-state.json", "experiment/source-lock.json"}
    for member in archive.namelist():
        if member in singles or member.startswith(prefixes):
            target = root / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    return experiment


def _code_identity(repo_root: Path) -> dict[str, str]:
    paths = (
        "app/services/direction_timing_ownership_service.py",
        "app/services/structured_autonomy_shadow_service.py",
        "scripts/new_issuer_holdout_selection_ownership_proof.py",
    )
    return {path: file_sha256(repo_root / path) for path in paths}


def run_offline_partial_audit(
    archive: zipfile.ZipFile,
    *,
    destination_root: Path,
    repo_root: Path,
    reconstructed_at: str,
) -> tuple[dict[str, object], dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="thesis-closeout-") as temporary:
        experiment = _extract_offline_inputs(archive, Path(temporary))
        args = SimpleNamespace(output_root=experiment)
        (
            state,
            cohort,
            _packets,
            base_contexts,
            evidence,
            owned,
            core_aliases,
            timing_aliases,
            price_maps,
            stocks,
        ) = proof_runner.load_inputs(args)
        if tuple(cohort) != COHORT:
            raise ValueError("offline_cohort_mismatch")
        architecture_match = (
            proof_runner.architecture_hashes(repo_root) == state["architecture_hashes"]
        )
        transport_match = proof_runner.transport_topology_hashes() == state[
            "transport_topology_hashes"
        ]
        if not architecture_match or not transport_match:
            raise ValueError("frozen_code_identity_mismatch")
        core_by_ticker: dict[str, DirectionalCoreCandidate] = {}
        core_contexts = []
        timing_contexts = []
        reconstructed_rows: list[dict[str, object]] = []
        code_identity = _code_identity(repo_root)
        for number, batch in enumerate(frozen.batches(cohort), start=1):
            context = (
                experiment
                / "model-contexts"
                / "FIRST"
                / "DIRECTIONAL_CORE"
                / f"batch-{number:02d}"
            )
            raw = read_json(context / "output.raw.json")
            binding = runtime_identity.load_binding(context / "identity-binding-lock.json")
            identity = runtime_identity.validate_output_identity(raw, binding)
            rows, alias_audit = frozen._resolve_batch_candidates(
                raw.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=core_aliases,
                model_type=DirectionalCoreCandidate,
            )
            audit = proof_runner.core_partial_audit(rows, owned)
            historical_audit = read_json(context / "partial_semantic_audit.json")
            normalized = read_json(context / "output.normalized.json")
            normalized_rows = normalized.get("candidates")
            rebuilt_rows = [row.model_dump(mode="json") for row in rows]
            row = {
                "batch": number,
                "subjects": list(batch),
                "checked_subject_count": len(rows),
                "identity_status": identity.get("status"),
                "alias_audit_status": "PASS",
                "resolved_alias_subject_count": len(alias_audit),
                "semantic_status": audit.get("status"),
                "historical_audit_exact_match": audit == historical_audit,
                "normalized_output_exact_match": rebuilt_rows == normalized_rows,
                "raw_output_sha256": file_sha256(context / "output.raw.json"),
                "method": "INDEPENDENT_OFFLINE_REVALIDATION",
            }
            core_contexts.append(row)
            for candidate in rows:
                core_by_ticker[candidate.ticker] = candidate
        for number, batch in enumerate(frozen.batches(cohort), start=1):
            context = (
                experiment
                / "model-contexts"
                / "FIRST"
                / "PRICE_TIMING"
                / f"batch-{number:02d}"
            )
            raw_path = context / "output.raw.json"
            if not raw_path.is_file():
                continue
            raw = read_json(raw_path)
            binding = runtime_identity.load_binding(context / "identity-binding-lock.json")
            identity = runtime_identity.validate_output_identity(raw, binding)
            rows, alias_audit = frozen._resolve_batch_candidates(
                raw.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=timing_aliases,
                model_type=PriceTimingCandidate,
            )
            audit, context_rows = proof_runner.timing_partial_audit(
                rows=rows,
                core_by_ticker=core_by_ticker,
                owned=owned,
                evidence=evidence,
                price_maps=price_maps,
                stocks=stocks,
                base_contexts=base_contexts,
            )
            historical_audit = read_json(context / "partial_semantic_audit.json")
            normalized = read_json(context / "output.normalized.json")
            rebuilt_rows = [row.model_dump(mode="json") for row in rows]
            timing_contexts.append(
                {
                    "batch": number,
                    "subjects": list(batch),
                    "checked_subject_count": len(rows),
                    "identity_status": identity.get("status"),
                    "alias_audit_status": "PASS",
                    "resolved_alias_subject_count": len(alias_audit),
                    "semantic_status": audit.get("status"),
                    "historical_audit_exact_match": audit == historical_audit,
                    "normalized_output_exact_match": rebuilt_rows
                    == normalized.get("candidates"),
                    "raw_output_sha256": file_sha256(raw_path),
                    "method": "INDEPENDENT_OFFLINE_REVALIDATION",
                }
            )
            derivative = {
                "contract": "offline-composer-renderer-derivative-v1",
                "provenance": "OFFLINE_RECONSTRUCTED",
                "historical_raw_output": False,
                "model_invocation_count": 0,
                "reconstructed_at": reconstructed_at,
                "batch": number,
                "subjects": list(batch),
                "code_identity": code_identity,
                "input_hashes": {
                    "core_outputs": {
                        ticker: file_sha256(
                            experiment
                            / "model-contexts"
                            / "FIRST"
                            / "DIRECTIONAL_CORE"
                            / f"batch-{(cohort.index(ticker) // 4) + 1:02d}"
                            / "output.raw.json"
                        )
                        for ticker in batch
                    },
                    "timing_output": file_sha256(raw_path),
                    "source_lock": file_sha256(experiment / "source-lock.json"),
                    "packets": {
                        ticker: file_sha256(experiment / "packets" / f"{ticker}.json")
                        for ticker in batch
                    },
                    "base_contexts": {
                        ticker: file_sha256(
                            experiment / "base-contexts" / f"{ticker}.txt"
                        )
                        for ticker in batch
                    },
                },
                "rows": context_rows,
                "validator_status": audit.get("status"),
            }
            derivative_path = (
                destination_root
                / "offline-derivatives"
                / "PRICE_TIMING"
                / f"batch-{number:02d}.json"
            )
            write_json(derivative_path, derivative)
            reconstructed_rows.extend(context_rows)
        reconstructed_rows.sort(key=lambda row: cohort.index(str(row["ticker"])))
        ownership, renderer, hard = proof_runner.run_gate_documents(
            "first_partial_offline", reconstructed_rows
        )
    core_pass = (
        len(core_contexts) == 4
        and sum(row["checked_subject_count"] for row in core_contexts) == 16
        and all(
            row["identity_status"] == "PASS"
            and row["alias_audit_status"] == "PASS"
            and row["semantic_status"] == "PASS"
            and row["historical_audit_exact_match"]
            and row["normalized_output_exact_match"]
            for row in core_contexts
        )
    )
    timing_pass = (
        len(timing_contexts) == 2
        and sum(row["checked_subject_count"] for row in timing_contexts) == 8
        and all(
            row["identity_status"] == "PASS"
            and row["alias_audit_status"] == "PASS"
            and row["semantic_status"] == "PASS"
            and row["historical_audit_exact_match"]
            and row["normalized_output_exact_match"]
            for row in timing_contexts
        )
    )
    renderer_pass = (
        len(reconstructed_rows) == 8
        and ownership.get("status") == "PASS"
        and renderer.get("status") == "PASS"
        and hard.get("status") == "PASS"
    )
    audit_result = {
        "contract": "offline-core16-timing8-partial-audit-v1",
        "source_generation_id": SOURCE_GENERATION_ID,
        "runtime_generation_id": RUNTIME_GENERATION_ID,
        "architecture_semantic_freeze_match": architecture_match,
        "transport_topology_freeze_match": transport_match,
        "core": {
            "applicable_subject_count": 16,
            "checked_subject_count": 16,
            "contexts": core_contexts,
            "status": "PASS" if core_pass else "FAIL",
        },
        "timing": {
            "applicable_subject_count": 8,
            "checked_subject_count": 8,
            "contexts": timing_contexts,
            "status": "PASS" if timing_pass else "FAIL",
        },
        "unproduced_timing_subject_count": 8,
        "unproduced_timing_status": "NOT_MEASURED",
        "whole_run_semantic_gate_status": "NOT_MEASURED",
        "whole_run_renderer_gate_status": "NOT_MEASURED",
        "whole_run_hard_safety_status": "NOT_MEASURED",
        "offline_audit_result": (
            "PASS_PARTIAL_SCOPE" if core_pass and timing_pass and renderer_pass else "FAIL"
        ),
        "status": "PASS" if core_pass and timing_pass and renderer_pass else "FAIL",
    }
    renderer_result = {
        "contract": "offline-composer-renderer-recovery-v1",
        "provenance": "OFFLINE_RECONSTRUCTED",
        "historical_raw_output": False,
        "model_invocation_count": 0,
        "applicable_subject_count": 8,
        "checked_subject_count": len(reconstructed_rows),
        "derivative_paths": [
            "offline-derivatives/PRICE_TIMING/batch-01.json",
            "offline-derivatives/PRICE_TIMING/batch-02.json",
        ],
        "ownership_gate": ownership,
        "renderer_gate": renderer,
        "hard_safety_gate": hard,
        "status": "PASS_PARTIAL_SCOPE" if renderer_pass else "FAIL",
    }
    if audit_result["status"] != "PASS":
        failed_contexts = [
            {
                "stage": stage,
                "batch": row["batch"],
                "identity": row["identity_status"],
                "alias": row["alias_audit_status"],
                "semantic": row["semantic_status"],
                "historical_match": row["historical_audit_exact_match"],
                "normalized_match": row["normalized_output_exact_match"],
            }
            for stage, contexts in (
                ("DIRECTIONAL_CORE", core_contexts),
                ("PRICE_TIMING", timing_contexts),
            )
            for row in contexts
            if not (
                row["identity_status"] == "PASS"
                and row["alias_audit_status"] == "PASS"
                and row["semantic_status"] == "PASS"
                and row["historical_audit_exact_match"]
                and row["normalized_output_exact_match"]
            )
        ]
        raise ValueError(
            "offline_partial_audit_failed:"
            f"core={core_pass}:timing={timing_pass}:renderer={renderer_pass}:"
            f"ownership={ownership.get('status')}:"
            f"renderer_gate={renderer.get('status')}:hard={hard.get('status')}:"
            f"contexts={json.dumps(failed_contexts, sort_keys=True)}"
        )
    return audit_result, renderer_result


def _parse_live_automation(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def _launchd_disabled(label: str) -> bool:
    uid = subprocess.run(
        ("id", "-u"), check=True, capture_output=True, text=True
    ).stdout.strip()
    output = subprocess.run(
        ("launchctl", "print-disabled", f"gui/{uid}"),
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    pattern = rf'"{re.escape(label)}"\s*=>\s*disabled'
    return re.search(pattern, output) is not None


def _launchd_loaded(label: str) -> bool:
    uid = subprocess.run(
        ("id", "-u"), check=True, capture_output=True, text=True
    ).stdout.strip()
    result = subprocess.run(
        ("launchctl", "print", f"gui/{uid}/{label}"),
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def validate_schedule_observation(
    observation: Mapping[str, object], *, repo_root: Path
) -> dict[str, object]:
    rows = observation.get("objects")
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("six_changed_scheduler_objects_required")
    backup_root = (
        repo_root
        / "artifacts"
        / "20260907-scheduled-monitoring-pause-closeout"
        / "scheduler-backup"
    )
    automation_files = {
        "thesis-monitor-ai-review-us-primary": "us-primary.automation.toml",
        "thesis-monitor-ai-review-us-backup": "us-backup.automation.toml",
        "thesis-monitor-ai-review-kr-primary": "kr-primary.automation.toml",
        "thesis-monitor-ai-review-kr-backup": "kr-backup.automation.toml",
    }
    live_root = Path.home() / ".codex" / "automations"
    verification = []
    for identifier, backup_name in automation_files.items():
        backup_path = backup_root / backup_name
        live_path = live_root / identifier / "automation.toml"
        before = _parse_live_automation(backup_path)
        after = _parse_live_automation(live_path)
        expected = dict(before)
        expected["status"] = "PAUSED"
        exact_status_only = expected == after
        verification.append(
            {
                "id": identifier,
                "before_status": before.get("status"),
                "after_status": after.get("status"),
                "status_only_change": exact_status_only,
                "before_sha256": file_sha256(backup_path),
                "after_sha256": file_sha256(live_path),
            }
        )
    launchd = []
    for label in (
        "com.seungsoo.thesis-monitor.daily",
        "com.seungsoo.thesis-monitor.kr-close",
    ):
        launchd.append(
            {
                "id": label,
                "disabled": _launchd_disabled(label),
                "loaded": _launchd_loaded(label),
            }
        )
    if not all(row["status_only_change"] for row in verification):
        raise ValueError("codex_automation_nonstatus_drift")
    if not all(row["disabled"] for row in launchd):
        raise ValueError("launchd_pause_not_persisted")
    if any(row["loaded"] for row in launchd):
        raise ValueError("launchd_calendar_job_still_loaded")
    return {
        "contract": "authorized-schedule-pause-verification-v1",
        "requested_logical_schedule_count": 2,
        "changed_scheduler_object_count": 6,
        "codex_automations": verification,
        "launchd_agents": launchd,
        "us_pause_status": observation["pause_result"]["us"],
        "kr_pause_status": observation["pause_result"]["kr"],
        "pause_dependency_blockers": [observation["pause_result"]["kr_blocker"]],
        "forced_termination_count": 0,
        "auto_resume_configured": False,
        "status": "PARTIAL_OPERATIONAL_COMPLETION",
    }


def production_pause_accounting(observation: Mapping[str, object]) -> dict[str, object]:
    result = observation["pause_result"]
    transition = observation["pause_transition_observation"]
    return {
        "authorized_schedule_pause_requested": True,
        "authorized_logical_schedule_count": 2,
        "scheduler_mutation_performed": True,
        "scheduler_objects_changed_count": result["scheduler_objects_changed_count"],
        "authorized_schedule_change_count": result["authorized_schedule_change_count"],
        "unauthorized_schedule_change_count": result[
            "unauthorized_schedule_change_count"
        ],
        "production_scheduler_change": True,
        "production_scheduler_change_count": result[
            "scheduler_objects_changed_count"
        ],
        "authorized_scheduler_storage_mutation": True,
        "investment_state_db_mutation": 0,
        "investment_state_db_mutation_scope": "TASK_INITIATED_MANUAL_MUTATION_ONLY",
        "pause_transition_scheduled_invocation_count": transition[
            "scheduled_invocation_count"
        ],
        "pause_transition_database_write_scope": transition["database_write_scope"],
        "production_telegram_send_initiated_by_task": 0,
        "monitoring_registration_calls": 0,
        "forced_termination_count": 0,
        "auto_resume_configured": False,
    }


def exposure_overlay(archive: zipfile.ZipFile) -> dict[str, object]:
    prior = zip_json(
        archive, "reports/proofs/03-prior-real-issuer-exposure-registry.json"
    )
    identities = zip_json(archive, "reports/proofs/18-source-identity-audit.json")
    rows = []
    for row in identities.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        ticker = str(row["ticker"])
        rows.append(
            {
                "ticker": ticker,
                "market": row.get("market"),
                "canonical_issuer_key": row.get("canonical_issuer_key"),
                "security_aliases": [ticker],
                "actual_output_exposure": True,
                "core_stage_output": True,
                "timing_stage_output": ticker in COHORT[:8],
                "exclusion_reasons": [
                    "ACTUAL_REAL_MODEL_OUTPUT_EXPOSURE",
                    "INCOMPLETE_FIRST_AFTER_FULL_ISSUER_EXPOSURE",
                ],
            }
        )
    if len(rows) != len(COHORT):
        raise ValueError("exposure_identity_count_mismatch")
    return {
        "contract": "exposure-retirement-exclusion-overlay-v1",
        "prior_registry_count": prior.get("registry_count"),
        "prior_registry_sha256": prior.get("registry_sha256"),
        "appended_exposed_issuer_count": len(rows),
        "reconciled_registry_count": int(prior.get("registry_count") or 0) + len(rows),
        "exclusion_shrink_count": 0,
        "rows": rows,
        "holdout_output_exposure_state": "FULLY_EXPOSED",
        "historical_retirement_state": "RETIRED_PARTIAL_EXPOSURE",
        "explicit_retirement_reason": "INCOMPLETE_FIRST_AFTER_FULL_ISSUER_EXPOSURE",
        "issuer_exposure": "16/16",
        "core_stage_coverage": "16/16",
        "timing_stage_coverage": "8/16",
        "complete_run_coverage": 0,
        "future_unseen_holdout_reuse_allowed": 0,
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "status": "PASS",
    }


def _failure_reconciliation(
    archive: zipfile.ZipFile, partial: Mapping[str, object]
) -> dict[str, object]:
    report27 = zip_json(archive, "reports/proofs/27-first-execution-summary.json")
    report60 = zip_json(archive, "reports/proofs/60-program-completion.json")
    report61 = zip_json(
        archive,
        "reports/proofs/61-existing-data-routes-final-freeze-ownership-proof-"
        "completion.json",
    )
    return {
        "contract": "failure-path-report-overlay-v1",
        "original_claims_preserved": True,
        "original_first_report_values": {
            "report27_status": report27.get("status"),
            "report27_completed_context_count": report27.get("completed_context_count"),
            "report60_run_results_first": (report60.get("run_results") or {}).get("first"),
            "report60_first_complete_run_attempt_count": report60.get(
                "first_complete_run_attempt_count"
            ),
            "report60_artifact_count": report60.get("artifact_count"),
            "report61_first_status": (report61.get("run_gates") or {})
            .get("first", {})
            .get("status"),
        },
        "reconciled": {
            "FIRST_attempt_count": partial["first_attempt_count"],
            "FIRST_completed_run_count": partial["first_completed_run_count"],
            "FIRST_status": partial["first_status"],
            "attempted_context_count": partial["attempted_context_count"],
            "terminal_context_count": partial["terminal_context_count"],
            "usable_output_context_count": partial["usable_output_context_count"],
            "failed_context_count": partial["failed_context_count"],
            "per_stage": partial["per_stage"],
            "raw_stage_row_count": partial["raw_stage_row_count"],
            "unique_exposed_issuer_count": partial["unique_exposed_issuer_count"],
            "whole_run_semantic_gate_status": "NOT_MEASURED",
            "whole_run_renderer_gate_status": "NOT_MEASURED",
            "whole_run_hard_safety_status": "NOT_MEASURED",
            "valid_repeated_run_count": 0,
            "stability_status": "NOT_MEASURED",
            "ownership_generalization_verdict": "NOT_ESTABLISHED",
        },
        "historical_artifact_count_overlay": {
            "zip_member_count": 912,
            "indexed_payload_count": 911,
            "hash_mismatch_count": 0,
            "size_mismatch_count": 0,
        },
        "status": "PASS",
    }


def _report_markdown(proofs: Mapping[str, Mapping[str, object]]) -> str:
    completion = proofs[REPORT_NAMES[-1]]
    failure = proofs[REPORT_NAMES[4]]
    offline = proofs[REPORT_NAMES[6]]
    schedule = proofs[REPORT_NAMES[2]]
    return f"""# Scheduled Monitoring Pause + Capacity Failure Partial-Proof Closeout

## Result

This bounded closeout completed without a new model call. The historical FIRST remains
`FAILED`; ownership generalization remains `NOT_ESTABLISHED`.

## Schedule pause

- US: `{schedule['us_pause_status']}`
- KR: `{schedule['kr_pause_status']}`
- Changed scheduler objects: `{schedule['changed_scheduler_object_count']}`
- Forced terminations: `0`
- Auto-resume: `0`
- Pause-transition race: the already-loaded KR calendar job invoked once at `16:20`,
  completed before final verification, and was then unloaded without forced termination.
- KR dependency: the already-held KR9 packet can still reach the unchanged shared 17:10
  fallback because no per-market pause control exists.

## Historical failure

- Invocation: `{failure['failed_invocation_id']}`
- Category: `{failure['failure_category']}`
- Lifecycle: `{failure['failure_lifecycle']}`
- Exit / elapsed / timeout: `1 / 382.087626 / 1800`
- Watchdog termination: `false`
- Explicit-run retry count: `0`; internal retry observability: `UNKNOWN`
- Current model capacity: `NOT_CHECKED`

`OUTPUT_FILE_MISSING` is retained as a downstream observation. It is not used as the primary
cause because the terminal CLI diagnostic explicitly reports model capacity.

## Preserved partial proof

- Real invocations: `7`; successful output contexts: `6`; failed contexts: `1`
- Directional Core: `4/4` contexts, `16/16` subjects
- Price Timing: `2/3` contexts, `8/16` subjects
- Raw stage rows: `24`; uniquely exposed issuers: `16`
- Offline audit: `{offline['offline_audit_result']}`
- Full-run semantic, renderer and hard-safety gates: `NOT_MEASURED`
- Repeated stability: `NOT_MEASURED`

The eight available Timing rows were recomposed and rendered deterministically with the frozen
code and exact archived inputs. Those artifacts are labeled `OFFLINE_RECONSTRUCTED`; they are
not represented as historical raw model output and were not delivered.

## Production accounting

- New real or fictional model calls: `0 / 0`
- Task-initiated manual investment-state DB mutation: `0`
- Pause-transition KR invocation DB-write scope: `UNKNOWN_WITHIN_EXISTING_SAME_DAY_RUN`
- Telegram send initiated by this task: `0`
- Monitoring registration: `0`
- Main merge, deployment, live V2 and Night Futures change: `0`
- Authorized scheduler objects changed: `6`; unauthorized changes: `0`

## Final decision

- Closeout readiness: `{completion['readiness']}`
- Ownership proof: `NOT_ESTABLISHED`
- Retired cohort reuse: `0`
- Next scope: `{completion['next_scope']}`
"""


def build_reports(
    *,
    archive: zipfile.ZipFile,
    archive_integrity: Mapping[str, object],
    schedule_observation: Mapping[str, object],
    schedule_verification: Mapping[str, object],
    partial: Mapping[str, object],
    preserved: Mapping[str, object],
    offline: Mapping[str, object],
    renderer: Mapping[str, object],
    exposure: Mapping[str, object],
    validation: Mapping[str, object],
    repo_root: Path,
    as_of: str,
) -> dict[str, dict[str, object]]:
    failed_prefix = "experiment/model-contexts/FIRST/PRICE_TIMING/batch-03"
    receipt = zip_json(archive, f"{failed_prefix}/transport_receipt.json")
    stderr = archive.read(f"{failed_prefix}/stderr.raw.log").decode("utf-8")
    failure = classify_transport_failure(receipt, stderr)
    if failure["failure_category"] != "CLI_REPORTED_MODEL_CAPACITY_FAILURE":
        raise ValueError("capacity_failure_classification_mismatch")
    failure.update(
        {
            "contract": "capacity-error-lifecycle-classification-v1",
            "failed_invocation_id": FAILED_INVOCATION_ID,
            "failure_stage": "PRICE_TIMING",
            "failure_batch": "03",
            "original_cli_error": CAPACITY_DIAGNOSTIC.removeprefix("ERROR: "),
            "stderr_sha256": bytes_sha256(stderr.encode("utf-8")),
            "explicit_run_retry_count": 0,
            "internal_retry_observability": "UNKNOWN",
            "current_model_capacity_status": "NOT_CHECKED",
            "historical_stall_pattern_recurred": 0,
            "output_file_missing_role": "DOWNSTREAM_OBSERVATION_NOT_PRIMARY_CAUSE",
        }
    )
    accounting = production_pause_accounting(schedule_observation)
    reconciliation = _failure_reconciliation(archive, partial)
    repository = {
        "branch": git_value("branch", "--show-current"),
        "head": git_value("rev-parse", "HEAD"),
        "status_short": git_value("status", "--short"),
        "base_sha": "5e98621bf5531f6da960ac7a47413f53f0fbe344",
        "historical_base_sha": "8dcf12fc3d4b3bac2a6e62679feb9e05d222ea1e",
        "historical_work_instruction_commit": (
            "1efa69a43ce1130bc7439c03fb4f87a36b42473f"
        ),
        "historical_implementation_commit": (
            "d0433edaa0d8f929b0ebb390c478e4d64f4834d0"
        ),
        "closeout_work_instruction_commit": (
            "309cd95959d184461a02078aa0c5b2c388d65f0a"
        ),
    }
    repository["implementation_commit"] = repository["head"]
    repository["final_head_sha"] = repository["head"]
    if repository["status_short"]:
        raise ValueError("clean_repository_required_for_final_report")
    proofs: dict[str, dict[str, object]] = {
        REPORT_NAMES[0]: {
            **archive_integrity,
            "repository": repository,
            "as_of": as_of,
        },
        REPORT_NAMES[1]: {
            "contract": "schedule-identity-before-state-v1",
            "before_observed_at": schedule_observation["before_observed_at"],
            "objects": schedule_observation["objects"],
            "shared_jobs_inspected_not_changed": schedule_observation[
                "shared_jobs_inspected_not_changed"
            ],
            "last_successful_monitor_runs": schedule_observation[
                "last_successful_monitor_runs"
            ],
            "same_day_delivery_state_at_pause": schedule_observation[
                "same_day_delivery_state_at_pause"
            ],
            "status": "PASS",
        },
        REPORT_NAMES[2]: dict(schedule_verification),
        REPORT_NAMES[3]: {
            "contract": "schedule-restoration-reference-v1",
            "auto_resume_configured": False,
            "restore_executed": False,
            "restoration_requires_new_explicit_user_instruction": True,
            "scheduler_backup_location": "evidence/scheduler-backup/",
            "launchd_restore_reference": [
                (
                    "enable and bootstrap com.seungsoo.thesis-monitor.daily from the "
                    "preserved user LaunchAgent definition"
                ),
                (
                    "enable and bootstrap com.seungsoo.thesis-monitor.kr-close from the "
                    "preserved user LaunchAgent definition"
                ),
            ],
            "codex_restore_reference": [
                "set thesis-monitor-ai-review-us-primary status to ACTIVE",
                "set thesis-monitor-ai-review-us-backup status to ACTIVE",
                "set thesis-monitor-ai-review-kr-primary status to ACTIVE",
                "set thesis-monitor-ai-review-kr-backup status to ACTIVE",
            ],
            "gap_handling": "MISSING_DAILY_EVALUATIONS_ARE_NOT_NO_MATERIAL_CHANGE",
            "status": "PASS",
        },
        REPORT_NAMES[4]: failure,
        REPORT_NAMES[5]: dict(preserved),
        REPORT_NAMES[6]: dict(offline),
        REPORT_NAMES[7]: dict(renderer),
        REPORT_NAMES[8]: reconciliation,
        REPORT_NAMES[9]: {
            "contract": "targeted-tests-bounded-diff-v1",
            **validation,
            "report_only_code_change_count": 2,
            "architecture_semantic_drift": 0,
            "transport_behavior_change": 0,
            "model_change": 0,
            "timeout_increase": 0,
            "batch_split": 0,
            "retry_added": 0,
            "status": "PASS"
            if all(
                validation.get(key) == "PASS"
                for key in ("focused_tests", "full_tests", "ruff", "diff_check")
            )
            else "FAIL",
        },
        REPORT_NAMES[10]: dict(exposure),
        REPORT_NAMES[11]: {
            "contract": "production-change-accounting-v1",
            **accounting,
            "main_merge": 0,
            "production_deployment": 0,
            "live_v2_change": 0,
            "night_futures_change": 0,
            "new_paid_dependency_count": 0,
            "new_free_api_gate_project": 0,
            "provider_or_credential_change": 0,
            "status": "PASS",
        },
    }
    completion = {
        "contract": CONTRACT,
        "as_of": as_of,
        "input_zip_sha256": HISTORICAL_ZIP_SHA256,
        "repository": repository,
        "schedule_pause_requested": True,
        "us_schedule_identity": "US_PRODUCER_PLUS_PRIMARY_BACKUP",
        "kr_schedule_identity": "KR_PRODUCER_PLUS_PRIMARY_BACKUP",
        "us_schedule_before": "ACTIVE",
        "us_schedule_after": "PAUSED",
        "us_pause_status": schedule_verification["us_pause_status"],
        "kr_schedule_before": "ACTIVE_WITH_ALREADY_HELD_KR9",
        "kr_schedule_after": "PRODUCER_AND_AI_AUTOMATIONS_PAUSED_SHARED_FALLBACK_ACTIVE",
        "kr_pause_status": schedule_verification["kr_pause_status"],
        "running_jobs_observed": 0,
        "pause_transition_scheduled_invocation_count": schedule_observation[
            "pause_transition_observation"
        ]["scheduled_invocation_count"],
        "pause_transition_invocation_completed": schedule_observation[
            "pause_transition_observation"
        ]["completed_before_final_verification"],
        "pause_transition_db_write_scope": schedule_observation[
            "pause_transition_observation"
        ]["database_write_scope"],
        "forced_termination_count": 0,
        "auto_resume_configured": False,
        "scheduler_objects_changed_count": 6,
        "authorized_schedule_change_count": 6,
        "unauthorized_schedule_change_count": 0,
        "pause_dependency_blockers": schedule_verification[
            "pause_dependency_blockers"
        ],
        "failure_category": failure["failure_category"],
        "original_cli_error": failure["original_cli_error"],
        "failed_invocation_id": FAILED_INVOCATION_ID,
        "failure_stage": "PRICE_TIMING",
        "failure_batch": "03",
        "exit_code": 1,
        "elapsed_seconds": 382.087626,
        "timeout_seconds": 1800,
        "watchdog_termination": False,
        "explicit_run_retry_count": 0,
        "internal_retry_observability": "UNKNOWN",
        "current_model_capacity_status": "NOT_CHECKED",
        "original_real_invocation_count": 7,
        "new_real_model_invocation_count": 0,
        "new_fictional_model_invocation_count": 0,
        "successful_context_count": 6,
        "failed_context_count": 1,
        "core_output_count": 16,
        "timing_output_count": 8,
        "raw_stage_row_count": 24,
        "unique_exposed_issuer_count": 16,
        "reconciled_FIRST_status": "FAILED",
        "FIRST_attempt_count": 1,
        "FIRST_completed_run_count": 0,
        "per_stage_attempted_and_successful_counts": partial["per_stage"],
        "offline_checked_counts": {"core": 16, "timing": 8, "renderer": 8},
        "offline_partial_invariant_result": offline["offline_audit_result"],
        "renderer_artifact_provenance": "OFFLINE_RECONSTRUCTED",
        "full_run_gates": "NOT_MEASURED",
        "repeated_stability_status": "NOT_MEASURED",
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "holdout_output_exposure_state": "FULLY_EXPOSED",
        "historical_retirement_state": "RETIRED_PARTIAL_EXPOSURE",
        "explicit_retirement_reason": "INCOMPLETE_FIRST_AFTER_FULL_ISSUER_EXPOSURE",
        "future_unseen_holdout_reuse_allowed": 0,
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "report_only_code_change_count": 2,
        "architecture_semantic_drift": 0,
        "transport_behavior_change": 0,
        "model_change": 0,
        "timeout_increase": 0,
        "batch_split": 0,
        "retry_added": 0,
        "investment_state_db_mutation": 0,
        "authorized_scheduler_storage_mutation": True,
        "production_scheduler_change": True,
        "production_scheduler_change_count": 6,
        "production_telegram_send_initiated_by_task": 0,
        "monitoring_registration_calls": 0,
        "main_merge": 0,
        "production_deployment": 0,
        "live_v2_change": 0,
        "night_futures_change": 0,
        "new_paid_dependency_count": 0,
        "new_free_api_gate_project": 0,
        "archive_verification": "PASS",
        "pause_result": "PARTIAL_OPERATIONAL_COMPLETION",
        "offline_audit_result": offline["offline_audit_result"],
        "report_reconciliation_result": "PASS",
        "readiness": "CLOSEOUT_COMPLETE_OWNERSHIP_PROOF_NOT_ESTABLISHED",
        "stop_reason": "CLI_REPORTED_MODEL_CAPACITY_FAILURE_DURING_FIRST_TIMING_03",
        "next_scope": (
            "SEPARATELY_AUTHORIZED_NEW_ISSUER_PROOF_WITH_NEW_COHORT_AND_FRESH_PRECOMMIT"
        ),
        "status": "PASS_CLOSEOUT",
    }
    proofs[REPORT_NAMES[12]] = completion
    return proofs


def _copy_scheduler_backups(repo_root: Path, destination: Path) -> None:
    source = (
        repo_root
        / "artifacts"
        / "20260907-scheduled-monitoring-pause-closeout"
        / "scheduler-backup"
    )
    shutil.copytree(source, destination)


def _finalize_index_and_zip(root: Path, zip_output: Path) -> dict[str, object]:
    payloads = sorted(
        path for path in root.rglob("*") if path.is_file() and path.name != "artifact-index.json"
    )
    rows = []
    secret_failures = 0
    for path in payloads:
        scan = proof_runner.scan_secrets([path])
        secret_failures += int(scan["secret_scan_status"] != "PASS")
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    index = {
        "contract": "scheduled-monitoring-pause-closeout-artifact-index-v1",
        "index_self_exclusion": "artifact-index.json",
        "all_payload_files_except_index_itself_individually_indexed": True,
        "indexed_payload_count": len(rows),
        "zip_member_count": len(rows) + 1,
        "secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": "PASS" if secret_failures == 0 else "FAIL",
    }
    write_json(root / "artifact-index.json", index)
    if secret_failures:
        raise ValueError("closeout_secret_scan_failed")
    zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = zip_output.with_suffix(zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root))
    temporary.replace(zip_output)
    with zipfile.ZipFile(zip_output) as archive:
        bad_member = archive.testzip()
        member_count = len(archive.namelist())
    if bad_member is not None or member_count != len(rows) + 1:
        raise ValueError("closeout_zip_integrity_failed")
    zip_sha = file_sha256(zip_output)
    write_text(zip_output.with_suffix(zip_output.suffix + ".sha256"), zip_sha)
    return {
        "zip_output": str(zip_output),
        "zip_sha256": zip_sha,
        "zip_member_count": member_count,
        "indexed_payload_count": len(rows),
        "secret_scan_failure_count": secret_failures,
        "status": "PASS",
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    repo_root = Path.cwd().resolve()
    if args.output_root.exists():
        raise ValueError(f"fresh_output_root_required:{args.output_root}")
    args.output_root.mkdir(parents=True)
    archive_integrity = verify_historical_archive(args.historical_zip)
    schedule_observation = read_json(args.schedule_observation)
    schedule_verification = validate_schedule_observation(
        schedule_observation, repo_root=repo_root
    )
    validation = read_json(args.validation)
    with zipfile.ZipFile(args.historical_zip) as archive:
        partial = reconcile_partial_execution(archive)
        preserved = preserve_historical_evidence(
            archive, args.output_root / "evidence" / "original-historical"
        )
        offline, renderer = run_offline_partial_audit(
            archive,
            destination_root=args.output_root / "evidence",
            repo_root=repo_root,
            reconstructed_at=args.as_of,
        )
        exposure = exposure_overlay(archive)
        proofs = build_reports(
            archive=archive,
            archive_integrity=archive_integrity,
            schedule_observation=schedule_observation,
            schedule_verification=schedule_verification,
            partial=partial,
            preserved=preserved,
            offline=offline,
            renderer=renderer,
            exposure=exposure,
            validation=validation,
            repo_root=repo_root,
            as_of=args.as_of,
        )
    _copy_scheduler_backups(
        repo_root, args.output_root / "evidence" / "scheduler-backup"
    )
    write_json(
        args.output_root / "evidence" / "schedule-observation.json",
        schedule_observation,
    )
    for name, proof in proofs.items():
        write_json(args.output_root / "reports" / "proofs" / f"{name}.json", proof)
    write_text(
        args.output_root
        / "reports"
        / "20260907-scheduled-monitoring-pause-capacity-failure-partial-proof-closeout.md",
        _report_markdown(proofs),
    )
    completion_path = (
        args.output_root / "reports" / "proofs" / f"{REPORT_NAMES[-1]}.json"
    )
    completion = read_json(completion_path)
    payload_count = sum(
        path.is_file()
        for path in args.output_root.rglob("*")
        if path.name != "artifact-index.json"
    )
    completion["artifact_indexed_payload_count"] = payload_count
    completion["artifact_zip_member_count"] = payload_count + 1
    write_json(completion_path, completion)
    result = _finalize_index_and_zip(args.output_root, args.zip_output)
    result.update(
        {
            "contract": CONTRACT,
            "readiness": completion["readiness"],
            "ownership_generalization_verdict": "NOT_ESTABLISHED",
            "new_model_invocation_count": 0,
            "pause_result": completion["pause_result"],
        }
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-zip", type=Path, required=True)
    parser.add_argument("--schedule-observation", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--zip-output", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    for name in (
        "historical_zip",
        "schedule_observation",
        "validation",
        "output_root",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    datetime.fromisoformat(args.as_of)
    return args


if __name__ == "__main__":
    run(parse_args())
