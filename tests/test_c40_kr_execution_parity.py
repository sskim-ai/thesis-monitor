"""C40 changed boundaries only. Synthetic admission/outputs, no live I/O."""
import asyncio
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
import socket
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

from app.services import model_timeout_retry as retry, prospective_class_c_owner as registration
from app.services import research_no_send_run as research
from app.services.model_invocation_journal import ModelInvocationJournal, read_invocation_journal
from app.services.production_model_profile import SolHighCallBudget, SolHighWirePolicy
from app.services.production_model_transport import OfficialProductionModelTransport
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests import test_c22bf_timeout as old, test_v8_mixed_retry as mixed
from tests import test_per_ticker_b2_kis_session as us
from tests.test_c22aa_research_boundaries import req
from tests.test_c22y_sol_high_contract import qualify_fixture
from tests.test_official_codex_shadow_transport import invocation


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C40 forbids network, DB and real subprocesses')
    for owner, name in ((socket.socket,'connect'),(socket.socket,'connect_ex'),(socket.socket,'sendto'),
                        (sqlite3,'connect'),(subprocess,'Popen'),(asyncio,'create_subprocess_exec')):
        monkeypatch.setattr(owner,name,denied)


def kr_budget(folder, plan, cap=1, maximum=19):
    now = datetime.now(timezone.utc)
    approval = registration.record_backend_approval(registration.ApprovalDecision(
        event_id='SYNTHETIC_C40',approved=True,user_message_sha256=digest('SYNTHETIC_NOT_LIVE'),
        effective_at=now-timedelta(seconds=1),expires_at=now+timedelta(hours=4,minutes=30),
        subjects=(*UNIVERSE['kr'],'IBM')))
    ledger = SelectedRunLedger(path=folder/'campaign.jsonl',approval=approval,master_id='SYNTHETIC_C40',
        children=dict(kr=dict(generation=plan.cohort.source_generation,subjects=list(UNIVERSE['kr'])),
                      us=dict(generation='UNUSED_SOURCE',subjects=['IBM'])),
        provider_caps={'kiwoom':1},max_http=1,max_models=maximum,
        database_identity=dict(path='SYNTHETIC_NO_DB',device=0,inode=0),staged_markets=True,
        runtime_cap=dict(endpoints={'fixture':[]}),wallclock_seconds_max=16200,
        timeout_retry_cap=cap,timeout_retry_market='kr')
    original = ledger._apply
    def apply(state,event,value):
        if event=='OPEN':
            state.update(active_markets=['kr'],sources={'kr':digest('synthetic-owner')})
        return original(state,event,value)
    ledger._apply = apply
    ledger._event('MODEL_PLAN',market='kr',sha256=plan.sha256,slots=len(plan.slots),
        slot_ids=[s.slot_id for s in plan.slots],slot_stages={s.slot_id:s.stage for s in plan.slots})
    runtime = folder/'runtime'
    budget = SolHighCallBudget(plan=plan,approved_max_invocations=maximum,approved_plan_sha256=plan.sha256,
        journal_path=runtime/'invocation-ledger'/plan.cohort.run_id/'events.jsonl',run_ledger=ledger,
        timeout_retry_cap=cap)
    return budget,runtime


def kr_transport(folder, patch, budget, runtime, outcomes, recorded):
    from app.services.model_execution_plan import FrozenCohort
    binding = qualify_fixture(invocation.__wrapped__(folder,patch))
    patch.setattr(FrozenCohort,'verify_source_owner',lambda *a:None)
    async def factory(*args, **kwargs):
        return old.FixtureWorker(next(outcomes),recorded)
    model = OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(binding),default=str)),
        runtime_root=runtime,execution_profile=SOL_HIGH_V1,call_budget=budget,worker_factory=factory)
    model.bind_cycle(market='kr',run_id=budget.plan.cohort.run_id)
    return model


def scenario(folder, patch, errors=()):
    patch.setattr(old,'admitted_budget',kr_budget)
    def injected(folder, patch, budget, runtime, outcomes, recorded):
        stream = list(outcomes)
        stream[:1] = list(errors)+([] if len(errors)==2 else stream[:1])
        return kr_transport(folder,patch,budget,runtime,iter(stream),recorded)
    patch.setattr(old,'transport',injected)
    return mixed.fixture_run(folder,patch,cap=1,limited=False,market='kr')


def control(patch, *, long_local=False, corruption=None, expiry=False):
    original_timer, original_stage = research._StageTimer,research.PreparedResearchBridge.stage
    clock=[None]
    class Timer(original_timer):
        def __init__(self, deadline, loop, campaign_end, retry_cap=0):
            if clock[0] is None:
                clock[0]=loop.time()
            super().__init__(deadline,SimpleNamespace(time=lambda:clock[0]),campaign_end,retry_cap)
    async def stage(self, request, directory):
        result=await original_stage(self,request,directory)
        name=request['stage']
        if long_local:
            clock[0]+=631.001 if name=='RENDER' else 630.296 if name=='VALIDATE' else 700
        if name=='RENDER' and corruption:
            if corruption=='generation':
                result=result.model_copy(update={'generation_id':'WRONG_GENERATION'})
            else:
                out=dict(result.output,messages=[dict(m) for m in result.output['messages']])
                out['messages'][0]['text']+=' changed'
                result=result.model_copy(update={'output':out})
        if name=='VALIDATE' and expiry:
            clock[0]=research.current_stage_timer().campaign_end+1
        return result
    patch.setattr(research,'_StageTimer',Timer)
    patch.setattr(research.PreparedResearchBridge,'stage',stage)


def test_kr9_success_keeps_full_validation_render_and_unlimited_local_measurement(tmp_path,monkeypatch):
    control(monkeypatch,long_local=True)
    f=scenario(tmp_path,monkeypatch)
    assert f.result['status']==research.TERMINAL,f.result.get('error_chain')
    assert len(f.result['messages'])==9 and len(f.calls)==len(f.budget.accepted)==18
    assert f.budget.retry_used==0 and f.budget.maximum==19
    assert Counter(c['stage'] for c in f.calls)==dict(MARKET=1,CORE=3,A=3,B=3,B2=8)
    assert digest(f.result['messages'])==f.result['messages_sha256']
    assert all(m['NO_SEND'] for m in f.result['messages'])
    assert [r['stage'] for r in f.result['stage_receipts']]==list(research.RESEARCH_STAGES)
    for row in f.result['stage_receipts']:
        assert row['status']=='PASS' and row['deadline']['local_seconds'] is None
        assert row['timing']['local_seconds']>600
    assert len(f.budget.journal.transact('OPEN')['accepted'])==18
    assert f.budget.run_ledger.state()['model_total']==18


def test_kr_market_timeout_retries_same_input_once_through_worker_frame_and_timer(tmp_path,monkeypatch):
    f=scenario(tmp_path,monkeypatch,['timeout'])
    assert f.result['status']==research.TERMINAL,f.result.get('error_chain')
    assert len(f.result['messages'])==9 and len(f.calls)==f.budget.physical_calls==19
    assert f.budget.run_ledger.state()['model_total']==19 and len(f.budget.accepted)==18
    a,b=f.calls[:2]
    assert a['request_id']!=b['request_id'] and a['attempt']['attempt_id']!=b['attempt']['attempt_id']
    assert all(a[k]==b[k] for k in ('slot_scope','prompt_sha256','schema_sha256'))
    assert a['timeout_retry_market']==b['timeout_retry_market']=='kr' and f.budget.retry_used==1
    row=f.result['stage_receipts'][0]
    assert row['deadline']['market_timeout_retry_cap']==1 and row['timing']['worker_windows']==2
    assert not f.budget.exhausted and not f.budget.run_ledger.state()['pending']


def test_second_kr_market_timeout_preserves_first_error_and_stops_without_render(tmp_path,monkeypatch):
    f=scenario(tmp_path,monkeypatch,['timeout','timeout'])
    assert f.result['status']=='FAILED_NO_SEND',f.result
    assert len(f.calls)==2 and f.budget.stopped and f.budget.retry_used==1
    assert 'messages' not in f.result and not (f.cycle/'render/response.json').exists()
    assert f.result['first_failure']['stage']=='MARKET'
    assert json.loads((f.cycle/'first-failure.json').read_bytes())==f.result['first_failure']
    assert f.result['error_chain'][0]['type']=='ModelTransportError'
    assert len(f.budget.journal.transact('OPEN')['timeouts'][f.plan.slots[0].slot_id])==2


def test_kr_nonconfirmed_auth_and_semantic_failures_never_retry(tmp_path,monkeypatch):
    for kind in ('auth','ambiguous'):
        with monkeypatch.context() as patch:
            f=scenario(tmp_path/kind,patch,[kind,'timeout'])
            assert f.result['status']=='FAILED_NO_SEND' and len(f.calls)==1 and f.budget.retry_used==0
    with monkeypatch.context() as patch:
        async def reject(*args):
            raise ValueError('production_canonical_semantic_reject')
        patch.setattr(research.PreparedResearchBridge,'stage',reject)
        f=scenario(tmp_path/'semantic',patch)
        assert f.result['status']=='FAILED_NO_SEND' and len(f.calls)==0 and f.budget.retry_used==0


def test_input_or_worker_drift_blocks_retry_and_kr_b2_remains_ineligible(tmp_path,monkeypatch):
    # Exercise existing persistent journal identity/hash guards without any Source reissue.
    identity=dict(plan_sha256=digest('p'),maximum=19,retry_cap=1,retry_market='kr')
    for kind in ('prompt','scope','plan','B2'):
        journal=ModelInvocationJournal(tmp_path/kind/'events.jsonl',**identity)
        scope=dict(slot_id='s',market='kr',stage='B2' if kind=='B2' else 'MARKET',
                   dependency_outputs={},source_generation_id='one',execution_generation_id='one')
        journal.transact('BIND',slot_id='s',scope=scope)
        first=old.attempt(1)
        journal.transact('CONSUME',slot_id='s',attempt=first)
        journal.transact('TIMEOUT_CONFIRMED',slot_id='s',proof=old.proof(first))
        before=journal.path.read_bytes()
        with pytest.raises(ValueError):
            if kind=='scope':
                journal.transact('BIND',slot_id='s',scope=dict(scope,execution_generation_id='two'))
            elif kind=='plan':
                ModelInvocationJournal(journal.path,**dict(identity,plan_sha256=digest('changed'))).transact('OPEN')
            else:
                journal.transact('RETRY_ATTEMPT',slot_id='s',attempt=old.attempt(2,2,
                    digest('changed') if kind=='prompt' else None))
        assert journal.path.read_bytes()==before
    with monkeypatch.context() as patch:
        # An extant worker group makes the same timeout evidence ambiguous.
        def injected(folder, patch, budget, runtime, outcomes, recorded):
            model=kr_transport(folder,patch,budget,runtime,iter(['timeout']),recorded)
            patch.setattr(retry.os,'killpg',lambda *a:None)
            return model
        patch.setattr(old,'transport',injected)
        patch.setattr(old,'admitted_budget',kr_budget)
        # Test at the original fixture boundary; only the model Worker is synthetic.
        f=mixed.fixture_run(tmp_path/'unreaped',patch,cap=1,limited=False,market='kr')
        assert f.result['status']=='FAILED_NO_SEND' and len(f.calls)==1 and f.budget.retry_used==0
        assert f.result['error_chain'][0]['type']=='ModelTransportError'
        assert not f.budget.journal.transact('OPEN')['timeouts']


def test_18_base_slots_require_19_approved_for_extra_market_and_no_us_policy_on_kr(tmp_path,monkeypatch):
    captured=[]
    def insufficient(folder,plan,cap):
        captured.append(Counter(s.stage for s in plan.slots))
        return kr_budget(folder,plan,cap,maximum=18)
    monkeypatch.setattr(old,'admitted_budget',insufficient)
    with pytest.raises(ValueError,match='KR_MARKET_RETRY_BUDGET_APPROVAL_REQUIRED'):
        mixed.fixture_run(tmp_path,monkeypatch,cap=1,limited=False,market='kr')
    assert captured==[dict(MARKET=1,CORE=3,A=3,B=3,B2=8)]
    from app.services.model_timeout_retry import retry_policy_limits,B2_PER_TICKER_ONE_RETRY_V1
    assert retry_policy_limits(B2_PER_TICKER_ONE_RETRY_V1)[2]==42
    assert SolHighWirePolicy().timeout_seconds==600


def test_campaign_expiry_and_final_generation_content_guards_remain(tmp_path,monkeypatch):
    for kind in ('generation','content','expiry'):
        with monkeypatch.context() as patch:
            control(patch,long_local=True,corruption=kind if kind!='expiry' else None,expiry=kind=='expiry')
            f=scenario(tmp_path/kind,patch)
            assert f.result['status']=='FAILED_NO_SEND' and 'messages' not in f.result
            assert f.result['first_failure']['stage']==('VALIDATE' if kind=='expiry' else 'RENDER')
            assert f.budget.stopped and len(f.calls)==18


def test_us15_original_mixed_partition_and_us_retry_scope_still_pass(tmp_path,monkeypatch):
    f=us.scenario(tmp_path,monkeypatch,{})
    assert f.result['status']==research.TERMINAL,f.result.get('error_chain')
    assert len(f.result['messages'])==15 and len(f.calls)==29 and len(f.budget.accepted)==29
    assert f.budget.maximum==42 and f.budget.retry_market=='us'
    assert next(m for m in f.result['messages'] if m['message_id']=='SKHY')['decision_mode']=='UNKNOWN_LIMIT'
    assert 'timeout_retry_market' not in f.budget.journal.identity


def test_failed_registered_result_never_enters_success_recorder(monkeypatch):
    from app.jobs import unified_market_snapshot as job
    from app.services.production_source_backend import CanonicalProductionSourceBackend
    actions=[]
    original=dict(status='FAILED_NO_SEND',first_failure=dict(code='RESEARCH_STAGE_FAILED',stage='MARKET'),
                  error_chain=[dict(type='ModelTransportError',frames=[])])
    def forbidden(*a):
        raise AssertionError('failed result entered rendered_market')
    ledger=SimpleNamespace(bind_model_plan=lambda *a:actions.append('plan'),rendered_market=forbidden,
                           stop=lambda code:actions.append(code))
    child=SimpleNamespace(verify=lambda:None,market='kr',binding=lambda:{},
        plan=SimpleNamespace(sha256=digest('plan'),cohort=SimpleNamespace(cutoff='2026-11-23T07:00:00+00:00')),
        owner=SimpleNamespace(close=lambda:actions.append('owner_closed')))
    async def prepare(**kwargs):
        return child,{}
    async def run(*args):
        return original
    monkeypatch.setattr(CanonicalProductionSourceBackend,'prepare_registered',prepare)
    monkeypatch.setattr(job,'load_adapter',lambda *a,**kw:object())
    monkeypatch.setattr(job,'build_engine',lambda *a,**kw:SimpleNamespace(run=run))
    source=dict(run_ledger=ledger,frozen=dict(stock_plan=dict(implementation_sha=digest('code'))))
    value=asyncio.run(job.run_registered(None,source=source,model=dict(run_ledger=ledger),
                                        mode='LIVE_NO_SEND',record_market_terminal=True))
    assert value is original and actions==['plan','RESEARCH_STAGE_FAILED','owner_closed']


def test_worker_630_campaign_16200_and_source_cohort_generation_guards(tmp_path):
    from dataclasses import replace
    from app.services.model_execution_plan import CohortSubject,FrozenCohort,compile_model_plan
    at='2026-11-11T00:00:00+00:00'
    cohort=FrozenCohort('SYNTHETIC_C40','source-one','2026-11-11',at,at,
        tuple(CohortSubject('kr',t,'OFFLINE:'+t,at,digest(t)) for t in UNIVERSE['kr']),
        (('kr',digest('fixture')),),digest('scope'))
    plan=compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
    budget,_=kr_budget(tmp_path,plan)
    for key in ('source_generation_id','execution_generation_id'):
        changed=req(plan,plan.slots[0]);changed[key]='WRONG_GENERATION'
        with pytest.raises(ValueError,match='binding_or_upstream'):
            budget.bind_stage('MARKET',changed)
    budget.plan=replace(plan,cohort=replace(cohort,feature_scope_sha256=digest('changed-cohort')))
    with pytest.raises(ValueError,match='plan_changed_after_approval'):
        budget.bind_stage('MARKET',req(plan,plan.slots[0]))
    assert not budget.used and budget.run_ledger.state()['model_total']==0
    async def check():
        start=asyncio.get_running_loop().time()
        now=[start]
        bound=research._split_stage_deadline(research.stage_deadline(plan,'MARKET'),600)
        timer=research._StageTimer(bound,SimpleNamespace(time=lambda:now[0]),start+16200,1)
        async with timer.timeout:
            timer.switch('worker')
            assert timer.timeout.when()==start+630 and bound['per_call_seconds']==600
            now[0]=start+630
            with pytest.raises(TimeoutError,match='worker_deadline'):
                timer.check()
        now[0]=start
        timer=research._StageTimer(bound,SimpleNamespace(time=lambda:now[0]),start+16200,1)
        now[0]=start+16200
        with pytest.raises(TimeoutError,match='campaign_deadline'):
            timer.check()
    asyncio.run(check())
