import json
from datetime import datetime, timezone
import sqlite3

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel, create_engine

from scripts.unified_adapter_preflight import (
    current_universe, file_hash, provider_telemetry_audit, raw_ohlcv_artifacts,
)


def test_telemetry_does_not_treat_skipped_provider_as_a_call():
    receipt = provider_telemetry_audit([
        {"provider": "alpha_vantage", "skip_delta": 8, "success_delta": 0},
        {"provider": "sec_edgar", "success_delta": 2},
    ])
    assert not receipt["prohibited_acquisition_events"]
    assert receipt["provider_events"]["alpha_vantage"]["skipped_events"] == 8
    assert receipt["current_task_provider_calls"] == 0


def test_historical_counts_are_not_current_network_counts():
    receipt = provider_telemetry_audit([
        {"provider": "alpha_vantage", "endpoint": "OVERVIEW", "ticker": "EXAMPLE",
         "success_delta": 1, "failure_delta": 2},
    ])
    assert len(receipt["prohibited_acquisition_events"]) == 1
    assert receipt["provider_events"]["alpha_vantage"]["failure_events"] == 2
    assert receipt["current_task_provider_calls"] == 0
    assert "not_exact_HTTP" in receipt["interpretation"]


def test_normalized_summary_is_not_a_raw_ohlcv_response(tmp_path):
    source = tmp_path / "private/source-results"
    source.mkdir(parents=True)
    (source / "stock.json").write_text(json.dumps({
        "status": "PASS", "raw_bar_fingerprint": "a" * 64,
        "periods": {"daily": {"bar_count": 100}},
    }))
    assert raw_ohlcv_artifacts(tmp_path) == []


def test_only_declared_archive_paths_are_inspected(tmp_path):
    payload = {"resolved_symbol": {"code": "EXAMPLE"}, "periods": {"daily": []}}
    source = tmp_path / "source"
    source.mkdir()
    inside = source / "response.json"
    inside.write_text(json.dumps(payload))
    other = tmp_path / "operating-state"
    other.mkdir()
    (other / "response.json").write_text(json.dumps(payload))
    (source / "link.json").symlink_to(other / "response.json")
    assert raw_ohlcv_artifacts(tmp_path) == [
        {"path": "source/response.json", "sha256": file_hash(inside)},
    ]


def test_canonical_universe_uses_readonly_database(tmp_path, monkeypatch):
    db = tmp_path / "local-fixture.sqlite3"
    engine = create_engine(f"sqlite:///{db}")
    SQLModel.metadata.create_all(engine)
    engine.dispose()
    before = file_hash(db)
    from scripts import unified_adapter_preflight as owner
    original = owner.production_universe_snapshot
    attempts = []

    def audit_query_only(session, *args, **kwargs):
        assert session.connection().exec_driver_sql("PRAGMA query_only").scalar() == 1
        with pytest.raises(OperationalError, match="readonly"):
            session.connection().exec_driver_sql("CREATE TABLE forbidden_write (x INT)")
        attempts.append(1)
        return original(session, *args, **kwargs)

    monkeypatch.setattr(owner, "production_universe_snapshot", audit_query_only)
    receipt = current_universe(db, datetime.now(timezone.utc))
    assert len(attempts) == 2
    assert receipt["us"]["eligible_subjects"] == receipt["kr"]["eligible_subjects"] == []
    assert file_hash(db) == before
    with sqlite3.connect(db) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name='forbidden_write'",
        ).fetchone() is None
