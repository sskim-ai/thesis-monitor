"""C59 changed boundaries only; synthetic workers and temporary registration rows."""
import asyncio
from hashlib import sha256
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import model_timeout_retry as retry, prospective_class_c_owner as registration
from app.services import research_no_send_run as research, production_model_transport as wire
from app.services.model_invocation_journal import read_invocation_journal
from app.services.production_model_profile import SolHighCallBudget
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_registration import current_monitoring_subjects
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests import test_c41_combined_retry as fixture, test_c22bf_timeout as old
from tests.test_c41_combined_retry import offline

POLICY = retry.ALL_MODEL_STAGE_ONE_RETRY_V1
STAGES = ('MARKET','CORE','A','B','B2')


def admitted(folder, market, subjects, *, limited=False):
    from dataclasses import replace
    from app.services.model_execution_plan import compile_model_plan
    plan = old.listed_plan(subjects) if market=='us' else fixture.plan_for('kr',subjects)
    if limited:
        plan = compile_model_plan(replace(plan.cohort,limitation_subjects=(subjects[-1],)),
            topology='CANONICAL_PRODUCTION')
    ceiling = retry.roster_model_ceiling(subjects)
    maximum = 2*len(plan.slots)
    now = datetime.now(timezone.utc)
    children = {market: dict(generation=plan.cohort.source_generation, subjects=list(subjects))}
    approval = registration.record_backend_approval(registration.ApprovalDecision(
        event_id='SYNTHETIC_C59',approved=True,user_message_sha256=digest('OFFLINE'),
        effective_at=now-timedelta(seconds=1),expires_at=now+timedelta(hours=4,minutes=30),
        subjects=tuple(subjects)))
    ledger = SelectedRunLedger(path=folder/'campaign.jsonl',approval=approval,master_id='SYNTHETIC_C59',
        children=children,provider_caps={'kiwoom':1},max_http=1,max_models=ceiling,
        database_identity=dict(path='SYNTHETIC_NO_DB',device=0,inode=0),staged_markets=True,
        runtime_cap=dict(endpoints={'fixture':[]}),wallclock_seconds_max=16200,
        timeout_retry_market=market,b2_retry_policy=POLICY)
    apply = ledger._apply
    def synthetic(state,event,value):
        if event=='OPEN':
            state.update(active_markets=[market],sources={market:digest('SYNTHETIC_SOURCE_ONLY')})
        return apply(state,event,value)
    ledger._apply = synthetic
    binding = retry.b2_retry_binding(plan,POLICY)
    ledger._event('MODEL_PLAN',market=market,sha256=plan.sha256,slots=len(plan.slots),
        slot_ids=[s.slot_id for s in plan.slots],slot_stages=binding['slot_stages'],b2_retry_binding=binding)
    runtime=folder/'runtime'
    budget=SolHighCallBudget(plan=plan,approved_max_invocations=maximum,approved_plan_sha256=plan.sha256,
        journal_path=runtime/'invocation-ledger'/plan.cohort.run_id/'events.jsonl',run_ledger=ledger,b2_retry_policy=POLICY)
    return plan,budget,runtime


@pytest.mark.parametrize('market,subjects,limited', [
    ('us',('AAA','BBB','CCC','DDD'),False),
    ('kr',('000001','000002','000003','000004','000005'),False),
    ('us',('AAA','BBB','CCC','DDD'),True),
])
def test_every_slot_can_timeout_once_and_continue(tmp_path,monkeypatch,market,subjects,limited):
    plan,budget,runtime=admitted(tmp_path,market,subjects,limited=limited)
    base=len(plan.slots)
    assert budget.maximum==2*base and budget.retry_capacity==base
    assert retry.b2_retry_budget_bounds(budget.b2_retry_policy,retry_market=market)==(2*base,2*base)
    assert budget.run_ledger.identity['max_models']==retry.roster_model_ceiling(subjects)
    calls=[]
    model=fixture.transport(tmp_path,monkeypatch,budget,runtime,iter(['timeout','pass']*base),calls)
    async def run():
        end=asyncio.get_running_loop().time()+16200
        for stage in STAGES:
            bound=research._split_stage_deadline(research.stage_deadline(plan,stage),600)
            timer=research._StageTimer(bound,asyncio.get_running_loop(),end,bound['planned_calls'])
            token=research._stage_timer.set(timer)
            try:
                async with timer.timeout:
                    for slot in (s for s in plan.slots if s.stage==stage):
                        row=fixture.payload_for(plan,slot);scope=budget.bind_stage(stage,row)
                        raw=await model.request(row['payload'],stage=stage,slot_scope=scope,
                            panel=slot.subjects[0] if stage=='B2' else None,
                            model=SOL_HIGH_V1.model,effort='high',timeout=600)
                        budget.record_acceptance(slot.slot_id,payload_sha256=row['payload_sha256'],
                            output_sha256=sha256(raw).hexdigest())
                assert timer.calls==2*bound['planned_calls']
            finally:
                research._stage_timer.reset(token)
    asyncio.run(run())
    journal=read_invocation_journal(budget.journal.path.read_bytes(),budget.journal.identity)
    assert len(calls)==2*base==budget.physical_calls==journal['physical_calls']==budget.run_ledger.state()['model_total']
    assert len(budget.accepted)==base and budget.retry_used==journal['retry_used']==base
    assert not journal['exhausted'] and budget.run_ledger.state()['http_total']==0
    for first,second in zip(calls[::2],calls[1::2]):
        assert first['request_id']!=second['request_id']
        assert all(first[k]==second[k] for k in ('slot_scope','prompt_sha256','schema_sha256','model','effort','timeout'))
    slot=plan.slots[-1]
    with pytest.raises(ValueError):
        budget.journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=old.attempt(999,3))


@pytest.mark.parametrize('market,subjects', [('us',('AAA','BBB')),('kr',('000001','000002'))])
def test_second_b_timeout_does_not_start_third(tmp_path,market,subjects):
    plan,budget,_=admitted(tmp_path,market,subjects)
    for i,slot in enumerate(plan.slots):
        row=fixture.payload_for(plan,slot);scope=budget.bind_stage(slot.stage,row)
        first=old.attempt(2*i+1)
        budget.consume(None,slot.stage,row['payload_sha256'],slot_scope=scope,attempt=first)
        if slot.stage=='B':
            assert budget.confirmed_timeout(slot.slot_id,old.proof(first))
            second=old.attempt(2*i+2,2)
            budget.consume(None,slot.stage,row['payload_sha256'],slot_scope=scope,attempt=second)
            assert not budget.confirmed_timeout(slot.slot_id,old.proof(second))
            assert len(budget.attempts[slot.slot_id])==2
            budget.stop()
            assert budget.run_ledger.state()['state']=='STOPPED_NO_SEND'
            return
        budget.record_acceptance(slot.slot_id,payload_sha256=row['payload_sha256'],output_sha256=digest(i))
    pytest.fail('B not reached')


def test_roster_changes_and_scheduled_ceiling(tmp_path,monkeypatch):
    db=tmp_path/'fixture.db'
    conn=sqlite3.Connection(str(db))
    conn.executescript("""
        CREATE TABLE watchlistitem(ticker TEXT, exchange TEXT,active INTEGER,monitoring_requested INTEGER,onboarding_state TEXT);
        CREATE TABLE securitymaster(ticker TEXT,exchange TEXT);
        INSERT INTO watchlistitem VALUES ('AAA','NYSE',1,1,'ACTIVE'),('BBB','NASDAQ',0,1,'INACTIVE'),
            ('000001','KOSPI',1,1,'ACTIVE'),('000002','KOSDAQ',1,1,'PENDING_ONBOARDING'),
            ('000003','KRX',1,0,'ACTIVE');
    """)
    conn.commit()
    st=db.stat()
    real=sqlite3.Connection
    def connect(uri,**kwargs):
        assert uri==db.as_uri()+'?mode=ro' and kwargs['uri'] is True
        return real(uri,**kwargs)
    monkeypatch.setattr(sqlite3,'connect',connect)
    def roster(m):
        return current_monitoring_subjects(db,device=st.st_dev,inode=st.st_ino,market=m)
    config=SimpleNamespace(market='us',all_stage_timeout_retry=True,
        market_b2_timeout_retry=False,kr_market_timeout_retry=False)
    try:
        assert roster('us')==('AAA',) and roster('kr')==('000001',)
        assert job._local_model_cap(config,None,subjects=roster('us'))==10
        conn.execute("UPDATE watchlistitem SET active=1,onboarding_state='ACTIVE' WHERE ticker='BBB'")
        conn.commit()
        assert roster('us')==('AAA','BBB')
        assert job._local_model_cap(config,None,subjects=roster('us'))==12
        conn.execute("UPDATE watchlistitem SET monitoring_requested=0 WHERE ticker='AAA'")
        conn.commit()
        assert roster('us')==('BBB',)
        assert job._local_model_cap(config,None,subjects=roster('us'))==10
        for n in (8,14,15,20,30,60):
            assert job._local_model_cap(config,None,subjects=tuple(str(i) for i in range(n)))==2*(1+3*((n+2)//3)+n)
    finally:
        conn.close()


class AtConsumption(Exception):
    pass


def request_at_size(stage,length):
    prompt="" if stage=="B2" else "\nFROZEN_CONTEXT:\n{}"
    payload={"input":{},"prompt":prompt,"response_schema":{"type":"object"}}
    payload["prompt"]="a"*(length-len(wire.render_prompt(payload,stage)))+prompt
    assert len(wire.render_prompt(payload,stage))==length
    return payload


@pytest.mark.parametrize('stage',STAGES)
def test_kr_frozen_512_boundary_before_consumption(tmp_path,monkeypatch,stage):
    transport=wire.OfficialProductionModelTransport.__new__(wire.OfficialProductionModelTransport)
    monkeypatch.setattr(wire,'validate_binding',lambda *a,**k:None)
    scope={'slot_id':'scope','stage':stage,'market':'kr'}
    budget=Mock()
    budget.retry_enabled=False
    budget.timeout_retry_cap=0
    budget.maximum=36
    budget.resolve_scope.return_value=scope
    budget.consume.side_effect=AtConsumption
    transport.execution_profile,transport.call_budget=SOL_HIGH_V1,budget
    transport.cycle,transport.counts,transport.total=('kr','size-probe'),{},0
    transport.runtime_root,transport.secrets,transport.cohort_source_owner=tmp_path,(),object()
    transport.binding=SimpleNamespace(executable=tmp_path/'never-started')
    def submit(n):
        return asyncio.run(transport._request_once(request_at_size(stage,n),model=SOL_HIGH_V1.model,
            effort='high',timeout=600,stage=stage,panel='panel',slot_scope=scope))
    with pytest.raises(ValueError,match='sol_high_input_exceeds_512KiB'):
        submit(512*1024+1)
    budget.consume.assert_not_called()
    with pytest.raises(AtConsumption):
        submit(512*1024)
    assert budget.consume.call_count==1
    assert not list(tmp_path.iterdir())


def test_confirmed_timeout_accepts_both_512_and_keeps_schema_384(tmp_path,monkeypatch):
    folder=tmp_path/('run-'+'a'*32)
    inputs=folder/'approved-input'
    inputs.mkdir(parents=True)
    monkeypatch.setattr(retry.os,'killpg',Mock(side_effect=ProcessLookupError))
    (folder/'events.jsonl').write_text('{"type":"thread.started"}\n{"type":"turn.started"}\n')
    (folder/'market-cli-dispatch.json').write_text(json.dumps(dict(timeout_seconds=600,sandbox='read-only',
        model='gpt-6.1-sol',effort='high',dispatched_at='2026-01-01T00:00:00Z')))
    (folder/'market-cli-exit.json').write_text(json.dumps(dict(timed_out=True,process_started=True,
        event_scan_truncated=False,completed_turns=0,first_event='thread.started',last_event='turn.started',
        cli_returncode=-9,elapsed_seconds=600,ended_at='2026-01-01T00:10:00Z')))
    receipt=dict(status='FAIL',error_code='TRANSPORT_TIMEOUT',process_started=True,cli_returncode=-9)
    def proof(market,n,schema_size=2):
        prompt,schema=b'p'*n,b's'*schema_size
        (inputs/'prompt.txt').write_bytes(prompt)
        (inputs/'provider-wire-schema.json').write_bytes(schema)
        return retry.confirmed_timeout(folder,worker_pid=1234,worker_returncode=0,receipt=receipt,
            prompt_sha256=sha256(prompt).hexdigest(),schema_sha256=sha256(schema).hexdigest(),frozen_market=market)
    for market in ('us','kr'):
        assert proof(market,512*1024)
        assert proof(market,512*1024+1) is None
        assert proof(market,512*1024,384*1024+1) is None
    assert proof(None,384*1024+1) is None
