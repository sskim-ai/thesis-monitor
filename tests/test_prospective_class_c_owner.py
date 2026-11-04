"""Real boundaries, synthetic SQLite and explicit synthetic operator decisions."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from app.services import prospective_class_c_owner as p
from app.services.minimal_class_c_export import CapturedClassC, capture_authorized_class_c
from app.services.unified_local_seed_bridge import admit_pinned_local_seed
from app.services.unified_snapshot_contract import digest, encoded
from test_minimal_class_c_export import database, POLICY


def fixture(tmp_path, ticker="NEWUS", market="us", mutation=None):
    permission = database(tmp_path, [(ticker, market)])
    with sqlite3.connect(permission.database) as db:
        db.execute("UPDATE watchlistitem SET first_eligible_session='2026-09-26'")
        if mutation:
            db.execute(mutation)
    decision = p.ApprovalDecision(event_id="SYNTHETIC_OPERATOR_CONSENT", approved=True,
        user_message_sha256=digest("SYNTHETIC_USER_MESSAGE"),
        effective_at=datetime.now(timezone.utc)-timedelta(minutes=1),
        expires_at=datetime.now(timezone.utc)+timedelta(minutes=50), subjects=(ticker,))
    approval = p.record_backend_approval(decision)
    capture = capture_authorized_class_c(permission)
    return approval, capture, decision


def issue(approval, capture, market="us", **kw):
    return p.issue_prospective_owner(approval=approval, capture=capture, market=market,
        source_generation_id="synthetic-current-export", generation_id="synthetic-shadow", policy=POLICY, **kw)


def admit(document, handle):
    return admit_pinned_local_seed(encoded(document), expected_sha256=digest(document),
        market=document["market"], session_key=document["session"],
        cutoff=datetime.fromisoformat(document["cutoff"]), policy=POLICY,
        subjects=document["universe"]["eligible_subjects"], prospective_owner=handle)


@pytest.mark.parametrize("ticker,market", [("NEWUS", "us"), ("999999", "kr"), ("NEWADS", "us")])
def test_live_capture_original_owner_idempotent_prospective_admission(tmp_path, ticker, market):
    approval, capture, _ = fixture(tmp_path, ticker, market)
    handle, doc = issue(approval, capture, market)
    assert admit(doc, handle) == doc == admit(doc, handle)
    assert doc["denials"] == []
    assert doc["production_seed_qualified"] is False
    receipt = doc["prospective_owner_receipt"]
    assert receipt["historical_writer_authority"] == "NOT_AVAILABLE"
    assert receipt["bindings"][ticker]["original_first_eligible_session"] == "2026-09-26"
    assert receipt["purpose"] == "MANUAL_SHADOW_UNSENT"
    assert "scheduled_at" not in receipt
    assert "NOT_D01_D02" in receipt["scope"]


@pytest.mark.parametrize("mutation", ["bare_owner", "bare_capture", "no_consent", "wrong_subject", "future_consent", "scheduled", "send"])
def test_no_caller_generated_authority(tmp_path, mutation):
    approval, capture, decision = fixture(tmp_path)
    if mutation == "bare_owner":
        _, doc = issue(approval, capture)
        with pytest.raises(ValueError):
            admit(doc, p.ProspectiveOwner())
        return
    if mutation == "bare_capture":
        capture = CapturedClassC()
    elif mutation == "no_consent":
        approval = p.OperatorApproval()
    elif mutation == "wrong_subject":
        approval = p.record_backend_approval(decision.model_copy(update={"subjects": ("OTHER",)}))
    elif mutation == "future_consent":
        with pytest.raises(ValueError):
            p.record_backend_approval(decision.model_copy(update={"effective_at": decision.expires_at}))
        return
    with pytest.raises(ValueError):
        issue(approval, capture, purpose=mutation if mutation in {"scheduled", "send"} else p.SCOPE)


@pytest.mark.parametrize("mutation", ["thesis", "security", "cutoff", "session", "receipt", "mode", "universe", "unissued_json"])
def test_edited_rehashed_projection_cannot_reissue(tmp_path, mutation):
    approval, capture, _ = fixture(tmp_path)
    handle, doc = issue(approval, capture)
    changed = deepcopy(doc)
    if mutation in {"thesis", "security"}:
        table = "investmentthesis" if mutation == "thesis" else "securitymaster"
        for component in changed["roles"].values():
            for row in component["records"]:
                if row["table"] == table:
                    key = "core_thesis" if mutation == "thesis" else "canonical_security_id"
                    row["record"][key] = "FORGED"
                    row["original_record_sha256"] = digest(row["record"])
            component["version"] = digest(component["records"])
    elif mutation == "cutoff":
        changed["cutoff"] = "2026-09-25T12:00:00+00:00"
    elif mutation == "session":
        changed["session"] = "2026-09-25"
    elif mutation == "receipt":
        changed["prospective_owner_receipt"]["generation_id"] = "OTHER"
    elif mutation == "mode":
        changed["prospective_owner_receipt"]["purpose"] = "SCHEDULED"
    elif mutation == "universe":
        changed["universe"]["eligible_subjects"] = ["OTHER"]
    else:
        handle = None
    with pytest.raises(ValueError):
        admit(changed, handle)


@pytest.mark.parametrize("action", ["revoke", "revoke_consent", "expiry", "wrong_generation", "wrong_purpose"])
def test_lifetime_and_run_scope(tmp_path, monkeypatch, action):
    approval, capture, _ = fixture(tmp_path)
    handle, doc = issue(approval, capture)
    if action == "revoke":
        p.revoke_prospective_owner(handle)
    elif action == "revoke_consent":
        p.revoke_approval(approval)
    elif action == "expiry":
        monkeypatch.setattr(p, "_now", lambda: datetime.fromisoformat(doc["prospective_owner_receipt"]["expires_at"]))
    else:
        with pytest.raises(ValueError):
            p.require_generation(handle, "OTHER" if action == "wrong_generation" else "synthetic-shadow", purpose="SCHEDULED" if action == "wrong_purpose" else p.SCOPE)
        return
    with pytest.raises(ValueError):
        admit(doc, handle)


@pytest.mark.parametrize("sql", [
    "UPDATE investmentthesis SET core_thesis='' WHERE version=2",
    "UPDATE watchlistitem SET active=0",
    "UPDATE securitymaster SET updated_at='2099-01-01'",
])
def test_unrelated_owner_denial_not_removed(tmp_path, sql):
    approval, capture, _ = fixture(tmp_path, mutation=sql)
    with pytest.raises(ValueError):
        handle, doc = issue(approval, capture)
        admit(doc, handle)


def test_false_operator_decision_not_issued():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        p.record_backend_approval(p.ApprovalDecision(event_id="denied", user_message_sha256=digest("denied"),
            approved=False, effective_at=now, expires_at=now+timedelta(hours=1), subjects=("NEWUS",)))


def test_duplicate_issue_is_same_live_capability_and_revoked_run_stays_revoked(tmp_path):
    approval, capture, _ = fixture(tmp_path)
    owner, document = issue(approval, capture)
    again, same = issue(approval, capture)
    assert again is owner and same == document
    p.revoke_prospective_owner(owner)
    with pytest.raises(ValueError, match="live_backend_owner"):
        issue(approval, capture)


@pytest.mark.parametrize("ticker,market,sql", [
    ("NEWNYSE", "us", "UPDATE securitymaster SET exchange='NYSE'"),
    ("NEWKOSDAQ", "kr", "UPDATE securitymaster SET exchange='KOSDAQ'"),
    ("NEWADR", "us", "UPDATE securitymaster SET security_type='adr',issuer_type='foreign_private_issuer',country='TW'"),
])
def test_listing_property_generality_with_real_owner_checks(tmp_path, ticker, market, sql):
    # Listing changes must agree in both original owners; nationality is not venue.
    permission = database(tmp_path, [(ticker, market)])
    with sqlite3.connect(permission.database) as db:
        db.execute(sql)
        if ticker == 'NEWNYSE':
            db.execute("UPDATE watchlistitem SET exchange='NYSE'")
        if ticker == 'NEWKOSDAQ':
            db.execute("UPDATE watchlistitem SET exchange='KOSDAQ'")
    now = datetime.now(timezone.utc)
    consent = p.record_backend_approval(p.ApprovalDecision(event_id='SYNTHETIC', approved=True,
        user_message_sha256=digest('synthetic'), effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(minutes=10), subjects=(ticker,)))
    handle, doc = issue(consent, capture_authorized_class_c(permission), market)
    assert admit(doc, handle) == doc


@pytest.mark.parametrize("ticker,market", [('035420','kr'),('NVDA','us')])
def test_new_registration_template_does_not_inherit_existing_approval(tmp_path, ticker, market):
    permission = database(tmp_path, [(ticker,market)])
    now=datetime.now(timezone.utc)
    consent=p.record_backend_approval(p.ApprovalDecision(event_id='SYNTHETIC_EXISTING_ONLY',approved=True,
        user_message_sha256=digest('existing only'),effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(minutes=10),subjects=('EXISTING',)))
    with pytest.raises(ValueError,match='subject_not_operator_authorized'):
        issue(consent,capture_authorized_class_c(permission),market)
