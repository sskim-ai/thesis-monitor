"""Archive-verified expanded-report GC. No worktree, DB or credential deletion."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile


def fingerprint(path):
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return dict(bytes=path.stat().st_size, sha256=h.hexdigest())


def verify_archive(path):
    path = Path(path)
    if path.is_symlink() or path.with_suffix(path.suffix + ".sha256").is_symlink():
        raise ValueError("archive_symlink")
    actual = fingerprint(path)
    if path.with_suffix(path.suffix + ".sha256").read_text().split()[0] != actual["sha256"]:
        raise ValueError("archive_sidecar_mismatch")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or any(Path(n).is_absolute() or ".." in Path(n).parts for n in names):
            raise ValueError("archive_unsafe_or_duplicate_path")
        if z.testzip() is not None:
            raise ValueError("archive_crc_failure")
        manifest = json.loads(z.read("result/bundle-manifest.json"))
        if set(names) != {"result/" + n for n in manifest} | {"result/bundle-manifest.json"}:
            raise ValueError("archive_manifest_extra_or_missing")
        for name, expected in manifest.items():
            body = z.read("result/" + name)
            if dict(bytes=len(body), sha256=sha256(body).hexdigest()) != expected:
                raise ValueError("archive_manifest_content_mismatch")
        manifest["bundle-manifest.json"] = dict(bytes=len(z.read("result/bundle-manifest.json")),
            sha256=sha256(z.read("result/bundle-manifest.json")).hexdigest())
    return dict(path=str(path.resolve()), **actual, crc="PASS", internal_manifest="PASS",
                entries=len(manifest)), manifest


def directory_proof(directory, *, archive, manifest, prefix, protected):
    directory = Path(directory)
    if directory.is_symlink() or directory.resolve() != directory.absolute():
        raise ValueError("gc_symlink_path")
    protected = [Path(p).resolve() for p in protected]
    if any(directory == p or directory in p.parents or p in directory.parents for p in protected):
        raise ValueError("gc_registered_dependency_or_active_path")
    if not directory.is_dir() or directory == Path(archive["path"]).parent:
        raise ValueError("gc_expanded_directory_required")
    records = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("gc_symlink_child")
        if not path.is_file():
            continue
        if (path.suffix.lower() in {".zip", ".sha256", ".db", ".sqlite", ".sqlite3"}
                or path.name.endswith(("-wal", "-shm")) or path.name == ".env"
                or any(part in {".git", "credentials", "auth.json"} for part in path.parts)):
            raise ValueError("gc_protected_file")
        relative = path.relative_to(directory).as_posix()
        actual = fingerprint(path)
        if manifest.get(prefix + relative) != actual:
            raise ValueError("gc_unarchived_or_changed_file:" + relative)
        records[relative] = actual
    if not records:
        raise ValueError("gc_empty_unproven_directory")
    return dict(path=str(directory), archive=archive, archive_prefix=prefix,
                files=records, bytes=sum(r["bytes"] for r in records.values()), eligible=True)


def remove_verified(row, *, protected):
    """Revalidate both archive and expanded bytes immediately before removal."""
    archive, manifest = verify_archive(row["archive"]["path"])
    current = directory_proof(row["path"], archive=archive, manifest=manifest,
                              prefix=row["archive_prefix"], protected=protected)
    if current != row:
        raise ValueError("gc_plan_drift")
    shutil.rmtree(row["path"])
    return dict(path=row["path"], bytes=row["bytes"], deleted=True, archive_sha256=archive["sha256"])
