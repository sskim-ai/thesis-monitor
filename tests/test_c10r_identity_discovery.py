"""Discovery permits official lookup, not acquisition/economic qualification."""
import json
from datetime import datetime, timezone

import pytest

from app.services import prospective_class_c_owner as owner
from app.services.minimal_class_c_export import MODELS, captured_private_snapshot
from app.services.onboarding_readiness_service import evaluate_identity_discovery
from test_c8_source_intake import pending
from test_minimal_class_c_export import POLICY


def discovery_capture(tmp_path, **kwargs):
    approval,capture,handle,receipt=pending(tmp_path,**kwargs)
    _,captured=captured_private_snapshot(capture)
    decision=owner._approval(approval)
    approval=owner.record_backend_approval(decision.model_copy(update={'event_id':captured['permission_event']}))
    return approval,capture,handle,receipt


@pytest.mark.parametrize('mutation',[
    "UPDATE securitymaster SET identity_quality='missing'",
    "UPDATE securitymaster SET identity_provider=''",
    "UPDATE securitymaster SET issuer_type='adr',adr_ratio=NULL",
])
def test_official_discovery_does_not_require_its_output(tmp_path, mutation):
    approval,capture,_,_=discovery_capture(tmp_path,mutation=mutation)
    handle,receipt=owner.issue_identity_discovery_owner(approval=approval,capture=capture,
        generation_id='C10R_TEST',policy=POLICY)
    assert receipt['subjects']['NEWUS']['identity_discovery_eligible']
    original=owner.require_identity_discovery(handle,generation_id='C10R_TEST',ticker='NEWUS')
    assert original['ticker']=='NEWUS'
    assert not any(receipt[k] for k in ('source_use','financial_use','current_production_ready','send'))
    with pytest.raises(ValueError):owner.require_generation(handle,'C10R_TEST')
    with pytest.raises(ValueError):owner.require_source_intake(handle,generation_id='C10R_TEST',ticker='NEWUS')


@pytest.mark.parametrize('change',['forged','generation','subject','revoked'])
def test_discovery_cannot_be_reconstructed_or_broadened(tmp_path,change):
    approval,capture,_,_=discovery_capture(tmp_path)
    handle,receipt=owner.issue_identity_discovery_owner(approval=approval,capture=capture,
        generation_id='C10R_TEST',policy=POLICY)
    if change=='forged':handle=receipt
    if change=='revoked':owner.revoke_approval(approval)
    with pytest.raises((TypeError,ValueError)):
        owner.require_identity_discovery(handle,generation_id='WRONG' if change=='generation' else 'C10R_TEST',
            ticker='OTHER' if change=='subject' else 'NEWUS')


@pytest.mark.parametrize('change',['intent','company','thesis','future'])
def test_original_registration_requirements_remain(tmp_path,change):
    _,capture,_,_=pending(tmp_path)
    raw,_=captured_private_snapshot(capture)
    rows={t:MODELS[t].model_validate(values[0]) for t,values in json.loads(raw).items()}
    if change=='intent':rows['watchlistitem'].monitoring_requested=False
    if change=='company':rows['company'].exchange='OTHER'
    if change=='thesis':rows['investmentthesis'].core_thesis=' '
    if change=='future':rows['watchlistitem'].registration_requested_at=datetime(2100,1,1,tzinfo=timezone.utc)
    result=evaluate_identity_discovery(rows['watchlistitem'],rows['securitymaster'],rows['company'],
        rows['investmentthesis'],cutoff=datetime.now(timezone.utc),policy=POLICY)
    assert not result['identity_discovery_eligible'] and result['denials']
