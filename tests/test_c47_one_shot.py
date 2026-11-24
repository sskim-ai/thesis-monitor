"""Prospective one-shot scheduling, no live worker/model/provider execution."""
import asyncio
from datetime import datetime, timedelta
import fcntl
import json

import pytest

from app.jobs import unified_market_snapshot as job
from tests.test_local_launchd_entry import configuration, code_pin
from tests.test_c28_integration import clock

TAG = 'us-20261124-c47a1b2c'


def configured(tmp_path, at='2026-11-24T10:00:00+09:00', target='2026-11-23'):
    path, raw = configuration(tmp_path)
    raw.update(us_night_policy='EXCLUDED_BEFORE_COLLECTION',
        one_shot=dict(tag=TAG, scheduled_at=at, target_session=target))
    path.write_text(json.dumps(raw))
    return path, job.read_local_configuration(path, 'us')


@pytest.mark.parametrize('stamp', ['2026-11-24T10:00:00+09:00','2026-11-24T20:00:00+09:00'])
def test_prospective_slot_keeps_latest_completed_session_and_original_limits(tmp_path, stamp):
    _, config = configured(tmp_path, stamp)
    start = datetime.fromisoformat(stamp)
    assert job._us_full_one_shot_window(TAG, config) == (start, start + timedelta(minutes=10))
    assert job._one_shot_deadline(TAG, config) == start + timedelta(seconds=16200)
    assert not job.one_shot_scope('us', TAG, config=config)
    assert job._local_model_cap(config, TAG) == 42
    assert str(job.latest_one_shot_us_session(start, one_shot_tag=TAG, config=config)) == '2026-11-23'
    assert job.latest_one_shot_us_session(start + timedelta(days=1), one_shot_tag=TAG, config=config) is None
    for tag in (None, TAG+'x', 'us-20261124-c38f2a6d'):
        with pytest.raises(ValueError, match='configuration_tag_mismatch'):
            job.one_shot_scope('us', tag, config=config)


def test_default_config_preserves_prior_serialization_and_kr_scope(tmp_path):
    path, _ = configuration(tmp_path)
    default = job.read_local_configuration(path, 'us')
    assert 'one_shot' not in default.model_dump(mode='json')
    assert 'us_night_policy' not in default.model_dump(mode='json')
    _, configured_us = configured(tmp_path)
    raw = configured_us.model_dump(mode='json')
    for change in (dict(market='kr'), dict(one_shot=dict(raw['one_shot'], scheduled_at='2026-11-24T10:00:00')),
                   dict(one_shot=dict(raw['one_shot'], tag='us-20261125-c47a1b2c'))):
        with pytest.raises(ValueError):
            job.LocalScheduleConfiguration.model_validate(dict(raw, **change))


def test_closed_slot_wrong_target_and_busy_lease_never_start_worker(tmp_path, monkeypatch):
    path, config = configured(tmp_path)
    code_pin(monkeypatch)
    start = config.one_shot.scheduled_at
    monkeypatch.setattr(job, '_local_registered_cycle', lambda *a, **kw:pytest.fail('worker_must_not_start'))
    for at in (start-timedelta(seconds=1),start+timedelta(minutes=10)):
        assert asyncio.run(job.run_local_scheduled(path,'us',now=at,one_shot_tag=TAG))['reason'] == 'ONE_SHOT_SLOT_CLOSED'
    with (tmp_path/'pair.lease').open('rb') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert asyncio.run(job.run_local_scheduled(path,'us',now=start,one_shot_tag=TAG))['reason'] == 'NO_RUN_LOCK_BUSY'
    path, _ = configured(tmp_path, target='2026-11-24')
    assert asyncio.run(job.run_local_scheduled(path,'us',now=start,one_shot_tag=TAG))['reason'] == 'SESSION_NOT_COMPLETED_OR_CLOSED'
    assert not list((tmp_path/'runs').rglob('intent.json'))


def test_new_run_consumed_once_preserves_no_send_retry_budget_and_exclusion_intent(tmp_path, monkeypatch):
    path, config = configured(tmp_path)
    code_pin(monkeypatch)
    start = config.one_shot.scheduled_at
    clock(monkeypatch, start)
    calls = []
    async def cycle(config, directory, session, **kwargs):
        calls.append((session, kwargs['one_shot_tag'], config.us_night_policy))
        return dict(status='SYNTHETIC_BOUNDARY_ONLY', normal_messages_sent=False)
    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    result = asyncio.run(job.run_local_scheduled(path,'us',now=start,one_shot_tag=TAG))
    assert result['status'] == 'SYNTHETIC_BOUNDARY_ONLY' and result['normal_messages_sent'] is False
    assert calls == [('2026-11-23', TAG, 'EXCLUDED_BEFORE_COLLECTION')]
    again = asyncio.run(job.run_local_scheduled(path,'us',now=start,one_shot_tag=TAG))
    assert again['reason'] == 'SESSION_ALREADY_CONSUMED' and len(calls) == 1
    root = tmp_path/'runs/one-shot/2026-11-24'/TAG
    intent = json.loads((root/'intent.json').read_bytes())
    assert (intent['max_http'],intent['max_models'],intent['source_seconds'],intent['model_per_call_seconds']) == (710,42,1800,600)
    assert intent['us_night_policy'] == config.us_night_policy
    assert intent['b2_retry_policy'] == job.B2_PER_TICKER_ONE_RETRY_V1
    assert intent['market_timeout_retry_cap'] == 0
