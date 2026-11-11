"""Changed lifecycle boundaries only; synthetic DB/wires, never real-call proof."""
import asyncio
import sqlite3
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services import prospective_class_c_owner as registration
from app.services import scoped_monitoring_research as scoped
from app.services.selected_source_registration import database_target, capture_approved_markets
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_snapshot_contract import digest
from tests.test_minimal_class_c_export import database, POLICY


def registered(tmp_path, us='NEWUS', source_identity=False):
    permission = database(tmp_path, [(us,'us'), ('999999','kr')])
    if source_identity:
        with sqlite3.connect(permission.database) as db:
            db.execute('UPDATE securitymaster SET canonical_security_id=? WHERE ticker=?', ('security-'+us,us))
    now = datetime.now(timezone.utc)
    decision = registration.ApprovalDecision(event_id='SYNTHETIC_ONE_EVENT', approved=True,
        user_message_sha256=digest('synthetic only'), effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(hours=3), subjects=permission.subjects)
    approval = registration.record_backend_approval(decision)
    settings = SimpleNamespace(database_url='sqlite:///'+str(permission.database))
    path, dev, ino = database_target(settings, runtime_directory=tmp_path)
    children = dict(us=dict(generation='US_CHILD',subjects=[us]),
        kr=dict(generation='KR_CHILD',subjects=['999999']))
    ledger = SelectedRunLedger(path=tmp_path/'run.jsonl', approval=approval, master_id='MASTER',
        children=children, provider_caps={'kiwoom':2}, max_http=2, max_models=10,
        database_identity=dict(path=str(path),device=dev,inode=ino))
    return settings, approval, decision, ledger


def capture(tmp_path, us='NEWUS', source_identity=False):
    settings, approval, decision, ledger = registered(tmp_path, us, source_identity)
    result = capture_approved_markets(settings=settings, runtime_directory=tmp_path,
        approval=approval, generations=dict(us='US_CHILD',kr='KR_CHILD'), policy=POLICY,
        ledger=ledger, enabled=True)
    return settings, approval, decision, ledger, result


def test_one_actual_capture_two_original_owners_and_five_selects(tmp_path):
    _, _, _, ledger, (_, owners, receipt) = capture(tmp_path)
    assert ledger.state()['state']=='REGISTRATION_CAPTURED'
    assert ledger.state()['db_select_actual']==5 and receipt['query_only'] and receipt['total_changes']==0
    assert len({id(x) for x in owners.values()})==2
    for market, owner in owners.items():
        _, row=registration._state(owner)
        assert row['approval_event']=='SYNTHETIC_ONE_EVENT'
        assert row['generation_id']==market.upper()+'_CHILD'
        assert len(row['bindings'])==1
    assert 'selected private' not in ledger.path.read_text()


def test_repeat_capture_and_wrong_database_denied_before_connection(tmp_path):
    settings, approval, _, ledger, _=capture(tmp_path)
    calls=[]
    with pytest.raises(ValueError,match='already_attempted'):
        capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
            generations=dict(us='US_CHILD',kr='KR_CHILD'),policy=POLICY,ledger=ledger,enabled=True,
            connect=lambda *a,**k:calls.append(1))
    assert calls==[] and ledger.state()['db_select_actual']==5
    (tmp_path/'other').mkdir()
    with pytest.raises(ValueError,match='database_frozen_scope'):
        ledger.before_registration(approval=approval,permission=database(tmp_path/'other',[('X','us')]),generations={})


def admitted_source(tmp_path, monkeypatch):
    # Exercise actual Stock/financial/preflight + original sealed Market kernel.
    # Only projector selection is injected for this dated synthetic fixture;
    # it does NOT prove current Selected build_inputs or a live 4-panel run.
    from tests.rev8_source_fixtures import fresh_inputs, POLICY as SOURCE_POLICY
    from tests.rev10_source_fixtures import wire_clock
    from tests.rev28_native_fixtures import native_input
    from tests.test_unified_stock_acquisition import plan as plan_fixture
    from tests.test_reported_business_native_projection import window
    from tests.test_r2b_r5_market_adapter import fixture
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from app.services.canonical_source_inputs import fresh_authority_inputs
    from scripts.m12dr_financial_source_authority import build_source_authority
    from scripts.r2b_r5_market_adapter import project_sealed_market_context
    from app.services.unified_source_policy import UnifiedSourcePolicy
    from app.services.provider_valuation_calibration_context import calibration_context
    settings, approval, decision, ledger, (_, owners, _) = capture(tmp_path, 'MU', True)
    p=plan_fixture.__wrapped__().model_copy(update={'run_id':'US_CHILD'})
    policy=UnifiedSourcePolicy(SOURCE_POLICY.allowed_providers|frozenset({'finnhub','kiwoom_rest'}))
    with wire_clock(p.frozen_at+timedelta(seconds=4)):
        inputs=fresh_inputs(tmp_path/'wire','MU',verified_identity=True,plan=p,policy=policy)
    inputs.update(reported_comparison_business=True,source_window=window(p))
    inputs['valuation_inputs']=native_input(inputs['financial_inputs']['plan']['security'],
        start=p.frozen_at,run=p.run_id,policy=policy)
    stock=assemble_fresh_stock(**inputs)
    packet, seed, graph=fixture('us',run=p.run_id)
    from tests.night_owner_fixtures import night_fixture
    night=night_fixture((p.frozen_at+timedelta(seconds=1)).isoformat(),run=p.run_id)
    market_source=graph['markets']['us']
    market_source['component']['original_source_time']=(p.frozen_at+timedelta(seconds=5)).isoformat()
    market_source['cutoff']=(p.frozen_at+timedelta(seconds=9)).isoformat()
    seed.update(started_at=p.frozen_at.isoformat(),run_acquisitions=dict(night=night['value_sha256']))
    seed['attempt_hashes']['us']=digest(market_source)
    graph.update(night=night,run_seed_sha256=digest(seed))
    packet.update(market_sources=deepcopy(market_source),night_and_publication_context=night,run_seed_sha256=digest(seed))
    for name, doc in packet['publication_context'].items():
        role=name.removeprefix('class-c/').removesuffix('.json')
        projection=dict(contract='unified-class-c-owner-projection-v1',role=role,
            eligible=False,values=[],records=[],version=digest([]),
            denials=[dict(reason='SYNTHETIC_EMPTY_PERSISTED_PUBLICATION')])
        projection['projection_sha256']=digest(projection)
        doc['projection']=projection
    graph['publication_context']=deepcopy(packet['publication_context'])
    graph['stocks']={'MU':build_source_authority(**fresh_authority_inputs(stock,inputs))}
    packet.update(stocks={'MU':stock},authority_graph_sha256=digest(graph))
    whole=dict(packets={'us':packet},seed=seed,authority_graph=graph,authority_graph_sha256=digest(graph))
    monkeypatch.setattr(scoped,'project_production_market_context',project_sealed_market_context)
    source, owner, cohort=scoped.prepare_scoped_research_source(enabled=True,market='us',subjects=('MU',),
        registration_owner=owners['us'],whole=whole,local_seeds={'MU':inputs['technical_inputs']['local_seed']},
        valuation_contexts={'MU':calibration_context(stock['valuation_view'])},generation=p.run_id,
        coverage=None,census=None)
    return source,owner,cohort,owners['us'],ledger,decision


def test_admitted_read_61_121_minutes_but_original_registration_expires(tmp_path,monkeypatch):
    source,owner,cohort,raw_owner,ledger,decision=admitted_source(tmp_path,monkeypatch)
    before=(digest(owner.source('us')),digest(owner.relationship('us')),digest(owner.acceptance()))
    assert source['prepared']['MU']['mode']=='EVIDENCE_BASED'
    cutoff=datetime.fromisoformat(registration._state(raw_owner)[1]['cutoff'])
    for minutes in (61,121):
        monkeypatch.setattr(registration,'_now',lambda:cutoff+timedelta(minutes=minutes))
        with pytest.raises(ValueError,match='owner_expired'):registration._state(raw_owner)
        cohort.verify_source_owner(owner)
        assert before==(digest(owner.source('us')),digest(owner.relationship('us')),digest(owner.acceptance()))
    monkeypatch.setattr(registration,'_now',lambda:decision.expires_at)
    with pytest.raises(ValueError,match='approval_expired'):
        ledger.before_http(market='us',provider='kiwoom',logical_id='new',plan_sha256=digest('p'))
    assert digest(owner.source('us'))==before[0]
    ledger.stop('SYNTHETIC_OPERATOR_STOP')
    assert digest(owner.source('us'))==before[0]
    owner.close()
    with pytest.raises(ValueError,match='live_source_owner'):owner.source('us')


def test_admitted_source_rehashed_or_generation_change_still_rejected(tmp_path,monkeypatch):
    _,owner,_,_,_,_=admitted_source(tmp_path,monkeypatch)
    from app.services.canonical_native_source_owner import _OWNERS
    row=_OWNERS[owner]
    row['acceptance']['generation_id']='OTHER'
    with pytest.raises(ValueError,match='admitted_source_drift'):owner.source('us')
    row['acceptance']=scoped._acceptance(row)
    row['source']['stocks']['MU']['packet_sha256']='0'*64
    with pytest.raises(ValueError,match='source_content_drift'):owner.source('us')


def test_shared_physical_intents_restart_duplicate_parallel_stop_and_caps(tmp_path):
    _,approval,_,ledger,(_,_,_)=capture(tmp_path)
    for m in ('us','kr'):ledger._event('PLAN',market=m,sha256=digest(m))
    key=ledger.before_http(market='us',provider='kiwoom',logical_id='auth',plan_sha256=digest('us'))
    with pytest.raises(ValueError,match='duplicate_or_parallel'):
        ledger.before_http(market='kr',provider='kiwoom',logical_id='one',plan_sha256=digest('kr'))
    ledger.result(key,ok=True)
    restored=SelectedRunLedger(path=ledger.path,approval=approval,master_id='MASTER',
        children=ledger.identity['children'],provider_caps={'kiwoom':2},max_http=2,max_models=10,
        database_identity=ledger.identity['database_identity'])
    with pytest.raises(ValueError,match='duplicate_or_parallel'):
        restored.before_http(market='us',provider='kiwoom',logical_id='auth',plan_sha256=digest('us'))
    key=restored.before_http(market='kr',provider='kiwoom',logical_id='one',plan_sha256=digest('kr'))
    restored.result(key,ok=True)
    with pytest.raises(ValueError,match='scope_or_budget'):
        restored.before_http(market='kr',provider='kiwoom',logical_id='two',plan_sha256=digest('kr'))
    restored.stop('SYNTHETIC_STOP')
    assert ledger.state()['http_total']==2 and ledger.state()['state']=='STOPPED_NO_SEND'


def test_preopen_python_repair_keeps_one_reserved_connection_and_never_retries_db(tmp_path):
    from app.services.minimal_class_c_export import ExportPermission
    settings,approval,_,ledger=registered(tmp_path)
    target=ledger.identity['database_identity']
    from pathlib import Path
    p=ExportPermission('SYNTHETIC_ONE_EVENT',True,Path(target['path']),target['device'],target['inode'],('NEWUS','999999'))
    ledger.before_registration(approval=approval,permission=p,generations=dict(us='US_CHILD',kr='KR_CHILD'))
    ledger.stop('SYNTHETIC_PREOPEN_TYPEERROR')
    ledger.correct_preopen_wiring(evidence_sha256=digest('no connect occurred'),observed_connections=0,observed_selects=0)
    capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
        generations=dict(us='US_CHILD',kr='KR_CHILD'),policy=POLICY,ledger=ledger,enabled=True)
    state=ledger.state()
    assert state['db_connection_attempts']==1 and state['db_select_actual']==5 and state['db_select_reserved']==5
    ledger.stop('SYNTHETIC_POST_OPEN_FAILURE')
    with pytest.raises(ValueError,match='cannot_repair_consumed'):
        ledger.correct_preopen_wiring(evidence_sha256=digest('not permitted'),observed_connections=0,observed_selects=0)


def test_model_budget_uses_shared_expiry_gate_before_consumption(tmp_path,monkeypatch):
    # Ledger-only source events below are accounting preconditions, NOT Owner
    # issuance or evidence of a completed economic/four-message simulation.
    from tests.test_c22aa_research_boundaries import plan,req
    from app.services.production_model_profile import SolHighCallBudget
    _,_,decision,ledger,_=capture(tmp_path)
    p=plan(1)
    for m in ('us','kr'):ledger._event('PLAN',market=m,sha256=digest(m))
    for m in ('us','kr'):
        ledger.source_captured(m)
        ledger._event('SOURCE',market=m,sha256=digest('accounting fixture'))
    for m in ('us','kr'):
        ledger._event('MODEL_PLAN',market=m,sha256=p.sha256,slots=len(p.slots),slot_ids=[s.slot_id for s in p.slots])
    b=SolHighCallBudget(plan=p,approved_max_invocations=len(p.slots),approved_plan_sha256=p.sha256,
        journal_path=tmp_path/'model',run_ledger=ledger)
    r=req(p,p.slots[0]);slot=b.bind_stage('MARKET',r)
    b.consume(None,'MARKET',r['payload_sha256'],slot_scope=slot)
    b.record_acceptance(p.slots[0].slot_id,payload_sha256=r['payload_sha256'],output_sha256=digest('synthetic output'))
    r=req(p,p.slots[1]);slot=b.bind_stage('CORE',r)
    monkeypatch.setattr(registration,'_now',lambda:decision.expires_at)
    with pytest.raises(ValueError,match='approval_expired'):
        b.consume(None,'CORE',r['payload_sha256'],slot_scope=slot)
    assert b.state()['consumed']==1 and ledger.state()['model_total']==1


def test_original_owner_rejection_keeps_completed_capture_receipt_not_new_consent(tmp_path):
    settings,approval,_,ledger=registered(tmp_path)
    with sqlite3.connect(ledger.identity['database_identity']['path']) as db:
        db.execute("UPDATE watchlistitem SET active=0 WHERE ticker='NEWUS'")
    with pytest.raises(ValueError,match='subject_not_operator_authorized'):
        capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
            generations=dict(us='US_CHILD',kr='KR_CHILD'),policy=POLICY,ledger=ledger,enabled=True)
    s=ledger.state()
    assert s['state']=='STOPPED_NO_SEND' and s['db_connection_attempts']==1 and s['db_select_actual']==5
    assert s['registration']==digest(s['registration_receipt']) and s['registration_receipt']['query_only']
    assert s['http_total']==s['model_total']==0


def test_selected_wire_attempts_counted_before_mock_http_and_429_stops(tmp_path):
    # Physical callback integration only. Bypass of the constructor below is
    # explicitly a test double, NOT Worker/normalizer/Source Owner admission.
    import json
    import httpx
    from tests.test_c22ab_selected_source import compile_market
    from app.services.selected_source_dispatch import SelectedSourceDispatcher
    from app.services.unified_live_source_transport import SourceSafetyStop
    _,approval,_,old,_=capture(tmp_path)
    ledger=SelectedRunLedger(path=tmp_path/'wire-ledger',approval=approval,master_id='WIRE_MASTER',
        children=old.identity['children'],provider_caps={'fred':2},max_http=2,max_models=10,
        database_identity=old.identity['database_identity'])
    ledger._event('DB_INTENT')
    receipt=old.state()['registration_receipt']
    ledger.registration_captured(receipt)
    compiled,_,_=compile_market('us','NEWUS')
    plan=compiled['plan']
    ledger._event('PLAN',market='us',sha256=plan.plan_sha256)
    ledger._event('PLAN',market='kr',sha256=digest('not a real source plan'))
    wire=object.__new__(SelectedSourceDispatcher)
    wire.plan=plan;wire.admission={'test_double_only':True};wire.run_ledger=ledger
    wire._require_current=lambda:None
    wire._initialize(root=tmp_path/'dispatch',secrets=())
    descriptors=[d for d in plan.descriptors if d.provider=='fred'][:2]
    seen=[]
    def sender(request):
        assert ledger.state()['http_total']==len(seen)+1
        seen.append('MOCK_NOT_NETWORK')
        return httpx.Response(200 if len(seen)==1 else 429,json={'synthetic':True})
    async def run(d):
        v=json.loads(d.request_json)
        request=httpx.Request(v['method'],v['url'],headers=v['headers'],content=v['body'])
        def normalize(raw):
            return dict(value=json.loads(raw),source_period='SYNTHETIC',consumer_complete=True)
        normalize.identity=(d.normalizer,d.owner_sha256)
        return await wire.execute(d.logical_request_id,request,transport=httpx.MockTransport(sender),normalize=normalize)
    assert asyncio.run(run(descriptors[0]))['status']=='PASS'
    with pytest.raises(SourceSafetyStop):asyncio.run(run(descriptors[1]))
    assert len(seen)==2 and ledger.state()['http_total']==2 and ledger.state()['state']=='STOPPED_NO_SEND'


def test_no_send_failure_is_local_terminal_and_reentry_is_read_only(tmp_path):
    from tests.test_c22aa_research_boundaries import plan,budget
    from app.services.research_no_send_run import PreparedResearchBridge,MarketResearchChild,run_prepared_research,RESEARCH_STAGES
    from app.services.unified_runtime_v2 import STAGES
    b=budget(plan(),tmp_path/'model-journal')
    bridge=object.__new__(PreparedResearchBridge)
    bridge.child=MarketResearchChild(plan(),None)
    bridge.child_binding={'synthetic':'not a source grant'}
    bridge.model=SimpleNamespace(call_budget=b)
    calls=[]
    def stop():calls.append('SOURCE_REJECTED');raise ValueError('ORIGINAL_SOURCE_REJECTED')
    bridge.snapshot=stop
    result=asyncio.run(run_prepared_research(bridge,root=tmp_path/'cycle',enabled=True))
    assert result['status']=='FAILED_NO_SEND' and calls==['SOURCE_REJECTED'] and b.state()['consumed']==0
    assert not result['normal_messages_sent'] and not result['failure_notifications_sent']
    assert asyncio.run(run_prepared_research(bridge,root=tmp_path/'cycle',enabled=True))==result
    assert calls==['SOURCE_REJECTED'] and STAGES[-1]=='DELIVER' and 'DELIVER' not in RESEARCH_STAGES
