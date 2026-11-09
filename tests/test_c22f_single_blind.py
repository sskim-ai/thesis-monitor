"""Four changed-boundary tests; subprocesses below are mocks, never model calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest
from scripts import dated_economic_model as runner
from app.services.dated_research_model import (AXES,build_prompt,encoded,load_bound_view,validate_output)

ROOT=Path(os.environ['C22F_TASK_ROOT'])


def scope():return json.loads((ROOT/'SCOPE.json').read_bytes())


def test_new_approval_and_real_runtime_are_required():
    original=scope()
    for field,bad in [('user_approved',False),('task','C22E'),('native_retry_policy','ZERO'),('wrapper_retries',1)]:
        value=deepcopy(original);value[field]=bad
        with pytest.raises(ValueError):runner.validate_native_retry_configuration(value,binary_sha=runner.CLI_SHA,version='codex-cli 0.167.0',signed_in=True)
    with pytest.raises(ValueError):runner.validate_native_retry_configuration(original,binary_sha='0'*64,version='codex-cli 0.167.0',signed_in=True)
    result=runner.validate_native_retry_configuration(original,binary_sha=runner.CLI_SHA,version='codex-cli 0.167.0',signed_in=True)
    assert result['native_HTTP_attempts']=='UNKNOWN' and result['native_stream_reconnects']=='UNKNOWN'


def test_approved_single_subject_blind_only_native_defaults():
    policy=scope();runner.validate_execution_request(['005930'],policy)
    for request in (['MU'],['005930','MU'],[],['005930','005930']):
        with pytest.raises(ValueError):runner.validate_execution_request(request,policy)
    bad=deepcopy(policy);bad['allowed_stages']=['BLIND','ADJUDICATION']
    with pytest.raises(ValueError):runner.validate_native_retry_configuration(bad,binary_sha=runner.CLI_SHA,version='codex-cli 0.167.0',signed_in=True)
    argv=runner.command(Path('/existing/codex'),root=Path('/private'),schema=Path('/schema'),output=Path('/output'))
    assert 'gpt-6.1-sol' in argv and 'read-only' in argv and 'model_reasoning_effort="high"' in argv
    assert not any('model_providers.' in a or 'max_retries' in a for a in argv)


def test_mock_success_error_timeout_all_consume_once(tmp_path,monkeypatch):
    actual_digest=runner.digest
    monkeypatch.setattr(runner,'digest',lambda b:runner.CLI_SHA if b==b'fake-binary' else actual_digest(b))
    monkeypatch.setattr(runner,'check_launcher_state',lambda:dict(competing_model_processes=[]))
    monkeypatch.setattr(runner.os,'killpg',lambda *a:None)
    accepted={k:dict(state='SYNTHETIC',confidence='LOW') for k in ('overall','newbuyer','holder_virtual')}
    accepted['citations']=[{},{}]
    monkeypatch.setattr(runner,'validate_output',lambda *a,**k:accepted)
    binary=SimpleNamespace(read_bytes=lambda:b'fake-binary',__str__=lambda s:'/fake/codex')
    for mode in ('success','error','timeout'):
        root=tmp_path/mode;root.mkdir();out=root/'out';out.mkdir();calls=[]
        class FakeProcess:
            pid=999999
            returncode=0 if mode=='success' else 1
            def communicate(self,**kwargs):
                if mode=='timeout':raise subprocess.TimeoutExpired('synthetic',600)
            def wait(self,**kwargs):self.returncode=-15
        def spawn(argv,**kwargs):
            calls.append(argv)
            kwargs['stdout'].write(b'{"type":"turn.completed"}\n')
            Path(argv[argv.index('-o')+1]).write_bytes(b'{"synthetic":true}')
            return FakeProcess()
        args=dict(scope=scope(),scope_path=root/'SCOPE.json',binary=binary,view={'ticker':'005930'},
            binding=dict(source_zip_sha256='a'*64,original_sha256='b'*64,research_view_sha256='c'*64),
            prompt=b'only synthetic',schema={},catalog={},out=out,spawn=spawn)
        result=runner.run_one_blind(**args)
        assert len(calls)==1 and result['wrapper_retries']==0 and result['ADJ_started']==0 and result['MU_started']==0
        assert result['accepted'] is (mode=='success')
        with pytest.raises(ValueError,match='already_consumed'):runner.run_one_blind(**args)
        assert len(calls)==1


def test_real_bound_input_unchanged_and_bad_numeric_citation_rejected():
    archive=ROOT.parent/'20261109-c22d-v2/C22D_V2_ALL_DELIVERABLES.zip'
    view,binding=load_bound_view(archive,expected_zip_sha256=scope()['input_zip_sha256'],ticker='005930')
    prompt,schema,catalog=build_prompt(view,binding,stage='BLIND')
    old=json.loads((ROOT.parent/'20261109-c22e/live-once/C22E_MODEL_BINDING_PROOF.json').read_bytes())['005930']
    assert runner.digest(prompt)==old['prompt_sha256'] and runner.digest(encoded(schema))==old['schema_sha256']
    assert len(prompt)<=384*1024
    result=dict(ticker='005930',input_digest=binding['research_view_sha256'],as_of=view['as_of'],stage='BLIND',
        thesis_comparison='NOT_COMPARED_TO_REGISTERED_THESIS',what_changes_mind=['Synthetic falsification.'],
        uncertainty=['Synthetic test, not a live judgment.'],adjudication_change_reason='NOT_APPLICABLE_BLIND',
        NO_SEND=True,Strict_NATIVE_STAGE_READY=False,citations=[])
    states=('BUY','ATTRACTIVE','HOLDABLE','HYPOTHESIS','UNKNOWN','POTENTIAL_EXPOSURE','MIXED','MIXED')
    ref=next(iter(catalog['refs']))
    for axis,state in zip(AXES,states):result[axis]=dict(state=state,confidence='LOW',statement='SYNTHETIC ONLY',refs=[ref])
    for fact in catalog['numeric_facts'][:2]:
        result['overall']['refs'].append(fact['ref']);result['citations'].append(dict(axis='overall',**fact))
    validate_output(encoded(result),view=view,binding=binding,stage='BLIND',catalog=catalog)
    result['citations'][0]['period']='1900-01-01'
    with pytest.raises(ValueError,match='numeric_value_unit_period_basis_mismatch'):
        validate_output(encoded(result),view=view,binding=binding,stage='BLIND',catalog=catalog)
