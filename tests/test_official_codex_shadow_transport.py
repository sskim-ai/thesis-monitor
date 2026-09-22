from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import accepted_decision_v2_runtime as runtime
from app.services import official_codex_shadow_transport_service as transport


@pytest.fixture
def invocation(tmp_path, monkeypatch):
    # Installation and login are offline fixtures, not assertions about this host.
    standalone_root = tmp_path / "official-standalone"
    executable = standalone_root / "releases/0.155.1-aarch64-apple-darwin/bin/codex"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"offline installation fixture, never executed")
    executable.chmod(0o700)
    home = tmp_path / "original-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    for key in transport.OVERRIDE_VARIABLES:
        monkeypatch.delenv(key, raising=False)
    cwd = tmp_path / "call" / "approved-input"
    cwd.mkdir(parents=True)
    prompt = cwd / "prompt.txt"
    schema = cwd / "provider-wire-schema.json"
    prompt.write_bytes("frozen UTF-8: 한글\n".encode())
    schema.write_bytes(b'{"type":"object"}')
    qualification = tmp_path / "qualification.json"
    qualification.write_text(
        json.dumps(
            {
                "contract": transport.QUALIFICATION_CONTRACT,
                "release_tag": transport.RELEASE_TAG,
                "package_sha256": transport.PACKAGE_SHA256,
                "checksum_manifest_sha256": transport.CHECKSUM_MANIFEST_SHA256,
                "provenance_status": "PASS",
                "executable": str(executable),
                "executable_sha256": transport.file_sha256(executable),
                "version": transport.SUPPORTED_VERSION,
                "standalone_root": str(standalone_root),
                "config_schema_sha256": transport.CONFIG_SCHEMA_SHA256,
                "command_prefix": list(transport.COMMAND_PREFIX),
                "required_tail_flags": ["--output-schema", "-o", "-"],
                "auth_status": "CHATGPT_AUTH_CONFIRMED",
                "fixture_only": True,
            }
        )
    )
    binding = transport.OfficialCodexBinding(
        executable,
        transport.file_sha256(executable),
        transport.SUPPORTED_VERSION,
        "CHATGPT_LOCAL_CONFIRMED",
        str(home),
        None,
        None,
        installation_verified=True,
        qualification_path=qualification,
        qualification_sha256=transport.file_sha256(qualification),
    )
    return dict(
        codex_bin=str(executable),
        prompt=prompt,
        schema=schema,
        cwd=cwd,
        output=cwd.parent / "raw-output.json",
        log=cwd.parent / "events.jsonl",
        timeout=1200,
        state_namespace="offline-request",
        official_shadow=transport.OfficialShadowRequest(
            binding,
            "offline-request",
            transport.file_sha256(prompt),
            transport.file_sha256(schema),
        ),
    )


def test_actual_shared_boundary_single_attempt_original_credentials(invocation, monkeypatch):
    calls = []

    def capture(argv, **kwargs):
        calls.append((argv, kwargs))
        assert "env" not in kwargs and "shell" not in kwargs
        assert kwargs["input"] == invocation["prompt"].read_bytes()
        assert kwargs["timeout"] == 1200
        assert kwargs["cwd"] == invocation["cwd"]
        assert set(kwargs["cwd"].iterdir()) == {invocation["prompt"], invocation["schema"]}
        assert argv[argv.index("--output-schema") + 1] == str(invocation["schema"])
        assert argv[argv.index("-m") + 1] == "gpt-5.6-sol"
        assert 'model_reasoning_effort="xhigh"' in argv
        assert "--json" in argv and "--ephemeral" in argv
        assert "--ignore-rules" in argv and "--ignore-user-config" in argv
        assert tuple(argv[1 : 1 + len(transport.COMMAND_PREFIX)]) == transport.COMMAND_PREFIX
        Path(argv[argv.index("-o") + 1]).write_text('{"answer":"fixture"}')
        kwargs["stdout"].write(b'{"type":"thread.started"}\n{"type":"turn.completed"}\n')
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(transport.subprocess, "run", capture)
    receipt = runtime._invoke_signed_in_codex(**invocation)
    assert len(calls) == receipt["transport_attempts"] == 1
    assert receipt["network_probe_attempts"] == 0
    assert receipt["input_boundary"]["source_only_inference_certified"] is False
    assert (
        receipt["qualification_sha256"]
        == invocation["official_shadow"].binding.qualification_sha256
    )
    assert len(receipt["invocation_identity_sha256"]) == 64
    assert json.loads(invocation["output"].read_bytes()) == {"answer": "fixture"}
    with pytest.raises(transport.OfficialShadowError, match="OUTPUT_NOT_EXCLUSIVE"):
        runtime._invoke_signed_in_codex(**invocation)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "kind,code",
    [
        ("executable", "OFFICIAL_EXECUTABLE_MISMATCH"),
        ("installation", "OFFICIAL_INSTALLATION_UNVERIFIED"),
        ("binary", "OFFICIAL_EXECUTABLE_DRIFT"),
        ("version", "OFFICIAL_OPTIONS_REVIEW_REQUIRED"),
        ("api", "AUTH_OR_PROVIDER_OVERRIDE_PRESENT"),
        ("unknown", "CHATGPT_AUTH_UNVERIFIED"),
        ("api_auth", "CHATGPT_AUTH_UNVERIFIED"),
        ("logged_out", "CHATGPT_AUTH_UNVERIFIED"),
        ("home", "CREDENTIAL_STORE_DRIFT"),
        ("config", "USER_CONFIG_MUST_BE_IGNORED"),
        ("qualification_missing", "OFFICIAL_QUALIFICATION_MISSING"),
        ("qualification_drift", "OFFICIAL_QUALIFICATION_DRIFT"),
        ("world_writable", "OFFICIAL_INSTALLATION_UNVERIFIED"),
        ("prompt", "PROMPT_DRIFT"),
        ("schema", "SCHEMA_DRIFT"),
        ("old_output", "OUTPUT_NOT_EXCLUSIVE"),
        ("old_symlink", "OUTPUT_NOT_EXCLUSIVE"),
        ("extra_file", "UNDECLARED_INPUT_PRESENT"),
        ("input_symlink", "UNDECLARED_INPUT_PRESENT"),
        ("repository", "INPUT_CWD_INSIDE_REPOSITORY"),
        ("identity", "REQUEST_ID_OR_TIMEOUT_DRIFT"),
        ("timeout", "REQUEST_ID_OR_TIMEOUT_DRIFT"),
    ],
)
def test_preflight_denials_never_spawn(invocation, monkeypatch, kind, code):
    request = invocation["official_shadow"]
    if kind == "executable":
        invocation["codex_bin"] = "/tmp/custom-native"
    elif kind in {"installation", "binary", "version", "unknown", "api_auth", "logged_out"}:
        updates = {
            "installation": {"installation_verified": False},
            "binary": {"executable_sha256": "0" * 64},
            "version": {"version": "new-version"},
            "unknown": {"auth_method": "UNKNOWN"},
            "api_auth": {"auth_method": "API_KEY"},
            "logged_out": {"auth_method": "NOT_LOGGED_IN"},
        }
        invocation["official_shadow"] = replace(
            request, binding=replace(request.binding, **updates[kind])
        )
    elif kind == "api":
        monkeypatch.setenv("OPENAI_API_KEY", "fixture-not-a-key")
    elif kind == "home":
        monkeypatch.setenv("CODEX_HOME", "/tmp/other-store")
    elif kind == "config":
        invocation["official_shadow"] = replace(
            request, binding=replace(request.binding, user_config_sha256="old-config-binding")
        )
    elif kind == "qualification_missing":
        invocation["official_shadow"] = replace(
            request, binding=replace(request.binding, qualification_path=None)
        )
    elif kind == "qualification_drift":
        request.binding.qualification_path.write_text("{}")
    elif kind == "world_writable":
        request.binding.executable.chmod(0o777)
    elif kind in {"prompt", "schema"}:
        invocation[kind].write_bytes(b"changed")
    elif kind == "old_output":
        invocation["output"].write_bytes(b'{"old":true}')
    elif kind == "old_symlink":
        invocation["output"].symlink_to("missing-old-output")
    elif kind == "extra_file":
        (invocation["cwd"] / "prior-answer.json").write_bytes(b"{}")
    elif kind == "input_symlink":
        original = invocation["prompt"].read_bytes()
        invocation["prompt"].unlink()
        external = invocation["cwd"].parent / "external.txt"
        external.write_bytes(original)
        invocation["prompt"].symlink_to(external)
    elif kind == "repository":
        (invocation["cwd"].parent / ".git").write_text("gitdir: elsewhere")
    elif kind == "identity":
        invocation["state_namespace"] = "different-batch"
    elif kind == "timeout":
        invocation["timeout"] = 3600
    called = []
    monkeypatch.setattr(transport.subprocess, "run", lambda *a, **k: called.append(a))
    with pytest.raises(transport.OfficialShadowError, match=code) as result:
        runtime._invoke_signed_in_codex(**invocation)
    assert result.value.process_started is False
    assert called == []


@pytest.mark.parametrize(
    "mode,code",
    [
        ("timeout", "TRANSPORT_TIMEOUT"),
        ("nonzero", "PROCESS_NONZERO"),
        ("empty", "FINAL_OUTPUT_EMPTY"),
        ("malformed", "FINAL_OUTPUT_MALFORMED"),
        ("list", "FINAL_OUTPUT_MALFORMED"),
        ("tool", "UNDECLARED_INPUT_OBSERVED"),
        ("unknown_event", "INPUT_BOUNDARY_UNVERIFIED"),
        ("start", "PROCESS_START_FAILED"),
    ],
)
def test_failed_invocation_no_retry_or_old_final(invocation, monkeypatch, mode, code):
    calls = []

    def capture(argv, **kwargs):
        calls.append(argv)
        if mode == "timeout":
            raise subprocess.TimeoutExpired(argv, 1200)
        if mode == "start":
            raise OSError("fixture start failure")
        data = {"empty": b"", "malformed": b"not json", "list": b"[]"}.get(mode, b"{}")
        invocation["output"].write_bytes(data)
        if mode == "tool":
            kwargs["stdout"].write(b'{"type":"item.completed","item":{"type":"web_search"}}\n')
        if mode == "unknown_event":
            kwargs["stdout"].write(b'{"type":"future.event"}\n')
        return SimpleNamespace(returncode=1 if mode == "nonzero" else 0)

    monkeypatch.setattr(transport.subprocess, "run", capture)
    with pytest.raises(transport.OfficialShadowError, match=code):
        runtime._invoke_signed_in_codex(**invocation)
    assert len(calls) == 1
    with pytest.raises(transport.OfficialShadowError, match="OUTPUT_NOT_EXCLUSIVE"):
        runtime._invoke_signed_in_codex(**invocation)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "events,state",
    [
        (b"", "INPUT_BOUNDARY_UNVERIFIED"),
        (b"not-json", "INPUT_BOUNDARY_UNVERIFIED"),
        (b'{"type":"new.event"}', "INPUT_BOUNDARY_UNVERIFIED"),
        (
            b'{"type":"thread.started"}\n{"type":"turn.completed"}',
            "DECLARED_INPUT_WITH_DOCUMENTED_RUNTIME_LIMITS",
        ),
        (
            b'{"type":"item.started","item":{"type":"command_execution"}}',
            "UNDECLARED_INPUT_OBSERVED",
        ),
    ],
)
def test_event_classification_never_certifies_isolation(events, state):
    result = transport.classify_input_events(events)
    assert result["state"] == state
    assert result["source_only_inference_certified"] is False


@pytest.mark.parametrize(
    "config",
    [
        'model_provider="alternate"',
        'profile="alternate"',
        'forced_login_method="api"',
        'model_instructions_file="/tmp/old-answer.txt"',
    ],
)
def test_user_config_is_not_read_when_verified_ignore_flag_is_required(
    invocation, monkeypatch, config
):
    request = invocation["official_shadow"]
    path = Path(request.binding.home) / ".codex" / "config.toml"
    path.parent.mkdir()
    path.write_text(config)
    original_read = Path.read_bytes

    def read_bytes(candidate):
        assert candidate != path, "ignored user config read"
        return original_read(candidate)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(Path, "read_text", lambda *a, **k: pytest.fail("unexpected text read"))
    transport.validate_binding(request.binding, invocation["codex_bin"])


@pytest.mark.parametrize(
    "key,value,code",
    [
        ("provenance_status", "UNKNOWN", "OFFICIAL_PROVENANCE_UNVERIFIED"),
        ("package_sha256", "0" * 64, "OFFICIAL_PROVENANCE_UNVERIFIED"),
        ("release_tag", "rust-v0.155.2", "OFFICIAL_PROVENANCE_UNVERIFIED"),
        ("executable", "/tmp/unqualified", "OFFICIAL_EXECUTABLE_MISMATCH"),
        ("standalone_root", "/tmp/unqualified", "OFFICIAL_EXECUTABLE_MISMATCH"),
        ("config_schema_sha256", "0" * 64, "OFFICIAL_REQUIRED_CONTROL_UNVERIFIED"),
        ("command_prefix", ["exec"], "OFFICIAL_REQUIRED_CONTROL_UNVERIFIED"),
        ("required_tail_flags", [], "OFFICIAL_REQUIRED_CONTROL_UNVERIFIED"),
        ("auth_status", "API_KEY_AUTH_OBSERVED", "CHATGPT_AUTH_UNVERIFIED"),
    ],
)
def test_qualified_receipt_fields_are_enforced(invocation, monkeypatch, key, value, code):
    request = invocation["official_shadow"]
    path = request.binding.qualification_path
    receipt = json.loads(path.read_bytes())
    receipt[key] = value
    path.write_text(json.dumps(receipt))
    invocation["official_shadow"] = replace(
        request, binding=replace(request.binding, qualification_sha256=transport.file_sha256(path))
    )
    monkeypatch.setattr(
        transport.subprocess, "run", lambda *a, **k: pytest.fail("must fail before spawn")
    )
    with pytest.raises(transport.OfficialShadowError, match=code):
        runtime._invoke_signed_in_codex(**invocation)


def test_prompt_mutation_during_invocation_is_not_accepted(invocation, monkeypatch):
    def capture(argv, **kwargs):
        invocation["prompt"].write_bytes(b"changed after freeze")
        invocation["output"].write_bytes(b"{}")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(transport.subprocess, "run", capture)
    with pytest.raises(transport.OfficialShadowError, match="INPUT_CHANGED_DURING_INVOCATION"):
        runtime._invoke_signed_in_codex(**invocation)
