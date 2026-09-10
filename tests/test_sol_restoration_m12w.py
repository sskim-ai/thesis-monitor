from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
import json
import os
import sys

import pytest

from app.services.codex_transport_lifecycle_service import invoke_instrumented_codex
from scripts import sol_runtime_adapter_m12w as a
from scripts import sol_restoration_m12w as v


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
        invocation_id="20260910-m12w-fictional-test:run-1:context-01",
        base_namespace="fictional-test",
    )

    def install(code, timeout=4):
        def invoke(invocation):
            assert invocation.timeout_seconds == 1800
            assert invocation.subject_count == 4
            assert invocation.model == "gpt-5.6-sol"
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


HEADER = "print('model: gpt-5.6-sol\\nreasoning effort: xhigh\\nsession id: fictional-test\\nuser\\n', file=sys.stderr, flush=True); "


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


def test_runtime_contract_preserves_semantics_and_restores_sol():
    root = v.read(v.ROOT)
    assert (root["model"], root["effort"]) == ("gpt-5.6-sol", "xhigh")
    assert root["selected_timeout_seconds"] == 1800
    assert root["previous_astra_timeout_seconds"] == 2400
    assert root["wrapper_retry_count"] == 0
    assert root["subjects_per_context"] == 4
    assert (
        root["semantic_freeze"]["target_buys"]
        == v.read(v.u.ROOT)["expectation"]["all_target_buys"]
    )
    assert root["runtime_instrumentation"]["backend_progress_heartbeat"] is False
    assert root["astra"]["proof_critical_status"] == "SUSPENDED_FROM_PROOF_CRITICAL_PATH"
    assert root["astra"]["model_calls_in_m12w"] == 0


def test_scoped_modules_do_not_import_production_side_effects():
    import ast

    for path in ("scripts/sol_runtime_adapter_m12w.py", "scripts/sol_restoration_m12w.py"):
        tree = ast.parse(Path(path).read_text())
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any("telegram" in m or "notification" in m or "database" in m for m in imports)


def test_run_restores_existing_runner_ownership(monkeypatch):
    original = v.u.m12._single_attempt_model_call
    old_output = v.u.f.OUTPUT
    monkeypatch.setattr(
        v,
        "read",
        lambda _path: {
            "status": "PASS",
            "code_file_sha256": {},
            "config_file_sha256": {},
        },
    )

    def stop():
        assert v.u.m12._single_attempt_model_call is a.single_attempt
        raise RuntimeError("test stop")

    monkeypatch.setattr(v.u.f, "run", stop)
    with pytest.raises(RuntimeError, match="test stop"):
        v.run()
    assert v.u.m12._single_attempt_model_call is original
    assert v.u.f.OUTPUT == old_output


def test_required_report_contract_has_69_unique_entries():
    assert sorted(v.SLUGS) == list(range(1, 70))
    assert len(set(v.SLUGS.values())) == 69


def test_existing_semantic_files_are_unchanged_from_m12v_base():
    result = v.freeze()
    assert result["status"] == "PASS"
    assert result["financial_semantic_change_count"] == 0
    assert result["directional_semantic_change_count"] == 0
    assert result["fictional_case_change_count"] == 0


def test_mutable_project_state_is_not_classified_as_financial_semantics():
    result = v.freeze()
    assert "docs/project-state.json" not in result["existing_file_sha256"]
    assert "docs/project-state.json" not in result["changed_existing_paths"]


def test_authoring_provenance_matches_requested_target():
    root = v.read(v.ROOT)
    assert root["authoring"]["status"] == "PASS"
    assert (root["authoring"]["model"], root["authoring"]["effort"]) == (
        "gpt-5.6-sol",
        "xhigh",
    )


def test_historical_sol_evidence_is_verified():
    result = v.historical_sol()
    assert result["status"] == "PASS"
    assert result["m12d_completed_context_count"] == 6
    assert result["m12d_timeout_count"] == 0
