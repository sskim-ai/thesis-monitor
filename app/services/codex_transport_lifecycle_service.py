from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Mapping, Sequence


TRANSPORT_LIFECYCLE_CONTRACT = "codex-transport-lifecycle-v1"
AUTHORITATIVE_TIMEOUT_OWNER = "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG"


class InstrumentedTransportError(RuntimeError):
    def __init__(self, status: str, receipt: dict[str, object]) -> None:
        self.status = status
        self.receipt = receipt
        super().__init__(f"{status}:{receipt.get('invocation_id')}")


@dataclass(frozen=True)
class InstrumentedCodexInvocation:
    invocation_id: str
    generation_id: str
    stage: str
    batch_id: str
    subject_count: int
    transport_grouping_mode: str
    model: str
    reasoning_effort: str
    cli_binary: Path
    cli_version: str
    command: Sequence[str]
    working_directory: Path
    prompt_path: Path
    schema_path: Path
    output_path: Path
    stdout_path: Path
    stderr_path: Path
    receipt_path: Path
    environment: dict[str, str]
    timeout_seconds: int
    cleanup_margin_seconds: int = 10
    metadata: Mapping[str, object] = field(default_factory=dict)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_once(path: Path, value: object) -> None:
    if path.exists():
        raise ValueError(f"transport_receipt_already_exists:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _drain_stream(
    stream,
    destination: Path,
    *,
    stream_name: str,
    timing: dict[str, float],
    counts: dict[str, int],
    lock: threading.Lock,
    monotonic: Callable[[], float],
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            observed = monotonic()
            output.write(chunk)
            output.flush()
            with lock:
                first_key = f"first_{stream_name}_byte_monotonic"
                timing.setdefault(first_key, observed)
                timing[f"last_{stream_name}_byte_monotonic"] = observed
                counts[f"{stream_name}_bytes"] += len(chunk)


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_process_group_cleanup(
    process_group_id: int,
    *,
    timeout_seconds: int,
    monotonic: Callable[[], float],
    sleeper: Callable[[float], None],
) -> bool:
    deadline = monotonic() + timeout_seconds
    while _process_group_exists(process_group_id):
        if monotonic() >= deadline:
            return False
        sleeper(0.05)
    return True


def invoke_instrumented_codex(
    invocation: InstrumentedCodexInvocation,
    *,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    if invocation.timeout_seconds < 1:
        raise ValueError("transport_timeout_must_be_positive")
    if invocation.cleanup_margin_seconds < 1:
        raise ValueError("transport_cleanup_margin_must_be_positive")
    if invocation.receipt_path.exists():
        raise ValueError(f"transport_receipt_already_exists:{invocation.receipt_path}")

    prompt_bytes = invocation.prompt_path.read_bytes()
    schema_bytes = invocation.schema_path.read_bytes()
    invocation.output_path.parent.mkdir(parents=True, exist_ok=True)
    invocation.output_path.unlink(missing_ok=True)
    invocation.stdout_path.unlink(missing_ok=True)
    invocation.stderr_path.unlink(missing_ok=True)

    started_at = datetime.now(UTC)
    started = monotonic()
    timing: dict[str, float] = {"invocation_start_monotonic": started}
    counts = {"stdout_bytes": 0, "stderr_bytes": 0}
    lock = threading.Lock()
    writer_error: list[str] = []
    process: subprocess.Popen[bytes] | None = None
    termination_initiator = "NONE"
    child_cleanup_status = "NOT_NEEDED"
    timed_out = False
    process_group_detected_after_leader_exit = False

    base_receipt: dict[str, object] = {
        "contract": TRANSPORT_LIFECYCLE_CONTRACT,
        "invocation_id": invocation.invocation_id,
        "generation_id": invocation.generation_id,
        "stage": invocation.stage,
        "batch_id": invocation.batch_id,
        "subject_count": invocation.subject_count,
        "transport_grouping_mode": invocation.transport_grouping_mode,
        "model": invocation.model,
        "reasoning_effort": invocation.reasoning_effort,
        "cli_binary_identity": {
            "path": str(invocation.cli_binary),
            "sha256": _sha256_file(invocation.cli_binary),
        },
        "cli_version": invocation.cli_version,
        "working_directory_identity": _sha256_bytes(
            str(invocation.working_directory.resolve()).encode()
        ),
        "prompt_sha256": _sha256_bytes(prompt_bytes),
        "schema_sha256": _sha256_bytes(schema_bytes),
        "input_payload_sha256": _sha256_bytes(prompt_bytes),
        "input_bytes": len(prompt_bytes),
        "configured_timeout_seconds": invocation.timeout_seconds,
        "timeout_owner": AUTHORITATIVE_TIMEOUT_OWNER,
        "timeout_owner_count": 1,
        "outer_watchdog_deadline": None,
        "cleanup_margin_seconds": invocation.cleanup_margin_seconds,
        "request_accepted_observability": "UNAVAILABLE",
        "secret_exposure_count": 0,
        "transport_metadata": dict(invocation.metadata),
        "started_at": started_at.isoformat(),
    }

    try:
        timing["process_spawn_requested_monotonic"] = monotonic()
        process = popen(
            list(invocation.command),
            cwd=str(invocation.working_directory),
            env=invocation.environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            bufsize=0,
        )
        timing["process_spawn_monotonic"] = monotonic()
    except Exception as exc:
        receipt = {
            **base_receipt,
            **timing,
            **counts,
            "status": "SPAWN_FAILED",
            "error_type": type(exc).__name__,
            "termination_initiator": "NONE",
            "child_cleanup_status": "NO_CHILD_SPAWNED",
            "orphan_model_process_count": 0,
            "duplicate_timeout_receipt_count": 0,
            "completed_at": datetime.now(UTC).isoformat(),
        }
        _write_json_once(invocation.receipt_path, receipt)
        raise InstrumentedTransportError("SPAWN_FAILED", receipt) from exc

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    def write_stdin() -> None:
        try:
            process.stdin.write(prompt_bytes)
            process.stdin.flush()
            with lock:
                timing["stdin_complete_monotonic"] = monotonic()
        except (BrokenPipeError, OSError) as exc:
            writer_error.append(type(exc).__name__)
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    writer = threading.Thread(target=write_stdin, name="codex-stdin", daemon=True)
    stdout_reader = threading.Thread(
        target=_drain_stream,
        args=(process.stdout, invocation.stdout_path),
        kwargs={
            "stream_name": "stdout",
            "timing": timing,
            "counts": counts,
            "lock": lock,
            "monotonic": monotonic,
        },
        name="codex-stdout",
        daemon=True,
    )
    stderr_reader = threading.Thread(
        target=_drain_stream,
        args=(process.stderr, invocation.stderr_path),
        kwargs={
            "stream_name": "stderr",
            "timing": timing,
            "counts": counts,
            "lock": lock,
            "monotonic": monotonic,
        },
        name="codex-stderr",
        daemon=True,
    )
    writer.start()
    stdout_reader.start()
    stderr_reader.start()

    deadline = started + invocation.timeout_seconds
    while process.poll() is None:
        if monotonic() >= deadline:
            timed_out = True
            termination_initiator = AUTHORITATIVE_TIMEOUT_OWNER
            try:
                os.killpg(process.pid, signal.SIGTERM)
                child_cleanup_status = "PROCESS_GROUP_SIGTERM_SENT"
            except ProcessLookupError:
                child_cleanup_status = "PROCESS_ALREADY_EXITED"
            try:
                process.wait(timeout=invocation.cleanup_margin_seconds)
                child_cleanup_status = "PROCESS_GROUP_TERMINATED"
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                    child_cleanup_status = "PROCESS_GROUP_SIGKILL_SENT"
                except ProcessLookupError:
                    child_cleanup_status = "PROCESS_EXITED_DURING_CLEANUP"
                process.wait()
                child_cleanup_status = "PROCESS_GROUP_KILLED"
            break
        sleeper(0.05)

    if process.poll() is None:
        process.wait()
    timing["process_exit_monotonic"] = monotonic()

    if _process_group_exists(process.pid):
        process_group_detected_after_leader_exit = True
        if not timed_out:
            termination_initiator = "POST_EXIT_PROCESS_GROUP_CLEANUP"
            try:
                os.killpg(process.pid, signal.SIGTERM)
                child_cleanup_status = "POST_EXIT_PROCESS_GROUP_SIGTERM_SENT"
            except ProcessLookupError:
                child_cleanup_status = "PROCESS_GROUP_ALREADY_GONE"
        if not _wait_for_process_group_cleanup(
            process.pid,
            timeout_seconds=invocation.cleanup_margin_seconds,
            monotonic=monotonic,
            sleeper=sleeper,
        ):
            try:
                os.killpg(process.pid, signal.SIGKILL)
                child_cleanup_status = "PROCESS_GROUP_SIGKILL_SENT"
            except ProcessLookupError:
                child_cleanup_status = "PROCESS_GROUP_EXITED_DURING_CLEANUP"
            _wait_for_process_group_cleanup(
                process.pid,
                timeout_seconds=invocation.cleanup_margin_seconds,
                monotonic=monotonic,
                sleeper=sleeper,
            )
        if not _process_group_exists(process.pid):
            child_cleanup_status = (
                "PROCESS_GROUP_CLEANED_AFTER_LEADER_EXIT"
                if not timed_out
                else "PROCESS_GROUP_CLEANED_AFTER_TIMEOUT"
            )

    writer.join(timeout=invocation.cleanup_margin_seconds)
    stdout_reader.join(timeout=invocation.cleanup_margin_seconds)
    stderr_reader.join(timeout=invocation.cleanup_margin_seconds)
    timing["stream_collection_complete_monotonic"] = monotonic()

    parsed = False
    parse_error: str | None = None
    if not timed_out and process.returncode == 0 and invocation.output_path.is_file():
        try:
            json.loads(invocation.output_path.read_text(encoding="utf-8"))
            parsed = True
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            parse_error = type(exc).__name__
    elif not invocation.output_path.is_file():
        parse_error = "OUTPUT_FILE_MISSING"
    timing["output_parse_complete_monotonic"] = monotonic()

    first_stdout = timing.get("first_stdout_byte_monotonic")
    first_stderr = timing.get("first_stderr_byte_monotonic")
    first_output_candidates = [
        value for value in (first_stdout, first_stderr) if value is not None
    ]
    status = (
        "TIMEOUT"
        if timed_out
        else "PASS"
        if process.returncode == 0 and parsed
        else "FAILED"
    )
    receipt = {
        **base_receipt,
        **timing,
        **counts,
        "status": status,
        "elapsed_to_first_stdout_seconds": (
            round(first_stdout - started, 6) if first_stdout is not None else None
        ),
        "elapsed_to_first_stderr_seconds": (
            round(first_stderr - started, 6) if first_stderr is not None else None
        ),
        "elapsed_to_first_output_seconds": (
            round(min(first_output_candidates) - started, 6)
            if first_output_candidates
            else None
        ),
        "elapsed_to_exit_seconds": round(timing["process_exit_monotonic"] - started, 6),
        "elapsed_to_parse_seconds": round(
            timing["output_parse_complete_monotonic"] - started, 6
        ),
        "output_bytes": (
            invocation.output_path.stat().st_size
            if invocation.output_path.is_file()
            else 0
        ),
        "output_parsed": parsed,
        "parse_error": parse_error,
        "stdin_writer_error": writer_error[0] if writer_error else None,
        "exit_code": process.returncode,
        "termination_signal": (
            -process.returncode if process.returncode is not None and process.returncode < 0 else None
        ),
        "termination_initiator": termination_initiator,
        "child_cleanup_status": child_cleanup_status,
        "process_group_detected_after_leader_exit": (
            process_group_detected_after_leader_exit
        ),
        "orphan_model_process_count": int(_process_group_exists(process.pid)),
        "duplicate_timeout_receipt_count": 0,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    _write_json_once(invocation.receipt_path, receipt)
    if status != "PASS":
        raise InstrumentedTransportError(status, receipt)
    return receipt
