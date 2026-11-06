"""Synthetic execution records only; no real model acceptance is claimed."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import FrozenInstanceError
import time

import pytest

from app.services import vnext_balanced_stage_review as stage
from app.services import vnext_unified_judgment as engine
from app.services.vnext_execution_profile import ASTRA_XHIGH_V1,SOL_HIGH_V1,ExecutionProfile,require_profile
from app.services.vnext_research_store import digest
from test_vnext_axis_evidence_roles import setup
from test_vnext_balanced_stage_review import MemoryController


def arguments(a, controller, *, name='BLIND',prior=None,version=stage.UNIFIED_AI_V3_SOL_HIGH):
    owner,economic,registry,packet,value=a
    def invoke(request,text,deadline):
        output=deepcopy(value)
        if name=='ADJUDICATION':output['adjudication_changes']='Same supplied facts were independently reconsidered.'
        checked=engine.validate_and_render(output,packet,registry=registry,timing_owner=owner,economic_loader=lambda:economic)
        now=time.time()
        record=dict(stage=name,status='VALIDATED',exit=0,attempt=1,retry=0,
            runtime=dict(verified=True,session='SYNTHETIC_SOL_'+name),
            model=request['model'],effort=request['effort'],packet_sha=digest(packet),
            prompt_sha=digest(text.encode()),schema_sha=digest(stage.output_schema(packet,version)),
            output_sha=digest(output),started=now,ended=now,deadline=deadline,
            stage_contract=request['contract'],prompt_version=version,invocation_id=request['invocation_id'],
            request_sha=digest(request),approved_request_sha=digest(request))
        if 'execution_profile' in request:record['execution_profile']=request['execution_profile']
        return dict(output=output,validation=checked,execution=record)
    return dict(invocation_id='C10R_SYNTHETIC_'+name,account='SYNTHETIC_C10R',packet=packet,
        stage=name,version=version,knowledge={},registry=registry,source_loader=lambda:deepcopy(packet),
        approval=lambda request:True,account_lease=nullcontext,invoke=invoke,prior=prior,
        timing_owner=owner,economic_loader=lambda:economic)


def test_sol_two_stage_original_owner_and_provenance(monkeypatch):
    from app.services.vnext_unified_dispatch import consume
    a=setup(monkeypatch);controller=MemoryController();controller.execution_profile=SOL_HIGH_V1
    # Only the dispatch storage environment is synthetic; all stage, citation,
    # source and economic validators above are the originals.
    from types import SimpleNamespace
    controller.config=SimpleNamespace(environment='test',mode='write')
    blind=controller.run_stage(**arguments(a,controller))
    adj=controller.run_stage(**arguments(a,controller,name='ADJUDICATION',prior=blind))
    owner=stage.StageReviewOwner(blind,adj,enabled=True)
    receipt=owner.issue()
    assert receipt['execution_profile']==SOL_HIGH_V1.contract
    assert receipt['model']=='gpt-6.1-sol' and receipt['effort']=='high'
    assert owner.consume(receipt,packet=a[3])['decision']['model_output']['overall']['stance']=='BUY'
    assert not receipt['send'] and not receipt['strict_B2']


def test_sol_does_not_mutate_original_schema_or_legacy_request(monkeypatch):
    a=setup(monkeypatch);packet=a[3]
    params=dict(invocation_id='TEST',account='TEST',packet=packet,stage='BLIND',knowledge={},registry=a[2],prior=None)
    old,_=stage._stage_request(**params,version=stage.UNIFIED_AI_V3_CITATION)
    new,text=stage._stage_request(**params,version=stage.UNIFIED_AI_V3_SOL_HIGH)
    assert (old['model'],old['effort'])==('gpt-6-astra','xhigh')
    assert 'execution_profile' not in old
    assert new['execution_profile']==SOL_HIGH_V1.contract
    assert new['schema_sha']==old['schema_sha'] and new['prompt_sha']!=old['prompt_sha']
    assert new['contract']!=old['contract'] and 'gpt-6.1-sol/high' in text


@pytest.mark.parametrize('change',['model','effort','profile','retry','prompt','source'])
def test_cannot_relabel_old_or_changed_execution(monkeypatch,change):
    a=setup(monkeypatch);controller=MemoryController();controller.execution_profile=SOL_HIGH_V1
    kw=arguments(a,controller);invoke=kw['invoke']
    def bad(*args):
        record=invoke(*args);e=record['execution']
        key,value={'model':('model','gpt-6-astra'),'effort':('effort','xhigh'),
            'profile':('execution_profile',ASTRA_XHIGH_V1.contract),'retry':('retry',1),
            'prompt':('prompt_sha','f'*64),'source':('packet_sha','f'*64)}[change]
        e[key]=value
        return record
    kw['invoke']=bad
    with pytest.raises(ValueError):controller.run_stage(**kw)
    with pytest.raises(ValueError,match='already_attempted_no_retry'):controller.run_stage(**kw)


def test_sol_controller_cannot_fallback_or_mix_prior(monkeypatch):
    a=setup(monkeypatch);controller=MemoryController()
    with pytest.raises(ValueError,match='controller_profile_mismatch'):
        controller.run_stage(**arguments(a,controller))
    controller.execution_profile=SOL_HIGH_V1
    blind=controller.run_stage(**arguments(a,controller))
    with pytest.raises(ValueError,match='VERSION_MISMATCH_PRECALL'):
        controller.run_stage(**arguments(a,controller,name='ADJUDICATION',prior=blind,version=stage.UNIFIED_AI_V3_CITATION))


def test_profile_is_fixed_and_unknown_model_rejected():
    with pytest.raises(FrozenInstanceError):SOL_HIGH_V1.effort='medium'
    with pytest.raises(ValueError):require_profile(ExecutionProfile(SOL_HIGH_V1.contract,'gpt-6-astra','high'))
    with pytest.raises(ValueError):require_profile(dict(model='gpt-6.1-sol',effort='high'))
