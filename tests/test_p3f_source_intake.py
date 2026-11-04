"""SYNTHETIC/OFFLINE only; real Source/Market/Native readiness is never issued."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine

from app.services import pending_source_intake as intake
from app.services import prospective_class_c_owner as original
from app.services.minimal_class_c_export import (ExportPermission, capture_authorized_class_c,
    captured_private_snapshot, MODELS)
from app.services.unified_snapshot_contract import digest


@pytest.fixture
def pending(tmp_path):
    now=datetime.now(timezone.utc)
    approval=original.record_backend_approval(original.ApprovalDecision(event_id='SYNTHETIC_P3F',
        user_message_sha256='a'*64,approved=True,effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(minutes=10),subjects=('FUTURE',)))
    scope=intake.record_backend_intake_scope(approval=approval,generation_id='SYNTHETIC',
        source_generation_id='SYNTHETIC',exclusive_use_confirmed=True,confirmation_sha256='b'*64,
        confirmed_at=now,enabled=True)
    db=tmp_path/'synthetic.sqlite3';engine=create_engine('sqlite:///'+str(db))
    for model in MODELS.values():model.__table__.create(engine,checkfirst=True)
    with Session(engine) as session:
        session.add(MODELS['company'](ticker='FUTURE',company_name='Synthetic',exchange='NASDAQ'))
        session.add(MODELS['securitymaster'](ticker='FUTURE',company_name='Synthetic',exchange='NASDAQ',
            country='US',canonical_company_id='issuer-future',canonical_security_id='security-future'))
        session.add(MODELS['watchlistitem'](ticker='FUTURE',company_name='Synthetic',exchange='NASDAQ',
            active=False,production_eligible=False,monitoring_requested=True,onboarding_state='PENDING_ONBOARDING'))
        session.add(MODELS['investmentthesis'](ticker='FUTURE',version=1,status='active',core_thesis='Synthetic only'))
        session.commit()
    stat=db.stat()
    permission=ExportPermission('SYNTHETIC_P3F',True,db,stat.st_dev,stat.st_ino,('FUTURE',))
    capture=capture_authorized_class_c(permission)
    raw,_=captured_private_snapshot(capture)
    args=dict(scope=scope,capture=capture,market='us',expected_capture_sha256=digest(json.loads(raw)),enabled=True)
    yield args,approval,engine,permission
    original.revoke_approval(approval);engine.dispose()


def test_pending_positive_and_original_parent_remains_separate(pending):
    args,_,_,_=pending
    cap,receipt=intake.issue_intake(**args)
    consumed=intake.consume_intake(cap,generation_id='SYNTHETIC',role='adjusted_daily',
        security_ids=('security-future',),session=receipt['calendar']['target'])
    assert not any(consumed[k] for k in ('ACTIVE','production_eligible','MarketParent','native','valuation','send'))
    with pytest.raises(ValueError,match='live_backend_owner'):
        original.require_generation(cap,'SYNTHETIC')
    with pytest.raises(ValueError,match='SOURCE_INTAKE_ADAPTER_NOT_PROVEN'):
        intake.require_live_worker_adapter(cap)
    with pytest.raises(ValueError,match='live_owner_required'):
        intake.consume_intake(receipt,generation_id='SYNTHETIC',role='adjusted_daily',security_ids=('security-future',),session=receipt['calendar']['target'])
    intake.revoke_intake(cap)
    with pytest.raises(ValueError,match='live_owner_required'):
        intake.consume_intake(cap,generation_id='SYNTHETIC',role='adjusted_daily',security_ids=('security-future',),session=receipt['calendar']['target'])


@pytest.mark.parametrize('change',['active','thesis','identity','duplicate'])
def test_pending_corrupt_registration_is_rejected(pending,change):
    args,_,engine,permission=pending
    with Session(engine) as session:
        if change=='active':
            item=session.get(MODELS['watchlistitem'],1);item.active=True;item.production_eligible=True
            session.add(item)
        elif change=='thesis':
            item=session.get(MODELS['investmentthesis'],1);item.core_thesis='';session.add(item)
        elif change=='identity':
            item=session.get(MODELS['securitymaster'],1);item.canonical_security_id='';session.add(item)
        else:
            session.add(MODELS['securitymaster'](ticker='FUTURE',company_name='Duplicate',exchange='NASDAQ',
                country='US',canonical_company_id='duplicate-issuer',canonical_security_id='duplicate-security'))
            # The original schema rejects duplicate ticker identity before capture.
            with pytest.raises(IntegrityError):session.commit()
            session.rollback()
            return
        session.commit()
    with pytest.raises(ValueError):
        new=capture_authorized_class_c(permission)
        raw,_=captured_private_snapshot(new)
        intake.issue_intake(**dict(args,capture=new,expected_capture_sha256=digest(json.loads(raw))))


def test_pending_hash_old_receipt_and_default_off_rejected(pending):
    args,_,_,_=pending
    for change in ({'expected_capture_sha256':'0'*64},{'capture':{'contract':'old-owner'}},{'enabled':False}):
        with pytest.raises(ValueError):intake.issue_intake(**dict(args,**change))


@pytest.mark.parametrize('change',[{'generation_id':'OLD'},{'role':'native'},
    {'security_ids':('security-future','security-future')},{'session':'2000-01-01'}])
def test_pending_consumption_does_not_escalate(pending,change):
    cap,receipt=intake.issue_intake(**pending[0])
    args=dict(generation_id='SYNTHETIC',role='completed_close',security_ids=('security-future',),session=receipt['calendar']['target'])
    with pytest.raises(ValueError):intake.consume_intake(cap,**dict(args,**change))


def test_unconfirmed_and_expired_scope_rejected(pending,monkeypatch):
    args,approval,_,_=pending
    now=datetime.now(timezone.utc)
    with pytest.raises(ValueError,match='exclusivity'):
        intake.record_backend_intake_scope(approval=approval,generation_id='x',source_generation_id='x',
            exclusive_use_confirmed=False,confirmation_sha256='b'*64,confirmed_at=now,enabled=True)
    cap,receipt=intake.issue_intake(**args)
    monkeypatch.setattr(intake,'_now',lambda:now+timedelta(hours=2))
    with pytest.raises(ValueError):
        intake.consume_intake(cap,generation_id='SYNTHETIC',role='completed_close',security_ids=('security-future',),session=receipt['calendar']['target'])


def test_original_capture_and_intake_are_process_local(pending,monkeypatch):
    args,_,_,_=pending
    cap,receipt=intake.issue_intake(**args)
    monkeypatch.setattr(intake.os,'getpid',lambda:-1)
    with pytest.raises(ValueError,match='changed'):
        intake.consume_intake(cap,generation_id='SYNTHETIC',role='completed_close',security_ids=('security-future',),session=receipt['calendar']['target'])
