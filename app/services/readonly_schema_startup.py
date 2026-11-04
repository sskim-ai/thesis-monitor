"""Schema-only SQLite admission. Never initialize or migrate the target database."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
import ctypes

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool

POLICY = "schema-verified-no-migration-startup-v2-os-write-denied-wal"
_PRAGMAS = {"table_info", "table_xinfo", "index_list", "index_info", "index_xinfo",
            "foreign_key_list", "schema_version", "user_version", "journal_mode",
            "database_list"}


class SchemaStartupDenied(RuntimeError):
    pass


def sqlite_path(url):
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" or parsed.query or not parsed.database:
        raise SchemaStartupDenied("unsupported_readonly_database")
    if parsed.database == ":memory:":
        raise SchemaStartupDenied("persistent_database_required")
    path = Path(parsed.database).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise SchemaStartupDenied("database_symlink_denied")
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid():
        raise SchemaStartupDenied("database_custody_denied")
    return path


def file_metadata(path):
    result = {}
    for suffix in ("", "-wal", "-shm", "-journal"):
        p = Path(str(path) + suffix)
        if p.is_symlink():
            raise SchemaStartupDenied("journal_symlink_denied")
        if not p.exists():
            result[suffix] = None
            continue
        st = p.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid():
            raise SchemaStartupDenied("journal_custody_denied")
        result[suffix] = [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns]
    if result["-journal"] and result["-journal"][2]:
        raise SchemaStartupDenied("rollback_journal_requires_separate_review")
    return result


def readonly_connection(url, journal=None):
    path = sqlite_path(url)
    files = file_metadata(path)
    # SQLite mode=ro may still update WAL shared-memory read marks.
    # Never use immutable=1 to hide uncheckpointed data from a live writer.
    wal = files["-wal"] is not None or files["-shm"] is not None
    if wal:
        _require_kernel_write_denial(path, journal)
    with path.open("rb") as stream:
        header = stream.read(100)
    if (len(header) != 100 or header[:16] != b"SQLite format 3\x00"
            or header[18:20] not in (b"\x01\x01", b"\x02\x02")):
        raise SchemaStartupDenied("non_rollback_database_header_denied")
    if header[18:20] == b"\x02\x02" and not wal:
        _require_kernel_write_denial(path, journal)
    con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    con.execute("PRAGMA query_only=ON")
    con.enable_load_extension(False)
    def authorizer(action, one, two, database, source):
        allowed = (
            action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_TRANSACTION)
            or action == sqlite3.SQLITE_READ and one in ("sqlite_master", "sqlite_schema", "sqlite_temp_master")
            or action == sqlite3.SQLITE_FUNCTION and two in ("like", "lower", "length")
            or action == sqlite3.SQLITE_PRAGMA and (
                one in _PRAGMAS and (one not in ("schema_version", "user_version", "journal_mode") or two is None)
                or one == "read_uncommitted" and two is None
                or one == "query_only" and two is None))
        if journal is not None:
            journal.append(dict(action=action, object=one, argument=two, allowed=bool(allowed)))
        return sqlite3.SQLITE_OK if allowed else sqlite3.SQLITE_DENY
    con.set_authorizer(authorizer)
    return con


def _require_kernel_write_denial(path, journal=None):
    """A WAL reader may update SHM even with mode=ro. Require OS denial first.

    This queries the current process sandbox; it never grants a permission or
    changes the sandbox. Unsupported platforms/API failures remain denied.
    The caller must start the process with a deny-file-write* profile covering
    the database directory. SQLite still uses ordinary locking, not immutable.
    """
    if sys.platform != "darwin":
        raise SchemaStartupDenied("wal_kernel_write_boundary_unavailable")
    try:
        library = ctypes.CDLL("/usr/lib/libsandbox.1.dylib", use_errno=True)
        check = library.sandbox_check
        check.restype = ctypes.c_int
        check.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        # SANDBOX_FILTER_PATH=1. A readable control rejects blanket/API errors.
        if check(os.getpid(), b"file-read-data", 1, os.fsencode(path)) != 0:
            raise SchemaStartupDenied("wal_read_boundary_unavailable")
        checks = []
        for suffix in ("", "-wal", "-shm", "-journal"):
            for operation in ("file-write-data", "file-write-create", "file-write-unlink", "file-write-mode"):
                result = check(os.getpid(), operation.encode(), 1, os.fsencode(str(path) + suffix))
                checks.append(dict(suffix=suffix, operation=operation, denied=result == 1))
                if result != 1:
                    raise SchemaStartupDenied("wal_kernel_write_denial_required")
        if journal is not None:
            journal.append(dict(boundary="MACOS_CURRENT_PROCESS_WRITE_DENY", checks=checks,
                                api="sandbox_check", permission_change=False))
    except (OSError, AttributeError) as exc:
        raise SchemaStartupDenied("wal_kernel_write_boundary_unavailable") from exc


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _schema(wrapper):
    with wrapper.connect() as connection:
        inspector = inspect(connection)
        tables = {}
        for name in sorted(inspector.get_table_names()):
            columns = [
                dict(name=c["name"], type=str(c["type"]), nullable=c["nullable"],
                     default=c["default"], primary_key=c.get("primary_key", 0))
                for c in inspector.get_columns(name)]
            tables[name] = dict(columns=columns, pk=inspector.get_pk_constraint(name),
                indexes=inspector.get_indexes(name), unique=inspector.get_unique_constraints(name),
                foreign_keys=inspector.get_foreign_keys(name), checks=inspector.get_check_constraints(name))
        schema_objects = connection.exec_driver_sql(
            "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE type IN ('view','trigger') ORDER BY type,name"
        ).fetchall()
        return dict(tables=tables, additional_objects=[tuple(r) for r in schema_objects])


def verify_schema(url, metadata, legacy_columns, journal=None):
    """Compare real metadata against a disposable schema built from existing ORM rules."""
    path = sqlite_path(url)
    before = file_metadata(path)
    expected_engine = create_engine("sqlite://", poolclass=StaticPool)
    try:
        metadata.create_all(expected_engine)
        with expected_engine.begin() as c:
            for table, columns in legacy_columns.items():
                existing = {r[1] for r in c.exec_driver_sql('PRAGMA table_info("' + table + '")')}
                if not existing:
                    continue
                for column, declaration in columns.items():
                    if column not in existing:
                        # Names and declarations are trusted source constants, never request inputs.
                        c.exec_driver_sql(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {declaration}')
        expected = _schema(expected_engine)
    finally:
        expected_engine.dispose()
    con = readonly_connection(url, journal)
    actual_engine = create_engine("sqlite://", creator=lambda: con, poolclass=StaticPool)
    try:
        con.execute("BEGIN")
        version = con.execute("PRAGMA schema_version").fetchone()[0]
        user_version = con.execute("PRAGMA user_version").fetchone()[0]
        if user_version != 0:
            raise SchemaStartupDenied("unreviewed_schema_migration_version")
        actual = _schema(actual_engine)
    finally:
        actual_engine.dispose()
        con.close()
    after = file_metadata(path)
    if before != after:
        raise SchemaStartupDenied("database_metadata_changed_during_inspection")
    if actual != expected:
        differences = sorted(k for k in set(expected["tables"]) | set(actual["tables"])
                             if expected["tables"].get(k) != actual["tables"].get(k))
        raise SchemaStartupDenied("schema_contract_mismatch:" + ",".join(differences))
    return dict(policy=POLICY, status="SCHEMA_VERIFIED_NO_MIGRATION_STARTUP",
                schema_sha256=_digest(actual), schema_version=version, user_version=user_version,
                tables=len(actual["tables"]), file_metadata=after,
                target_mutation=False, target_row_reads=False)
