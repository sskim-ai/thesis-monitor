"""Dynamic plan tests only. Toy cohorts and fake workers do not issue Source rights."""
import asyncio
from copy import deepcopy
from dataclasses import asdict, replace
import json
from types import SimpleNamespace

import pytest

from app.services.model_execution_plan import CohortSubject, FrozenCohort, ModelExecutionPlan, compile_model_plan
from app.services.production_model_profile import SolHighCallBudget
from app.services.production_model_transport import OfficialProductionModelTransport, request_from_frame
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from app.services import official_codex_shadow_transport_service as cli
from tests.test_c22y_sol_high_contract import qualify_fixture, fake_cli, OfflineWorker
from tests.test_official_codex_shadow_transport import invocation


def cohort(us=14, kr=8):
    rows = tuple(CohortSubject(m, f'{m.upper()}{i:03}', f'TOY_ONLY:{m}:{i}',
        '2026-11-11T00:00:00+00:00', digest([m, i]))
        for m, count in (('us', us), ('kr', kr)) for i in range(count))
    return FrozenCohort('OFFLINE_C22Z_ONLY', 'TOY_SOURCE_GENERATION', '2026-11-10',
        '2026-11-11T00:00:00+00:00', '2026-11-11T05:00:00+00:00', rows,
        tuple((m, digest(['original-owner-fixture', m])) for m, n in (('us', us), ('kr', kr)) if n),
        digest('NO_SEND_ONLY_OFFLINE'), planning_only=True)


def budget(plan, cap=None):
    return SolHighCallBudget(plan=plan, approved_max_invocations=len(plan.slots) if cap is None else cap,
        approved_plan_sha256=plan.sha256)


def request(plan, slot):
    context = {t: {'source_generation': plan.cohort.source_generation, 'price': 100} for t in slot.subjects}
    value = dict(prompt='Offline mock stage\nFROZEN_CONTEXT:\n'+json.dumps(context),
        input=context, response_schema={'type': 'object'})
    return dict(market=slot.market, batch=1 if slot.stage == 'MARKET' else slot.batch_id,
        subjects=list(slot.subjects), execution_generation_id=plan.cohort.run_id,
        source_generation_id=plan.cohort.source_generation, payload=value, payload_sha256=digest(value))


def accept_one(item, plan, slot):
    value = request(plan, slot)
    scope = item.bind_stage(slot.stage, value)
    item.consume(None, slot.stage, value['payload_sha256'], slot_scope=scope)
    item.record_acceptance(slot.slot_id, payload_sha256=value['payload_sha256'], output_sha256=digest(['accepted-fixture', slot.slot_id]))
    return scope


@pytest.mark.parametrize('us,kr,total', [(14,8,48),(15,8,49),(16,8,53),(13,8,47),(14,9,49),(14,10,53),(1,1,10),(2,0,6),(0,0,0)])
def test_dynamic_cost_registry_not_a_fixed_cap(us, kr, total):
    plan = compile_model_plan(cohort(us, kr), topology='CANONICAL_PRODUCTION')
    assert len(plan.slots) == total
    assert sum(s.stage == 'MARKET' for s in plan.slots) == bool(us)+bool(kr)
    assert ModelExecutionPlan.from_dict(plan.to_dict()) == plan
    assert budget(plan).state()['planned_slots'] == total
    if (us, kr) == (14,8):
        assert sum(s.market == 'us' for s in plan.slots) == 30
        assert sum(s.market == 'kr' for s in plan.slots) == 18
    if total == 0:
        with pytest.raises(ValueError):
            budget(plan).consume(None, 'MARKET', digest('not planned'))


def test_reordered_cohort_same_plan_and_split_is_not_canonical():
    original = cohort()
    reordered = replace(original, subjects=tuple(reversed(original.subjects)), source_owner_bindings=tuple(reversed(original.source_owner_bindings)))
    assert compile_model_plan(original, topology='CANONICAL_PRODUCTION').sha256 == compile_model_plan(reordered, topology='CANONICAL_PRODUCTION').sha256
    split = compile_model_plan(cohort(1,1), topology='SPLIT_RESEARCH')
    assert len(split.slots) == 6 and not any(s.stage in ('CORE','A','B','B2') for s in split.slots)
    adj = next(s for s in split.slots if s.stage == 'ADJUDICATION')
    with pytest.raises(ValueError, match='upstream_acceptance_gap'):
        budget(split).bind_stage('ADJUDICATION', request(split, adj))
    with pytest.raises(ValueError, match='SOURCE_OWNER_REQUIRED'):
        split.cohort.verify_source_owner(None)


@pytest.mark.parametrize('change', ['missing','duplicate','profile','cap','new_cohort'])
def test_unapproved_plan_drift_zero_invocations(change):
    plan = compile_model_plan(cohort(), topology='CANONICAL_PRODUCTION')
    with pytest.raises(ValueError):
        if change == 'missing':
            budget(replace(plan, slots=plan.slots[1:]))
        elif change == 'duplicate':
            budget(replace(plan, slots=plan.slots+(plan.slots[0],)))
        elif change == 'profile':
            budget(replace(plan, execution_profile='SOL_61_MEDIUM_EXECUTION_V1'))
        elif change == 'cap':
            budget(plan, 47)
        else:
            changed = compile_model_plan(cohort(15,8), topology='CANONICAL_PRODUCTION')
            SolHighCallBudget(plan=changed, approved_max_invocations=49, approved_plan_sha256=plan.sha256)


@pytest.mark.parametrize('change', ['ticker','batch','source_generation','payload_sha','security'])
def test_request_or_payload_mismatch_before_invocation(change):
    plan = compile_model_plan(cohort(3,0), topology='CANONICAL_PRODUCTION')
    item = budget(plan)
    market, core = plan.slots[:2]
    accept_one(item, plan, market)
    value = request(plan, core)
    if change == 'ticker': value['subjects'][0] = 'NOT_REGISTERED'
    if change == 'batch': value['batch'] = 999
    if change == 'source_generation': value['source_generation_id'] = 'OTHER'
    if change == 'payload_sha': value['payload']['input']['US000']['price'] = 999
    with pytest.raises(ValueError):
        if change == 'security':
            replace(plan.cohort, subjects=(replace(plan.cohort.subjects[0], security_id=plan.cohort.subjects[1].security_id), *plan.cohort.subjects[1:]))
        else:
            item.bind_stage('CORE', value)
    assert len(item.used) == 1  # only the explicit preceding offline acceptance


def test_failed_slot_not_refilled_and_markets_share_one_budget():
    plan = compile_model_plan(cohort(1,1), topology='CANONICAL_PRODUCTION')
    item = budget(plan)
    markets = [s for s in plan.slots if s.stage == 'MARKET']
    for slot in reversed(markets):
        accept_one(item, plan, slot)
    core = next(s for s in plan.slots if s.stage == 'CORE')
    scope = item.bind_stage('CORE', request(plan, core))
    item.consume(None, 'CORE', scope['payload_sha256'], slot_scope=scope)
    # A failed consumed slot has no acceptance; no retry or successor payload binding.
    with pytest.raises(ValueError):
        item.consume(None, 'CORE', scope['payload_sha256'], slot_scope=scope)
    with pytest.raises(ValueError):
        item.bind_stage('A', request(plan, next(s for s in plan.slots if s.stage == 'A' and s.market == core.market)))
    assert item.state()['consumed'] == 3 and item.state()['remaining'] == 7


def test_three_subject_bridge_worker_scope_and_cycle_no_refill(tmp_path, monkeypatch):
    fixture = invocation.__wrapped__(tmp_path, monkeypatch)
    binding = qualify_fixture(fixture)
    monkeypatch.setattr(cli.subprocess, 'run', fake_cli)
    # Mock only the source-owner admission; this test is not a real Source grant.
    monkeypatch.setattr(FrozenCohort, 'verify_source_owner', lambda *args: None)
    plan = compile_model_plan(cohort(3,0), topology='CANONICAL_PRODUCTION')
    item = budget(plan)
    workers = []
    async def factory(*args, **kwargs):
        worker = OfflineWorker()
        workers.append(worker)
        return worker
    model = OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(binding),default=str)),
        runtime_root=tmp_path/'runtime', execution_profile=SOL_HIGH_V1, call_budget=item, worker_factory=factory)
    model.bind_cycle(market='us', run_id=plan.cohort.run_id)
    bridge = SimpleNamespace(_native_owner_parents={}, execution_profile=SOL_HIGH_V1, model=model)
    session = SimpleNamespace(market='us', verify_model_build=lambda *a: None, accept=lambda *a: None)
    for slot in plan.slots[:2]:
        asyncio.run(ProductionRuntimeBridgeV1._invoke(bridge, session, slot.stage, request(plan,slot), tmp_path/slot.slot_id))
    scope = workers[-1].frame['slot_scope']
    assert scope['subjects'] == ['US000','US001','US002'] and scope['batch_id'] == 1
    assert request_from_frame(workers[-1].frame).model_plan_scope == scope
    assert len(item.used) == len(workers) == 2 and len(item.accepted) == 2
    model.bind_cycle(market='us', run_id=plan.cohort.run_id)
    assert item.state()['consumed'] == 2
    with pytest.raises(ValueError):
        asyncio.run(ProductionRuntimeBridgeV1._invoke(bridge, session, 'CORE', request(plan,plan.slots[1]), tmp_path/'retry'))
    assert len(workers) == 2
    wrong = deepcopy(workers[-1].frame)
    wrong['slot_scope']['subjects'] = ['OTHER']
    with pytest.raises(ValueError):
        request_from_frame(wrong)


@pytest.mark.parametrize('drift', ['price','ticker','source'])
def test_original_build_receipt_drift_zero_model(tmp_path, drift):
    plan = compile_model_plan(cohort(3,0), topology='CANONICAL_PRODUCTION')
    req = request(plan, plan.slots[1])
    req.update(directory=str(tmp_path), internal_schema_sha256=digest({'type':'object'}))
    for name,value in [('request-receipt.json',req),('subject-context.json',req['payload']['input']),
            ('provider-wire-schema.json',req['payload']['response_schema']),('internal-semantic-schema.json',{'type':'object'})]:
        (tmp_path/name).write_text(json.dumps(value))
    (tmp_path/'prompt.txt').write_text(req['payload']['prompt'])
    stub = SimpleNamespace(_verify_native_source=lambda: None, captured={'CORE':[deepcopy(req)]})
    changed = deepcopy(req)
    if drift == 'price': changed['payload']['input']['US000']['price'] = 777
    if drift == 'ticker': changed['subjects'][0] = 'OTHER'
    if drift == 'source': changed['source_generation_id'] = 'OTHER'
    changed['payload_sha256'] = digest(changed['payload'])
    with pytest.raises(ValueError):
        ProductionMonitoringSession.verify_model_build(stub, 'CORE', changed)


def test_planning_cohort_cannot_open_production_session(tmp_path):
    with pytest.raises(ValueError, match='SOURCE_OWNER_REQUIRED'):
        ProductionMonitoringSession(tmp_path, market='us', generation_id='OFFLINE_C22Z_ONLY', source={}, frozen_cohort=cohort(3,0))


def test_original_owner_identity_and_availability_are_not_ui_assertions(monkeypatch):
    from app.services.canonical_native_source_owner import CanonicalPreparedSourceOwner
    original = cohort(1,0)
    cutoff = original.cutoff
    row = replace(original.subjects[0], available_at=cutoff)
    relation = dict(generation_id=original.run_id, source_generation_id=original.source_generation,
        subjects=[row.ticker], subject_sha256={row.ticker:row.owner_subject_sha256})
    bound = replace(original, subjects=(row,), source_owner_bindings=(('us',digest(relation)),), planning_only=False)
    owner = object.__new__(CanonicalPreparedSourceOwner)
    # Existing Source-owner methods are fixtures here; no operating owner is minted.
    monkeypatch.setattr(CanonicalPreparedSourceOwner,'relationship',lambda *a:relation)
    monkeypatch.setattr(CanonicalPreparedSourceOwner,'resolve_subject',lambda *a:dict(cutoff=cutoff, canonical_security_id=row.security_id))
    bound.verify_source_owner(owner)
    for changed in (replace(row,security_id='UI_ONLY_ID'), replace(row,available_at='2026-11-11T00:00:00+00:00')):
        with pytest.raises(ValueError,match='CANONICAL_ID_OR_SOURCE_TIME'):
            replace(bound,subjects=(changed,)).verify_source_owner(owner)
