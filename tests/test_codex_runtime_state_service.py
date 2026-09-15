from __future__ import annotations

import concurrent.futures
import sqlite3
from pathlib import Path

import pytest

from app.services.codex_runtime_state_service import (
    RUNTIME_NAMESPACE_POLICY,
    RUNTIME_STATE_NOT_READY,
    CodexRuntimeIsolationCollision,
    CodexRuntimeIsolationRegistry,
    CodexRuntimeStateError,
    context_runtime_state_namespace,
    prepare_codex_runtime_state,
    runtime_state_namespace_hash,
)


def _auth_source(tmp_path: Path) -> Path:
    source = tmp_path / "signed-in-auth.json"
    source.write_text("{}\n", encoding="utf-8")
    source.chmod(0o600)
    return source


def test_runtime_state_prepares_private_claim_scoped_sqlite_home(
    tmp_path: Path,
) -> None:
    auth_source = _auth_source(tmp_path)
    first = prepare_codex_runtime_state(
        tmp_path, namespace="primary-claim", auth_source=auth_source
    )
    second = prepare_codex_runtime_state(
        tmp_path, namespace="backup-claim", auth_source=auth_source
    )

    assert first.sqlite_home != second.sqlite_home
    assert first.mode == "0700"
    assert first.sqlite_wal_probe == "PASS"
    assert first.environment({"CODEX_HOME": "/signed-in/home"}) == {
        "CODEX_HOME": str(first.codex_home),
        "CODEX_SQLITE_HOME": str(first.sqlite_home),
    }
    assert (first.codex_home / "auth.json").is_symlink()
    assert (first.codex_home / "auth.json").resolve() == auth_source
    assert not list(first.sqlite_home.glob(".runtime-state-probe-*"))


def test_runtime_state_primary_backup_concurrency_isolated(tmp_path: Path) -> None:
    auth_source = _auth_source(tmp_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        states = list(
            executor.map(
                lambda namespace: prepare_codex_runtime_state(
                    tmp_path, namespace=namespace, auth_source=auth_source
                ),
                ("primary-claim", "backup-claim"),
            )
        )

    assert len({state.sqlite_home for state in states}) == 2
    for state in states:
        database = state.sqlite_home / "state_5.sqlite"
        connection = sqlite3.connect(database)
        connection.execute("CREATE TABLE IF NOT EXISTS state_probe (value INTEGER)")
        connection.commit()
        connection.close()


def test_runtime_state_rejects_empty_namespace(tmp_path: Path) -> None:
    with pytest.raises(CodexRuntimeStateError, match=RUNTIME_STATE_NOT_READY):
        prepare_codex_runtime_state(tmp_path, namespace=" ")


def test_context_runtime_namespace_includes_invocation_identity() -> None:
    first = context_runtime_state_namespace(
        base_namespace="shared-generation", invocation_id="first:core:01"
    )
    second = context_runtime_state_namespace(
        base_namespace="shared-generation", invocation_id="first:core:02"
    )

    assert runtime_state_namespace_hash(first) != runtime_state_namespace_hash(second)
    assert RUNTIME_NAMESPACE_POLICY in first


def test_runtime_isolation_registry_rejects_reused_component(tmp_path: Path) -> None:
    registry = CodexRuntimeIsolationRegistry()
    first_workdir = tmp_path / "first"
    second_workdir = tmp_path / "second"
    first_workdir.mkdir()
    second_workdir.mkdir()
    registry.claim(
        base_namespace="proof:first:core",
        invocation_id="generation:first:core:01",
        working_directory=first_workdir,
    )

    with pytest.raises(CodexRuntimeIsolationCollision, match="invocation_id"):
        registry.claim(
            base_namespace="proof:first:core",
            invocation_id="generation:first:core:01",
            working_directory=second_workdir,
        )
    with pytest.raises(
        CodexRuntimeIsolationCollision, match="working_directory_identity"
    ):
        registry.claim(
            base_namespace="proof:first:core",
            invocation_id="generation:first:core:02",
            working_directory=first_workdir,
        )
