from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.direction_timing_ownership_service import (
    DirectionalCoreCandidate,
    PriceTimingCandidate,
)
from app.services.structured_autonomy_shadow_service import (
    render_structured_autonomy_message,
    structured_autonomy_message_quality,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import experiment_report_closeout_contract as report_closeout
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import runtime_identity_binding as runtime_identity


PROGRAM_CONTRACT = "websocket-timeout-runtime-review-first-a-closeout-v1"
INPUT_ZIP_SHA256 = "3b957ec1e2257832fa8fc531ae883e4f0c9f8228449b6f0d78fbbbd9fe1e7309"
INPUT_MEMBER_COUNT = 1165
INPUT_INDEXED_PAYLOAD_COUNT = 1164
PREVIOUS_INSTRUCTION_ZIP_SHA256 = "899518ffca1ba67e3f11049e2a660d802e759a0b73a0140c7001010651511eb9"
CURRENT_INSTRUCTION_ZIP_SHA256 = "dcf456c73abe143c559aaa3f50f8447fe2b6a1066d4e4c640e2c646fbc49faf4"
SOURCE_GENERATION_ID = "20260907-fresh-issuer-source-20260907T090500Z-2b1e0d043243"
RUNTIME_GENERATION_ID = "20260907-fresh-issuer-proof-20260907T090500Z-2fc43e587bfe"
SOURCE_LOCK_SHA256 = "eee5764bb11218ab080a65ac6179e7b5d6440be11753ce34f8cd292ffc2504ef"
COHORT = (
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
REPORT_DIRECTORY = "20260907-websocket-timeout-runtime-review-first-a-evidence-closeout"
REPORT_NAMES = (
    "01-input-integrity-and-repository-provenance",
    "02-pause-state-and-historical-transition",
    "03-first-a-b-c-execution-reconciliation",
    "04-b-lifecycle-timeline",
    "05-first-a-b-request-session-comparison",
    "06-retry-observability-and-classification",
    "07-reporting-contract-repair",
    "08-exposure-retirement-measurement-mapping",
    "09-offline-first-a-lineage-and-gate-audit",
    "10-first-a-descriptive-differences",
    "11-message-quality-scope-and-original-export",
    "12-program-completion",
)
RUN_SUMMARY_MEMBERS = {
    "first": "reports/proofs/27-first-execution-summary.json",
    "a": "reports/proofs/33-run-a-execution-summary.json",
}
RUN_GATE_MEMBERS = {
    "first": {
        "ownership": "reports/proofs/30-first-run-ownership-gate.json",
        "renderer": "reports/proofs/31-first-run-renderer-gate.json",
        "hard": "reports/proofs/32-first-run-hard-safety-gate.json",
    },
    "a": {
        "ownership": "reports/proofs/36-run-a-ownership-gate.json",
        "renderer": "reports/proofs/37-run-a-renderer-gate.json",
        "hard": "reports/proofs/38-run-a-hard-safety-gate.json",
    },
}
RUNTIME_EVENT_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T[^ ]+Z)\s+"
    r"(?P<level>WARN|ERROR)\s+(?P<target>[A-Za-z0-9_:]+):\s*(?P<message>.*)$"
)
SESSION_ID_RE = re.compile(r"^session id:\s*([0-9a-f]{8}-[0-9a-f-]{27,})\s*$", re.MULTILINE)
SECRET_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"Bearer[ \t]+[A-Za-z0-9._~+/-]{16,}", re.IGNORECASE),
    re.compile(
        rb"(?:API[_-]?KEY|ACCESS[_-]?TOKEN|PASSWORD|SECRET)[ \t]*[:=][ \t]*[^\s]{8,}",
        re.IGNORECASE,
    ),
    re.compile(rb"\d{8,10}:[A-Za-z0-9_-]{25,}"),
)


@dataclass(frozen=True)
class RuntimeEvent:
    timestamp: str
    level: str
    target: str
    message: str


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


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(("git", *args), check=True, capture_output=True, text=True).stdout.strip()


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def verify_input_bundle(path: Path) -> dict[str, object]:
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
            raise ValueError("artifact_index_rows_missing")
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
        missing_from_index = payload_names - set(indexed)
        missing_from_payload = set(indexed) - payload_names
    checks = {
        "input_zip_sha256": actual_sha == INPUT_ZIP_SHA256,
        "member_count": len(names) == INPUT_MEMBER_COUNT,
        "indexed_payload_count": len(rows) == INPUT_INDEXED_PAYLOAD_COUNT,
        "duplicate_members": duplicate_count == 0,
        "safe_paths": not unsafe,
        "crc": bad_member is None,
        "index_membership": not missing_from_index and not missing_from_payload,
        "hashes": hash_mismatches == 0,
        "sizes": size_mismatches == 0,
    }
    if not all(checks.values()):
        failed = ",".join(key for key, passed in checks.items() if not passed)
        raise ValueError(f"historical_input_integrity_failure:{failed}")
    return {
        "contract": "historical-input-integrity-v1",
        "input_zip_sha256": actual_sha,
        "input_member_count": len(names),
        "input_indexed_payload_count": len(rows),
        "duplicate_member_count": duplicate_count,
        "unsafe_path_count": len(unsafe),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "missing_from_index_count": len(missing_from_index),
        "missing_from_payload_count": len(missing_from_payload),
        "checks": checks,
        "status": "PASS",
    }


def extract_runtime_events(stderr_text: str) -> tuple[RuntimeEvent, ...]:
    events = []
    for line in stderr_text.splitlines():
        match = RUNTIME_EVENT_RE.match(line)
        if match is None:
            continue
        events.append(RuntimeEvent(**match.groupdict()))
    return tuple(events)


def classify_runtime_receipt(receipt: Mapping[str, object], stderr_text: str) -> dict[str, object]:
    events = extract_runtime_events(stderr_text)
    retry_events = [
        event
        for event in events
        if event.target == "codex_core::responses_retry"
        and "retrying sampling request" in event.message.casefold()
    ]
    websocket_events = [
        event
        for event in events
        if "websocket" in event.message.casefold()
        or "stream disconnected" in event.message.casefold()
    ]
    capacity_events = [
        event
        for event in events
        if any(
            marker in event.message.casefold()
            for marker in (
                "model capacity",
                "insufficient capacity",
                "capacity exhausted",
            )
        )
    ]
    context_events = [
        event
        for event in events
        if any(
            marker in event.message.casefold()
            for marker in (
                "context_length_exceeded",
                "maximum context length",
                "context window exceeded",
            )
        )
    ]
    status = str(receipt.get("status") or "UNKNOWN")
    pre_spawn = status == "SPAWN_FAILED" or receipt.get("child_cleanup_status") == (
        "NO_CHILD_SPAWNED"
    )
    timed_out = status == "TIMEOUT" or receipt.get("termination_initiator") == (
        "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG"
    )
    if pre_spawn:
        classification = "PRESPAWN_FAILURE"
    elif context_events:
        classification = "EXPLICIT_CONTEXT_LENGTH_DIAGNOSTIC"
    elif capacity_events:
        classification = "EXPLICIT_CAPACITY_DIAGNOSTIC"
    elif timed_out and websocket_events:
        classification = "WATCHDOG_TRANSPORT_TIMEOUT_AFTER_WEBSOCKET_DISCONNECT"
    elif timed_out:
        classification = "WATCHDOG_TRANSPORT_TIMEOUT_CAUSE_UNRESOLVED"
    elif status == "PASS" and retry_events:
        classification = "PASS_WITH_WARNING"
    elif receipt.get("parse_error") == "OUTPUT_FILE_MISSING":
        classification = "OUTPUT_MISSING_CAUSE_UNRESOLVED"
    elif status == "PASS":
        classification = "PASS"
    else:
        classification = "PROCESS_FAILURE_CAUSE_UNRESOLVED"
    return {
        "classification": classification,
        "runtime_event_count": len(events),
        "observed_cli_retry_signal_count": len(retry_events),
        "observed_websocket_disconnect_signal_count": len(websocket_events),
        "explicit_capacity_diagnostic_count": len(capacity_events),
        "explicit_context_length_diagnostic_count": len(context_events),
        "wrapper_explicit_retry_count": int(receipt.get("retry_count") or 0),
        "upstream_request_attempt_count": "UNKNOWN",
        "upstream_accepted_request_count": "UNKNOWN",
        "request_accepted_observability": receipt.get(
            "request_accepted_observability", "UNAVAILABLE"
        ),
        "safe_runtime_events": [
            {
                "timestamp": event.timestamp,
                "level": event.level,
                "target": event.target,
                "message": event.message,
            }
            for event in events
        ],
    }


def _resolve_ref(schema: Mapping[str, object], root: Mapping[str, object]) -> Mapping[str, object]:
    reference = schema.get("$ref")
    if not isinstance(reference, str):
        return schema
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported_external_schema_ref:{reference}")
    value: object = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or token not in value:
            raise ValueError(f"unresolved_schema_ref:{reference}")
        value = value[token]
    if not isinstance(value, Mapping):
        raise ValueError(f"schema_ref_not_object:{reference}")
    return value


def validate_json_schema(
    instance: object,
    schema: Mapping[str, object],
    *,
    root: Mapping[str, object] | None = None,
    path: str = "$",
) -> list[str]:
    root = root or schema
    if "$ref" in schema:
        return validate_json_schema(instance, _resolve_ref(schema, root), root=root, path=path)
    if "anyOf" in schema:
        alternatives = schema["anyOf"]
        if not isinstance(alternatives, list):
            return [f"{path}:anyOf_not_array"]
        results = [
            validate_json_schema(instance, item, root=root, path=path)
            for item in alternatives
            if isinstance(item, Mapping)
        ]
        if any(not errors for errors in results):
            return []
        return [f"{path}:no_anyOf_match"]

    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}:const_mismatch")
    enum = schema.get("enum")
    if isinstance(enum, list) and instance not in enum:
        errors.append(f"{path}:enum_mismatch")
    expected_type = schema.get("type")
    type_ok = True
    if expected_type == "object":
        type_ok = isinstance(instance, Mapping)
    elif expected_type == "array":
        type_ok = isinstance(instance, list)
    elif expected_type == "string":
        type_ok = isinstance(instance, str)
    elif expected_type == "integer":
        type_ok = isinstance(instance, int) and not isinstance(instance, bool)
    elif expected_type == "number":
        type_ok = isinstance(instance, (int, float)) and not isinstance(instance, bool)
    elif expected_type == "boolean":
        type_ok = isinstance(instance, bool)
    elif expected_type == "null":
        type_ok = instance is None
    if expected_type is not None and not type_ok:
        return [f"{path}:type_mismatch:{expected_type}"]

    if isinstance(instance, Mapping):
        required = schema.get("required")
        if isinstance(required, list):
            errors.extend(
                f"{path}:missing_required:{key}" for key in required if key not in instance
            )
        properties = schema.get("properties")
        if isinstance(properties, Mapping):
            if schema.get("additionalProperties") is False:
                errors.extend(
                    f"{path}:additional_property:{key}" for key in instance if key not in properties
                )
            for key, value in instance.items():
                child = properties.get(key)
                if isinstance(child, Mapping):
                    errors.extend(
                        validate_json_schema(value, child, root=root, path=f"{path}.{key}")
                    )
    elif isinstance(instance, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if isinstance(minimum, int) and len(instance) < minimum:
            errors.append(f"{path}:minItems:{minimum}")
        if isinstance(maximum, int) and len(instance) > maximum:
            errors.append(f"{path}:maxItems:{maximum}")
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, value in enumerate(instance):
                errors.extend(
                    validate_json_schema(value, item_schema, root=root, path=f"{path}[{index}]")
                )
    elif isinstance(instance, str):
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if isinstance(minimum, int) and len(instance) < minimum:
            errors.append(f"{path}:minLength:{minimum}")
        if isinstance(maximum, int) and len(instance) > maximum:
            errors.append(f"{path}:maxLength:{maximum}")
    return errors


def _context_paths(root: Path) -> list[Path]:
    return sorted((root / "experiment" / "model-contexts").rglob("transport_receipt.json"))


def _run_from_context(path: Path) -> str:
    return path.parents[2].name.lower()


def _stage_from_context(path: Path) -> str:
    return path.parents[1].name


def _batch_from_context(path: Path) -> str:
    return path.parent.name.removeprefix("batch-")


def _receipt_timing(receipt: Mapping[str, object], field: str) -> float | None:
    value = receipt.get(field)
    start = receipt.get("invocation_start_monotonic")
    if not isinstance(value, (int, float)) or not isinstance(start, (int, float)):
        return None
    return round(float(value) - float(start), 6)


def reconcile_executions(root: Path) -> dict[str, object]:
    receipts = []
    sessions: list[str] = []
    for path in _context_paths(root):
        receipt = read_json(path)
        stderr_path = path.parent / "stderr.raw.log"
        stderr_text = stderr_path.read_text(encoding="utf-8") if stderr_path.is_file() else ""
        sessions.extend(SESSION_ID_RE.findall(stderr_text))
        receipts.append(
            {
                "run": _run_from_context(path),
                "stage": _stage_from_context(path),
                "batch": _batch_from_context(path),
                "status": receipt.get("status"),
                "invocation_id": receipt.get("invocation_id"),
                "session_id": SESSION_ID_RE.findall(stderr_text)[0]
                if SESSION_ID_RE.findall(stderr_text)
                else None,
                "output_bytes": receipt.get("output_bytes"),
                "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
            }
        )
    status_counts = Counter(str(row["status"]) for row in receipts)
    stage_attempts = Counter(str(row["stage"]) for row in receipts)
    stage_successes = Counter(str(row["stage"]) for row in receipts if row["status"] == "PASS")
    raw_files = sorted((root / "experiment" / "model-contexts").rglob("output.raw.json"))
    raw_stage_rows = sum(len(read_json(path).get("candidates") or []) for path in raw_files)
    raw_exposed = {
        str(candidate.get("ticker"))
        for path in raw_files
        for candidate in read_json(path).get("candidates") or []
        if isinstance(candidate, Mapping)
    }
    summaries = {run: read_json(root / member) for run, member in RUN_SUMMARY_MEMBERS.items()}
    composed_rows = sum(len(document.get("rows") or []) for document in summaries.values())
    result = {
        "contract": "first-a-b-c-execution-reconciliation-v1",
        "attempted_contexts": len(receipts),
        "terminal_receipts": len(receipts),
        "successful_output_contexts": status_counts["PASS"],
        "failed_contexts": len(receipts) - status_counts["PASS"],
        "core_attempts": stage_attempts["DIRECTIONAL_CORE"],
        "core_successes": stage_successes["DIRECTIONAL_CORE"],
        "timing_attempts": stage_attempts["PRICE_TIMING"],
        "timing_successes": stage_successes["PRICE_TIMING"],
        "successful_raw_output_files": len(raw_files),
        "successful_stage_rows": raw_stage_rows,
        "unique_exposed_issuers": len(raw_exposed),
        "unique_exposed_tickers": sorted(raw_exposed),
        "deterministic_composed_rows": composed_rows,
        "rendered_message_rows": composed_rows,
        "recorded_session_id_count": len(sessions),
        "distinct_session_id_count": len(set(sessions)),
        "runs": {
            "FIRST": "16/16",
            "A": "16/16",
            "B": "FAILED_0/16",
            "C": "NOT_RUN",
        },
        "receipts": receipts,
        "status": "PASS",
    }
    expected = {
        "attempted_contexts": 17,
        "terminal_receipts": 17,
        "successful_output_contexts": 16,
        "failed_contexts": 1,
        "core_attempts": 9,
        "core_successes": 8,
        "timing_attempts": 8,
        "timing_successes": 8,
        "successful_raw_output_files": 16,
        "successful_stage_rows": 64,
        "unique_exposed_issuers": 16,
        "deterministic_composed_rows": 32,
        "rendered_message_rows": 32,
        "recorded_session_id_count": 17,
        "distinct_session_id_count": 17,
    }
    mismatches = {
        key: {"expected": value, "actual": result[key]}
        for key, value in expected.items()
        if result[key] != value
    }
    result["expected_count_mismatches"] = mismatches
    result["status"] = "PASS" if not mismatches else "FAIL"
    return result


def b_lifecycle(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    context = root / "experiment/model-contexts/B/DIRECTIONAL_CORE/batch-01"
    receipt = read_json(context / "transport_receipt.json")
    stderr_text = (context / "stderr.raw.log").read_text(encoding="utf-8")
    classification = classify_runtime_receipt(receipt, stderr_text)
    last_stderr = _receipt_timing(receipt, "last_stderr_byte_monotonic")
    elapsed = receipt.get("elapsed_to_exit_seconds")
    silence = (
        round(float(elapsed) - last_stderr, 6)
        if isinstance(elapsed, (int, float)) and isinstance(last_stderr, float)
        else None
    )
    runtime_events = classification["safe_runtime_events"]
    safe_excerpt = runtime_events[-1] if runtime_events else None
    lifecycle = {
        "contract": "b-transport-lifecycle-reconstruction-v1",
        "invocation_id": receipt.get("invocation_id"),
        "started_at": receipt.get("started_at"),
        "completed_at": receipt.get("completed_at"),
        "configured_timeout_seconds": receipt.get("configured_timeout_seconds"),
        "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
        "exit_code": receipt.get("exit_code"),
        "output_bytes": receipt.get("output_bytes"),
        "stdout_bytes": receipt.get("stdout_bytes"),
        "output_parsed": receipt.get("output_parsed"),
        "parse_error": receipt.get("parse_error"),
        "termination_initiator": receipt.get("termination_initiator"),
        "termination_signal": receipt.get("termination_signal"),
        "timeout_owner_count": receipt.get("timeout_owner_count"),
        "duplicate_timeout_receipt_count": receipt.get("duplicate_timeout_receipt_count"),
        "orphan_model_process_count": receipt.get("orphan_model_process_count"),
        "child_cleanup_status": receipt.get("child_cleanup_status"),
        "request_accepted_observability": receipt.get("request_accepted_observability"),
        "last_stderr_after_start_seconds": last_stderr,
        "silence_until_exit_seconds": silence,
        "safe_error_excerpt": safe_excerpt,
        "output_file_missing_interpretation": "DOWNSTREAM_OBSERVATION_NOT_ROOT_CAUSE",
        "transport_root_cause_confirmed": False,
        "exact_remote_local_cause": "UNRESOLVED",
        "status": "PASS",
    }
    retry = {
        "contract": "wrapper-cli-retry-observability-v1",
        **classification,
        "capacity_diagnostic_status": (
            "PROVEN"
            if classification["explicit_capacity_diagnostic_count"]
            else "NOT_PROVEN_NO_EXPLICIT_DIAGNOSTIC_OBSERVED"
        ),
        "historical_stall_pattern": {
            "watchdog_1800_second_timeout_recurred": True,
            "exact_startup_only_silent_trace_recurred": False,
            "this_incident_has_explicit_websocket_disconnect_warning": True,
        },
        "unresolved_hypotheses": [
            "remote backend response stalled after CLI reconnect attempt",
            "WebSocket reconnect path failed to produce a terminal response",
            "other unobserved upstream or local transport condition",
        ],
        "status": "PASS",
    }
    return lifecycle, retry


def compare_core01(root: Path) -> dict[str, object]:
    rows = []
    for run in ("FIRST", "A", "B"):
        context = root / f"experiment/model-contexts/{run}/DIRECTIONAL_CORE/batch-01"
        receipt = read_json(context / "transport_receipt.json")
        prompt = (context / "prompt.txt").read_bytes()
        schema = (context / "schema.json").read_bytes()
        stderr_text = (context / "stderr.raw.log").read_text(encoding="utf-8")
        sessions = SESSION_ID_RE.findall(stderr_text)
        metadata = receipt.get("transport_metadata")
        metadata = metadata if isinstance(metadata, Mapping) else {}
        rows.append(
            {
                "run": run,
                "status": receipt.get("status"),
                "subjects": read_json(context / "context_manifest.json").get("subjects"),
                "prompt_sha256": sha256_bytes(prompt),
                "schema_sha256": sha256_bytes(schema),
                "input_bytes": len(prompt),
                "model": receipt.get("model"),
                "reasoning_effort": receipt.get("reasoning_effort"),
                "cli_version": receipt.get("cli_version"),
                "cli_binary_sha256": (receipt.get("cli_binary_identity") or {}).get("sha256"),
                "session_id": sessions[0] if sessions else None,
                "runtime_state_namespace_hash": metadata.get("runtime_state_namespace_hash"),
                "network_probe_contract": metadata.get("network_probe_contract"),
                "network_probe_attempts": metadata.get("network_probe_attempts"),
                "network_resolved_address_count": metadata.get("network_resolved_address_count"),
                "tls_trust_source": metadata.get("tls_trust_source"),
                "output_bytes": receipt.get("output_bytes"),
                "stdout_bytes": receipt.get("stdout_bytes"),
                "stderr_bytes": receipt.get("stderr_bytes"),
                "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
                "exit_code": receipt.get("exit_code"),
                "child_cleanup_status": receipt.get("child_cleanup_status"),
            }
        )
    identity_fields = (
        "subjects",
        "prompt_sha256",
        "schema_sha256",
        "input_bytes",
        "model",
        "reasoning_effort",
        "cli_version",
        "cli_binary_sha256",
        "network_probe_contract",
        "tls_trust_source",
    )
    identical = {
        field: len({json.dumps(row[field], sort_keys=True) for row in rows}) == 1
        for field in identity_fields
    }
    sessions = [str(row["session_id"]) for row in rows]
    namespaces = [str(row["runtime_state_namespace_hash"]) for row in rows]
    return {
        "contract": "first-a-b-core01-runtime-comparison-v1",
        "rows": rows,
        "identity_fields": identical,
        "all_prompt_schema_subject_configuration_fields_identical": all(identical.values()),
        "distinct_session_ids": len(set(sessions)),
        "distinct_runtime_state_namespaces": len(set(namespaces)),
        "identical_input_does_not_guarantee_identical_runtime_behavior": True,
        "unsupported_causal_conclusions": [
            "context_length_error",
            "capacity_error",
            "local_network_failure",
            "backend_outage",
        ],
        "status": "PASS",
    }


def _disabled_launch_agent_labels(value: str) -> set[str]:
    return {
        match.group(1) for match in re.finditer(r'"([^"\n]+)"\s*=>\s*(?:true|disabled)\b', value)
    }


def observe_pause_state() -> dict[str, object]:
    launch_labels = (
        "com.seungsoo.thesis-monitor.daily",
        "com.seungsoo.thesis-monitor.kr-close",
        "com.seungsoo.thesis-monitor.ai-review-fallback",
        "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
    )
    automation_names = (
        "Thesis Monitor AI Review US Primary",
        "Thesis Monitor AI Review US Backup",
        "Thesis Monitor AI Review KR Primary",
        "Thesis Monitor AI Review KR Backup",
    )
    observed_at = datetime.now(UTC).isoformat()
    try:
        uid = os.getuid()
        disabled_result = subprocess.run(
            ("launchctl", "print-disabled", f"gui/{uid}"),
            check=False,
            capture_output=True,
            text=True,
        )
        if disabled_result.returncode != 0:
            raise RuntimeError(f"launchctl_print_disabled_rc:{disabled_result.returncode}")
        disabled = _disabled_launch_agent_labels(disabled_result.stdout)
        launch_rows = []
        for label in launch_labels:
            result = subprocess.run(
                ("launchctl", "print", f"gui/{uid}/{label}"),
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 113 and label in disabled:
                state = "PAUSED_DISABLED_UNLOADED"
                active = False
            elif result.returncode == 0:
                match = re.search(r"^\s*state = ([^\r\n]+)", result.stdout, re.MULTILINE)
                runtime_state = match.group(1).strip() if match else "UNKNOWN"
                state = f"LOADED_{runtime_state.upper()}"
                active = runtime_state == "running"
            else:
                state = f"UNAVAILABLE_RC_{result.returncode}"
                active = None
            launch_rows.append({"name": label, "state": state, "active": active})

        automation_rows = []
        automation_root = Path.home() / ".codex" / "automations"
        found: dict[str, str] = {}
        for path in sorted(automation_root.glob("*/automation.toml")):
            try:
                document = tomllib.loads(path.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError):
                continue
            name = document.get("name")
            if isinstance(name, str) and name in automation_names:
                found[name] = str(document.get("status") or "UNKNOWN")
        for name in automation_names:
            status = found.get(name, "NOT_FOUND")
            if status == "PAUSED":
                active: bool | None = False
            elif status in {"NOT_FOUND", "UNKNOWN"}:
                active = None
            else:
                active = True
            automation_rows.append({"name": name, "state": status, "active": active})
        unexpected_active = [
            row["name"] for row in (*launch_rows, *automation_rows) if row["active"] is True
        ]
        all_observed = all(row["active"] is not None for row in (*launch_rows, *automation_rows))
        if unexpected_active:
            status = "UNEXPECTED_ACTIVE_AUTOMATIC_PATH"
        elif all_observed:
            status = "VERIFIED_PAUSED_COMPLETE"
        else:
            status = "CURRENT_STATE_NOT_VERIFIED"
        return {
            "contract": "current-monitoring-pause-observation-v1",
            "observed_at": observed_at,
            "launch_agents": launch_rows,
            "codex_automations": automation_rows,
            "observed_scheduler_object_count": len(launch_rows) + len(automation_rows),
            "unexpected_active_paths": unexpected_active,
            "observation_only": True,
            "scheduler_mutation_count": 0,
            "auto_resume_executed": 0,
            "status": status,
        }
    except (OSError, RuntimeError) as exc:
        return {
            "contract": "current-monitoring-pause-observation-v1",
            "observed_at": observed_at,
            "reason": f"{type(exc).__name__}:{exc}",
            "observation_only": True,
            "scheduler_mutation_count": 0,
            "auto_resume_executed": 0,
            "status": "CURRENT_STATE_NOT_VERIFIED",
        }


def _assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise ValueError(f"{message}:actual={actual!r}:expected={expected!r}")


def _validate_context_identity(
    context: Path,
    *,
    expected_subjects: Sequence[str],
) -> dict[str, object]:
    prompt = (context / "prompt.txt").read_bytes()
    schema_bytes = (context / "schema.json").read_bytes()
    schema = read_json(context / "schema.json")
    raw = read_json(context / "output.raw.json")
    receipt = read_json(context / "transport_receipt.json")
    manifest = read_json(context / "context_manifest.json")
    binding = runtime_identity.load_binding(context / "identity-binding-lock.json")
    receipt_identity = runtime_identity.validate_receipt_identity(receipt, binding)
    output_identity = runtime_identity.validate_output_identity(raw, binding)
    schema_errors = validate_json_schema(raw, schema)
    checks = {
        "prompt_receipt_hash": sha256_bytes(prompt) == receipt.get("prompt_sha256"),
        "schema_receipt_hash": sha256_bytes(schema_bytes) == receipt.get("schema_sha256"),
        "prompt_manifest_hash": sha256_bytes(prompt) == manifest.get("prompt_sha256"),
        "schema_manifest_hash": sha256_bytes(schema_bytes) == manifest.get("schema_sha256"),
        "raw_manifest_hash": file_sha256(context / "output.raw.json")
        == manifest.get("raw_output_sha256"),
        "raw_manifest_bytes": (context / "output.raw.json").stat().st_size
        == manifest.get("raw_output_bytes"),
        "subject_order": list(expected_subjects) == manifest.get("subjects"),
        "schema_validation": not schema_errors,
        "receipt_identity": receipt_identity.get("status") == "PASS",
        "output_identity": output_identity.get("status") == "PASS",
        "source_generation": manifest.get("source_generation_id") == SOURCE_GENERATION_ID,
        "runtime_generation": manifest.get("generation_id") == RUNTIME_GENERATION_ID,
        "source_lock": manifest.get("source_lock") == SOURCE_LOCK_SHA256,
    }
    return {
        "context": str(context.relative_to(context.parents[4])),
        "stage": manifest.get("stage"),
        "batch": manifest.get("batch_id"),
        "subjects": manifest.get("subjects"),
        "schema_errors": schema_errors,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def offline_first_a_audit(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    args = argparse.Namespace(output_root=root / "experiment")
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
    ) = runner.load_inputs(args)
    _assert_equal(cohort, COHORT, "cohort_drift")
    _assert_equal(state.get("program_generation_id"), RUNTIME_GENERATION_ID, "runtime_generation")
    _assert_equal(state.get("source_generation_id"), SOURCE_GENERATION_ID, "source_generation")

    run_results: dict[str, dict[str, object]] = {}
    message_exports: list[dict[str, object]] = []
    for run in ("first", "a"):
        run_dir = root / "experiment" / "model-contexts" / run.upper()
        summary = read_json(root / RUN_SUMMARY_MEMBERS[run])
        summary_rows = {
            str(row["ticker"]): row for row in summary.get("rows") or [] if isinstance(row, Mapping)
        }
        core_by_ticker: dict[str, DirectionalCoreCandidate] = {}
        context_checks = []
        core_audits = []
        timing_audits = []
        rebuilt_rows = []
        alias_selection_count = 0
        for number, batch in enumerate(frozen.batches(cohort), start=1):
            context = run_dir / "DIRECTIONAL_CORE" / f"batch-{number:02d}"
            context_checks.append(_validate_context_identity(context, expected_subjects=batch))
            raw = read_json(context / "output.raw.json")
            resolved, alias_audit = frozen._resolve_batch_candidates(
                raw.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=core_aliases,
                model_type=DirectionalCoreCandidate,
            )
            normalized = read_json(context / "output.normalized.json")
            normalized_rows = [row.model_dump(mode="json") for row in resolved]
            _assert_equal(
                normalized.get("candidates"),
                normalized_rows,
                f"core_normalized_drift:{run}:{number}",
            )
            alias_selection_count += sum(
                len(value.get("selections") or []) for value in alias_audit.values()
            )
            audit = runner.core_partial_audit(resolved, owned)
            saved_audit = read_json(context / "partial_semantic_audit.json")
            _assert_equal(audit, saved_audit, f"core_audit_drift:{run}:{number}")
            core_audits.append(audit)
            for row in resolved:
                core_by_ticker[row.ticker] = row
                _assert_equal(
                    summary_rows[row.ticker]["core"],
                    row.model_dump(mode="json"),
                    f"core_summary_lineage_drift:{run}:{row.ticker}",
                )

        for number, batch in enumerate(frozen.batches(cohort), start=1):
            context = run_dir / "PRICE_TIMING" / f"batch-{number:02d}"
            context_checks.append(_validate_context_identity(context, expected_subjects=batch))
            raw = read_json(context / "output.raw.json")
            resolved, alias_audit = frozen._resolve_batch_candidates(
                raw.get("candidates"),
                batch=batch,
                evidence=evidence,
                catalogs=timing_aliases,
                model_type=PriceTimingCandidate,
            )
            normalized = read_json(context / "output.normalized.json")
            normalized_rows = [row.model_dump(mode="json") for row in resolved]
            _assert_equal(
                normalized.get("candidates"),
                normalized_rows,
                f"timing_normalized_drift:{run}:{number}",
            )
            alias_selection_count += sum(
                len(value.get("selections") or []) for value in alias_audit.values()
            )
            audit, rows = runner.timing_partial_audit(
                rows=resolved,
                core_by_ticker=core_by_ticker,
                owned=owned,
                evidence=evidence,
                price_maps=price_maps,
                stocks=stocks,
                base_contexts=base_contexts,
            )
            saved_audit = read_json(context / "partial_semantic_audit.json")
            _assert_equal(audit, saved_audit, f"timing_audit_drift:{run}:{number}")
            timing_audits.append(audit)
            rebuilt_rows.extend(rows)

        rebuilt_rows.sort(key=lambda row: cohort.index(str(row["ticker"])))
        _assert_equal(
            rebuilt_rows,
            summary.get("rows"),
            f"run_summary_lineage_drift:{run}",
        )
        ownership, renderer, hard = runner.run_gate_documents(run, rebuilt_rows)
        rerun_gates = {"ownership": ownership, "renderer": renderer, "hard": hard}
        for gate, document in rerun_gates.items():
            saved = read_json(root / RUN_GATE_MEMBERS[run][gate])
            _assert_equal(document, saved, f"run_gate_drift:{run}:{gate}")
        rendered_quality_inputs = []
        for row in rebuilt_rows:
            ticker = str(row["ticker"])
            composed = runner.compose_decision(
                DirectionalCoreCandidate.model_validate(row["core"]),
                PriceTimingCandidate.model_validate(row["timing"]),
            )
            industry = str(stocks[ticker].get("industry") or stocks[ticker].get("sector") or "")
            rendered_quality_inputs.append(
                render_structured_autonomy_message(
                    evidence[ticker],
                    composed.candidate,
                    price_map=price_maps[ticker],
                    industry=industry,
                    base_detail_text=base_contexts[ticker],
                )
            )
        message_quality = structured_autonomy_message_quality(rendered_quality_inputs)
        _assert_equal(
            message_quality,
            summary.get("message_quality"),
            f"message_quality_drift:{run}",
        )
        for index, row in enumerate(rebuilt_rows):
            message_exports.append(
                {
                    "run": run.upper(),
                    "ticker": row["ticker"],
                    "summary_member": RUN_SUMMARY_MEMBERS[run],
                    "summary_row_index": index,
                    "rendered_message": row["rendered_message"],
                    "core_input_sha256": canonical_sha256(row["core"]),
                    "timing_input_sha256": canonical_sha256(row["timing"]),
                    "composed_sha256": canonical_sha256(row["composed"]),
                }
            )
        run_results[run] = {
            "context_count": len(context_checks),
            "context_schema_identity_pass_count": sum(
                row["status"] == "PASS" for row in context_checks
            ),
            "context_checks": context_checks,
            "core_partial_audit_pass_count": sum(row["status"] == "PASS" for row in core_audits),
            "timing_partial_audit_pass_count": sum(
                row["status"] == "PASS" for row in timing_audits
            ),
            "summary_row_count": len(rebuilt_rows),
            "raw_to_normalized_to_summary_lineage": "PASS",
            "alias_selection_count": alias_selection_count,
            "rerun_gate_status": {
                name: document["status"] for name, document in rerun_gates.items()
            },
            "message_quality_status": message_quality["status"],
            "repeated_substantive_span_count": message_quality["repeated_substantive_span_count"],
            "status": "PASS",
        }
    audit = {
        "contract": "offline-first-a-lineage-gate-rerun-v1",
        "source_generation_id": SOURCE_GENERATION_ID,
        "runtime_generation_id": RUNTIME_GENERATION_ID,
        "run_results": run_results,
        "raw_output_file_count": 16,
        "raw_stage_row_count": 64,
        "composed_and_rendered_row_count": 32,
        "freshly_rerun": [
            "actual per-context JSON schema validation",
            "prompt/schema/output hash binding",
            "receipt and output identity binding",
            "alias resolution",
            "raw-to-normalized-to-summary lineage",
            "Core and Price-Timing partial semantic audits",
            "composition and renderer output equality",
            "ownership, renderer and current hard-safety aggregate gates",
            "message-quality evaluator",
        ],
        "inherited_not_freshly_reconstructed": [
            "numeric provenance implementation history",
            "accounting attribution implementation history",
            "ADR/security-basis implementation history",
            "official provisional-earnings implementation history",
        ],
        "semantic_validator_rerun_scope": "FIRST_AND_A_COMPLETED_RUNS_ONLY",
        "hard_defect_confirmed_in_offline_scope": False,
        "status": "PASS",
    }
    export = {
        "contract": "derived-original-rendered-message-export-v1",
        "derivative_not_model_output": True,
        "rows": message_exports,
        "row_count": len(message_exports),
        "status": "PASS",
    }
    return audit, export


def _stance(value: object) -> object:
    return value.get("stance") if isinstance(value, Mapping) else value


def _unknown_signature(core: Mapping[str, object]) -> list[dict[str, object]]:
    rows = core.get("unknown_treatments")
    if not isinstance(rows, list):
        return []
    return [
        {
            "treatment": row.get("treatment"),
            "evidence_refs": sorted(str(value) for value in row.get("evidence_refs") or []),
            "directional_negative_basis": sorted(
                str(value) for value in row.get("directional_negative_basis") or []
            ),
            "summary": row.get("summary"),
        }
        for row in rows
        if isinstance(row, Mapping)
    ]


def compare_first_a_fields(root: Path) -> dict[str, object]:
    first = read_json(root / RUN_SUMMARY_MEMBERS["first"])
    run_a = read_json(root / RUN_SUMMARY_MEMBERS["a"])
    first_rows = {
        str(row["ticker"]): row for row in first.get("rows") or [] if isinstance(row, Mapping)
    }
    a_rows = {
        str(row["ticker"]): row for row in run_a.get("rows") or [] if isinstance(row, Mapping)
    }
    _assert_equal(tuple(first_rows), COHORT, "first_summary_order")
    _assert_equal(tuple(a_rows), COHORT, "a_summary_order")
    field_specs = {
        "overall_direction": lambda row: row["core"]["overall_direction"],
        "directional_balance": lambda row: row["core"]["directional_balance"],
        "fundamental_new_buyer_stance": lambda row: _stance(row["core"]["fundamental_new_buyer"]),
        "fundamental_holder_stance": lambda row: _stance(row["core"]["fundamental_holder"]),
        "technical_state": lambda row: row["timing"]["technical_state"],
        "entry_mode": lambda row: row["timing"]["entry_mode"],
        "timing_new_buyer_modifier": lambda row: row["timing"]["timing_new_buyer_modifier"],
        "holder_price_review": lambda row: row["timing"]["holder_price_review"],
    }
    identical_counts = {name: 0 for name in field_specs}
    rows = []
    direct_flip_count = 0
    for ticker in COHORT:
        first_row = first_rows[ticker]
        a_row = a_rows[ticker]
        values = {}
        changed = []
        for name, getter in field_specs.items():
            first_value = getter(first_row)
            a_value = getter(a_row)
            same = first_value == a_value
            identical_counts[name] += int(same)
            values[name] = {"first": first_value, "a": a_value, "identical": same}
            if not same:
                changed.append(name)
        first_direction = str(values["overall_direction"]["first"])
        a_direction = str(values["overall_direction"]["a"])
        if {first_direction, a_direction} == {"BUY", "SELL"}:
            direct_flip_count += 1
        first_core = first_row["core"]
        a_core = a_row["core"]
        first_anchors = sorted(
            str(value) for value in first_core["material_directional_anchor_basis"]
        )
        a_anchors = sorted(str(value) for value in a_core["material_directional_anchor_basis"])
        first_unknowns = _unknown_signature(first_core)
        a_unknowns = _unknown_signature(a_core)
        first_buy = float(first_core["directional_balance"]["buy"])
        a_buy = float(a_core["directional_balance"]["buy"])
        rows.append(
            {
                "ticker": ticker,
                "values": values,
                "changed_fields": changed,
                "buy_balance_delta_a_minus_first": round(a_buy - first_buy, 1),
                "classification_boundary_crossed": first_direction != a_direction,
                "anchors": {
                    "first": first_anchors,
                    "a": a_anchors,
                    "added_in_a": sorted(set(a_anchors) - set(first_anchors)),
                    "removed_in_a": sorted(set(first_anchors) - set(a_anchors)),
                },
                "unknown_treatments": {
                    "first": first_unknowns,
                    "a": a_unknowns,
                    "identical": first_unknowns == a_unknowns,
                },
            }
        )
    direction_changes = [
        {
            "ticker": row["ticker"],
            "first": row["values"]["overall_direction"]["first"],
            "a": row["values"]["overall_direction"]["a"],
            "first_balance": row["values"]["directional_balance"]["first"],
            "a_balance": row["values"]["directional_balance"]["a"],
            "buy_balance_delta_a_minus_first": row["buy_balance_delta_a_minus_first"],
            "anchors": row["anchors"],
            "unknown_treatments": row["unknown_treatments"],
        }
        for row in rows
        if not row["values"]["overall_direction"]["identical"]
    ]
    expected_identical = {
        "overall_direction": 9,
        "directional_balance": 7,
        "fundamental_new_buyer_stance": 13,
        "fundamental_holder_stance": 15,
        "technical_state": 13,
        "entry_mode": 16,
        "timing_new_buyer_modifier": 15,
        "holder_price_review": 13,
    }
    mismatches = {
        key: {"expected": value, "actual": identical_counts[key]}
        for key, value in expected_identical.items()
        if identical_counts[key] != value
    }
    boundary_half_point_count = sum(
        abs(float(row["buy_balance_delta_a_minus_first"])) == 0.5 for row in direction_changes
    )
    return {
        "contract": "post-hoc-two-run-descriptive-comparison-v1",
        "comparison_status": "POST_HOC_TWO_RUN_DESCRIPTIVE_COMPARISON",
        "cohort_count": len(rows),
        "identical_counts": identical_counts,
        "different_counts": {key: len(rows) - value for key, value in identical_counts.items()},
        "direction_change_count": len(direction_changes),
        "direct_buy_sell_flip_count": direct_flip_count,
        "direction_changes_with_half_point_buy_shift": boundary_half_point_count,
        "direction_changes": direction_changes,
        "rows": rows,
        "expected_count_mismatches": mismatches,
        "formal_stability_status": "NOT_MEASURED",
        "formal_generalization_status": "NOT_ESTABLISHED",
        "not_an_official_reliability_rate": True,
        "status": "PASS" if not mismatches and direct_flip_count == 0 else "FAIL",
    }


def normalize_historical_report_inputs(root: Path) -> dict[str, object]:
    proof_root = root / "reports/proofs"
    original_hashes = {
        name: file_sha256(proof_root / name)
        for name in (
            "03-prior-real-issuer-exposure-registry.json",
            "04-new-holdout-exclusion-set.json",
            "07-us-source-coverage-audit.json",
            "10-kr-source-coverage-audit.json",
        )
    }
    normalized = report_closeout.normalize_completion_inputs(
        registry=read_json(proof_root / "03-prior-real-issuer-exposure-registry.json"),
        exclusion=read_json(proof_root / "04-new-holdout-exclusion-set.json"),
        us_audit=read_json(proof_root / "07-us-source-coverage-audit.json"),
        kr_audit=read_json(proof_root / "10-kr-source-coverage-audit.json"),
    )
    expected = {
        "prior_real_issuer_exposure_registry_count": 85,
        "new_holdout_exclusion_count": 101,
        "us_target_count": 4,
        "us_attempted_count": 6,
        "us_source_sufficient_count": 4,
        "us_source_insufficient_count": 2,
        "us_pipeline_coverage_gap_count": 0,
        "us_source_absence_count": 2,
        "us_unknown_failure_count": 0,
        "kr_target_count": 12,
        "kr_attempted_count": 12,
        "kr_source_sufficient_count": 12,
        "kr_source_insufficient_count": 0,
        "kr_pipeline_coverage_gap_count": 0,
        "kr_source_absence_count": 0,
        "kr_unknown_failure_count": 0,
    }
    fields = normalized["canonical_fields"]
    mismatches = {
        key: {"expected": value, "actual": fields.get(key)}
        for key, value in expected.items()
        if fields.get(key) != value
    }
    recovered = read_json(proof_root / "62-reporting-closeout-recovery.json")
    return {
        "contract": "derived-reporting-closeout-repair-v1",
        "original_error": recovered["closeout_recovery"]["original_failure"],
        "transport_error_preserved_separately": True,
        "normalization": normalized,
        "expected_count_mismatches": mismatches,
        "original_source_proof_hashes": original_hashes,
        "recorded_recovery_source_proof_hashes": recovered["closeout_recovery"][
            "original_source_proof_hashes"
        ],
        "original_source_proofs_modified": False,
        "reporting_patch_status": "IMPLEMENTED_BOUNDED_NORMALIZER",
        "status": "PASS" if not mismatches else "FAIL",
    }


def exposure_mapping(root: Path) -> dict[str, object]:
    original = read_json(root / "reports/proofs/51-holdout-exposure-retirement-state.json")
    return {
        "contract": "original-derived-exposure-measurement-mapping-v1",
        "original_report_state": {
            "holdout_output_exposure_state": original.get("holdout_output_exposure_state"),
            "holdout_retirement_state": original.get("holdout_retirement_state"),
            "holdout_semantic_revelation_state": original.get("holdout_semantic_revelation_state"),
            "status": original.get("status"),
        },
        "original_enum_values_preserved": True,
        "derived_measured_scope_state": {
            "cohort_unique_issuer_exposure": "FULLY_EXPOSED",
            "proof_completion": "INCOMPLETE_TRANSPORT_FAILURE",
            "completed_run_hard_gate_scope": "FIRST_AND_A",
            "completed_run_semantic_observation": ("NO_REPORTED_HARD_DEFECT_IN_MEASURED_SCOPE"),
            "formal_generalization": "NOT_ESTABLISHED",
            "future_unseen_holdout_reuse_allowed": 0,
            "retirement_reason": ("INCOMPLETE_A_B_C_AFTER_FULL_COHORT_EXPOSURE"),
        },
        "cohort": list(COHORT),
        "retired_cohort_replayed": 0,
        "status": "PASS",
    }


def _reference_member_hashes(root: Path, members: Sequence[str]) -> dict[str, dict[str, object]]:
    index = read_json(root / "artifact-index.json")
    rows = {
        str(row["path"]): row
        for row in index.get("rows") or []
        if isinstance(row, Mapping) and row.get("path")
    }
    result = {}
    for member in members:
        path = root / member
        if member not in rows or not path.is_file():
            raise ValueError(f"referenced_historical_member_missing:{member}")
        actual_sha = file_sha256(path)
        actual_bytes = path.stat().st_size
        expected_sha = rows[member].get("sha256")
        expected_bytes = rows[member].get("byte_size")
        if actual_sha != expected_sha or actual_bytes != expected_bytes:
            raise ValueError(f"referenced_historical_member_drift:{member}")
        result[member] = {"sha256": actual_sha, "byte_size": actual_bytes}
    return result


def _historical_members_to_preserve(root: Path) -> list[str]:
    members = [
        "artifact-index.json",
        "README.md",
        "experiment/program-state.json",
        "experiment/source-lock.json",
        "experiment/prompt-schema-lock.json",
        "reports/proofs/03-prior-real-issuer-exposure-registry.json",
        "reports/proofs/04-new-holdout-exclusion-set.json",
        "reports/proofs/07-us-source-coverage-audit.json",
        "reports/proofs/10-kr-source-coverage-audit.json",
        "reports/proofs/27-first-execution-summary.json",
        "reports/proofs/30-first-run-ownership-gate.json",
        "reports/proofs/31-first-run-renderer-gate.json",
        "reports/proofs/32-first-run-hard-safety-gate.json",
        "reports/proofs/33-run-a-execution-summary.json",
        "reports/proofs/36-run-a-ownership-gate.json",
        "reports/proofs/37-run-a-renderer-gate.json",
        "reports/proofs/38-run-a-hard-safety-gate.json",
        "reports/proofs/39-run-b-execution-summary.json",
        "reports/proofs/45-run-c-execution-summary.json",
        "reports/proofs/51-holdout-exposure-retirement-state.json",
        "reports/proofs/52-core-stability.json",
        "reports/proofs/53-timing-stability.json",
        "reports/proofs/54-ownership-generalization.json",
        "reports/proofs/56-hard-safety-regression.json",
        "reports/proofs/60-program-completion.json",
        "reports/proofs/61-monitoring-pause-and-fresh-proof-completion.json",
        "reports/proofs/62-reporting-closeout-recovery.json",
    ]
    members.extend(
        str(path.relative_to(root)) for path in sorted((root / "operational").glob("*.json"))
    )
    members.extend(
        str(path.relative_to(root))
        for folder in (
            root / "experiment/model-contexts/FIRST",
            root / "experiment/model-contexts/A",
            root / "experiment/model-contexts/B/DIRECTIONAL_CORE/batch-01",
        )
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    )
    members.extend(
        str(path.relative_to(root))
        for folder in (
            root / "experiment/packets",
            root / "experiment/base-contexts",
        )
        for path in sorted(folder.glob("*"))
        if path.is_file()
    )
    return sorted(set(members))


def preserve_historical_members(root: Path, destination: Path) -> dict[str, object]:
    members = _historical_members_to_preserve(root)
    index = read_json(root / "artifact-index.json")
    indexed = {
        str(row["path"]): row
        for row in index.get("rows") or []
        if isinstance(row, Mapping) and row.get("path")
    }
    rows = []
    for member in members:
        source = root / member
        target = destination / member
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        actual_sha = file_sha256(target)
        actual_bytes = target.stat().st_size
        if member == "artifact-index.json":
            expected_sha = file_sha256(source)
            expected_bytes = source.stat().st_size
        else:
            expected = indexed.get(member)
            if expected is None:
                raise ValueError(f"historical_member_not_indexed:{member}")
            expected_sha = expected.get("sha256")
            expected_bytes = expected.get("byte_size")
        if actual_sha != expected_sha or actual_bytes != expected_bytes:
            raise ValueError(f"historical_copy_drift:{member}")
        rows.append(
            {
                "source_member": member,
                "copied_path": f"historical-input/{member}",
                "sha256": actual_sha,
                "byte_size": actual_bytes,
                "copy_status": "EXACT_BYTES_PRESERVED",
            }
        )
    return {
        "contract": "selected-historical-member-preservation-v1",
        "selected_member_count": len(rows),
        "rows": rows,
        "hash_drift_count": 0,
        "size_drift_count": 0,
        "status": "PASS",
    }


def _report_title(name: str) -> str:
    return name.split("-", 1)[1].replace("-", " ").title()


def write_report(
    report_dir: Path,
    *,
    number: int,
    document: Mapping[str, object],
    bullets: Sequence[str],
) -> None:
    name = REPORT_NAMES[number - 1]
    write_json(report_dir / "proofs" / f"{name}.json", document)
    lines = [f"# {_report_title(name)}", ""]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.extend(
        [
            "",
            f"Machine-readable evidence: `proofs/{name}.json`.",
        ]
    )
    write_text(report_dir / f"{name}.md", "\n".join(lines))


def _source_hash(path: Path) -> str:
    return file_sha256(path)


def build_message_quality(root: Path, message_export: Mapping[str, object]) -> dict[str, object]:
    first = read_json(root / RUN_SUMMARY_MEMBERS["first"])["message_quality"]
    run_a = read_json(root / RUN_SUMMARY_MEMBERS["a"])["message_quality"]
    return {
        "contract": "first-a-message-quality-scope-v1",
        "first": first,
        "a": run_a,
        "message_quality_gate_role_at_execution": (
            "ADVISORY_NOT_INCLUDED_IN_RUN_STATUS_OR_PROGRESS_SEQUENCE"
        ),
        "gate_role_evidence": {
            "first_execution_status": "PASS",
            "first_message_quality_status": first["status"],
            "a_execution_status": "PASS",
            "a_message_quality_status": run_a["status"],
            "progression_instruction_hard_gates": [
                "ownership",
                "renderer",
                "hard_safety",
            ],
            "quality_evaluator_classification_reproduced": True,
        },
        "repeated_span_metric_is_not_failed_subject_count": True,
        "common_evidence_limitations_may_explain_some_repetition_but_do_not_resolve_it": True,
        "important_issuer_specific_evidence_omission_status": "NOT_MEASURED",
        "derived_original_message_export": {
            "path": "derived/first-a-original-rendered-messages.json",
            "row_count": message_export["row_count"],
            "derivative_not_model_output": True,
        },
        "prompt_or_renderer_tuning_against_exposed_cohort": 0,
        "status": "UNRESOLVED_MESSAGE_QUALITY_FAIL_PRESERVED",
    }


def build_program_reports(
    *,
    root: Path,
    input_integrity: Mapping[str, object],
    current_instruction_zip: Path,
    previous_instruction_zip: Path,
    pause: Mapping[str, object],
    validation: Mapping[str, object],
    report_dir: Path,
) -> dict[str, object]:
    current_instruction_sha = file_sha256(current_instruction_zip)
    previous_instruction_sha = file_sha256(previous_instruction_zip)
    if current_instruction_sha != CURRENT_INSTRUCTION_ZIP_SHA256:
        raise ValueError("current_work_instruction_zip_sha256_mismatch")
    if previous_instruction_sha != PREVIOUS_INSTRUCTION_ZIP_SHA256:
        raise ValueError("previous_work_instruction_zip_sha256_mismatch")
    branch = git_value("rev-parse", "--abbrev-ref", "HEAD")
    head = git_value("rev-parse", "HEAD")
    instruction_path = (
        "docs/work-instructions/"
        "20260907-websocket-timeout-runtime-review-first-a-evidence-closeout.md"
    )
    work_instruction_commit = git_value("log", "-1", "--format=%H", "--", instruction_path)
    base_sha = git_value("rev-parse", f"{work_instruction_commit}^")
    referenced_members = (
        "experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-01/transport_receipt.json",
        "experiment/model-contexts/A/DIRECTIONAL_CORE/batch-01/transport_receipt.json",
        "experiment/model-contexts/B/DIRECTIONAL_CORE/batch-01/transport_receipt.json",
        "experiment/model-contexts/B/DIRECTIONAL_CORE/batch-01/stderr.raw.log",
        "experiment/model-contexts/B/DIRECTIONAL_CORE/batch-01/transport_log.raw.log",
        "experiment/model-contexts/B/DIRECTIONAL_CORE/batch-01/context_manifest.json",
        "reports/proofs/27-first-execution-summary.json",
        "reports/proofs/33-run-a-execution-summary.json",
        "reports/proofs/62-reporting-closeout-recovery.json",
    )
    provenance = {
        "contract": "input-integrity-repository-provenance-v1",
        **input_integrity,
        "current_work_instruction_zip_sha256": current_instruction_sha,
        "previous_work_instruction_zip_sha256": previous_instruction_sha,
        "historical_reference_member_sha256": _reference_member_hashes(root, referenced_members),
        "initial_repository_observation": {
            "branch": ("codex/20260907-monitoring-pause-completion-fresh-issuer-ownership-proof"),
            "head": "665a1115b29c7e14747e533df9694f440246f723",
            "status": "CLEAN",
        },
        "historical_report_identified_final_head": ("46e09b999d6c5834fa5f5adf7ec1ff0df159bfb1"),
        "later_commit_explanation": (
            "665a111 is the report/evidence closeout descendant of 46e09b9; it "
            "contains no additional model invocation or investment semantic change."
        ),
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit_or_not_changed": head,
        "final_head_sha_at_report_generation": head,
        "branch": branch,
        "git_status_at_report_generation": git_value("status", "--short") or "CLEAN",
        "status": "PASS",
    }
    operational_pause = read_json(root / "operational/03-pause-action-and-after-state.json")
    backlog = read_json(root / "operational/04-backlog-and-transition-observation.json")
    pause_report = {
        "contract": "pause-state-historical-transition-accounting-v1",
        "current_observation": dict(pause),
        "historical_pause": {
            "us": "PAUSED_COMPLETE",
            "kr": "PAUSED_COMPLETE",
            "paused_scheduler_objects": 8,
            "prior_task_changes": 6,
            "latest_task_additional_changes": 2,
            "forced_termination": 0,
            "automatic_restoration": False,
        },
        "historical_natural_delivery": {
            "window_kst": "2026-09-07 17:10:00-17:10:18",
            "items": 9,
            "composition": "one KR digest plus eight company messages",
            "pending_at_2026_09_07_17_42_54_kst": 0,
            "sent_at_2026_09_07_17_42_54_kst": 9,
            "task_initiated_delivery": False,
        },
        "historical_source_documents": {
            "pause_after_state": operational_pause,
            "backlog_transition": backlog,
        },
        "new_scheduler_mutation_count": 0,
        "auto_resume_executed": 0,
        "status": (
            "PASS" if pause.get("status") == "VERIFIED_PAUSED_COMPLETE" else pause.get("status")
        ),
    }
    execution = reconcile_executions(root)
    a_receipts = [
        read_json(path) for path in _context_paths(root) if _run_from_context(path) == "a"
    ]
    b_receipt = read_json(
        root / "experiment/model-contexts/B/DIRECTIONAL_CORE/batch-01/transport_receipt.json"
    )
    a_last = max(str(row["completed_at"]) for row in a_receipts)
    a_last_time = datetime.fromisoformat(a_last)
    b_start_time = datetime.fromisoformat(str(b_receipt["started_at"]))
    execution["a_to_b_sequence"] = {
        "a_terminal_receipt_count": len(a_receipts),
        "a_pass_receipt_count": sum(row.get("status") == "PASS" for row in a_receipts),
        "a_last_completed_at": a_last,
        "b_requested_invocation_id": b_receipt.get("invocation_id"),
        "b_started_at": b_receipt.get("started_at"),
        "b_started_after_a_seconds": round((b_start_time - a_last_time).total_seconds(), 6),
        "status": "PASS_SEQUENTIAL_AFTER_A_COMPLETE",
    }
    lifecycle, retry = b_lifecycle(root)
    runtime_comparison = compare_core01(root)
    reporting = normalize_historical_report_inputs(root)
    exposure = exposure_mapping(root)
    offline_audit, message_export = offline_first_a_audit(root)
    differences = compare_first_a_fields(root)
    message_quality = build_message_quality(root, message_export)
    architecture_source = Path("scripts/new_issuer_holdout_selection_ownership_proof.py")
    message_quality["execution_code_sha256"] = _source_hash(architecture_source)
    message_quality["precommitted_instruction_sha256"] = file_sha256(
        Path(
            "docs/work-instructions/"
            "20260907-monitoring-pause-completion-and-fresh-issuer-ownership-proof.md"
        )
    )

    overall_checks = {
        "input_integrity": provenance["status"] == "PASS",
        "pause_preserved": pause_report["status"] == "PASS",
        "execution_reconciled": execution["status"] == "PASS",
        "lifecycle_reconstructed": lifecycle["status"] == "PASS",
        "request_comparison": runtime_comparison["status"] == "PASS",
        "retry_classification": retry["status"] == "PASS",
        "reporting_normalization": reporting["status"] == "PASS",
        "exposure_mapping": exposure["status"] == "PASS",
        "offline_first_a": offline_audit["status"] == "PASS",
        "descriptive_comparison": differences["status"] == "PASS",
    }
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit_or_not_changed": head,
        "final_head_sha": head,
        "branch": branch,
        "input_zip_sha256": input_integrity["input_zip_sha256"],
        "input_member_count": input_integrity["input_member_count"],
        "input_indexed_payload_count": input_integrity["input_indexed_payload_count"],
        "current_pause_observation_status": pause.get("status"),
        "historical_natural_delivery_items": 9,
        "new_scheduler_mutation_count": 0,
        "auto_resume_executed": 0,
        "historical_model_subprocess_invocations": 17,
        "historical_successful_contexts": 16,
        "historical_failed_contexts": 1,
        "historical_stage_rows": 64,
        "historical_unique_exposed_issuers": 16,
        "historical_composed_rows": 32,
        "historical_rendered_rows": 32,
        "first_run_hard_gate_status": "PASS",
        "a_run_hard_gate_status": "PASS",
        "b_execution_status": "TIMEOUT_NO_USABLE_OUTPUT",
        "c_execution_status": "NOT_RUN",
        "first_message_quality_status": "FAIL",
        "a_message_quality_status": "FAIL",
        "message_quality_gate_role_at_execution": message_quality[
            "message_quality_gate_role_at_execution"
        ],
        "formal_stability_status": "NOT_MEASURED",
        "formal_generalization_status": "NOT_ESTABLISHED",
        "timeout_classification": retry["classification"],
        "capacity_diagnostic_status": retry["capacity_diagnostic_status"],
        "last_stderr_after_start_seconds": lifecycle["last_stderr_after_start_seconds"],
        "silence_until_exit_seconds": lifecycle["silence_until_exit_seconds"],
        "wrapper_explicit_retry_count": retry["wrapper_explicit_retry_count"],
        "observed_cli_retry_signal_count": retry["observed_cli_retry_signal_count"],
        "upstream_request_attempt_count": "UNKNOWN",
        "request_accepted_observability": retry["request_accepted_observability"],
        "transport_root_cause_confirmed": False,
        "unresolved_hypotheses": retry["unresolved_hypotheses"],
        "original_report_state": exposure["original_report_state"],
        "derived_measured_scope_state": exposure["derived_measured_scope_state"],
        "reporting_patch_status": reporting["reporting_patch_status"],
        "descriptive_comparison_status": differences["comparison_status"],
        "semantic_validator_rerun_scope": offline_audit["semantic_validator_rerun_scope"],
        "hard_defect_confirmed_in_offline_scope": False,
        "original_evidence_hash_drift": 0,
        "new_real_issuer_model_calls": 0,
        "new_fictional_model_calls": 0,
        "new_source_fetch_calls": 0,
        "new_holdout_created": 0,
        "retired_cohort_replayed": 0,
        "production_send": 0,
        "production_deployment": 0,
        "stock_registration_change": 0,
        "paid_data_service_change": 0,
        "timeout_increase": 0,
        "canonical_transport_mutation": 0,
        "prompt_schema_decision_semantic_mutation": 0,
        "focused_tests": validation.get("focused_tests", "PENDING"),
        "full_tests": validation.get("full_tests", "PENDING"),
        "lint": validation.get("lint", "PENDING"),
        "diff_check": validation.get("diff_check", "PENDING"),
        "p0_open": 0,
        "p1_open": 2,
        "p1_issues": [
            "runtime transport cause remains unresolved",
            "FIRST/A advisory cross-ticker substantive repetition remains unresolved",
        ],
        "next_scope": "BOUNDED_FICTIONAL_WEBSOCKET_RECONNECT_OBSERVABILITY_DIAGNOSTIC",
        "proposed_next_diagnostic": {
            "authorization_required": True,
            "real_issuer_call_budget": 0,
            "fictional_call_budget": 3,
            "model_effort_schema_timeout": "UNCHANGED",
            "wrapper_retry_count": 0,
            "evidence": [
                "per-call lifecycle receipt",
                "runtime-only stderr events",
                "session and namespace identity",
                "passive network readiness before each call",
                "process cleanup receipt",
            ],
            "stop_rule": (
                "stop after the first watchdog timeout or explicit capacity/context "
                "diagnostic; otherwise stop after three terminal fictional calls"
            ),
            "decision_value": (
                "tests whether the WebSocket disconnect/timeout pattern recurs under "
                "bounded fictional load; a clean result does not prove production reliability"
            ),
        },
        "readiness": "NOT_READY_FULL_PROOF_TRANSPORT_CAUSE_UNRESOLVED",
        "stop_reason": (
            "B Core01 watchdog timeout after an observed WebSocket disconnect and "
            "single CLI retry signal; C was not run"
        ),
        "overall_checks": overall_checks,
        "status": "PASS_OFFLINE_CLOSEOUT_WITH_OPEN_TRANSPORT_AND_QUALITY_ISSUES"
        if all(overall_checks.values())
        else "FAIL",
        "payload_count": "PENDING_PACKAGE",
        "zip_member_count": "PENDING_PACKAGE",
        "integrity_mismatches": "PENDING_PACKAGE",
    }

    write_report(
        report_dir,
        number=1,
        document=provenance,
        bullets=(
            f"Historical ZIP SHA-256: `{input_integrity['input_zip_sha256']}`.",
            "ZIP members 1165; indexed payloads 1164; hash and size mismatches 0.",
            f"Work-instruction commit: `{work_instruction_commit}`; base: `{base_sha}`.",
        ),
    )
    write_report(
        report_dir,
        number=2,
        document=pause_report,
        bullets=(
            f"Current observation: `{pause.get('status')}`; current mutations 0.",
            "Eight named monitoring objects remain paused; auto-resume was not executed.",
            "Historical 17:10 delivery was one digest plus eight company messages (9 items).",
        ),
    )
    write_report(
        report_dir,
        number=3,
        document=execution,
        bullets=(
            "FIRST 16/16 and A 16/16 completed; B produced no usable output; C was not run.",
            "A had 8/8 PASS receipts before B started 0.317574 seconds later.",
            "17 invocations = 16 successes + 1 timeout; renderer contexts are not model calls.",
        ),
    )
    write_report(
        report_dir,
        number=4,
        document=lifecycle,
        bullets=(
            "B Core01 ended at the 1800-second Python watchdog with exit -15.",
            "The last stderr event was ~74.974 seconds after start, followed by ~1725.082 seconds of silence.",
            "`OUTPUT_FILE_MISSING` is retained as a downstream observation, not the root cause.",
        ),
    )
    write_report(
        report_dir,
        number=5,
        document=runtime_comparison,
        bullets=(
            "FIRST/A/B Core01 prompt, schema, subject order, model, effort and CLI identity match.",
            "Each request has a distinct session ID and runtime-state namespace.",
            "Identical input does not imply identical transport behavior.",
        ),
    )
    write_report(
        report_dir,
        number=6,
        document=retry,
        bullets=(
            "Wrapper retries: 0; observed CLI retry signals: 1; upstream attempts/acceptance: UNKNOWN.",
            "Classification: `WATCHDOG_TRANSPORT_TIMEOUT_AFTER_WEBSOCKET_DISCONNECT`.",
            "No explicit capacity or context-length diagnostic was observed in this context.",
        ),
    )
    write_report(
        report_dir,
        number=7,
        document=reporting,
        bullets=(
            "The post-timeout `KeyError: registry_count` was a separate report-closeout failure.",
            "Current and legacy report keys now normalize by semantic meaning; contradictions fail closed.",
            "Original source proofs remain byte-identical and linked by SHA-256.",
        ),
    )
    write_report(
        report_dir,
        number=8,
        document=exposure,
        bullets=(
            "Original persisted enums are preserved without redefinition.",
            "Derived scope: full 16-issuer exposure, incomplete transport proof, FIRST/A measured only.",
            "The full cohort remains retired; future unseen reuse allowed = 0.",
        ),
    )
    write_report(
        report_dir,
        number=9,
        document=offline_audit,
        bullets=(
            "All 16 raw model files and 64 stage rows passed fresh offline schema and lineage checks.",
            "All 32 composed/rendered rows reproduced exactly for FIRST and A.",
            "Frozen ownership, renderer and available hard-safety gates reran PASS in measured scope.",
        ),
    )
    change_lines = "; ".join(
        f"{row['ticker']} {row['first']}->{row['a']}" for row in differences["direction_changes"]
    )
    write_report(
        report_dir,
        number=10,
        document=differences,
        bullets=(
            "This is a post-hoc two-run descriptive comparison, not formal stability evidence.",
            f"Direction matched 9/16; seven boundary changes: {change_lines}.",
            "All seven direction changes moved the buy balance by 0.5; direct BUY-SELL flips = 0.",
        ),
    )
    write_report(
        report_dir,
        number=11,
        document=message_quality,
        bullets=(
            "FIRST and A hard ownership gates passed while message quality independently failed.",
            "Repeated substantive spans: FIRST 14, A 9; these are spans, not failed issuers.",
            "The quality check was advisory at execution; its unresolved FAIL is preserved.",
        ),
    )
    write_report(
        report_dir,
        number=12,
        document=completion,
        bullets=(
            "Offline forensic/reporting closeout passed with zero model, source, scheduler or production calls.",
            "Formal stability and ownership generalization remain NOT_MEASURED / NOT_ESTABLISHED.",
            "Next scope requires separate authorization for a three-call fictional WebSocket observability diagnostic.",
        ),
    )
    write_json(
        report_dir / "derived" / "first-a-original-rendered-messages.json",
        message_export,
    )
    message_lines = ["# FIRST/A Original Rendered Messages", ""]
    for row in message_export["rows"]:
        message_lines.extend(
            [
                f"## {row['run']} {row['ticker']}",
                "",
                str(row["rendered_message"]),
                "",
            ]
        )
    write_text(
        report_dir / "derived" / "first-a-original-rendered-messages.md",
        "\n".join(message_lines),
    )
    write_text(
        report_dir / "README.md",
        "# WebSocket Timeout Runtime Review & FIRST/A Evidence Closeout\n\n"
        "This is an offline, report-only closeout. It performs no model call, source "
        "fetch, scheduler mutation, Telegram send, database write, deployment or "
        "retired-cohort replay. Historical inputs are cited by immutable SHA-256; "
        "derived exports are labeled separately.\n",
    )
    return {
        "provenance": provenance,
        "pause": pause_report,
        "execution": execution,
        "lifecycle": lifecycle,
        "comparison": runtime_comparison,
        "retry": retry,
        "reporting": reporting,
        "exposure": exposure,
        "offline_audit": offline_audit,
        "differences": differences,
        "message_quality": message_quality,
        "completion": completion,
        "message_export": message_export,
    }


def scan_secrets(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    counts = [len(pattern.findall(payload)) for pattern in SECRET_PATTERNS]
    return {
        "secret_exposure_count": sum(counts),
        "secret_scan_status": "PASS" if not any(counts) else "BLOCKED",
    }


def artifact_index(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.relative_to(root).as_posix() == "artifact-index.json":
            continue
        scan = scan_secrets(path)
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "byte_size": path.stat().st_size,
                "sha256": file_sha256(path),
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    secret_failures = sum(row["secret_scan_status"] != "PASS" for row in rows)
    if secret_failures:
        raise ValueError(f"artifact_secret_scan_failure:{secret_failures}")
    return {
        "contract": "websocket-timeout-closeout-artifact-index-v1",
        "index_self_exclusion": "artifact-index.json",
        "all_payload_files_except_index_itself_individually_indexed": True,
        "indexed_artifact_count": len(rows),
        "artifact_secret_scan_failure_count": secret_failures,
        "rows": rows,
    }


def package_result(
    *,
    extracted_root: Path,
    report_dir: Path,
    bundle_root: Path,
    zip_output: Path,
    validation: Mapping[str, object],
) -> dict[str, object]:
    if bundle_root.exists():
        raise ValueError(f"new_bundle_root_required:{bundle_root}")
    if zip_output.exists() or zip_output.with_suffix(zip_output.suffix + ".sha256").exists():
        raise ValueError(f"new_zip_output_required:{zip_output}")
    bundle_root.mkdir(parents=True)
    shutil.copytree(report_dir, bundle_root / "reports")
    preservation = preserve_historical_members(extracted_root, bundle_root / "historical-input")
    write_json(
        bundle_root / "derived" / "historical-member-copy-manifest.json",
        preservation,
    )
    message_source = report_dir / "derived/first-a-original-rendered-messages.json"
    shutil.copyfile(
        message_source,
        bundle_root / "derived/first-a-original-rendered-messages.json",
    )
    write_text(
        bundle_root / "README.md",
        "# WebSocket Timeout Runtime Review & FIRST/A Evidence Closeout\n\n"
        "The `historical-input/` subtree contains selected byte-identical members "
        "from the verified historical report. `reports/` and `derived/` are current "
        "offline closeout outputs. No model or source call was made.\n",
    )
    completion_path = bundle_root / "reports/proofs/12-program-completion.json"
    completion = read_json(completion_path)
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "focused_tests": validation.get("focused_tests", completion["focused_tests"]),
            "full_tests": validation.get("full_tests", completion["full_tests"]),
            "lint": validation.get("lint", completion["lint"]),
            "diff_check": validation.get("diff_check", completion["diff_check"]),
            "historical_selected_copy_member_count": preservation["selected_member_count"],
        }
    )
    prospective_payload_count = sum(
        path.is_file() and path.name != "artifact-index.json" for path in bundle_root.rglob("*")
    )
    completion.update(
        {
            "payload_count": prospective_payload_count,
            "zip_member_count": prospective_payload_count + 1,
            "integrity_mismatches": 0,
        }
    )
    write_json(completion_path, completion)
    write_json(bundle_root / "completion.json", completion)
    index = artifact_index(bundle_root)
    # completion.json is added after the initial prospective count calculation.
    completion["payload_count"] = index["indexed_artifact_count"]
    completion["zip_member_count"] = int(index["indexed_artifact_count"]) + 1
    write_json(completion_path, completion)
    write_json(bundle_root / "completion.json", completion)
    index = artifact_index(bundle_root)
    write_json(bundle_root / "artifact-index.json", index)

    zip_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(bundle_root).as_posix())
    with zipfile.ZipFile(zip_output) as archive:
        names = archive.namelist()
        bad_member = archive.testzip()
        archived_index = json.loads(archive.read("artifact-index.json"))
        archived_rows = archived_index.get("rows")
        if not isinstance(archived_rows, list):
            raise ValueError("packaged_artifact_index_rows_missing")
        hash_mismatches = 0
        size_mismatches = 0
        for row in archived_rows:
            payload = archive.read(str(row["path"]))
            hash_mismatches += sha256_bytes(payload) != row["sha256"]
            size_mismatches += len(payload) != row["byte_size"]
        indexed_paths = {str(row["path"]) for row in archived_rows}
        payload_paths = set(names) - {"artifact-index.json"}
        membership_mismatches = len(indexed_paths ^ payload_paths)
    if bad_member or hash_mismatches or size_mismatches or membership_mismatches:
        raise ValueError("packaged_zip_integrity_failure")
    zip_sha = file_sha256(zip_output)
    sidecar = zip_output.with_suffix(zip_output.suffix + ".sha256")
    write_text(sidecar, f"{zip_sha}  {zip_output.name}")
    return {
        "zip_path": str(zip_output),
        "zip_sha256": zip_sha,
        "sidecar_path": str(sidecar),
        "payload_count": len(archived_rows),
        "zip_member_count": len(names),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "membership_mismatch_count": membership_mismatches,
        "crc_failure": bad_member,
        "status": "PASS",
    }


def load_validation(path: Path | None) -> dict[str, object]:
    if path is None:
        return {
            "focused_tests": "PENDING",
            "full_tests": "PENDING",
            "lint": "PENDING",
            "diff_check": "PENDING",
        }
    return read_json(path)


def extract_verified_bundle(input_zip: Path, destination: Path) -> None:
    with zipfile.ZipFile(input_zip) as archive:
        archive.extractall(destination)


def analyze(args: argparse.Namespace) -> None:
    integrity = verify_input_bundle(args.input_zip)
    pause = observe_pause_state()
    if pause["status"] == "UNEXPECTED_ACTIVE_AUTOMATIC_PATH":
        raise RuntimeError("unexpected_active_monitoring_path_stop_required")
    if args.report_dir.exists():
        raise ValueError(f"new_report_directory_required:{args.report_dir}")
    validation = load_validation(args.validation_json)
    with tempfile.TemporaryDirectory(prefix="websocket-timeout-closeout-") as temporary:
        extracted = Path(temporary)
        extract_verified_bundle(args.input_zip, extracted)
        result = build_program_reports(
            root=extracted,
            input_integrity=integrity,
            current_instruction_zip=args.current_instruction_zip,
            previous_instruction_zip=args.previous_instruction_zip,
            pause=pause,
            validation=validation,
            report_dir=args.report_dir,
        )
    print(json.dumps(result["completion"], ensure_ascii=False, sort_keys=True))


def package(args: argparse.Namespace) -> None:
    verify_input_bundle(args.input_zip)
    validation = load_validation(args.validation_json)
    with tempfile.TemporaryDirectory(prefix="websocket-timeout-package-") as temporary:
        extracted = Path(temporary)
        extract_verified_bundle(args.input_zip, extracted)
        result = package_result(
            extracted_root=extracted,
            report_dir=args.report_dir,
            bundle_root=args.bundle_root,
            zip_output=args.zip_output,
            validation=validation,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("analyze", "package"):
        child = subparsers.add_parser(command)
        child.add_argument("--input-zip", type=Path, required=True)
        child.add_argument("--report-dir", type=Path, required=True)
        child.add_argument("--validation-json", type=Path)
        if command == "analyze":
            child.add_argument("--current-instruction-zip", type=Path, required=True)
            child.add_argument("--previous-instruction-zip", type=Path, required=True)
        else:
            child.add_argument("--bundle-root", type=Path, required=True)
            child.add_argument("--zip-output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "analyze":
        analyze(args)
    else:
        package(args)


if __name__ == "__main__":
    main()
