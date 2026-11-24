"""V8 changed boundary only. All Source/upstream inputs are synthetic fixtures."""
import ast
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import date
import json
from pathlib import Path
import socket
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from app.services.model_execution_plan import compile_model_plan, verify_mixed_render
from app.services.model_invocation_journal import read_invocation_journal
from app.services.model_timeout_retry import verify_render_partition
from app.services.production_model_profile import SolHighCallBudget
from app.services.research_no_send_run import PARTIAL, PreparedResearchBridge, PreparedResearchEnvelope, TERMINAL
from app.services.unified_market_run import UnifiedMarketRun, RunConfiguration
from app.services.unified_runtime_v2 import CONTRACT
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests import test_c22bf_timeout as old
from tests.test_c22aa_research_boundaries import req

WORKSPACE = Path('/Users/sskim/Documents/Codex/2026-07-04/the')
V7 = WORKSPACE/'maintenance/20261119-pr52-v7-b2-recovery-feasibility/TM_PR52_V7_B2_RECOVERY_FEASIBILITY_20261119_RESULT.zip'
CALLER = WORKSPACE/'maintenance/20261118-pr52-v3d-us1117/run_source_only.py'


@pytest.fixture(autouse=True)
def deny_live(monkeypatch):
    import sqlite3
    def denied(*args, **kwargs):
        raise AssertionError('V8 forbids network, DB, and real model workers')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket.socket, 'connect_ex', denied)
    monkeypatch.setattr(socket.socket, 'sendto', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', denied)


def fixture_run(tmp_path, monkeypatch, outcomes=(), *, cap=1, limited=True, subjects=None, market='us'):
    from app.services import production_message_renderer as render, model_timeout_retry as timeout
    from app.services import research_artifact_budget as artifacts
    from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan, AcceptedMarketCalibration
    from app.services.daily_digest_renderer import render_daily_digest
    from app.services.numeric_semantic_registry import build_numeric_registry
    from app.services.unified_stock_acquisition import UNIVERSE
    from scripts import newbuyer_b2_contract as b1, kis_eps_wire_calibration as sealed
    from tests.test_newbuyer_b2_v2 import inputs as b2_inputs
    from tests.test_r9_rev7_detailed_renderer import inputs as detailed_inputs
    from tests.test_m12ds_r4_r1_production_calibration import plan_for
    from tests.test_production_b2_execution import body
    from tests.test_m12ds_r4_r4_market_balance import source as market_source, catalog as market_catalog

    # These tiny synthetic model artifacts exercise retry/rendering, not disk
    # capacity. Keep the production guard and inject only this fixture's disk.
    statvfs = artifacts.os.statvfs
    def synthetic_disk(path):
        values = list(statvfs(path))
        blocks = max(values[4], (artifacts.FREE_GUARD+artifacts.WORK_CAP)//values[1]+1)
        values[4] = blocks
        return artifacts.os.statvfs_result(values)
    monkeypatch.setattr(artifacts.os,'statvfs',synthetic_disk)

    subjects = tuple(sorted(UNIVERSE[market] if subjects is None else subjects))
    if market == 'kr':
        from app.services.model_execution_plan import CohortSubject, FrozenCohort
        at = '2026-11-11T00:00:00+00:00'
        cohort = FrozenCohort('SYNTHETIC_C40_KR','source-one','2026-11-11',at,at,
            tuple(CohortSubject('kr',t,'OFFLINE:'+t,at,digest(t)) for t in subjects),
            (('kr',digest('test-owner')),),digest('scope'))
        base = compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
    else:
        base = old.listed_plan(subjects, run='SYNTHETIC_V8_US', source='source-one')
    plan = compile_model_plan(replace(base.cohort, limitation_subjects=('SKHY',) if limited else ()),
                              topology='CANONICAL_PRODUCTION')
    batches=(len(subjects)+2)//3
    b_batches=sum(bool(set(subjects[i:i+3])-set(plan.cohort.limitation_subjects)) for i in range(0,len(subjects),3))
    assert len(plan.slots) == 1+2*batches+b_batches+len(subjects)-len(plan.cohort.limitation_subjects)
    original = old.SelectedRunLedger
    def fresh_ledger(**kwargs):
        kwargs.update(provider_caps={'kiwoom':1}, max_http=1)
        return original(**kwargs)
    monkeypatch.setattr(old, 'SelectedRunLedger', fresh_ledger)
    budget, runtime = old.admitted_budget(tmp_path, plan, cap)
    packets, stocks, cores, pa, pb, requests, accepted = {}, {}, {}, {}, {}, {}, {}
    entry_contexts = {}
    ordinary = tuple(t for t in subjects if t not in plan.cohort.limitation_subjects)
    for ticker in ordinary:
        setup = detailed_inputs.__wrapped__()
        packet = setup['packet'].model_copy(update={'ticker':ticker,**({'market':'kr'} if market=='kr' else {})})
        src = setup['source_stock']
        if market == 'kr':
            from tests.test_kr_forward_valuation_integration import view
            from app.services.kr_forward_valuation_context import KrForwardValuationView, calibration_context
            forward = view(missing=True).model_dump(mode='json')
            quote = src['packet']['stocks'][0]['current_price_context']
            quote['currency'] = 'KRW'
            forward['native'].update(ticker=ticker,security_id='OFFLINE:'+ticker,run_id='source-one',
                price_session=quote['as_of_date'],price_context_sha256=digest(quote))
            forward['kis']['security_code'] = ticker
            forward = KrForwardValuationView.model_validate(forward)
            src['valuation_view'] = forward.native.model_dump(mode='json')
            src['packet']['stocks'][0]['current_price_context']['currency'] = 'KRW'
            src['packet']['stocks'][0]['fact_catalog'][0]['fields']['currency'] = 'KRW'
            src['fixture_forward'] = forward.model_dump(mode='json')
        src.update(ticker=ticker,evidence_packet=packet.model_dump(mode='json'))
        src['packet']['stocks'][0]['ticker'] = ticker
        src['packet']['stocks'][0]['chart_context'] = {}
        fact = src['packet']['stocks'][0]['fact_catalog'][0]
        fact['ticker'] = ticker
        src['source_graph'][fact['fact_id']]['fact_sha256'] = digest(fact)
        src['packet']['stocks'][0]['numeric_registry'] = build_numeric_registry([fact])
        src['packet_sha256'] = digest(src['packet'])
        src['valuation_view']['ticker'] = ticker
        baseline = plan_for(packet)
        a, core = dict(setup['pass_a'],ticker=ticker), setup['core']
        provenance = dict(core_sha256=digest(core),pass_a_sha256=digest(a),pass_b_sha256=digest(baseline.decision),
            pass_b_input_sha256=digest('synthetic B'),fresh_stock_sha256=digest(src))
        receipt = dict(baseline.acceptance,stage_provenance_sha256=digest(provenance),
                       execution_generation_id=plan.cohort.run_id)
        accepted[ticker] = AcceptedDetailedCalibrationPlan(**dict(baseline.model_dump(mode='json'),
            execution_generation_id=plan.cohort.run_id,stage_provenance=provenance,
            acceptance=receipt,acceptance_sha256=digest(receipt)))
        data = b2_inputs(legacy=False)
        sub = data['v1_request']['subject']
        entry_contexts[ticker] = dict(ticker=ticker,
            source_evidence_binding=dict(ticker=ticker,source_generation_id='source-one'),
            current_price=deepcopy(sub['current_price']), decision_evidence=[],
            source_use_projection=dict(source_permissions=[]),
            r2_eligible_range_catalog=dict(tactical_candidates=[]))
        sub.update(ticker=ticker,security_id='OFFLINE:'+ticker,source_generation_id='source-one',
            frozen_authority={'core':digest(core),'pass_a':digest(a),'accepted_b':digest(baseline.decision),
                              'context':digest(entry_contexts[ticker])})
        sub['tactical_catalog'][0].update(ticker=ticker,security_id='OFFLINE:'+ticker)
        for fact in sub['facts'].values():
            fact.update(ticker=ticker,security_id='OFFLINE:'+ticker)
        data['v1_request']['output_schema'] = b1.output_schema(sub)
        data['v1_request']['request_sha256'] = digest({k:v for k,v in data['v1_request'].items() if k!='request_sha256'})
        coverage = dict(data['coverage']['rows'][0],ticker=ticker,canonical_security_id='OFFLINE:'+ticker,
                        source_generation='source-one')
        coverage.pop('receipt_sha256')
        coverage = sealed.sealed(coverage)
        data['coverage'].pop('receipt_sha256')
        data['coverage'] = sealed.sealed(dict(data['coverage'],rows=[coverage]))
        from scripts.newbuyer_fper_prerequisite_scope import blocker_census
        data['census'] = blocker_census([coverage],expected_subjects=[ticker])
        data.update(coverage_sha=data['coverage']['receipt_sha256'],census_sha=data['census']['receipt_sha256'])
        from app.services.new_buyer_request_owner import build_request
        requests[ticker] = build_request(**data)
        packets[ticker],stocks[ticker],cores[ticker],pa[ticker],pb[ticker] = packet,src,core,a,baseline.decision
    monkeypatch.setattr(render,'stock_plan',lambda session,ticker,packet:accepted[ticker])
    monkeypatch.setattr(timeout.os,'killpg',lambda *args:(_ for _ in ()).throw(ProcessLookupError()))
    sequence = [b'{}']*sum(s.stage!='B2' for s in plan.slots)
    for ticker in ordinary:
        if ticker == 'TSM':
            sequence.extend(outcomes)
            if outcomes == ['timeout','timeout']:
                continue
        sequence.append(body(requests[ticker]))
    calls = []
    if not cap:
        class CapZeroWorker(old.FixtureWorker):
            async def communicate(self, raw):
                from dataclasses import asdict
                from app.services.production_model_profile import SolHighWirePolicy
                from app.services.production_model_transport import request_from_frame
                from app.services.official_codex_shadow_transport_service import command_prefix
                from app.services.unified_run_artifacts import durable_json
                frame = json.loads(raw)
                request = request_from_frame(frame)
                assert not request.observe_timeout
                folder = Path(frame['directory'])
                self.recorded.append(json.loads((folder/'production-authorization.json').read_bytes()))
                out, inputs = folder/'raw-output.json', folder/'approved-input'
                assert isinstance(self.result, bytes)
                out.write_bytes(self.result)
                proof = dict(execution_policy=asdict(SolHighWirePolicy()),request_id=frame['request_id'],
                    command=[str(request.binding.executable),*command_prefix(SOL_HIGH_V1),'--output-schema',
                        str(inputs/'provider-wire-schema.json'),'-o',str(out),'-'],
                    qualification_sha256=request.binding.qualification_sha256,prompt_sha256=request.prompt_sha256,
                    schema_sha256=request.schema_sha256,model_plan_scope=request.model_plan_scope,transport_attempts=1)
                durable_json(folder/'transport-receipt.json',dict(status='PASS',transport=proof),exclusive=True)
                return b'',b''
        monkeypatch.setattr(old,'FixtureWorker',CapZeroWorker)
    model = old.transport(tmp_path,monkeypatch,budget,runtime,iter(sequence),calls)
    bridge = object.__new__(PreparedResearchBridge)
    source = dict(source_generation_id='source-one')
    owner = SimpleNamespace(source=lambda market:source)
    bridge.child = SimpleNamespace(plan=plan,owner=owner,market=market,verify=lambda:None)
    bridge.execution_profile, bridge._native_owner_parents = SOL_HIGH_V1, {}
    bridge._retained_kr_ecos_body = None
    bridge.model = model
    model.cohort_source_owner = owner
    bridge.child_binding = dict(plan_sha256=plan.sha256,cohort_sha256=plan.cohort.sha256,market=market,
        run_id=plan.cohort.run_id,source_generation='source-one',assessment_date=plan.cohort.assessment_date,
        cutoff=plan.cohort.cutoff,message_ids=['MARKET_'+market.upper(),*subjects],
        **(dict(limitation_subjects=['SKHY']) if limited else {}))
    envelope = PreparedResearchEnvelope(generation_id=plan.cohort.run_id,subjects=subjects)
    if market == 'kr':
        source['forward_views'] = {t:s['fixture_forward'] for t,s in stocks.items()}
    snapshot = dict(child_binding=bridge.child_binding,collection=dict(market=market,
        production_envelope=envelope.model_dump(mode='json'),monitoring_input=source))
    bridge.snapshot = lambda:snapshot
    decision = dict(status='UNKNOWN_LIMIT',fixture='existing limitation output, not economic revalidation')
    limited_message = dict(message_id='SKHY',generation_id=plan.cohort.run_id,
        decision_mode='UNKNOWN_LIMIT',text='SKHY: 자료 제한으로 방향 판단을 발행하지 않습니다.',
        plan_sha256=digest('preaccepted synthetic limitation plan'),limitation_decision_sha256=digest(decision))
    monkeypatch.setattr(render,'limitation_message',lambda session,ticker:dict(limited_message))
    market_context = market_source()
    market_context['session']['market'] = market
    market_decision = dict(market=market.upper(),regime='MIXED',confidence='MEDIUM',breadth_state='Market breadth is mixed.',
        leadership='Leadership is selective.',flows_or_participation='Participation is mixed.',
        rates_or_macro_context='Macro context remains mixed.')
    if market == 'kr':
        from app.services.market_numeric_claim_service import numeric_catalog
        catalog = numeric_catalog(market_context,market='kr',assessment_date='2026-09-22',
            eligible_refs=[f['fact_id'] for f in market_context['fact_catalog']])
    else:
        catalog = market_catalog(market_context)
    market_receipt = dict(status='PASS',errors=[],market=market,assessment_date='2026-09-22',
        source_context_sha256=digest(market_context),decision_sha256=digest(market_decision),numeric_catalog_sha256=digest(catalog))
    market_plan = AcceptedMarketCalibration(market=market,assessment_date='2026-09-22',source_context=market_context,
        decision=market_decision,acceptance=market_receipt,acceptance_sha256=digest(market_receipt),numeric_catalog=catalog)
    bridge._render_market = lambda session:dict(message_id='MARKET_'+market.upper(),generation_id=plan.cohort.run_id,
        text=render_daily_digest(None,accepted_market=market_plan),plan_sha256=digest(market_plan.model_dump(mode='json')))
    def session(request,directory):
        def build(stage):
            result = []
            for slot in plan.slots:
                if slot.stage != stage:
                    continue
                row = req(plan,slot)
                row['payload']['prompt'] += '\nFROZEN_CONTEXT:\n{}'
                row['payload_sha256'] = digest(row['payload'])
                row['batch'] = 1 if stage=='MARKET' else slot.batch_id
                result.append(row)
            return result
        values = SimpleNamespace(market=market,gen=plan.cohort.run_id,source_gen='source-one',source=source,
            valuation_context=lambda ticker:calibration_context(source['forward_views'][ticker]),
            fresh_stocks=stocks,cores=cores,arows=pa,brows=pb,bctx=entry_contexts,b2_request=lambda t:requests[t],
            verify_model_build=lambda *args:None,accept=lambda *args:None,build=build,
            limitation_subjects=frozenset(plan.cohort.limitation_subjects),ordinary_subjects=lambda:ordinary,
            limitation_decision=lambda ticker:decision)
        return values,SimpleNamespace(production_envelope=envelope)
    bridge._session = session
    config = RunConfiguration(root=tmp_path/'preview',debug_destination=None,repo_commit='synthetic',
        scheduler_identity='synthetic',adapter_fingerprint=digest('fixture'),runtime_contract=CONTRACT,
        stage_timeout_seconds=600,collection_timeout_seconds=600)
    result = asyncio.run(UnifiedMarketRun(config,bridge).run(market,date(2026,11,11)))
    return SimpleNamespace(result=result,budget=budget,plan=plan,calls=calls,cycle=config.root/plan.cohort.run_id)


@pytest.mark.parametrize('outcomes,attempts,cap', [([],29,1),(['timeout'],30,1),([],29,0)])
def test_mixed_full_real_stage_render_chain(tmp_path,monkeypatch,outcomes,attempts,cap):
    fixture = fixture_run(tmp_path,monkeypatch,outcomes,cap=cap)
    result = fixture.result
    assert result['status'] == TERMINAL, result.get('error_chain')
    assert len(result['messages']) == 15 and digest(result['messages']) == result['messages_sha256']
    assert all(row['status']=='PASS' for row in result['stage_receipts'])
    assert [row['stage'] for row in result['stage_receipts']] == ['MARKET','CORE','A','B','B2','VALIDATE','RENDER']
    assert len(fixture.calls) == fixture.budget.physical_calls == attempts
    assert len(fixture.budget.accepted) == 29 and fixture.budget.retry_used == bool(outcomes)
    assert not any(call['slot_scope']['stage']=='B2' and call['slot_scope']['subjects']==['SKHY'] for call in fixture.calls)
    if outcomes:
        retry_calls = [call for call in fixture.calls if call['slot_scope']['subjects']==['TSM']]
        assert len(retry_calls)==2 and retry_calls[0]['request_id']!=retry_calls[1]['request_id']
        assert all(retry_calls[0][key]==retry_calls[1][key] for key in ('slot_scope','prompt_sha256','schema_sha256'))
    journal = read_invocation_journal(fixture.budget.journal.path.read_bytes())
    b2 = json.loads((fixture.cycle/'b2/response.json').read_bytes())['output']
    assert not b2.get('unissued')
    verify_render_partition(messages=result['messages'],subjects=fixture.plan.cohort.market_subjects['us'],
        slots=fixture.plan.slots,b2=b2,journal=journal,accepted_content_sha256=result['messages_sha256'],plan=fixture.plan)
    verify_mixed_render(fixture.plan,result['messages'],result['limitation_receipts'])
    if not outcomes and cap == 1:
        with ZipFile(V7) as archive:
            prior = ast.parse(archive.read('code/app/services/model_timeout_retry.py'))
        function = next(node for node in prior.body if isinstance(node,ast.FunctionDef) and node.name=='verify_render_partition')
        import app.services.model_timeout_retry as current
        namespace = {'verify_b2_coverage':current.verify_b2_coverage}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'V7-preserved-partition','exec'),namespace)
        args = dict(messages=result['messages'],subjects=fixture.plan.cohort.market_subjects['us'],
            slots=fixture.plan.slots,b2=b2,journal=journal,accepted_content_sha256=result['messages_sha256'])
        with pytest.raises(ValueError,match='production_partial_b2_original_coverage_gap'):
            namespace['verify_render_partition'](**args)
        for mutation in ('fake_SKHY_B2','fake_SKHY_omission','missing_message','duplicate_message','wrong_SHA','duplicate_slot'):
            changed = deepcopy(args)
            changed['plan'] = fixture.plan
            if mutation=='fake_SKHY_B2':
                changed['b2']['rows']['SKHY'] = {}
            elif mutation=='fake_SKHY_omission':
                changed['b2']['unissued'] = {'SKHY':{}}
            elif mutation=='missing_message':
                changed['messages'] = changed['messages'][1:]
                changed['accepted_content_sha256'] = digest(changed['messages'])
            elif mutation=='duplicate_message':
                changed['messages'].append(changed['messages'][0])
                changed['accepted_content_sha256'] = digest(changed['messages'])
            elif mutation=='duplicate_slot':
                changed['slots'] = (*fixture.plan.slots,fixture.plan.slots[-1])
            else:
                changed['accepted_content_sha256'] = digest('wrong message SHA')
            with pytest.raises(ValueError):
                verify_render_partition(**changed)


def test_mixed_retry_exhaustion_preserves_verified_partial_messages(tmp_path,monkeypatch):
    fixture = fixture_run(tmp_path,monkeypatch,['timeout','timeout'])
    result = fixture.result
    assert result['status']==PARTIAL, result.get('error_chain')
    assert fixture.budget.retry_used==1 and not fixture.budget.stopped
    assert len(result['messages'])==14 and result['expected_message_count']==15
    assert {m['message_id'] for m in result['messages']}==set(result['child_binding']['message_ids'])-{'TSM'}
    assert next(m for m in result['messages'] if m['message_id']=='SKHY')['decision_mode']=='UNKNOWN_LIMIT'
    assert all(m['NO_SEND'] is True for m in result['messages']) and result['normal_messages_sent'] is False
    assert (fixture.cycle/'render/response.json').exists()
    omitted = json.loads((fixture.cycle/'b2/TSM/unissued.json').read_bytes())
    assert omitted['status']=='B2_UNISSUED_TIMEOUT' and omitted['attempts']==2
    assert result['unissued']=={'TSM':omitted}
    assert not (fixture.cycle/'b2/TSM/accepted.json').exists()
    assert not (fixture.cycle/'b2/SKHY').exists()
    b2 = json.loads((fixture.cycle/'b2/response.json').read_bytes())['output']
    args = dict(messages=result['messages'],subjects=fixture.plan.cohort.market_subjects['us'],
        slots=fixture.plan.slots,b2=b2,journal=read_invocation_journal(fixture.budget.journal.path.read_bytes()),
        accepted_content_sha256=result['messages_sha256'],plan=fixture.plan)
    verify_render_partition(**args)
    verify_mixed_render(fixture.plan,result['messages'],result['limitation_receipts'],omitted=result['unissued'])
    for mutation in ('limited_omission','wrong_slot','one_timeout','missing_message','wrong_hash'):
        changed = deepcopy(args)
        if mutation=='limited_omission':
            changed['b2']['unissued']['SKHY'] = dict(omitted)
        elif mutation=='wrong_slot':
            changed['b2']['unissued']['TSM']['slot_id'] = 'not-the-original-slot'
        elif mutation=='one_timeout':
            changed['b2']['unissued']['TSM']['attempts'] = 1
        elif mutation=='missing_message':
            changed['messages'] = changed['messages'][1:]
            changed['accepted_content_sha256'] = digest(changed['messages'])
        else:
            changed['accepted_content_sha256'] = digest('changed content')
        with pytest.raises(ValueError):
            verify_render_partition(**changed)
    with pytest.raises(ValueError,match='model_render_mixed_census'):
        verify_mixed_render(fixture.plan,result['messages'],result['limitation_receipts'],omitted={'TSM','SKHY'})


def test_current_caller_shared_retry_wiring_is_default_off():
    tree = ast.parse(CALLER.read_bytes())
    function = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='approved_live_v2')
    constructors = [n for n in ast.walk(function) if isinstance(n,ast.Call)]
    ledger = next(n for n in constructors if isinstance(n.func,ast.Name) and n.func.id=='SelectedRunLedger')
    assert next(k.value.id for k in ledger.keywords if k.arg=='timeout_retry_cap')=='timeout_retry_cap'
    model = next(n for n in constructors if isinstance(n.func,ast.Name) and n.func.id=='dict'
        and any(k.arg=='approved_max_invocations' for k in n.keywords))
    assert next(k.value.id for k in model.keywords if k.arg=='timeout_retry_cap')=='timeout_retry_cap'
    expression = next(n.value for n in ast.walk(function) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='timeout_retry_cap' for t in n.targets))
    assert expression.orelse.value==0 and expression.body.args[1].value==0


@pytest.mark.parametrize('ledger_cap,model_cap', [(1,0),(0,1)])
def test_mismatched_retry_caps_rejected_before_journal(tmp_path,ledger_cap,model_cap):
    plan = old.listed_plan(['IBM'])
    ledger = SimpleNamespace(identity={'timeout_retry_cap':ledger_cap})
    with pytest.raises(ValueError,match='ledger_cap_mismatch'):
        SolHighCallBudget(plan=plan,approved_max_invocations=len(plan.slots)+1,approved_plan_sha256=plan.sha256,
            journal_path=tmp_path/'never',run_ledger=ledger,timeout_retry_cap=model_cap)
    assert not (tmp_path/'never').exists()


def test_non29_plan_cannot_spend_fixed30_retry_budget(tmp_path):
    from app.services.unified_stock_acquisition import UNIVERSE
    plan = old.listed_plan(UNIVERSE['us'])
    assert len(plan.slots)==30
    ledger = SimpleNamespace(identity={'timeout_retry_cap':1,'max_models':30})
    with pytest.raises(ValueError,match='approved_new_us_campaign'):
        SolHighCallBudget(plan=plan,approved_max_invocations=30,approved_plan_sha256=plan.sha256,
            journal_path=tmp_path/'never',run_ledger=ledger,timeout_retry_cap=1)
    assert not (tmp_path/'never').exists()


def test_nonmixed_partial_partition_and_old_STOP_remain_closed(tmp_path):
    from app.services.model_invocation_journal import ModelInvocationJournal
    from app.services.model_timeout_retry import verify_b2_coverage
    slots = [SimpleNamespace(stage='B2',subjects=(ticker,),slot_id=ticker) for ticker in ('IBM','MU')]
    omitted = dict(status='B2_UNISSUED_TIMEOUT',slot_id='MU',request_sha256=digest('MU'),attempts=2)
    output = dict(rows={'IBM':{}},unissued={'MU':omitted})
    verify_b2_coverage(output,subjects=('IBM','MU'),slots=slots,exhausted={'MU'},
        bound={'MU':dict(payload_sha256=digest('MU'))},attempts={'MU':[{},{}]})
    journal = ModelInvocationJournal(tmp_path/'synthetic-old-stop',plan_sha256=digest('old'),maximum=1)
    journal.transact('STOP')
    with pytest.raises(ValueError,match='failed_cycle'):
        journal.transact('BIND',slot_id='new',scope={})
    changed_plan = old.listed_plan(['IBM'],run='OTHER_GENERATION')
    with pytest.raises(ValueError):
        SolHighCallBudget(plan=changed_plan,approved_plan_sha256=digest('V6_PLAN_NOT_CURRENT'),
            approved_max_invocations=len(changed_plan.slots),journal_path=tmp_path/'not-authorized')


@pytest.mark.parametrize('expire', [False,True])
def test_retry_stage_timer_keeps_600s_calls_and_campaign_end(monkeypatch,expire):
    from app.services import research_no_send_run as research
    class Timeout:
        def __init__(self): self.value = None
        def reschedule(self,value): self.value = value
        def when(self): return self.value
    monkeypatch.setattr(asyncio,'timeout_at',lambda value:Timeout())
    loop = SimpleNamespace(tick=0.0)
    loop.time = lambda:loop.tick
    bound = dict(stage='B2',planned_calls=13,per_call_seconds=600,overhead_seconds=30,local_seconds=600)
    timer = research._StageTimer(bound,loop,1000 if expire else 16200,retry_cap=1)
    timer.timeout.reschedule(600)
    for ordinal in range(14):
        timer.switch('worker')
        assert timer.timeout.when() == min(loop.tick+630,timer.campaign_end)
        loop.tick += 600
        if expire and ordinal==1:
            with pytest.raises(TimeoutError,match='campaign_deadline'):
                timer.switch('local')
            return
        timer.switch('local')
    assert timer.calls==14 and timer.worker_seconds==8400 and timer.local_seconds==0
    with pytest.raises(ValueError,match='worker_count_exceeded'):
        timer.switch('worker')


@pytest.mark.parametrize('approved', [True,False])
def test_caller_new_directory_and_approval_gate_before_IO(tmp_path,approved):
    import runpy
    import sys
    from datetime import datetime,timedelta
    namespace = runpy.run_path(str(CALLER),run_name='offline_v8_caller')
    function = deepcopy(next(node for node in ast.parse(CALLER.read_bytes()).body
        if isinstance(node,ast.FunctionDef) and node.name=='approved_live_v2'))
    boundary = next(i for i,node in enumerate(function.body) if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Subscript) and isinstance(target.value,ast.Attribute)
            and isinstance(target.value.value,ast.Name) and target.value.value.id=='sys'
            and target.value.attr=='path' for target in node.targets))
    function.body = function.body[:boundary]
    namespace['MAINT'] = tmp_path
    directory = tmp_path/'fresh-campaign'
    directory.mkdir()
    now = datetime.now(namespace['KST'])
    parameters = dict(authorized_at=(now-timedelta(seconds=1)).isoformat(),expires_at=(now+timedelta(hours=1)).isoformat(),
        candidate_commit='f'*40,session='2026-11-18',manual_source_seconds=1800,mode='LIVE_NO_SEND',
        timeout_retry_cap=1,optional_news_429='SELECTED_US_OPTIONAL_NEWS_429_V1',approved=approved,
        concurrency_absent=True,max_http=710,max_models=30,provider_caps=namespace['CAPS'])
    namespace['read'] = lambda path:parameters
    namespace['subprocess'] = SimpleNamespace(check_output=lambda args,**kwargs:'f'*40 if args[-1]=='HEAD' else '')
    namespace['sys'] = SimpleNamespace(argv=['caller','approved-us-v5-no-send','--run-directory',str(directory)],
        prefix=sys.prefix,flags=SimpleNamespace(no_site=False))
    namespace['PY'] = Path(sys.prefix)/'bin/python'
    exec(compile(ast.Module(body=[function],type_ignores=[]),'actual-caller-pre-IO-prefix','exec'),namespace)
    if approved:
        namespace['approved_live_v2']()
        assert (directory/'private').is_dir()
    else:
        with pytest.raises(ValueError,match='NEW_EXPLICIT_SCOPE_REQUIRED'):
            namespace['approved_live_v2']()
        assert not (directory/'private').exists()
