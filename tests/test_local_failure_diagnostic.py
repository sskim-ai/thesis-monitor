"""Synthetic exception visibility only; no Source replay, DB or live transport."""
import asyncio
from datetime import datetime
import json
import socket
import sqlite3

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import production_source_backend as backend
from tests.test_local_launchd_entry import configuration, code_pin


@pytest.fixture(autouse=True)
def offline_diagnostic_only(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('diagnostic_test_no_network_or_DB')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)


def execute(folder, monkeypatch, cycle):
    path, _ = configuration(folder)
    code_pin(monkeypatch)
    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    return job.run_local_scheduled(path, 'us', now=datetime.fromisoformat('2026-11-20T08:26:00+09:00'))


def test_original_frame_and_allowlisted_code_without_source_replay(tmp_path, monkeypatch):
    original = []
    async def cycle(config, directory, session):
        try:
            await backend.CanonicalProductionSourceBackend.prepare_registered(
                settings=None, registration_owner=None, run_ledger=None, root=None,
                frozen={}, compiler=None, credentials=None, policy=None, deadline=None)
        except ValueError as exc:
            original.append(exc)
            raise
    with pytest.raises(ValueError) as caught:
        asyncio.run(execute(tmp_path, monkeypatch, cycle))
    assert caught.value is original[0]
    folder = tmp_path/'runs/us-2026-11-19'
    receipt = json.loads((folder/'failure-diagnostic.json').read_bytes())
    assert set(receipt) == {'exception_class', 'stable_error_code', 'last_application_frame', 'stage', 'NO_SEND',
        'application_frames', 'market', 'target_session', 'source_generation', 'code_commit',
        'runtime_module_sha256', 'source_seal_file_sha256', 'recorded_before_owner_cleanup'}
    assert receipt['exception_class'] == 'ValueError'
    assert receipt['stable_error_code'] == 'production_registered_selected_plan_required'
    assert receipt['stage'] == 'SOURCE_PREPARATION_OR_COLLECTION' and receipt['NO_SEND'] is True
    frame = receipt['last_application_frame']
    assert frame['basename'] == 'production_source_backend.py' and frame['function'] == 'prepare_registered'
    assert type(frame['line']) is int and frame['line'] > 0 and '/' not in frame['basename']
    assert json.loads((folder/'terminal.json').read_bytes()) == dict(
        status='STOPPED_NO_SEND', error_type='ValueError', normal_messages_sent=False)


def test_collector_return_marker_only_labels_stage_not_source_acceptance(tmp_path, monkeypatch):
    async def cycle(config, directory, session):
        (directory/'source-time-result.json').write_text(json.dumps(dict(
            status='COLLECTOR_RETURNED_REQUIRES_SOURCE_ADMISSION')))
        await backend.CanonicalProductionSourceBackend.prepare_registered(
            settings=None, registration_owner=None, run_ledger=None, root=None,
            frozen={}, compiler=None, credentials=None, policy=None, deadline=None)
    with pytest.raises(ValueError):
        asyncio.run(execute(tmp_path, monkeypatch, cycle))
    folder = tmp_path/'runs/us-2026-11-19'
    receipt = json.loads((folder/'failure-diagnostic.json').read_bytes())
    assert receipt['stage'] == 'SOURCE_POST_COLLECTION' and receipt['NO_SEND'] is True
    assert json.loads((folder/'terminal.json').read_bytes())['status'] == 'STOPPED_NO_SEND'
    assert not (folder/'campaign.jsonl').exists()


def test_secret_payload_and_non_allowlisted_identifier_are_not_saved(tmp_path, monkeypatch):
    for index, secret in enumerate(('api_key=DO_NOT_EXPORT_SYNTHETIC_SECRET',
            'selected_private_DO_NOT_EXPORT_SYNTHETIC_SECRET', {'token': 'DO_NOT_EXPORT_SYNTHETIC_SECRET'})):
        error = ValueError(secret)
        async def cycle(config, directory, session):
            raise error
        folder = tmp_path/str(index)
        with pytest.raises(ValueError) as caught:
            asyncio.run(execute(folder, monkeypatch, cycle))
        assert caught.value is error
        output = folder/'runs/us-2026-11-19'
        receipt = json.loads((output/'failure-diagnostic.json').read_bytes())
        assert receipt['stable_error_code'] is None and receipt['NO_SEND'] is True
        assert receipt['last_application_frame']['basename'] == 'unified_market_snapshot.py'
        for path in output.glob('*.json'):
            assert b'DO_NOT_EXPORT' not in path.read_bytes() and b'api_key=' not in path.read_bytes()


def test_diagnostic_write_error_keeps_original_stop_and_consumed_attempt(tmp_path, monkeypatch):
    from app.services import unified_run_artifacts as artifacts
    real = artifacts.durable_json
    def write(path, value, **kwargs):
        if path.name == 'failure-diagnostic.json':
            raise OSError('SYNTHETIC_DIAGNOSTIC_DISK_FAILURE')
        return real(path, value, **kwargs)
    monkeypatch.setattr(artifacts, 'durable_json', write)
    error = ValueError('SYNTHETIC_ORIGINAL_STOP')
    calls = []
    async def cycle(*args):
        calls.append(True)
        raise error
    with pytest.raises(ValueError) as caught:
        asyncio.run(execute(tmp_path, monkeypatch, cycle))
    assert caught.value is error
    assert asyncio.run(execute(tmp_path, monkeypatch, cycle))['reason'] == 'SESSION_ALREADY_CONSUMED'
    assert len(calls) == 1
    folder = tmp_path/'runs/us-2026-11-19'
    assert json.loads((folder/'terminal.json').read_bytes())['error_type'] == 'ValueError'
    assert not (folder/'failure-diagnostic.json').exists()


def test_cancel_stays_cancelled_and_success_has_no_failure_receipt(tmp_path, monkeypatch):
    cancelled = asyncio.CancelledError('SYNTHETIC_PRIVATE_CANCEL_DETAIL')
    async def cancel(*args):
        raise cancelled
    with pytest.raises(asyncio.CancelledError) as caught:
        asyncio.run(execute(tmp_path/'cancel', monkeypatch, cancel))
    assert caught.value is cancelled
    folder = tmp_path/'cancel/runs/us-2026-11-19'
    receipt = json.loads((folder/'failure-diagnostic.json').read_bytes())
    assert receipt['exception_class'] == 'CancelledError' and receipt['stable_error_code'] is None
    assert b'SYNTHETIC_PRIVATE' not in (folder/'failure-diagnostic.json').read_bytes()
    async def success(*args):
        return dict(status='SYNTHETIC_NO_SEND', normal_messages_sent=False)
    result = asyncio.run(execute(tmp_path/'success', monkeypatch, success))
    assert result['status'] == 'SYNTHETIC_NO_SEND'
    assert not (tmp_path/'success/runs/us-2026-11-19/failure-diagnostic.json').exists()


def test_first_diagnostic_is_sealed_before_cleanup_and_not_overwritten(tmp_path):
    from hashlib import sha256
    from types import SimpleNamespace
    config = SimpleNamespace(market='us', code_commit='3'*40)
    original = ValueError('selected_whole_original_stock_incomplete')
    cleanup = ValueError('SYNTHETIC_CLEANUP_PRIVATE_DETAIL')
    seal_body = b'{"receipt_sha256":"synthetic"}\n'
    (tmp_path/'source-seal.json').write_bytes(seal_body)
    with pytest.raises(ValueError) as caught:
        try:
            try:
                raise original
            except BaseException as exc:
                job._record_local_failure(tmp_path, exc, config=config, session='2026-11-19',
                    generation='local-us-2026-11-19-source', before_owner_cleanup=True)
                raise
            finally:
                path = tmp_path/'failure-diagnostic.json'
                body = path.read_bytes()
                receipt = json.loads(body)
                integrity = json.loads((tmp_path/'failure-diagnostic-sha256.json').read_bytes())
                assert receipt['recorded_before_owner_cleanup'] is True
                assert integrity == dict(file=path.name, bytes=len(body), sha256=sha256(body).hexdigest())
                assert receipt['source_seal_file_sha256'] == sha256(seal_body).hexdigest()
                raise cleanup
        except BaseException as exc:
            job._record_local_failure(tmp_path, exc, config=config, session='2026-11-19')
            raise
    assert caught.value is cleanup
    assert (tmp_path/'failure-diagnostic.json').read_bytes() == body
    assert receipt['stable_error_code'] == original.args[0]
    assert receipt['code_commit'] == config.code_commit and receipt['market'] == 'us'
    assert receipt['source_generation'] == 'local-us-2026-11-19-source'
    assert len(receipt['application_frames']) <= 8
    assert b'SYNTHETIC_CLEANUP_PRIVATE_DETAIL' not in body


def test_registered_cycle_records_in_handler_before_original_finally():
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(job._local_registered_cycle))
    cycle = tree.body[0]
    guarded = next(node for node in cycle.body if isinstance(node, ast.Try) and node.finalbody)
    handler = guarded.handlers[0]
    assert isinstance(handler.type, ast.Name) and handler.type.id == 'BaseException'
    call = handler.body[0].value
    assert call.func.id == '_record_local_failure'
    assert next(k.value.value for k in call.keywords if k.arg == 'before_owner_cleanup') is True
    assert isinstance(handler.body[1], ast.Raise) and handler.body[1].exc is None
    assert any(isinstance(node, ast.Attribute) and node.attr == 'revoke_prospective_owner'
        for node in ast.walk(guarded.finalbody[0]))


def test_precleanup_diagnostic_disk_error_does_not_replace_original(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from app.services import unified_run_artifacts as artifacts
    def denied(*args, **kwargs):
        raise OSError('SYNTHETIC_PRIVATE_DISK_DETAIL')
    monkeypatch.setattr(artifacts, 'durable_json', denied)
    original = asyncio.CancelledError('SYNTHETIC_PRIVATE_CANCEL_DETAIL')
    with pytest.raises(asyncio.CancelledError) as caught:
        try:
            raise original
        except BaseException as exc:
            job._record_local_failure(tmp_path, exc, config=SimpleNamespace(market='us', code_commit='3'*40),
                session='2026-11-19', before_owner_cleanup=True)
            raise
    assert caught.value is original
    assert not list(tmp_path.iterdir())
