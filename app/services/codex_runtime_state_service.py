from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path


RUNTIME_STATE_CONTRACT = "codex-runtime-state-v1"
RUNTIME_STATE_NOT_READY = "LOCAL_CODEX_RUNTIME_STATE_NOT_READY"
RUNTIME_NAMESPACE_POLICY = "PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE"
RUNTIME_ISOLATION_CONTRACT = "codex-model-context-runtime-isolation-v1"


class CodexRuntimeStateError(ValueError):
    """Raised before model transport when local Codex state is not writable."""


class CodexRuntimeIsolationCollision(CodexRuntimeStateError):
    """Raised before model spawn when a context isolation identity is reused."""


@dataclass(frozen=True)
class CodexRuntimeIsolationIdentity:
    contract: str
    policy: str
    invocation_id: str
    base_namespace_hash: str
    runtime_state_namespace: str
    runtime_state_namespace_hash: str
    working_directory_identity: str

    @property
    def execution_isolation_valid(self) -> bool:
        return True

    def audit_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "policy": self.policy,
            "invocation_id": self.invocation_id,
            "base_namespace_hash": self.base_namespace_hash,
            "runtime_state_namespace_hash": self.runtime_state_namespace_hash,
            "working_directory_identity": self.working_directory_identity,
            "invocation_identity_unique": True,
            "runtime_state_namespace_unique": True,
            "working_directory_unique": True,
            "execution_isolation_valid": True,
        }


class CodexRuntimeIsolationRegistry:
    """Claims invocation, namespace, and working-directory identities once."""

    def __init__(self) -> None:
        self._invocation_ids: set[str] = set()
        self._namespace_hashes: set[str] = set()
        self._working_directory_identities: set[str] = set()

    @property
    def claim_count(self) -> int:
        return len(self._invocation_ids)

    @property
    def distinct_namespace_count(self) -> int:
        return len(self._namespace_hashes)

    @property
    def distinct_working_directory_count(self) -> int:
        return len(self._working_directory_identities)

    def seed(
        self,
        *,
        invocation_id: str,
        runtime_state_namespace_hash: str,
        working_directory_identity: str,
    ) -> None:
        collisions = self._collisions(
            invocation_id=invocation_id,
            namespace_hash=runtime_state_namespace_hash,
            working_directory_identity=working_directory_identity,
        )
        if collisions:
            raise CodexRuntimeIsolationCollision(
                "RUNTIME_NAMESPACE_COLLISION:existing_claim:" + ",".join(collisions)
            )
        self._record(
            invocation_id=invocation_id,
            namespace_hash=runtime_state_namespace_hash,
            working_directory_identity=working_directory_identity,
        )

    def claim(
        self,
        *,
        base_namespace: str,
        invocation_id: str,
        working_directory: Path,
    ) -> CodexRuntimeIsolationIdentity:
        namespace = context_runtime_state_namespace(
            base_namespace=base_namespace,
            invocation_id=invocation_id,
        )
        namespace_hash = runtime_state_namespace_hash(namespace)
        working_directory_identity = hashlib.sha256(
            str(working_directory.resolve()).encode("utf-8")
        ).hexdigest()
        collisions = self._collisions(
            invocation_id=invocation_id,
            namespace_hash=namespace_hash,
            working_directory_identity=working_directory_identity,
        )
        if collisions:
            raise CodexRuntimeIsolationCollision(
                "RUNTIME_NAMESPACE_COLLISION:" + ",".join(collisions)
            )
        self._record(
            invocation_id=invocation_id,
            namespace_hash=namespace_hash,
            working_directory_identity=working_directory_identity,
        )
        return CodexRuntimeIsolationIdentity(
            contract=RUNTIME_ISOLATION_CONTRACT,
            policy=RUNTIME_NAMESPACE_POLICY,
            invocation_id=invocation_id,
            base_namespace_hash=runtime_state_namespace_hash(base_namespace),
            runtime_state_namespace=namespace,
            runtime_state_namespace_hash=namespace_hash,
            working_directory_identity=working_directory_identity,
        )

    def _collisions(
        self,
        *,
        invocation_id: str,
        namespace_hash: str,
        working_directory_identity: str,
    ) -> list[str]:
        collisions = []
        if invocation_id in self._invocation_ids:
            collisions.append("invocation_id")
        if namespace_hash in self._namespace_hashes:
            collisions.append("runtime_state_namespace_hash")
        if working_directory_identity in self._working_directory_identities:
            collisions.append("working_directory_identity")
        return collisions

    def _record(
        self,
        *,
        invocation_id: str,
        namespace_hash: str,
        working_directory_identity: str,
    ) -> None:
        self._invocation_ids.add(invocation_id)
        self._namespace_hashes.add(namespace_hash)
        self._working_directory_identities.add(working_directory_identity)


@dataclass(frozen=True)
class CodexRuntimeState:
    contract: str
    namespace_hash: str
    codex_home: Path
    sqlite_home: Path
    signed_in_auth_reference: str
    ownership: str
    mode: str
    sqlite_wal_probe: str

    def environment(self, base: dict[str, str] | None = None) -> dict[str, str]:
        environment = dict(os.environ if base is None else base)
        environment["CODEX_HOME"] = str(self.codex_home)
        environment["CODEX_SQLITE_HOME"] = str(self.sqlite_home)
        return environment

    def audit_dict(self) -> dict[str, str]:
        return {
            "contract": self.contract,
            "namespace_hash": self.namespace_hash,
            "codex_home": str(self.codex_home),
            "sqlite_home": str(self.sqlite_home),
            "signed_in_auth_reference": self.signed_in_auth_reference,
            "ownership": self.ownership,
            "mode": self.mode,
            "sqlite_wal_probe": self.sqlite_wal_probe,
            "codex_home_behavior": "isolated_with_read_only_signed_in_auth_reference",
        }


def _namespace_hash(namespace: str) -> str:
    value = namespace.strip()
    if not value:
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:empty_namespace")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def runtime_state_namespace_hash(namespace: str) -> str:
    return _namespace_hash(namespace)


def context_runtime_state_namespace(*, base_namespace: str, invocation_id: str) -> str:
    base = base_namespace.strip()
    invocation = invocation_id.strip()
    if not base:
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:empty_base_namespace")
    if not invocation:
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:empty_invocation_id")
    return json.dumps(
        {
            "base_namespace": base,
            "contract": RUNTIME_ISOLATION_CONTRACT,
            "invocation_id": invocation,
            "policy": RUNTIME_NAMESPACE_POLICY,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _assert_private_owned_directory(path: Path) -> None:
    metadata = path.stat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:state_home_not_directory")
    if metadata.st_uid != os.geteuid():
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:state_home_owner_mismatch")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode & 0o077:
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:state_home_not_private")


def _sqlite_wal_write_probe(path: Path) -> None:
    probe = path / f".runtime-state-probe-{uuid.uuid4().hex}.sqlite3"
    renamed = probe.with_suffix(".verified")
    sidecars = (probe, renamed, Path(f"{probe}-wal"), Path(f"{probe}-shm"))
    try:
        connection = sqlite3.connect(probe)
        try:
            mode = connection.execute("PRAGMA journal_mode=WAL").fetchone()
            if not mode or str(mode[0]).casefold() != "wal":
                raise sqlite3.OperationalError("wal_mode_unavailable")
            connection.execute("CREATE TABLE runtime_probe (value INTEGER NOT NULL)")
            connection.execute("INSERT INTO runtime_probe VALUES (1)")
            connection.commit()
            value = connection.execute("SELECT value FROM runtime_probe").fetchone()
            if value != (1,):
                raise sqlite3.DatabaseError("probe_round_trip_failed")
        finally:
            connection.close()
        os.replace(probe, renamed)
        os.replace(renamed, probe)
    except (OSError, sqlite3.Error) as exc:
        raise CodexRuntimeStateError(
            f"{RUNTIME_STATE_NOT_READY}:sqlite_wal_write_probe_failed"
        ) from exc
    finally:
        for item in sidecars:
            try:
                item.unlink()
            except FileNotFoundError:
                pass


def prepare_codex_runtime_state(
    root: Path,
    *,
    namespace: str,
    auth_source: Path | None = None,
) -> CodexRuntimeState:
    namespace_hash = _namespace_hash(namespace)
    claim_root = root.resolve() / namespace_hash
    codex_home = claim_root / "home"
    sqlite_home = claim_root / "sqlite"
    try:
        for path in (claim_root, codex_home, sqlite_home):
            path.mkdir(parents=True, mode=0o700, exist_ok=True)
            os.chmod(path, 0o700)
    except OSError as exc:
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:state_home_create_failed") from exc
    for path in (claim_root, codex_home, sqlite_home):
        _assert_private_owned_directory(path)
    source = auth_source or (
        Path(os.environ["CODEX_HOME"]) / "auth.json"
        if os.environ.get("CODEX_HOME")
        else Path.home() / ".codex" / "auth.json"
    )
    try:
        auth_metadata = source.stat()
    except OSError as exc:
        raise CodexRuntimeStateError(
            f"{RUNTIME_STATE_NOT_READY}:signed_in_auth_reference_missing"
        ) from exc
    if auth_metadata.st_uid != os.geteuid() or stat.S_IMODE(auth_metadata.st_mode) & 0o077:
        raise CodexRuntimeStateError(f"{RUNTIME_STATE_NOT_READY}:signed_in_auth_reference_unsafe")
    auth_reference = codex_home / "auth.json"
    try:
        if auth_reference.is_symlink():
            if auth_reference.resolve() != source.resolve():
                replacement = codex_home / ".auth.json.next"
                replacement.unlink(missing_ok=True)
                replacement.symlink_to(source.resolve())
                replacement.replace(auth_reference)
        elif auth_reference.exists():
            raise CodexRuntimeStateError(
                f"{RUNTIME_STATE_NOT_READY}:signed_in_auth_plaintext_copy_forbidden"
            )
        else:
            auth_reference.symlink_to(source.resolve())
    except OSError as exc:
        raise CodexRuntimeStateError(
            f"{RUNTIME_STATE_NOT_READY}:signed_in_auth_reference_create_failed"
        ) from exc
    _sqlite_wal_write_probe(sqlite_home)
    metadata = sqlite_home.stat()
    return CodexRuntimeState(
        contract=RUNTIME_STATE_CONTRACT,
        namespace_hash=namespace_hash,
        codex_home=codex_home,
        sqlite_home=sqlite_home,
        signed_in_auth_reference="READ_ONLY_SYMLINK",
        ownership=f"uid:{metadata.st_uid}",
        mode=f"{stat.S_IMODE(metadata.st_mode):04o}",
        sqlite_wal_probe="PASS",
    )
