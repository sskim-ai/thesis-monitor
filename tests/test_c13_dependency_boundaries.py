"""Offline retained-graph proof; never constructs a live Source capability."""
import asyncio,json,os,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.services.current_scoped_source_dispatch import CurrentScopedRequestPlan
from app.services.sealed_fresh_dispatch import SealedDispatcher,consume_bound_result
from app.services.sealed_response_binding import SlotNotSelected
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_snapshot_contract import digest
from app.services.market_component_execution import drain_selected_market_slots,verified_raw_hashes

@pytest.fixture
def retained(tmp_path):
    supplied=os.environ.get('C13_KR_CAPTURE')
    if not supplied:pytest.skip('Explicit retained public-source capture required')
    source=Path(supplied);root=tmp_path/'TEST_ONLY_KR_REPLAY'
    shutil.copytree(source,root)
    run=object.__new__(SealedDispatcher)
    run.root=root;run.plan=CurrentScopedRequestPlan.model_validate(json.loads((root/'plan.json').read_bytes()))
    run.results={};run.used=set();run.halted=False
    for p in sorted((root/'physical').glob('attempt-*.start.json')):
        e=json.loads(p.read_bytes());key=e['logical_request_id']
        resolved,_,_=run.resolve(key)
        f=json.loads((root/'receipts'/key/'final.json').read_bytes())
        consume_bound_result(root=root,plan=run.plan,logical_id=key,receipt_sha256=f['receipt_sha256'])
        run.results[key]=f;run.used.add(key)
    assert len(run.results)==42
    return run

def test_retained_actual_42_parent_before_child(retained):
    assert len(retained.results)==42
    assert all(set(d.response_binding.parents)<=retained.results.keys()
        for d in retained.plan.descriptors if d.logical_request_id in retained.used and d.response_binding)

def test_missing_predecessor_is_not_a_terminal_success(retained):
    with pytest.raises(SourceSafetyStop,match='binding_parent_not_executed'):
        retained.resolve('kr_market:KOSPI:ka10066:continuation:16')

def test_original_drain_persists_all_seven_no_io_receipts(retained):
    class NoHTTP:
        async def command(self,c):raise AssertionError('No new request allowed')
    asyncio.run(drain_selected_market_slots(NoHTTP(),retained))
    tails=[r for r in retained.results.values() if r['status']=='NOT_SELECTED']
    assert len(tails)==7 and all(not r['attempts'] for r in tails)
    assert len(verified_raw_hashes(retained.results,retained.plan,retained.root))>=1
    assert len(retained.used)==len(retained.plan.descriptors)
    with pytest.raises(SourceSafetyStop,match='repeated'):
        retained.skip_unselected('kr_market:KOSPI:ka10066:continuation:15')

@pytest.mark.parametrize('mutation',['reverse','missing_parent','cycle'])
def test_original_plan_rejects_invalid_dependency_order(retained,mutation):
    raw=retained.plan.model_dump(mode='json');rows=raw['descriptors']
    if mutation=='reverse':rows.reverse()
    elif mutation=='missing_parent':rows[:]=[d for d in rows if d['logical_request_id']!='kr_market:KOSPI:ka10066:continuation:15']
    else:
        child=next(d for d in rows if d['logical_request_id']=='kr_market:KOSPI:ka10066:continuation:15')
        child['response_binding']['parents']=['kr_market:KOSPI:ka10066:continuation:16']
    with pytest.raises(ValueError):CurrentScopedRequestPlan.model_validate(raw)

@pytest.mark.parametrize('mutation',['generation_id','descriptor_sha256','plan_sha256','logical_request_id'])
def test_parent_identity_cannot_be_rehashed_into_authority(retained,mutation):
    key='kr_market:KOSPI:ka10066:continuation:14'
    p=retained.root/'receipts'/key/'final.json';f=json.loads(p.read_bytes())
    f[mutation]='0'*64 if mutation.endswith('sha256') else 'wrong'
    f['receipt_sha256']=digest({k:v for k,v in f.items() if k!='receipt_sha256'})
    p.write_text(json.dumps(f));retained.results[key]=f
    with pytest.raises(ValueError):retained.resolve('kr_market:KOSPI:ka10066:continuation:15')

def test_changed_binding_code_is_not_a_valid_parent(retained):
    retained.plan=retained.plan.model_copy(update={'binding_owner_sha256':'0'*64})
    with pytest.raises(SourceSafetyStop,match='response_binding_owner_drift'):
        retained.resolve('kr_market:KOSPI:ka10066:continuation:15')

def test_json_parent_cannot_restore_expired_capability():
    from app.services.pending_source_parent import resolve_parent
    with pytest.raises(ValueError):resolve_parent({'scope':'SCOPED_COMPLETED_CLOSE_ONLY_PENDING'})

def test_pending_json_cannot_issue_a_current_price():
    from app.services.pending_source_intake import consume_intake
    with pytest.raises(ValueError):consume_intake({},generation_id='old',role='completed_close',security_ids=('x',),session='2026-11-05')

def test_historical_json_cannot_be_a_technical_owner():
    from app.services.vnext_optional_fy1_research import attach
    with pytest.raises(ValueError,match='live_owner'):
        attach({'public_security':{},'as_of':'2026-11-05'},technical_owner={})

def test_fabricated_valuation_is_not_an_atomic_owner():
    from app.services.provider_native_valuation_snapshot import ProviderNativeValuationSnapshot
    with pytest.raises(ValueError):ProviderNativeValuationSnapshot.model_validate({'metric':'PER','value':1,'display_eligible':True})

def test_native_admission_cannot_be_constructed_from_historical_json():
    from app.services.canonical_native_admission import CanonicalNativeAdmission
    with pytest.raises(ValueError):CanonicalNativeAdmission()

def test_one_subject_revocation_does_not_veto_other_research_subjects():
    from app.services.vnext_daily_research import UseRegistry
    r=UseRegistry();e=dict(source_sha='a'*64,original_run='old',field='completed_close')
    r.revoke('SECURITY_A','a'*64)
    assert r.revoked('SECURITY_A',e) and not r.revoked('SECURITY_B',e)

def test_sol_profile_and_legacy_policy_tag_are_separate():
    from app.services.vnext_balanced_stage_review import execution_profile,UNIFIED_AI_V3_SOL_HIGH,UNIFIED_AI_V3
    assert execution_profile(UNIFIED_AI_V3_SOL_HIGH).model=='gpt-6.1-sol'
    assert execution_profile(UNIFIED_AI_V3_SOL_HIGH)!=execution_profile(UNIFIED_AI_V3)

def test_mismatched_research_registration_rejected():
    from app.services.vnext_daily_research import stage_state,UseRegistry
    from app.services.vnext_composite_research import PUBLIC_ID
    a={k:'a' for k in PUBLIC_ID};a['canonical_security_id']='SEC_A';b=dict(a,canonical_security_id='SEC_B')
    with pytest.raises(ValueError,match='stage_registration_identity_mismatch'):
        stage_state({'public_security':a},{'security':b},UseRegistry())

def test_previous_market_session_cannot_fill_current_target():
    from app.services.native_completed_market import select_completed_daily_rows
    with pytest.raises(ValueError,match='target_completed_session_missing'):
        select_completed_daily_rows([{'date':'2026-11-03'},{'date':'2026-11-04'}],target_session='2026-11-05',count=2)

def test_pending_monitoring_request_does_not_become_active():
    from datetime import datetime,timezone
    from app.services.onboarding_readiness_service import production_universe_snapshot
    item=SimpleNamespace(ticker='SYNTH',exchange='NASDAQ',monitoring_requested=True,active=False,
        onboarding_state='PENDING_ONBOARDING',production_eligible=False,activated_at=None,first_eligible_session=None)
    session=SimpleNamespace(exec=lambda query:SimpleNamespace(all=lambda:[item],first=lambda:None))
    value=production_universe_snapshot(session,'us',cutoff=datetime(2026,11,6,tzinfo=timezone.utc),session_key='synthetic')
    assert not value.eligible_items
    assert set(value.excluded_subjects[0]['reasons'])=={'monitoring_not_active','onboarding_not_active','production_not_eligible'}
