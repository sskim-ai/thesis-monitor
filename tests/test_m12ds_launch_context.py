import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from scripts import m12dr_fresh_blind_reproof as previous
from scripts import m12ds_launch_context as launch
from scripts.m12ds_same_blind_reproof import Reproof


PORTABLE_BASELINE = Path(__file__).resolve().parents[1] / "docs/architecture/M12DS_R5_PORTABLE_HISTORICAL_BASELINES.json"
REVIEWED_ATTESTATION_SHA256 = "ae8d685c86913f39e85c1bdf0ee03b925dfa45b75218fb8f5e8a692e02232efc"


def portable_baseline(payload=None):
    raw = PORTABLE_BASELINE.read_bytes() if payload is None else payload
    # Pin the reviewed resource independently, not a mutable file's own checksum.
    assert sha256(raw).hexdigest() == REVIEWED_ATTESTATION_SHA256, "portable_attestation_identity"
    data = json.loads(raw)
    root = data["clean_root_sha"]
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=previous.REPO)
    assert git("rev-parse", root + "^{tree}").decode().strip() == data["clean_root_tree_sha"]
    git("merge-base", "--is-ancestor", root, "HEAD")
    for key in ("runner", "transport"):
        row = data[key]
        assert sha256(git("show", root + ":" + row["path"])).hexdigest() == row["reviewed_root_file_sha256"]
    return data


def runner_fingerprints(source):
    cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Reproof")
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    fingerprints = {name: sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
                    for name, node in methods.items() if name not in {"invoke", "pass_a"}}
    tail = json.dumps([ast.dump(n, include_attributes=False) for n in methods["pass_a"].body[1:]],
                      separators=(",", ":"))
    return fingerprints, sha256(tail.encode()).hexdigest()


def assert_runner_semantics(source, baseline):
    actual, tail = runner_fingerprints(source)
    for name, expected in baseline["protected_methods"].items():
        assert actual.get(name) == expected, name
    assert tail == baseline["pass_a_validation_tail_sha256"], "pass_a_validation_tail"


def assert_transport_bytes(payload, baseline):
    assert sha256(payload).hexdigest() == baseline["reviewed_root_file_sha256"], "transport_bytes"


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
    baseline = portable_baseline()["runner"]
    assert_runner_semantics((previous.REPO / baseline["path"]).read_text(), baseline)
    for name in ("chain", "core", "before_a", "args", "identity", "pass_a", "before_b", "pass_b"):
        assert getattr(Reproof, name) is getattr(previous.Reproof, name)
    assert "authority_core_schema" not in Reproof.__dict__


def test_original_child_transport_byte_identity():
    baseline = portable_baseline()["transport"]
    assert baseline["path"] == launch.HELPER
    assert_transport_bytes((previous.REPO / launch.HELPER).read_bytes(), baseline)
    assert "read-only" in previous.transport.COMMAND_PREFIX
    assert '--ephemeral' in previous.transport.COMMAND_PREFIX


def test_portable_runner_detects_every_protected_method_mutation():
    baseline = portable_baseline()["runner"]
    source = ast.parse((previous.REPO / baseline["path"]).read_text())
    for name in (*baseline["protected_methods"], "pass_a"):
        changed = deepcopy(source)
        cls = next(n for n in changed.body if isinstance(n, ast.ClassDef) and n.name == "Reproof")
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
        method.body.append(ast.parse("raise RuntimeError('unapproved semantic change')").body[0])
        with pytest.raises(AssertionError):
            assert_runner_semantics(ast.unparse(changed), baseline)


def test_portable_runner_keeps_original_unprotected_scope():
    baseline = portable_baseline()["runner"]
    source = (previous.REPO / baseline["path"]).read_text()
    assert_runner_semantics(source + "\n# nonsemantic comment\n", baseline)
    changed = ast.parse(source)
    cls = next(n for n in changed.body if isinstance(n, ast.ClassDef) and n.name == "Reproof")
    for method in (n for n in cls.body if isinstance(n, ast.FunctionDef)):
        if method.name == "invoke":
            method.body = ast.parse("return None").body
        elif method.name == "pass_a":
            method.body[0] = ast.parse("req = None").body[0]
    assert_runner_semantics(ast.unparse(changed), baseline)


def test_portable_transport_detects_one_byte_mutation():
    baseline = portable_baseline()["transport"]
    raw = (previous.REPO / baseline["path"]).read_bytes()
    with pytest.raises(AssertionError, match="transport_bytes"):
        assert_transport_bytes(raw + b" ", baseline)


@pytest.mark.parametrize("case", ["malformed", "root", "tree", "hash", "fingerprint", "owner", "path"])
def test_portable_attestation_negative_controls(case):
    data = json.loads(PORTABLE_BASELINE.read_bytes())
    if case == "malformed":
        payload = b"{"
    else:
        if case in {"root", "tree"}:
            data["clean_root_sha" if case == "root" else "clean_root_tree_sha"] = "0" * 40
        elif case == "fingerprint":
            data["runner"]["protected_methods"]["chain"] = "0" * 64
        else:
            data["transport"][{"hash": "reviewed_root_file_sha256"}.get(case, case)] = "wrong"
        payload = json.dumps(data).encode()
    with pytest.raises(AssertionError, match="portable_attestation_identity"):
        portable_baseline(payload)


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
