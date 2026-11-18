"""Actual retained seal replay is offline custody, never live Source admission."""
import asyncio
from collections import Counter
import inspect
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import production_source_backend as backend
from app.services.production_source_seal import corpus_index, seal_collection, verify_collection_seal
from app.services.unified_snapshot_contract import digest


@pytest.fixture(autouse=True)
def no_live_io(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('async_closure_test_live_io_denied')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(socket, 'create_connection', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr(subprocess, 'Popen', denied)


def test_original_retained_night_and_seal_in_active_loop(tmp_path, monkeypatch):
    location = os.environ.get('TM_V4_RETAINED_SOURCE')
    if not location:
        pytest.skip('explicit retained-source custody fixture not supplied')
    root = Path(location).resolve(strict=True)
    frozen = json.loads((root/'production-frozen-source-plan.json').read_bytes())
    outcome = json.loads((root/'acquisition-outcome.json').read_bytes())
    before = corpus_index(root)
    traces = []
    phase = ['NEGATIVE_DIRECT_SYNC']
    names = {'seal_collection', 'slot_dispositions', '_verified_night_probe_tail', 'replay_night'}

    def readonly_source(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1:3]
            writing = flags is not None and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            writing = writing or isinstance(mode, str) and any(c in mode for c in 'wax+')
            if writing and (path == root or path.is_relative_to(root)):
                raise AssertionError('retained_original_source_write_denied')
        elif event in {'socket.connect', 'socket.getaddrinfo', 'socket.sendto', 'sqlite3.connect'} or event.startswith('subprocess.'):
            raise AssertionError('retained_seal_replay_external_io_denied')
    sys.addaudithook(readonly_source)

    def profile(frame, event, arg):
        if event == 'call' and frame.f_code.co_name in names:
            try:
                asyncio.get_running_loop()
                running = True
            except RuntimeError:
                running = False
            traces.append(dict(phase=phase[0], function=frame.f_code.co_name,
                file=Path(frame.f_code.co_filename).name, thread=threading.get_ident(), active_loop=running))
    monkeypatch.setattr(tempfile, 'tempdir', str(tmp_path))
    evidence = dict(status='STARTED', live_source_accepted=False, registration_owner_issued=False,
        financial_http=0, operating_db=0, models=0, original_generation=frozen['generation_id'])
    old_profile, old_thread_profile = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)

    async def run():
        with pytest.raises(RuntimeError, match='running event loop') as failure:
            seal_collection(root, seal_path=tmp_path/'negative.json', frozen=frozen, outcome=outcome)
        trace = failure.value.__traceback__
        while trace:
            pending = trace.tb_frame.f_locals.get('main')
            if inspect.iscoroutine(pending):
                pending.close()
            trace = trace.tb_next
        assert not (tmp_path/'negative.json').exists()
        phase[0] = 'POSITIVE_ORIGINAL_IN_THREAD'
        seal = await backend._source_sync(seal_collection, root,
            seal_path=tmp_path/'positive-source-seal.json', frozen=frozen, outcome=outcome)
        verify_collection_seal(root, seal, frozen)
        bad = {**seal, 'source_plan_sha256': '0'*64}
        with pytest.raises(ValueError, match='source_seal_changed'):
            verify_collection_seal(root, bad, frozen)
        rows = seal['slot_dispositions']['rows']
        tails = [r for r in rows if r.get('night_probe_terminal_proof')]
        assert seal['slot_dispositions']['status'] == 'PASS' and len(tails) == 4
        assert len(list((root/'night/probe').glob('receipt-*.json'))) == 3
        for side in ('NEGATIVE_DIRECT_SYNC', 'POSITIVE_ORIGINAL_IN_THREAD'):
            observed = {r['function'] for r in traces if r['phase'] == side}
            assert names <= observed
        assert all(not r['active_loop'] for r in traces if r['phase'] == 'POSITIVE_ORIGINAL_IN_THREAD')
        evidence.update(status='OFFLINE_REAL_SEAL_AND_NIGHT_TAIL_PASS',
            negative_control='ORIGINAL_NESTED_LOOP_RUNTIME_ERROR',
            real_validator_functions=sorted(names), tail_slots_closed=len(tails), original_night_get_receipts=3,
            slot_dispositions=seal['slot_dispositions']['counts'], scratch_seal_sha256=seal['receipt_sha256'],
            verification='ORIGINAL_CORPUS_AND_HASH_PASS', tampered_seal='REJECTED')
    try:
        asyncio.run(run())
    except Exception as exc:
        evidence.update(status='OFFLINE_REAL_SEAL_FAIL', failure_type=type(exc).__name__)
        raise
    finally:
        sys.setprofile(old_profile)
        threading.setprofile(old_thread_profile)
        after = corpus_index(root)
        evidence.update(original_file_count=len(before), original_corpus_sha256=digest(before),
            after_corpus_sha256=digest(after), original_unchanged=before == after,
            traces=traces, calls=dict(Counter(r['function'] for r in traces)))
        destination = os.environ.get('TM_V4_EVIDENCE_DIR')
        if destination:
            name = os.environ.get('TM_V4_EVIDENCE_NAME', 'SOURCE_SEAL_OFFLINE_EVIDENCE.json')
            with (Path(destination)/name).open('x') as f:
                json.dump(evidence, f, indent=2)
        assert before == after


@pytest.mark.parametrize('managed', [False, True])
def test_thread_cancel_negative_vs_owned_drain(tmp_path, managed):
    entered, release = threading.Event(), threading.Event()
    closed, owned = [], []
    marker = tmp_path/'thread-result.json'
    child = SimpleNamespace(owner=SimpleNamespace(close=lambda: closed.append('closed')))

    def work():
        entered.set()
        assert release.wait(3)
        marker.write_text('SYNTHETIC_ONLY')
        return child, {}

    async def run():
        async def caller():
            if managed:
                await backend._source_sync(work, on_cancel=lambda result: result[0].owner.close())
            else:
                await asyncio.to_thread(work)
            owned.append('not permitted after cancel')
        task = asyncio.create_task(caller())
        deadline = time.monotonic()+2
        while not entered.is_set():
            assert time.monotonic() < deadline
            await asyncio.sleep(0.001)
        task.cancel()
        await asyncio.sleep(0.02)
        if managed:
            assert not task.done() and not marker.exists()
            task.cancel()
            await asyncio.sleep(0.01)
            assert not task.done()
        else:
            assert task.done() and not marker.exists()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        if not managed:
            while not marker.exists():
                await asyncio.sleep(0.001)
        pin = marker.stat().st_mtime_ns
        await asyncio.sleep(0.02)
        assert marker.stat().st_mtime_ns == pin
    asyncio.run(run())
    assert not owned and closed == (['closed'] if managed else [])


def test_rejection_propagates_and_model_factory_is_not_entered(monkeypatch):
    def rejected():
        raise ValueError('SYNTHETIC_SOURCE_REJECTED')
    async def prepare(**kwargs):
        await backend._source_sync(rejected)
    monkeypatch.setattr(backend.CanonicalProductionSourceBackend, 'prepare_registered', prepare)
    monkeypatch.setattr(job, 'load_adapter', lambda *a, **k: pytest.fail('model factory entered'))
    ledger = object()
    with pytest.raises(ValueError, match='SYNTHETIC_SOURCE_REJECTED'):
        asyncio.run(job.run_registered(None, source={'run_ledger': ledger},
            model={'run_ledger': ledger}, mode='LIVE_NO_SEND'))


def test_selected_and_production_share_only_owned_sync_boundaries():
    import ast
    tree = ast.parse(inspect.getsource(backend))
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CanonicalProductionSourceBackend')
    methods = {n.name:n for n in owner.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name in ('prepare_registered', 'collect'):
        calls = [n for n in ast.walk(methods[name]) if isinstance(n, ast.Call)]
        direct = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'seal_collection']
        threaded = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == '_source_sync'
                    and n.args and isinstance(n.args[0], ast.Name) and n.args[0].id == 'seal_collection']
        assert not direct and len(threaded) == 1
    prepared = [n for n in ast.walk(methods['prepare_registered']) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == '_source_sync'
                and n.args and isinstance(n.args[0], ast.Name) and n.args[0].id == 'prepare_child']
    assert len(prepared) == 1 and any(k.arg == 'on_cancel' for k in prepared[0].keywords)
