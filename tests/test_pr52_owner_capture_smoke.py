"""Public CI: original registration capture with a disposable synthetic DB."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from app.services import prospective_class_c_owner as reg
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_plan import COUNTS, build_stock_plan
from app.services.selected_source_registration import capture_approved_markets, local_seed
from app.services.unified_snapshot_contract import digest
from tests.test_minimal_class_c_export import POLICY, database


def test_registered_kr_owner_projects_after_only_one_readonly_file_connection(tmp_path):
    scope = {"kr": ["005930"], "us": ["MU"]}
    fixture = database(tmp_path, [(t, m) for m, ts in scope.items() for t in ts])
    db = fixture.database
    db_uri = db.as_uri() + "?mode=ro"
    db_sha = sha256(db.read_bytes()).hexdigest()
    now = datetime.now(timezone.utc)
    event = "SYNTHETIC_OWNER_INTEGRATION"
    permit = reg.record_backend_approval(reg.ApprovalDecision(
        event_id=event,
        approved=True,
        user_message_sha256=digest("synthetic fixture only"),
        effective_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
        subjects=fixture.subjects,
    ))
    generations = {"kr": "SYNTHETIC_KR_SOURCE"}
    ledger = SelectedRunLedger(
        path=tmp_path / "fixture-ledger.jsonl",
        approval=permit,
        master_id="SYNTHETIC_MASTER",
        children={m: {"generation": generations.get(m, "SYNTHETIC_US_INACTIVE"), "subjects": ts}
                  for m, ts in scope.items()},
        provider_caps={},
        max_http=0,
        max_models=0,
        database_identity={"path": str(db), "device": db.stat().st_dev, "inode": db.stat().st_ino},
        staged_markets=True,
        runtime_cap={"endpoints": {"fixture": {"unused": True}},
                     "market_subjects": {"kr": [], "us": []},
                     "stop_on_first_external_failure": True},
        capture_max_private_export_bytes=64 * 1024**2,
    )
    observed = []
    active = True

    def guard(kind, args):
        if not active:
            return
        if kind == "sqlite3.connect":
            target = str(args[0])
            if target not in {db_uri, ":memory:"}:
                raise PermissionError("fixture_unapproved_database_denied")
            observed.append(target)
        if kind.startswith(("socket.", "subprocess.", "os.exec", "os.posix_spawn")):
            raise PermissionError("fixture_external_io_denied")

    sys.addaudithook(guard)
    owners = {}
    try:
        _, owners, readback = capture_approved_markets(
            settings=SimpleNamespace(database_url="sqlite:///" + str(db)),
            runtime_directory=tmp_path,
            approval=permit,
            generations=generations,
            policy=POLICY,
            ledger=ledger,
            enabled=True,
            subject_limits={"kr": 1},
            priority_subjects={"kr": ("005930",)},
        )
        assert readback["sqlite_mode"] == "ro" and readback["query_only"]
        state = ledger.state()
        assert state["db_select_actual"] == 5 and state["http_total"] == state["model_total"] == 0
        owner = owners["kr"]
        document, receipt = reg._state(owner)
        identities = {r["record"]["ticker"]: r["record"]
                      for r in document["roles"]["security_identity"]["records"]}
        assert tuple(identities) == ("005930",)
        plan = build_stock_plan(
            market="kr", identities=identities, at=datetime.fromisoformat(receipt["cutoff"]),
            generation=generations["kr"], code_sha="a" * 40, counts=COUNTS,
        )
        assert plan.planning_only  # This test does not issue Native/financial dispatch authority.
        seed = local_seed(owner, stock=plan, policy=POLICY)
        assert seed["market"] == "kr" and seed["cutoff"] == receipt["cutoff"]
        assert seed["session"] == receipt["calendar"]["target"]
        assert observed[0] == db_uri and observed.count(db_uri) == 1
        assert observed[1:] and set(observed[1:]) == {":memory:"}
        for target in (db, tmp_path / "unexpected.sqlite3"):
            with pytest.raises(PermissionError, match="fixture_unapproved_database_denied"):
                sqlite3.connect(target)
        assert sha256(db.read_bytes()).hexdigest() == db_sha
    finally:
        active = False
        for owner in owners.values():
            reg.revoke_prospective_owner(owner)
        reg.revoke_approval(permit)
