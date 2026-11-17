"""Offline storage and original MARKET handoff, with no external transport."""
import asyncio
import json
import os
from pathlib import Path
import socket
from types import SimpleNamespace

import pytest

from app.services.research_artifact_budget import ArtifactCapacityError, ResearchArtifactBudget, artifact_scope
from app.services.research_request_storage import load_stage_request, save_stage_request
from app.services.unified_run_artifacts import durable_json
from app.services.unified_runtime_v2 import CONTRACT, STAGES
from app.services.unified_snapshot_contract import digest


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('C22AR offline test attempted network or worker execution')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', forbidden)


def test_all_stage_storage_reference_and_capacity(tmp_path):
    root = tmp_path/'KR_REPLAY'
    runtime = tmp_path/'runtime'
    budget = ResearchArtifactBudget(roots={root:'result', runtime:'scratch', root/'snapshots':'source'})
    run = root.name
    snapshot = dict(child_binding=dict(run_id=run, market='kr', source_generation='SOURCE', cutoff='dated'),
        collection=dict(market='kr', production_envelope=dict(generation_id=run),
                        monitoring_input=dict(source_generation_id='SOURCE', blob='x'*30_768_992)))
    inputs = {}
    with artifact_scope(budget):
        for stage in STAGES[:-1]:
            req = dict(contract=CONTRACT, run_id=run, stage=stage, snapshot_sha256=digest(snapshot),
                snapshot=snapshot, inputs=dict(inputs), configuration_sha256=digest('config'))
            proof = save_stage_request(root, req)
            path = root/stage.lower()/'request.json'
            assert load_stage_request(path, expected_logical_sha256=proof['logical_request_sha256'],
                expected_storage_sha256=proof['storage_record_sha256']) == req
            assert path.stat().st_size < 4096
            value = dict(runtime_contract=CONTRACT, run_id=run, generation_id=run, stage=stage,
                snapshot_sha256=digest(snapshot), request_sha256=digest(req), status='PASS', errors=[], output={})
            durable_json(path.with_name('response.json'),value,exclusive=True)
            inputs[stage] = value
        save_stage_request(root, req)  # No duplicate snapshot or immutable rewrite.
    assert len(list((root/'snapshots').iterdir())) == 1
    for i in range(41):
        context = runtime/str(i)
        context.mkdir(parents=True)
        with (context/'cli.sqlite3-wal').open('xb') as f:
            f.truncate(40*1024**2)
    os.link(runtime/'0/cli.sqlite3-wal',runtime/'0/hardlink')
    sizes = budget.check(path=runtime)
    assert sizes['scratch'] == 41*40*1024**2 and sizes['source'] > 30_768_992
    assert sizes['result'] < 100_000 and sizes['total'] < budget.work_cap
    legacy = root/'legacy.json'
    durable_json(legacy,req,exclusive=True)
    assert load_stage_request(legacy,expected_logical_sha256=digest(req)) == req
    record = json.loads(path.read_bytes())
    durable_json(path,{**record,'snapshot_ref':'../../other.json'})
    with pytest.raises(ValueError,match='path_drift'):
        load_stage_request(path)
    durable_json(path,record)
    durable_json(root/'core/response.json',dict(inputs['CORE'], status='FAIL'))
    with pytest.raises(ValueError,match='upstream_hash_drift'):
        load_stage_request(path)


def test_capacity_prewrite_peak_and_unknown_symlink(tmp_path):
    root = tmp_path/'run'
    root.mkdir()
    cache = root/'cache'
    cache.mkdir()
    budget = ResearchArtifactBudget(roots={root:'result', cache:'scratch'},result_cap=100,work_cap=1000)
    with artifact_scope(budget):
        durable_json(root/'report.json','a'*60,exclusive=True)
        before = (root/'report.json').read_bytes()
        with pytest.raises(ArtifactCapacityError) as err:
            durable_json(root/'report.json','b'*60)
        assert err.value.receipt['code'] == 'RESEARCH_RESULT_CAP'
        assert (root/'report.json').read_bytes() == before and not list(root.glob('.pending-*'))
        with (cache/'temp-shm').open('xb') as f:
            f.truncate(1000)
        with pytest.raises(ArtifactCapacityError,match='RESEARCH_WORK_CAP'):
            durable_json(root/'small.json',1,exclusive=True)
        assert not (root/'small.json').exists()
    (cache/'unexpected').symlink_to(tmp_path/'not-followed')
    with pytest.raises(ValueError,match='unexpected_symlink'):
        budget.measure()


def test_capacity_blocks_before_any_transport_consume(tmp_path, monkeypatch):
    from app.services import production_model_transport as transport
    from app.services.vnext_execution_profile import SOL_HIGH_V1

    calls = []
    model = object.__new__(transport.OfficialProductionModelTransport)
    model.execution_profile = SOL_HIGH_V1
    model.binding = SimpleNamespace(executable='offline-fixture')
    model.call_budget = SimpleNamespace(plan=None, maximum=1, consume=lambda *a,**kw:calls.append('CONSUME'))
    model.cycle, model.counts, model.total, model.secrets = ('kr','KR_TEST'), {}, 0, ()
    model.runtime_root = tmp_path
    monkeypatch.setattr(transport,'validate_binding',lambda *a,**kw:None)
    budget = ResearchArtifactBudget(roots={tmp_path:'scratch'}, result_cap=100)
    with artifact_scope(budget), pytest.raises(ArtifactCapacityError,match='RESEARCH_RESULT_CAP'):
        asyncio.run(model.request(dict(prompt='offline\nFROZEN_CONTEXT:\n{}\n', response_schema={}, input={}),model=SOL_HIGH_V1.model,
            effort=SOL_HIGH_V1.effort,timeout=600,stage='MARKET'))
    assert not calls and model.total == 0 and not list(tmp_path.iterdir())


def test_actual_market_cold_handoff_to_render(tmp_path):
    from app.services.accepted_market_replay import AcceptedMarketOrigin, verify_market_replay
    from app.services.model_execution_plan import CohortSubject, FrozenCohort, compile_model_plan
    from app.services.production_model_profile import SolHighCallBudget
    from app.services.production_monitoring_session import ProductionMonitoringSession
    from app.services.production_message_renderer import market_message
    from app.services.research_no_send_run import PreparedResearchBridge, run_prepared_research
    from app.services.unified_runtime_v2 import StageResultV2
    from app.services.vnext_execution_profile import SOL_HIGH_V1

    if not (origin_root := os.environ.get('C22AR_ORIGIN_ROOT')):
        pytest.skip('Private local C22AQ origin custody required')
    origin_root = Path(origin_root)
    old_run = 'C22AQ_KR_EXEC_20261112T130813Z'
    origin = AcceptedMarketOrigin(origin_root/'TM_C22AQ_V1_RECOVERY1_RESULT_20261112.zip',
        'de3b3607f1c21d1c506c898e5aed31d925ae34a59801ccfc39c458abba343794',
        origin_root/'recovery-1/private-live/no-send'/old_run/'market',
        Path('/private/tmp/c22aq-sol-high-20261112T130813Z/invocation-ledger')/old_run/'events.jsonl')
    before = origin.invocation_journal.read_bytes()
    snapshot = load_stage_request(origin.stage_directory/'request.json')['snapshot']
    source = snapshot['collection']['monitoring_input']
    old = snapshot['child_binding']
    run = 'C22AR_KR_OFFLINE_COLD'
    scope = snapshot['collection']['production_envelope']
    scope['generation_id'] = run
    cohort = FrozenCohort(run,old['source_generation'],old['assessment_date'],old['effective_at'],old['cutoff'],
        tuple(CohortSubject('kr',t,'offline:'+t,old['cutoff'],digest(t)) for t in scope['subjects']),
        (('kr',digest('offline-no-owner-grant')),),digest('offline-scope'))
    plan = compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
    snapshot['child_binding'] = dict(old,run_id=run,consumed_source_sha256=digest(source),cohort_sha256=cohort.sha256,plan_sha256=plan.sha256)
    budget = SolHighCallBudget(plan=plan,approved_max_invocations=17,approved_plan_sha256=plan.sha256,
        journal_path=tmp_path/'new-journal.jsonl',market_origin=origin)
    stages = []

    class OfflineWire:
        call_budget = budget
        async def request(self,*args,**kwargs):
            raise AssertionError('No MARKET or stock model transport in this test')

    bridge = object.__new__(PreparedResearchBridge)
    bridge.child = SimpleNamespace(plan=plan)
    bridge.child_binding = snapshot['child_binding']
    bridge.execution_profile = SOL_HIGH_V1
    bridge._native_owner_parents = {}
    bridge.model = OfflineWire()
    bridge.snapshot = lambda:snapshot

    def session(request, directory):
        # Replay MARKET only. The historical stock owner is not revived or used.
        prepared = ProductionMonitoringSession(directory/'canonical',market='kr',generation_id=old_run,
            source=request['snapshot']['collection']['monitoring_input'],source_generation_id=old['source_generation'])
        prepared.gen = run
        bridge._restore_upstream(prepared,request)
        return prepared, SimpleNamespace(production_envelope=SimpleNamespace(subjects=scope['subjects'], model_dump=lambda **_:scope))

    bridge._session = session
    original_stage = bridge.stage

    async def stage(request, directory):
        name = request['stage']
        if name == 'MARKET':
            return await original_stage(request,directory)
        for slot in (s for s in plan.slots if s.stage == name):
            payload = dict(fixture='No stock analysis or model output', slot=slot.slot_id)
            pin = digest(payload)
            bound = budget.bind_stage(name,dict(market='kr',batch=slot.batch_id,subjects=list(slot.subjects),
                source_generation_id=cohort.source_generation,execution_generation_id=run,payload=payload,payload_sha256=pin))
            budget.consume(None,name,pin,slot_scope=bound)
            budget.record_acceptance(slot.slot_id,payload_sha256=pin,output_sha256=digest(slot.slot_id))
            stages.append(name)
        output = dict(fixture=True)
        if name in ('VALIDATE','RENDER'):
            restored, _ = session(dict(request,stage='CORE'),directory)
            market = dict(market_message(restored), snapshot_sha256=request['snapshot_sha256'], NO_SEND=True)
            messages = [market]+[dict(message_id=t,NO_SEND=True,text='Synthetic slot fixture only') for t in scope['subjects']]
            output = dict(content_sha256=digest(messages)) if name == 'VALIDATE' else dict(messages=messages)
        return StageResultV2(run_id=run,generation_id=run,stage=name,snapshot_sha256=request['snapshot_sha256'],
            request_sha256=digest(request),status='PASS',output=output)

    bridge.stage = stage
    bridge.artifact_budget = ResearchArtifactBudget(roots={tmp_path:'scratch',tmp_path/'cycles':'result',
        budget.journal.path:'result'})
    state = asyncio.run(run_prepared_research(bridge,root=tmp_path/'cycles',enabled=True))
    assert origin.invocation_journal.read_bytes() == before
    assert state['status'] == 'RENDER_VERIFIED_NO_SEND', (state.get('error_chain'),stages)
    assert len(state['messages']) == 9 and all(m['NO_SEND'] for m in state['messages'])
    assert stages == ['CORE']*3+['A']*3+['B']*3+['B2']*8
    assert len(budget.inherited) == 1 and len(budget.used) == 17 and len(budget.accepted) == 18
    assert len(list((tmp_path/'cycles'/run/'snapshots').iterdir())) == 1
    assert budget.inherited[plan.slots[0].slot_id]['output_sha256'] == '3f85f90944bfbdcfe014402245ad1bccfdf2c9c90f4007867dad89a97bb7e715'
    assert state['messages'][0]['message_id'] == 'MARKET_KR' and state['messages'][0]['text'] != 'Synthetic slot fixture only'
    market_request = load_stage_request(tmp_path/'cycles'/run/'market/request.json')
    replay, _ = session(market_request,tmp_path/'negative')
    item, = replay.build('MARKET')
    changed = dict(snapshot,child_binding=dict(snapshot['child_binding'],cutoff='2026-11-13T00:00:00+00:00'))
    with pytest.raises(ValueError,match='origin_scope_drift'):
        verify_market_replay(origin,snapshot=changed,session=replay,item=item)
    tampered = dict(item,payload=dict(item['payload'],prompt='Changed input'))
    with pytest.raises(ValueError,match='canonical_acceptance_or_payload_drift'):
        verify_market_replay(origin,snapshot=snapshot,session=replay,item=tampered)
    reread = SolHighCallBudget(plan=plan,approved_max_invocations=17,approved_plan_sha256=plan.sha256,
        journal_path=budget.journal.path,market_origin=origin)
    assert reread.inherited == budget.inherited and reread.used == budget.used
    with pytest.raises(ValueError,match='budget_exhausted'):
        slot = plan.slots[0]
        bound = reread.bound[slot.slot_id]
        reread.consume(None,'MARKET',bound['payload_sha256'],slot_scope=bound)
