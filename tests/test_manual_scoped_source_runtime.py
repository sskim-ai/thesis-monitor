"""Synthetic registration, original scoped code; no native execution or live PASS."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest
import httpx

from app.services import current_class_c_source_bridge as registration
from app.services import current_scoped_source_owner as owner
from app.services import manual_scoped_source_runtime as manual
from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
from app.services.current_scoped_worker_bridge import ScopedBridge
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.unified_snapshot_contract import encoded
from app.services.unified_source_policy import UnifiedSourcePolicy
from tests.test_current_class_c_source_bridge import case as p2g_case, POLICY as REGISTRATION_POLICY, CONFIG

POLICY = UnifiedSourcePolicy(REGISTRATION_POLICY.allowed_providers | {'kiwoom'})


@pytest.fixture
def case(p2g_case, tmp_path, monkeypatch):
    from app.services import kiwoom_global_lane
    monkeypatch.setattr(kiwoom_global_lane,'DEFAULT_ROOT',tmp_path/'synthetic-lane')
    monkeypatch.setattr(kiwoom_global_lane,'_loaded_lane',None)
    monkeypatch.delenv('KIWOOM_GLOBAL_LANE_REQUIRED',raising=False)
    c = p2g_case
    c['owners'] = {m: owner.registration.issue_prospective_owner(approval=c['approval'],
        capture=c['kwargs']['capture'], market=m, source_generation_id='synthetic-registration',
        generation_id='p2h-test', policy=POLICY)[0] for m in ('kr','us')}
    kwargs = deepcopy({k:v for k,v in c['kwargs'].items() if k not in {'capture','owners','policy'}})
    kwargs.update(capture=c['kwargs']['capture'], owners=c['owners'], policy=POLICY)
    kwargs['stock_metadata']['run_id'] = 'p2h-test'
    native = tmp_path/'synthetic-native'
    (native/'app').mkdir(parents=True)
    native_pins = {}
    for i in range(25):
        name = f'app/synthetic_{i}.py'
        raw = b'# synthetic code only\n'
        (native/name).write_bytes(raw)
        native_pins[name] = dict(bytes=len(raw),sha256=manual.sha256_bytes(raw))
    c['native_root'],c['native_pins'] = native,native_pins
    kwargs['stock_metadata']['owner_files'] = {n:v['sha256'] for n,v in native_pins.items()}
    kwargs['counts'] = {m:dict(adjusted_daily=1000,adjusted_weekly=700,
        adjusted_monthly=300,unadjusted_weekly_valuation=300) for m in ('kr','us')}
    c['handle'], c['stock'], c['frozen'] = registration.prepare_current_bridge(**kwargs, enabled=True)
    c['prepare'] = dict(class_c_bridge=c['handle'],frozen=c['frozen'],stock_plan=c['stock'],
        policy=POLICY,maximum_attempts=20,provider_config_sha256=CONFIG)
    return c


def prepared(c):
    return manual.prepare(**c['prepare'], enabled=True)


def runtime(c, tmp_path):
    handle = prepared(c)
    parent, wire, stock = manual.inputs(handle)
    plan = wire['request_plan']
    dispatcher = CurrentScopedDispatcher(parent=parent, plan=plan, root=tmp_path/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
        config_identities={'kiwoom':CONFIG}, credential_presence={'kiwoom':True})
    output = tmp_path/'worker'
    output.mkdir()
    envelope = dict(stage=str(manual.ROOT),output=str(output),external_root=str(c['native_root']),
        external_pins=deepcopy(c['native_pins']),stock_plan=stock,request_interval=1.5,
        latest_completed_us_session=c['frozen']['sessions']['us'],us_market_symbols=[],
        read_paths=[str(manual.ROOT/'scripts/current_scoped_source_worker.py'),
            *[str(c['native_root']/n) for n in c['native_pins']]])
    path = tmp_path/'worker-plan.json'
    path.write_bytes(encoded(envelope))
    worker = ScopedBridge(parent=parent,original_plan=plan,
        transport=SealedSourceTransport(dispatcher,httpx.MockTransport(lambda request:pytest.fail('NO_IO_TEST')),
            providers={'kiwoom'}),worker=manual.ROOT/'scripts/current_scoped_source_worker.py',
        frozen=path,sha=manual.sha256_bytes(path.read_bytes()),output=output,credentials={},market_reads=())
    return handle, dispatcher, worker, envelope


def test_full_registration_narrow_chart_plan_no_close_expansion(case):
    h = prepared(case)
    assert prepared(case) is h
    parent, wire, stock = manual.inputs(h)
    receipt = manual.describe(h)
    assert len(wire['stock_reads']) == 2 and len(stock['reads']) == 2
    assert {r.market for r in wire['stock_reads']} == {'kr','us'}
    assert all(r.count == 1000 and r.role == 'adjusted_daily' for r in wire['stock_reads'])
    assert receipt['parent']['planned_attempts'] == 20
    assert {d.endpoint_operation for d in wire['request_plan'].descriptors} == {'credential_exchange','usa06012','ka10081'}
    spec = owner.ScopedSourceSpec.model_validate_json(owner._PARENTS[parent].spec_json)
    assert len(spec.config.subjects) == 22
    assert not receipt['actual_source_issued'] and not receipt['full_native'] and not receipt['full_market']
    assert not wire['us_market_symbols']


def test_selection_uses_canonical_identity_and_copies_do_not_grant_authority(case):
    import gc
    h = prepared(case)
    _, wire, stock = manual.inputs(h)
    for r in wire['stock_reads']:
        assert r.canonical_security_id == min(x.canonical_security_id for x in case['stock'].reads if x.market == r.market)
    stock['reads'].clear()
    assert len(manual.inputs(h)[2]['reads']) == 2
    with pytest.raises(ValueError): manual.inputs(manual.describe(h))
    del h
    gc.collect()
    with pytest.raises(ValueError,match='handle_lifetime_ended'): prepared(case)


def test_default_off_and_budget_must_cover_all_original_pages(case):
    with pytest.raises(ValueError, match='default_off'): manual.prepare(**case['prepare'])
    for cap in (19,33,True):
        with pytest.raises(ValueError): manual.prepare(**dict(case['prepare'],maximum_attempts=cap),enabled=True)


@pytest.mark.parametrize('field', ['purpose','generation','issuer','sixth_candidate'])
def test_original_bridge_blocks_changed_contract_before_issuer(case, field):
    frozen = deepcopy(case['frozen'])
    if field=='purpose': frozen['execution_purpose']='PRODUCTION_MONITORING'
    elif field=='generation': frozen['generation_id']='another'
    elif field=='issuer': frozen['stock_plan']['reads'][0]['canonical_security_id']='unrelated-ads'
    else: frozen['stock_plan']['reads'][0]['subject']='META'
    with pytest.raises(ValueError,match='frozen_contract'):
        manual.prepare(**dict(case['prepare'],frozen=frozen),enabled=True)


def test_original_owner_revocation_and_cross_process(case, monkeypatch):
    h = prepared(case)
    with monkeypatch.context() as m:
        m.setattr(manual.os,'getpid',lambda:0)
        with pytest.raises(ValueError,match='process_or_code'): manual.inputs(h)
    owner.registration.revoke_prospective_owner(case['owners']['kr'])
    with pytest.raises(ValueError): manual.inputs(h)


def test_original_runtime_binding_is_not_native_execution(case,tmp_path):
    h, run, worker, _ = runtime(case,tmp_path)
    value=manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)
    assert value['runtime_bound'] and not value['actual_source_issued']
    assert manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)==value
    sealed=worker.transport
    worker.transport=SimpleNamespace(dispatcher=run)
    with pytest.raises(ValueError,match='original_sealed_transport'):
        manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)
    worker.transport=sealed
    sealed.providers=frozenset({'kiwoom','sec_edgar'})
    with pytest.raises(ValueError,match='original_sealed_transport'):
        manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)
    sealed.providers=frozenset({'kiwoom'})
    assert worker.process is None and not run.used and run.physical_attempts == 0
    parent, wire, _ = manual.inputs(h)
    with pytest.raises(ValueError):
        owner.issue_source_result(parent,plan=wire['request_plan'],dispatcher=run,entry_id=wire['stock_reads'][0].entry_id)
    with pytest.raises(ValueError,match='original_manual_dispatcher'):
        registration.bind_existing_dispatcher(case['handle'],run,policy=POLICY)


@pytest.mark.parametrize('field',['pin','native','session','secret_read','historical'])
def test_runtime_substitution_denied_before_child(case,tmp_path,field):
    h, run, worker, envelope = runtime(case,tmp_path)
    if field=='pin': worker.sha='f'*64
    elif field=='native': envelope['external_pins']['app/synthetic_0.py']['sha256']='f'*64
    elif field=='session': envelope['latest_completed_us_session']='1900-01-01'
    elif field=='secret_read': envelope['read_paths']=['/not-accessed/.env']
    else: envelope['historical_source_root']='/not-accessed/history'
    if field!='pin':
        worker.frozen.write_bytes(encoded(envelope))
        worker.sha=manual.sha256_bytes(worker.frozen.read_bytes())
    with pytest.raises(ValueError): manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)
    assert worker.process is None and not run.used


def test_dispatcher_concurrency_and_explicit_revocation(case,tmp_path):
    h, run, worker, _ = runtime(case,tmp_path)
    parent, wire, _ = manual.inputs(h)
    with pytest.raises(ValueError):
        CurrentScopedDispatcher(parent=parent,plan=wire['request_plan'],root=tmp_path/'other',
            owners={d.normalizer:d.owner_sha256 for d in wire['request_plan'].descriptors},
            config_identities={'kiwoom':CONFIG},credential_presence={'kiwoom':True})
    manual.revoke(h)
    with pytest.raises(ValueError): owner.resolve_parent(parent)
    with pytest.raises(ValueError): manual.inputs(h)


@pytest.mark.parametrize('mutation',['worker','envelope','native'])
def test_bound_runtime_mutation_rejected_before_command(case,tmp_path,mutation):
    import asyncio
    h, run, worker, envelope = runtime(case,tmp_path)
    manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)
    if mutation=='worker': worker.worker=manual.ROOT/'scripts/unified_stock_source_worker.py'
    elif mutation=='envelope':
        envelope['request_interval']=0
        worker.frozen.write_bytes(encoded(envelope))
        worker.sha=manual.sha256_bytes(worker.frozen.read_bytes())
    else: (case['native_root']/'app/synthetic_0.py').write_text('# changed\n')
    with pytest.raises(ValueError): manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)
    with pytest.raises(ValueError): asyncio.run(manual.command(h,{'stocks':True}))
    assert worker.process is None and run.physical_attempts==0


def test_changed_provider_configuration_rejected(case):
    with pytest.raises(ValueError,match='provider_config_changed'):
        manual.prepare(**dict(case['prepare'],provider_config_sha256='f'*64),enabled=True)


def test_original_expiry_and_wrong_worker_command(case,tmp_path,monkeypatch):
    import asyncio
    from datetime import datetime,timedelta,timezone
    h,run,worker,_=runtime(case,tmp_path)
    manual.bind_runtime(h,dispatcher=run,worker_bridge=worker)
    for command in ({'replay':True},{'market':'SPY'},{'discovery':True}):
        with pytest.raises(ValueError,match='command_outside_chart_scope'):
            asyncio.run(manual.command(h,command))
    monkeypatch.setattr(owner.registration,'_now',lambda:datetime.now(timezone.utc)+timedelta(hours=2))
    with pytest.raises(ValueError,match='expired'): manual.inputs(h)
    assert worker.process is None and run.physical_attempts==0
