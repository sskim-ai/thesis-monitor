"""Archive-only M12V adapter over the existing instrumented CLI lifecycle."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
import subprocess

from app.services.codex_transport_lifecycle_service import (
    InstrumentedCodexInvocation,
    InstrumentedTransportError,
    invoke_instrumented_codex,
)
from scripts import financial_exclusion_expectation_m12u as u

ROOT = Path("docs/architecture/M12V_RUNTIME_ARCHITECTURE.json")


def output_observation(lifecycle):
    if lifecycle.get("output_parsed"):
        return "FINAL_OUTPUT_COMPLETE"
    if lifecycle.get("output_bytes", 0):
        return "FINAL_OUTPUT_PARTIAL"
    if lifecycle.get("stdout_bytes", 0):
        return "LOCAL_STDOUT_ACTIVITY_NO_FINAL_OUTPUT"
    if lifecycle.get("stderr_bytes", 0):
        return "LOCAL_STDERR_ACTIVITY_NO_FINAL_OUTPUT"
    return "NO_LOCAL_STREAM_ACTIVITY"


def single_attempt(
    *,
    codex_bin,
    prompt,
    schema,
    output,
    log,
    receipt_path,
    working_directory,
    runtime_state_root,
    isolation_registry,
    invocation_id,
    base_namespace,
):
    contract = u.read(ROOT)
    if not invocation_id.startswith("20260910-m12v-fictional-"):
        raise ValueError("m12v_fictional_invocation_required")
    if (
        contract["model"],
        contract["effort"],
        contract["selected_timeout_seconds"],
        contract["wrapper_retry_count"],
        contract["subjects_per_context"],
    ) != ("gpt-6-astra", "xhigh", 2400, 0, 4):
        raise ValueError("m12v_runtime_contract_mismatch")
    lifecycle_path = log.with_name("lifecycle-receipt.json")
    stdout_path, stderr_path = log.with_name("stdout.log"), log.with_name("stderr.log")
    if any(
        p.exists() for p in (output, log, receipt_path, lifecycle_path, stdout_path, stderr_path)
    ):
        raise ValueError("m12v_existing_artifact_refuses_rerun")
    working_directory.mkdir(parents=True, exist_ok=False)
    identity = isolation_registry.claim(
        base_namespace=base_namespace,
        invocation_id=invocation_id,
        working_directory=working_directory,
    )
    state = u.m12.prepare_codex_runtime_state(
        runtime_state_root, namespace=identity.runtime_state_namespace
    )
    tls = u.m12.codex_tls_environment(state.environment())
    readiness_start = datetime.now(UTC).isoformat()
    readiness = u.m12.probe_codex_network_readiness()
    readiness_end = datetime.now(UTC).isoformat()
    receipt = {
        "contract": "m12v-single-attempt-receipt-v1",
        "invocation_id": invocation_id,
        "model": contract["model"],
        "reasoning_effort": contract["effort"],
        "timeout_seconds": 2400,
        "wrapper_retry_count": 0,
        "transport_attempt_count": 1,
        "batch_split": 0,
        "single_authoritative_watchdog": True,
        "runtime_isolation": identity.audit_dict(),
        "runtime_state": state.audit_dict(),
        "network_readiness": asdict(readiness),
        "network_readiness_start": readiness_start,
        "network_readiness_end": readiness_end,
        "tls_trust_source": tls.trust_source,
        "prompt_sha256": u.sha(prompt.read_bytes()),
        "schema_sha256": u.sha(schema.read_bytes()),
    }
    if not readiness.ready:
        receipt.update(
            status="FAIL",
            failure_type=readiness.failure_type,
            started_at=readiness_start,
            finished_at=readiness_end,
            model_process_spawned=False,
            orphan_process_count=0,
            cli_internal_retry_event_count=0,
        )
        u.write(receipt_path, receipt)
        raise RuntimeError("m12v_network_preflight_failed")
    command = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "-m",
        contract["model"],
        "-c",
        'model_reasoning_effort="xhigh"',
        "--output-schema",
        str(schema.resolve()),
        "-o",
        str(output.resolve()),
        "-",
    ]
    version = subprocess.check_output([codex_bin, "--version"], text=True).strip()
    invocation = InstrumentedCodexInvocation(
        invocation_id=invocation_id,
        generation_id=invocation_id.split(":")[0],
        stage="FULL_FICTIONAL",
        batch_id=":".join(invocation_id.split(":")[1:]),
        subject_count=4,
        transport_grouping_mode="MODEL_CONTEXT_COUPLED",
        model=contract["model"],
        reasoning_effort=contract["effort"],
        cli_binary=Path(codex_bin),
        cli_version=version,
        command=command,
        working_directory=working_directory,
        prompt_path=prompt,
        schema_path=schema,
        output_path=output,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        receipt_path=lifecycle_path,
        environment=tls.environment,
        timeout_seconds=2400,
        cleanup_margin_seconds=5,
        metadata={"runtime_contract_sha256": u.sha(ROOT.read_bytes())},
    )
    try:
        lifecycle = invoke_instrumented_codex(invocation)
    except InstrumentedTransportError as exc:
        lifecycle = exc.receipt
    # Keep raw streams intact. This legacy compatibility view is NOT chronological.
    combined = b"".join(p.read_bytes() for p in (stderr_path, stdout_path) if p.exists())
    log.write_bytes(combined)
    timed_out = lifecycle["status"] == "TIMEOUT"
    diagnostic = u.m12.diagnose_codex_transport_failure(
        combined.decode(errors="replace"), timed_out=timed_out
    )
    observed = u.e.observed_runtime(combined.decode(errors="replace"))
    success = (
        lifecycle["status"] == "PASS"
        and lifecycle.get("orphan_model_process_count") == 0
        and observed == {"model": "gpt-6-astra", "effort": "xhigh"}
    )
    receipt.update(
        started_at=lifecycle["started_at"],
        finished_at=lifecycle.get("completed_at", datetime.now(UTC).isoformat()),
        model_process_spawned=lifecycle["status"] != "SPAWN_FAILED",
        returncode=lifecycle.get("exit_code"),
        timed_out=timed_out,
        timeout_count=int(timed_out),
        output_exists=output.is_file(),
        output_size=output.stat().st_size if output.is_file() else 0,
        output_sha256=u.sha(output.read_bytes()) if output.is_file() else None,
        log_sha256=u.sha(combined),
        status="PASS" if success else "FAIL",
        failure_type=None if success else diagnostic.failure_type,
        orphan_process_count=lifecycle.get("orphan_model_process_count", "NOT_MEASURED"),
        lifecycle_receipt_sha256=u.sha(lifecycle_path.read_bytes()),
        lifecycle=lifecycle,
        local_output_observation=output_observation(lifecycle),
        backend_progress_state="NOT_MEASURED",
        request_id=None,
        response_id=None,
        cli_advertised_runtime=observed,
        backend_model_attestation="NOT_MEASURED",
        combined_log_order="STDERR_THEN_STDOUT_NOT_CHRONOLOGICAL",
    )
    if lifecycle["status"] == "PASS" and not success:
        receipt["failure_type"] = "MODEL_IDENTITY_OR_ORPHAN_FAILURE"
    details = u.t.diagnostics(
        receipt, combined.decode(errors="replace"), prompt.read_bytes(), schema.read_bytes()
    )
    receipt.update({k: v for k, v in details.items() if k != "receipt"})
    u.write(receipt_path, receipt)
    if not success:
        raise RuntimeError(f"m12v_model_context_failed:{receipt['failure_type']}")
    return receipt
