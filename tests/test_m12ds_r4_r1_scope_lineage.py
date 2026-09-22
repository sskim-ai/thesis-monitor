from pathlib import Path
from copy import deepcopy
import json
import os
import subprocess

import pytest

from scripts.approved_scope_descendants import PINS, approved_descendant
from scripts import approved_scope_descendants as guard
from scripts import financial_exclusion_expectation_m12u as u
from scripts import sol_restoration_m12w as w
from scripts import boundary_band_application_scope_m12aa as aa
from scripts import leverage_hold_sell_boundary_m12ab as ab


# Isolated real Git graphs keep this contract test independent of checkout depth.
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    return subprocess.check_output(["git", "-c", "user.name=Provenance Test", "-c",
                                    "user.email=provenance@example.invalid", "-c",
                                    "commit.gpgsign=false", *args], cwd=repo, env=env,
                                   stderr=subprocess.DEVNULL).decode().strip()


def commit(repo, message):
    git(repo, "add", ".")
    git(repo, "commit", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def clean_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    parent = commit(repo, "parent")
    for path in PINS:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((SOURCE_ROOT / path).read_bytes())
    workflow = repo / guard.WORKFLOW_PATH
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_bytes(subprocess.check_output(
        ["git", "show", guard.CLEAN_IDENTITY["clean_root_sha"] + ":" + guard.WORKFLOW_PATH], cwd=SOURCE_ROOT))
    root = commit(repo, "reviewed clean root")
    identity = {**guard.CLEAN_IDENTITY, "clean_root_sha": root,
                "clean_root_tree_sha": git(repo, "rev-parse", "HEAD^{tree}"), "parent_main_sha": parent}
    attestation = {**identity, "protected_paths": [
        {"path": path, "owner": owner, "historical_pin": pin, "sha256": guard.REVIEWED_HASHES[path]}
        for path, (owner, pin) in PINS.items()]}
    document = tmp_path / "attestation.json"
    document.write_text(json.dumps(attestation))
    monkeypatch.chdir(repo)
    monkeypatch.setattr(guard, "CLEAN_IDENTITY", identity)
    monkeypatch.setattr(guard, "ATTESTATION_PATH", document)
    return repo, attestation, document


def test_approved_descendants_require_exact_ancestor_blobs(clean_repo):
    for path in PINS:
        receipt = approved_descendant(path)
        assert receipt and receipt["clean_root_ancestor_verified"], path
        assert receipt["ancestor_verified"] is False
    assert approved_descendant("app/services/daily_monitor_service.py") is None


def test_clean_descendant_and_missing_private_objects(clean_repo, monkeypatch):
    repo, _, _ = clean_repo
    commit(repo, "public descendant")
    for _, pin in PINS.values():
        with pytest.raises(subprocess.CalledProcessError):
            git(repo, "cat-file", "-e", pin + "^{commit}")
    calls, original = [], guard._git

    def traced(*args):
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(guard, "_git", traced)
    for path in PINS:
        assert approved_descendant(path)["provenance_mode"] == "REVIEWED_CLEAN_HISTORY"
    assert not any(pin in " ".join(args) for args in calls for _, pin in PINS.values())


@pytest.mark.parametrize("path", list(PINS))
def test_clean_mutation_rejected_for_every_owner(clean_repo, path):
    target = Path(path)
    target.write_bytes(target.read_bytes() + b"\n# unapproved\n")
    assert approved_descendant(path) is None


@pytest.mark.parametrize("case", ["root", "tree", "parent", "hash", "owner", "path", "missing_row",
                                 "missing_file", "malformed", "duplicate_key", "mode", "reference", "extra"])
def test_bad_attestation_fail_closed(clean_repo, case):
    _, original, document = clean_repo
    row = deepcopy(original)
    if case in {"root", "tree", "parent", "reference"}:
        key = {"root": "clean_root_sha", "tree": "clean_root_tree_sha",
               "parent": "parent_main_sha", "reference": "approved_reference_sha"}[case]
        row[key] = "0" * 40
    elif case in {"hash", "owner", "path"}:
        row["protected_paths"][0][{"hash": "sha256"}.get(case, case)] = "wrong"
    elif case == "missing_row":
        row["protected_paths"].pop()
    elif case == "missing_file":
        document.unlink()
    elif case == "malformed":
        document.write_text("{")
    elif case == "duplicate_key":
        document.write_text('{"mode":"wrong",' + json.dumps(row)[1:])
    elif case == "mode":
        row["mode"] = "UNSUPPORTED"
    else:
        row["extra"] = True
    if case not in {"missing_file", "malformed", "duplicate_key"}:
        document.write_text(json.dumps(row))
    assert all(approved_descendant(path) is None for path in PINS)


def test_clean_root_must_be_ancestor(clean_repo):
    repo, row, _ = clean_repo
    git(repo, "checkout", "--detach", row["parent_main_sha"])
    for path in PINS:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((SOURCE_ROOT / path).read_bytes())
    commit(repo, "unreviewed parallel history")
    assert all(approved_descendant(path) is None for path in PINS)


def test_git_tree_identity_is_checked(clean_repo, monkeypatch):
    _, row, document = clean_repo
    wrong = {**guard.CLEAN_IDENTITY, "clean_root_tree_sha": "0" * 40}
    monkeypatch.setattr(guard, "CLEAN_IDENTITY", wrong)
    document.write_text(json.dumps({**row, **wrong}))
    assert all(approved_descendant(path) is None for path in PINS)


def test_head_bytes_and_working_bytes_are_both_bound(clean_repo):
    repo, _, _ = clean_repo
    target = Path(next(iter(PINS)))
    original = target.read_bytes()
    target.write_bytes(original + b"\n# changed HEAD\n")
    commit(repo, "unauthorized protected commit")
    target.write_bytes(original)
    assert approved_descendant(str(target)) is None


def test_clean_root_bytes_must_match_attestation(clean_repo, monkeypatch):
    repo, row, document = clean_repo
    target = Path(next(iter(PINS)))
    original = target.read_bytes()
    target.write_bytes(original + b"\n# wrong root content\n")
    root = commit(repo, "wrong protected root")
    identity = {**guard.CLEAN_IDENTITY, "clean_root_sha": root,
                "clean_root_tree_sha": git(repo, "rev-parse", root + "^{tree}"),
                "parent_main_sha": row["clean_root_sha"]}
    monkeypatch.setattr(guard, "CLEAN_IDENTITY", identity)
    document.write_text(json.dumps({**row, **identity}))
    target.write_bytes(original)
    commit(repo, "restore current bytes only")
    assert approved_descendant(str(target)) is None


def test_failed_clean_mode_does_not_fall_back_to_legacy(clean_repo, monkeypatch):
    _, row, document = clean_repo
    monkeypatch.setattr(guard, "PINS", {path: (owner, row["clean_root_sha"])
                                      for path, (owner, _) in PINS.items()})
    document.write_text("{}")
    assert all(approved_descendant(path) is None for path in PINS)


@pytest.mark.parametrize("changed", [False, True])
def test_legacy_exact_ancestry_is_preserved(clean_repo, monkeypatch, changed):
    repo, row, _ = clean_repo
    monkeypatch.setattr(guard, "CLEAN_IDENTITY", {**guard.CLEAN_IDENTITY, "clean_root_sha": "0" * 40})
    monkeypatch.setattr(guard, "PINS", {path: (owner, row["clean_root_sha"])
                                      for path, (owner, _) in PINS.items()})
    commit(repo, "legacy descendant")
    for path in PINS:
        if changed:
            target = Path(path)
            target.write_bytes(target.read_bytes() + b"\n# unapproved\n")
        receipt = approved_descendant(path)
        if changed:
            assert receipt is None
        else:
            assert receipt["ancestor_verified"] is True
            assert receipt["provenance_mode"] == "LEGACY_HISTORICAL_ANCESTRY"


def approved_workflow_bytes():
    return (SOURCE_ROOT / guard.WORKFLOW_PATH).read_bytes()


def test_reviewed_workflow_transition_and_descendant(clean_repo):
    repo, _, _ = clean_repo
    path = Path(guard.WORKFLOW_PATH)
    assert approved_descendant(guard.WORKFLOW_PATH) is None
    path.write_bytes(approved_workflow_bytes())
    precommit = approved_descendant(guard.WORKFLOW_PATH)
    assert precommit["exact_transform_verified"]
    assert precommit["head_sha256"] == guard.WORKFLOW_BEFORE_SHA256
    commit(repo, "approved history-depth transition")
    committed = approved_descendant(guard.WORKFLOW_PATH)
    assert committed["head_sha256"] == guard.WORKFLOW_AFTER_SHA256
    assert committed["clean_root_ancestor_verified"]
    commit(repo, "unchanged descendant")
    assert approved_descendant(guard.WORKFLOW_PATH) == committed


@pytest.mark.parametrize("mutation", ["depth", "permission", "job", "whitespace"])
def test_workflow_only_exact_reviewed_change_is_accepted(clean_repo, mutation):
    data = approved_workflow_bytes()
    if mutation == "depth":
        data = data.replace(b"fetch-depth: 0", b"fetch-depth: 1")
    elif mutation == "permission":
        data += b"\npermissions: write-all\n"
    elif mutation == "job":
        data = data.replace(b"run: pytest", b"run: echo bypass")
    else:
        data += b" "
    Path(guard.WORKFLOW_PATH).write_bytes(data)
    assert approved_descendant(guard.WORKFLOW_PATH) is None


def test_workflow_bad_head_cannot_be_masked_by_working_copy(clean_repo):
    repo, _, _ = clean_repo
    path = Path(guard.WORKFLOW_PATH)
    path.write_bytes(approved_workflow_bytes() + b"\n# unauthorized\n")
    commit(repo, "unapproved workflow HEAD")
    path.write_bytes(approved_workflow_bytes())
    assert approved_descendant(guard.WORKFLOW_PATH) is None


def test_workflow_requires_reviewed_root_ancestry(clean_repo):
    repo, row, _ = clean_repo
    git(repo, "checkout", "--detach", row["parent_main_sha"])
    path = Path(guard.WORKFLOW_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(approved_workflow_bytes())
    commit(repo, "unapproved parallel root")
    assert approved_descendant(guard.WORKFLOW_PATH) is None


@pytest.mark.parametrize("identity_key", ["clean_root_tree_sha", "parent_main_sha"])
def test_workflow_rejects_wrong_root_identity(clean_repo, monkeypatch, identity_key):
    Path(guard.WORKFLOW_PATH).write_bytes(approved_workflow_bytes())
    monkeypatch.setattr(guard, "CLEAN_IDENTITY", {**guard.CLEAN_IDENTITY, identity_key: "0" * 40})
    assert approved_descendant(guard.WORKFLOW_PATH) is None


def test_workflow_rejects_wrong_root_bytes(clean_repo, monkeypatch):
    repo, row, _ = clean_repo
    path = Path(guard.WORKFLOW_PATH)
    path.write_bytes(path.read_bytes() + b"\n# wrong root\n")
    wrong = commit(repo, "wrong root bytes")
    monkeypatch.setattr(guard, "CLEAN_IDENTITY", {**guard.CLEAN_IDENTITY,
        "clean_root_sha": wrong, "clean_root_tree_sha": git(repo, "rev-parse", "HEAD^{tree}"),
        "parent_main_sha": row["clean_root_sha"]})
    path.write_bytes(approved_workflow_bytes())
    assert approved_descendant(guard.WORKFLOW_PATH) is None


@pytest.mark.parametrize("protected_test", ["M12E", "M12U", "M12F", "M12W", "M12AA", "M12AB"])
def test_each_migrated_scope_still_detects_unauthorized_owner_mutation(monkeypatch, protected_test, request):
    target = "app/services/daily_digest_renderer.py"
    if protected_test == "M12W":
        repo, row, _ = request.getfixturevalue("clean_repo")
        monkeypatch.setattr(w, "BASE", row["clean_root_sha"])
        commit(repo, "unchanged reviewed descendant")
        before = w.freeze()
        assert before["status"] == "PASS"
        assert before["verification_mode"] == "EXACT_BASE_ARCHIVE_SHA256"
        assert before["changed_existing_paths"] == []
        assert approved_descendant(target)["clean_root_ancestor_verified"]
        path = Path(target)
        path.write_bytes(path.read_bytes() + b"\n# unauthorized owner mutation\n")
        commit(repo, "mutated descendant")
        assert approved_descendant(target) is None
        after = w.freeze()
        assert after["status"] == "FAIL"
        assert after["verification_mode"] == "EXACT_BASE_ARCHIVE_SHA256"
        assert after["changed_existing_paths"] == [target]
        return
    original = Path.read_bytes

    def mutated(path):
        payload = original(path)
        return payload + b"\n# unauthorized mutation\n" if str(path) == target else payload

    monkeypatch.setattr(Path, "read_bytes", mutated)
    assert approved_descendant(target) is None
    if protected_test in {"M12E", "M12U", "M12F"}:
        assert target in u.scope_audit()["unexpected_file_changes"]
    else:
        assert (aa if protected_test == "M12AA" else ab)._freeze_paths((target,))["status"] == "FAIL"
