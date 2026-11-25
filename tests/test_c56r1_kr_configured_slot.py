"""Configured KR full-market scheduling; no live I/O."""
import asyncio
from datetime import datetime
import fcntl
import json
import socket
import sqlite3
import subprocess

import pytest

from app.jobs import unified_market_snapshot as job
from app.services.model_timeout_retry import B2_PER_TICKER_ONE_RETRY_V1
from tests.test_local_launchd_entry import configuration, code_pin

TAG = 'kr-20261125-c56r1a2b'
START = '2026-11-25T18:30:00+09:00'


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('configured_slot_test_no_live_io')
    for owner, name in ((socket.socket, 'connect'), (socket.socket, 'connect_ex'),
                        (socket, 'getaddrinfo'), (sqlite3, 'connect'),
                        (subprocess, 'Popen'), (asyncio, 'create_subprocess_exec')):
        monkeypatch.setattr(owner, name, denied)


def configured(folder, **overrides):
    path, value = configuration(folder, market='kr')
    value.update(market_b2_timeout_retry=True, one_shot=dict(
        tag=TAG, scheduled_at=START, target_session='2026-11-25'))
    value.update(overrides)
    path.write_text(json.dumps(value))
    return path


def test_kr_slot_exact_market_date_and_deadline(tmp_path):
    config = job.read_local_configuration(configured(tmp_path), 'kr')
    assert job.one_shot_scope('kr', TAG, config=config) is False
    assert job._local_model_cap(config, TAG) == 27
    assert job.latest_one_shot_session('kr', datetime.fromisoformat(START),
        one_shot_tag=TAG, config=config).isoformat() == '2026-11-25'
    assert job._one_shot_deadline(TAG, config) == datetime.fromisoformat('2026-11-25T23:00:00+09:00')
    assert config.model_dump(mode='json')['one_shot']['tag'] == TAG
    for market, tag in (('us', TAG), ('kr', None), ('kr', 'kr-20261125-c56r1a2c')):
        with pytest.raises(ValueError, match='local_one_shot_configuration_tag_mismatch'):
            job.one_shot_scope(market, tag, config=config)


@pytest.mark.parametrize('overrides', [
    dict(one_shot=dict(tag='us-20261125-c56r1a2b', scheduled_at=START, target_session='2026-11-25')),
    dict(one_shot=dict(tag='kr-20261124-c56r1a2b', scheduled_at=START, target_session='2026-11-25')),
    dict(one_shot=dict(tag='kr-20261123-c42b84e7a', scheduled_at='2026-11-23T18:30:00+09:00',
                       target_session='2026-11-23')),
    dict(us_night_policy='OPTIONAL_CURRENT_PROBE'),
])
def test_wrong_market_date_legacy_tag_or_us_policy_rejected(tmp_path, overrides):
    with pytest.raises(ValueError):
        job.read_local_configuration(configured(tmp_path, **overrides), 'kr')


@pytest.mark.parametrize('scheduled,target,tag,now,reason', [
    (START, '2026-11-25', TAG, '2026-11-25T18:29:59+09:00', 'ONE_SHOT_SLOT_CLOSED'),
    (START, '2026-11-25', TAG, '2026-11-25T18:40:00+09:00', 'ONE_SHOT_SLOT_CLOSED'),
    (START, '2026-11-25', TAG, '2026-11-26T18:30:00+09:00', 'ONE_SHOT_DATE_CLOSED'),
    (START, '2026-11-25', TAG, '2027-11-25T18:30:00+09:00', 'ONE_SHOT_DATE_CLOSED'),
    (START, '2026-11-24', TAG, START, 'SESSION_NOT_COMPLETED_OR_CLOSED'),
    ('2026-11-25T15:20:00+09:00', '2026-11-25', TAG, '2026-11-25T15:20:00+09:00',
     'SESSION_NOT_COMPLETED_OR_CLOSED'),
    ('2026-11-28T18:30:00+09:00', '2026-11-28', 'kr-20261128-c56r1a2b',
     '2026-11-28T18:30:00+09:00', 'SESSION_NOT_COMPLETED_OR_CLOSED'),
])
def test_closed_slot_does_not_consume_intent(tmp_path, monkeypatch, scheduled, target, tag, now, reason):
    path = configured(tmp_path, one_shot=dict(tag=tag, scheduled_at=scheduled, target_session=target))
    monkeypatch.setattr(job, '_local_registered_cycle', lambda *a, **k: pytest.fail('no campaign'))
    row = asyncio.run(job.run_local_scheduled(path, 'kr', now=datetime.fromisoformat(now), one_shot_tag=tag))
    assert row['status'] == 'NO_RUN' and row['reason'] == reason
    assert not (tmp_path/'runs').exists()


def test_kr_single_consumption_preserves_regular_failure_and_policy(tmp_path, monkeypatch):
    path = configured(tmp_path)
    code_pin(monkeypatch)
    now = datetime.fromisoformat(START)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz is not None else now.replace(tzinfo=None)

    monkeypatch.setattr(job, 'datetime', FrozenDateTime)
    original = tmp_path/'runs/kr-2026-11-25/terminal.json'
    original.parent.mkdir(parents=True)
    original.write_bytes(b'original failure receipt')
    calls = []

    async def cycle(config, directory, session, *, one_shot_tag=None):
        calls.append((directory, session, one_shot_tag))
        return dict(status='SYNTHETIC_NO_SEND', normal_messages_sent=False)

    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    row = asyncio.run(job.run_local_scheduled(path, 'kr', now=now, one_shot_tag=TAG))
    generation = tmp_path/'runs/one-shot/2026-11-25'/TAG
    assert row['normal_messages_sent'] is False
    assert calls == [(generation, '2026-11-25', TAG)]
    intent = json.loads((generation/'intent.json').read_bytes())
    assert (intent['max_http'], intent['max_models'], intent['source_seconds']) == (334, 27, 600)
    assert intent['market_timeout_retry_cap'] == 1 and intent['b2_retry_policy'] == B2_PER_TICKER_ONE_RETRY_V1
    assert intent['normal_messages_sent'] is False and 'us_night_policy' not in intent
    assert (generation.parent/(TAG+'.intent.json')).is_file()
    assert asyncio.run(job.run_local_scheduled(path, 'kr', now=now, one_shot_tag=TAG))['reason'] == 'SESSION_ALREADY_CONSUMED'
    assert len(calls) == 1 and original.read_bytes() == b'original failure receipt'


def test_shared_lease_busy_before_intent(tmp_path, monkeypatch):
    path = configured(tmp_path)
    code_pin(monkeypatch)
    with (tmp_path/'pair.lease').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        row = asyncio.run(job.run_local_scheduled(path, 'kr',
            now=datetime.fromisoformat(START), one_shot_tag=TAG))
    assert row['reason'] == 'NO_RUN_LOCK_BUSY'
    assert not list((tmp_path/'runs').glob('**/intent.json'))


def test_existing_us_config_and_regular_kr_contract_retained(tmp_path):
    path, value = configuration(tmp_path/'us', market='us')
    value.update(us_night_policy='OPTIONAL_CURRENT_PROBE', one_shot=dict(
        tag='us-20261126-c55a1b2c', scheduled_at='2026-11-26T08:10:00+09:00',
        target_session='2026-11-25'))
    path.write_text(json.dumps(value))
    config = job.read_local_configuration(path, 'us')
    assert job.latest_one_shot_session('us', datetime.fromisoformat('2026-11-26T08:10:00+09:00'),
        one_shot_tag=config.one_shot.tag, config=config).isoformat() == '2026-11-25'
    assert job._local_model_cap(config, config.one_shot.tag) == 42
    path, _ = configuration(tmp_path/'kr', market='kr')
    config = job.read_local_configuration(path, 'kr')
    assert 'one_shot' not in config.model_dump(mode='json')
    assert 'us_night_policy' not in config.model_dump(mode='json')
    assert job.one_shot_scope('kr', None, config=config) is False
