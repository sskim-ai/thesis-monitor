from copy import deepcopy
from pathlib import Path
import subprocess

import pytest

from scripts import packet_only_offline_adapter as adapter


def sample():
    schema = {
        "type": "object",
        "properties": {"X": {"type": "string"}},
        "required": ["X"],
        "additionalProperties": False,
    }
    frozen = {
        "invocation_id": "test-id",
        "executable_sha256": "a" * 64,
        "source_manifest_sha256": "b" * 64,
        "source_prompt_sha256": "c" * 64,
        "task_instructions": "task",
        "evidence": "untrusted evidence",
        "output_schema": schema,
    }
    raw = adapter.canonical(frozen)
    body = {
        "model": adapter.MODEL,
        "reasoning": {"effort": "xhigh"},
        "client_metadata": {
            "session_id": "test-id",
            "thread_id": "test-id",
            "x-codex-installation-id": adapter.POLICY,
            "x-codex-window-id": "test-id",
        },
        "prompt_cache_key": "test-id",
        "include": ["reasoning.encrypted_content"],
        "parallel_tool_calls": False,
        "store": False,
        "stream": True,
        "tool_choice": "auto",
        "text": {"format": {"schema": deepcopy(schema), "strict": True}},
        "input": [{"type": "additional_tools", "role": "developer", "tools": []}]
        + [
            {"type": "message", "role": role, "content": [{"type": "input_text", "text": text}]}
            for role, text in [
                ("developer", "base"),
                ("developer", "task"),
                ("user", "untrusted evidence"),
            ]
        ],
    }
    receipt = {
        "policy": adapter.POLICY,
        "invocation_id": frozen["invocation_id"],
        "approved_input_sha256": adapter.digest(raw),
        "executable_sha256": frozen["executable_sha256"],
        "model": adapter.MODEL,
        "effort": "xhigh",
        "source_manifest_sha256": frozen["source_manifest_sha256"],
        "source_prompt_sha256": frozen["source_prompt_sha256"],
        "static_context_sha256": adapter.digest(b"base"),
        "task_sha256": adapter.digest(b"task"),
        "evidence_sha256": adapter.digest(b"untrusted evidence"),
        "schema_sha256": adapter.digest(adapter.canonical(schema)),
        "auth_access": "NOT_ATTEMPTED",
        "managed_live_policy": "UNRESOLVED_LIVE_BLOCKED",
        "registered_dispatch_handlers": [],
        "host_context_discovery": "NOT_STARTED",
        "gate": "OFFLINE_INSPECT_AND_STOP",
        "transport_stop_code": "PACKET_ONLY_OFFLINE_NO_TRANSPORT",
        "model_transport_attempted": False,
        "execution_authorized": False,
        "managed_composition": {
            "state": "ABSENT_IN_EXPLICIT_SYNTHETIC_INPUT_NOT_LIVE_ABSENCE",
            "layers": [],
            "scope": "SYNTHETIC_CONFIG_ONLY_LIVE_UNRESOLVED",
            "live_policy": "UNRESOLVED_LIVE_BLOCKED",
        },
        "final_request_body": adapter.canonical(body).decode(),
        "final_request_sha256": adapter.digest(adapter.canonical(body)),
    }
    return frozen, raw, body, receipt


def test_receipt_exact_and_full_body_binding():
    frozen, raw, body, receipt = sample()
    assert adapter.verify_receipt(receipt, frozen, raw, "base") == {
        "request_bytes": len(adapter.canonical(body)),
        "request_sha256": adapter.digest(adapter.canonical(body)),
    }
    receipt["final_request_body"] += " "
    with pytest.raises(ValueError, match="RETURNED_BODY_HASH"):
        adapter.verify_receipt(receipt, frozen, raw, "base")


@pytest.mark.parametrize(
    "field,value",
    [
        ("invocation_id", "other"),
        ("executable_sha256", "wrong"),
        ("approved_input_sha256", "wrong"),
        ("schema_sha256", "wrong"),
        ("source_manifest_sha256", "wrong"),
        ("source_prompt_sha256", "wrong"),
        ("model", "other"),
        ("effort", "high"),
        ("gate", "EXECUTE"),
        ("auth_access", "READ"),
        ("model_transport_attempted", True),
        ("execution_authorized", True),
        ("registered_dispatch_handlers", ["shell"]),
    ],
)
def test_receipt_mismatch_rejects(field, value):
    frozen, raw, _, receipt = sample()
    receipt[field] = value
    with pytest.raises(ValueError):
        adapter.verify_receipt(receipt, frozen, raw, "base")


@pytest.mark.parametrize("mutation", ["privilege", "duplicate", "tool", "attachment", "schema"])
def test_rehashed_semantic_mutation_still_rejected(mutation):
    frozen, raw, body, receipt = sample()
    if mutation == "privilege":
        body["input"][-1]["role"] = "developer"
    elif mutation == "duplicate":
        body["input"].append(deepcopy(body["input"][-1]))
    elif mutation == "tool":
        body["input"][0]["tools"] = [{"type": "function", "name": "shell"}]
    elif mutation == "attachment":
        body["input"][-1]["content"][0] = {"type": "input_file", "file_id": "x"}
    else:
        body["text"]["format"]["schema"]["additionalProperties"] = True
    receipt["final_request_body"] = adapter.canonical(body).decode()
    receipt["final_request_sha256"] = adapter.digest(adapter.canonical(body))
    with pytest.raises(ValueError):
        adapter.verify_receipt(receipt, frozen, raw, "base")


@pytest.mark.parametrize("stage,wrapper", [("A", "classifications"), ("B", "decisions")])
def test_source_layout_preserves_utf8_and_never_duplicates(stage, wrapper):
    context = {"subjects": [{"ticker": "X", "evidence": "한글 근거"}]}
    schema = {"properties": {wrapper: {"properties": {"X": {}}}}}
    prompt = (
        f'task\n\nSUBJECT_KEYS:\n["X"]\n\nPASS_{stage}_CONTEXT:\n'
        + adapter.canonical(context["subjects"]).decode()
        + "\n"
    )
    task, evidence = adapter.split_source(prompt, context, schema, stage)
    assert task == "task"
    assert (task + evidence).encode() == prompt.encode()
    context["subjects"][0]["evidence"] = "changed"
    with pytest.raises(ValueError, match="SOURCE_CONTEXT_NOT_EQUIVALENT"):
        adapter.split_source(prompt, context, schema, stage)


@pytest.mark.parametrize("mutation", ["prior", "invocation", "store", "non_strict", "instructions"])
def test_native_serialization_contract_rejects_unapproved_options(mutation):
    frozen, raw, body, receipt = sample()
    if mutation == "prior":
        body["previous_response_id"] = "history"
    elif mutation == "invocation":
        body["client_metadata"]["thread_id"] = "different"
    elif mutation == "store":
        body["store"] = True
    elif mutation == "non_strict":
        body["text"]["format"]["strict"] = False
    else:
        body["instructions"] = "unapproved"
    receipt["final_request_body"] = adapter.canonical(body).decode()
    receipt["final_request_sha256"] = adapter.digest(adapter.canonical(body))
    with pytest.raises(ValueError):
        adapter.verify_receipt(receipt, frozen, raw, "base")


@pytest.mark.parametrize("raw", ['{"x":1,"x":2}', '{"x":NaN}'])
def test_noncanonical_json_rejects(raw):
    with pytest.raises(ValueError):
        adapter.load_json(raw)


def test_bound_binary_rejects_hash_and_symlink(tmp_path):
    binary = tmp_path / "inspector"
    binary.write_bytes(b"binary")
    with pytest.raises(ValueError, match="BOUND_FILE_DRIFT"):
        adapter.bound_file({"path": str(binary), "sha256": "wrong"})
    alias = tmp_path / "alias"
    alias.symlink_to(binary)
    with pytest.raises(ValueError, match="BOUND_FILE_PATH"):
        adapter.bound_file({"path": str(alias), "sha256": adapter.digest(b"binary")})


@pytest.mark.parametrize("failure", ["timeout", "missing", "exit"])
def test_process_failure_stops_without_retry_and_keeps_bytes(tmp_path, monkeypatch, failure):
    frozen, raw, _, _ = sample()
    calls = []
    row = {"id": "A/kr/batch-01", "invocation_id": "test-id"}
    binary = {"path": "/absolute/inspector", "sha256": "frozen"}
    monkeypatch.setattr(
        adapter,
        "load_approval",
        lambda *args: ({"executable": binary}, [(row, frozen, raw, "base")] * 16),
    )
    monkeypatch.setattr(adapter, "bound_file", lambda record: b"binary")

    def fail(args, **kwargs):
        calls.append(args)
        assert args == [binary["path"], "--approved-input-sha256", adapter.digest(raw)]
        assert kwargs["timeout"] == 30
        assert set(kwargs["env"]) == {"HOME", "TMPDIR", "PATH", "LANG"}
        assert list(Path(kwargs["cwd"]).iterdir()) == []
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args, 30, output=b"partial", stderr=b"timeout")
        if failure == "missing":
            raise FileNotFoundError("missing")
        return subprocess.CompletedProcess(args, 1, b"partial", b"rejected")

    monkeypatch.setattr(adapter.subprocess, "run", fail)
    with pytest.raises((ValueError, subprocess.TimeoutExpired, FileNotFoundError)):
        adapter.inspect_approval(tmp_path / "approval.json", "hash", tmp_path / "results")
    assert len(calls) == 1
    directory = tmp_path / "results" / row["id"]
    assert (directory / "process.json").exists()
    assert (directory / "stdout.json").read_bytes() == (b"" if failure == "missing" else b"partial")
