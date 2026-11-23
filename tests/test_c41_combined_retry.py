"""Changed retry boundaries only; preserved C40 messages are not re-rendered."""
import asyncio
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

from app.services import model_timeout_retry as retry, prospective_class_c_owner as registration
from app.services import research_no_send_run as research
from app.services.model_execution_plan import CohortSubject,FrozenCohort,compile_model_plan,verify_mixed_render
from app.services.model_invocation_journal import ModelInvocationJournal,read_invocation_journal
from app.services.production_b2_execution import ModelTransportError
from app.services.production_model_profile import SolHighCallBudget,SolHighWirePolicy
from app.services.production_model_transport import OfficialProductionModelTransport
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests import test_c22bf_timeout as old
from tests.test_c22aa_research_boundaries import req
from tests.test_c22y_sol_high_contract import qualify_fixture
from tests.test_official_codex_shadow_transport import invocation

POLICY=retry.B2_PER_TICKER_ONE_RETRY_V1
BASE=Path('/Users/sskim/Documents/Codex/2026-07-04/the')
C40=BASE/'maintenance/20261123-pr52-c40-kr-parity'
PROOFS=[]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args,**kwargs):
        raise AssertionError('C41 forbids network, operating DB and real subprocesses')
    for owner,name in ((socket.socket,'connect'),(socket.socket,'connect_ex'),(socket.socket,'sendto'),
                       (sqlite3,'connect'),(subprocess,'Popen'),(asyncio,'create_subprocess_exec')):
        monkeypatch.setattr(owner,name,denied)


@pytest.fixture(scope='session',autouse=True)
def save_proofs():
    yield
    if path:=os.environ.get('C41_TEST_PROOFS'):
        Path(path).write_text(json.dumps(dict(synthetic_only=True,real_HTTP_DB_models=0,cases=PROOFS),indent=2))


def plan_for(market,subjects=None):
    if market=='us':
        p=old.listed_plan(UNIVERSE['us'] if subjects is None else subjects,
                          run='SYNTHETIC_V8_US',source='source-one')
        return compile_model_plan(replace(p.cohort,limitation_subjects=('SKHY',) if subjects is None else ()),
                                  topology='CANONICAL_PRODUCTION')
    at='2026-11-11T00:00:00+00:00'
    subjects=UNIVERSE['kr'] if subjects is None else subjects
    cohort=FrozenCohort('SYNTHETIC_C40_KR','source-one','2026-11-11',at,at,
        tuple(CohortSubject('kr',t,'OFFLINE:'+t,at,digest(t)) for t in sorted(subjects)),
        (('kr',digest('test-owner')),),digest('scope'))
    return compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')


def admitted(folder,plan,maximum=None):
    market=next(iter(plan.cohort.market_subjects));binding=retry.b2_retry_binding(plan)
    maximum=binding['maximum']+1 if maximum is None else maximum
    now=datetime.now(timezone.utc)
    children={market:dict(generation=plan.cohort.source_generation,subjects=list(UNIVERSE[market]))}
    if market=='kr':children['us']=dict(generation='UNUSED',subjects=['IBM'])
    approval=registration.record_backend_approval(registration.ApprovalDecision(event_id='SYNTHETIC_C41',
        approved=True,user_message_sha256=digest('OFFLINE_NOT_A_LIVE_GRANT'),effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(hours=4,minutes=30),subjects=tuple(t for c in children.values() for t in c['subjects'])))
    ledger=SelectedRunLedger(path=folder/'campaign.jsonl',approval=approval,master_id='SYNTHETIC_C41',
        children=children,provider_caps={'kiwoom':1},max_http=1,max_models=maximum,
        database_identity=dict(path='SYNTHETIC_NO_DB',device=0,inode=0),staged_markets=True,
        runtime_cap=dict(endpoints={'fixture':[]}),wallclock_seconds_max=16200,
        timeout_retry_cap=1,timeout_retry_market=market,b2_retry_policy=POLICY)
    apply=ledger._apply
    def synthetic(state,event,value):
        if event=='OPEN':state.update(active_markets=[market],sources={market:digest('SYNTHETIC_SOURCE_ONLY')})
        return apply(state,event,value)
    ledger._apply=synthetic
    ledger._event('MODEL_PLAN',market=market,sha256=plan.sha256,slots=len(plan.slots),
        slot_ids=[s.slot_id for s in plan.slots],slot_stages=binding['slot_stages'],b2_retry_binding=binding)
    runtime=folder/'runtime'
    budget=SolHighCallBudget(plan=plan,approved_max_invocations=maximum,approved_plan_sha256=plan.sha256,
        journal_path=runtime/'invocation-ledger'/plan.cohort.run_id/'events.jsonl',run_ledger=ledger,
        timeout_retry_cap=1,b2_retry_policy=POLICY)
    return budget,runtime


def transport(folder,patch,budget,runtime,outcomes,recorded):
    binding=qualify_fixture(invocation.__wrapped__(folder,patch))
    patch.setattr(FrozenCohort,'verify_source_owner',lambda *a:None)
    patch.setattr(retry.os,'killpg',lambda *a:(_ for _ in ()).throw(ProcessLookupError()))
    async def factory(*args,**kwargs):
        return old.FixtureWorker(next(outcomes),recorded)
    model=OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(binding),default=str)),
        runtime_root=runtime,execution_profile=SOL_HIGH_V1,call_budget=budget,worker_factory=factory)
    model.bind_cycle(market=next(iter(budget.plan.cohort.market_subjects)),run_id=budget.plan.cohort.run_id)
    return model


def payload_for(plan,slot):
    row=req(plan,slot)
    row['payload']['prompt']+='\nFROZEN_CONTEXT:\n{}'
    row['payload_sha256']=digest(row['payload'])
    return row


def exercise(folder,patch,market,failures=None,*,stop_before=None,b2_raw=None):
    plan=plan_for(market);budget,runtime=admitted(folder,plan)
    failures=failures or {};sequence=[]
    for slot in plan.slots:
        key='MARKET' if slot.stage=='MARKET' else slot.subjects[0] if slot.stage=='B2' else slot.stage
        errors=failures.get(key,())
        sequence.extend(errors)
        if len(errors)<2:sequence.append(b2_raw if b2_raw is not None and slot.stage=='B2' else 'pass')
    calls=[];model=transport(folder,patch,budget,runtime,iter(sequence),calls)
    error=None
    async def run():
        nonlocal error
        end=asyncio.get_running_loop().time()+16200
        for stage in ('MARKET','CORE','A','B','B2'):
            if stage==stop_before:break
            deadline=research._split_stage_deadline(research.stage_deadline(plan,stage),600)
            allowance=1 if stage=='MARKET' else budget.retry_capacity if stage=='B2' else 0
            timer=research._StageTimer(deadline,asyncio.get_running_loop(),end,allowance)
            token=research._stage_timer.set(timer)
            try:
                async with timer.timeout:
                    for slot in (s for s in plan.slots if s.stage==stage):
                        row=payload_for(plan,slot);scope=budget.bind_stage(stage,row)
                        raw=await model.request(row['payload'],stage=stage,slot_scope=scope,
                            panel=slot.subjects[0] if stage=='B2' else None,
                            model=SOL_HIGH_V1.model,effort='high',timeout=600)
                        budget.record_acceptance(slot.slot_id,payload_sha256=row['payload_sha256'],output_sha256=sha256(raw).hexdigest())
            except Exception as exc:
                error=exc;budget.stop();break
            finally:research._stage_timer.reset(token)
    asyncio.run(run())
    ledger=budget.run_ledger.state();journal=read_invocation_journal(budget.journal.path.read_bytes(),budget.journal.identity)
    assert len(calls)==budget.physical_calls==ledger['model_total']==journal['physical_calls']
    assert ledger['http_total']==0 and journal['retry_used']==budget.retry_used
    PROOFS.append(dict(market=market,failures=failures,physical=len(calls),accepted=len(budget.accepted),
        maximum=budget.maximum,retries=budget.retry_used,error=type(error).__name__ if error else None,
        journal_sha256=sha256(budget.journal.path.read_bytes()).hexdigest(),real_HTTP_DB_models=0))
    return SimpleNamespace(plan=plan,budget=budget,calls=calls,error=error,journal=journal,model=model)


def smoke_preserved_messages(f,market):
    rows=json.loads((C40/'SYNTHETIC_RESULTS.json').read_bytes())['results']
    ref=next(r for r in rows if r['messages']==(9 if market=='kr' else 15) and r['status']==research.TERMINAL)
    root=Path(os.environ.get('C41_C40_BASELINE_ROOT','/private/tmp/tm-c40-final-20261123'))
    value=json.loads((root/ref['test']/ref['case']).read_bytes())
    assert digest(value['messages'])==ref['content_sha256']
    b2=dict(rows={s.subjects[0]:dict(result=dict(status='PASS',ticker=s.subjects[0],
        request_sha256=f.budget.bound[s.slot_id]['payload_sha256'],
        attempts=[dict(raw_sha256=f.budget.accepted[s.slot_id])])) for s in f.plan.slots if s.stage=='B2'})
    retry.verify_render_partition(messages=value['messages'],subjects=f.plan.cohort.market_subjects[market],
        slots=f.plan.slots,b2=b2,journal=f.journal,accepted_content_sha256=ref['content_sha256'],plan=f.plan)
    if market=='us':verify_mixed_render(f.plan,value['messages'],value['limitation_receipts'])
    PROOFS.append(dict(smoke='PRESERVED_C40_MESSAGES_AT_CHANGED_RETRY_ACCEPTANCE_BOUNDARY',market=market,
        count=len(value['messages']),content_sha256=ref['content_sha256'],renderer_rerun=False))


def test_actual_plan_caps_and_legacy_diagnostics_are_plan_derived():
    for market,base,b2,total in (('kr',18,8,27),('us',29,13,43)):
        plan=plan_for(market);binding=retry.b2_retry_binding(plan)
        assert retry.retry_policy_limits(POLICY,plan=plan)==(base,b2,base+b2)
        assert binding['maximum']+retry.market_timeout_retry_cap(binding,retry_cap=1,retry_market=market)==total
        assert all(len(s.subjects)==len(s.security_ids)==1 for s in plan.slots if s.stage=='B2')
        assert 'SKHY' not in binding['b2_slots'].values()
    for subjects in (('MU',),('GOOGL','MU'),('005930',)):
        plan=plan_for('kr' if subjects[0].isdigit() else 'us',subjects)
        base,b2,total=retry.retry_policy_limits(POLICY,plan=plan)
        assert base==len(plan.slots) and b2==len(subjects) and total==base+b2
    assert retry.retry_policy_limits(retry.B2_US2_DIAGNOSTIC_V1)==(6,2,8)
    assert retry.retry_policy_limits(retry.B2_SR5_DIAGNOSTIC_V1)==(11,4,15)
    for policy,subjects in ((retry.B2_US2_DIAGNOSTIC_V1,('GOOGL','MU')),
                            (retry.B2_SR5_DIAGNOSTIC_V1,('CRCL','HUT','SKHY','TSM','WULF'))):
        p=old.listed_plan(subjects)
        if 'SKHY' in subjects:p=compile_model_plan(replace(p.cohort,limitation_subjects=('SKHY',)),topology='CANONICAL_PRODUCTION')
        binding=retry.b2_retry_binding(p,policy)
        assert retry.market_timeout_retry_cap(binding)==0
        with pytest.raises(ValueError):retry.market_timeout_retry_cap(binding,retry_cap=1)


def test_insufficient_kr18_19_26_and_us42_fail_before_worker(tmp_path):
    for market,cap,required in (('kr',18,27),('kr',19,27),('kr',26,27),('us',42,43)):
        folder=tmp_path/f'{market}{cap}'
        with pytest.raises(ValueError,match='required='+str(required)):
            admitted(folder,plan_for(market),cap)
        events=[json.loads(r) for r in (folder/'campaign.jsonl').read_text().splitlines()]
        assert not any(r['event'] in ('MODEL_PLAN','INTENT') for r in events)


def test_caller_rejects_current_caps_before_source_db_or_runtime(tmp_path,monkeypatch):
    from app.jobs import unified_market_snapshot as job
    def denied(*args):raise AssertionError('budget refusal reached a runtime')
    monkeypatch.setattr(job,'_local_model_runtime',denied)
    for market,required in (('kr',27),('us',43)):
        config=SimpleNamespace(market=market,market_b2_timeout_retry=True,kr_market_timeout_retry=False)
        with pytest.raises(ValueError,match='required='+str(required)):
            asyncio.run(job._local_registered_cycle(config,tmp_path,'2026-11-23'))


def test_kr_normal_18_acceptances_no_retry_and_preserved9_boundary(tmp_path,monkeypatch):
    f=exercise(tmp_path,monkeypatch,'kr')
    assert f.error is None and len(f.calls)==len(f.budget.accepted)==18 and f.budget.retry_used==0
    smoke_preserved_messages(f,'kr')


def test_kr_market_one_b2_and_both_use_independent_reserves(tmp_path,monkeypatch):
    ticker=next(s.subjects[0] for s in plan_for('kr').slots if s.stage=='B2')
    for name,errors,count in (('market',{'MARKET':['timeout']},19),('b2',{ticker:['timeout']},19),
                              ('both',{'MARKET':['timeout'],ticker:['timeout']},20)):
        with monkeypatch.context() as patch:
            f=exercise(tmp_path/name,patch,'kr',errors)
            assert f.error is None and len(f.calls)==count and len(f.budget.accepted)==18
            assert f.budget.retry_used==count-18
            for slot in f.budget.attempts:
                attempts=f.budget.attempts[slot]
                assert len(attempts)<=2
                if len(attempts)==2:
                    assert attempts[0]['attempt_id']!=attempts[1]['attempt_id']
                    assert all(attempts[0][k]==attempts[1][k] for k in ('prompt_sha256','schema_sha256'))


def test_worst_case_kr27_us43_preserved_message_partition(tmp_path,monkeypatch):
    for market,count,accepted in (('kr',27,18),('us',43,29)):
        failures={s.subjects[0]:['timeout'] for s in plan_for(market).slots if s.stage=='B2'}
        failures['MARKET']=['timeout']
        with monkeypatch.context() as patch:
            f=exercise(tmp_path/market,patch,market,failures)
            assert f.error is None and len(f.calls)==count and len(f.budget.accepted)==accepted
            assert not f.budget.exhausted and f.budget.maximum==count
            assert len({c['request_id'] for c in f.calls})==count
            smoke_preserved_messages(f,market)


def test_second_timeout_stops_without_omission_or_third_attempt(tmp_path,monkeypatch):
    for market in ('kr','us'):
        ticker=next(s.subjects[0] for s in plan_for(market).slots if s.stage=='B2')
        for target in ('MARKET',ticker):
            with monkeypatch.context() as patch:
                f=exercise(tmp_path/market/target,patch,market,{target:['timeout','timeout']})
                assert isinstance(f.error,ModelTransportError) and f.budget.stopped
                calls=[r for r in f.calls if r['stage']=='MARKET' if target=='MARKET'] if target=='MARKET' else [
                    r for r in f.calls if r['stage']=='B2' and r['slot_scope']['subjects']==[target]]
                assert len(calls)==2 and not f.budget.exhausted
                assert f.budget.run_ledger.state()['state']=='STOPPED_NO_SEND'


def test_auth_nonconfirmed_core_timeout_and_unreaped_worker_do_not_retry(tmp_path,monkeypatch):
    for kind in ('auth','ambiguous','CORE'):
        with monkeypatch.context() as patch:
            errors={'CORE':['timeout']} if kind=='CORE' else {'MARKET':[kind]}
            f=exercise(tmp_path/kind,patch,'kr',errors)
            assert isinstance(f.error,ModelTransportError) and f.budget.retry_used==0
            assert len([r for r in f.calls if r['stage']==('CORE' if kind=='CORE' else 'MARKET')])==1
    with monkeypatch.context() as patch:
        actual=old.FixtureWorker.communicate
        async def extant(self,raw):
            value=await actual(self,raw);patch.setattr(retry.os,'killpg',lambda *a:None);return value
        patch.setattr(old.FixtureWorker,'communicate',extant)
        f=exercise(tmp_path/'unreaped',patch,'kr',{'MARKET':['timeout']})
        assert isinstance(f.error,ModelTransportError) and len(f.calls)==1 and f.budget.retry_used==0
    for kind in ('PROCESS_START_FAILED','WORKER_NONZERO'):
        with monkeypatch.context() as patch:
            actual=old.FixtureWorker.communicate
            async def rejected(self,raw):
                self.result='auth';value=await actual(self,raw)
                folder=Path(json.loads(raw)['directory'])
                receipt=json.loads((folder/'transport-receipt.json').read_bytes())
                receipt.update(error_code=kind,process_started=kind!='PROCESS_START_FAILED')
                (folder/'transport-receipt.json').write_text(json.dumps(receipt))
                if kind=='WORKER_NONZERO':self.returncode=2
                return value
            patch.setattr(old.FixtureWorker,'communicate',rejected)
            f=exercise(tmp_path/kind,patch,'kr')
            assert isinstance(f.error,ModelTransportError) and len(f.calls)==1 and f.budget.retry_used==0


def test_changed_scope_schema_prompt_duplicate_and_third_attempt_are_rejected(tmp_path):
    plan=plan_for('kr');budget,_=admitted(tmp_path,plan);row=payload_for(plan,plan.slots[0])
    for key,value in (('market','us'),('subjects',['OTHER']),('source_generation_id','OTHER'),('execution_generation_id','OTHER')):
        with pytest.raises(ValueError):budget.bind_stage('MARKET',dict(row,**{key:value}))
    scope=budget.bind_stage('MARKET',row);first=old.attempt(1)
    for key,value in (('cohort_sha256',digest('wrong')),('slot_id',digest('wrong')),('market','us'),
                      ('payload_sha256',digest('wrong')),('subjects',['OTHER']),('source_generation','OTHER')):
        with pytest.raises(ValueError):budget.consume(None,'MARKET',row['payload_sha256'],slot_scope=dict(scope,**{key:value}),attempt=first)
    budget.consume(None,'MARKET',row['payload_sha256'],slot_scope=scope,attempt=first)
    assert budget.confirmed_timeout(scope['slot_id'],old.proof(first))
    before=budget.journal.path.read_bytes()
    for change in ('prompt_sha256','schema_sha256'):
        second=dict(old.attempt(2,2),**{change:digest('changed')})
        with pytest.raises(ValueError):
            budget.journal.transact('RETRY_ATTEMPT',slot_id=scope['slot_id'],attempt=second)
        assert budget.journal.path.read_bytes()==before
    second=old.attempt(2,2)
    budget.consume(None,'MARKET',row['payload_sha256'],slot_scope=scope,attempt=second)
    for duplicate in (second,old.attempt(3,3)):
        with pytest.raises(ValueError):budget.consume(None,'MARKET',row['payload_sha256'],slot_scope=scope,attempt=duplicate)
    assert budget.physical_calls==budget.run_ledger.state()['model_total']==2


def test_combined_cold_identity_reaches_original_partition_and_timers_unchanged(tmp_path,monkeypatch):
    from app.services import research_request_storage as storage
    class AtPartition(Exception):pass
    for market in ('kr','us'):
        plan=plan_for(market);budget,_=admitted(tmp_path/market,plan)
        binding=dict(plan_sha256=plan.sha256,run_id=plan.cohort.run_id,source_generation=plan.cohort.source_generation,
            assessment_date=plan.cohort.assessment_date,message_ids=['MARKET_'+market.upper(),*plan.cohort.market_subjects[market]])
        outputs={};receipts=[];requests={};messages=[]
        for stage in research.RESEARCH_STAGES:
            request=dict(run_id=plan.cohort.run_id,snapshot=dict(child_binding=binding),inputs=deepcopy(outputs))
            output=dict(rows={}) if stage=='B2' else dict(messages=messages) if stage=='RENDER' else dict(content_sha256=digest(messages)) if stage=='VALIDATE' else {}
            response=dict(output=output)
            requests[stage]=(request,response);outputs[stage]=response
            receipts.append(dict(stage=stage,status='PASS',logical_request_sha256=digest('logical'),storage_record_sha256=digest('stored'),response_sha256=digest(response)))
        cycle=tmp_path/market/'cycle';cycle.mkdir()
        (cycle/'terminal.json').write_text(json.dumps(dict(status=research.TERMINAL,normal_messages_sent=False,
            failure_notifications_sent=False,child_binding=binding,stage_receipts=receipts,messages=[],messages_sha256=digest([]))))
        with monkeypatch.context() as patch:
            patch.setattr(storage,'load_stage_request',lambda path,**kw:requests[path.parent.name.upper()][0])
            patch.setattr(storage,'load_stage_response',lambda path,request:requests[path.parent.name.upper()][1])
            def reached(**kwargs):
                assert kwargs['plan']==plan and kwargs['subjects']==plan.cohort.market_subjects[market]
                raise AtPartition
            patch.setattr(retry,'verify_render_partition',reached)
            with pytest.raises(AtPartition):retry.read_no_send_partition(cycle,plan=plan,invocation_journal=budget.journal.path)
    baseline=json.loads((C40/'CODE_STATUS.json').read_bytes())['files']['app/services/research_no_send_run.py']['sha256']
    assert sha256(Path(research.__file__).read_bytes()).hexdigest()==baseline
    assert SolHighWirePolicy().timeout_seconds==600
    assert all(research._split_stage_deadline(research.stage_deadline(plan,s),600)['local_seconds'] is None for s in research.RESEARCH_STAGES)


def test_actual_b2_schema_and_semantic_rejection_consumer_has_no_retry(tmp_path,monkeypatch):
    from app.services.production_b2_execution import execute_b2,parse_authorization,SemanticReject
    from app.services.new_buyer_request_owner import provider_payload
    from tests.test_newbuyer_b2_v2 import outputs
    ref=next(r for r in json.loads((C40/'SYNTHETIC_RESULTS.json').read_bytes())['results'] if r['messages']==9)
    root=Path(os.environ.get('C41_C40_BASELINE_ROOT','/private/tmp/tm-c40-final-20261123'))
    cycle=(root/ref['test']/ref['case']).parent
    ticker=next(s.subjects[0] for s in plan_for('kr').slots if s.stage=='B2')
    request=json.loads((cycle/'b2'/ticker/'request.json').read_bytes())
    auth=parse_authorization(json.loads((cycle/'b2'/ticker/'authorization.json').read_bytes()),execution_profile=SOL_HIGH_V1)
    bad=next(r for r in outputs(request) if r['reason_class']=='VALUATION_NEUTRAL')
    bad['reason_evidence_refs']=['valuation:PER'];bad['valuation_context']['valuation_evidence_refs']=['valuation:FORWARD_PE']
    values={'form':b'not json','schema':b'{}','semantic':json.dumps({'new_buyer_shadow':bad}).encode()}
    current={k:getattr(auth,k) for k in ('generation_id','source_generation_id','source_envelope_sha256',
        'owner_sha256','core_sha256','pass_a_sha256','pass_b_sha256')}
    for kind,raw in values.items():
        with monkeypatch.context() as patch:
            f=exercise(tmp_path/kind,patch,'kr',stop_before='B2',b2_raw=raw)
            payload=provider_payload(request,expected_request_sha256=auth.request_sha256)
            f.budget.bind_stage('B2',dict(market='kr',batch=None,subjects=[ticker],payload=payload,
                payload_sha256=auth.request_sha256,execution_generation_id=f.plan.cohort.run_id,
                source_generation_id=f.plan.cohort.source_generation))
            async def run():
                timer=research._StageTimer(research._split_stage_deadline(research.stage_deadline(f.plan,'B2'),600),
                    asyncio.get_running_loop(),asyncio.get_running_loop().time()+16200,f.budget.retry_capacity)
                token=research._stage_timer.set(timer)
                try:
                    async with timer.timeout:
                        return await execute_b2(request,auth,current_binding=current,transport=f.model,directory=tmp_path/kind/'consumer')
                finally:research._stage_timer.reset(token)
            with pytest.raises(SemanticReject if kind=='semantic' else ModelTransportError):asyncio.run(run())
            attempts=[c for c in f.calls if c['stage']=='B2']
            assert len(attempts)==1 and f.budget.retry_used==0
            receipt=json.loads((tmp_path/kind/'consumer/attempt-1/receipt.json').read_bytes())
            assert receipt['classification']=={'form':'RESPONSE_FORM_FAILURE','schema':'PROVIDER_SCHEMA_FAILURE','semantic':'SEMANTIC_REJECT'}[kind]


def test_source_owner_and_combined_identity_drift_fail_before_dispatch(tmp_path,monkeypatch):
    plan=plan_for('kr');budget,runtime=admitted(tmp_path,plan)
    calls=[];model=transport(tmp_path,monkeypatch,budget,runtime,iter(['pass']),calls)
    row=payload_for(plan,plan.slots[0]);scope=budget.bind_stage('MARKET',row)
    def stale(*a):raise ValueError('SYNTHETIC_SOURCE_OWNER_NOT_CURRENT')
    monkeypatch.setattr(FrozenCohort,'verify_source_owner',stale)
    async def run():
        timer=research._StageTimer(research._split_stage_deadline(research.stage_deadline(plan,'MARKET'),600),
            asyncio.get_running_loop(),asyncio.get_running_loop().time()+16200,1)
        token=research._stage_timer.set(timer)
        try:
            async with timer.timeout:
                return await model.request(row['payload'],stage='MARKET',slot_scope=scope,model=SOL_HIGH_V1.model,effort='high',timeout=600)
        finally:research._stage_timer.reset(token)
    with pytest.raises(ValueError,match='SOURCE_OWNER_NOT_CURRENT'):asyncio.run(run())
    assert not calls and budget.physical_calls==budget.run_ledger.state()['model_total']==0
    with pytest.raises(ValueError):
        SolHighCallBudget(plan=plan,approved_max_invocations=27,approved_plan_sha256=plan.sha256,
            journal_path=tmp_path/'bad.jsonl',run_ledger=budget.run_ledger,timeout_retry_cap=0,b2_retry_policy=POLICY)
    assert budget.journal.identity['timeout_retry_cap']==1 and budget.journal.identity['b2_retry_policy']['maximum']==26
