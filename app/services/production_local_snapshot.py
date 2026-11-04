"""Copy a coherent SQLite file set before projecting local runtime inputs."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile

from sqlmodel import Session, create_engine


def _identity(path):
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("production_database_regular_file_required")
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("production_database_changed_during_snapshot")
    return (after.st_ino, len(raw), after.st_mtime_ns, sha256(raw).hexdigest()), raw


@contextmanager
def readonly_local_snapshot(database, *, temporary_parent):
    """Never open the operating SQLite files through SQLite, including its WAL.

    The private copy may replay WAL into its own temporary SHM. A concurrent
    operating write invalidates the snapshot instead of accepting mixed bytes.
    """
    database = Path(database)
    paths = [database, Path(str(database) + "-wal")]
    first = {p: _identity(p) for p in paths}
    if first[database] is None:
        raise ValueError("production_database_missing")
    with tempfile.TemporaryDirectory(prefix="local-source-", dir=temporary_parent) as temp:
        target = Path(temp) / "source.sqlite3"
        for index, path in enumerate(paths):
            if first[path] is not None:
                output = target if index == 0 else Path(str(target) + "-wal")
                with output.open("xb") as stream:
                    stream.write(first[path][1])
                output.chmod(0o600)
        second = {p: _identity(p) for p in paths}
        if any((first[p][0] if first[p] else None) != (second[p][0] if second[p] else None) for p in paths):
            raise ValueError("production_database_changed_during_snapshot")

        def connect():
            connection = sqlite3.connect(target.as_uri() + "?mode=ro", uri=True)
            connection.execute("PRAGMA query_only=ON")
            return connection

        engine = create_engine("sqlite://", creator=connect)
        try:
            with Session(engine) as session:
                yield session, {"database": first[database][0][3],
                    "wal": first[paths[1]][0][3] if first[paths[1]] else None,
                    "operating_sqlite_opened": False, "migration": "NO_MIGRATION_REQUIRED"}
        finally:
            engine.dispose()
