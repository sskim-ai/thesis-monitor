"""Seven changed boundaries only. Clocks/Source/CLI are synthetic; live I/O is denied."""
import ast
import asyncio
import fcntl
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

from app.services import research_no_send_run as research, model_timeout_retry as retry
from app.services.model_invocation_journal import ModelInvocationJournal, read_invocation_journal
from app.services.unified_snapshot_contract import digest
from tests import test_c22bf_timeout as old, test_per_ticker_b2_kis_session as full


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C33 forbids live DB/network/model processes')
    popen=subprocess.Popen;root=str(Path(__file__).resolve().parents[1])
    def read_only_git(args,*more,**kwargs):
        if (isinstance(args,list) and len(args)==5 and args[:4]==['git','-C',root,'show']
                and args[4].startswith('6b63fe01871bc00c26ca92247ba6336effeb84b4:app/services/')):
            return popen(args,*more,**kwargs)
        return denied(args,*more,**kwargs)
    for owner,name in ((socket.socket,'connect'),(socket.socket,'connect_ex'),(socket.socket,'sendto'),
                       (sqlite3,'connect'),(asyncio,'create_subprocess_exec')):
        monkeypatch.setattr(owner,name,denied)
    monkeypatch.setattr(subprocess,'Popen',read_only_git)


def bound(stage, calls):
    plan=SimpleNamespace(slots=[SimpleNamespace(stage=stage)]*calls,validate=lambda:None)
    return research._split_stage_deadline(research.stage_deadline(plan,stage),600)


def test_market_local_over_600_one_24543_worker_and_campaign_cap():
    async def run():
        clock=[asyncio.get_running_loop().time()]
        timer=research._StageTimer(bound('MARKET',1),SimpleNamespace(time=lambda:clock[0]),clock[0]+5000)
        async with timer.timeout:
            assert timer.deadline['local_seconds'] is None and timer.timeout.when()==timer.campaign_end
            clock[0]+=700
            timer.check();timer.switch('worker')
            assert timer.timeout.when()==clock[0]+630
            clock[0]+=24.543;timer.switch('local')
            assert timer.timeout.when()==timer.campaign_end
            clock[0]+=100;timer.check()
        receipt=timer.receipt()
        assert receipt['local_seconds']==800 and receipt['worker_seconds']==24.543 and receipt['worker_windows']==1
    asyncio.run(run())


def test_all_five_model_stages_have_no_local_cumulative_limit():
    async def run():
        for stage in sorted(research.MODEL_STAGES):
            calls=1 if stage=='MARKET' else 5
            clock=[asyncio.get_running_loop().time()]
            timer=research._StageTimer(bound(stage,calls),SimpleNamespace(time=lambda:clock[0]),clock[0]+10000)
            async with timer.timeout:
                for _ in range(calls):
                    clock[0]+=650/calls;timer.check();timer.switch('worker')
                    clock[0]+=10;timer.switch('local')
                    assert timer.timeout.when()==timer.campaign_end
            assert timer.receipt()['local_seconds']==650 and timer.receipt()['worker_windows']==calls
    asyncio.run(run())


def test_c32_b2_6096_before_rxrx_now_completes_13_and_synthetic_15(tmp_path,monkeypatch):
    original=research._StageTimer;offset=[0.0];before_rxrx=[]
    class ShiftedTimer(original):
        def __init__(self,deadline,loop,campaign_end,retry_cap=0):
            super().__init__(deadline,SimpleNamespace(time=lambda:loop.time()+offset[0]),campaign_end,retry_cap)
    monkeypatch.setattr(research,'_StageTimer',ShiftedTimer)
    transport=old.transport
    def wrapped(*args):
        model=transport(*args);request=model.request
        async def invoke(payload,**kwargs):
            timer=research.current_stage_timer()
            if kwargs['stage']=='B2':
                ticker=kwargs.get('panel') or kwargs['slot_scope']['subjects'][0]
                if ticker=='RXRX':
                    offset[0]+=609.6-timer.receipt()['local_seconds']
                    before_rxrx.append(timer.receipt()['local_seconds'])
                elif before_rxrx:
                    offset[0]+=30
            return await request(payload,**kwargs)
        model.request=invoke
        return model
    monkeypatch.setattr(old,'transport',wrapped)
    f=full.scenario(tmp_path,monkeypatch,{})
    assert f.result['status']=='RENDER_VERIFIED_NO_SEND',f.result.get('error_chain')
    assert before_rxrx==[609.6] and len(f.result['messages'])==15
    assert len(f.calls)==f.budget.physical_calls==f.budget.run_ledger.state()['model_total']==29
    assert len(f.budget.accepted)==29 and f.budget.retry_used==0 and f.budget.run_ledger.state()['http_total']==0
    b2=next(s for s in f.result['stage_receipts'] if s['stage']=='B2')
    assert b2['timing']['local_seconds']>600 and b2['timing']['worker_windows']==13
    assert b2['deadline']['local_seconds'] is None
    assert [r['stage'] for r in f.result['stage_receipts']][-2:]==['VALIDATE','RENDER']
    assert all(r['status']=='PASS' for r in f.result['stage_receipts'])
    assert next(m for m in f.result['messages'] if m['message_id']=='SKHY')['decision_mode']=='UNKNOWN_LIMIT'
    cold=retry.read_no_send_partition(f.cycle,plan=f.plan,invocation_journal=f.budget.journal.path)
    assert cold['count']==15 and cold['physical_attempts']==29


def test_600_cli_timeout_market_b2_retry_42_and_duplicate_acceptance_unchanged(tmp_path,monkeypatch):
    from app.services import official_codex_production_executor as executor
    from app.services.official_codex_shadow_transport_service import OfficialShadowError
    from app.services.production_model_profile import SolHighWirePolicy
    from app.services.model_execution_plan import compile_model_plan
    from app.services.unified_stock_acquisition import UNIVERSE
    from dataclasses import replace
    seconds=iter((0.0,600.1));calls=[];reaped=[]
    class CLI:
        returncode=None
        def __init__(self,*args,**kwargs):self.stdout=kwargs['stdout']
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def communicate(self,prompt,timeout):
            calls.append(timeout);self.stdout.write(b'{"type":"thread.started"}\n{"type":"turn.started"}\n');self.stdout.flush()
            raise subprocess.TimeoutExpired('synthetic CLI',timeout)
        def poll(self):return self.returncode
        def kill(self):self.returncode=-9
        def wait(self):reaped.append(True);return self.returncode
    monkeypatch.setattr(executor.subprocess,'Popen',CLI);monkeypatch.setattr(executor,'monotonic',lambda:next(seconds))
    inputs=tmp_path/'approved-input';inputs.mkdir()
    request=SimpleNamespace(binding=SimpleNamespace(version='SYNTHETIC',executable_sha256=digest('cli')),
        execution_policy=SolHighWirePolicy())
    with (tmp_path/'events.jsonl').open('xb') as out,(tmp_path/'stderr').open('xb') as err:
        with pytest.raises(OfficialShadowError,match='TRANSPORT_TIMEOUT'):
            executor._run_observed_market(['cli','--sandbox','read-only'],cwd=inputs,prompt=b'public',stdout=out,
                stderr=err,timeout=600,options={},receipt={'invocation_identity_sha256':digest('request')},request=request)
    assert calls==[600] and reaped and json.loads((tmp_path/'market-cli-exit.json').read_bytes())['timed_out']
    base=old.listed_plan(UNIVERSE['us'])
    plan=compile_model_plan(replace(base.cohort,limitation_subjects=('SKHY',)),topology='CANONICAL_PRODUCTION')
    binding=retry.b2_retry_binding(plan)
    journal=ModelInvocationJournal(tmp_path/'journal.jsonl',plan_sha256=plan.sha256,maximum=42,b2_retry_policy=binding)
    b2_retries=0
    for i,slot in enumerate(plan.slots):
        journal.transact('BIND',slot_id=slot.slot_id,scope=dict(slot_id=slot.slot_id,stage=slot.stage,subjects=list(slot.subjects),dependency_outputs={}))
        a=old.attempt(i*10+1);journal.transact('CONSUME',slot_id=slot.slot_id,attempt=a)
        if slot.stage=='MARKET' or slot.stage=='B2' and b2_retries<12:
            journal.transact('TIMEOUT_CONFIRMED',slot_id=slot.slot_id,proof=old.proof(a))
            a=old.attempt(i*10+2,2);journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=a)
            b2_retries+=slot.stage=='B2'
            with pytest.raises(ValueError):journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=old.attempt(i*10+3,3))
        elif slot.stage=='B2':
            journal.transact('TIMEOUT_CONFIRMED',slot_id=slot.slot_id,proof=old.proof(a))
            with pytest.raises(ValueError):journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=old.attempt(i*10+2,2))
            break
        journal.transact('ACCEPT',slot_id=slot.slot_id,attempt_id=a['attempt_id'],output_sha256=digest(i))
        with pytest.raises(ValueError):journal.transact('ACCEPT',slot_id=slot.slot_id,attempt_id=a['attempt_id'],output_sha256=digest('again'))
    assert read_invocation_journal(journal.path.read_bytes())['physical_calls']==42


def test_campaign_expiry_before_worker_during_worker_and_awaited_local_releases_lock(tmp_path,monkeypatch):
    original_timer=research._StageTimer;original_worker=old.FixtureWorker
    for phase in ('before','worker','local'):
        with monkeypatch.context() as patch:
            killed=[];reaped=[]
            class ExpiringTimer(original_timer):
                def __init__(self,deadline,loop,campaign_end,retry_cap=0):
                    super().__init__(deadline,loop,min(campaign_end,loop.time()+(-1 if phase=='before' else .1)),retry_cap)
            patch.setattr(research,'_StageTimer',ExpiringTimer)
            if phase=='local':
                async def local_block(*args):await asyncio.Future()
                patch.setattr(research.PreparedResearchBridge,'stage',local_block)
            if phase=='worker':
                class HangingWorker(original_worker):
                    def __init__(self,*args):
                        super().__init__(*args);self.returncode=None
                        patch.setattr(retry.os,'killpg',lambda pid,sig:killed.append(pid))
                    async def communicate(self,raw):await asyncio.Future()
                    async def wait(self):self.returncode=-9;reaped.append(self.pid);return self.returncode
                patch.setattr(old,'FixtureWorker',HangingWorker)
            f=full.scenario(tmp_path/phase,patch,{})
            assert f.result['status']=='FAILED_NO_SEND' and 'messages' not in f.result
            assert f.budget.stopped and f.budget.run_ledger.state()['state']=='STOPPED_NO_SEND'
            if phase=='worker':
                assert killed==reaped==[987654321] and f.budget.physical_calls==1
                exits=list(f.budget.journal.path.parents[2].glob('*/parent-exit.json'))
                assert len(exits)==1 and json.loads(exits[0].read_bytes())['child_reaped']
            else:assert f.budget.physical_calls==0
            with (f.cycle/'cycle.lock').open('a') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)


def test_validate_and_render_local_600_and_worker_630_guards_remain():
    async def run():
        for stage in ('VALIDATE','RENDER'):
            clock=[asyncio.get_running_loop().time()]
            timer=research._StageTimer(bound(stage,0),SimpleNamespace(time=lambda:clock[0]),clock[0]+10000)
            async with timer.timeout:
                assert timer.deadline['local_seconds']==600
                clock[0]+=600.1
                with pytest.raises(TimeoutError,match='research_local_deadline'):timer.check()
        clock=[asyncio.get_running_loop().time()]
        timer=research._StageTimer(bound('MARKET',1),SimpleNamespace(time=lambda:clock[0]),clock[0]+10000)
        async with timer.timeout:
            timer.switch('worker');clock[0]+=630.1
            with pytest.raises(TimeoutError,match='research_worker_deadline'):timer.check()
    asyncio.run(run())


def test_legacy_request_hashes_campaign_derivation_and_protected_kr_unchanged():
    root=Path(__file__).resolve().parents[1]
    # Read the existing local commit; no checkout/Source replay or remote I/O.
    parent=subprocess.check_output(['git','-C',str(root),'show','6b63fe01871bc00c26ca92247ba6336effeb84b4:app/services/research_no_send_run.py'])
    before=ast.parse(parent);after=ast.parse((root/'app/services/research_no_send_run.py').read_bytes())
    function=lambda tree,name:next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
    assert ast.dump(function(before,'stage_deadline'))==ast.dump(function(after,'stage_deadline'))
    assert ast.dump(function(before,'run_prepared_research'))==ast.dump(function(after,'run_prepared_research'))
    for name in ('request',):
        assign=lambda tree:next(n for n in ast.walk(function(tree,'_run')) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
        assert ast.dump(assign(before))==ast.dump(assign(after))
    for name in ('production_model_transport.py','model_timeout_retry.py','model_invocation_journal.py',
                 'production_model_profile.py','selected_run_lifecycle.py','model_execution_plan.py'):
        old_code=subprocess.check_output(['git','-C',str(root),'show','6b63fe01871bc00c26ca92247ba6336effeb84b4:app/services/'+name])
        assert old_code==(root/'app/services'/name).read_bytes()
    plan=SimpleNamespace(slots=[SimpleNamespace(stage='MARKET')],validate=lambda:None)
    assert research.stage_deadline(plan,'MARKET')['total_seconds']==630
    assert bound('B',5)['scope']=='MODEL_LOCAL_UNLIMITED_CAMPAIGN_AND_PER_CALL_CAPPED'
