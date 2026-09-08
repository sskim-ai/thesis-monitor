from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    OwnedEvidencePacket,
    canonical_sha256,
    stage_alias_catalogs,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import runtime_identity_binding as runtime_identity
from scripts import synthetic_canary_fixture_repair_ownership_resume as guarded
from scripts import uskr22_structured_autonomy_shadow as engine
from scripts.websocket_timeout_runtime_review_first_a_closeout import (
    SESSION_ID_RE,
    classify_runtime_receipt,
    extract_runtime_events,
    observe_pause_state,
    validate_json_schema,
)


PROGRAM_CONTRACT = "bounded-fictional-websocket-reconnect-observability-diagnostic-v1"
BASELINE_ZIP_SHA256 = "1ddf30ac6b1420eed68f6e44e7f19ef455ca3e6619588b45be537e1d385612b3"
BASELINE_MEMBER_COUNT = 329
BASELINE_INDEXED_PAYLOAD_COUNT = 328
EXPECTED_CLI_VERSION = "codex-cli 0.148.0-alpha.15"
EXPECTED_CLI_SHA256 = "7645c3caf5607e4528eb3a15b12496c284c2a918939aed34e863c760c1b421e7"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
TIMEOUT_OWNER_COUNT = 1
MAX_CALLS = 3
SUBJECTS = (
    "SYNTHETIC_WS_A",
    "SYNTHETIC_WS_B",
    "SYNTHETIC_WS_C",
    "SYNTHETIC_WS_D",
)
PADDING_BYTES = 2300
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260907-bounded-fictional-websocket-reconnect-observability-diagnostic.md"
)
HISTORICAL_REAL_COHORT = (
    "NU",
    "LNG",
    "TCI",
    "WMG",
    "043100",
    "025000",
    "131030",
    "372910",
    "130740",
    "045340",
    "006910",
    "288980",
    "023440",
    "064820",
    "001440",
    "073490",
)
HISTORICAL_MEMBERS = (
    "completion.json",
    "reports/proofs/02-pause-state-and-historical-transition.json",
    "reports/proofs/04-b-lifecycle-timeline.json",
    "reports/proofs/05-first-a-b-request-session-comparison.json",
    "reports/proofs/06-retry-observability-and-classification.json",
    "reports/proofs/08-exposure-retirement-measurement-mapping.json",
    "reports/proofs/09-offline-first-a-lineage-and-gate-audit.json",
    "reports/proofs/10-first-a-descriptive-differences.json",
    "reports/proofs/11-message-quality-scope-and-original-export.json",
    "reports/proofs/12-program-completion.json",
)
SECRET_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"Bearer[ \t]+[A-Za-z0-9._~+/-]{16,}", re.IGNORECASE),
    re.compile(
        rb"(?:API[_-]?KEY|ACCESS[_-]?TOKEN|PASSWORD|SECRET)"
        rb"[ \t]*[:=][ \t]*[^\s]{8,}",
        re.IGNORECASE,
    ),
    re.compile(rb"\d{8,10}:[A-Za-z0-9_-]{25,}"),
)
REPORT_NAMES = (
    "01-repository-input-pause",
    "02-fixture-precommit-budget",
    "03-observer-preflight-tests",
    "04-per-attempt-results",
    "05-aggregate-lifecycle-session",
    "06-historical-scope-quality",
    "07-production-no-change",
    "08-program-completion",
)


class DiagnosticStop(RuntimeError):
    """Raised when a predeclared diagnostic stop condition is reached."""


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_sha256(value: object) -> str:
    return sha256_bytes(inspect.getsource(value).encode())


def git_value(*args: str) -> str:
    return subprocess.run(("git", *args), check=True, capture_output=True, text=True).stdout.strip()


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def verify_indexed_zip(path: Path) -> dict[str, object]:
    actual_sha = file_sha256(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicate_count = sum(count > 1 for count in Counter(names).values())
        unsafe = [
            name
            for name in names
            if name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts
        ]
        bad_member = archive.testzip()
        index = zip_json(archive, "artifact-index.json")
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("baseline_artifact_index_rows_missing")
        indexed = {
            str(row["path"]): row for row in rows if isinstance(row, Mapping) and row.get("path")
        }
        payload_names = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for name in sorted(payload_names & set(indexed)):
            payload = archive.read(name)
            hash_mismatches += sha256_bytes(payload) != indexed[name].get("sha256")
            size_mismatches += len(payload) != indexed[name].get("byte_size")
        membership_mismatches = len(payload_names ^ set(indexed))
    checks = {
        "zip_sha256": actual_sha == BASELINE_ZIP_SHA256,
        "member_count": len(names) == BASELINE_MEMBER_COUNT,
        "indexed_payload_count": len(rows) == BASELINE_INDEXED_PAYLOAD_COUNT,
        "duplicate_members": duplicate_count == 0,
        "safe_paths": not unsafe,
        "crc": bad_member is None,
        "index_membership": membership_mismatches == 0,
        "hashes": hash_mismatches == 0,
        "sizes": size_mismatches == 0,
    }
    if not all(checks.values()):
        failed = ",".join(key for key, passed in checks.items() if not passed)
        raise ValueError(f"baseline_integrity_failure:{failed}")
    return {
        "contract": "indexed-baseline-integrity-v1",
        "input_zip_sha256": actual_sha,
        "input_member_count": len(names),
        "input_indexed_payload_count": len(rows),
        "duplicate_member_count": duplicate_count,
        "unsafe_path_count": len(unsafe),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "membership_mismatch_count": membership_mismatches,
        "crc_failure": bad_member,
        "checks": checks,
        "status": "PASS",
    }


def scan_bytes(value: bytes) -> int:
    return sum(len(pattern.findall(value)) for pattern in SECRET_PATTERNS)


def scan_path(path: Path) -> int:
    return scan_bytes(path.read_bytes())


def cli_identity() -> dict[str, object]:
    codex_bin = Path(engine._signed_in_codex_bin()).resolve()
    version = transport.cli_version(str(codex_bin))
    identity = {
        "path": str(codex_bin),
        "version": version,
        "sha256": file_sha256(codex_bin),
    }
    identity["checks"] = {
        "version": identity["version"] == EXPECTED_CLI_VERSION,
        "sha256": identity["sha256"] == EXPECTED_CLI_SHA256,
    }
    identity["status"] = "PASS" if all(identity["checks"].values()) else "FAIL"
    return identity


class PausedScheduleProcessObserver:
    """Observe the completed pause plus currently running natural/model processes."""

    NATURAL_JOB_MARKERS = guarded.SandboxCompatibleWorkloadObserver.NATURAL_JOB_MARKERS

    @property
    def backend(self) -> str:
        return "PAUSE_REGISTRY_PLUS_PS_NATURAL_MARKERS_PLUS_LSOF_CODEX_RUNTIME_STATE"

    @property
    def capabilities(self) -> dict[str, object]:
        return {
            "protected_window_observable": True,
            "paused_schedule_registry_observable": True,
            "natural_process_observable": True,
            "model_execution_observable": True,
            "scheduler_mutation": False,
        }

    def _natural_processes(self) -> list[dict[str, object]]:
        result = subprocess.run(
            ("/bin/ps", "-axo", "pid=,command="),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise guarded.LiveWorkloadObservationUnavailable(
                f"natural_process_observation_failed:{result.returncode}"
            )
        rows: list[dict[str, object]] = []
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            pid_text, separator, command = line.partition(" ")
            if not separator or not pid_text.isdigit():
                continue
            matched = [marker for marker in self.NATURAL_JOB_MARKERS if marker in command]
            if matched:
                rows.append({"pid": int(pid_text), "matched_markers": matched})
        return rows

    def observe(self) -> dict[str, object]:
        pause = observe_pause_state()
        if pause.get("status") != "VERIFIED_PAUSED_COMPLETE":
            raise guarded.LiveWorkloadObservationUnavailable(
                f"monitoring_pause_not_verified:{pause.get('status')}"
            )
        natural_rows = self._natural_processes()
        base = guarded.SandboxCompatibleWorkloadObserver()
        model_count, model_pids = base._model_executions()
        return {
            "workload_observation_backend": self.backend,
            "observation_capabilities": self.capabilities,
            "paused_schedule_count": pause["observed_scheduler_object_count"],
            "pause_observed_at": pause["observed_at"],
            "unexpected_active_monitoring_paths": pause["unexpected_active_paths"],
            "active_natural_job_count": len(natural_rows),
            "running_model_process_count": model_count,
            "natural_job_rows": natural_rows,
            "model_execution_pids": model_pids,
        }


class SingleObservationWorkloadGuard(guarded.LiveWorkloadGuard):
    """Use one fail-closed observation per call and never poll or sleep."""

    def __init__(self, audit_path: Path, *, observer: object | None = None) -> None:
        super().__init__(audit_path, observer=observer or PausedScheduleProcessObserver())
        self._approved: set[tuple[str, str, int]] = set()

    def preflight(self, *, stage: str, batch_id: str, subject_count: int) -> dict[str, object]:
        result = super().preflight(stage=stage, batch_id=batch_id, subject_count=subject_count)
        if result["status"] == "PASS":
            self._approved.add((stage, batch_id, subject_count))
        return result

    def wait_until_clear(self, *, stage: str, batch_id: str, subject_count: int) -> None:
        key = (stage, batch_id, subject_count)
        if key in self._approved:
            self._approved.remove(key)
            return
        event = self.observe_once(stage=stage, batch_id=batch_id, subject_count=subject_count)
        if not event["safe_to_spawn"]:
            raise guarded.LiveWorkloadObservationUnavailable(
                "diagnostic_workload_not_safe_to_spawn"
            )


def generation_id(implementation_commit: str, now: datetime) -> str:
    stamp = now.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = sha256_bytes(f"{implementation_commit}|{stamp}|{PROGRAM_CONTRACT}".encode())[:12]
    return f"20260907-fictional-websocket-diagnostic-{stamp}-{suffix}"


def planned_calls(diagnostic_generation_id: str) -> list[dict[str, object]]:
    return [
        {
            "ordinal": ordinal,
            "call_id": f"call-{ordinal:02d}",
            "invocation_id": (
                f"{diagnostic_generation_id}:call-{ordinal:02d}:DIRECTIONAL_CORE:call-{ordinal:02d}"
            ),
            "state_namespace": (f"FICTIONAL_WEBSOCKET_DIAGNOSTIC_20260907_CALL_{ordinal:02d}"),
            "subjects": list(SUBJECTS),
        }
        for ordinal in range(1, MAX_CALLS + 1)
    ]


def build_fixture(
    diagnostic_generation_id: str,
) -> tuple[dict[str, OwnedEvidencePacket], dict[str, object], str, dict[str, object]]:
    owned = {
        ticker: guarded.fictional_owned(ticker, market="us", padding_bytes=PADDING_BYTES)
        for ticker in SUBJECTS
    }
    catalogs = {ticker: stage_alias_catalogs(owned[ticker])[0] for ticker in SUBJECTS}
    prompt = frozen._core_prompt(
        packet_id=diagnostic_generation_id,
        tickers=SUBJECTS,
        contexts=tuple(
            frozen._owned_context(owned[ticker], catalogs[ticker]) for ticker in SUBJECTS
        ),
    )
    schema = transport._batch_schema(
        candidate=DirectionalCoreCandidate,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id=diagnostic_generation_id,
        catalogs=catalogs,
    )
    return owned, catalogs, prompt, schema


def _source_lock(
    diagnostic_generation_id: str,
    owned: Mapping[str, OwnedEvidencePacket],
) -> dict[str, object]:
    packet_sha256 = {
        ticker: canonical_sha256(owned[ticker].model_dump(mode="json")) for ticker in SUBJECTS
    }
    value: dict[str, object] = {
        "contract": "fictional-websocket-diagnostic-source-lock-v1",
        "source_generation_id": diagnostic_generation_id,
        "ordered_subjects": list(SUBJECTS),
        "market": "us",
        "stage": "DIRECTIONAL_CORE",
        "packet_sha256": packet_sha256,
        "new_holdout_created": 0,
        "real_issuer_count": 0,
        "fictional_subject_count": len(SUBJECTS),
    }
    value["source_lock_sha256"] = canonical_sha256(value)
    return value


def fixture_audit(owned: Mapping[str, OwnedEvidencePacket]) -> dict[str, object]:
    rows = []
    for ticker in SUBJECTS:
        packet = owned[ticker]
        source = packet.source_packet
        source_refs = [row.ref.source_ref for row in packet.evidence]
        rows.append(
            {
                "ticker": ticker,
                "ticker_reserved_fictional": ticker.startswith("SYNTHETIC_"),
                "routing_market": source.market,
                "company_name": source.company_name,
                "all_source_refs_fictional": all(
                    str(value).startswith("synthetic_transport_fixture.") for value in source_refs
                ),
                "all_ref_ids_fictional": all(
                    row.ref.ref_id.startswith(f"fictional:{ticker}:") for row in packet.evidence
                ),
            }
        )
    real_overlap = sorted(set(SUBJECTS) & set(HISTORICAL_REAL_COHORT))
    checks = {
        "four_subjects": len(rows) == 4,
        "subject_order": tuple(row["ticker"] for row in rows) == SUBJECTS,
        "routing_market_us": all(row["routing_market"] == "us" for row in rows),
        "reserved_fictional_identity": all(row["ticker_reserved_fictional"] for row in rows),
        "fictional_source_lineage": all(
            row["all_source_refs_fictional"] and row["all_ref_ids_fictional"] for row in rows
        ),
        "historical_real_cohort_overlap": not real_overlap,
    }
    return {
        "contract": "fictional-four-subject-fixture-audit-v1",
        "rows": rows,
        "historical_real_cohort_overlap": real_overlap,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def classify_attempt(
    receipt: Mapping[str, object],
    stderr_text: str,
    *,
    schema_valid: bool,
    identity_valid: bool,
    preservation_valid: bool,
    session_identity_valid: bool = True,
) -> dict[str, object]:
    runtime = classify_runtime_receipt(receipt, stderr_text)
    disconnects = int(runtime["observed_websocket_disconnect_signal_count"])
    capacity = int(runtime["explicit_capacity_diagnostic_count"])
    context = int(runtime["explicit_context_length_diagnostic_count"])
    status = str(receipt.get("status") or "UNKNOWN")
    timed_out = status == "TIMEOUT" or receipt.get("termination_initiator") == (
        "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG"
    )
    exit_code = receipt.get("exit_code")

    if not preservation_valid:
        outcome = "EVIDENCE_PRESERVATION_FAILURE"
    elif capacity:
        outcome = "EXPLICIT_CAPACITY_FAILURE_OBSERVED"
    elif context:
        outcome = "EXPLICIT_CONTEXT_FAILURE_OBSERVED"
    elif timed_out and disconnects:
        outcome = "DISCONNECT_THEN_WATCHDOG_TIMEOUT_OBSERVED"
    elif timed_out:
        outcome = "TIMEOUT_WITHOUT_OBSERVED_DISCONNECT"
    elif status == "PASS" and schema_valid and identity_valid and session_identity_valid:
        outcome = (
            "DISCONNECT_THEN_SUCCESS_OBSERVED" if disconnects else "VALID_OUTPUT_NO_DISCONNECT"
        )
    elif status == "PASS" and not schema_valid:
        outcome = "SCHEMA_INVALID_RESULT"
    elif status == "PASS" and (not identity_valid or not session_identity_valid):
        outcome = "IDENTITY_INVALID_RESULT"
    elif status == "SPAWN_FAILED" or receipt.get("child_cleanup_status") == ("NO_CHILD_SPAWNED"):
        outcome = "PRESPAWN_FAILURE"
    elif isinstance(exit_code, int) and exit_code != 0:
        outcome = "UNCLASSIFIED_TERMINAL_FAILURE"
    else:
        outcome = "UNUSABLE_TERMINAL_RESULT"

    usable = outcome in {
        "VALID_OUTPUT_NO_DISCONNECT",
        "DISCONNECT_THEN_SUCCESS_OBSERVED",
    }
    return {
        "contract": "fictional-websocket-attempt-classification-v1",
        "outcome": outcome,
        "usable": usable,
        "stop_remaining_calls": not usable,
        "observed_transport_classification": runtime["classification"],
        "observed_cli_retry_signal_count": runtime["observed_cli_retry_signal_count"],
        "observed_websocket_disconnect_signal_count": disconnects,
        "explicit_capacity_diagnostic_count": capacity,
        "explicit_context_length_diagnostic_count": context,
        "wrapper_explicit_retry_count": 0,
        "upstream_request_attempt_count": "UNKNOWN",
        "request_accepted_observability": "UNAVAILABLE",
        "schema_valid": schema_valid,
        "identity_valid": identity_valid,
        "session_identity_valid": session_identity_valid,
        "evidence_preservation_valid": preservation_valid,
        "runtime_events": runtime["safe_runtime_events"],
    }


def _redact_secrets(value: bytes) -> bytes:
    result = value
    for pattern in SECRET_PATTERNS:
        result = pattern.sub(b"[REDACTED]", result)
    return result


def preserve_attempt_artifacts(
    *,
    source_receipt: Path,
    source_stdout: Path,
    source_stderr: Path,
    source_output: Path,
    destination: Path,
    require_receipt: bool,
) -> dict[str, object]:
    destination.mkdir(parents=True, exist_ok=True)
    specifications = (
        (
            "transport_receipt",
            source_receipt,
            destination / "transport_receipt.json",
            require_receipt,
        ),
        ("stdout", source_stdout, destination / "stdout.raw.log", False),
        ("stderr", source_stderr, destination / "stderr.safe.log", False),
        ("output", source_output, destination / "output.raw.json", False),
    )
    rows = []
    failures = []
    for name, source, target, required in specifications:
        if not source.is_file():
            rows.append(
                {
                    "artifact": name,
                    "source_exists": False,
                    "required": required,
                    "preserved": False,
                    "exact_bytes": None,
                    "secret_match_count": 0,
                }
            )
            if required:
                failures.append(f"required_artifact_missing:{name}")
            continue
        try:
            original = source.read_bytes()
            secret_count = scan_bytes(original)
            preserved = _redact_secrets(original) if secret_count else original
            target.write_bytes(preserved)
            row = {
                "artifact": name,
                "source_exists": True,
                "required": required,
                "preserved": True,
                "original_sha256": sha256_bytes(original),
                "original_byte_size": len(original),
                "preserved_sha256": sha256_bytes(preserved),
                "preserved_byte_size": len(preserved),
                "exact_bytes": secret_count == 0,
                "secret_match_count": secret_count,
                "destination": target.name,
            }
            rows.append(row)
            if secret_count and name in {"transport_receipt", "output"}:
                failures.append(f"structured_artifact_secret_redaction:{name}")
        except OSError as exc:
            rows.append(
                {
                    "artifact": name,
                    "source_exists": True,
                    "required": required,
                    "preserved": False,
                    "error": f"{type(exc).__name__}:{exc}",
                }
            )
            failures.append(f"artifact_preservation_error:{name}")
    return {
        "contract": "attempt-artifact-preservation-v1",
        "rows": rows,
        "failures": failures,
        "evidence_preservation_failure_count": len(failures),
        "status": "PASS" if not failures else "FAIL",
    }


def _baseline_facts(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        completion = zip_json(archive, "completion.json")
        hard = zip_json(archive, "reports/proofs/09-offline-first-a-lineage-and-gate-audit.json")
        quality = zip_json(
            archive, "reports/proofs/11-message-quality-scope-and-original-export.json"
        )
    return {
        "historical_completion_status": completion.get("status"),
        "historical_model_subprocess_invocations": completion.get(
            "historical_model_subprocess_invocations"
        ),
        "historical_successful_contexts": completion.get("historical_successful_contexts"),
        "historical_failed_contexts": completion.get("historical_failed_contexts"),
        "historical_first_hard_gate_status": completion.get("first_run_hard_gate_status"),
        "historical_a_hard_gate_status": completion.get("a_run_hard_gate_status"),
        "historical_first_message_quality_status": completion.get("first_message_quality_status"),
        "historical_a_message_quality_status": completion.get("a_message_quality_status"),
        "historical_formal_stability_status": completion.get("formal_stability_status"),
        "historical_formal_generalization_status": completion.get("formal_generalization_status"),
        "historical_failure_classification": completion.get("timeout_classification"),
        "historical_prompt_bytes": 17940,
        "historical_first_a_descriptive_comparison": {
            "same_direction": "9/16",
            "boundary_direction_changes": "7/16",
            "direct_buy_sell_flips": 0,
        },
        "historical_repeated_substantive_spans": {"FIRST": 14, "A": 9},
        "hard_audit_source_status": hard.get("status"),
        "quality_audit_source_status": quality.get("status"),
    }


def _repository_state() -> dict[str, object]:
    status = git_value("status", "--short")
    return {
        "branch": git_value("branch", "--show-current"),
        "head": git_value("rev-parse", "HEAD"),
        "tree": git_value("rev-parse", "HEAD^{tree}"),
        "base_sha": git_value("rev-parse", "HEAD~2"),
        "status_short": status.splitlines() if status else [],
    }


def _implementation_hashes() -> dict[str, str]:
    return {
        "diagnostic_script": file_sha256(Path(__file__).resolve()),
        "observer": source_sha256(PausedScheduleProcessObserver),
        "single_observation_guard": source_sha256(SingleObservationWorkloadGuard),
        "canonical_adapter": source_sha256(transport.ContinuationTransportAdapter),
        "guarded_adapter": source_sha256(guarded.GuardedTransportAdapter),
        "instrumented_lifecycle": source_sha256(
            __import__(
                "app.services.codex_transport_lifecycle_service",
                fromlist=["invoke_instrumented_codex"],
            ).invoke_instrumented_codex
        ),
        "fixture_builder": source_sha256(guarded.fictional_owned),
        "core_prompt_builder": source_sha256(frozen._core_prompt),
        "schema_builder": source_sha256(transport._batch_schema),
        "runtime_event_extractor": source_sha256(extract_runtime_events),
        "attempt_classifier": source_sha256(classify_attempt),
        "artifact_preserver": source_sha256(preserve_attempt_artifacts),
    }


def prepare(args: argparse.Namespace) -> dict[str, object]:
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise ValueError(f"diagnostic_output_root_not_empty:{args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=True)
    repository = _repository_state()
    if repository["status_short"]:
        raise ValueError("implementation_worktree_must_be_clean_before_prepare")

    integrity = verify_indexed_zip(args.baseline_zip)
    pause = observe_pause_state()
    if pause.get("status") != "VERIFIED_PAUSED_COMPLETE":
        raise DiagnosticStop(f"monitoring_pause_not_verified:{pause.get('status')}")
    cli = cli_identity()
    if cli["status"] != "PASS":
        raise DiagnosticStop("cli_identity_drift")

    generated_at = datetime.now(UTC)
    implementation_commit = str(repository["head"])
    diagnostic_generation_id = generation_id(implementation_commit, generated_at)
    owned, catalogs, prompt, schema = build_fixture(diagnostic_generation_id)
    fixture = fixture_audit(owned)
    if fixture["status"] != "PASS":
        raise DiagnosticStop("fictional_fixture_identity_failure")
    prompt_bytes = prompt.encode("utf-8")
    if not 15_000 <= len(prompt_bytes) <= 20_000:
        raise DiagnosticStop(f"fictional_prompt_size_outside_target:{len(prompt_bytes)}")

    fixture_root = args.output_root / "fixture"
    packet_root = fixture_root / "packets"
    packet_root.mkdir(parents=True)
    for ticker in SUBJECTS:
        write_json(
            packet_root / f"{ticker}.json",
            owned[ticker].model_dump(mode="json"),
        )
    prompt_path = fixture_root / "prompt.template.txt"
    schema_path = fixture_root / "schema.template.json"
    prompt_path.write_bytes(prompt_bytes)
    write_json(schema_path, schema)

    source_lock = _source_lock(diagnostic_generation_id, owned)
    write_json(args.output_root / "source-lock.json", source_lock)
    write_json(args.output_root / "baseline-integrity.json", integrity)
    write_json(args.output_root / "pause-state.json", pause)
    write_json(args.output_root / "cli-identity.json", cli)
    write_json(args.output_root / "fixture-audit.json", fixture)
    baseline = _baseline_facts(args.baseline_zip)
    write_json(args.output_root / "historical-baseline-facts.json", baseline)

    packet_hashes = {ticker: file_sha256(packet_root / f"{ticker}.json") for ticker in SUBJECTS}
    plans = planned_calls(diagnostic_generation_id)
    implementation_hashes = _implementation_hashes()
    precommit: dict[str, object] = {
        "contract": "bounded-fictional-websocket-diagnostic-precommit-v1",
        "prepared_at": generated_at.isoformat(),
        "diagnostic_generation_id": diagnostic_generation_id,
        "repository": repository,
        "work_instruction_commit": git_value("rev-parse", "HEAD~1"),
        "implementation_commit": implementation_commit,
        "planned_calls": plans,
        "planned_call_budget": MAX_CALLS,
        "fictional_subject_count": len(SUBJECTS),
        "fictional_subject_ids": list(SUBJECTS),
        "market": "us",
        "stage": "DIRECTIONAL_CORE",
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "fixture_sha256": canonical_sha256(
            {ticker: owned[ticker].model_dump(mode="json") for ticker in SUBJECTS}
        ),
        "packet_file_sha256": packet_hashes,
        "prompt_sha256": file_sha256(prompt_path),
        "prompt_bytes": prompt_path.stat().st_size,
        "historical_prompt_bytes": baseline["historical_prompt_bytes"],
        "prompt_byte_delta_from_historical": (
            prompt_path.stat().st_size - int(baseline["historical_prompt_bytes"])
        ),
        "schema_sha256": file_sha256(schema_path),
        "identity_normalized_prompt_semantic_hash": (
            runtime_identity.normalized_prompt_semantic_hash(
                prompt_path.read_text(encoding="utf-8")
            )
        ),
        "identity_normalized_schema_semantic_hash": (
            runtime_identity.normalized_schema_semantic_hash(read_json(schema_path))
        ),
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "cli_identity": cli,
        "configured_timeout_seconds": TIMEOUT_SECONDS,
        "timeout_owner": "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG",
        "timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "fresh_session_policy": "CODEX_EXEC_EPHEMERAL_PER_CALL",
        "fresh_namespace_policy": "DISTINCT_PREDECLARED_NAMESPACE_PER_CALL",
        "workload_guard": "SingleObservationWorkloadGuard",
        "workload_observer": "PausedScheduleProcessObserver",
        "network_readiness_check": "existing_probe_codex_network_readiness_once_per_allowed_call",
        "implementation_hashes": implementation_hashes,
        "maximum_subprocess_call_budget": MAX_CALLS,
        "wrapper_explicit_retry_budget": 0,
        "stop_rules": [
            "first watchdog timeout or nonzero terminal failure",
            "first explicit capacity or context-length failure",
            "first schema or runtime identity failure",
            "first evidence preservation failure",
            "first unsafe or unavailable pre-spawn observation",
            "first fixture/model/schema/CLI/transport drift",
            "first real-issuer contamination",
        ],
        "canonical_transport_mutation": 0,
        "model_prompt_schema_semantic_mutation": 0,
        "timeout_increase": 0,
        "wrapper_explicit_retry_count": 0,
        "validation_before_freeze": {
            "focused": args.focused_result,
            "full_pytest": args.full_result,
            "ruff": args.ruff_result,
            "diff_check": args.diff_result,
        },
    }
    precommit["precommit_sha256"] = canonical_sha256(precommit)
    write_json(args.output_root / "diagnostic-precommit.json", precommit)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "diagnostic_generation_id": diagnostic_generation_id,
        "prepared_at": generated_at.isoformat(),
        "base_sha": repository["base_sha"],
        "work_instruction_commit": precommit["work_instruction_commit"],
        "implementation_commit": implementation_commit,
        "implementation_tree": repository["tree"],
        "branch": repository["branch"],
        "precommit_sha256": precommit["precommit_sha256"],
        "fixture_sha256": precommit["fixture_sha256"],
        "prompt_sha256": precommit["prompt_sha256"],
        "schema_sha256": precommit["schema_sha256"],
        "source_lock_sha256": precommit["source_lock_sha256"],
        "implementation_hashes": implementation_hashes,
        "planned_calls": plans,
        "planned_call_budget": MAX_CALLS,
        "consumed_subprocess_call_budget": 0,
        "existing_network_readiness_check_count": 0,
        "per_call_results": [],
        "stop_reason": None,
        "new_real_issuer_model_calls": 0,
        "new_fictional_model_subprocess_calls": 0,
        "new_market_financial_source_fetch_calls": 0,
        "scheduler_mutation_count": 0,
        "auto_resume_executed": 0,
        "production_send": 0,
        "production_deployment": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    return state


def _verify_file_hash(path: Path, expected: object, label: str) -> None:
    if not path.is_file() or file_sha256(path) != expected:
        raise DiagnosticStop(f"frozen_artifact_drift:{label}")


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> dict[str, object]:
    if state.get("state") != "PREPARED_FROZEN":
        raise DiagnosticStop(f"diagnostic_state_not_executable:{state.get('state')}")
    repository = _repository_state()
    if repository["head"] != state["implementation_commit"]:
        raise DiagnosticStop("implementation_commit_drift")
    if repository["tree"] != state["implementation_tree"]:
        raise DiagnosticStop("implementation_tree_drift")
    if repository["status_short"]:
        raise DiagnosticStop("worktree_not_clean_at_execution_freeze")
    if _implementation_hashes() != state["implementation_hashes"]:
        raise DiagnosticStop("implementation_hash_drift")

    precommit_path = args.output_root / "diagnostic-precommit.json"
    precommit = read_json(precommit_path)
    recorded = str(precommit.pop("precommit_sha256"))
    if canonical_sha256(precommit) != recorded or recorded != state["precommit_sha256"]:
        raise DiagnosticStop("precommit_hash_drift")
    precommit["precommit_sha256"] = recorded
    _verify_file_hash(
        args.output_root / "fixture" / "prompt.template.txt",
        state["prompt_sha256"],
        "prompt_template",
    )
    _verify_file_hash(
        args.output_root / "fixture" / "schema.template.json",
        state["schema_sha256"],
        "schema_template",
    )
    if verify_indexed_zip(args.baseline_zip)["status"] != "PASS":
        raise DiagnosticStop("baseline_integrity_drift")
    cli = cli_identity()
    if cli["status"] != "PASS":
        raise DiagnosticStop("cli_identity_drift")
    return {"repository": repository, "precommit": precommit, "cli": cli}


def _call_binding(
    *,
    state: Mapping[str, object],
    call: Mapping[str, object],
    source_lock: Mapping[str, object],
) -> runtime_identity.RuntimeIdentityBinding:
    packet_hashes = source_lock.get("packet_sha256")
    if not isinstance(packet_hashes, Mapping):
        raise DiagnosticStop("source_lock_packet_hashes_missing")
    generation = str(state["diagnostic_generation_id"])
    return runtime_identity.RuntimeIdentityBinding(
        source_generation_id=generation,
        runtime_generation_id=generation,
        source_lock_sha256=str(state["source_lock_sha256"]),
        run_id="DIAGNOSTIC",
        stage="DIRECTIONAL_CORE",
        batch_id=str(call["call_id"]),
        invocation_id=str(call["invocation_id"]),
        ordered_subjects=SUBJECTS,
        output_contract=CORE_OUTPUT_CONTRACT,
        per_subject_packet_hashes=tuple(
            (ticker, str(packet_hashes[ticker])) for ticker in SUBJECTS
        ),
    )


def _receipt_paths(receipt_root: Path, invocation_id: str) -> tuple[Path, Path, Path]:
    receipt = receipt_root / f"{sha256_bytes(invocation_id.encode())[:16]}.json"
    return receipt, receipt.with_suffix(".stdout.log"), receipt.with_suffix(".stderr.log")


def _runtime_timeline(receipt: Mapping[str, object]) -> dict[str, object]:
    start = receipt.get("invocation_start_monotonic")

    def relative(field: str) -> float | None:
        value = receipt.get(field)
        if not isinstance(start, (int, float)) or not isinstance(value, (int, float)):
            return None
        return round(float(value) - float(start), 6)

    return {
        "start": 0.0 if isinstance(start, (int, float)) else None,
        "spawn_requested": relative("process_spawn_requested_monotonic"),
        "spawn": relative("process_spawn_monotonic"),
        "stdin_complete": relative("stdin_complete_monotonic"),
        "first_stderr": relative("first_stderr_byte_monotonic"),
        "last_stderr": relative("last_stderr_byte_monotonic"),
        "first_stdout": relative("first_stdout_byte_monotonic"),
        "last_stdout": relative("last_stdout_byte_monotonic"),
        "exit": relative("process_exit_monotonic"),
        "streams_complete": relative("stream_collection_complete_monotonic"),
        "parse_complete": relative("output_parse_complete_monotonic"),
    }


def _read_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _validate_call_output(
    *,
    output_path: Path,
    schema_path: Path,
    binding: runtime_identity.RuntimeIdentityBinding,
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, object],
) -> dict[str, object]:
    if not output_path.is_file():
        return {
            "output_exists": False,
            "parse_status": "OUTPUT_FILE_MISSING",
            "schema_errors": ["output_file_missing"],
            "schema_status": "FAIL",
            "output_identity": {"status": "FAIL", "reason": "output_file_missing"},
            "alias_resolution_status": "NOT_RUN",
            "candidate_count": 0,
            "status": "FAIL",
        }
    try:
        output = read_json(output_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "output_exists": True,
            "parse_status": f"FAIL:{type(exc).__name__}",
            "schema_errors": ["output_parse_failure"],
            "schema_status": "FAIL",
            "output_identity": {"status": "FAIL", "reason": "output_parse_failure"},
            "alias_resolution_status": "NOT_RUN",
            "candidate_count": 0,
            "status": "FAIL",
        }
    schema = read_json(schema_path)
    schema_errors = validate_json_schema(output, schema)
    output_identity = runtime_identity.validate_output_identity(output, binding)
    alias_status = "NOT_RUN"
    alias_error = None
    candidate_count = len(output.get("candidates") or [])
    try:
        frozen._resolve_batch_candidates(
            output.get("candidates"),
            batch=SUBJECTS,
            evidence={ticker: owned[ticker].source_packet for ticker in SUBJECTS},
            catalogs=catalogs,
            model_type=DirectionalCoreCandidate,
        )
        alias_status = "PASS"
    except Exception as exc:
        alias_status = "FAIL"
        alias_error = f"{type(exc).__name__}:{exc}"
    status = (
        "PASS"
        if not schema_errors
        and output_identity["status"] == "PASS"
        and alias_status == "PASS"
        and candidate_count == len(SUBJECTS)
        else "FAIL"
    )
    return {
        "output_exists": True,
        "parse_status": "PASS",
        "schema_errors": schema_errors,
        "schema_status": "PASS" if not schema_errors else "FAIL",
        "output_identity": output_identity,
        "alias_resolution_status": alias_status,
        "alias_resolution_error": alias_error,
        "candidate_count": candidate_count,
        "status": status,
    }


def _empty_receipt_from_error(
    call: Mapping[str, object], exc: BaseException, lifecycle: Mapping[str, object]
) -> dict[str, object]:
    return {
        "contract": "pre-spawn-diagnostic-observation-v1",
        "invocation_id": call["invocation_id"],
        "generation_id": str(call["invocation_id"]).split(":call-", 1)[0],
        "stage": "DIRECTIONAL_CORE",
        "batch_id": call["call_id"],
        "subject_count": len(SUBJECTS),
        "status": "PRESPAWN_FAILURE",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "exit_code": None,
        "termination_initiator": "NONE",
        "child_cleanup_status": "NO_CHILD_SPAWNED",
        "orphan_model_process_count": 0,
        "request_accepted_observability": "UNAVAILABLE",
        "transport_lifecycle": dict(lifecycle),
    }


def execute_one_call(
    *,
    args: argparse.Namespace,
    state: Mapping[str, object],
    call: Mapping[str, object],
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, object],
    adapter: guarded.GuardedTransportAdapter,
    guard: SingleObservationWorkloadGuard,
    prior_sessions: set[str],
    prior_namespace_hashes: set[str],
) -> dict[str, object]:
    call_dir = args.output_root / "diagnostic-contexts" / str(call["call_id"])
    call_dir.mkdir(parents=True, exist_ok=False)
    source_lock = read_json(args.output_root / "source-lock.json")
    binding = _call_binding(state=state, call=call, source_lock=source_lock)
    identity_lock = runtime_identity.bind_runtime_request(
        prompt_template=args.output_root / "fixture" / "prompt.template.txt",
        schema_template=args.output_root / "fixture" / "schema.template.json",
        runtime_prompt=call_dir / "prompt.txt",
        runtime_schema=call_dir / "schema.json",
        binding=binding,
        lock_path=call_dir / "identity-binding-lock.json",
    )
    identity_preflight = runtime_identity.preflight_actual_request(
        prompt_path=call_dir / "prompt.txt",
        schema_path=call_dir / "schema.json",
        lock_path=call_dir / "identity-binding-lock.json",
        source_lock_path=args.output_root / "source-lock.json",
        validator_expected_packet_id=str(state["diagnostic_generation_id"]),
        adapter_generation_id=adapter.continuation_generation,
        result_path=call_dir / "identity-preflight.json",
    )
    started_at = datetime.now(UTC)
    model_count_before = adapter.model_call_count
    root_exception: BaseException | None = None
    lifecycle: dict[str, object] = {}
    adapter_invocation_attempted = False

    try:
        workload_preflight = adapter.preflight(
            stage="DIRECTIONAL_CORE",
            batch_id=str(call["call_id"]),
            subject_count=len(SUBJECTS),
        )
    except Exception as exc:
        workload_preflight = {
            "contract": "prespawn-live-workload-guard-preflight-v1",
            "status": "FAIL",
            "safe_to_spawn": 0,
            "root_exception": f"{type(exc).__name__}:{exc}",
        }
        root_exception = exc
    write_json(call_dir / "workload-preflight.json", workload_preflight)

    with tempfile.TemporaryDirectory(prefix=f"{call['call_id']}-private-") as temp_name:
        private_root = Path(temp_name)
        receipt_root = private_root / "receipts"
        adapter.receipt_root = receipt_root
        source_output = private_root / "output.raw.json"
        source_log = private_root / "combined.log"
        source_receipt, source_stdout, source_stderr = _receipt_paths(
            receipt_root, str(call["invocation_id"])
        )
        if root_exception is None and workload_preflight.get("status") != "PASS":
            root_exception = DiagnosticStop("pre_spawn_workload_not_safe")
        if root_exception is None:
            try:
                adapter_invocation_attempted = True
                with engine.isolated_model_working_directory(
                    run=f"diagnostic-{call['call_id']}", batch=int(call["ordinal"])
                ) as model_cwd:
                    adapter.invoke(
                        prompt=call_dir / "prompt.txt",
                        output=source_output,
                        log=source_log,
                        schema=call_dir / "schema.json",
                        cwd=model_cwd,
                        timeout=TIMEOUT_SECONDS,
                        state_namespace=str(call["state_namespace"]),
                        invocation_id=str(call["invocation_id"]),
                        stage="DIRECTIONAL_CORE",
                        batch_id=str(call["call_id"]),
                        subject_count=len(SUBJECTS),
                    )
            except BaseException as exc:
                root_exception = exc
        lifecycle = adapter.lifecycle_for(str(call["invocation_id"]))
        spawned = adapter.model_call_count > model_count_before
        require_receipt = spawned
        preservation = preserve_attempt_artifacts(
            source_receipt=source_receipt,
            source_stdout=source_stdout,
            source_stderr=source_stderr,
            source_output=source_output,
            destination=call_dir,
            require_receipt=require_receipt,
        )

    receipt_path = call_dir / "transport_receipt.json"
    if receipt_path.is_file():
        receipt = read_json(receipt_path)
    elif root_exception is not None:
        receipt = _empty_receipt_from_error(call, root_exception, lifecycle)
    else:
        receipt = _empty_receipt_from_error(
            call, RuntimeError("transport_receipt_missing"), lifecycle
        )

    stderr_text = _read_optional_text(call_dir / "stderr.safe.log")
    runtime_events = extract_runtime_events(stderr_text)
    sessions = SESSION_ID_RE.findall(stderr_text)
    session_id = sessions[0] if sessions else None
    namespace_hash = (
        receipt.get("transport_metadata", {}).get("runtime_state_namespace_hash")
        if isinstance(receipt.get("transport_metadata"), Mapping)
        else None
    )
    session_identity_valid = bool(session_id) and session_id not in prior_sessions
    namespace_identity_valid = bool(namespace_hash) and namespace_hash not in (
        prior_namespace_hashes
    )
    if session_id:
        prior_sessions.add(session_id)
    if namespace_hash:
        prior_namespace_hashes.add(str(namespace_hash))

    output_validation = _validate_call_output(
        output_path=call_dir / "output.raw.json",
        schema_path=call_dir / "schema.json",
        binding=binding,
        owned=owned,
        catalogs=catalogs,
    )
    receipt_identity = (
        runtime_identity.validate_receipt_identity(receipt, binding)
        if receipt_path.is_file()
        else {"status": "NOT_RUN", "reason": "no_transport_receipt"}
    )
    identity_valid = (
        identity_preflight["status"] == "PASS"
        and identity_lock.get("decision_prompt_semantic_change") == 0
        and identity_lock.get("investment_schema_semantic_change") == 0
        and receipt_identity["status"] == "PASS"
        and output_validation.get("output_identity", {}).get("status") == "PASS"
        and namespace_identity_valid
    )
    classification = classify_attempt(
        receipt,
        stderr_text,
        schema_valid=output_validation["status"] == "PASS",
        identity_valid=identity_valid,
        preservation_valid=preservation["status"] == "PASS",
        session_identity_valid=session_identity_valid,
    )
    if not spawned:
        classification["outcome"] = "PRESPAWN_FAILURE"
        classification["usable"] = False
        classification["stop_remaining_calls"] = True

    lifecycle_summary = {
        "contract": "fictional-websocket-lifecycle-summary-v1",
        "call_id": call["call_id"],
        "invocation_id": call["invocation_id"],
        "state_namespace": call["state_namespace"],
        "state_namespace_hash": namespace_hash,
        "session_id": session_id,
        "session_id_observation_count": len(sessions),
        "fresh_session_identity_valid": session_identity_valid,
        "fresh_namespace_identity_valid": namespace_identity_valid,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "subprocess_spawned": int(spawned),
        "timeline_seconds_from_start": _runtime_timeline(receipt),
        "receipt_status": receipt.get("status"),
        "exit_code": receipt.get("exit_code"),
        "input_bytes": receipt.get("input_bytes"),
        "stdout_bytes": receipt.get("stdout_bytes"),
        "stderr_bytes": receipt.get("stderr_bytes"),
        "output_bytes": receipt.get("output_bytes"),
        "termination_initiator": receipt.get("termination_initiator"),
        "child_cleanup_status": receipt.get("child_cleanup_status"),
        "orphan_model_process_count": receipt.get("orphan_model_process_count"),
        "root_exception": (
            f"{type(root_exception).__name__}:{root_exception}"
            if root_exception is not None
            else None
        ),
        "adapter_lifecycle": lifecycle,
        "output_validation": output_validation,
        "receipt_identity_validation": receipt_identity,
        "artifact_preservation": preservation,
        "classification": classification,
    }
    write_json(
        call_dir / "runtime-events.json",
        {
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
        },
    )
    write_json(call_dir / "artifact-preservation.json", preservation)
    write_json(call_dir / "lifecycle-summary.json", lifecycle_summary)
    manifest = {
        "contract": "fictional-websocket-context-manifest-v1",
        "call": dict(call),
        "binding": binding.document(),
        "prompt_sha256": file_sha256(call_dir / "prompt.txt"),
        "schema_sha256": file_sha256(call_dir / "schema.json"),
        "identity_binding_lock_hash": identity_lock["identity_binding_lock_hash"],
        "files": {
            path.name: {"sha256": file_sha256(path), "byte_size": path.stat().st_size}
            for path in sorted(call_dir.iterdir())
            if path.is_file() and path.name != "context_manifest.json"
        },
    }
    write_json(call_dir / "context_manifest.json", manifest)
    return {
        "call_id": call["call_id"],
        "ordinal": call["ordinal"],
        "invocation_id": call["invocation_id"],
        "state_namespace": call["state_namespace"],
        "state_namespace_hash": namespace_hash,
        "session_id": session_id,
        "subprocess_spawned": int(spawned),
        "existing_network_readiness_check_count": int(adapter_invocation_attempted),
        "receipt_status": receipt.get("status"),
        "exit_code": receipt.get("exit_code"),
        "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
        "output_bytes": receipt.get("output_bytes"),
        "classification": classification,
        "preservation_status": preservation["status"],
        "root_exception": lifecycle_summary["root_exception"],
    }


def aggregate_results(
    *,
    state: Mapping[str, object],
    results: Sequence[Mapping[str, object]],
    stop_reason: str | None,
) -> dict[str, object]:
    classifications = [row.get("classification") or {} for row in results]
    outcomes = [str(row.get("outcome") or "UNKNOWN") for row in classifications]
    consumed = sum(int(row.get("subprocess_spawned") or 0) for row in results)
    sessions = [str(row["session_id"]) for row in results if row.get("session_id")]
    namespaces = [
        str(row["state_namespace_hash"]) for row in results if row.get("state_namespace_hash")
    ]
    unattempted = [
        {
            "call_id": call["call_id"],
            "reason": stop_reason or "call_budget_not_reached",
        }
        for call in state["planned_calls"][len(results) :]
    ]
    all_usable = len(results) == MAX_CALLS and all(
        bool(item.get("usable")) for item in classifications
    )
    disconnect_success = outcomes.count("DISCONNECT_THEN_SUCCESS_OBSERVED")
    disconnect_timeout = outcomes.count("DISCONNECT_THEN_WATCHDOG_TIMEOUT_OBSERVED")
    timeout_without = outcomes.count("TIMEOUT_WITHOUT_OBSERVED_DISCONNECT")
    preservation_failures = sum(
        int(not bool(item.get("evidence_preservation_valid"))) for item in classifications
    )
    prompt_hashes = {
        file_sha256(
            Path(str(state.get("output_root", "")))
            / "diagnostic-contexts"
            / str(row["call_id"])
            / "prompt.txt"
        )
        for row in results
        if state.get("output_root")
    }
    schema_hashes = {
        file_sha256(
            Path(str(state.get("output_root", "")))
            / "diagnostic-contexts"
            / str(row["call_id"])
            / "schema.json"
        )
        for row in results
        if state.get("output_root")
    }
    return {
        "contract": "bounded-fictional-websocket-diagnostic-aggregate-v1",
        "diagnostic_generation_id": state["diagnostic_generation_id"],
        "diagnostic_execution_status": (
            "COMPLETED_BOUNDED_BUDGET" if all_usable else "STOPPED_ON_PREDECLARED_CONDITION"
        ),
        "planned_call_budget": MAX_CALLS,
        "consumed_subprocess_call_budget": consumed,
        "new_real_issuer_model_calls": 0,
        "new_fictional_model_subprocess_calls": consumed,
        "per_call_results": list(results),
        "outcome_counts": dict(Counter(outcomes)),
        "unattempted_calls_and_reasons": unattempted,
        "stop_reason": stop_reason,
        "observed_cli_retry_signal_count": sum(
            int(item.get("observed_cli_retry_signal_count") or 0) for item in classifications
        ),
        "observed_websocket_disconnect_signal_count": sum(
            int(item.get("observed_websocket_disconnect_signal_count") or 0)
            for item in classifications
        ),
        "disconnect_followed_by_success_count": disconnect_success,
        "disconnect_followed_by_timeout_count": disconnect_timeout,
        "timeout_without_observed_disconnect_count": timeout_without,
        "explicit_capacity_failure_count": outcomes.count("EXPLICIT_CAPACITY_FAILURE_OBSERVED"),
        "explicit_context_failure_count": outcomes.count("EXPLICIT_CONTEXT_FAILURE_OBSERVED"),
        "orphan_model_process_count": sum(
            int(
                read_json(
                    Path(str(state["output_root"]))
                    / "diagnostic-contexts"
                    / str(row["call_id"])
                    / "lifecycle-summary.json"
                ).get("orphan_model_process_count")
                or 0
            )
            for row in results
        ),
        "evidence_preservation_failure_count": preservation_failures,
        "existing_network_readiness_check_count": sum(
            int(row.get("existing_network_readiness_check_count") or 0) for row in results
        ),
        "session_identity_count": len(set(sessions)),
        "session_identity_observed_count": len(sessions),
        "distinct_namespace_count": len(set(namespaces)),
        "namespace_identity_observed_count": len(namespaces),
        "prompt_hash_count": len(prompt_hashes),
        "schema_hash_count": len(schema_hashes),
        "model_prompt_schema_semantic_drift": int(len(prompt_hashes) > 1 or len(schema_hashes) > 1),
        "wrapper_explicit_retry_count": 0,
        "upstream_request_attempt_count": "UNKNOWN",
        "request_accepted_observability": "UNAVAILABLE",
        "historical_failure_reproduced_in_this_probe": int(disconnect_timeout > 0),
        "reconnect_path_exercised": (
            "OBSERVED_SUCCESS"
            if disconnect_success
            else "OBSERVED_TIMEOUT"
            if disconnect_timeout
            else "NOT_OBSERVED"
        ),
        "runtime_root_cause_confirmed": False,
        "runtime_reliability_status": "NOT_ESTABLISHED",
        "remaining_hypotheses_and_limitations": [
            "Three or fewer fictional calls do not establish production reliability.",
            "The probe does not recreate the 16 successful contexts before the historical failure.",
            "Upstream request acceptance and attempt counts remain unobservable.",
            "A clean bounded result does not prove the reconnect path was exercised.",
        ],
        "status": (
            "PASS_BOUNDED_DIAGNOSTIC_COMPLETED"
            if all_usable
            else "STOPPED_ON_PREDECLARED_CONDITION"
        ),
    }


def execute(args: argparse.Namespace) -> dict[str, object]:
    state_path = args.output_root / "program-state.json"
    state = read_json(state_path)
    state["output_root"] = str(args.output_root.resolve())
    verify_frozen(args, state)
    owned, catalogs, prompt, schema = build_fixture(str(state["diagnostic_generation_id"]))
    if file_sha256(args.output_root / "fixture" / "prompt.template.txt") != (
        sha256_bytes(prompt.encode("utf-8"))
    ):
        raise DiagnosticStop("fixture_prompt_rebuild_drift")
    if canonical_sha256(schema) != canonical_sha256(
        read_json(args.output_root / "fixture" / "schema.template.json")
    ):
        raise DiagnosticStop("fixture_schema_rebuild_drift")
    if fixture_audit(owned)["status"] != "PASS":
        raise DiagnosticStop("fixture_real_issuer_contamination")

    state["state"] = "EXECUTING_NO_RESUME"
    state["execution_started_at"] = datetime.now(UTC).isoformat()
    write_json(state_path, state)
    observer = PausedScheduleProcessObserver()
    guard = SingleObservationWorkloadGuard(
        args.output_root / "workload-guard-audit.json", observer=observer
    )
    adapter = guarded.GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["diagnostic_generation_id"]),
        receipt_root=args.output_root / "unused-receipt-root",
        codex_bin=str(cli_identity()["path"]),
    )
    results: list[dict[str, object]] = []
    prior_sessions: set[str] = set()
    prior_namespace_hashes: set[str] = set()
    stop_reason: str | None = None
    for call in state["planned_calls"]:
        result = execute_one_call(
            args=args,
            state=state,
            call=call,
            owned=owned,
            catalogs=catalogs,
            adapter=adapter,
            guard=guard,
            prior_sessions=prior_sessions,
            prior_namespace_hashes=prior_namespace_hashes,
        )
        results.append(result)
        state["per_call_results"] = results
        state["consumed_subprocess_call_budget"] = sum(
            int(row["subprocess_spawned"]) for row in results
        )
        state["new_fictional_model_subprocess_calls"] = state["consumed_subprocess_call_budget"]
        state["existing_network_readiness_check_count"] = sum(
            int(row["existing_network_readiness_check_count"]) for row in results
        )
        write_json(state_path, state)
        if result["classification"]["stop_remaining_calls"]:
            stop_reason = str(result["classification"]["outcome"])
            break
    if stop_reason is None and len(results) == MAX_CALLS:
        stop_reason = "BOUNDED_CALL_BUDGET_COMPLETE"
    aggregate = aggregate_results(state=state, results=results, stop_reason=stop_reason)
    write_json(args.output_root / "aggregate-result.json", aggregate)
    state.update(
        {
            "state": "EXECUTION_COMPLETE",
            "execution_completed_at": datetime.now(UTC).isoformat(),
            "stop_reason": stop_reason,
            "diagnostic_execution_status": aggregate["diagnostic_execution_status"],
            "consumed_subprocess_call_budget": aggregate["consumed_subprocess_call_budget"],
            "new_fictional_model_subprocess_calls": aggregate[
                "new_fictional_model_subprocess_calls"
            ],
            "existing_network_readiness_check_count": aggregate[
                "existing_network_readiness_check_count"
            ],
            "per_call_results": results,
        }
    )
    write_json(state_path, state)
    return aggregate


def completion_document(
    *,
    args: argparse.Namespace,
    indexed_payload_count: int | None = None,
    zip_member_count: int | None = None,
) -> dict[str, object]:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "EXECUTION_COMPLETE":
        raise DiagnosticStop(f"execution_not_complete:{state.get('state')}")
    aggregate = read_json(args.output_root / "aggregate-result.json")
    integrity = read_json(args.output_root / "baseline-integrity.json")
    pause = read_json(args.output_root / "pause-state.json")
    cli = read_json(args.output_root / "cli-identity.json")
    precommit = read_json(args.output_root / "diagnostic-precommit.json")
    baseline = read_json(args.output_root / "historical-baseline-facts.json")
    current_pause = observe_pause_state()
    if current_pause.get("status") != "VERIFIED_PAUSED_COMPLETE":
        raise DiagnosticStop("monitoring_pause_drift_at_completion")
    final_head = git_value("rev-parse", "HEAD")
    completion: dict[str, object] = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": state["base_sha"],
        "work_instruction_commit": state["work_instruction_commit"],
        "implementation_commit": state["implementation_commit"],
        "final_head_sha": final_head,
        "branch": state["branch"],
        "input_zip_sha256": integrity["input_zip_sha256"],
        "input_integrity_status": integrity["status"],
        "pause_observed_at": current_pause["observed_at"],
        "initial_pause_observed_at": pause["observed_at"],
        "observed_paused_schedule_count": current_pause["observed_scheduler_object_count"],
        "unexpected_active_monitoring_paths": current_pause["unexpected_active_paths"],
        "scheduler_mutation_count": 0,
        "auto_resume_executed": 0,
        "natural_live_cancel_count": 0,
        "diagnostic_generation_id": state["diagnostic_generation_id"],
        "precommit_sha256": state["precommit_sha256"],
        "fixture_sha256": state["fixture_sha256"],
        "planned_call_budget": MAX_CALLS,
        "consumed_subprocess_call_budget": aggregate["consumed_subprocess_call_budget"],
        "unattempted_calls_and_reasons": aggregate["unattempted_calls_and_reasons"],
        "new_real_issuer_model_calls": 0,
        "new_fictional_model_subprocess_calls": aggregate["new_fictional_model_subprocess_calls"],
        "new_market_financial_source_fetch_calls": 0,
        "existing_network_readiness_check_count": aggregate[
            "existing_network_readiness_check_count"
        ],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "cli_version": cli["version"],
        "cli_binary_sha256": cli["sha256"],
        "subjects_per_context": len(SUBJECTS),
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "configured_timeout_seconds": TIMEOUT_SECONDS,
        "timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "session_identity_count": aggregate["session_identity_count"],
        "distinct_namespace_count": aggregate["distinct_namespace_count"],
        "model_prompt_schema_semantic_drift": aggregate["model_prompt_schema_semantic_drift"],
        "canonical_transport_mutation": 0,
        "cli_or_protocol_change": 0,
        "timeout_increase": 0,
        "wrapper_explicit_retry_count": 0,
        "per_call_results": aggregate["per_call_results"],
        "observed_cli_retry_signal_count": aggregate["observed_cli_retry_signal_count"],
        "observed_websocket_disconnect_signal_count": aggregate[
            "observed_websocket_disconnect_signal_count"
        ],
        "upstream_request_attempt_count": "UNKNOWN",
        "request_accepted_observability": "UNAVAILABLE",
        "disconnect_followed_by_success_count": aggregate["disconnect_followed_by_success_count"],
        "disconnect_followed_by_timeout_count": aggregate["disconnect_followed_by_timeout_count"],
        "timeout_without_observed_disconnect_count": aggregate[
            "timeout_without_observed_disconnect_count"
        ],
        "explicit_capacity_failure_count": aggregate["explicit_capacity_failure_count"],
        "explicit_context_failure_count": aggregate["explicit_context_failure_count"],
        "orphan_model_process_count": aggregate["orphan_model_process_count"],
        "evidence_preservation_failure_count": aggregate["evidence_preservation_failure_count"],
        "historical_failure_reproduced_in_this_probe": aggregate[
            "historical_failure_reproduced_in_this_probe"
        ],
        "reconnect_path_exercised": aggregate["reconnect_path_exercised"],
        "runtime_root_cause_confirmed": False,
        "runtime_reliability_status": "NOT_ESTABLISHED",
        "remaining_hypotheses_and_limitations": aggregate["remaining_hypotheses_and_limitations"],
        "historical_first_a_hard_gate_status": {
            "FIRST": baseline["historical_first_hard_gate_status"],
            "A": baseline["historical_a_hard_gate_status"],
        },
        "historical_message_quality_status": {
            "FIRST": baseline["historical_first_message_quality_status"],
            "A": baseline["historical_a_message_quality_status"],
            "repeated_substantive_spans": baseline["historical_repeated_substantive_spans"],
        },
        "formal_stability_status": "NOT_MEASURED",
        "formal_generalization_status": "NOT_ESTABLISHED",
        "production_db_mutation": 0,
        "production_send": 0,
        "production_deployment": 0,
        "paid_data_service_change": 0,
        "new_free_api_management_gate": 0,
        "stock_registration_change": 0,
        "night_futures_change": 0,
        "monitoring_bootstrap_started": 0,
        "retired_real_cohort_replayed": 0,
        "historical_b_or_c_resumed": 0,
        "task_implementation_preflight_status": "PASS",
        "diagnostic_execution_status": aggregate["diagnostic_execution_status"],
        "disconnect_observed": int(
            int(aggregate["observed_websocket_disconnect_signal_count"]) > 0
        ),
        "recovery_observed": aggregate["reconnect_path_exercised"],
        "root_cause_status": "UNRESOLVED",
        "formal_proof_status": "INCOMPLETE",
        "status": aggregate["status"],
        "stop_reason": aggregate["stop_reason"],
        "next_scope": (
            "SEPARATELY_AUTHORIZED_REAL_PROOF_WITH_TRANSPORT_RISK_CARRIED"
            if aggregate["diagnostic_execution_status"] == "COMPLETED_BOUNDED_BUDGET"
            else "BOUNDED_RUNTIME_INTERVENTION_REVIEW_SUPPORTED_BY_OBSERVED_FAILURE"
        ),
        "validation_before_freeze": precommit["validation_before_freeze"],
        "indexed_payload_count": indexed_payload_count,
        "zip_member_count": zip_member_count,
        "artifact_hash_mismatch_count": 0 if indexed_payload_count is not None else None,
        "artifact_size_mismatch_count": 0 if indexed_payload_count is not None else None,
    }
    return completion


def _attempt_table(results: Sequence[Mapping[str, object]]) -> str:
    if not results:
        return "| Call | Spawned | Status | Outcome | Session |\n|---|---:|---|---|---|\n"
    rows = ["| Call | Spawned | Status | Outcome | Session |", "|---|---:|---|---|---|"]
    for result in results:
        classification = result.get("classification") or {}
        session = str(result.get("session_id") or "NOT_OBSERVED")
        rows.append(
            "| {call} | {spawned} | {status} | {outcome} | `{session}` |".format(
                call=result.get("call_id"),
                spawned=result.get("subprocess_spawned"),
                status=result.get("receipt_status"),
                outcome=classification.get("outcome"),
                session=session,
            )
        )
    return "\n".join(rows) + "\n"


def _report_documents(args: argparse.Namespace) -> dict[str, tuple[dict[str, object], str]]:
    state = read_json(args.output_root / "program-state.json")
    aggregate = read_json(args.output_root / "aggregate-result.json")
    integrity = read_json(args.output_root / "baseline-integrity.json")
    pause = read_json(args.output_root / "pause-state.json")
    precommit = read_json(args.output_root / "diagnostic-precommit.json")
    fixture = read_json(args.output_root / "fixture-audit.json")
    cli = read_json(args.output_root / "cli-identity.json")
    baseline = read_json(args.output_root / "historical-baseline-facts.json")
    guard = read_json(args.output_root / "workload-guard-audit.json")
    completion = completion_document(args=args)
    results = aggregate["per_call_results"]

    repository_proof = {
        "contract": "diagnostic-repository-input-pause-proof-v1",
        "base_sha": state["base_sha"],
        "work_instruction_commit": state["work_instruction_commit"],
        "implementation_commit": state["implementation_commit"],
        "branch": state["branch"],
        "input_integrity": integrity,
        "initial_pause_observation": pause,
        "completion_pause_observation": observe_pause_state(),
        "scheduler_mutation_count": 0,
        "auto_resume_executed": 0,
        "status": "PASS",
    }
    repository_md = f"""# Repository, Input Integrity, and Pause

The indexed historical baseline passed SHA, membership, hash, size, path, and CRC checks. The eight monitoring schedule objects remained paused; this diagnostic did not mutate or resume them.

- Branch: `{state["branch"]}`
- Base: `{state["base_sha"]}`
- Work instruction: `{state["work_instruction_commit"]}`
- Implementation: `{state["implementation_commit"]}`
- Input ZIP SHA-256: `{integrity["input_zip_sha256"]}`
- Initial pause observation: `{pause["observed_at"]}`
"""

    fixture_proof = {
        "contract": "diagnostic-fixture-precommit-budget-proof-v1",
        "fixture_audit": fixture,
        "precommit": precommit,
        "budget": {
            "planned": MAX_CALLS,
            "consumed": aggregate["consumed_subprocess_call_budget"],
            "unattempted": aggregate["unattempted_calls_and_reasons"],
            "wrapper_retries": 0,
        },
        "status": "PASS",
    }
    fixture_md = f"""# Fixed Fixture, Precommit, and Budget

The request used four invented US-routed subjects with synthetic source identities. Prompt, schema, subject order, model, effort, timeout, call order, and three distinct namespaces were frozen before call 1.

- Generation: `{state["diagnostic_generation_id"]}`
- Prompt bytes: `{precommit["prompt_bytes"]}` (historical Core request: 17,940)
- Prompt SHA-256: `{precommit["prompt_sha256"]}`
- Schema SHA-256: `{precommit["schema_sha256"]}`
- Precommit SHA-256: `{precommit["precommit_sha256"]}`
- Budget: {aggregate["consumed_subprocess_call_budget"]} / {MAX_CALLS} subprocess calls consumed
"""

    observer_proof = {
        "contract": "diagnostic-observer-preflight-tests-proof-v1",
        "observer_backend": PausedScheduleProcessObserver().backend,
        "guard_audit": guard,
        "cli_identity": cli,
        "implementation_hashes": state["implementation_hashes"],
        "validation_before_freeze": precommit["validation_before_freeze"],
        "canonical_transport_mutation": 0,
        "status": "PASS",
    }
    observer_md = f"""# Observer, Exact-Path Preflight, and Tests

The diagnostic combined the exact paused-schedule registry with process-marker and Codex runtime-state observations. Each permitted call passed the existing identity binding before transport, and the unchanged adapter retained the sole 1,800-second watchdog.

- CLI: `{cli["version"]}` / `{cli["sha256"]}`
- Observer: `{PausedScheduleProcessObserver().backend}`
- Focused tests: `{precommit["validation_before_freeze"]["focused"]}`
- Full tests: `{precommit["validation_before_freeze"]["full_pytest"]}`
- Ruff: `{precommit["validation_before_freeze"]["ruff"]}`
- Diff check: `{precommit["validation_before_freeze"]["diff_check"]}`
"""

    attempt_proof = {
        "contract": "diagnostic-per-attempt-results-v1",
        "results": results,
        "stop_reason": aggregate["stop_reason"],
        "status": aggregate["diagnostic_execution_status"],
    }
    attempt_md = (
        "# Per-Attempt Results\n\n"
        + _attempt_table(results)
        + (
            "\nEvery attempted subprocess consumed budget. No wrapper relaunch or fourth call was permitted.\n"
        )
    )

    aggregate_proof = {
        **aggregate,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "cli_identity": cli,
        "configured_timeout_seconds": TIMEOUT_SECONDS,
        "timeout_owner_count": TIMEOUT_OWNER_COUNT,
    }
    aggregate_md = f"""# Aggregate Lifecycle, Retry, and Session Comparison

- Execution: `{aggregate["diagnostic_execution_status"]}`
- WebSocket disconnect signals: {aggregate["observed_websocket_disconnect_signal_count"]}
- CLI retry signals: {aggregate["observed_cli_retry_signal_count"]}
- Disconnect then success: {aggregate["disconnect_followed_by_success_count"]}
- Disconnect then watchdog timeout: {aggregate["disconnect_followed_by_timeout_count"]}
- Distinct observed sessions: {aggregate["session_identity_count"]}
- Distinct observed namespace hashes: {aggregate["distinct_namespace_count"]}
- Root cause confirmed: `false`
- Runtime reliability: `NOT_ESTABLISHED`

Observed CLI retry signals do not reveal upstream request-attempt or acceptance counts; both remain unknown/unavailable.
"""

    historical_proof = {
        "contract": "diagnostic-historical-scope-quality-carry-forward-v1",
        "historical": baseline,
        "new_probe_scope": {
            "fictional_subjects": list(SUBJECTS),
            "real_issuer_calls": 0,
            "historical_b_or_c_resumed": 0,
            "fills_missing_historical_runs": False,
        },
        "formal_stability_status": "NOT_MEASURED",
        "formal_generalization_status": "NOT_ESTABLISHED",
        "status": "PASS_SCOPE_PRESERVED",
    }
    historical_md = """# Historical Scope and Open Quality Findings

Historical FIRST and A hard ownership/renderer/safety gates remain PASS. B remains a timeout with no usable output and C remains not run. This fictional transport probe neither fills B/C nor establishes formal stability or generalization.

The historical message-quality findings also remain open: FIRST failed with 14 repeated substantive spans and A failed with 9. Those are span counts, not issuer-failure counts, and transport outcomes do not resolve them.
"""

    production_proof = {
        "contract": "diagnostic-production-no-change-proof-v1",
        "new_real_issuer_model_calls": 0,
        "new_market_financial_source_fetch_calls": 0,
        "historical_b_or_c_resumed": 0,
        "scheduler_mutation_count": 0,
        "auto_resume_executed": 0,
        "natural_live_cancel_count": 0,
        "production_db_mutation": 0,
        "production_send": 0,
        "production_deployment": 0,
        "stock_registration_change": 0,
        "night_futures_change": 0,
        "paid_data_service_change": 0,
        "new_free_api_management_gate": 0,
        "canonical_transport_mutation": 0,
        "cli_or_protocol_change": 0,
        "timeout_increase": 0,
        "status": "PASS_ZERO_PRODUCTION_CHANGE",
    }
    production_md = """# Production and Operational No-Change Proof

No real issuer was sent to the model. No source was fetched, no historical B/C context was resumed, and no scheduler, database, registration, delivery, deployment, Night Futures, billing, credential, CLI, protocol, timeout, or canonical transport setting changed.
"""

    completion_md = f"""# Program Completion

The bounded diagnostic ended with `{completion["diagnostic_execution_status"]}` after consuming {completion["consumed_subprocess_call_budget"]} of 3 authorized fictional subprocess calls.

- Disconnect observed: `{completion["disconnect_observed"]}`
- Reconnect path: `{completion["reconnect_path_exercised"]}`
- Historical failure reproduced: `{completion["historical_failure_reproduced_in_this_probe"]}`
- Runtime root cause: `UNRESOLVED`
- Runtime reliability: `NOT_ESTABLISHED`
- Formal proof: `INCOMPLETE`
- Status: `{completion["status"]}`
- Stop reason: `{completion["stop_reason"]}`

This result is a small runtime observation only. It does not establish production reliability or complete FIRST/A/B/C generalization.
"""
    return {
        REPORT_NAMES[0]: (repository_proof, repository_md),
        REPORT_NAMES[1]: (fixture_proof, fixture_md),
        REPORT_NAMES[2]: (observer_proof, observer_md),
        REPORT_NAMES[3]: (attempt_proof, attempt_md),
        REPORT_NAMES[4]: (aggregate_proof, aggregate_md),
        REPORT_NAMES[5]: (historical_proof, historical_md),
        REPORT_NAMES[6]: (production_proof, production_md),
        REPORT_NAMES[7]: (completion, completion_md),
    }


def write_reports(args: argparse.Namespace) -> dict[str, object]:
    args.report_dir.mkdir(parents=True, exist_ok=True)
    documents = _report_documents(args)
    for name, (proof, markdown) in documents.items():
        write_json(args.report_dir / f"{name}.json", proof)
        write_text(args.report_dir / f"{name}.md", markdown)
    return {
        "report_count": len(documents) * 2,
        "report_dir": str(args.report_dir),
        "status": "PASS",
    }


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file():
            _copy_file(path, destination / path.relative_to(source))


def _artifact_index(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.relative_to(root).as_posix() == "artifact-index.json":
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
            }
        )
    return {
        "contract": "indexed-evidence-bundle-v1",
        "index_self_exclusion": "artifact-index.json",
        "rows": rows,
        "indexed_payload_count": len(rows),
    }


def verify_output_zip(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sum(count > 1 for count in Counter(names).values())
        unsafe = [
            name
            for name in names
            if name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts
        ]
        crc_failure = archive.testzip()
        index = zip_json(archive, "artifact-index.json")
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("output_artifact_index_rows_missing")
        indexed = {
            str(row["path"]): row for row in rows if isinstance(row, Mapping) and row.get("path")
        }
        payloads = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        secret_matches = 0
        for name in sorted(payloads & set(indexed)):
            payload = archive.read(name)
            hash_mismatches += sha256_bytes(payload) != indexed[name].get("sha256")
            size_mismatches += len(payload) != indexed[name].get("byte_size")
            secret_matches += scan_bytes(payload)
        membership_mismatches = len(payloads ^ set(indexed))
    checks = {
        "duplicate_members": duplicates == 0,
        "safe_paths": not unsafe,
        "crc": crc_failure is None,
        "index_membership": membership_mismatches == 0,
        "hashes": hash_mismatches == 0,
        "sizes": size_mismatches == 0,
        "secret_scan": secret_matches == 0,
    }
    return {
        "zip_sha256": file_sha256(path),
        "zip_member_count": len(names),
        "indexed_payload_count": len(rows),
        "duplicate_member_count": duplicates,
        "unsafe_path_count": len(unsafe),
        "crc_failure": crc_failure,
        "artifact_hash_mismatch_count": hash_mismatches,
        "artifact_size_mismatch_count": size_mismatches,
        "artifact_membership_mismatch_count": membership_mismatches,
        "secret_match_count": secret_matches,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def package(args: argparse.Namespace) -> dict[str, object]:
    report_files = [
        args.report_dir / f"{name}.{suffix}" for name in REPORT_NAMES for suffix in ("json", "md")
    ]
    missing = [str(path) for path in report_files if not path.is_file()]
    if missing:
        raise ValueError(f"required_reports_missing:{','.join(missing)}")
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "EXECUTION_COMPLETE":
        raise DiagnosticStop("cannot_package_incomplete_execution")

    with tempfile.TemporaryDirectory(prefix="fictional-websocket-bundle-") as temp_name:
        root = Path(temp_name) / "bundle"
        root.mkdir()
        for path in report_files:
            _copy_file(path, root / "reports" / path.name)
        experiment_files = (
            "baseline-integrity.json",
            "pause-state.json",
            "cli-identity.json",
            "fixture-audit.json",
            "historical-baseline-facts.json",
            "source-lock.json",
            "diagnostic-precommit.json",
            "program-state.json",
            "workload-guard-audit.json",
            "aggregate-result.json",
        )
        for name in experiment_files:
            _copy_file(args.output_root / name, root / "experiment" / name)
        _copy_tree(args.output_root / "fixture", root / "experiment" / "fixture")
        _copy_tree(
            args.output_root / "diagnostic-contexts",
            root / "experiment" / "diagnostic-contexts",
        )
        with zipfile.ZipFile(args.baseline_zip) as archive:
            for member in HISTORICAL_MEMBERS:
                destination = root / "historical-baseline" / member
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(member))
        write_text(
            root / "README.md",
            """# Bounded Fictional WebSocket Reconnect Observability Diagnostic

This bundle contains a maximum-three-call fictional transport observation, its frozen inputs, exact safe attempt artifacts, eight compact reports, and only the selected historical comparison proofs needed to interpret the result.

It contains no new real-issuer model call, no market-data fetch, no scheduler resume, and no production delivery or deployment. A clean bounded result does not establish runtime reliability or formal investment generalization.
""",
        )
        provisional = completion_document(args=args)
        write_json(root / "completion.json", provisional)
        payload_count = sum(
            path.is_file() and path.name != "artifact-index.json" for path in root.rglob("*")
        )
        completion = completion_document(
            args=args,
            indexed_payload_count=payload_count,
            zip_member_count=payload_count + 1,
        )
        write_json(root / "completion.json", completion)
        index = _artifact_index(root)
        if index["indexed_payload_count"] != payload_count:
            raise ValueError("package_payload_count_drift")
        write_json(root / "artifact-index.json", index)
        if any(scan_path(path) for path in root.rglob("*") if path.is_file()):
            raise DiagnosticStop("secret_scan_failure_before_package")
        args.zip_path.parent.mkdir(parents=True, exist_ok=True)
        args.zip_path.unlink(missing_ok=True)
        with zipfile.ZipFile(
            args.zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root).as_posix())
    verification = verify_output_zip(args.zip_path)
    if verification["status"] != "PASS":
        raise DiagnosticStop("output_zip_verification_failure")
    sidecar = args.zip_path.with_suffix(args.zip_path.suffix + ".sha256")
    write_text(sidecar, f"{verification['zip_sha256']}  {args.zip_path.name}")
    return {**verification, "zip_path": str(args.zip_path), "sidecar": str(sidecar)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=PROGRAM_CONTRACT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--output-root", type=Path, required=True)
        subparser.add_argument("--baseline-zip", type=Path, required=True)

    prepare_parser = subparsers.add_parser("prepare")
    common(prepare_parser)
    prepare_parser.add_argument("--focused-result", required=True)
    prepare_parser.add_argument("--full-result", required=True)
    prepare_parser.add_argument("--ruff-result", required=True)
    prepare_parser.add_argument("--diff-result", required=True)

    execute_parser = subparsers.add_parser("execute")
    common(execute_parser)

    report_parser = subparsers.add_parser("report")
    common(report_parser)
    report_parser.add_argument("--report-dir", type=Path, required=True)

    package_parser = subparsers.add_parser("package")
    common(package_parser)
    package_parser.add_argument("--report-dir", type=Path, required=True)
    package_parser.add_argument("--zip-path", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "prepare":
        result = prepare(args)
    elif args.command == "execute":
        result = execute(args)
    elif args.command == "report":
        result = write_reports(args)
    elif args.command == "package":
        result = package(args)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
