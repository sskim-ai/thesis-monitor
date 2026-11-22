"""Only C37 finalization branches, using existing synthetic US15 fixtures."""
import asyncio
from collections import Counter
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

from app.services import research_no_send_run as research
from app.services.production_model_profile import SolHighWirePolicy
from app.services.unified_snapshot_contract import digest
from tests import test_per_ticker_b2_kis_session as full

OriginalTimer=research._StageTimer
original_stage=research.PreparedResearchBridge.stage
original_validate=research.validate_stage_v2


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args,**kwargs):
        raise AssertionError('C37 forbids real DB, network and model processes')
    for owner,name in ((socket.socket,'connect'),(socket.socket,'connect_ex'),(socket.socket,'sendto'),
        (sqlite3,'connect'),(subprocess,'Popen'),(asyncio,'create_subprocess_exec')):
        monkeypatch.setattr(owner,name,denied)


def controlled(patch, *, expiry=None, corruption=None, long_local=False):
    clock=[None];events=[]
    class Timer(OriginalTimer):
        def __init__(self,deadline,loop,campaign_end,retry_cap=0):
            if clock[0] is None:clock[0]=loop.time()
            if expiry==(deadline['stage'],'before'):clock[0]=campaign_end+1
            super().__init__(deadline,SimpleNamespace(time=lambda:clock[0]),campaign_end,retry_cap)
    async def stage(self,request,directory):
        name=request['stage'];value=await original_stage(self,request,directory)
        if long_local and name in ('VALIDATE','RENDER'):
            clock[0]+=630.296 if name=='VALIDATE' else 631.001
        if expiry==(name,'after'):clock[0]=research.current_stage_timer().campaign_end+1
        if name=='RENDER' and corruption:
            if corruption=='generation':
                value=value.model_copy(update={'generation_id':'SYNTHETIC_WRONG_GENERATION'})
            else:
                output=dict(value.output)
                output['messages']=[dict(row) for row in output['messages']]
                output['messages'][0]['text']+=' corrupted content'
                value=value.model_copy(update={'output':output})
        events.append(('returned',name))
        return value
    def validate(value,request):
        events.append(('external_validate',request['stage']))
        return original_validate(value,request)
    patch.setattr(research,'_StageTimer',Timer)
    patch.setattr(research.PreparedResearchBridge,'stage',stage)
    patch.setattr(research,'validate_stage_v2',validate)
    return events


def proof(path,value):
    (path/'c37-proof.json').write_text(json.dumps(value,indent=2))


def test_validate_630296_and_render_631001_keep_full15_and_external_checks(tmp_path,monkeypatch):
    events=controlled(monkeypatch,long_local=True)
    f=full.scenario(tmp_path,monkeypatch,{})
    assert f.result['status']==research.TERMINAL,f.result.get('error_chain')
    assert Counter(call['stage'] for call in f.calls)==dict(MARKET=1,CORE=5,A=5,B=5,B2=13)
    assert len(f.calls)==len(f.budget.accepted)==29 and f.budget.maximum==42 and f.budget.retry_used==0
    assert len(f.result['messages'])==15 and not f.result['normal_messages_sent']
    assert digest(f.result['messages'])==f.result['messages_sha256']
    assert all(r['status']=='PASS' for r in f.result['stage_receipts'])
    receipts={r['stage']:r for r in f.result['stage_receipts']}
    assert receipts['VALIDATE']['timing']['local_seconds']==630.296
    assert receipts['RENDER']['timing']['local_seconds']==631.001
    for name in ('VALIDATE','RENDER'):
        assert receipts[name]['deadline']['local_seconds'] is None
        assert events.index(('returned',name))<events.index(('external_validate',name))
        response=json.loads((f.cycle/name.lower()/'response.json').read_bytes())
        assert digest(response)==receipts[name]['response_sha256']
    value=json.loads((f.cycle/'validate/response.json').read_bytes())
    assert value['output']['content_sha256']==f.result['messages_sha256']
    assert SolHighWirePolicy().timeout_seconds==600
    proof(tmp_path,dict(synthetic=True,messages=15,logical_acceptances=29,model_maximum=f.budget.maximum,
        content_sha256=f.result['messages_sha256'],finalization_receipts=[receipts[n] for n in ('VALIDATE','RENDER')],
        external_validator_order=events,real_API_DB_model_calls=0))


def test_wrong_render_content_hash_and_generation_still_rejected(tmp_path,monkeypatch):
    results=[]
    for kind in ('content_hash','generation'):
        with monkeypatch.context() as patch:
            events=controlled(patch,corruption=kind,long_local=True)
            f=full.scenario(tmp_path/kind,patch,{})
            assert f.result['status']=='FAILED_NO_SEND' and 'messages' not in f.result
            assert f.result['first_failure']['stage']=='RENDER' and f.result['first_failure']['type']=='ValueError'
            assert ('external_validate','VALIDATE') in events and ('external_validate','RENDER') in events
            assert len(f.calls)==29 and f.budget.stopped and f.budget.retry_used==0
            assert (f.cycle/'render/response.json').exists()==(kind=='content_hash')
            results.append(dict(corruption=kind,first_failure=f.result['first_failure'],error_chain=f.result['error_chain']))
    proof(tmp_path,dict(synthetic=True,rejections=results,real_API_DB_model_calls=0))


def expired_cases(tmp_path,monkeypatch,when):
    results=[]
    for name in ('VALIDATE','RENDER'):
        with monkeypatch.context() as patch:
            events=controlled(patch,expiry=(name,when))
            f=full.scenario(tmp_path/name,patch,{})
            assert f.result['status']=='FAILED_NO_SEND' and 'messages' not in f.result
            assert f.result['first_failure']['stage']==name and f.result['first_failure']['type']=='TimeoutError'
            assert ('returned',name) in events if when=='after' else ('returned',name) not in events
            assert ('external_validate',name) not in events
            assert len(f.calls)==29 and f.budget.stopped and not (f.cycle/name.lower()/'response.json').exists()
            first=json.loads((f.cycle/'first-failure.json').read_bytes())
            assert first==f.result['first_failure']
            results.append(dict(stage=name,expiry=when,first_failure=first,error_chain=f.result['error_chain']))
    proof(tmp_path,dict(synthetic=True,expiry_cases=results,real_API_DB_model_calls=0))


def test_campaign_expiry_before_both_finalization_stages(tmp_path,monkeypatch):
    expired_cases(tmp_path,monkeypatch,'before')


def test_campaign_expiry_after_both_finalization_returns(tmp_path,monkeypatch):
    expired_cases(tmp_path,monkeypatch,'after')
