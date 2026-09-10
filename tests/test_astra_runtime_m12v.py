from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
import json
import os
import sys

import pytest

from app.services.codex_transport_lifecycle_service import invoke_instrumented_codex
from scripts import astra_runtime_adapter_m12v as a
from scripts import astra_runtime_m12v as v


@dataclass
class Readiness:
    ready: bool = True
    attempts: int = 1
    resolved_address_count: int = 1
    failure_type: str | None = None


@pytest.fixture
def call(tmp_path, monkeypatch):
    audit = {
        "invocation_id": "test",
        "runtime_state_namespace_hash": "unique",
        "working_directory_identity": "unique",
    }
    identity = SimpleNamespace(runtime_state_namespace="unique", audit_dict=lambda: audit)
    monkeypatch.setattr(
        a.u.m12,
        "prepare_codex_runtime_state",
        lambda *args, **kwargs: SimpleNamespace(
            environment=lambda: dict(os.environ), audit_dict=lambda: {"test": True}
        ),
    )
    monkeypatch.setattr(
        a.u.m12,
        "codex_tls_environment",
        lambda env: SimpleNamespace(environment=env, trust_source="test"),
    )
    monkeypatch.setattr(a.u.m12, "probe_codex_network_readiness", lambda: Readiness())
    prompt, schema = tmp_path / "prompt", tmp_path / "schema"
    prompt.write_text("fictional payload " * 4000)
    schema.write_text("{}")
    args = dict(
        codex_bin=sys.executable,
        prompt=prompt,
        schema=schema,
        output=tmp_path / "output",
        log=tmp_path / "transport.log",
        receipt_path=tmp_path / "receipt.json",
        working_directory=tmp_path / "work",
        runtime_state_root=tmp_path / "state",
        isolation_registry=SimpleNamespace(claim=lambda **kwargs: identity),
        invocation_id="20260910-m12v-fictional-test:run-1:context-01",
        base_namespace="fictional-test",
    )

    def install(code, timeout=4):
        def invoke(invocation):
            assert invocation.timeout_seconds == 2400
            assert invocation.subject_count == 4
            assert invocation.model == "gpt-6-astra"
            assert invocation.reasoning_effort == "xhigh"
            assert "--json" not in invocation.command
            local = replace(
                invocation,
                command=(sys.executable, "-c", code, str(args["output"])),
                timeout_seconds=timeout,
                cleanup_margin_seconds=1,
            )
            return invoke_instrumented_codex(local)

        monkeypatch.setattr(a, "invoke_instrumented_codex", invoke)

    return args, install


HEADER = "print('model: gpt-6-astra\\nreasoning effort: xhigh\\nsession id: fictional-test\\nuser\\n', file=sys.stderr, flush=True); "


def test_adapter_preserves_payload_and_observes_streams(call):
    args, install = call
    install(
        "import sys,json; p=sys.stdin.read(); "
        + HEADER
        + "print('final',flush=True); open(sys.argv[1],'w').write(json.dumps({'payload':p}))"
    )
    receipt = a.single_attempt(**args)
    assert receipt["status"] == "PASS"
    assert json.loads(args["output"].read_text())["payload"] == args["prompt"].read_text()
    assert receipt["lifecycle"]["elapsed_to_first_stdout_seconds"] is not None
    assert receipt["lifecycle"]["elapsed_to_first_stderr_seconds"] is not None
    assert receipt["orphan_process_count"] == 0
    assert receipt["wrapper_retry_count"] == 0
    assert receipt["backend_progress_state"] == "NOT_MEASURED"
    assert receipt["local_output_observation"] == "FINAL_OUTPUT_COMPLETE"
    with pytest.raises(ValueError, match="existing_artifact"):
        a.single_attempt(**args)


def test_adapter_timeout_is_one_attempt_and_no_orphan(call):
    args, install = call
    install("import sys,time; sys.stdin.read(); " + HEADER + "time.sleep(30)", timeout=1)
    with pytest.raises(RuntimeError, match="model_context_failed"):
        a.single_attempt(**args)
    receipt = json.loads(args["receipt_path"].read_text())
    assert receipt["timed_out"] is True
    assert receipt["orphan_process_count"] == 0
    assert receipt["wrapper_retry_count"] == 0
    assert receipt["cli_internal_retry_event_count"] == 0
    assert receipt["local_output_observation"] == "LOCAL_STDERR_ACTIVITY_NO_FINAL_OUTPUT"
    assert receipt["backend_progress_state"] == "NOT_MEASURED"
    assert receipt["lifecycle"]["elapsed_to_first_stdout_seconds"] is None


def test_adapter_wrong_advertised_model_fails(call):
    args, install = call
    install(
        "import sys; sys.stdin.read(); print('model: wrong\\nreasoning effort: xhigh',file=sys.stderr); open(sys.argv[1],'w').write('{}')"
    )
    with pytest.raises(RuntimeError, match="MODEL_IDENTITY"):
        a.single_attempt(**args)


def test_adapter_missing_output_not_pass(call):
    args, install = call
    install("import sys; sys.stdin.read(); " + HEADER)
    with pytest.raises(RuntimeError):
        a.single_attempt(**args)
    assert json.loads(args["receipt_path"].read_text())["status"] == "FAIL"


def test_adapter_nonfictional_rejected_before_spawn(call):
    args, _ = call
    args["invocation_id"] = "real-cohort:run-1:context-01"
    with pytest.raises(ValueError, match="fictional"):
        a.single_attempt(**args)


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({}, "NO_LOCAL_STREAM_ACTIVITY"),
        ({"stderr_bytes": 4}, "LOCAL_STDERR_ACTIVITY_NO_FINAL_OUTPUT"),
        ({"stdout_bytes": 4}, "LOCAL_STDOUT_ACTIVITY_NO_FINAL_OUTPUT"),
        ({"output_bytes": 4}, "FINAL_OUTPUT_PARTIAL"),
        ({"output_parsed": True}, "FINAL_OUTPUT_COMPLETE"),
    ],
)
def test_observation_does_not_invent_backend_progress(payload, expected):
    assert a.output_observation(payload) == expected


def test_runtime_contract_preserves_semantics_and_has_finite_budget():
    root = v.read(v.ROOT)
    assert root["selected_timeout_seconds"] == 2400 <= 2 * root["old_timeout_seconds"]
    assert root["wrapper_retry_count"] == 0
    assert root["subjects_per_context"] == 4
    assert (
        root["semantic_freeze"]["target_buys"] == v.read(v.u.ROOT)["expectation"]["all_target_buys"]
    )
    assert sum(o["selected"] for o in root["options"]) == 1
    assert root["event_capability"]["backend_progress_heartbeat"] is False


def test_scoped_modules_do_not_import_production_side_effects():
    import ast

    for path in ("scripts/astra_runtime_adapter_m12v.py", "scripts/astra_runtime_m12v.py"):
        tree = ast.parse(Path(path).read_text())
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any("telegram" in m or "notification" in m or "database" in m for m in imports)


def test_run_restores_existing_runner_ownership(monkeypatch):
    original = v.u.m12._single_attempt_model_call
    old_output = v.u.f.OUTPUT

    def stop():
        assert v.u.m12._single_attempt_model_call is a.single_attempt
        raise RuntimeError("test stop")

    monkeypatch.setattr(v.u.f, "run", stop)
    with pytest.raises(RuntimeError, match="test stop"):
        v.run()
    assert v.u.m12._single_attempt_model_call is original
    assert v.u.f.OUTPUT == old_output
