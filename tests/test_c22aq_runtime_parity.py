"""C22AQ changed boundaries only. No actual CLI, credentials or operating DB."""
import asyncio
from copy import deepcopy
from dataclasses import asdict,replace
from datetime import datetime,timezone
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import codex_runtime_binding as binding
from app.services import official_codex_production_executor as executor
from app.services.official_codex_shadow_transport_service import OfficialShadowError,file_sha256
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1


@pytest.fixture
def installed(tmp_path,monkeypatch):
    home=tmp_path/'home';auth=home/'.codex/auth.json';auth.parent.mkdir(parents=True)
    auth.write_text('SYNTHETIC_NO_CREDENTIAL');auth.chmod(0o600)
    exe=tmp_path/'release/bin/codex';exe.parent.mkdir(parents=True);exe.write_text('NOT_EXECUTABLE_MODEL');exe.chmod(0o700)
    (exe.parent.parent/'codex-package.json').write_text(json.dumps(dict(version='9.9.9-test',variant='codex',entrypoint='bin/codex')))
    display=tmp_path/'codex';display.symlink_to(exe)
    env=dict(HOME=str(home),CODEX_HOME=None,PATH='/usr/bin:/bin')
    inspection=dict(selected_executable=str(exe),selected_display_path=str(display),
        candidates=[dict(display_path=str(display),sha256=file_sha256(exe))],environment=env,
        signature=dict(returncode=0,requirement=binding.SIGNATURE_REQUIREMENT,network='OS_DENY_NETWORK',
            fixture_only=True),auth_reference=binding.auth_identity(auth),commands=dict(
            version=dict(returncode=0,inspection_started=True,version='codex-cli 9.9.9-test'),
            options=dict(returncode=0,inspection_started=True,flags={f:True for f in binding.FLAGS}),
            auth=dict(returncode=0,inspection_started=True,method='CHATGPT')))
    path=tmp_path/'inspection.json';path.write_text(json.dumps(inspection))
    value=binding.freeze_current_binding(inspection_path=path,qualification_path=tmp_path/'review.json',profile=SOL_HIGH_V1)
    for key in (*binding.OVERRIDES,'CODEX_HOME','CODEX_CLI_BIN'):monkeypatch.delenv(key,raising=False)
    for key in ('HOME','PATH'):monkeypatch.setenv(key,env[key])
    return value,inspection,path


def test_current_review_historical_separation_and_drift(installed,monkeypatch):
    value,inspection,path=installed
    binding.validate_binding(value,str(value.executable),profile=SOL_HIGH_V1)
    assert binding.binding_from_json(json.loads(json.dumps(asdict(value),default=str)))==value
    legacy={k:v for k,v in asdict(value).items() if k not in ('runtime_contract','display_path','auth_source')}
    called=[]
    monkeypatch.setattr(binding,'validate_historical_binding',lambda *a,**kw:called.append(True))
    binding.validate_binding(binding.binding_from_json(legacy),str(value.executable),profile=SOL_HIGH_V1)
    assert called==[True]
    for wrong in (replace(value,executable_sha256='0'*64),replace(value,version='codex-cli 0.155.1'),
            replace(value,runtime_contract='invented')):
        with pytest.raises(OfficialShadowError):binding.validate_binding(wrong,str(value.executable),profile=SOL_HIGH_V1)
    monkeypatch.setenv('PATH','/different')
    with pytest.raises(OfficialShadowError,match='PATH_DRIFT'):binding.validate_binding(value,str(value.executable),profile=SOL_HIGH_V1)
    monkeypatch.setenv('PATH',inspection['environment']['PATH'])
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-forbidden')
    with pytest.raises(OfficialShadowError,match='OVERRIDE'):binding.validate_binding(value,str(value.executable),profile=SOL_HIGH_V1)


def test_missing_options_or_installation_not_qualified(installed,tmp_path):
    value,inspection,path=installed
    for index,change in enumerate(('flag','signature','auth')):
        wrong=deepcopy(inspection)
        if change=='flag':wrong['commands']['options']['flags']['--ignore-rules']=False
        elif change=='signature':wrong['signature']['returncode']=1
        else:wrong['commands']['auth']['method']='UNKNOWN'
        path.write_text(json.dumps(wrong))
        with pytest.raises(OfficialShadowError):binding.freeze_current_binding(
            inspection_path=path,qualification_path=tmp_path/('rejected'+str(index)),profile=SOL_HIGH_V1)


def test_same_binding_onboarding_worker_executor_and_child_environment(installed,tmp_path,monkeypatch):
    from app.services import onboarding_decision_service as onboarding
    from app.services import codex_runtime_state_service as runtime
    from app.services import production_model_transport as wire
    from app.services.production_model_profile import ModelCallSlot,SolHighCallBudget
    from tests.test_c22y_sol_high_contract import payload,OfflineWorker,fake_cli
    value,inspection,path=installed
    observed=[]
    def prepare(root,*,namespace,auth_source):
        home=Path(root)/namespace.replace(':','_')/'home';home.mkdir(parents=True)
        (home/'auth.json').symlink_to(auth_source)
        return SimpleNamespace(codex_home=home,environment=lambda env:{**env,'CODEX_HOME':str(home)})
    monkeypatch.setattr(runtime,'prepare_codex_runtime_state',prepare)
    def call(command,**kwargs):
        observed.append((command,kwargs['env']))
        if 'input' in kwargs:return fake_cli(command,**kwargs)
        Path(command[command.index('-o')+1]).write_text('{}')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(executor.subprocess,'run',call)
    monkeypatch.setattr(onboarding,'get_settings',lambda:SimpleNamespace(data_dir=tmp_path/'data'))
    prompt=tmp_path/'prompt';prompt.write_text('synthetic');schema=tmp_path/'schema';schema.write_text('{}')
    onboarding._invoke_signed_in_codex(prompt=prompt,output=tmp_path/'onboard-output',log=tmp_path/'onboard-log',
        schema=schema,timeout=600,state_namespace='test',execution_profile=SOL_HIGH_V1,runtime_binding=value)
    process=OfflineWorker();factory_env=[]
    async def factory(*args,**kw):factory_env.append(kw['env']);return process
    data=payload('MARKET');budget=SolHighCallBudget([ModelCallSlot('KR_MARKET','MARKET',digest(data),'market')])
    transport=wire.OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(value),default=str)),
        runtime_root=tmp_path/'transport',worker_factory=factory,execution_profile=SOL_HIGH_V1,call_budget=budget)
    transport.bind_cycle(market='kr',run_id='C22AQ_SYNTHETIC')
    assert asyncio.run(transport.request(data,model=SOL_HIGH_V1.model,effort='high',timeout=600,stage='MARKET',panel='KR_MARKET'))==b'{}'
    assert len(observed)==2 and all(c[0]==str(value.executable) for c,e in observed)
    assert all(e['HOME']==value.home and e['PATH']==inspection['environment']['PATH'] for c,e in observed)
    assert all(binding.auth_identity(Path(e['CODEX_HOME'])/'auth.json')==binding.auth_identity(value.auth_source) for c,e in observed)
    assert len({e['CODEX_HOME'] for c,e in observed})==2
    assert factory_env[0]['PATH']==binding.parent_environment(value)['PATH']
    assert wire.request_from_frame(process.frame).binding==value
    with pytest.raises(ValueError):asyncio.run(transport.request(data,model=SOL_HIGH_V1.model,effort='high',timeout=600,stage='MARKET',panel='KR_MARKET'))
    assert len(observed)==2


def test_exact_server_codes_status_and_not_model_prose():
    error=dict(status=400,error=dict(code='model_not_found',type='invalid_request_error',message='PRIVATE_DO_NOT_EXPORT'))
    nested=dict(type='turn.failed',error=dict(message=json.dumps(error)))
    result=executor.model_failure_diagnosis(json.dumps(nested).encode())
    assert result['classification']=='MODEL_CLIENT_ACCOUNT_COMBINATION_UNSUPPORTED'
    assert result['server_errors'][-1]['status']==400 and result['server_errors'][-1]['code']=='model_not_found'
    assert 'PRIVATE' not in json.dumps(result)
    for code,expected in (('token_expired','AUTHENTICATION_FAILURE'),('workspace_mismatch','AUTH_WORKSPACE_MISMATCH'),
            ('rate_limit_exceeded','QUOTA_OR_RATE_LIMIT')):
        value=executor.model_failure_diagnosis(json.dumps(dict(error=dict(code=code))).encode())
        assert value['classification']==expected and value['reset_information']=='UNOBSERVED'
    for row in (dict(type='item.completed',item=dict(text=json.dumps(error))),dict(type='error',message='model_not_found'),
            dict(type='warning',message='falling back to bundled metadata')):
        assert executor.model_failure_diagnosis(json.dumps(row).encode())['classification']=='PROCESS_ERROR_UNCLASSIFIED'


def test_worker_exit_zero_cli_failure_and_bridge_cause_preserved(installed,tmp_path,monkeypatch):
    from app.jobs import production_model_worker as worker
    from app.services import production_model_transport as wire
    from app.services.production_b2_execution import ModelTransportError
    from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
    from app.services.production_model_profile import ModelCallSlot,SolHighCallBudget
    from tests.test_c22y_sol_high_contract import payload
    import io
    value,_,_=installed
    diagnosis=executor.model_failure_diagnosis(b'{"error":{"code":"model_not_found","status":400}}')
    def reject(**kw):
        exc=OfficialShadowError('MODEL_ENTITLEMENT_OR_QUOTA_UNAVAILABLE',process_started=True)
        exc.cli_returncode=1;exc.diagnosis=diagnosis;raise exc
    monkeypatch.setattr(worker,'invoke_official_bound',reject)
    class Process:
        pid=123;returncode=0
        async def communicate(self,raw):
            monkeypatch.setattr(worker.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(raw)))
            assert worker.main() is None
    async def factory(*a,**kw):return Process()
    data=payload('MARKET');budget=SolHighCallBudget([ModelCallSlot('KR_MARKET','MARKET',digest(data),'market')])
    transport=wire.OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(value),default=str)),
        runtime_root=tmp_path/'transport',worker_factory=factory,execution_profile=SOL_HIGH_V1,call_budget=budget)
    transport.bind_cycle(market='kr',run_id='C22AQ_SYNTHETIC')
    bridge=SimpleNamespace(_native_owner_parents={},execution_profile=SOL_HIGH_V1,model=transport)
    with pytest.raises(ModelTransportError,match='MODEL_ENTITLEMENT'):
        asyncio.run(ProductionRuntimeBridgeV1._invoke(bridge,SimpleNamespace(market='kr'),'MARKET',
            dict(payload=data,subjects=[]),tmp_path/'bridge'))
    receipt=json.loads((tmp_path/'bridge/attempt-1/receipt.json').read_bytes())
    assert receipt['diagnosis']==diagnosis and receipt['worker_returncode']==0 and receipt['cli_returncode']==1
    assert not (tmp_path/'bridge/attempt-2').exists()


def test_formal_market_reused_dynamic_slots_and_failed_intent_not_refilled(tmp_path):
    from tests.test_c22z_dynamic_model_plan import cohort,request,accept_one
    from app.services.model_execution_plan import compile_model_plan
    from app.services.production_model_profile import SolHighCallBudget
    plan=compile_model_plan(cohort(us=10,kr=8),topology='CANONICAL_PRODUCTION')
    assert len(plan.slots)==41 and sum(s.market=='kr' for s in plan.slots)==18
    assert sum(s.market=='us' for s in plan.slots)==23
    journal=tmp_path/'journal.jsonl'
    budget=SolHighCallBudget(plan=plan,approved_max_invocations=41,approved_plan_sha256=plan.sha256,journal_path=journal)
    market=next(s for s in plan.slots if s.market=='kr' and s.stage=='MARKET')
    accept_one(budget,plan,market)
    assert len(budget.used)==len(budget.accepted)==1
    with pytest.raises(ValueError):budget.bind_stage('MARKET',request(plan,market))
    core=next(s for s in plan.slots if s.market=='kr' and s.stage=='CORE')
    assert budget.bind_stage('CORE',request(plan,core))['dependency_outputs'][market.slot_id]
    budget.stop();before=journal.read_bytes()
    reopened=SolHighCallBudget(plan=plan,approved_max_invocations=41,approved_plan_sha256=plan.sha256,journal_path=journal)
    us=next(s for s in plan.slots if s.market=='us' and s.stage=='MARKET')
    with pytest.raises(ValueError):reopened.bind_stage('MARKET',request(plan,us))
    assert len(reopened.used)==1 and journal.read_bytes().startswith(before)


def test_aggregate_flow_selected_composition_to_prompt_has_no_detail_grant(tmp_path):
    from tests.test_c22ap_role_aligned_partial import captured,SESSION_DATE
    from app.services.unified_source_composition import SourceInput,A
    from app.services.selected_source_composition import selected_market_packet
    from tests.test_r2b_r5_market_adapter import fixture
    from app.services.canonical_market_projection import _project_market_context
    result,norm,owner,graph,cutoff,calls,reads=captured(tmp_path,False)
    receipt=graph.receipt
    from app.services.unified_source_composition import SourceRole
    role=SourceRole(key='kr_local_indices_sectors_breadth',owner='kiwoom_pages',market='kr',symbol='*',
        provider='kiwoom_rest',basis='query_time',session=str(SESSION_DATE),acquisition_class=A,mandatory=True)
    native=dict(item=SourceInput(role=role.key,run_id=receipt.run_id,attempt_id=receipt.attempt_id,acquisition_class=A,
        requested_at=receipt.requested_at,received_at=receipt.received_at,artifact=receipt.artifact,
        artifact_sha256=receipt.artifact_sha256,receipt_artifact='aggregate.json',
        receipt_sha256=file_sha256(tmp_path/'selected/aggregate.json')),role=role,root=tmp_path/'selected',
        run_id=receipt.run_id,start=receipt.requested_at,cutoff=cutoff,attempt_id=receipt.attempt_id,
        policy=__import__('app.services.unified_source_policy',fromlist=['UnifiedSourcePolicy']).UnifiedSourcePolicy(frozenset({'kiwoom_rest'})),
        owners={'kiwoom_pages':owner})
    selected=selected_market_packet(native)
    assert len(selected['aggregate_flows']['value']['market_flows'])==6
    assert not selected['aggregate_flows']['value']['economic_use']
    packet,seed,authority=fixture('kr',run=receipt.run_id)
    # Synthetic composition envelope tests consumers; it is not a current Source grant.
    selected['cutoff']='2026-08-25T08:02:00+00:00'
    seed.update(started_at='2026-08-25T08:00:00+00:00',attempts={'kr':receipt.attempt_id},
        attempt_hashes={'kr':digest(selected)})
    publication=dict(contract='fresh-publication-replay-v1',run_id=receipt.run_id,providers={},value_sha256=digest({}))
    authority.update(markets={'kr':selected},run_seed_sha256=digest(seed),publication_context=publication)
    packet.update(market_sources=deepcopy(selected),run_seed_sha256=digest(seed),authority_graph_sha256=digest(authority),
        publication_context=publication)
    projection=_project_market_context(packet,seed,authority,expected_authority_sha256=digest(authority),execution_metadata={})
    facts=projection['packet']['market_context']['fact_catalog']
    flows=[f for f in facts if f['fact_type']=='market_flow']
    assert len(flows)==6
    assert projection['packet']['market_context']['adapter_context']['market_flows']==[]
    assert all(f['fields']['source_ref'].endswith(str(SESSION_DATE)) for f in flows)
    assert all(f['fields']['source_ref'] not in projection['context']['facts'] and f['fact_id'] not in projection['context']['facts'] for f in flows)
    reference=projection['context']['dated_aggregate_flow_references']
    assert len(reference['value']['market_flows'])==6 and not reference['directional_citation_eligible']
    from app.services.market_numeric_claim_service import render_typed_market_facts
    source=projection['packet']['market_context'];catalog=projection['context']['numeric_catalog']
    assert len([r for r in catalog['claims'] if r['claim_type']=='DATED_AGGREGATE_FLOW'])==6
    rendered=render_typed_market_facts(catalog,source)
    assert 'KRW' in rendered and str(SESSION_DATE) in rendered and 'KRX·NXT' in rendered
    assert projection['receipt']['numeric_alias_binding']['status']=='PASS'
    source['fact_catalog'][next(i for i,f in enumerate(source['fact_catalog']) if f['fact_type']=='market_flow')]['fields']['net_buy_amount']+=1
    with pytest.raises(ValueError):render_typed_market_facts(catalog,source)


def test_semantic_rejection_local_but_auth_and_ledger_failure_global(tmp_path):
    from app.services.research_no_send_run import PreparedResearchBridge,run_prepared_research
    from app.services.production_b2_execution import SemanticReject,ModelTransportError
    from tests.test_c22z_dynamic_model_plan import cohort
    from app.services.model_execution_plan import compile_model_plan
    for index,exc in enumerate((SemanticReject('rejected'),ModelTransportError('MODEL_AUTHENTICATION_FAILED'),ValueError('journal_chain_drift'))):
        stops=[];calls=[]
        bridge=object.__new__(PreparedResearchBridge)
        plan=compile_model_plan(cohort(us=0,kr=1),topology='CANONICAL_PRODUCTION')
        bridge.child=SimpleNamespace(plan=plan)
        bridge.child_binding={'SYNTHETIC_NOT_SOURCE_AUTHORITY':True}
        bridge.snapshot=lambda:{'SYNTHETIC_NOT_SOURCE_AUTHORITY':True}
        async def fail(*a,**kw):calls.append(True);raise exc
        bridge.stage=fail
        bridge.model=SimpleNamespace(call_budget=SimpleNamespace(stop=lambda **kw:stops.append(kw['global_stop'])))
        output=asyncio.run(run_prepared_research(bridge,root=tmp_path/str(index),enabled=True,local_output_rejection=True))
        assert output['status']=='FAILED_NO_SEND' and calls==[True]
        assert stops==[not isinstance(exc,SemanticReject)]


def test_partial_field_success_does_not_create_amount_history_or_unit_rights():
    from app.services.sec_financial_source_completeness import field_completeness
    selection=dict(fields=dict(revenue=dict(status='PASS'),operating_income=dict(status='BLOCKED',
        denial_reasons=['NO_EXACT_COMPARABLE_PRIOR'])))
    docs=[dict(occurrences=[dict(field='operating_income',occurrence_id='current-only')],
        valid_occurrence_ids=['current-only'],inline_owner=dict(denials=[]))]
    complete=dict(bounded_plan_complete=False,reasons=['PURPOSE_UNRESOLVED'],receipt_sha256='a'*64,
        current_generation_eligible=True)
    result=field_completeness(selection,docs,complete)
    assert result['partial_field_consumption_allowed']
    assert result['field_claim_limits']['revenue']['growth_claim']
    assert not result['field_claim_limits']['operating_income']['growth_claim']
    assert result['fields']['operating_income']['valid_occurrence_refs']==['current-only']
    assert all(not r['zero_imputation'] and not r['valuation_or_per_share_grant'] for r in result['field_claim_limits'].values())
    # Remaining current-only monitoring path is still unresolved, not a fake PASS.
    selection['fields']['revenue']['status']='BLOCKED'
    assert not field_completeness(selection,docs,complete)['partial_field_consumption_allowed']
    selection['fields']['revenue']['status']='PASS';complete['current_generation_eligible']=False
    assert not field_completeness(selection,docs,complete)['partial_field_consumption_allowed']
