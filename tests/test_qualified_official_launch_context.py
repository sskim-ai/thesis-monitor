"""Synthetic qualification evidence only; never claim a live child was audited."""
from copy import deepcopy
from dataclasses import replace

import pytest

from scripts import qualified_official_launch_context as q


@pytest.fixture
def inputs():
    env = {name: {"present": True, "sha256": q.digest(name)}
           for name in ("CODEX_SANDBOX", "HTTPS_PROXY", "SSL_CERT_FILE")}
    actual_env = deepcopy(env)
    actual_env["CODEX_SANDBOX"] = {"present": False, "sha256": None}
    identity = q.LaunchIdentity(**{key: q.digest(key) for key in (
        "implementation_sha", "whole_source_sha256", "source_only_zip_sha256", "request_freeze_sha256",
        "prompt_schema_sha256", "executable_sha256", "launcher_sha256", "qualification_sha256", "cwd_sha256")},
        source_generation_id="fictional-same-sealed-generation")
    prep = dict(uid=501, gid=20, state_access=dict(path_sha256="state", uid=501, gid=20, mode="0o600"),
                safe_environment=env, home_access=dict(path_sha256="home"),
                codex_home_access=dict(path_sha256="codex-home"))
    context = dict(contract=q.CONTRACT, at="time-1", pid=123, uid=501, gid=20,
        cwd_sha256=identity.cwd_sha256, home_sha256="home", codex_home_sha256="codex-home",
        codex_home_env=dict(present=False, sha256=None), state_path_sha256="state",
        state_owner_mode=[501, 20, 0o600], state_read_ready=True,
        state_probe_open_flags="O_RDONLY|O_NOFOLLOW", state_probe_write_calls=0,
        state_permissions_modified=False, safe_environment=actual_env)
    return dict(identity=identity, expected_identity=identity, preparation=prep,
        preparation_sha256="frozen-prep", actual_preparation_sha256="frozen-prep",
        context=context, entry_environment=deepcopy(actual_env),
        state_evidence=q.StateWriteEvidence("PARENT_AND_OFFICIAL_CHILD", 0, 0,
            "synthetic-proof-not-live-evidence", identity.executable_sha256, identity.launcher_sha256),
        binding_verified=True, provider_calls=0, secret_scan_passed=True)


def test_qualified_transition_freeze_and_stability(inputs):
    frozen = q.QualifiedOfficialModelLaunchContext.qualify(**inputs)
    assert frozen.transition_differences == ("CODEX_SANDBOX",)
    receipt = frozen.receipt()
    receipt["context"]["safe_environment"].clear()
    assert frozen.receipt()["context"]["safe_environment"]
    context = {**inputs["context"], "at": "time-2"}
    result = frozen.verify(context=context, identity=inputs["identity"],
        preparation_sha256="frozen-prep", freeze_sha256=frozen.sha256)
    assert result["status"] == "PASS"


@pytest.mark.parametrize("key", ["HTTPS_PROXY", "SSL_CERT_FILE", "unexpected_inventory_key"])
def test_unexpected_transition_never_adaptively_allowed(inputs, key):
    inputs["context"]["safe_environment"][key] = {"present": True, "sha256": "changed"}
    inputs["entry_environment"] = deepcopy(inputs["context"]["safe_environment"])
    with pytest.raises(q.LaunchQualificationError, match="TRANSITION_GAP"):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


@pytest.mark.parametrize("key", ["uid", "gid", "home_sha256", "state_path_sha256"])
def test_identity_transition_rejects(inputs, key):
    inputs["context"][key] = 999 if key in {"uid", "gid"} else "wrong"
    with pytest.raises(q.LaunchQualificationError, match="TRANSITION_GAP"):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


@pytest.mark.parametrize("key", ["source_generation_id", "request_freeze_sha256", "whole_source_sha256",
    "source_only_zip_sha256", "implementation_sha", "prompt_schema_sha256", "model", "effort"])
def test_source_request_code_policy_mismatch_rejects(inputs, key):
    inputs["identity"] = replace(inputs["identity"], **{key: "drift"})
    with pytest.raises(q.LaunchQualificationError, match="REQUEST_FREEZE_IDENTITY_GAP"):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


@pytest.mark.parametrize("marker", [{"present": True, "sha256": "spoofed"}, None])
def test_manual_marker_override_or_deletion_rejects(inputs, marker):
    if marker is None:
        inputs["context"]["safe_environment"].pop("CODEX_SANDBOX")
    else:
        inputs["context"]["safe_environment"]["CODEX_SANDBOX"] = marker
    with pytest.raises(q.LaunchQualificationError, match="QUALIFICATION_GAP"):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


def test_old_receipt_rewrite_rejects(inputs):
    inputs["actual_preparation_sha256"] = "rewritten"
    with pytest.raises(q.LaunchQualificationError, match="TRANSITION_GAP"):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


@pytest.mark.parametrize("change", [dict(scope="PARENT_PROBE_ONLY"), dict(write_calls=None),
    dict(write_calls=1), dict(permission_mutations=1), dict(proof_sha256=None),
    dict(executable_sha256="other"), dict(launcher_sha256="other")])
def test_state_proof_missing_partial_wrong_owner_or_nonzero_rejects(inputs, change):
    inputs["state_evidence"] = replace(inputs["state_evidence"], **change)
    with pytest.raises(q.LaunchQualificationError, match="QUALIFICATION_GAP"):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


@pytest.mark.parametrize("key,value", [("state_read_ready", False), ("state_probe_write_calls", 1),
    ("state_permissions_modified", True)])
def test_state_access_fail_closed(inputs, key, value):
    inputs["context"][key] = value
    with pytest.raises(q.LaunchQualificationError):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


@pytest.mark.parametrize("key,value", [("binding_verified", False), ("secret_scan_passed", False),
                                        ("provider_calls", 1)])
def test_unqualified_same_marker_still_fails(inputs, key, value):
    inputs["preparation"]["safe_environment"] = deepcopy(inputs["context"]["safe_environment"])
    inputs[key] = value
    with pytest.raises(q.LaunchQualificationError):
        q.QualifiedOfficialModelLaunchContext.qualify(**inputs)


@pytest.mark.parametrize("key", ["safe_environment", "state_owner_mode", "pid", "cwd_sha256",
                                  "codex_home_env", "state_read_ready"])
def test_immediate_post_freeze_drift_rejects(inputs, key):
    frozen = q.QualifiedOfficialModelLaunchContext.qualify(**inputs)
    context = deepcopy(inputs["context"])
    context[key] = "drift"
    with pytest.raises(q.LaunchQualificationError, match="POST_FREEZE_CONTEXT_DRIFT"):
        frozen.verify(context=context, identity=inputs["identity"],
                      preparation_sha256="frozen-prep", freeze_sha256=frozen.sha256)


def test_read_probe_never_opens_state_writable(tmp_path, monkeypatch):
    home = tmp_path / "home"
    store = home / ".codex"
    store.mkdir(parents=True)
    state = store / "state_5.sqlite"
    state.write_bytes(b"synthetic-non-sqlite")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    real_open = q.os.open
    flags = []
    def guarded(path, mode, *args, **kwargs):
        flags.append(mode)
        assert mode & q.os.O_ACCMODE == q.os.O_RDONLY
        return real_open(path, mode, *args, **kwargs)
    monkeypatch.setattr(q.os, "open", guarded)
    result = q.capture_context(["CODEX_SANDBOX"])
    assert result["state_read_ready"] and len(flags) == 1
    assert result["state_probe_write_calls"] == 0
    assert state.read_bytes() == b"synthetic-non-sqlite"
