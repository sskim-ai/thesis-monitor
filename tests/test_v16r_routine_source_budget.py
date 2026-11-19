"""Finite offline scope tests. Synthetic Owners are never operating approvals."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import fcntl
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import prospective_class_c_owner as registration
from app.services import production_source_backend as backend
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_context import freeze_registered_child
from app.services.selected_source_registration import capture_approved_markets, database_target
from app.services.selected_source_plan import SelectedStockPlan, SelectedRequestPlan
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import UNIVERSE
from tests.test_c22ab_selected_source import compile_market
from tests.test_manual_source_budget import offline_only, prepared
from tests.test_minimal_class_c_export import database, POLICY


class CollectorReached(RuntimeError):
    pass


def routine(folder, *, seconds=1800, approval_seconds=10800, campaign_seconds=10800):
    folder.mkdir()
    permission = database(folder, [(t, 'us') for t in UNIVERSE['us']])
    now = datetime.now(timezone.utc)
    approval = registration.record_backend_approval(registration.ApprovalDecision(
        event_id='V16R_SYNTHETIC_NOT_LIVE', approved=True, user_message_sha256=digest('TEST_ONLY'),
        effective_at=now-timedelta(seconds=1), expires_at=now+timedelta(seconds=approval_seconds),
        subjects=permission.subjects, routine_us_no_send_source_seconds=seconds))
    settings = SimpleNamespace(database_url='sqlite:///'+str(permission.database))
    path, dev, ino = database_target(settings, runtime_directory=folder)
    ledger = SelectedRunLedger(path=folder/'campaign.jsonl', approval=approval, master_id='TEST_MASTER',
        children={'us':dict(generation='BOUNDARY-us', subjects=list(UNIVERSE['us']))},
        provider_caps={'kiwoom':10}, max_http=10, max_models=30,
        database_identity=dict(path=str(path), device=dev, inode=ino),
        wallclock_seconds_max=campaign_seconds, staged_markets=True,
        runtime_cap={'endpoints':{'kiwoom':[dict(methods=['GET','POST'],host='wire.test',
            prefix='/',endpoint='SYNTHETIC_ONLY')]}})
    _, owners, _ = capture_approved_markets(settings=settings, runtime_directory=folder,
        approval=approval, generations={'us':'BOUNDARY-us'}, policy=POLICY, ledger=ledger,
        enabled=True, subject_limits={'us':1}, priority_subjects={'us':('MU',)})
    _, compiled_args, _ = compile_market('us','MU')
    frozen, compiler, kis, _ = freeze_registered_child(registration_owner=owners['us'],
        policy=POLICY, code_sha='a'*40, native={}, native_owner_root=folder,
        config_identities=compiled_args['config_identities'], configured_kr_pages=20,
        listing_rows=[], kis_static_hashes={}, run_ledger=ledger, enabled=True, master_id='TEST_MASTER')
    plan = SelectedRequestPlan.model_validate(frozen['plan'])
    ledger.bind_source_plan('us',plan)
    root = folder/'source'
    root.mkdir()
    (root/'production-frozen-source-plan.json').write_bytes(encoded(frozen)+b'\n')
    return dict(registration_owner=owners['us'], run_ledger=ledger, root=root, frozen=frozen,
        compiler=compiler, credentials={}, policy=POLICY, kis_plan=kis, deadline=time.monotonic()+4000)


def probe(source, *, seconds=1800, manual=None, observed=None):
    observed = {} if observed is None else observed
    class Collector:
        async def collect(self, **kwargs):
            observed.update(kwargs)
            raise CollectorReached('SYNTHETIC_BEFORE_SOURCE_ADMISSION')
    source = dict(source,transport=Collector())
    options = {'routine_us_no_send_source_seconds':seconds} if seconds is not None else {}
    if manual is not None:
        options['manual_source_seconds'] = manual
    model = {'run_ledger':source['run_ledger']} if manual is not None else None
    with pytest.raises(CollectorReached):
        asyncio.run(job.run_registered(None, source=source, model=model,
            mode='LIVE_NO_SEND' if manual is not None else 'SOURCE_ONLY', **options))
    return observed


def test_bound_routine_caller_to_real_collector_wait_for_1800(tmp_path, monkeypatch):
    source = routine(tmp_path/'routine')
    observed = {}
    original = asyncio.wait_for
    async def timed(awaitable, timeout):
        observed['outer_timeout'] = timeout
        return await original(awaitable, timeout)
    monkeypatch.setattr(backend.asyncio,'wait_for',timed)
    monkeypatch.setattr(job,'load_adapter',lambda *a,**k:pytest.fail('model_factory_must_not_run'))
    began = time.monotonic()
    probe(source,observed=observed)
    budget = json.loads((source['root'].parent/'source-time-budget.json').read_bytes())
    assert 1798 < observed['deadline']-began <= 1800.1
    assert 1798 < observed['outer_timeout'] <= 1800
    assert observed['deadline'] == budget['monotonic_deadline']
    assert budget['purpose'] == registration.ROUTINE_SCOPE and budget['manual_no_send'] is False
    assert source['frozen']['execution_purpose'] == registration.ROUTINE_SCOPE
    assert source['frozen']['plan']['routine_us_no_send_source_seconds'] == 1800
    assert source['run_ledger'].state()['model_total'] == source['run_ledger'].state()['http_total'] == 0
    cold = SelectedRunLedger.attach_worker(source['run_ledger'].worker_binding())
    assert cold.identity == source['run_ledger'].identity


def test_inactive_wire_manual_and_default_600_are_backward_compatible(tmp_path):
    now = datetime.now(timezone.utc)
    decision = registration.ApprovalDecision(event_id='TEST', approved=True,
        user_message_sha256='a'*64, effective_at=now, expires_at=now+timedelta(hours=1), subjects=('MU',))
    legacy = dict(event_id='TEST', approved=True, user_message_sha256='a'*64,
        effective_at=now.isoformat().replace('+00:00','Z'),
        expires_at=(now+timedelta(hours=1)).isoformat().replace('+00:00','Z'),
        subjects=['MU'],manual_no_send_source_seconds=None)
    assert decision.model_dump(mode='json') == legacy
    assert digest(decision.model_dump(mode='json')) == digest(legacy)
    assert json.loads(decision.model_dump_json()) == legacy
    for market,ticker in [('us','MU'),('kr','999999')]:
        compiled,args,_ = compile_market(market,ticker)
        for cls,value in [(SelectedStockPlan,args['stock']), (SelectedRequestPlan,compiled['plan'])]:
            raw = value.model_dump(mode='json')
            assert 'routine_us_no_send_source_seconds' not in raw
            assert cls.model_validate(raw).model_dump(mode='json') == raw
            assert digest(raw) == digest(cls.model_validate(raw).model_dump(mode='json'))
    for name,manual,cap in [('default',None,600),('manual',1800,1800)]:
        args = prepared(tmp_path/name)
        source = {k:v for k,v in args.items() if k!='settings'}
        began = time.monotonic()
        seen = probe(source,seconds=None,manual=manual)
        assert cap-2 < seen['deadline']-began <= cap+0.1
    from app.services.unified_market_run import RunConfiguration, UnifiedMarketRun
    from app.services.unified_runtime_v2 import CONTRACT
    config = RunConfiguration(root=tmp_path,debug_destination=None,repo_commit='TEST',scheduler_identity='TEST',
        adapter_fingerprint='TEST',runtime_contract=CONTRACT,collection_timeout_seconds=600,stage_timeout_seconds=600)
    UnifiedMarketRun(config,object())
    from dataclasses import replace
    with pytest.raises(ValueError,match='600_second_contract'):
        UnifiedMarketRun(replace(config,collection_timeout_seconds=1800),object())


def test_manual_or_plain_approval_cannot_enable_routine_and_modes_are_closed(tmp_path):
    for name,cap in [('manual',1800),('plain',None)]:
        args = prepared(tmp_path/name,approved=cap)
        with pytest.raises(ValueError):
            asyncio.run(job.run_registered(None,source={k:v for k,v in args.items() if k!='settings'},
                routine_us_no_send_source_seconds=1800))
        assert not (args['root'].parent/'source-time-budget.json').exists()
    for options in [dict(mode='SEND'),dict(manual_source_seconds=1800,routine_us_no_send_source_seconds=1800),
            dict(source={'routine_us_no_send_source_seconds':1800})]:
        with pytest.raises(ValueError):
            asyncio.run(job.run_registered(None,**({'source':{}}|options)))
    now = datetime.now(timezone.utc)
    for cap in [True,599,1801]:
        with pytest.raises(ValueError):
            registration.ApprovalDecision(event_id='TEST',approved=True,user_message_sha256='a'*64,
                effective_at=now,expires_at=now+timedelta(hours=1),subjects=('MU',),
                routine_us_no_send_source_seconds=cap)
    with pytest.raises(ValueError,match='exclusive'):
        registration.ApprovalDecision(event_id='TEST',approved=True,user_message_sha256='a'*64,
            effective_at=now,expires_at=now+timedelta(hours=1),subjects=('MU',),
            manual_no_send_source_seconds=1800,routine_us_no_send_source_seconds=1800)


def test_owner_kr_purpose_generation_subjects_and_plan_tampering_denied(tmp_path):
    source = routine(tmp_path/'denials')
    owner = source['registration_owner']
    original_owner = registration._OWNERS[owner]
    capture = registration._OWNER_CAPTURES[owner]
    for market,purpose in [('kr',registration.ROUTINE_SCOPE),('us',registration.SCOPE)]:
        with pytest.raises(ValueError,match='scope_or_current_capture'):
            registration.issue_prospective_owner(approval=source['run_ledger'].approval,capture=capture,
                market=market,source_generation_id='WRONG',generation_id='WRONG',policy=POLICY,purpose=purpose)
    for key,value in [('purpose',registration.SCOPE),('market','kr'),
            ('expires_at',(datetime.now(timezone.utc)+timedelta(days=1)).isoformat())]:
        receipt = json.loads(original_owner[2]);receipt[key] = value
        registration._OWNERS[owner] = (original_owner[0],original_owner[1],json.dumps(receipt))
        with pytest.raises(ValueError):
            registration._state(owner)
    registration._OWNERS[owner] = original_owner
    original = deepcopy(source['frozen'])
    for change in ['generation','subjects','purpose','registration_hash']:
        frozen = deepcopy(original)
        if change=='generation': frozen['generation_id']='OTHER'
        if change=='subjects': frozen['plan']['subjects']=['OTHER']
        if change=='purpose': frozen['execution_purpose']=registration.SCOPE
        if change=='registration_hash': frozen['registration_receipt_sha256']='0'*64
        (source['root']/'production-frozen-source-plan.json').write_bytes(encoded(frozen)+b'\n')
        with pytest.raises(ValueError):
            asyncio.run(job.run_registered(None,source=source|{'frozen':frozen},
                routine_us_no_send_source_seconds=1800))
    assert not (source['root'].parent/'source-time-budget.json').exists()


def test_approval_owner_plan_ledger_time_binding_is_not_self_attested(tmp_path):
    source = routine(tmp_path/'times')
    ledger,owner = source['run_ledger'],source['registration_owner']
    approval_json = registration._APPROVALS[ledger.approval]
    owner_tuple = registration._OWNERS[owner]
    original_frozen = deepcopy(source['frozen'])
    for change in ['approval','owner','plan','stock','ledger','requested']:
        frozen = deepcopy(original_frozen)
        if change=='approval':
            value=json.loads(approval_json);value['routine_us_no_send_source_seconds']=1200
            registration._APPROVALS[ledger.approval]=json.dumps(value)
        if change=='owner':
            value=json.loads(owner_tuple[2]);value['routine_us_no_send_source_seconds']=1200
            registration._OWNERS[owner]=(owner_tuple[0],owner_tuple[1],json.dumps(value))
        if change in ['plan','stock']:
            frozen['plan' if change=='plan' else 'stock_plan']['routine_us_no_send_source_seconds']=1200
        if change=='ledger':ledger.identity['routine_us_no_send_source_seconds']=1200
        (source['root']/'production-frozen-source-plan.json').write_bytes(encoded(frozen)+b'\n')
        with pytest.raises(ValueError):
            asyncio.run(job.run_registered(None,source=source|{'frozen':frozen},
                routine_us_no_send_source_seconds=1200 if change=='requested' else 1800))
        registration._APPROVALS[ledger.approval]=approval_json
        registration._OWNERS[owner]=owner_tuple
        ledger.identity['routine_us_no_send_source_seconds']=1800
    assert not (source['root'].parent/'source-time-budget.json').exists()


def test_shorter_expiry_campaign_external_deadline_and_600_boundary(tmp_path,monkeypatch):
    for name,approval,wall,external,expected,cap in [
            ('approval',120,10800,4000,120,1800),('campaign',10800,90,4000,90,1800),
            ('external',10800,10800,30,30,1800),('boundary600',10800,10800,4000,600,600)]:
        source = routine(tmp_path/name,seconds=cap,approval_seconds=approval,campaign_seconds=wall)
        source['deadline']=time.monotonic()+external
        began=time.monotonic()
        seen=probe(source,seconds=cap)
        assert expected-5 < seen['deadline']-began <= expected+0.1
    source = routine(tmp_path/'expired')
    _,receipt=registration._state(source['registration_owner'])
    monkeypatch.setattr(registration,'_now',lambda:datetime.fromisoformat(receipt['expires_at'])+timedelta(seconds=1))
    with pytest.raises(ValueError,match='expired'):
        asyncio.run(job.run_registered(None,source=source,routine_us_no_send_source_seconds=1800))


def test_timeout_cleans_synthetic_lease_preserves_stop_and_no_duplicate(tmp_path):
    source = routine(tmp_path/'cancel')
    stop=tmp_path/'synthetic-lane-stop';stop.write_bytes(b'PRESERVED_STOP')
    lease=tmp_path/'synthetic-lease';lease.touch()
    calls=[]
    class Collector:
        async def collect(self,**kwargs):
            calls.append(kwargs['deadline'])
            with lease.open('rb') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                try: await asyncio.Event().wait()
                finally: source['run_ledger'].stop('SYNTHETIC_SOURCE_TIMEOUT')
    source |= dict(transport=Collector(),deadline=time.monotonic()+0.05)
    with pytest.raises(TimeoutError):
        asyncio.run(job.run_registered(None,source=source,routine_us_no_send_source_seconds=1800))
    assert len(calls)==1 and stop.read_bytes()==b'PRESERVED_STOP'
    with lease.open('rb') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    result=json.loads((source['root'].parent/'source-time-result.json').read_bytes())
    assert result['status']=='FAILED_OR_CANCELLED'
    with pytest.raises(ValueError):
        asyncio.run(job.run_registered(None,source=source,routine_us_no_send_source_seconds=1800))
    assert len(calls)==1 and source['run_ledger'].state()['model_total']==0


def test_dispatcher_keeps_original_purpose_and_no_economic_or_model_grant(tmp_path):
    from app.services.selected_source_dispatch import SelectedSourceDispatcher
    from app.services.selected_source_composition import SelectedSourceRunBinding
    from pydantic import TypeAdapter
    source=routine(tmp_path/'purpose')
    owner,stock=source['registration_owner'],source['compiler']['stock']
    dispatcher=object.__new__(SelectedSourceDispatcher)
    dispatcher.registration_owner,dispatcher.stock,dispatcher.policy=owner,stock,POLICY
    dispatcher.guard=lambda:None
    dispatcher._qualified_registration=(owner,stock,POLICY)
    dispatcher._require_current()
    with pytest.raises(ValueError,match='purpose_mismatch'):
        registration.require_generation(owner,stock.run_id)
    bad=stock.model_copy(update={'routine_us_no_send_source_seconds':None})
    dispatcher.stock=bad
    dispatcher._qualified_registration=(owner,bad,POLICY)
    with pytest.raises(ValueError,match='purpose_mismatch'):
        dispatcher._require_current()
    field=TypeAdapter(SelectedSourceRunBinding.model_fields['execution_purpose'].annotation)
    assert field.validate_python(registration.ROUTINE_SCOPE)==registration.ROUTINE_SCOPE
    assert field.validate_python(registration.SCOPE)==registration.SCOPE
    with pytest.raises(ValueError):field.validate_python('SEND')
    _,receipt=registration._state(owner)
    assert receipt['scope']=='MEMBERSHIP_ONLY_NOT_D01_D02'
    assert source['frozen']['financial_use_granted'] is False
    assert source['run_ledger'].state()['model_total']==source['run_ledger'].state()['http_total']==0
