from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import text

from app.services.production_local_snapshot import readonly_local_snapshot
from app.services.production_source_configuration import ProtocolFile, ProductionSourceConfiguration


def protocol(path, purpose="PUBLIC_PROTOCOL"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"{\"protocol\":true}")
    return ProtocolFile(path=str(path), sha256=sha256(path.read_bytes()).hexdigest(), purpose=purpose)


def test_static_configuration_rejects_historical_and_fixture_roots(tmp_path):
    for component in ("Reports", "tests", "fixtures"):
        item = protocol(tmp_path / component / "protocol.json")
        with pytest.raises(ValueError, match="not_deployed"):
            item.read()
    item = protocol(tmp_path / "protocol.json")
    assert item.read() == b'{"protocol":true}'
    Path(item.path).write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash_mismatch"):
        item.read()


def test_configuration_has_no_historical_authorization(tmp_path):
    item = protocol(tmp_path / "protocol.json")
    value = dict(database_path=str(tmp_path / "state.db"), native_owner_root=str(tmp_path / "native"),
        native_python=str(tmp_path / "python"), completed_close=item, issuer_identity=item,
        kr_listing_routing=item.model_copy(update={"purpose": "IDENTITY_ROUTING_ONLY"}), kis_protocols={"protocol.json": item})
    config = ProductionSourceConfiguration(**value)
    assert len(config.identity) == 64
    with pytest.raises(ValueError):
        ProductionSourceConfiguration(**value, rev10_receipt_sha256="0" * 64)
    value["kis_protocols"] = {"../private": item}
    with pytest.raises(ValueError, match="names_invalid"):
        ProductionSourceConfiguration(**value)


@pytest.mark.parametrize("wal", [False, True])
def test_private_snapshot_reads_current_rows_without_operating_sqlite_writes(tmp_path, wal):
    db = tmp_path / "operating.db"
    conn = sqlite3.connect(db)
    if wal:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute("CREATE TABLE source (value TEXT)")
    conn.execute("INSERT INTO source VALUES ('current')")
    conn.commit()
    paths = [p for p in tmp_path.iterdir() if p.name.startswith("operating.db")]
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths}
    with readonly_local_snapshot(db, temporary_parent=tmp_path) as (session, receipt):
        assert session.exec(text("SELECT value FROM source")).one()[0] == "current"
        assert receipt["operating_sqlite_opened"] is False
        assert receipt["migration"] == "NO_MIGRATION_REQUIRED"
        with pytest.raises(Exception, match="readonly"):
            session.exec(text("INSERT INTO source VALUES ('forbidden')"))
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths} == before
    assert not list(tmp_path.glob("local-source-*"))
    conn.close()


def test_private_snapshot_fails_on_concurrent_operating_change(tmp_path, monkeypatch):
    from app.services import production_local_snapshot as owner
    db = tmp_path / "operating.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE source (value TEXT)")
    conn.commit()
    original = owner._identity
    calls = []

    def changed(path):
        calls.append(path)
        if len(calls) == 3:
            conn.execute("INSERT INTO source VALUES ('concurrent')")
            conn.commit()
        return original(path)

    monkeypatch.setattr(owner, "_identity", changed)
    with pytest.raises(ValueError, match="changed_during_snapshot"):
        with owner.readonly_local_snapshot(db, temporary_parent=tmp_path):
            raise AssertionError("mixed snapshot must never be consumed")
    conn.close()
