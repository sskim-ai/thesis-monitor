"""New intake boundaries; no prior suite rerun and no live providers."""
from datetime import datetime, timedelta, timezone
import sqlite3
import asyncio
import json

import pytest

from app.services import prospective_class_c_owner as owner
from app.services.minimal_class_c_export import capture_authorized_class_c, project_captured_export
from app.services.unified_snapshot_contract import digest
from test_minimal_class_c_export import database, POLICY


def pending(tmp_path, *, ticker='NEWUS', market='us', mutation=None):
    permission=database(tmp_path,[(ticker,market)])
    with sqlite3.connect(permission.database) as db:
        db.execute("UPDATE watchlistitem SET active=0, production_eligible=0, monitoring_requested=1, onboarding_state='PENDING_ONBOARDING',activated_at=NULL,first_eligible_session=NULL")
        if mutation:db.execute(mutation)
    now=datetime.now(timezone.utc)
    approval=owner.record_backend_approval(owner.ApprovalDecision(event_id='C8_SYNTHETIC_ONLY',
        user_message_sha256=digest('synthetic'),approved=True,effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(minutes=30),subjects=(ticker,)))
    capture=capture_authorized_class_c(permission)
    handle,receipt=owner.issue_source_intake_owner(approval=approval,capture=capture,market=market,
        generation_id='C8_TEST',policy=POLICY)
    return approval,capture,handle,receipt


@pytest.mark.parametrize('ticker,market',[('NEWUS','us'),('999999','kr')])
def test_pending_intake_uses_capture_without_production_promotion(tmp_path,ticker,market):
    _,capture,handle,receipt=pending(tmp_path,ticker=ticker,market=market)
    admitted=owner.require_source_intake(handle,generation_id='C8_TEST',ticker=ticker)
    assert admitted['registered_source_intake_eligible']
    assert not any(admitted[k] for k in ('research_analysis_eligible','current_production_ready','delivery_eligible','send','database_modified'))
    assert not receipt['production_seed_qualified'] and not receipt['source_or_economic_authority']
    at=datetime.fromisoformat(receipt['cutoff'])
    original=project_captured_export(capture,market=market,
        session_key=owner.completed_clock(market,at)['target'],policy=POLICY)
    assert original['universe']['eligible_subjects']==[]


@pytest.mark.parametrize('mutation',[
    'UPDATE watchlistitem SET monitoring_requested=0',
    "UPDATE watchlistitem SET onboarding_state='INACTIVE'",
    'UPDATE watchlistitem SET registration_requested_at=NULL',
    "UPDATE watchlistitem SET registration_requested_at='2099-01-01'",
    "UPDATE securitymaster SET canonical_security_id=''",
    "UPDATE securitymaster SET issuer_type='unknown'",
    "UPDATE securitymaster SET identity_provider='mock'",
    "UPDATE securitymaster SET identity_quality='missing'",
    "UPDATE securitymaster SET exchange='NYSE'",
    "UPDATE securitymaster SET updated_at='2099-01-01'",
    "UPDATE watchlistitem SET issuer_type='adr',adr_ratio=5",
    "UPDATE investmentthesis SET core_thesis=''",
    'DELETE FROM company',
])
def test_disabled_or_invalid_registration_does_not_bootstrap(tmp_path,mutation):
    if mutation.endswith('registration_requested_at=NULL'):
        with pytest.raises(sqlite3.IntegrityError):
            pending(tmp_path,mutation=mutation)
        return
    _,_,handle,receipt=pending(tmp_path,mutation=mutation)
    assert not receipt['subjects']['NEWUS']['registered_source_intake_eligible']
    with pytest.raises(ValueError,match='subject_denied'):
        owner.require_source_intake(handle,generation_id='C8_TEST',ticker='NEWUS')


@pytest.mark.parametrize('change',['forged','generation','subject','revoke','approval','expiry'])
def test_intake_capability_is_not_serialized_authority(tmp_path,monkeypatch,change):
    approval,_,handle,receipt=pending(tmp_path)
    if change=='forged':handle=owner.SourceIntakeOwner()
    if change=='revoke':owner.revoke_source_intake(handle)
    if change=='approval':owner.revoke_approval(approval)
    if change=='expiry':monkeypatch.setattr(owner,'_now',lambda:datetime.fromisoformat(receipt['expires_at']))
    with pytest.raises(ValueError):
        owner.require_source_intake(handle,generation_id='OTHER' if change=='generation' else 'C8_TEST',
            ticker='OTHER' if change=='subject' else 'NEWUS')


def test_adr_missing_share_basis_is_explicit_not_per_share_use(tmp_path):
    _,_,handle,receipt=pending(tmp_path,mutation="UPDATE securitymaster SET issuer_type='foreign_private_issuer',security_type='adr',country='TW'")
    admitted=owner.require_source_intake(handle,generation_id='C8_TEST',ticker='NEWUS')
    assert admitted['restricted_uses']==['SECURITY_MASTER:per_share_depositary_basis']
    assert not receipt['source_or_economic_authority']


def test_exact_restored_22_pending_cohort_intake_without_source_approval(tmp_path):
    from app.services.unified_stock_acquisition import UNIVERSE
    subjects=[(ticker,market) for market,tickers in UNIVERSE.items() for ticker in tickers]
    permission=database(tmp_path,subjects)
    with sqlite3.connect(permission.database) as db:
        db.execute("UPDATE watchlistitem SET active=0,production_eligible=0,monitoring_requested=1,onboarding_state='PENDING_ONBOARDING'")
    now=datetime.now(timezone.utc)
    approval=owner.record_backend_approval(owner.ApprovalDecision(event_id='C8_SYNTHETIC22',
        user_message_sha256=digest('synthetic22'),approved=True,effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(minutes=30),subjects=tuple(t for t,_ in subjects)))
    capture=capture_authorized_class_c(permission)
    for market in UNIVERSE:
        handle,receipt=owner.issue_source_intake_owner(approval=approval,capture=capture,market=market,
            generation_id='C8_TEST',policy=POLICY)
        assert set(receipt['subjects'])==set(UNIVERSE[market])
        assert all(owner.require_source_intake(handle,generation_id='C8_TEST',ticker=t)['registered_source_intake_eligible'] for t in UNIVERSE[market])


def test_authenticated_local_registration_is_not_upstream_data_entitlement(tmp_path):
    _,_,handle,receipt=pending(tmp_path,mutation="UPDATE securitymaster SET identity_provider='registered_manual_definition'")
    assert owner.require_source_intake(handle,generation_id='C8_TEST',ticker='NEWUS')['registered_source_intake_eligible']
    assert not receipt['source_or_economic_authority']


def test_intake_cannot_be_consumed_as_original_prospective_owner(tmp_path):
    _,_,handle,_=pending(tmp_path)
    with pytest.raises(ValueError,match='live_backend_owner'):
        owner.require_generation(handle,'C8_TEST')


def test_reconciler_rejects_forged_capability_before_database_or_collectors():
    from app.models.watchlist import WatchlistItem
    from app.services.onboarding_reconciler_service import resume_onboarding_subject,OnboardingAttemptMode
    with pytest.raises(ValueError,match='source_intake_live_owner_required'):
        asyncio.run(resume_onboarding_subject(None,WatchlistItem(ticker='NEWUS',company_name='Synthetic'),
            origin='C8_SYNTHETIC',mode=OnboardingAttemptMode.PREFLIGHT,
            source_intake_owner=owner.SourceIntakeOwner(),source_intake_generation='C8_TEST'))


def test_registration_drift_rejected_before_onboarding(tmp_path):
    from app.services.minimal_class_c_export import captured_private_snapshot,MODELS
    _,capture,handle,_=pending(tmp_path)
    raw,_=captured_private_snapshot(capture)
    item=MODELS['watchlistitem'].model_validate(json.loads(raw)['watchlistitem'][0])
    owner.require_source_intake(handle,generation_id='C8_TEST',ticker='NEWUS',registration=item)
    item.monitoring_requested=False
    with pytest.raises(ValueError,match='registration_changed'):
        owner.require_source_intake(handle,generation_id='C8_TEST',ticker='NEWUS',registration=item)
