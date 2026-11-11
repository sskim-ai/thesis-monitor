"""New lifecycle boundaries only. No synthetic economic E2E claim."""
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.services.model_execution_plan import CohortSubject, FrozenCohort, compile_model_plan
from app.services.production_model_profile import SolHighCallBudget
from app.services.production_b2_execution import ModelTransportError
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.vnext_execution_profile import SOL_HIGH_V1
from app.services.research_no_send_run import (
    MarketResearchChild, PreparedResearchBridge, MasterFourPanelManifest,
    build_research_no_send_adapter, run_prepared_research, stage_deadline,
)
from app.services.scoped_monitoring_research import prepare_scoped_research_source
from app.services.unified_snapshot_contract import digest


def plan(n=3):
    c = FrozenCohort('BOUNDARY_ONLY_US','SOURCE_US','2026-11-10',
        '2026-11-11T00:00:00+00:00','2026-11-11T00:00:00+00:00',
        tuple(CohortSubject('us',f'X{i}',f'TEST:{i}','2026-11-11T00:00:00+00:00',digest(i)) for i in range(n)),
        (('us',digest('boundary-not-original-owner')),),digest('scope'))
    return compile_model_plan(c,topology='CANONICAL_PRODUCTION')


def budget(p,path):
    return SolHighCallBudget(plan=p,approved_max_invocations=len(p.slots),approved_plan_sha256=p.sha256,journal_path=path)


def req(p,slot):
    payload = dict(prompt='offline lifecycle only',input={},response_schema={})
    return dict(market=slot.market,batch=1 if slot.stage=='MARKET' else slot.batch_id,
        subjects=list(slot.subjects),execution_generation_id=p.cohort.run_id,
        source_generation_id=p.cohort.source_generation,payload=payload,payload_sha256=digest(payload))


def consume(b,p,slot):
    r = req(p,slot)
    scope = b.bind_stage(slot.stage,r)
    b.consume(None,slot.stage,r['payload_sha256'],slot_scope=scope)
    return scope


def test_three_subject_batch_stage_deadline():
    p = plan(4)
    core = [s for s in p.slots if s.stage=='CORE']
    assert [len(s.subjects) for s in core] == [3,1]
    assert stage_deadline(p,'CORE')['total_seconds'] == 1230
    assert stage_deadline(p,'B2')['total_seconds'] == 2430
    assert stage_deadline(p,'RENDER')['total_seconds'] == 30
    with pytest.raises(ValueError):
        stage_deadline(p,'DELIVER')


def test_source_only_receipt_and_old_registration_cannot_issue():
    with pytest.raises(ValueError,match='disabled'):
        prepare_scoped_research_source(market='us',subjects=('X',),registration_owner=None,
            whole={},local_seeds={},valuation_contexts={},generation='G',coverage={},census={})
    with pytest.raises(ValueError,match='live_backend_owner'):
        prepare_scoped_research_source(enabled=True,market='us',subjects=('X',),registration_owner={'source_only':True},
            whole={},local_seeds={},valuation_contexts={},generation='G',coverage={},census={})


def test_factory_off_and_planning_cohort_never_becomes_live():
    from app.services.production_adapter_factory import build_research_adapter
    child = MarketResearchChild(plan(),None)
    with pytest.raises(ValueError,match='factory_disabled'):
        build_research_no_send_adapter(child=child,settings=None,binding=None,runtime_root=None,
            journal_path=None,approved_max_invocations=6,approved_plan_sha256='',clock=None)
    with pytest.raises(ValueError,match='factory_disabled'):
        build_research_adapter(child=child,settings=None,binding=None,runtime_root=None,
            journal_path=None,approved_max_invocations=6,approved_plan_sha256='',clock=None)
    with pytest.raises(ValueError,match='SOURCE_OWNER_REQUIRED'):
        child.verify()


def test_persistent_intent_survives_new_python_process(tmp_path):
    p = plan(); path = tmp_path/'invocations.jsonl'
    b = budget(p,path); consume(b,p,p.slots[0])
    script = """import json,sys
from app.services.model_execution_plan import ModelExecutionPlan
from app.services.production_model_profile import SolHighCallBudget
p=ModelExecutionPlan.from_dict(json.loads(sys.argv[1]))
b=SolHighCallBudget(plan=p,approved_max_invocations=len(p.slots),approved_plan_sha256=p.sha256,journal_path=sys.argv[2])
assert b.state()['consumed']==1
try:b.consume(None,'MARKET',next(iter(b.bound.values()))['payload_sha256'],slot_scope=next(iter(b.bound.values())))
except ValueError:print('RESTART_DUPLICATE_DENIED')
else:raise AssertionError('duplicate')
"""
    result = subprocess.run([sys.executable,'-c',script,json.dumps(p.to_dict()),str(path)],
        cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,check=True)
    assert result.stdout.strip() == 'RESTART_DUPLICATE_DENIED'


def test_accepted_dependencies_restore_without_budget_refill(tmp_path):
    p=plan(); path=tmp_path/'j'
    b=budget(p,path); scope=consume(b,p,p.slots[0])
    b.record_acceptance(p.slots[0].slot_id,payload_sha256=scope['payload_sha256'],output_sha256=digest('boundary response'))
    restored=budget(p,path)
    consume(restored,p,p.slots[1])
    assert budget(p,path).state()['consumed']==2


def test_parallel_pending_and_failed_stage_prevent_later_calls(tmp_path):
    p=plan(4); b=budget(p,tmp_path/'j'); first=consume(b,p,p.slots[0])
    b.record_acceptance(p.slots[0].slot_id,payload_sha256=first['payload_sha256'],output_sha256=digest('mock'))
    consume(b,p,p.slots[1])
    with pytest.raises(ValueError,match='parallel'):
        consume(b,p,p.slots[2])
    b.stop()
    with pytest.raises(ValueError,match='failed_cycle'):
        budget(p,tmp_path/'j').bind_stage('A',req(p,next(s for s in p.slots if s.stage=='A')))


def test_changed_plan_or_cap_and_torn_journal_are_rejected(tmp_path):
    p=plan(); path=tmp_path/'j'; budget(p,path)
    with pytest.raises(ValueError,match='identity_or_chain'):
        SolHighCallBudget(plan=p,approved_max_invocations=99,approved_plan_sha256=p.sha256,journal_path=path)
    with path.open('ab') as f:f.write(b'{')
    with pytest.raises(ValueError,match='torn_write'):
        budget(p,path)


def test_no_send_failure_and_interrupted_cycle_never_notify(tmp_path):
    p=plan(); b=budget(p,tmp_path/'j')
    bridge=object.__new__(PreparedResearchBridge)
    bridge.child=MarketResearchChild(p,None)
    bridge.child_binding={'boundary':'not-source'}
    bridge.model=SimpleNamespace(call_budget=b)
    def missing():raise ValueError('missing_real_source_before_models')
    bridge.snapshot=missing
    result=asyncio.run(run_prepared_research(bridge,root=tmp_path/'cycle',enabled=True))
    assert result['status']=='FAILED_NO_SEND' and result['normal_messages_sent'] is False
    assert result['failure_notifications_sent'] is False and not result['stage_receipts']
    assert b.state()['consumed']==0
    assert asyncio.run(bridge.notify_failure({}))['external_attempts']==0
    assert asyncio.run(run_prepared_research(bridge,root=tmp_path/'cycle',enabled=True))==result


def test_master_does_not_flatten_or_accept_incomplete_children():
    # No current owner is forged: admission must fail before combining four panels.
    master=MasterFourPanelManifest('P',(MarketResearchChild(plan(),None),))
    with pytest.raises(ValueError,match='SOURCE_OWNER_REQUIRED'):
        master.combine({})


@pytest.mark.parametrize('failure',['QUOTA_UNAVAILABLE','WORKER_QUALIFICATION_EXPIRED'])
def test_transport_only_failure_never_retries_or_accepts(tmp_path,failure):
    p=plan(); b=budget(p,tmp_path/'j'); calls=[]
    class Transport:
        call_budget=b
        async def request(self,*args,**kwargs):
            calls.append(failure)
            raise ModelTransportError(failure)
    def forbidden(*args):raise AssertionError('must not accept failed transport')
    session=SimpleNamespace(market='us',verify_model_build=lambda *args:None,accept=forbidden)
    bridge=SimpleNamespace(_native_owner_parents={},execution_profile=SOL_HIGH_V1,model=Transport())
    with pytest.raises(ModelTransportError):
        asyncio.run(ProductionRuntimeBridgeV1._invoke(bridge,session,'MARKET',req(p,p.slots[0]),tmp_path/'attempt'))
    assert calls==[failure] and not b.accepted
