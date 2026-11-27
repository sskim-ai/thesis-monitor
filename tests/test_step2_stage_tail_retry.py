"""STEP 2 scheduling reliability. All workers/values are synthetic, no finance/model/DB."""
import asyncio
from hashlib import sha256
from types import SimpleNamespace

import pytest

from app.services import model_timeout_retry as retry
from app.services import research_no_send_run as research
from app.services.model_execution_plan import ModelExecutionPlan
from app.services.model_invocation_journal import read_invocation_journal
from app.services.production_b2_execution import ModelTransportError, authorize_b2, execute_b2
from app.services.production_runtime_bridge import execute_stage_tail
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests import test_c41_combined_retry as fixture, test_c22bf_timeout as old
from tests.test_c41_combined_retry import offline
from tests.test_c59_all_stage_retry import admitted, STAGES
from tests.test_step2_quality_summary import _detail
from tests.test_production_b2_execution import request_and_auth, Transport, body


def tickers(market):
    return ('AAA','BBB','CCC','DDD','EEE') if market=='us' else tuple(f'{i:06d}' for i in range(1,6))


@pytest.mark.parametrize('market,failed_stage,recovers',[
    ('kr','CORE',False),('us','CORE',False),
    ('kr','A',False),('us','A',False),
    ('kr','B',False),('us','B',False),
    ('kr','B2',False),('us','B2',False),
    ('kr','B',True),('us','B2',True),
])
def test_real_two_ledgers_tail_order_dependency_partition(tmp_path,market,failed_stage,recovers):
    plan,budget,_=admitted(tmp_path,market,tickers(market),batch_local=True)
    assert ModelExecutionPlan.from_dict(plan.to_dict())==plan
    policy=budget.b2_retry_policy
    assert retry.stage_tail_retry(policy)
    root=next(s for s in plan.slots if s.stage==failed_stage)
    calls,scopes=[],{}
    async def issue(slot,again):
        row=fixture.payload_for(plan,slot)
        if not again:
            scopes[slot.slot_id]=budget.bind_stage(slot.stage,row)
        scope=scopes[slot.slot_id]
        attempt=old.attempt(len(calls)+1,2 if again else 1)
        calls.append((slot.slot_id,attempt['ordinal']))
        budget.consume(None,slot.stage,row['payload_sha256'],slot_scope=scope,attempt=attempt)
        if slot==root and (not again or not recovers):
            proof=old.proof(attempt)
            pending=budget.confirmed_timeout(slot.slot_id,proof)
            if not again:
                # A retry before the remaining first-pass batch calls is denied.
                assert not retry.initial_stage_done(policy,slot.stage,budget.used,budget.exhausted)
                with pytest.raises(ValueError):
                    budget.journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,
                        attempt=old.attempt(999,2))
                with pytest.raises(ValueError):
                    budget.run_ledger.before_model(plan,scope,attempt=old.attempt(999,2))
            exc=ModelTransportError('TRANSPORT_TIMEOUT')
            exc.slot_id,exc.confirmed_timeout,exc.deferred_retry_pending=slot.slot_id,proof,pending
            raise exc
        budget.record_acceptance(slot.slot_id,payload_sha256=row['payload_sha256'],
                                 output_sha256=digest(slot.slot_id))
        return slot.slot_id

    async def run():
        for stage in STAGES:
            skipped=retry.dependency_skips(policy,budget.exhausted)
            active=[s for s in plan.slots if s.stage==stage and s.slot_id not in skipped]
            start=len(calls)
            await execute_stage_tail([(s.slot_id,s) for s in active],issue,budget=budget)
            assert calls[start:]==[(s.slot_id,1) for s in active]+(
                [(root.slot_id,2)] if stage==failed_stage else [])
    asyncio.run(run())
    state=read_invocation_journal(budget.journal.path.read_bytes(),budget.journal.identity)
    exhausted=set() if recovers else {root.slot_id}
    skipped=retry.dependency_skips(policy,exhausted)
    assert state['exhausted']==exhausted
    assert set(state['accepted'])=={s.slot_id for s in plan.slots}-exhausted-skipped
    assert state['used']&skipped==set()
    assert state['physical_calls']==len(calls)==budget.run_ledger.state()['model_total']
    assert state['retry_used']==1 and state['physical_calls']<=budget.maximum
    omissions=retry.timeout_omissions(plan,exhausted,state['bound'],state['attempts'])
    assert set(omissions)==(set() if recovers else set(root.subjects))
    assert all(r['status']==failed_stage+'_UNISSUED_TIMEOUT' for r in omissions.values())
    b2={'rows':{},'unissued':omissions}
    for s in plan.slots:
        if s.stage=='B2' and s.slot_id in state['accepted']:
            t=s.subjects[0]
            b2['rows'][t]={'result':dict(status='PASS',ticker=t,
                request_sha256=state['bound'][s.slot_id]['payload_sha256'],
                attempts=[{'raw_sha256':state['accepted'][s.slot_id]}])}
    from app.services.monitoring_summary import summary_message
    from app.services.analysis_report_service import telegram_render_parts
    gen=plan.cohort.run_id
    subjects=plan.cohort.market_subjects[market]
    details=[_detail(t,gen) for t in subjects if t not in omissions]
    for m in details:
        m['text']='synthetic detail'
    summary=summary_message(market=market,generation=gen,subjects=subjects,
        messages=details,omitted=omissions,completed=plan.cohort.assessment_date,cutoff=plan.cohort.cutoff)
    messages=[dict(message_id='MARKET_'+market.upper(),generation_id=gen,text='synthetic market'),summary,*details]
    for m in messages:
        m.update(NO_SEND=True,telegram_parts=telegram_render_parts(m['text']))
    retry.verify_render_partition(messages=messages,subjects=subjects,slots=plan.slots,b2=b2,
        journal=state,accepted_content_sha256=digest(messages),plan=plan,include_summary=True)
    for t in omissions:
        assert t+' — '+failed_stage+' 타임아웃·분석 미완료' in summary['text']
    budget.run_ledger._event('RENDER_MARKET',market=market,result_sha256=digest(messages),
                             timeout_slots=sorted(exhausted))
    assert budget.run_ledger.state()['state']=='RENDERED_NO_SEND'


@pytest.mark.parametrize('market,stage',[('kr','B'),('us','B2')])
def test_original_worker_frame_and_retry_pins(tmp_path,monkeypatch,market,stage):
    plan,budget,runtime=admitted(tmp_path,market,tickers(market),batch_local=True)
    for i,s in enumerate(plan.slots):
        if STAGES.index(s.stage)>=STAGES.index(stage):
            continue
        row=fixture.payload_for(plan,s)
        scope=budget.bind_stage(s.stage,row)
        budget.consume(None,s.stage,row['payload_sha256'],slot_scope=scope,attempt=old.attempt(i+1))
        budget.record_acceptance(s.slot_id,payload_sha256=row['payload_sha256'],output_sha256=digest(s.slot_id))
    active=[s for s in plan.slots if s.stage==stage]
    recorded=[]
    model=fixture.transport(tmp_path,monkeypatch,budget,runtime,
        iter(['timeout']+['pass']*(len(active)-1)+['timeout']),recorded)
    scopes={}
    async def issue(slot,again):
        row=fixture.payload_for(plan,slot)
        if not again:
            scopes[slot.slot_id]=budget.bind_stage(stage,row)
        raw=await model.request(row['payload'],stage=stage,slot_scope=scopes[slot.slot_id],
            panel=slot.subjects[0] if stage=='B2' else None,model=SOL_HIGH_V1.model,
            effort='high',timeout=600,deferred_retry=again)
        budget.record_acceptance(slot.slot_id,payload_sha256=row['payload_sha256'],output_sha256=sha256(raw).hexdigest())
        return raw
    async def run():
        bound=research._split_stage_deadline(research.stage_deadline(plan,stage),600)
        timer=research._StageTimer(bound,asyncio.get_running_loop(),
            asyncio.get_running_loop().time()+16200,len(active))
        token=research._stage_timer.set(timer)
        try:
            async with timer.timeout:
                return await execute_stage_tail([(s.slot_id,s) for s in active],issue,budget=budget)
        finally:
            research._stage_timer.reset(token)
    accepted=asyncio.run(run())
    assert set(accepted)=={s.slot_id for s in active[1:]}
    assert [r['slot_scope']['slot_id'] for r in recorded]==[s.slot_id for s in active]+[active[0].slot_id]
    assert recorded[0]['ordinal']==1 and recorded[-1]['ordinal']==2
    for k in ('slot_scope','prompt_sha256','schema_sha256','model','effort','timeout'):
        assert recorded[0][k]==recorded[-1][k]
    assert budget.exhausted=={active[0].slot_id}


def test_unknown_transport_error_does_not_queue():
    seen=[]
    async def issue(item,again):
        seen.append((item,again))
        raise ModelTransportError('unclassified')
    with pytest.raises(ModelTransportError):
        asyncio.run(execute_stage_tail([('a','a'),('b','b')],issue,
            budget=SimpleNamespace(exhausted=set())))
    assert seen==[('a',False)]


def test_b2_retry_reuses_original_request_and_preserves_attempt_files(tmp_path):
    request,_,binding=request_and_auth()
    auth=authorize_b2(request,**binding,execution_profile=SOL_HIGH_V1)
    transport=Transport([ModelTransportError('TRANSPORT_TIMEOUT'),body(request)])
    with pytest.raises(ModelTransportError):
        asyncio.run(execute_b2(request,auth,current_binding=binding,transport=transport,directory=tmp_path))
    result=asyncio.run(execute_b2(request,auth,current_binding=binding,transport=transport,directory=tmp_path,
        deferred_retry=True))
    assert result['status']=='PASS'
    assert [r['ordinal'] for r in result['attempts']]==[1,2]
    assert transport.calls[0][0]==transport.calls[1][0]
    assert (tmp_path/'attempt-1'/'receipt.json').exists()
    assert (tmp_path/'attempt-2'/'response.raw').exists()
    with pytest.raises(ValueError):
        asyncio.run(execute_b2(request,auth,current_binding=binding,transport=transport,directory=tmp_path,
            deferred_retry=True))
    assert len(transport.calls)==2
