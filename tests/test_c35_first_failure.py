"""Changed failure boundary only; no DB, provider or actual CLI processes."""
import asyncio
import errno
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import research_no_send_run as research
from app.services.research_artifact_budget import ArtifactCapacityError, ResearchArtifactBudget, artifact_scope
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from tests import test_per_ticker_b2_kis_session as full


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C35 offline: DB/network/real process forbidden')
    for owner, name in ((socket.socket, 'connect'), (socket.socket, 'connect_ex'),
                        (socket.socket, 'sendto'), (sqlite3, 'connect'),
                        (subprocess, 'Popen'), (asyncio, 'create_subprocess_exec')):
        monkeypatch.setattr(owner, name, denied)


def shortage():
    return ArtifactCapacityError(code='RESEARCH_FREE_SPACE_GUARD', role='free',
        current=12*1024**3-1, projected=12*1024**3-1, cap=12*1024**3)


def registered(monkeypatch, result, *, stop_fails=False):
    from app.services.production_source_backend import CanonicalProductionSourceBackend
    stopped, rendered, closed = [], [], []
    def stop(reason):
        stopped.append(reason)
        if stop_fails:
            raise OSError(errno.ENOSPC, 'synthetic filesystem full')
    ledger = SimpleNamespace(bind_model_plan=lambda child: None, stop=stop,
        rendered_market=lambda child, value: rendered.append(value))
    child = SimpleNamespace(verify=lambda: None, market='us', binding=lambda: {},
        plan=SimpleNamespace(sha256=digest('plan'),cohort=SimpleNamespace(cutoff='2026-11-20T21:00:00+00:00')),
        owner=SimpleNamespace(close=lambda: closed.append(True)))
    async def prepare(**kwargs):
        return child, {}
    async def run(*args):
        return result
    monkeypatch.setattr(CanonicalProductionSourceBackend, 'prepare_registered', prepare)
    monkeypatch.setattr(job, 'load_adapter', lambda *args, **kwargs: object())
    monkeypatch.setattr(job, 'build_engine', lambda *args, **kwargs: SimpleNamespace(run=run))
    value = asyncio.run(job.run_registered(object(),source=dict(run_ledger=ledger,
        frozen={'stock_plan': {'implementation_sha': digest('code')}}), model=dict(run_ledger=ledger),
        mode='LIVE_NO_SEND', record_market_terminal=True))
    assert value is result and closed == [True]
    return stopped, rendered


def test_b2_intent_capacity_failure_survives_guard_and_registered_caller(tmp_path, monkeypatch):
    original = research.PreparedResearchBridge.stage
    original_check = ResearchArtifactBudget.check
    failed = []
    async def stage(self, request, directory):
        if request['stage'] == 'B2':
            failed.append(True)
            raise shortage()
        return await original(self, request, directory)
    def check(self, **kwargs):
        if failed:
            raise shortage()
        return original_check(self, **kwargs)
    monkeypatch.setattr(research.PreparedResearchBridge, 'stage', stage)
    monkeypatch.setattr(ResearchArtifactBudget, 'check', check)
    f = full.scenario(tmp_path, monkeypatch, {})
    assert len(f.calls) == 16 and all(r['stage'] != 'B2' for r in f.calls)
    assert [r['status'] for r in f.result['stage_receipts']] == ['PASS']*4+['INTENT']
    assert f.result['first_failure']['code'] == 'RESEARCH_FREE_SPACE_GUARD'
    assert f.result['first_failure']['type'] == 'ArtifactCapacityError'
    assert f.result['first_failure']['stage'] == 'B2'
    assert f.result['storage_failure']['cap_bytes'] == 12*1024**3
    raw = (f.cycle/'first-failure.json').read_bytes()
    assert len(raw) <= 4096 and json.loads(raw) == f.result['first_failure']
    assert not (f.cycle/'terminal.json').exists() and f.budget.stopped
    assert 'messages' not in f.result and not f.result['normal_messages_sent']
    stopped, rendered = registered(monkeypatch, f.result, stop_fails=True)
    assert stopped == ['RESEARCH_FREE_SPACE_GUARD'] and not rendered
    assert f.result['error_chain'][0]['type'] == 'ArtifactCapacityError'


@pytest.mark.parametrize('terminal_error', ['capacity', 'ENOSPC'])
def test_terminal_write_failure_never_masks_primary(tmp_path, monkeypatch, terminal_error):
    original = research.durable_json
    primary = ValueError('synthetic private prompt must not enter receipt')
    def write(path, value, **kwargs):
        if Path(path).name == 'intent.json':
            raise primary
        if Path(path).name == 'terminal.json':
            raise shortage() if terminal_error == 'capacity' else OSError(errno.ENOSPC, 'full')
        return original(path, value, **kwargs)
    monkeypatch.setattr(research, 'durable_json', write)
    stopped = []
    bridge = SimpleNamespace(child_binding={}, model=SimpleNamespace(call_budget=SimpleNamespace(
        stop=lambda **kwargs: stopped.append(kwargs))))
    budget = ResearchArtifactBudget(roots={tmp_path: 'result'})
    result = asyncio.run(research._run(bridge,tmp_path,local_output_rejection=False,artifacts=budget))
    first = result['first_failure'].copy()
    assert result['error_chain'][0]['type'] == 'ValueError' and first['stage'] == 'INITIALIZE'
    assert 'synthetic private' not in (tmp_path/'first-failure.json').read_text()
    assert stopped == [dict(global_stop=True)] and result['status'] == 'FAILED_NO_SEND'
    _, rendered = registered(monkeypatch,result)
    assert not rendered and result['first_failure'] == first


def test_synthetic_full_15_hash_terminal_and_caller_unchanged(tmp_path, monkeypatch):
    f = full.scenario(tmp_path,monkeypatch,{})
    assert f.result['status'] == research.TERMINAL and len(f.result['messages']) == 15
    assert len(f.calls) == 29 and f.budget.retry_used == 0
    assert digest(f.result['messages']) == f.result['messages_sha256']
    assert json.loads((f.cycle/'terminal.json').read_bytes()) == f.result
    assert not (f.cycle/'first-failure.json').exists() and 'first_failure' not in f.result
    stopped, rendered = registered(monkeypatch,f.result)
    assert not stopped and rendered == [f.result]


def test_terminal_only_enospc_after_render_drops_messages_and_stops(tmp_path, monkeypatch):
    original = research.durable_json
    def write(path, value, **kwargs):
        if Path(path).name == 'terminal.json':
            raise OSError(errno.ENOSPC, 'synthetic full disk after render')
        return original(path, value, **kwargs)
    monkeypatch.setattr(research,'durable_json',write)
    f = full.scenario(tmp_path,monkeypatch,{})
    assert len(f.calls) == 29 and f.budget.stopped and f.budget.retry_used == 0
    assert f.result['status'] == 'FAILED_NO_SEND' and 'messages' not in f.result
    assert f.result['first_failure']['type'] == 'OSError' and f.result['first_failure']['stage'] == 'RENDER'
    assert f.result['terminal_write_blocked']['errno'] == errno.ENOSPC
    assert (f.cycle/'first-failure.json').stat().st_size <= 4096
    stopped, rendered = registered(monkeypatch,f.result)
    assert stopped == ['RESEARCH_STAGE_FAILED'] and not rendered


def test_guard_still_blocks_payload_and_does_not_retry(tmp_path, monkeypatch):
    budget = ResearchArtifactBudget(roots={tmp_path: 'result'})
    monkeypatch.setattr('app.services.research_artifact_budget.os.statvfs',
        lambda path: SimpleNamespace(f_bavail=1,f_frsize=4096))
    with artifact_scope(budget), pytest.raises(ArtifactCapacityError,match='RESEARCH_FREE_SPACE_GUARD'):
        durable_json(tmp_path/'blocked-model-body.json',{'payload':'not written'})
    assert not (tmp_path/'blocked-model-body.json').exists()
    state = dict(first_failure=research._first_failure(shortage(),'B2'))
    with artifact_scope(budget): research._persist_first_failure(tmp_path,state)
    assert state['first_failure_receipt']['status'] == 'PERSISTED'
    assert (tmp_path/'first-failure.json').stat().st_size <= 4096


def test_emergency_receipt_enospc_bounded_exclusive_and_no_symlink(tmp_path, monkeypatch):
    state = dict(first_failure=research._first_failure(shortage(),'B2'))
    original = research.os.open
    def no_space(path, flags, *args, **kwargs):
        if path == '.first-failure.pending':
            raise OSError(errno.ENOSPC,'synthetic disk full')
        return original(path, flags, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(research.os,'open',no_space)
        research._persist_first_failure(tmp_path,state)
    assert state['first_failure_receipt'] == dict(status='UNAVAILABLE',type='OSError',errno=errno.ENOSPC)
    research._persist_first_failure(tmp_path,state)
    first = (tmp_path/'first-failure.json').read_bytes()
    research._persist_first_failure(tmp_path,dict(first_failure={'code':'do_not_overwrite'}))
    assert (tmp_path/'first-failure.json').read_bytes() == first
    folder = tmp_path/'other'; folder.mkdir()
    oversized = dict(first_failure={'unexpected':'x'*4097})
    research._persist_first_failure(folder,oversized)
    assert oversized['first_failure_receipt']['status'] == 'UNAVAILABLE' and not list(folder.iterdir())
    alias = tmp_path/'alias'; alias.symlink_to(folder,target_is_directory=True)
    research._persist_first_failure(alias,state)
    assert state['first_failure_receipt']['status'] == 'UNAVAILABLE' and not list(folder.iterdir())
