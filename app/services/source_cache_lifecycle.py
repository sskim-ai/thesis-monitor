"""Public/test raw custody, not source-use authority or a production scheduler.

Reuses the existing durable artifact writer. Cleanup is limited to files created
by this live generation; arbitrary historical trees require a separate review.
"""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
from weakref import WeakKeyDictionary
import zipfile

from app.services.unified_run_artifacts import durable_bytes
from app.services.unified_snapshot_contract import digest, encoded

CONTRACT = "public-source-cas-lifecycle-v1"
MAX_OBJECT = 16 * 1024**2
_GENERATIONS = WeakKeyDictionary()
_RESTORES = WeakKeyDictionary()


def pin(raw):
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value):
        raise ValueError("invalid_sha256")
    return value


@contextmanager
def _directory(path):
    """Anchor every component; never follow links, including parent links."""
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("absolute_unaliased_path_required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _read(path, limit=MAX_OBJECT):
    with _directory(path.parent) as parent:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
                raise ValueError("unsafe_or_oversized_file")
            raw = bytearray()
            while chunk := os.read(fd, min(65536, limit + 1 - len(raw))):
                raw.extend(chunk)
                if len(raw) > limit:
                    raise ValueError("object_limit")
            after = os.fstat(fd)
            if _identity(before) != _identity(after):
                raise ValueError("concurrent_writer")
            return bytes(raw), _identity(after)
        finally:
            os.close(fd)


def _identity(st):
    return (st.st_dev, st.st_ino, st.st_nlink, st.st_size, st.st_mtime_ns)


def _mkdir(path, *, exclusive=False):
    with _directory(path.parent) as parent:
        try:
            os.mkdir(path.name, mode=0o700, dir_fd=parent)
        except FileExistsError:
            if exclusive:
                raise
        child = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        os.close(child)


def _write(path, raw):
    with _directory(path.parent) as parent:
        durable_bytes(Path(path.name), raw, exclusive=True, directory_fd=parent)


@dataclass(frozen=True)
class SourceMetadata:
    issuer_id: str
    official_source: str
    filing_id: str
    source_url: str
    acquisition_timestamp: str
    publication_timestamp: str
    source_domain: str
    capture_context: str
    entity: str
    classification: str
    content_encoding: str
    parser_version: str
    effective_period: str
    origin_generation: str

    def validate(self):
        if self.classification not in {"PUBLIC_OFFICIAL", "SYNTHETIC"}:
            raise ValueError("private_or_unknown_source_not_allowed")
        if not all(isinstance(v, str) and v.strip() for v in asdict(self).values()):
            raise ValueError("source_metadata_incomplete")


class Generation:
    __slots__ = ("__weakref__",)


class RestoredPack:
    __slots__ = ("__weakref__",)


class SourceCache:
    def __init__(self, root):
        self.root = Path(root)
        if any(part in {"Mobile Documents", ".git", ".ssh", ".aws"} or part.startswith(".env")
               for part in self.root.parts):
            raise ValueError("protected_or_cloud_root")
        with _directory(self.root):
            pass
        for suffix in ("cache", "cache/objects", "cache/objects/sha256", "cache/catalog", "scratch"):
            path = self.root / suffix
            _mkdir(path)

    def put(self, raw, *, expected, metadata):
        metadata.validate()
        if len(raw) > MAX_OBJECT or pin(raw) != expected:
            raise ValueError("source_sha_or_size_mismatch")
        key = _hash(expected["sha256"])
        path = self.root / "cache/objects/sha256" / key[:2] / key
        _mkdir(path.parent)
        try:
            _write(path, raw)
        except FileExistsError:
            existing, _ = _read(path)
            if existing != raw:
                raise ValueError("cas_collision_or_corruption") from None
        row = dict(contract=CONTRACT, raw=expected, metadata=asdict(metadata),
            authority="BYTES_ONLY_NOT_OWNER_NOT_FRESHNESS")
        catalog = self.root / "cache/catalog" / (digest(row) + ".json")
        try:
            _write(catalog, encoded(row) + b"\n")
        except FileExistsError:
            if json.loads(_read(catalog)[0]) != row:
                raise ValueError("catalog_collision_or_corruption") from None
        return dict(catalog_sha256=digest(row), **expected)

    def read(self, reference):
        catalog = self.root / "cache/catalog" / (_hash(reference["catalog_sha256"]) + ".json")
        row = json.loads(_read(catalog)[0])
        if digest(row) != reference["catalog_sha256"] or row["contract"] != CONTRACT:
            raise ValueError("catalog_binding")
        if row["raw"] != {k: reference[k] for k in ("bytes", "sha256")}:
            raise ValueError("pointer_binding")
        SourceMetadata(**row["metadata"]).validate()
        key = _hash(reference["sha256"])
        raw, _ = _read(self.root / "cache/objects/sha256" / key[:2] / key)
        if pin(raw) != row["raw"]:
            raise ValueError("cas_corrupt")
        return raw, row

    def replay(self, reference, *, issuer_id, origin_generation, period, purpose):
        raw, row = self.read(reference)
        meta = row["metadata"]
        if (issuer_id, origin_generation, period) != (
            meta["issuer_id"], meta["origin_generation"], meta["effective_period"]
        ):
            raise ValueError("STALE_SOURCE")
        if purpose != "ORIGINAL_AUDIT_REPLAY":
            raise ValueError("FRESH_REQUIRED")
        return raw

    def begin(self, generation_id, references, *, budget_bytes):
        if not re.fullmatch(r"ng[0-9]+-[a-z0-9-]{1,64}", generation_id):
            raise ValueError("generation_name")
        if not 0 < budget_bytes <= 100_000_000:
            raise ValueError("generation_budget")
        for ref in references:
            self.read(ref)
        generation_raw = encoded(dict(
            contract=CONTRACT, generation=generation_id, references=references))
        if len(generation_raw) > budget_bytes:
            raise ValueError("generation_budget")
        path = self.root / "scratch" / generation_id
        _mkdir(path, exclusive=True)
        handle = Generation()
        _GENERATIONS[handle] = dict(cache=self, path=path, files={}, budget=budget_bytes,
            closed=False, references=json.loads(encoded(references)),
            directory_identity=(path.stat().st_dev, path.stat().st_ino),
            synthetic=all(self.read(ref)[1]["metadata"]["classification"] == "SYNTHETIC"
                for ref in references))
        self.write(handle, "generation.json", generation_raw)
        return handle

    def write(self, generation, name, raw):
        state = self._generation(generation)
        if state["closed"] or not re.fullmatch(r"[A-Za-z0-9_-]+\.(json|txt|html|xml)", name):
            raise ValueError("generation_closed_or_name")
        if sum(x["pin"]["bytes"] for x in state["files"].values()) + len(raw) > state["budget"]:
            raise ValueError("generation_budget")
        path = state["path"] / name
        _write(path, raw)
        checked, identity = _read(path)
        if checked != raw:
            raise ValueError("write_changed")
        state["files"][name] = dict(pin=pin(raw), identity=identity)

    def _generation(self, handle):
        if type(handle) is not Generation:
            raise ValueError("live_generation_required")
        state = _GENERATIONS.get(handle)
        if state is None or state["cache"] is not self:
            raise ValueError("live_generation_required")
        return state

    def seal(self, generation):
        state = self._generation(generation)
        if state["closed"]:
            raise ValueError("generation_already_closed")
        payload = {}
        for name, value in state["files"].items():
            raw, identity = _read(state["path"] / name)
            if identity != value["identity"] or pin(raw) != value["pin"]:
                raise ValueError("generation_identity_drift")
            payload["generation/" + name] = raw
        for ref in state["references"]:
            raw, row = self.read(ref)
            payload["blobs/" + ref["sha256"]] = raw
            payload["catalog/" + ref["catalog_sha256"] + ".json"] = encoded(row)
        manifest = {name: pin(raw) for name, raw in payload.items()}
        out = BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, raw in sorted(payload.items()):
                z.writestr(name, raw)
            z.writestr("manifest.json", encoded(dict(contract=CONTRACT, files=manifest)))
        packed = out.getvalue()
        if len(packed) > 100_000_000:
            raise ValueError("pack_limit")
        state["closed"] = True
        state["pack_sha"] = pin(packed)["sha256"]
        return packed

    def restore(self, packed, *, expected_sha, original_replay):
        if len(packed) > 100_000_000 or pin(packed)["sha256"] != _hash(expected_sha):
            raise ValueError("archive_identity")
        with zipfile.ZipFile(BytesIO(packed)) as z:
            names = z.namelist()
            if (len(names) > 4096 or sum(x.file_size for x in z.infolist()) > 100_000_000
                    or any(x.file_size > MAX_OBJECT for x in z.infolist())):
                raise ValueError("restore_budget")
            if len(set(names)) != len(names) or z.testzip() is not None:
                raise ValueError("archive_members_or_crc")
            manifest = json.loads(z.read("manifest.json"))
            if manifest["contract"] != CONTRACT or set(names) != set(manifest["files"]) | {"manifest.json"}:
                raise ValueError("archive_manifest")
            restored = {}
            total = 0
            for name, expected in manifest["files"].items():
                if not re.fullmatch(r"(generation|blobs|catalog)/[A-Za-z0-9_.-]+", name):
                    raise ValueError("archive_path")
                total += expected["bytes"]
                if expected["bytes"] > MAX_OBJECT or total > 100_000_000:
                    raise ValueError("restore_budget")
                raw = z.read(name)
                if pin(raw) != expected:
                    raise ValueError("archive_member_pin")
                restored[name] = raw
        replay = original_replay(dict(restored))
        if not replay:
            raise ValueError("original_replay_failed")
        proof = RestoredPack()
        _RESTORES[proof] = dict(cache=self, sha=expected_sha, replay=replay,
            remote=False)
        return proof

    def confirm_readback(self, proof, readback):
        """Trusted delivery adapter supplies downloaded bytes, never an OK flag."""
        state = _RESTORES.get(proof) if type(proof) is RestoredPack else None
        if state is None or state["cache"] is not self:
            raise ValueError("live_restore_required")
        if readback is None or sha256(readback).hexdigest() != state["sha"]:
            raise ValueError("THIN_SEAL_REMOTE_RESTORE_PENDING")
        state["byte_readback"] = True
        return {"status": "BYTE_EQUALITY_ONLY", "remote_custody": "NOT_ESTABLISHED"}

    def cleanup(self, generation, proof):
        self._generation(generation)
        raise ValueError("THIN_SEAL_REMOTE_RESTORE_PENDING")

    def cleanup_synthetic(self, generation, proof):
        """Only reconstructable synthetic files in this live owned generation."""
        state = self._generation(generation)
        restored = _RESTORES.get(proof) if type(proof) is RestoredPack else None
        if not state["closed"] or not restored or restored["cache"] is not self:
            raise ValueError("sealed_restored_generation_required")
        if not state["synthetic"]:
            raise ValueError("REAL_SOURCE_CLEANUP_NOT_AUTHORIZED")
        if restored["sha"] != state["pack_sha"] or not restored.get("byte_readback"):
            raise ValueError("THIN_SEAL_REMOTE_RESTORE_PENDING")
        path = state["path"]
        with _directory(path) as fd:
            st = os.fstat(fd)
            if (st.st_dev, st.st_ino) != state["directory_identity"]:
                raise ValueError("generation_directory_drift")
            if set(os.listdir(fd)) != set(state["files"]):
                raise ValueError("unknown_generation_content")
            for name, value in state["files"].items():
                raw, identity = _read(path / name)
                if identity != value["identity"] or pin(raw) != value["pin"]:
                    raise ValueError("concurrent_writer_or_inode_drift")
            removed = []
            for name, value in state["files"].items():
                if _identity(os.stat(name, dir_fd=fd, follow_symlinks=False)) != value["identity"]:
                    raise ValueError("concurrent_writer_or_inode_drift")
                os.unlink(name, dir_fd=fd)
                removed.append(dict(path=str(path / name), **value["pin"]))
        with _directory(path.parent) as parent:
            st = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if (st.st_dev, st.st_ino) != state["directory_identity"]:
                raise ValueError("generation_directory_drift")
            os.rmdir(path.name, dir_fd=parent)
        del _GENERATIONS[generation]
        return removed
