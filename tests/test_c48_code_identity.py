"""Real code-content comparisons at the registered boundary; synthetic I/O only."""
import asyncio
from datetime import datetime
import json
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import production_source_backend as backend
from tests.test_c42_kr_caller import offline
from tests.test_local_launchd_entry import code_pin, configuration


@pytest.fixture
def code_tree(tmp_path, monkeypatch):
    root = tmp_path / 'code'
    for name in ('app/services/owner.py', 'scripts/policy.json',
                 'docs/operations/UNIFIED_ACQUISITION_CLASSES.json'):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('VALUE = 1\n' if path.suffix == '.py' else '{}\n')
    # Redirect the real inventory's input; never replace its digest or comparison.
    monkeypatch.setattr(backend, 'ROOT', root)
    return root / 'app/services/owner.py'


def child_and_model(monkeypatch, events, *, cleanup_fails=False):
    def close():
        events.append('close')
        if cleanup_fails:
            raise RuntimeError('synthetic cleanup failure')

    child = SimpleNamespace(market='us', verify=lambda: events.append('verify'), binding=lambda: {},
        plan=SimpleNamespace(sha256='0' * 64,
            cohort=SimpleNamespace(cutoff='2026-11-23T22:00:00+00:00')),
        owner=SimpleNamespace(close=close))
    ledger = SimpleNamespace(bind_model_plan=lambda _: events.append('bind'),
        rendered_market=lambda *_: events.append('terminal'))

    def adapter(*args, **kwargs):
        events.append('adapter')
        return object()

    async def model(*args):
        events.append('model')
        return dict(status='RENDER_VERIFIED_NO_SEND', normal_messages_sent=False)

    monkeypatch.setattr(job, 'load_adapter', adapter)
    monkeypatch.setattr(job, 'build_engine', lambda *a, **kw: SimpleNamespace(run=model))
    source = dict(run_ledger=ledger, frozen={'stock_plan': {'implementation_sha': 'a' * 40}})
    return child, source, dict(run_ledger=ledger)


def test_current_code_enters_model_without_manual_file_approval(code_tree, monkeypatch):
    events = []
    code_tree.write_text('VALUE = 2\n')
    child, source, model = child_and_model(monkeypatch, events)

    async def prepare(**kwargs):
        events.append('source')
        return child, {}

    monkeypatch.setattr(backend.CanonicalProductionSourceBackend, 'prepare_registered', prepare)
    result = asyncio.run(job.run_registered(None, source=source, model=model,
        mode='LIVE_NO_SEND', record_market_terminal=True))
    assert result['status'] == 'RENDER_VERIFIED_NO_SEND'
    assert events == ['source', 'verify', 'adapter', 'bind', 'model', 'terminal', 'close']


def test_changed_code_stops_before_source_collection(code_tree, monkeypatch):
    before = backend.runtime_code_identity()
    code_tree.write_text('VALUE = 3\n')
    entered = []

    async def forbidden(**kwargs):
        entered.append('source')
        pytest.fail('changed code must stop before collection')

    monkeypatch.setattr(backend.CanonicalProductionSourceBackend, 'prepare_registered', forbidden)
    with pytest.raises(ValueError, match='^registered_runtime_code_changed$'):
        asyncio.run(job.run_registered(None, source={}, initial_code_identity=before))
    assert not entered


def test_model_code_change_stops_before_success_record(code_tree, tmp_path, monkeypatch):
    events = []
    child, source, model = child_and_model(monkeypatch, events)
    code_pin(monkeypatch)
    path, _ = configuration(tmp_path / 'schedule')
    directory = tmp_path / 'schedule/runs/us-2026-11-23'

    async def prepare(**kwargs):
        events.append('source')
        (directory / 'source-time-result.json').write_text(json.dumps(dict(
            status='COLLECTOR_RETURNED_REQUIRES_SOURCE_ADMISSION')))
        return child, {}

    async def consume(*args):
        events.append('model')
        code_tree.write_text('VALUE = 5\n')
        return dict(status='RENDER_VERIFIED_NO_SEND', normal_messages_sent=False)

    async def cycle(*args, **kwargs):
        return await job.run_registered(None, source=source, model=model,
            mode='LIVE_NO_SEND', record_market_terminal=True)

    monkeypatch.setattr(backend.CanonicalProductionSourceBackend, 'prepare_registered', prepare)
    monkeypatch.setattr(job, 'build_engine', lambda *a, **kw: SimpleNamespace(run=consume))
    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    with pytest.raises(ValueError, match='^registered_runtime_code_changed$'):
        asyncio.run(job.run_local_scheduled(path, 'us',
            now=datetime.fromisoformat('2026-11-24T08:10:00+09:00')))
    assert events == ['source', 'verify', 'adapter', 'bind', 'model', 'close']
    assert json.loads((directory / 'terminal.json').read_bytes())['status'] == 'STOPPED_NO_SEND'
    row = json.loads((directory / 'failure-diagnostic.json').read_bytes())
    assert row['stable_error_code'] == 'registered_runtime_code_changed'
    assert row['stage'] == 'LOCAL_REGISTERED_CYCLE'


@pytest.mark.parametrize('cleanup_fails', [False, True])
def test_collection_code_change_stops_models_and_preserves_first_receipt(
        code_tree, tmp_path, monkeypatch, cleanup_fails):
    events = []
    child, source, model = child_and_model(monkeypatch, events, cleanup_fails=cleanup_fails)
    code_pin(monkeypatch)
    path, config = configuration(tmp_path / 'schedule')
    directory = tmp_path / 'schedule/runs/us-2026-11-23'

    async def prepare(**kwargs):
        events.append('source')
        code_tree.write_text('VALUE = 4\n')
        (directory / 'source-time-result.json').write_text(json.dumps(dict(
            status='COLLECTOR_RETURNED_REQUIRES_SOURCE_ADMISSION')))
        return child, {}

    async def cycle(*args, **kwargs):
        return await job.run_registered(None, source=source, model=model, mode='LIVE_NO_SEND',
            initial_code_identity=backend.runtime_code_identity())

    monkeypatch.setattr(backend.CanonicalProductionSourceBackend, 'prepare_registered', prepare)
    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    with pytest.raises(ValueError, match='^registered_runtime_code_changed$'):
        asyncio.run(job.run_local_scheduled(path, 'us',
            now=datetime.fromisoformat('2026-11-24T08:10:00+09:00')))
    assert events == ['source', 'close']  # No model factory, plan binding or model execution.
    receipt = directory / 'failure-diagnostic.json'
    first = receipt.read_bytes()
    row = json.loads(first)
    assert row['stable_error_code'] == 'registered_runtime_code_changed'
    assert row['stage'] == 'LOCAL_REGISTERED_CYCLE' and row['NO_SEND'] is True
    assert json.loads((directory / 'terminal.json').read_bytes())['status'] == 'STOPPED_NO_SEND'
    job._record_local_failure(directory, RuntimeError('later cleanup failure'),
        config=SimpleNamespace(**config), session='2026-11-23')
    assert receipt.read_bytes() == first
