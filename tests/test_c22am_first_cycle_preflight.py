"""C22AM bounded offline probes. All rows, consents and wires are synthetic."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.services import minimal_class_c_export as export
from app.services import prospective_class_c_owner as prospective
from app.services import selected_source_registration as registration
from app.services.model_execution_plan import CohortSubject, FrozenCohort, compile_model_plan
from app.services.production_model_profile import SolHighCallBudget
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.selected_source_plan import SelectedConsumerPolicy, build_stock_plan, COUNTS
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests.test_minimal_class_c_export import database, POLICY

KST=ZoneInfo('Asia/Seoul')
AM=datetime(2026,11,13,8,10,tzinfo=KST).astimezone(timezone.utc)
PM=datetime(2026,11,13,16,10,tzinfo=KST).astimezone(timezone.utc)
SUBJECTS=(('MU','us'),('005930','kr'))

def record(name,value):
    folder=Path(os.environ['C22AM_PROBE_ROOT'])
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/(name+'.json')).open('x') as stream:
        json.dump(dict(provenance='SYNTHETIC_ORIGINAL_FUNCTIONS_NOT_CURRENT_OWNER',
            real_financial_HTTP=0,real_model_calls=0,operating_DB_connections=0,**value),stream,indent=2,default=str)

@pytest.fixture
def dual(tmp_path,monkeypatch,request):
    at=getattr(request,'param',AM)
    permission=database(tmp_path,list(SUBJECTS))
    with sqlite3.connect(permission.database) as db:
        db.execute("UPDATE watchlistitem SET first_eligible_session=CASE ticker WHEN 'MU' THEN '2026-11-13' ELSE '2026-11-12' END")
    class FixtureClock(datetime):
        @classmethod
        def now(cls,tz=None):
            return at.astimezone(tz) if tz else at.replace(tzinfo=None)
    monkeypatch.setattr(export,'datetime',FixtureClock)
    monkeypatch.setattr(prospective,'_now',lambda:at)
    decision=prospective.ApprovalDecision(event_id='synthetic-explicit-grant',approved=True,
        user_message_sha256=digest('OFFLINE_SYNTHETIC_NO_LIVE_APPROVAL'),effective_at=at-timedelta(minutes=1),
        expires_at=at+timedelta(minutes=30),subjects=tuple(t for t,_ in SUBJECTS))
    approval=prospective.record_backend_approval(decision)
    generations={m:'C22AM_SYNTHETIC_'+m.upper() for _,m in SUBJECTS}
    capture,owners,receipt=registration.capture_markets(permission=permission,approval=approval,
        generations=generations,policy=POLICY,enabled=True,market_subjects={m:[t] for t,m in SUBJECTS})
    yield SimpleNamespace(permission=permission,capture=capture,owners=owners,receipt=receipt,
        generations=generations,approval=approval,at=at)
    for owner in owners.values():prospective.revoke_prospective_owner(owner)
    prospective.revoke_approval(approval)

def test_kst_first_cycle_is_not_exchange_session_date():
    from app.services.onboarding_reconciler_service import _next_cycle_date
    before=datetime(2026,11,12,11,57,tzinfo=KST)
    assert _next_cycle_date('us',before)==date(2026,11,13)
    assert _next_cycle_date('kr',before)==date(2026,11,12)
    rows=[]
    for clock in (AM,AM+timedelta(minutes=5),AM+timedelta(minutes=10),PM,PM+timedelta(minutes=5),PM+timedelta(minutes=10)):
        sessions={m:prospective.completed_clock(m,clock)['target'] for m in ('us','kr')}
        assert sessions['us']=='2026-11-12'
        assert sessions['kr']==('2026-11-12' if clock<PM else '2026-11-13')
        rows.append(dict(cutoff=clock.isoformat(),KST_cycle_date=clock.astimezone(KST).date().isoformat(),sessions=sessions))
    record('clock_candidates',dict(candidates=rows,clock_was_not_changed_in_real_execution=True))

def test_original_dual_owner_to_local_seed_positive(dual,monkeypatch):
    from app.services import unified_local_seed_bridge as bridge
    results={};drift={};original_project=bridge.project_local_seed
    def compared(*args,**kwargs):
        projected=original_project(*args,**kwargs)
        authenticated,_=prospective._state(dual.owners[kwargs['market']])
        def differences(a,b,path='universe'):
            if type(a)!=type(b):return [path+':type']
            if isinstance(a,dict):
                return [p for key in a.keys()|b.keys() for p in (
                    differences(a[key],b[key],path+'/'+key) if key in a and key in b else [path+'/'+key+':presence'])]
            if isinstance(a,list):
                if len(a)!=len(b):return [path+':cardinality']
                return [p for i,(x,y) in enumerate(zip(a,b)) for p in differences(x,y,path+'/'+str(i))]
            return [] if a==b else [path]
        drift[kwargs['market']]=differences(projected['universe'],authenticated['universe'])
        return projected
    monkeypatch.setattr(bridge,'project_local_seed',compared)
    for ticker,market in SUBJECTS:
        owner=dual.owners[market]
        document,receipt=prospective._state(owner)
        assert any(d['reason']==prospective.LEGACY_DENIAL for d in document['denials'])
        identities={ticker:next(r['record'] for c in document['roles'].values()
            for r in c['records'] if r['table']=='securitymaster' and r['record']['ticker']==ticker)}
        plan=build_stock_plan(market=market,identities=identities,at=AM,generation=dual.generations[market],
            code_sha='a'*40,counts=COUNTS,registration_sha256=digest(receipt))
        projected=registration.local_seed(owner,stock=plan,policy=POLICY)
        assert projected['universe']['eligible_subjects']==[ticker] and not projected['denials']
        assert projected['production_seed_qualified'] is False
        assert receipt['scope']=='MEMBERSHIP_ONLY_NOT_D01_D02'
        with pytest.raises(ValueError):registration.local_seed(owner,stock=plan.model_copy(update={'run_id':'FOREIGN'}),policy=POLICY)
        results[market]=dict(owner_issued=True,local_seed=True,session=projected['session'],
            original_first_cycle=receipt['bindings'][ticker]['original_first_eligible_session'],
            membership_only=True,historical_writer_authority=receipt['historical_writer_authority'])
    assert sum(r['operation']=='SELECT' for r in dual.receipt['query_trace'])==5
    assert all(drift.values())
    record('dual_owner_local_seed',dict(markets=results,synthetic_capture_SELECT=5,actual_owner_issued=False,
        lossy_replay_universe_drift_paths=drift,full_original_capture_replay_preserved=True))

def test_only_legacy_denial_is_removed_and_row_changes_reject(dual):
    owner=dual.owners['kr'];original,_=prospective._state(owner)
    changed=deepcopy(original)
    extra=dict(role='security_identity',ticker='005930',reason='SYNTHETIC_UNRELATED_SOURCE_DENIAL')
    changed['denials'].append(extra)
    projected=prospective.apply_prospective_owner(changed,original=original,owner=owner)
    assert projected['denials']==[extra] and not projected['roles']['security_identity']['eligible']
    changed=deepcopy(original)
    for component in changed['roles'].values():
        for row in component['records']:
            if row['table']=='securitymaster':row['record']['canonical_security_id']='FORGED'
    with pytest.raises(ValueError):prospective.apply_prospective_owner(changed,original=original,owner=owner)
    record('denial_and_identity',dict(only_legacy_removed=True,unrelated_denial_preserved=True,changed_identity_rejected=True))

def test_date_eligibility_missing_and_future_records_still_reject(dual):
    from app.services.onboarding_readiness_service import canonical_registration_eligibility
    rows,_=export.captured_private_snapshot(dual.capture);rows=json.loads(rows)
    models={t:{r['ticker']:export.MODELS[t].model_validate(r) for r in values} for t,values in rows.items()}
    def check(ticker,cutoff,**changes):
        args=dict(ticker=ticker,item=models['watchlistitem'][ticker],security=models['securitymaster'][ticker],
            thesis=models['investmentthesis'][ticker],company=models['company'][ticker],cutoff=cutoff)
        return canonical_registration_eligibility(**{**args,**changes})
    old=datetime(2026,11,12,11,57,tzinfo=KST)
    assert not check('MU',old)['canonical_eligible'] and check('005930',old)['canonical_eligible']
    assert all(check(t,AM)['canonical_eligible'] for t,_ in SUBJECTS)
    assert not check('MU',AM,thesis=None)['canonical_eligible']
    future=models['securitymaster']['MU'].model_copy(update={'updated_at':AM+timedelta(seconds=1)})
    assert not check('MU',AM,security=future)['canonical_eligible']
    record('canonical_eligibility',dict(before=dict(MU=False,KR=True),eligible_cycle=dict(MU=True,KR=True),
        missing_thesis_rejected=True,future_identity_rejected=True,no_operating_rows_fabricated=True))

@pytest.mark.parametrize('dual',[PM],indirect=True)
def test_original_frozen_children_share_master_not_trade_date(dual,tmp_path):
    from app.services.selected_source_context import freeze_registered_child
    ledger=SimpleNamespace(identity={'children':{m:dict(generation=g,subjects=[t])
        for t,m in SUBJECTS for g in [dual.generations[m]]}},worker_binding=lambda:dict(test_only=True))
    configs={p:digest('SYNTHETIC_CONFIG:'+p) for p in ('kiwoom','sec_edgar','opendart','fred','eia','ecos',
        'krx_night_futures','finnhub','google_news_rss','naver_news')}
    results={}
    for ticker,market in SUBJECTS:
        frozen,compiler,kis,local=freeze_registered_child(registration_owner=dual.owners[market],policy=POLICY,
            code_sha='a'*40,native=None,native_owner_root=tmp_path/'not-installed',config_identities=configs,
            configured_kr_pages=20,listing_rows=[],kis_static_hashes={},
            completed_close_documentation={'path':'SYNTHETIC_ONLY','sha256':'a'*64},
            consumer_policy=SelectedConsumerPolicy(),master_id='C22AM_SYNTHETIC_MASTER',
            ohlcv_source_url='https://synthetic.invalid/ohlcv',enabled=True,run_ledger=ledger)
        assert frozen['master_id']=='C22AM_SYNTHETIC_MASTER'
        assert len(frozen['stock_plan']['reads'])==4 and frozen['financial_use_granted'] is False
        assert frozen['stock_plan']['planning_only'] is True
        assert frozen['sessions'][market]==prospective.completed_clock(market,dual.at)['target']
        results[market]=dict(generation=frozen['generation_id'],master=frozen['master_id'],
            sessions=frozen['sessions'],cutoff=frozen['frozen_at'],plan_sha256=digest(frozen['plan']),
            planning_only=True,kis_plan_present=kis is not None,local_seed_denials=local['denials'])
    assert len({r['generation'] for r in results.values()})==2
    assert results['us']['sessions']['us']=='2026-11-12'
    assert results['kr']['sessions']['kr']=='2026-11-13'
    record('frozen_children',dict(markets=results,dispatch=False,native_inspection_not_performed=True))

def test_original_capture_replay_does_not_accept_forged_rows_or_unissued_owner(dual):
    from app.services.unified_local_seed_bridge import admit_pinned_local_seed
    from app.services.unified_snapshot_contract import encoded
    owner=dual.owners['us'];original,_=prospective._state(owner)
    document=prospective.apply_prospective_owner(original,original=original,owner=owner)
    changed=deepcopy(document)
    for component in changed['roles'].values():
        for row in component['records']:
            if row['table']=='investmentthesis':
                row['record']['core_thesis']='FORGED_AND_REHASHED'
                row['original_record_sha256']=digest(row['record'])
        component['version']=digest(component['records'])
    raw=encoded(changed)
    with pytest.raises(ValueError):admit_pinned_local_seed(raw,expected_sha256=digest(changed),
        market='us',session_key=document['session'],cutoff=dual.at,subjects=['MU'],policy=POLICY,prospective_owner=owner)
    with pytest.raises(ValueError):prospective.replay_captured_local_seed(prospective.ProspectiveOwner(),policy=POLICY)
    retained=prospective._OWNER_CAPTURES.pop(owner)
    try:
        with pytest.raises(ValueError,match='original_capture_required'):
            prospective.replay_captured_local_seed(owner,policy=POLICY)
    finally:prospective._OWNER_CAPTURES[owner]=retained
    record('capture_replay_negatives',dict(forged_thesis_rejected=True,unissued_owner_rejected=True,
        missing_original_capture_rejected=True,no_query_or_source_hash_waiver=True))

@pytest.mark.parametrize('ticker',['MU','005930'])
def test_original_stock_economic_coverage_and_monitoring_preflight_positive(tmp_path,monkeypatch,ticker):
    from tests import test_newbuyer_b2_v2_coverage as fixture
    from tests.test_reported_business_native_projection import window
    from app.services.current_source_coverage import seal_inputs,compose,SEMANTICS
    from app.services.canonical_source_inputs import fresh_authority_inputs
    from app.services.canonical_monitoring_source import prepare_monitoring_subject
    from scripts.m12dr_financial_source_authority import build_source_authority
    from tests.rev10_source_fixtures import wire_clock
    original_fresh=fixture.fresh_inputs
    def fictional_wire(*args,**kwargs):
        with wire_clock(kwargs['plan'].frozen_at+timedelta(seconds=4)):
            return original_fresh(*args,**kwargs)
    monkeypatch.setattr(fixture,'fresh_inputs',fictional_wire)
    captured={};original=fixture.assemble_fresh_stock
    def observed(**inputs):
        inputs.update(reported_comparison_business=True,source_window=window(inputs['technical_inputs']['plan']))
        captured.update(inputs)
        return original(**inputs)
    monkeypatch.setattr(fixture,'assemble_fresh_stock',observed)
    owner=fixture.source(tmp_path/'source',ticker=ticker,generation='C22AM_MOCK_'+ticker,empty=ticker.isdigit())
    seal=seal_inputs({ticker:owner},subjects=[ticker],semantics_version=SEMANTICS)
    coverage=compose({ticker:owner},subjects=[ticker],generations={ticker:owner.generation},
        input_seal=seal,input_seal_sha256=seal['receipt_sha256'],semantics_version=SEMANTICS)
    assert coverage['coverage']['coverage_complete'] and coverage['census'] is not None
    authority=build_source_authority(**fresh_authority_inputs(owner.stock,captured))
    readiness,prepared=prepare_monitoring_subject(stock=owner.stock,authority=authority,
        local_seed=captured['technical_inputs']['local_seed'],generation=owner.generation)
    assert readiness['status']=='PASS' and prepared['mode']=='EVIDENCE_BASED'
    owner.stock['packet_sha256']='0'*64
    with pytest.raises(ValueError):prepare_monitoring_subject(stock=owner.stock,authority=authority,
        local_seed=captured['technical_inputs']['local_seed'],generation=owner.generation)
    record('stock_owner_'+ticker,dict(original_stock_owner=True,coverage_complete=True,subject_preflight='EVIDENCE_BASED',
        source_generation=owner.generation,source_cutoff=captured['technical_inputs']['plan'].frozen_at.isoformat(),
        no_current_C22AM_generation_grant=True,full_market_source_or_renderer_proved=False,
        valuation_resolutions=coverage['resolutions'][ticker]['metrics']))

def test_ten_canonical_slots_persist_consumption_and_never_reonboard(tmp_path):
    cohort=FrozenCohort('C22AM_TOY_MASTER','C22AM_TOY_SOURCE','2026-11-12',AM.isoformat(),AM.isoformat(),
        tuple(CohortSubject(m,t,'SYNTHETIC:'+t,AM.isoformat(),digest(t)) for t,m in SUBJECTS),
        tuple((m,digest(m)) for m in ('us','kr')),digest('PLANNING_ONLY'))
    plan=compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
    assert len(plan.slots)==10 and {s.stage for s in plan.slots}=={'MARKET','CORE','A','B','B2'}
    path=tmp_path/'calls.jsonl'
    budget=SolHighCallBudget(plan=plan,approved_max_invocations=10,approved_plan_sha256=plan.sha256,journal_path=path)
    for slot in plan.slots:
        payload=dict(input={'synthetic':True},response_schema={'type':'object'},prompt='SYNTHETIC')
        request=dict(market=slot.market,batch=1 if slot.stage=='MARKET' else slot.batch_id,subjects=list(slot.subjects),
            execution_generation_id=cohort.run_id,source_generation_id=cohort.source_generation,
            payload=payload,payload_sha256=digest(payload))
        scope=budget.bind_stage(slot.stage,request)
        budget.consume(None,slot.stage,digest(payload),slot_scope=scope)
        budget.record_acceptance(slot.slot_id,payload_sha256=digest(payload),output_sha256=digest(slot.slot_id))
    restored=SolHighCallBudget(plan=plan,approved_max_invocations=10,approved_plan_sha256=plan.sha256,journal_path=path)
    assert len(restored.used)==len(restored.accepted)==10
    with pytest.raises(ValueError):restored.consume(None,slot.stage,digest(payload),slot_scope=scope)
    with pytest.raises(ValueError):cohort.verify_source_owner(None)
    record('ten_slot_journal',dict(slots=[dict(market=s.market,stage=s.stage) for s in plan.slots],
        exact_model=SOL_HIGH_V1.model_request(),persistent_no_refill=True,synthetic_acceptance_only=True,
        onboarding_slots=0,actual_signed_in_CLI_started=0))

def test_sol_high_bridge_timeout_and_schema_fail_are_one_attempt(tmp_path):
    from app.services.production_b2_execution import ModelTransportError
    results=[]
    for failure in ('timeout','schema'):
        calls=[]
        class Model:
            execution_profile=SOL_HIGH_V1
            async def request(self,*args,**kwargs):
                calls.append(kwargs)
                if failure=='timeout':raise TimeoutError('SYNTHETIC')
                return b'{"value":"wrong"}'
        session=SimpleNamespace(market='us',accept=lambda *a:pytest.fail('must not accept'))
        bridge=SimpleNamespace(_native_owner_parents={},execution_profile=SOL_HIGH_V1,model=Model())
        request=dict(batch=1,subjects=[],payload=dict(prompt='SYNTHETIC',input={},response_schema=dict(
            type='object',properties={'value':{'type':'integer'}},required=['value'])))
        with pytest.raises(ModelTransportError):
            asyncio.run(ProductionRuntimeBridgeV1._invoke(bridge,session,'MARKET',request,tmp_path/failure))
        assert len(calls)==1 and not (tmp_path/failure/'attempt-2').exists()
        assert calls[0]['model']=='gpt-6.1-sol' and calls[0]['effort']=='high'
        results.append(dict(failure=failure,fake_attempts=1,repair=0))
    record('bridge_no_retry',dict(cases=results,real_CLI_started=0))
