import ast
from pathlib import Path
import subprocess

import pytest

from scripts import m12dr_fresh_blind_reproof as previous
from scripts import m12ds_launch_context as launch
from scripts.m12ds_same_blind_reproof import Reproof


@pytest.mark.parametrize("message,kind", [
    ("attempt to write a readonly database", "OFFICIAL_STATE_DB_READONLY"),
    ("failed to initialize in-process app-server client: Operation not permitted", "APP_SERVER_INITIALIZATION_PERMISSION_DENIED"),
])
def test_startup_denial_is_systemic(message, kind):
    assert launch.known_failure("PROCESS_NONZERO", elapsed=.15, events=b"", final_exists=False, stderr=message) == kind


@pytest.mark.parametrize("override", [
    {"elapsed": 30}, {"events": b'{"type":"thread.started"}'}, {"final_exists": True},
    {"stderr": "ordinary process error"}, {"code": "TRANSPORT_TIMEOUT"},
])
def test_ordinary_nonzero_and_post_dispatch_failure_not_reclassified(override):
    args = dict(code="PROCESS_NONZERO", elapsed=.15, events=b"", final_exists=False,
                stderr="attempt to write a readonly database")
    args.update(override)
    assert launch.known_failure(**args) is None


def test_certificate_regression_stops_even_after_dispatch():
    assert launch.known_failure("TRANSPORT_TIMEOUT", elapsed=1200, events=b'{"type":"thread.started"}',
                                final_exists=False, stderr="Invalid peer certificate: UnknownIssuer") == "CERTIFICATE_TRUST_FAILURE"


def runner(tmp_path):
    instance = object.__new__(Reproof)
    instance.ledger = []
    instance.sealed = tmp_path / "sealed"
    instance.publish = lambda: None
    return instance


@pytest.mark.parametrize("failure", ["SCHEMA_REJECT", "SEMANTIC_REJECT", "TRANSPORT_TIMEOUT", "PROCESS_NONZERO"])
def test_batch_local_failure_keeps_independent_batch_fail_soft(tmp_path, failure):
    instance = runner(tmp_path)

    def fail():
        raise previous.BatchFailure(failure)

    instance.bounded("core", {"market": "us", "batch": 1}, fail)
    instance.bounded("core", {"market": "us", "batch": 2}, lambda: None)
    assert [r["status"] for r in instance.ledger] == ["FAIL", "PASS"]


def test_startup_denial_stops_before_next_batch(tmp_path):
    instance = runner(tmp_path)

    def fail():
        raise previous.SystemicFailure("OFFICIAL_STATE_DB_READONLY")

    with pytest.raises(previous.SystemicFailure):
        for batch in (1, 2):
            instance.bounded("core", {"market": "us", "batch": batch}, fail)
    assert len(instance.ledger) == 1
    assert instance.ledger[0]["status"] == "SYSTEMIC_STOP"


def test_runner_hook_preserves_all_financial_semantic_methods():
    path = "scripts/m12dr_fresh_blind_reproof.py"
    baseline = subprocess.check_output(["git", "show", "df90c148e8f7d3c604354e6001db38640692ebd4:" + path], cwd=previous.REPO, text=True)

    def methods(source):
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Reproof")
        return {n.name: ast.dump(n, include_attributes=False) for n in cls.body if isinstance(n, ast.FunctionDef)}

    before, after = methods(baseline), methods((previous.REPO / path).read_text())
    for name in before.keys() - {"invoke", "pass_a"}:
        assert before[name] == after[name], name
    # R1 only adds frozen-request injection; the validation/materialization tail stays exact.
    def a_tail(source):
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Reproof")
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "pass_a")
        return [ast.dump(n, include_attributes=False) for n in method.body[1:]]
    assert a_tail(baseline) == a_tail((previous.REPO / path).read_text())
    for name in ("chain", "core", "before_a", "args", "identity", "pass_a", "before_b", "pass_b"):
        assert getattr(Reproof, name) is getattr(previous.Reproof, name)
    assert "authority_core_schema" not in Reproof.__dict__


def test_original_child_transport_byte_identity():
    original = subprocess.check_output(["git", "show", "4a700efe205ee46e0c14e31b5e29590bb0d5788f:" + launch.HELPER], cwd=previous.REPO)
    assert original == (previous.REPO / launch.HELPER).read_bytes()
    assert "read-only" in previous.transport.COMMAND_PREFIX
    assert '--ephemeral' in previous.transport.COMMAND_PREFIX


def test_probe_never_changes_state_contents_or_mode(tmp_path):
    path = tmp_path / "state.sqlite"
    path.write_bytes(b"fixture is not an actual sqlite DB")
    before = path.stat()
    result = launch.path_access(path, open_existing=True)
    assert result["effective_open_readwrite_without_write"]
    assert path.read_bytes() == b"fixture is not an actual sqlite DB"
    assert path.stat().st_mode == before.st_mode
    assert path.stat().st_mtime_ns == before.st_mtime_ns


def test_no_transport_calls_or_auth_copy_in_context_probe():
    text = Path(launch.__file__).read_text()
    assert "invoke_official_shadow(" not in text
    assert "chmod(" not in text and "chown(" not in text
