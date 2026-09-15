from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.services.codex_transport_lifecycle_service import (
    AUTHORITATIVE_TIMEOUT_OWNER,
    InstrumentedCodexInvocation,
    InstrumentedTransportError,
    invoke_instrumented_codex,
)


def _invocation(tmp_path: Path, code: str, *, timeout: int = 5) -> InstrumentedCodexInvocation:
    prompt = tmp_path / "prompt.txt"
    schema = tmp_path / "schema.json"
    output = tmp_path / "output.json"
    prompt.write_text("payload", encoding="utf-8")
    schema.write_text("{}", encoding="utf-8")
    return InstrumentedCodexInvocation(
        invocation_id="test-invocation",
        generation_id="test-generation",
        stage="TEST",
        batch_id="1",
        subject_count=1,
        transport_grouping_mode="MODEL_CONTEXT_COUPLED",
        model="test-model",
        reasoning_effort="test-effort",
        cli_binary=Path(sys.executable),
        cli_version="test-python",
        command=(sys.executable, "-c", code, str(output)),
        working_directory=tmp_path,
        prompt_path=prompt,
        schema_path=schema,
        output_path=output,
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        receipt_path=tmp_path / "receipt.json",
        environment={},
        timeout_seconds=timeout,
        cleanup_margin_seconds=2,
    )


def test_instrumented_transport_records_full_lifecycle(tmp_path: Path) -> None:
    code = (
        "import json,sys; payload=sys.stdin.read(); "
        "print('stdout-ready', flush=True); "
        "print('stderr-ready', file=sys.stderr, flush=True); "
        "open(sys.argv[1],'w').write(json.dumps({'read':payload}))"
    )
    receipt = invoke_instrumented_codex(_invocation(tmp_path, code))

    assert receipt["status"] == "PASS"
    assert receipt["timeout_owner"] == AUTHORITATIVE_TIMEOUT_OWNER
    assert receipt["timeout_owner_count"] == 1
    assert receipt["stdin_complete_monotonic"] is not None
    assert receipt["first_stdout_byte_monotonic"] is not None
    assert receipt["first_stderr_byte_monotonic"] is not None
    assert receipt["output_parsed"] is True
    assert receipt["orphan_model_process_count"] == 0
    assert json.loads((tmp_path / "output.json").read_text())["read"] == "payload"


def test_timeout_terminates_process_group_and_writes_one_receipt(tmp_path: Path) -> None:
    code = (
        "import sys,time; sys.stdin.read(); "
        "print('started', file=sys.stderr, flush=True); time.sleep(30)"
    )
    invocation = _invocation(tmp_path, code, timeout=1)

    with pytest.raises(InstrumentedTransportError) as error:
        invoke_instrumented_codex(invocation)

    receipt = error.value.receipt
    assert receipt["status"] == "TIMEOUT"
    assert receipt["termination_initiator"] == AUTHORITATIVE_TIMEOUT_OWNER
    assert receipt["child_cleanup_status"] in {
        "PROCESS_GROUP_TERMINATED",
        "PROCESS_GROUP_KILLED",
    }
    assert receipt["orphan_model_process_count"] == 0
    assert receipt["duplicate_timeout_receipt_count"] == 0
    assert invocation.receipt_path.is_file()
    with pytest.raises(ValueError, match="transport_receipt_already_exists"):
        invoke_instrumented_codex(invocation)


def test_zero_exit_without_structured_output_fails_closed(tmp_path: Path) -> None:
    invocation = _invocation(tmp_path, "import sys; sys.stdin.read()")

    with pytest.raises(InstrumentedTransportError) as error:
        invoke_instrumented_codex(invocation)

    assert error.value.status == "FAILED"
    assert error.value.receipt["parse_error"] == "OUTPUT_FILE_MISSING"


def test_timeout_cleans_descendant_in_same_process_group(tmp_path: Path) -> None:
    code = (
        "import subprocess,sys,time; sys.stdin.read(); "
        "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
        "print('descendant-started', file=sys.stderr, flush=True); time.sleep(30)"
    )
    invocation = _invocation(tmp_path, code, timeout=1)

    with pytest.raises(InstrumentedTransportError) as error:
        invoke_instrumented_codex(invocation)

    assert error.value.receipt["status"] == "TIMEOUT"
    assert error.value.receipt["orphan_model_process_count"] == 0
    assert error.value.receipt["child_cleanup_status"] in {
        "PROCESS_GROUP_TERMINATED",
        "PROCESS_GROUP_CLEANED_AFTER_TIMEOUT",
    }
