"""Manual timer boundary only; synthetic registration is not live Source PASS."""
import asyncio
from datetime import datetime, timedelta, timezone
import fcntl
import json
from pathlib import Path
import socket
import sqlite3
import sqlite3.dbapi2
import sys
import time
from types import SimpleNamespace
from urllib.parse import unquote, urlsplit

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import production_source_backend as backend
from app.services import production_source_transport as transport
from app.services import prospective_class_c_owner as registration
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_registration import capture_approved_markets, database_target
from app.services.sealed_native_bridge import SealedNativeBridge
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from tests.test_c22ab_selected_source import compile_market
from tests.test_minimal_class_c_export import database, POLICY


@pytest.fixture(autouse=True)
def offline_only(monkeypatch, tmp_path):
    def denied(*args, **kwargs):
        raise AssertionError('manual_budget_test_network_denied')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    original = sqlite3.connect

    def local(path, *args, **kwargs):
        value = str(path)
        if value != ':memory:':
            p = Path(unquote(urlsplit(value).path) if value.startswith('file:') else value)
            assert p.resolve().is_relative_to(tmp_path.resolve()), 'operating_db_denied'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', local)
    monkeypatch.setattr(sqlite3.dbapi2, 'connect', local)


def prepared(folder, *, approved=1800, wallclock=10800):
    folder.mkdir()
    permission = database(folder, [('NEWUS', 'us'), ('999999', 'kr')])
    now = datetime.now(timezone.utc)
    approval = registration.record_backend_approval(registration.ApprovalDecision(
        event_id='SYNTHETIC_MANUAL_BUDGET_ONLY', approved=True,
        user_message_sha256=digest('NOT_A_USER_LIVE_APPROVAL'),
        effective_at=now-timedelta(seconds=2), expires_at=now+timedelta(hours=3),
        subjects=permission.subjects, manual_no_send_source_seconds=approved))
    settings = SimpleNamespace(database_url='sqlite:///'+str(permission.database))
    path, dev, ino = database_target(settings, runtime_directory=folder)
    ledger = SelectedRunLedger(path=folder/'campaign.jsonl', approval=approval, master_id='TEST',
        children={'us': dict(generation='BOUNDARY-us', subjects=['NEWUS']),
                  'kr': dict(generation='BOUNDARY-kr', subjects=['999999'])},
        provider_caps={'kiwoom': 2}, max_http=2, max_models=10,
        database_identity=dict(path=str(path), device=dev, inode=ino),
        wallclock_seconds_max=wallclock)
    _, owners, _ = capture_approved_markets(settings=settings, runtime_directory=folder,
        approval=approval, generations={'us': 'BOUNDARY-us', 'kr': 'BOUNDARY-kr'},
        policy=POLICY, ledger=ledger, enabled=True)
    compiled, _, _ = compile_market('us', 'NEWUS')
    plan = compiled['plan']
    ledger.bind_source_plan('us', plan)
    frozen = dict(scope='SELECTED_ORIGINAL_RESEARCH_V1', generation_id=plan.generation_id,
        plan=plan.model_dump(mode='json'), shared_run_ledger=ledger.worker_binding())
    root = folder/'source'
    durable_json(root/'production-frozen-source-plan.json', frozen, exclusive=True)
    return dict(settings=None, registration_owner=owners['us'], run_ledger=ledger,
        root=root, frozen=frozen, compiler={}, credentials={}, policy=POLICY,
        deadline=time.monotonic()+1800)


class CollectorReached(RuntimeError):
    pass


def probe(args, *, manual=None):
    observed = {}

    class Collector:
        async def collect(self, **kwargs):
            observed.update(kwargs)
            raise CollectorReached('NO_NETWORK_SYNTHETIC_COLLECTOR')
    options = {} if manual is None else dict(manual_no_send=True, manual_source_seconds=manual)
    with pytest.raises(CollectorReached):
        asyncio.run(backend.CanonicalProductionSourceBackend.prepare_registered(
            **args, transport=Collector(), **options))
    return observed


def test_default_stays_600_even_with_long_deadline_and_approved_manual_field(tmp_path):
    args = prepared(tmp_path/'default')
    before = time.monotonic()
    observed = probe(args)
    assert 599 < observed['deadline']-before <= 600.1
    receipt = json.loads((args['root'].parent/'source-time-budget.json').read_bytes())
    assert receipt['ceiling_seconds'] == 600 and receipt['manual_no_send'] is False


def test_explicit_bound_manual_1800_uses_exact_original_deadline(tmp_path):
    args = prepared(tmp_path/'manual')
    observed = probe(args, manual=1800)
    assert observed['deadline'] == args['deadline']
    receipt = json.loads((args['root'].parent/'source-time-budget.json').read_bytes())
    assert receipt['ceiling_seconds'] == 1800
    assert receipt['original_approval_sha256'] == args['run_ledger'].identity['approval_sha256']


def test_invalid_or_unapproved_budget_rejected_before_collector(tmp_path):
    for i, (approved, requested) in enumerate(((None, 1800), (1200, 1800), (1800, True), (1800, 1801))):
        args = prepared(tmp_path/str(i), approved=approved)
        with pytest.raises(ValueError, match='manual_source_budget'):
            asyncio.run(backend.CanonicalProductionSourceBackend.prepare_registered(
                **args, manual_no_send=True, manual_source_seconds=requested, transport=object()))
        assert not (args['root'].parent/'source-time-budget.json').exists()
    with pytest.raises(ValueError):
        registration.ApprovalDecision(event_id='bad', approved=True, user_message_sha256='a'*64,
            effective_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc),
            subjects=('X',), manual_no_send_source_seconds=1801)


def test_source_only_or_source_dict_cannot_enable_manual_budget(monkeypatch):
    monkeypatch.setattr(backend.CanonicalProductionSourceBackend, 'prepare_registered',
        lambda **kwargs: pytest.fail('Source entered'))
    with pytest.raises(ValueError, match='requires_no_send'):
        asyncio.run(job.run_registered(None, source={}, manual_source_seconds=1800))
    with pytest.raises(ValueError, match='explicit_entry_argument'):
        asyncio.run(job.run_registered(None, source={'manual_no_send': True, 'manual_source_seconds': 1800}))


def test_expiry_capture_and_campaign_window_still_reject(tmp_path, monkeypatch):
    for name in ('revoked', 'expired', 'owner_window', 'campaign_window', 'approval_mismatch'):
        args = prepared(tmp_path/name, wallclock=900 if name == 'campaign_window' else 10800)
        ledger = args['run_ledger']
        if name == 'revoked':
            registration.revoke_approval(ledger.approval)
        elif name == 'owner_window':
            raw, doc, receipt = registration._OWNERS[args['registration_owner']]
            receipt = json.loads(receipt)
            receipt['expires_at'] = (datetime.now(timezone.utc)+timedelta(seconds=120)).isoformat()
            registration._OWNERS[args['registration_owner']] = (raw, doc, json.dumps(receipt))
        elif name == 'approval_mismatch':
            ledger.identity['approval_sha256'] = '0'*64
        with monkeypatch.context() as clock:
            if name == 'expired':
                _, receipt = registration._state(args['registration_owner'])
                clock.setattr(registration, '_now', lambda: datetime.fromisoformat(receipt['expires_at']))
            with pytest.raises(ValueError):
                asyncio.run(backend.CanonicalProductionSourceBackend.prepare_registered(
                    **args, manual_no_send=True, manual_source_seconds=1800, transport=object()))
            if name == 'expired':
                registration.revoke_prospective_owner(args['registration_owner'])
                assert ledger.state()['state'] == 'STOPPED_NO_SEND'


def test_invalid_monotonic_deadlines_fail_before_collector(tmp_path):
    for i, deadline in enumerate((float('nan'), float('inf'), True, time.monotonic()+5000)):
        args = prepared(tmp_path/str(i))
        args['deadline'] = deadline
        with pytest.raises(ValueError, match='deadline_outside_budget'):
            asyncio.run(backend.CanonicalProductionSourceBackend.prepare_registered(
                **args, manual_no_send=True, manual_source_seconds=1800, transport=object()))


def test_actual_cancellation_reaps_local_child_releases_test_lease_and_preserves_stop(tmp_path):
    args = prepared(tmp_path/'cancel')
    lane_stop = tmp_path/'synthetic-lane-stop.json'
    lane_stop.write_bytes(b'{"halted":true,"sequence":1}')
    lease = tmp_path/'synthetic-pair.lease'
    lease.touch()
    processes = []

    class Collector:
        async def collect(self, **kwargs):
            with lease.open('rb') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                bridge = SealedNativeBridge(owner_root=None, input_path=None, input_sha256=None,
                    output=None, transport=None, market_reads=())
                bridge.process = await asyncio.create_subprocess_exec(sys.executable, '-I', '-S', '-B', '-c',
                    'import sys; sys.stdin.buffer.readline()', env={'LANG': 'C'}, cwd=tmp_path,
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                processes.append(bridge.process)
                try:
                    await asyncio.Event().wait()
                finally:
                    await bridge.shutdown()
                    args['run_ledger'].stop('SYNTHETIC_SOURCE_DEADLINE')
    args['deadline'] = time.monotonic()+0.25
    with pytest.raises(TimeoutError):
        asyncio.run(backend.CanonicalProductionSourceBackend.prepare_registered(
            **args, manual_no_send=True, manual_source_seconds=1800, transport=Collector()))
    assert len(processes) == 1 and processes[0].returncode == 0
    with lease.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert lane_stop.read_bytes() == b'{"halted":true,"sequence":1}'
    with pytest.raises(ValueError, match='stopped'):
        args['run_ledger'].worker_binding()


def test_no_model_factory_or_plan_binding_on_failed_source(tmp_path, monkeypatch):
    args = prepared(tmp_path/'no-model')
    ledger = args['run_ledger']
    class Collector:
        async def collect(self, **kwargs):
            raise CollectorReached('Source not admitted')
    args['transport'] = Collector()
    monkeypatch.setattr(job, 'load_adapter', lambda *a, **k: pytest.fail('model factory entered'))
    with pytest.raises(CollectorReached):
        asyncio.run(job.run_registered(None, source={k: v for k, v in args.items() if k != 'settings'}, model={'run_ledger': ledger},
            mode='LIVE_NO_SEND', manual_source_seconds=1800))
    assert ledger.state()['model_total'] == 0 and not ledger.state()['models']


def test_transport_guard_preserves_safe_deadline_vs_plan_drift_codes(tmp_path, monkeypatch):
    frozen = dict(plan={}, config_identities={}, candidate={})
    durable_json(tmp_path/'production-frozen-source-plan.json', frozen, exclusive=True)
    monkeypatch.setattr(transport, 'ProductionSourceDispatcher', lambda **kwargs: object())
    mode = ['deadline']
    async def acquire(**kwargs):
        if mode[0] == 'plan':
            (tmp_path/'production-frozen-source-plan.json').write_text('{}')
        kwargs['guard']()
    monkeypatch.setattr(transport, 'acquire_all', acquire)
    collector = transport.NativeProductionSourceTransport(None)
    with pytest.raises(SourceSafetyStop, match='source_deadline_exceeded'):
        asyncio.run(collector.collect(root=tmp_path, frozen=frozen, compiler={}, kis_plan=None,
            credentials={}, deadline=time.monotonic()-1))
    mode[0] = 'plan'
    with pytest.raises(SourceSafetyStop, match='source_frozen_plan_drift'):
        asyncio.run(collector.collect(root=tmp_path, frozen=frozen, compiler={}, kis_plan=None,
            credentials={}, deadline=time.monotonic()+600))


def test_scheduled_model_and_source_configuration_stays_600(tmp_path):
    from app.services.unified_market_run import RunConfiguration, UnifiedMarketRun
    from app.services.unified_runtime_v2 import CONTRACT
    config = RunConfiguration(root=tmp_path, debug_destination=None, repo_commit='TEST',
        scheduler_identity='TEST', adapter_fingerprint='TEST', runtime_contract=CONTRACT,
        collection_timeout_seconds=600, stage_timeout_seconds=600)
    assert UnifiedMarketRun(config, object()).config.stage_timeout_seconds == 600
    with pytest.raises(ValueError, match='600_second_contract_required'):
        UnifiedMarketRun(RunConfiguration(**{**config.__dict__, 'collection_timeout_seconds': 1800}), object())


def test_registered_seal_sync_replay_runs_off_event_loop(tmp_path, monkeypatch):
    from app.services import selected_source_preparation as preparation
    args = prepared(tmp_path/'seal-thread')
    calls = []

    def sealer(*a, **kwargs):
        async def captured_only_replay():
            return 'SYNTHETIC_NO_NETWORK_REPLAY'
        result = asyncio.run(captured_only_replay())
        calls.append(result)
        return {'synthetic': True}
    async def active_loop_reproduction():
        async def body():
            return None
        pending = body()
        try:
            with pytest.raises(RuntimeError, match='running event loop'):
                asyncio.run(pending)
        finally:
            pending.close()
    asyncio.run(active_loop_reproduction())
    monkeypatch.setattr(backend, 'require_captured_phase', lambda *a: None)
    monkeypatch.setattr(backend, 'market_inputs', lambda *a: None)
    monkeypatch.setattr(backend, 'seal_collection', sealer)
    monkeypatch.setattr(backend, 'verify_collection_seal', lambda *a: calls.append('verify_seal'))
    child = SimpleNamespace(verify=lambda: None, plan=SimpleNamespace(validate=lambda: None),
        owner=SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(preparation, 'prepare_child', lambda **kwargs: (child, {}))
    monkeypatch.setattr(args['run_ledger'], 'source_captured', lambda m: calls.append('capture_stub'))
    monkeypatch.setattr(args['run_ledger'], 'source_owned', lambda c: calls.append('owned_stub'))
    class Collector:
        async def collect(self, **kwargs):
            return {'synthetic': True}
    actual, _ = asyncio.run(backend.CanonicalProductionSourceBackend.prepare_registered(
        **args, manual_no_send=True, manual_source_seconds=1800, transport=Collector()))
    assert actual is child and calls == ['capture_stub', 'SYNTHETIC_NO_NETWORK_REPLAY', 'verify_seal', 'owned_stub']
