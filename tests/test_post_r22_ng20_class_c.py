"""Isolated original Class-C issuance, not Manual/Native consumer proof."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.services import minimal_class_c_export as exporter
from app.services import prospective_class_c_owner as prospective
from app.services.unified_local_seed_bridge import admit_pinned_local_seed
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import UNIVERSE
from tests.ng20_class_c_fixture import DIRECTORY, TEST_ONLY, build_class_c_fixture


POLICY = UnifiedSourcePolicy(frozenset({"canonical_local", "sec_edgar", "opendart"}))
GENERATION = "TEST_ONLY_SYNTHETIC-ng20-class-c"


@pytest.fixture
def clock(monkeypatch):
    cutoff = datetime(2026, 10, 19, 7, tzinfo=timezone.utc)

    class CaptureClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cutoff.astimezone(tz) if tz is not None else cutoff.replace(tzinfo=None)

    monkeypatch.setattr(exporter, "datetime", CaptureClock)
    monkeypatch.setattr(prospective, "_now", lambda: cutoff)
    return cutoff


@pytest.fixture
def captured(tmp_path, clock):
    return build_class_c_fixture(
        tmp_path, generation_id=GENERATION, source_generation_id=GENERATION + ":source",
        cutoff=clock, policy=POLICY,
    )


def test_original_capture_and_two_market_owner_replay(captured, clock, record_property):
    receipt = captured["capture_receipt"]
    assert receipt["cutoff"] == receipt["snapshot_started_at"] == receipt["snapshot_finished_at"] == clock.isoformat()
    assert receipt["generation_retroactive"] is False
    assert all(value["selected"] == 22 and value["missing"] == 0 for value in receipt["tables"].values())
    assert [row["operation"] for row in receipt["query_trace"]] == [
        "PRAGMA", "PRAGMA", "BEGIN", *["SELECT"] * 5, "ROLLBACK"]
    assert set(table for table, _ in receipt["observed_column_reads"]) == set(exporter.COLUMNS)
    assert digest(captured["simulated_approval_event"]) == captured["approval_decision"].user_message_sha256
    for market, tickers in UNIVERSE.items():
        owner, document = captured["owners"][market], captured["projections"][market]
        prospective.require_generation(owner, GENERATION)
        accepted = admit_pinned_local_seed(
            captured["projection_bytes"][market],
            expected_sha256=captured["protected_input_hashes"]["class-c/local-" + market + ".json"],
            market=market, session_key=captured["sessions"][market], cutoff=clock,
            subjects=tickers, policy=POLICY, prospective_owner=owner,
        )
        assert accepted == document and document["production_seed_qualified"] is False
        issued = document["prospective_owner_receipt"]
        assert issued["scope"] == "MEMBERSHIP_ONLY_NOT_D01_D02"
        assert issued["approval_event"].startswith(TEST_ONLY)
        assert issued["capture_receipt_sha256"] == digest(receipt)
        assert set(issued["bindings"]) == set(tickers)
        assert all(r["original_first_eligible_session"] == captured["sessions"][market]
                   for r in issued["bindings"].values())
        assert captured["original_projections"][market]["denials"]
    record_property("ng20_class_c_issuance", captured["diagnostics"])


def test_mismatched_clock_denied_before_new_database(tmp_path, clock):
    with pytest.raises(ValueError, match="caller_installed_capture_and_owner_clock_required"):
        build_class_c_fixture(tmp_path, generation_id=GENERATION, source_generation_id=GENERATION,
                              cutoff=clock + timedelta(seconds=1), policy=POLICY)
    assert not (tmp_path / DIRECTORY).exists()


def test_false_export_permission_denied_before_connection(captured):
    def forbidden_connect(*args, **kwargs):
        pytest.fail("denied permission must not open SQLite")

    with pytest.raises(PermissionError, match="explicit_read_authorization_required"):
        exporter.capture_authorized_class_c(replace(captured["permission"], approved=False),
                                            connect=forbidden_connect)


def test_raw_copy_and_unissued_capture_cannot_replace_original(captured):
    original = captured["raw"]
    document = deepcopy(captured["projections"]["us"])
    document["prospective_owner_receipt"]["generation_id"] = "other"
    assert exporter.captured_private_snapshot(captured["capture"])[0] == original
    with pytest.raises(ValueError, match="class_c_unissued_capture"):
        exporter.project_captured_export(exporter.CapturedClassC(), market="us",
            session_key=captured["sessions"]["us"], policy=POLICY)
    with pytest.raises(ValueError, match="prospective_receipt_replay_mismatch"):
        admit_pinned_local_seed(encoded(document), expected_sha256=digest(document),
            market="us", session_key=document["session"],
            cutoff=datetime.fromisoformat(document["cutoff"]), subjects=UNIVERSE["us"],
            policy=POLICY, prospective_owner=captured["owners"]["us"])


@pytest.mark.parametrize("action", ["wrong_generation", "production_purpose", "revoked_approval", "expired"])
def test_original_owner_scope_and_lifetime(captured, monkeypatch, action):
    owner = captured["owners"]["us"]
    generation, purpose = GENERATION, prospective.SCOPE
    if action == "wrong_generation":
        generation = "other-generation"
    elif action == "production_purpose":
        purpose = "PRODUCTION_MONITORING"
    elif action == "revoked_approval":
        prospective.revoke_approval(captured["approval"])
    else:
        monkeypatch.setattr(prospective, "_now", lambda: captured["approval_decision"].expires_at)
    with pytest.raises(ValueError, match="prospective_generation_or_purpose_mismatch|prospective_live_operator_approval_required|prospective_approval_expired"):
        prospective.require_generation(owner, generation, purpose=purpose)
