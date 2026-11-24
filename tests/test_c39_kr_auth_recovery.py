"""C31 auth boundary backport and the single C39 KR date, entirely synthetic."""
import asyncio
from dataclasses import replace
from datetime import datetime
import json
import os
from pathlib import Path
import socket
import sqlite3

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import codex_runtime_binding as binding
from app.services import codex_runtime_state_service as runtime
from app.services.official_codex_shadow_transport_service import OfficialShadowError, file_sha256
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests.test_c22aq_runtime_parity import installed
from tests.test_local_launchd_entry import configuration, code_pin


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C39_NO_NETWORK_DB_OR_MODEL')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr('subprocess.Popen', denied)
    monkeypatch.setattr(runtime, '_sqlite_wal_write_probe', lambda path: None)


def test_c31_inode_replacement_legacy_review_and_executable_drift(installed, tmp_path):
    value, inspection, path = installed
    auth = Path(value.auth_source)
    inspection['auth_reference'].update(device=-1, inode=-1, uid=-1, mode='0o000')
    path.write_text(json.dumps(inspection))
    value = binding.freeze_current_binding(inspection_path=path, qualification_path=tmp_path/'new-review.json', profile=SOL_HIGH_V1)
    qualified = json.loads(value.qualification_path.read_bytes())
    qualified['auth_reference'].update(device=-1, inode=-1, uid=-1, mode='0o000')
    value.qualification_path.write_text(json.dumps(qualified))
    value = replace(value, qualification_sha256=file_sha256(value.qualification_path))
    old_inode = auth.stat().st_ino
    replacement = auth.with_suffix('.replacement')
    replacement.write_bytes(b'{}')
    replacement.chmod(0o600)
    replacement.replace(auth)
    assert auth.stat().st_ino != old_inode
    binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
    assert binding.parent_environment(value)['HOME'] == value.home
    assert binding.auth_identity(auth) == dict(path=str(auth), exists=True, readable=True, content_read=False)
    with pytest.raises(OfficialShadowError, match='EXECUTABLE_DRIFT'):
        binding.validate_binding(replace(value, executable_sha256='0'*64), str(value.executable), profile=SOL_HIGH_V1)


def test_c31_missing_auth_denies_binding_and_runtime(installed, tmp_path):
    value, _, _ = installed
    auth = Path(value.auth_source)
    auth.unlink()
    with pytest.raises(OfficialShadowError, match='AUTH_REFERENCE_MISSING'):
        binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
    with pytest.raises(runtime.CodexRuntimeStateError, match='auth_reference_missing'):
        runtime.prepare_codex_runtime_state(tmp_path/'runtime', namespace='missing', auth_source=auth)


def test_c31_actual_open_failure_denies(installed, tmp_path, monkeypatch):
    value, _, _ = installed
    auth = Path(value.auth_source)
    original = Path.open
    def denied_auth(path, *args, **kwargs):
        if path == auth:
            raise PermissionError('synthetic-unreadable')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', denied_auth)
    with pytest.raises(OfficialShadowError, match='AUTH_REFERENCE_UNREADABLE'):
        binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
    with pytest.raises(runtime.CodexRuntimeStateError, match='auth_reference_unreadable'):
        runtime.prepare_codex_runtime_state(tmp_path/'runtime', namespace='unreadable', auth_source=auth)


def test_c31_isolated_symlink_and_different_route_denied(installed, tmp_path, monkeypatch):
    value, _, _ = installed
    environment = binding.invocation_environment(value, root=tmp_path/'runtime', namespace='isolated')
    home = Path(environment['CODEX_HOME'])
    reference = home/'auth.json'
    assert reference.is_symlink() and reference.resolve() == Path(value.auth_source)
    assert binding.auth_identity(reference) == binding.auth_identity(value.auth_source)
    reference.unlink()
    reference.write_bytes(b'{}')
    with pytest.raises(runtime.CodexRuntimeStateError, match='plaintext_copy_forbidden'):
        runtime.prepare_codex_runtime_state(tmp_path/'runtime', namespace='isolated', auth_source=Path(value.auth_source))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path/'different-home'))
    with pytest.raises(OfficialShadowError):
        binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)


def test_exact_c39_date_completed_session_scope_and_unchanged_us():
    tag = job.KR_RECOVERY_20261123_TAG
    assert job.one_shot_scope('kr', tag) is False
    for market, wrong in (('us', tag), ('kr', 'kr-20261123-00000000')):
        with pytest.raises(ValueError, match='tag_scope'):
            job.one_shot_scope(market, wrong)
    for stamp in ('2026-11-22T16:00:00+09:00', '2026-11-23T15:29:00+09:00', '2026-11-24T16:00:00+09:00'):
        assert job.latest_one_shot_session('kr', datetime.fromisoformat(stamp), one_shot_tag=tag) is None
    assert str(job.latest_one_shot_session('kr', datetime.fromisoformat('2026-11-23T15:35:00+09:00'), one_shot_tag=tag)) == '2026-11-23'
    assert job.latest_one_shot_session('kr', datetime(2026, 11, 23, 16), one_shot_tag=tag) is None
    assert job._one_shot_deadline(tag) == datetime.fromisoformat('2026-11-24T00:00:00+09:00')
    for old in job.US_FULL_20261121_SLOTS:
        assert job.one_shot_scope('us', old) is False
        assert job._us_full_one_shot_window(old) is not None


def test_c39_same_day_caller_new_output_and_no_replay(tmp_path, monkeypatch):
    code_pin(monkeypatch)
    path, _ = configuration(tmp_path, market='kr')
    prior = tmp_path/'runs/kr-2026-11-23'
    prior.mkdir(parents=True)
    (prior/'terminal.json').write_text('OLD_FAILURE_KEEP')
    calls = []
    async def cycle(config, directory, session, *, one_shot_tag):
        calls.append((directory, session, one_shot_tag))
        return dict(status='SYNTHETIC_NO_SEND', normal_messages_sent=False)
    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    now = datetime.fromisoformat('2026-11-23T16:30:00+09:00')
    tag = job.KR_RECOVERY_20261123_TAG
    result = asyncio.run(job.run_local_scheduled(path, 'kr', now=now, one_shot_tag=tag))
    assert result['status'] == 'SYNTHETIC_NO_SEND'
    directory = tmp_path/'runs/one-shot/2026-11-23'/tag
    assert calls == [(directory, '2026-11-23', tag)]
    intent = json.loads((directory/'intent.json').read_bytes())
    assert intent['max_http'] == 334 and intent['max_models'] == 18 and intent['source_seconds'] == 600
    assert intent['b2_retry_policy'] is None and intent['normal_messages_sent'] is False
    assert asyncio.run(job.run_local_scheduled(path, 'kr', now=now, one_shot_tag=tag))['reason'] == 'SESSION_ALREADY_CONSUMED'
    assert len(calls) == 1 and (prior/'terminal.json').read_text() == 'OLD_FAILURE_KEEP'
