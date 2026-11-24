"""Real temporary files/processes; no financial, model or database execution."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.services import model_runtime_retention as retention
from app.services.codex_runtime_state_service import runtime_state_namespace_hash
from app.services.production_b2_execution import ModelTransportError
from app.services.research_artifact_budget import (
    ArtifactCapacityError, CLI_RESULT_FILENAMES, ResearchArtifactBudget, artifact_scope,
)
from scripts.c51_storage_inventory import inventory
from tests.test_production_model_transport import (
    invocation, payload, transport,
)


def state_for(attempt):
    return attempt / 'runtime-state' / runtime_state_namespace_hash(attempt.name)


def seed(attempt):
    state = state_for(attempt)
    cache = state / 'home/cache/remote_plugin_catalog'
    cache.mkdir(parents=True)
    (cache / 'fixture.bin').write_bytes(b'x' * 8192)
    (state / 'sqlite').mkdir()
    (state / 'sqlite/state.sqlite').write_bytes(b'private invocation state')
    (attempt / 'events.jsonl').write_bytes(b'{"type":"turn.completed"}\n')
    return state


def test_cleanup_unlinks_only_this_namespace_and_preserves_evidence_and_auth(tmp_path, monkeypatch):
    attempt = tmp_path / 'attempt-one'
    state = seed(attempt)
    auth = tmp_path / 'configured-auth'
    auth.write_bytes(b'not credentials')
    (state / 'home/auth.json').symlink_to(auth)
    other = attempt / 'runtime-state/another-namespace'
    other.mkdir()
    (other / 'keep').write_bytes(b'not ours')
    before = (attempt / 'events.jsonl').read_bytes()
    monkeypatch.setattr(retention.os, 'killpg', lambda *args: (_ for _ in ()).throw(ProcessLookupError()))
    receipt = retention.record_invocation_cleanup(attempt, worker_pid=123, worker_reaped=True)
    assert receipt['status'] == 'REMOVED' and receipt['removed_files'] == 3
    assert not state.exists() and (other / 'keep').read_bytes() == b'not ours'
    assert auth.read_bytes() == b'not credentials' and (attempt / 'events.jsonl').read_bytes() == before


def test_live_group_blocks_cleanup_even_when_parent_is_reported_reaped(tmp_path):
    attempt = tmp_path / 'attempt-live'
    state = seed(attempt)
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], start_new_session=True)
    try:
        receipt = retention.retire_invocation_state(attempt, worker_pid=process.pid, worker_reaped=True)
        assert receipt['status'] == 'RETAINED_PROCESS_GROUP_ACTIVE' and state.is_dir()
    finally:
        process.kill()
        process.wait(timeout=5)
    receipt = retention.retire_invocation_state(attempt, worker_pid=process.pid, worker_reaped=True)
    assert receipt['status'] == 'REMOVED' and not state.exists()


@pytest.mark.parametrize('unsafe', ['parent-link', 'state-link', 'unreaped'])
def test_unconfirmed_or_redirected_state_is_never_removed(tmp_path, unsafe):
    attempt = tmp_path / 'attempt'
    state = seed(attempt)
    if unsafe == 'unreaped':
        assert retention.retire_invocation_state(attempt, worker_pid=os.getpid(), worker_reaped=False)[
            'status'] == 'RETAINED_WORKER_NOT_REAPED'
    else:
        redirected = tmp_path / 'outside'
        selected = state.parent if unsafe == 'parent-link' else state
        selected.rename(redirected)
        selected.symlink_to(redirected, target_is_directory=True)
        with pytest.raises(ValueError, match='unsafe_path'):
            retention.retire_invocation_state(attempt, worker_pid=123, worker_reaped=True)
        assert redirected.is_dir()


WORKER = '''
import hashlib,json,pathlib,sys,time
frame=json.loads(sys.stdin.buffer.read())
root=pathlib.Path(frame['directory'])
state=root/'runtime-state'/hashlib.sha256(root.name.encode()).hexdigest()[:24]
cache=state/'home/cache/remote_plugin_catalog'
cache.mkdir(parents=True)
with (cache/'cache.bin').open('wb') as handle:
    handle.truncate((65 if sys.argv[1]=='capacity' else 2)*1024**2)
(root/'events.jsonl').write_text('{"type":"turn.started"}\\n')
(root/'started').touch()
if sys.argv[1] in {'cancel','capacity'}:
    time.sleep(30)
else:
    (root/'raw-output.json').write_bytes(b'{}')
    receipt={'status':'PASS'} if sys.argv[1]=='success' else {'status':'FAIL','error_code':'PROCESS_NONZERO'}
    (root/'transport-receipt.json').write_text(json.dumps(receipt))
    sys.exit(0 if sys.argv[1]=='success' else 1)
'''


@pytest.mark.parametrize('outcome', ['success', 'nonzero', 'cancel'])
def test_real_worker_exit_and_cancel_reclaim_state_without_losing_original_outcome(invocation, tmp_path, outcome):
    item, _ = transport(invocation, tmp_path)
    children = []

    async def factory(*args, **kwargs):
        process = await asyncio.create_subprocess_exec(sys.executable, '-c', WORKER, outcome,
            start_new_session=True, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        children.append(process)
        return process

    item.worker_factory = factory

    async def exercise():
        task = asyncio.create_task(item.request(payload(), model='gpt-5.6-sol', effort='xhigh', timeout=600))
        try:
            if outcome == 'cancel':
                async with asyncio.timeout(5):
                    while not list(item.runtime_root.glob('*/started')):
                        await asyncio.sleep(0.01)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            elif outcome == 'nonzero':
                with pytest.raises(ModelTransportError, match='WORKER_NONZERO'):
                    await task
            else:
                assert await task == b'{}'
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            for process in children:
                if process.returncode is None:
                    process.kill()
                    await process.wait()

    asyncio.run(exercise())
    attempt, = item.runtime_root.glob('*')
    receipt = json.loads((attempt / 'runtime-cleanup.json').read_bytes())
    assert receipt['status'] == 'REMOVED' and receipt['removed_logical_bytes'] == 2 * 1024**2
    assert not state_for(attempt).exists() and (attempt / 'events.jsonl').is_file()
    assert json.loads((attempt / 'parent-exit.json').read_bytes())['child_reaped']
    if outcome != 'cancel':
        assert (attempt / 'raw-output.json').read_bytes() == b'{}'
        assert (attempt / 'transport-receipt.json').is_file()


def test_cleanup_failure_is_secondary_to_model_failure(invocation, tmp_path, monkeypatch):
    from tests.test_production_model_transport import Process

    class Failed(Process):
        async def communicate(self, frame):
            result = await super().communicate(frame)
            seed(Path(self.frame['directory']))
            return result

    process = Failed({'status': 'FAIL', 'error_code': 'PROCESS_NONZERO'}, returncode=1)
    item, _ = transport(invocation, tmp_path, process)
    monkeypatch.setattr(retention.os, 'killpg', lambda *args: (_ for _ in ()).throw(ProcessLookupError()))
    monkeypatch.setattr(retention.shutil, 'rmtree', lambda *args: (_ for _ in ()).throw(OSError('fixture')))
    with pytest.raises(ModelTransportError, match='WORKER_NONZERO'):
        asyncio.run(item.request(payload(), model='gpt-5.6-sol', effort='xhigh', timeout=600))
    attempt = Path(process.frame['directory'])
    assert state_for(attempt).is_dir()
    assert json.loads((attempt / 'runtime-cleanup.json').read_bytes())['status'] == 'RETAINED_CLEANUP_ERROR'


def test_capacity_failure_reaps_worker_frees_state_and_preserves_first_error(invocation, tmp_path, monkeypatch):
    item, _ = transport(invocation, tmp_path)
    budget = ResearchArtifactBudget(roots={item.runtime_root: 'scratch'}, work_cap=64 * 1024**2)
    monkeypatch.setattr(retention.os, 'statvfs', lambda path: SimpleNamespace(f_bavail=8 * 1024**2, f_frsize=4096))
    wait = asyncio.wait
    monkeypatch.setattr(asyncio, 'wait', lambda tasks, timeout: wait(tasks, timeout=0.01))
    children = []

    async def factory(*args, **kwargs):
        process = await asyncio.create_subprocess_exec(sys.executable, '-c', WORKER, 'capacity',
            start_new_session=True, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        children.append(process)
        return process

    item.worker_factory = factory

    async def exercise():
        with artifact_scope(budget):
            with pytest.raises(ArtifactCapacityError, match='RESEARCH_WORK_CAP') as failure:
                await asyncio.wait_for(item.request(payload(), model='gpt-5.6-sol', effort='xhigh', timeout=600), 5)
        assert failure.value.receipt['cap_bytes'] == 64 * 1024**2

    asyncio.run(exercise())
    assert children[0].returncode == -9
    attempt, = item.runtime_root.glob('*')
    receipt = json.loads((attempt / 'runtime-cleanup.json').read_bytes())
    assert receipt['status'] == 'REMOVED' and receipt['removed_logical_bytes'] == 65 * 1024**2
    assert (attempt / 'events.jsonl').is_file() and not state_for(attempt).exists()


def test_repeated_calls_do_not_accumulate_cache_in_work_budget(invocation, tmp_path, monkeypatch):
    from tests.test_production_model_transport import Process

    class Cached(Process):
        async def communicate(self, frame):
            result = await super().communicate(frame)
            state = seed(Path(self.frame['directory']))
            (state / 'home/cache/remote_plugin_catalog/fixture.bin').write_bytes(b'x' * 2 * 1024**2)
            return result

    item, _ = transport(invocation, tmp_path, Cached())
    budget = ResearchArtifactBudget(roots={item.runtime_root: 'scratch'})
    # Exercise retained bytes independently of this test host's available disk.
    monkeypatch.setattr(retention.os, 'statvfs', lambda path: SimpleNamespace(f_bavail=8 * 1024**2, f_frsize=4096))
    monkeypatch.setattr(retention.os, 'killpg', lambda *args: (_ for _ in ()).throw(ProcessLookupError()))
    with artifact_scope(budget):
        for _ in range(3):
            assert asyncio.run(item.request(payload(), model='gpt-5.6-sol', effort='xhigh', timeout=600)) == b'{}'
            assert budget.measure()['total'] < 32 * 1024
    assert 2 * 1024**2 < budget.peak_work < 3 * 1024**2
    assert len(list(item.runtime_root.glob('*/raw-output.json'))) == 3


@pytest.mark.parametrize('state_parent_link', [False, True])
def test_inventory_scopes_roots_deduplicates_links_and_never_reads_auth(tmp_path, monkeypatch, state_parent_link):
    generation, runtime = tmp_path / 'generation', tmp_path / 'runtime'
    (generation / 'results').mkdir(parents=True)
    runtime.mkdir()
    (generation / 'source.bin').write_bytes(b'x' * 100)
    os.link(generation / 'source.bin', generation / 'results/result.bin')
    attempt = runtime / 'attempt'
    state = seed(attempt)
    auth = tmp_path / 'auth'
    auth.write_bytes(b'not credentials')
    (state / 'home/auth.json').symlink_to(auth)
    for name in CLI_RESULT_FILENAMES:
        (attempt / name).write_bytes(b'retained evidence')
    if state_parent_link:
        outside = tmp_path / 'outside-state'
        state.parent.rename(outside)
        state.parent.symlink_to(outside, target_is_directory=True)
    preflight = generation / 'model-runtime-preflight.json'
    preflight.write_text(json.dumps(dict(runtime_root=str(runtime), artifact_roots={
        str(generation): 'source', str(generation / 'results'): 'result', str(runtime): 'scratch'})))
    opened = Path.open

    def guarded(path, *args, **kwargs):
        assert path == preflight
        return opened(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', guarded)
    report = inventory(generation)
    assert report['accounting_kind'] == 'FILESYSTEM_ROOTS_WITH_KNOWN_RECEIPT_OVERRIDES_NOT_FULL_HISTORICAL_BUDGET'
    assert report['totals']['result']['logical_bytes'] == 100 + len(CLI_RESULT_FILENAMES) * len(b'retained evidence')
    assert report['physical_root_totals'][str(generation / 'results')]['logical_bytes'] == 100
    assert report['physical_root_totals'][str(runtime)]['logical_bytes'] == (
        report['totals']['scratch']['logical_bytes'] + len(CLI_RESULT_FILENAMES) * len(b'retained evidence'))
    assert report['totals']['source']['logical_bytes'] == preflight.stat().st_size
    assert report['deleted_files'] == report['credentials_opened'] == 0
    if state_parent_link:
        assert report['runtime_state_candidates'] == []
        assert report['invalid_runtime_state_candidates'] == [dict(attempt=str(attempt), reason='SYMLINK_IN_STATE_PATH')]
        assert report['totals']['scratch']['logical_bytes'] < 8192
    else:
        assert report['totals']['scratch']['logical_bytes'] > 8192
        assert report['runtime_state_candidates'][0]['disposable_state'] == str(state)
    assert state.is_dir()
