"""Offline C22BF boundaries. Only the model/clock and historical Owner are fixtures."""
import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.services import prospective_class_c_owner as registration
from app.services.model_execution_plan import FrozenCohort, compile_model_plan
from app.services.model_invocation_journal import ModelInvocationJournal, read_invocation_journal
from app.services.production_b2_execution import ModelTransportError
from app.services.production_model_profile import SolHighCallBudget, SolHighWirePolicy
from app.services.production_model_transport import OfficialProductionModelTransport, request_from_frame
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.research_no_send_run import (
    PARTIAL, PreparedResearchBridge, _split_stage_deadline, run_prepared_research, stage_deadline,
)
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests.production_entrypoint_wire_fixture import SyntheticModelProcess
from tests.test_c22aa_research_boundaries import req
from tests.test_c22y_sol_high_contract import qualify_fixture
from tests.test_official_codex_shadow_transport import invocation


@pytest.fixture(autouse=True)
def no_external_io(monkeypatch):
    def blocked(*args,**kwargs):
        raise AssertionError('offline test attempted network or real worker')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    monkeypatch.setattr(socket.socket,'connect_ex',blocked)
    monkeypatch.setattr(asyncio,'create_subprocess_exec',blocked)


def attempt(n, ordinal=1, pin=None):
    return dict(attempt_id='offline-'+f'{n:032x}',ordinal=ordinal,
        prompt_sha256=pin or digest('prompt'),schema_sha256=digest('schema'))


def proof(row):
    return dict(**{k:v for k,v in row.items() if k!='ordinal'},event_sha256=digest('event'),
        elapsed_seconds=600,started_at='2026-11-14T00:00:00+00:00',ended_at='2026-11-14T00:10:00+00:00',
        worker_group_reaped=True,remote_completion_and_billing='UNOBSERVED',error='TRANSPORT_TIMEOUT')


def test_research_finalization_local_deadline():
    for stage, calls, total in (("VALIDATE",0,600),("RENDER",0,600),("MARKET",1,630),("CORE",4,2430)):
        plan = SimpleNamespace(slots=[SimpleNamespace(stage=stage)] * calls, validate=lambda: None)
        original = stage_deadline(plan, stage)
        split = _split_stage_deadline(original, 900)
        assert original["total_seconds"] == total
        assert split["local_seconds"] is None
        assert split["planned_calls"] == calls
        assert split["per_call_seconds"] == 600 and split["overhead_seconds"] == 30
        assert split["retries"] == 0


def test_exact_append_only_retry_rejects_replay_or_changed_input(tmp_path):
    path = tmp_path/'events.jsonl'
    journal = ModelInvocationJournal(path,plan_sha256=digest('p'),maximum=3,retry_cap=2)
    journal.transact('BIND',slot_id='s',scope=dict(slot_id='s',dependency_outputs={},stage='B2'))
    journal.transact('CONSUME',slot_id='s',attempt=attempt(1))
    journal.transact('TIMEOUT_CONFIRMED',slot_id='s',proof=proof(attempt(1)))
    before = path.read_bytes()
    for event, data in [('RETRY_ATTEMPT',dict(attempt=attempt(2,2,digest('changed')))),
                        ('ACCEPT',dict(attempt_id=attempt(1)['attempt_id'],output_sha256=digest('impostor')))]:
        with pytest.raises(ValueError):
            journal.transact(event,slot_id='s',**data)
        assert path.read_bytes()==before
    journal.transact('RETRY_ATTEMPT',slot_id='s',attempt=attempt(2,2))
    journal.transact('ACCEPT',slot_id='s',attempt_id=attempt(2)['attempt_id'],output_sha256=digest('accepted'))
    after = path.read_bytes()
    assert after.startswith(before)
    assert read_invocation_journal(after)['physical_calls']==2
    with pytest.raises(ValueError,match='acceptance'):
        journal.transact('ACCEPT',slot_id='s',attempt_id=attempt(2)['attempt_id'],output_sha256=digest('again'))
    journal.transact('STOP')
    with pytest.raises(ValueError,match='failed_cycle'):
        journal.transact('RETRY_ATTEMPT',slot_id='s',attempt=attempt(3,2))


def admitted_budget(tmp_path, plan, cap):
    now = datetime.now(timezone.utc)
    subjects = list(plan.cohort.market_subjects['us'])
    # Synthetic plan admission only. The original selected ledger still applies every event.
    from app.services.unified_stock_acquisition import UNIVERSE
    kr_fixture = UNIVERSE['kr'][0]
    d = registration.ApprovalDecision(event_id='OFFLINE_C22BF',approved=True,user_message_sha256=digest('fixture'),
        effective_at=now-timedelta(seconds=1),expires_at=now+timedelta(hours=1),subjects=tuple(subjects+[kr_fixture]))
    a = registration.record_backend_approval(d)
    ledger = SelectedRunLedger(path=tmp_path/'campaign.jsonl',approval=a,master_id='OFFLINE_C22BF',
        children=dict(us=dict(generation=plan.cohort.source_generation,subjects=subjects),
            kr=dict(generation='UNUSED',subjects=[kr_fixture])),provider_caps={},max_http=0,
        max_models=len(plan.slots)+cap,database_identity=dict(path='offline-fixture',device=0,inode=0),
        staged_markets=True,runtime_cap=dict(endpoints={'fixture':[]}),wallclock_seconds_max=3600,timeout_retry_cap=cap)
    # Admit synthetic prepared input; no registration query or capture of live data.
    original = ledger._apply
    def apply(state,event,record):
        if event=='OPEN':
            state.update(active_markets=['us'],sources={'us':digest('test-owner')})
        return original(state,event,record)
    ledger._apply = apply
    ledger._event('MODEL_PLAN',market='us',sha256=plan.sha256, slots=len(plan.slots),
        slot_ids=[s.slot_id for s in plan.slots],slot_stages={s.slot_id:s.stage for s in plan.slots})
    runtime = tmp_path/'runtime'
    journal = runtime/'invocation-ledger'/plan.cohort.run_id/'events.jsonl'
    budget = SolHighCallBudget(plan=plan,approved_max_invocations=len(plan.slots)+cap,
        approved_plan_sha256=plan.sha256,journal_path=journal,run_ledger=ledger,timeout_retry_cap=cap)
    return budget,runtime


def listed_plan(subjects, *, run='OFFLINE_C22BF_US', source='TOY_SOURCE_GENERATION',
                assessment='2026-11-10', at='2026-11-11T00:00:00+00:00'):
    from app.services.model_execution_plan import CohortSubject

    cohort = FrozenCohort(run,source,assessment,at,at,
        tuple(CohortSubject('us',t,'OFFLINE:'+t,at,digest(t)) for t in subjects), (('us',digest('owner')),),digest('scope'))
    return compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')


class FixtureWorker:
    returncode = 0
    pid = 987654321

    def __init__(self, result, recorded):
        self.result,self.recorded = result,recorded

    async def communicate(self, raw):
        frame = json.loads(raw)
        request = request_from_frame(frame)
        assert request.observe_timeout
        folder = Path(frame['directory'])
        auth = json.loads((folder/'production-authorization.json').read_bytes())
        self.recorded.append(auth)
        if self.result in {'timeout','ambiguous','auth'}:
            if self.result=='auth':
                durable_json(folder/'transport-receipt.json',dict(status='FAIL',process_started=True,
                    error_code='MODEL_AUTHENTICATION_FAILED'),exclusive=True)
                return b'',b''
            events = b'{"type":"thread.started"}\n{"type":"turn.started"}\n'
            if self.result=='ambiguous':
                events += b'{"type":"turn.completed"}\n'
            (folder/'events.jsonl').write_bytes(events)
            flow = proof(auth['attempt'])
            durable_json(folder/'market-cli-dispatch.json',dict(timeout_seconds=600,sandbox='read-only',
                model='gpt-6.1-sol',effort='high',dispatched_at=flow['started_at']),exclusive=True)
            durable_json(folder/'market-cli-exit.json',dict(timed_out=True,process_started=True,cli_returncode=-9,
                event_scan_truncated=False,completed_turns=int(self.result=='ambiguous'),
                first_event='thread.started',last_event='turn.started',elapsed_seconds=600,
                ended_at=flow['ended_at']),exclusive=True)
            durable_json(folder/'transport-receipt.json',dict(status='FAIL',error_code='TRANSPORT_TIMEOUT',
                process_started=True,cli_returncode=-9),exclusive=True)
        else:
            inputs = folder/'approved-input'
            out = folder/'raw-output.json'
            if isinstance(self.result,bytes):
                out.write_bytes(self.result)
            elif self.result=='synthesize':
                await SyntheticModelProcess().communicate(raw)
                (folder/'transport-receipt.json').unlink()
            else:
                out.write_bytes(b'{}')
            from app.services.official_codex_shadow_transport_service import command_prefix
            transport = dict(execution_policy=asdict(SolHighWirePolicy()),request_id=frame['request_id'],
                command=[str(request.binding.executable),*command_prefix(SOL_HIGH_V1),'--output-schema',
                    str(inputs/'provider-wire-schema.json'),'-o',str(out),'-'],
                qualification_sha256=request.binding.qualification_sha256,prompt_sha256=request.prompt_sha256,
                schema_sha256=request.schema_sha256,model_plan_scope=request.model_plan_scope,transport_attempts=1)
            durable_json(folder/'transport-receipt.json',dict(status='PASS',transport=transport),exclusive=True)
        return b'',b''

    async def wait(self):
        return self.returncode


def transport(tmp_path, monkeypatch, budget, runtime, outcomes, recorded):
    old = invocation.__wrapped__(tmp_path,monkeypatch)
    binding = qualify_fixture(old)
    monkeypatch.setattr(FrozenCohort,'verify_source_owner',lambda *a:None)
    async def factory(*args,**kwargs):
        return FixtureWorker(next(outcomes),recorded)
    model = OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(binding),default=str)),
        runtime_root=runtime,execution_profile=SOL_HIGH_V1,call_budget=budget,worker_factory=factory)
    model.bind_cycle(market='us',run_id=budget.plan.cohort.run_id)
    return model


@pytest.mark.parametrize('outcomes, count, failure',[
    (['pass'],1,None),(['timeout','pass'],2,None),
    (['ambiguous'],1,'RECONCILIATION_REQUIRED'),(['auth'],1,'MODEL_AUTHENTICATION_FAILED')])
def test_worker_qualified_timeout_only(tmp_path,monkeypatch,outcomes,count,failure):
    from app.services import research_no_send_run as research
    from app.services import model_timeout_retry as proof_module
    def gone(*args):
        raise ProcessLookupError
    monkeypatch.setattr(proof_module.os,'killpg',gone)
    timer = SimpleNamespace(check=lambda:None,switch=lambda phase:None,deadline={'overhead_seconds':30})
    monkeypatch.setattr(research,'current_stage_timer',lambda:timer)
    plan = listed_plan(['IBM'])
    budget,runtime = admitted_budget(tmp_path,plan,2)
    calls = []
    model = transport(tmp_path,monkeypatch,budget,runtime,iter(outcomes),calls)
    slot = plan.slots[0]
    row = req(plan,slot)
    row['payload']['prompt'] += '\nFROZEN_CONTEXT:\n{}'
    row['payload_sha256'] = digest(row['payload'])
    scope = budget.bind_stage(slot.stage,row)
    request = model.request(row['payload'],model=SOL_HIGH_V1.model,effort='high',timeout=600,
        stage=slot.stage,slot_scope=scope)
    if failure:
        with pytest.raises(ModelTransportError,match=failure):
            asyncio.run(request)
        assert budget.run_ledger.state()['pending']
        budget.stop()
        assert budget.run_ledger.state()['state']=='STOPPED_NO_SEND'
    else:
        raw = asyncio.run(request)
        budget.record_acceptance(slot.slot_id,payload_sha256=row['payload_sha256'],output_sha256=sha256_bytes(raw))
        assert len(budget.accepted)==1
    assert len(calls)==budget.physical_calls==budget.run_ledger.state()['model_total']==count
    if count==2:
        assert calls[0]['request_id'] != calls[1]['request_id']
        assert all(calls[0][k]==calls[1][k] for k in ('slot_scope','prompt_sha256','schema_sha256'))
        assert budget.retry_used==1 and not budget.run_ledger.state()['pending']


def test_b2_cap_exhausted_is_local_shared_stage_timeout_is_not(tmp_path):
    path = tmp_path/'events.jsonl'
    journal = ModelInvocationJournal(path,plan_sha256=digest('p'),maximum=7,retry_cap=2)
    for n, slot in enumerate(('one','two','three','four'),1):
        journal.transact('BIND',slot_id=slot,scope=dict(slot_id=slot,dependency_outputs={},stage='B2'))
        first = attempt(10*n)
        journal.transact('CONSUME',slot_id=slot,attempt=first)
        if n==4:
            journal.transact('ACCEPT',slot_id=slot,attempt_id=first['attempt_id'],output_sha256=digest('success'))
            continue
        journal.transact('TIMEOUT_CONFIRMED',slot_id=slot,proof=proof(first))
        retry = attempt(10*n+1,2)
        if n<3:
            journal.transact('RETRY_ATTEMPT',slot_id=slot,attempt=retry)
            journal.transact('TIMEOUT_CONFIRMED',slot_id=slot,proof=proof(retry))
        else:
            with pytest.raises(ValueError,match='retry_unavailable'):
                journal.transact('RETRY_ATTEMPT',slot_id=slot,attempt=retry)
        journal.transact('RETRY_EXHAUSTED',slot_id=slot)
    journal.transact('BIND',slot_id='shared',scope=dict(slot_id='shared',dependency_outputs={},stage='CORE'))
    journal.transact('CONSUME',slot_id='shared',attempt=attempt(50))
    journal.transact('TIMEOUT_CONFIRMED',slot_id='shared',proof=proof(attempt(50)))
    with pytest.raises(ValueError,match='exhaustion_unproven'):
        journal.transact('RETRY_EXHAUSTED',slot_id='shared')
    state = read_invocation_journal(path.read_bytes())
    assert state['physical_calls']==7 and state['retry_used']==2 and state['exhausted']=={'one','two','three'}
    assert set(state['accepted'])=={'four'}


def test_us10_partial_with_original_b2_and_renderer(tmp_path,monkeypatch):
    from app.services.research_request_storage import load_stage_request
    from app.services.research_no_send_run import PreparedResearchEnvelope
    from app.services import production_message_renderer as render
    from app.services import new_buyer_request_owner as b2
    from app.services import model_timeout_retry as timeout
    from tests.test_newbuyer_b2_v2 import inputs as b2_inputs
    from tests.test_r9_rev7_detailed_renderer import inputs as detailed_inputs
    from tests.test_m12ds_r4_r1_production_calibration import plan_for
    from tests.test_production_b2_execution import body
    from scripts import newbuyer_b2_contract as b1
    from scripts import kis_eps_wire_calibration as sealed

    workspace = Path(__file__).resolve().parents[3]
    old = workspace/'maintenance/20261114-c22be-v1/private-live/no-send/C22BE_V1_APPROVED_20261114T053619Z_US'
    if not (old/'market/request.json').is_file():
        pytest.skip('Local closed MARKET fixture is not distributed')
    # Only the Market renderer consumes dated Market evidence; cloned stock fixtures
    # own their own synthetic identities and never reuse a closed economic Owner.
    original_market = load_stage_request(old/'market/request.json')['snapshot']['collection']['monitoring_input']['markets']['us']
    market_output = json.loads((old/'market/response.json').read_bytes())['output']['rows'][0]['output']
    from app.services.unified_stock_acquisition import UNIVERSE
    subjects = tuple(sorted(UNIVERSE['us']))[:10]
    plan = listed_plan(subjects,run='exec-one',source='source-one')
    budget,runtime = admitted_budget(tmp_path,plan,2)
    envelope = PreparedResearchEnvelope(generation_id=plan.cohort.run_id,subjects=subjects)
    packets, stocks, cores, pa, pb, requests, accepted = {},{},{},{},{},{},{}
    for ticker in subjects:
        setup = detailed_inputs.__wrapped__()
        packet = setup['packet'].model_copy(update={'ticker':ticker})
        src = setup['source_stock']
        src.update(ticker=ticker,evidence_packet=packet.model_dump(mode='json'))
        src['packet']['stocks'][0]['ticker']=ticker
        src['packet']['stocks'][0]['fact_catalog'][0]['ticker']=ticker
        src['packet_sha256']=digest(src['packet'])
        fact = src['packet']['stocks'][0]['fact_catalog'][0]
        src['source_graph'][fact['fact_id']]['fact_sha256']=digest(fact)
        from app.services.numeric_semantic_registry import build_numeric_registry
        src['packet']['stocks'][0]['numeric_registry']=build_numeric_registry([fact])
        src['packet_sha256']=digest(src['packet'])
        src['valuation_view']['ticker']=ticker
        baseline = plan_for(packet)
        a = dict(setup['pass_a'],ticker=ticker)
        core = setup['core']
        provenance = dict(core_sha256=digest(core),pass_a_sha256=digest(a),pass_b_sha256=digest(baseline.decision),
            pass_b_input_sha256=digest('test B'),fresh_stock_sha256=digest(src))
        receipt = dict(baseline.acceptance,stage_provenance_sha256=digest(provenance))
        from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan
        accepted[ticker] = AcceptedDetailedCalibrationPlan(**dict(baseline.model_dump(mode='json'),
            stage_provenance=provenance,acceptance=receipt,acceptance_sha256=digest(receipt)))
        data = b2_inputs(legacy=False)
        sub = data['v1_request']['subject']
        sub.update(ticker=ticker,security_id='OFFLINE:'+ticker,source_generation_id='source-one',
            frozen_authority={'core':digest(core),'pass_a':digest(a),'accepted_b':digest(baseline.decision),'context':digest('test')})
        sub['tactical_catalog'][0].update(ticker=ticker,security_id='OFFLINE:'+ticker)
        for fact in sub['facts'].values():
            fact.update(ticker=ticker,security_id='OFFLINE:'+ticker)
        data['v1_request']['output_schema']=b1.output_schema(sub)
        data['v1_request']['request_sha256']=digest({k:v for k,v in data['v1_request'].items() if k!='request_sha256'})
        coverage_row = dict(data['coverage']['rows'][0],ticker=ticker,canonical_security_id='OFFLINE:'+ticker,
            source_generation='source-one')
        coverage_row.pop('receipt_sha256')
        coverage_row = sealed.sealed(coverage_row)
        data['coverage'].pop('receipt_sha256')
        data['coverage']=sealed.sealed(dict(data['coverage'],rows=[coverage_row]))
        from scripts.newbuyer_fper_prerequisite_scope import blocker_census
        data['census']=blocker_census([coverage_row],expected_subjects=[ticker])
        data.update(coverage_sha=data['coverage']['receipt_sha256'],census_sha=data['census']['receipt_sha256'])
        requests[ticker]=b2.build_request(**data)
        packets[ticker],stocks[ticker],cores[ticker],pa[ticker],pb[ticker]=packet,src,core,a,baseline.decision
    monkeypatch.setattr(render,'stock_plan',lambda session,ticker,packet:accepted[ticker])
    def gone(*args):
        raise ProcessLookupError
    monkeypatch.setattr(timeout.os,'killpg',gone)
    calls = []
    model = transport(tmp_path,monkeypatch,budget,runtime,
        iter([*([b'{}']*13),'timeout','timeout',*(body(requests[t]) for t in subjects[1:])]),calls)
    bridge = object.__new__(PreparedResearchBridge)
    source = dict(source_generation_id=plan.cohort.source_generation)
    fixture_owner = SimpleNamespace(source=lambda market:source)
    bridge.child = SimpleNamespace(plan=plan,owner=fixture_owner,market='us')
    bridge.execution_profile = SOL_HIGH_V1
    bridge._native_owner_parents = {}
    bridge._retained_kr_ecos_body = None
    bridge.model = model
    model.cohort_source_owner = fixture_owner
    bridge.child_binding = dict(plan_sha256=plan.sha256,cohort_sha256=plan.cohort.sha256,market='us',
        run_id=plan.cohort.run_id,source_generation=plan.cohort.source_generation,assessment_date=plan.cohort.assessment_date,
        cutoff=plan.cohort.cutoff,message_ids=['MARKET_US',*subjects])
    snapshot = dict(child_binding=bridge.child_binding,collection=dict(market='us',
        production_envelope=envelope.model_dump(mode='json'),monitoring_input=source))
    bridge.snapshot = lambda:snapshot
    # Upstream stage generation/acceptance is fixture-only. Exercise the original
    # B2 request authorization, schema/semantic validation and both renderers.
    def session(request,directory):
        stage = request['stage']
        values = SimpleNamespace(market='us',gen=plan.cohort.run_id,source_gen=plan.cohort.source_generation,
            projected={'us':original_market},markets={'us':market_output},fresh_stocks=stocks,
            cores=cores,arows=pa,brows=pb,b2_request=lambda t:requests[t],verify_model_build=lambda *a:None,
            accept=lambda *a:None,build=lambda s:[dict(req(plan,z),batch=1 if s=='MARKET' else z.batch_id)
                for z in plan.slots if z.stage==s])
        if stage in {'MARKET','CORE','A','B'}:
            build = values.build
            def build_with_prompt(s):
                rows = build(s)
                for row in rows:
                    row['payload']['prompt']+='\nFROZEN_CONTEXT:\n{}'
                    row['payload_sha256']=digest(row['payload'])
                return rows
            values.build=build_with_prompt
        return values,SimpleNamespace(production_envelope=envelope)
    bridge._session = session
    result = asyncio.run(run_prepared_research(bridge,root=tmp_path/'preview',enabled=True,
        split_model_timing=True,multi_batch_local_seconds=900))
    assert result['status']==PARTIAL, result.get('error_chain')
    assert result['expected_message_count']==11 and len(result['messages'])==10
    assert len(calls)==24 and budget.retry_used==1 and len(budget.accepted)==22
    assert list(result['unissued'])==list(calls[13]['slot_scope']['subjects'])
    assert 'MARKET_US' in {m['message_id'] for m in result['messages']}
    cycle = tmp_path/'preview'/plan.cohort.run_id
    fixture_plan = tmp_path/'plan.json'
    fixture_plan.write_text(json.dumps(plan.to_dict()))
    cold = """import json,socket,sqlite3,sys
from pathlib import Path
from app.services.model_execution_plan import ModelExecutionPlan
from app.services.model_timeout_retry import read_no_send_partition
def deny(*a,**k):raise AssertionError('cold database or network')
socket.socket.connect=socket.socket.connect_ex=sqlite3.connect=deny
p,c,j=map(Path,sys.argv[1:])
print(json.dumps(read_no_send_partition(c,plan=ModelExecutionPlan.from_dict(json.loads(p.read_bytes())),invocation_journal=j)))
"""
    child = subprocess.run([sys.executable,'-B','-c',cold,str(fixture_plan),str(cycle),str(budget.journal.path)],
        capture_output=True,text=True,cwd=Path(__file__).resolve().parents[1],check=True)
    readback = json.loads(child.stdout)
    assert (readback['count'],readback['expected'],readback['physical_attempts'])==(10,11,24)
    assert readback['message_sha256']=={row['message_id']:digest(row) for row in result['messages']}
    assert not (cycle/'b2'/next(iter(result['unissued']))/'accepted.json').exists()
