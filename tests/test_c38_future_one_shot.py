from datetime import datetime, timedelta
from types import SimpleNamespace

from app.jobs import unified_market_snapshot as job


TAG = 'us-20261124-c38f2a6d'


def test_frozen_future_window_requires_original_completed_session(monkeypatch):
    start, end = job._us_full_one_shot_window(TAG)
    assert start == datetime.fromisoformat('2026-11-24T08:10:00+09:00')
    assert end - start == timedelta(minutes=10)
    assert str(job.latest_one_shot_us_session(start, one_shot_tag=TAG)) == '2026-11-23'
    assert job.latest_one_shot_us_session(start - timedelta(days=1), one_shot_tag=TAG) is None
    assert job.latest_one_shot_us_session(start + timedelta(days=1), one_shot_tag=TAG) is None
    assert job._one_shot_deadline(TAG) == start + timedelta(hours=4, minutes=30)
    assert not job.one_shot_scope('us', TAG)
    old = 'us-20261121-c36e7a4b'
    old_start, _ = job._us_full_one_shot_window(old)
    assert str(job.latest_one_shot_us_session(old_start, one_shot_tag=old)) == '2026-11-20'
    from app.services import market_session, unified_market_run
    monkeypatch.setattr(unified_market_run, 'target_session', lambda *a: None)
    assert job.latest_one_shot_us_session(start, one_shot_tag=TAG) is None
    monkeypatch.undo()
    monkeypatch.setattr(market_session, 'us_market_session', lambda *a: SimpleNamespace(
        latest_completed_regular_session_date=datetime.fromisoformat('2026-11-20').date()))
    assert job.latest_one_shot_us_session(start, one_shot_tag=TAG) is None


def test_future_job_reaches_existing_cycle_only_inside_frozen_window(tmp_path, monkeypatch):
    import asyncio
    from app.services.unified_run_artifacts import load_json

    start, end = job._us_full_one_shot_window(TAG)
    config = SimpleNamespace(enabled=True, code_commit='a' * 40, run_root=str(tmp_path / 'runs'),
        shared_lease_path=str(tmp_path / 'lease'), model_dump=lambda **k: {'test': 'no-live'})
    (tmp_path / 'lease').touch()
    monkeypatch.setattr(job, 'read_local_configuration', lambda *a: config)
    monkeypatch.setattr(job.subprocess, 'check_output', lambda args, **k:
        config.code_commit + '\n' if 'rev-parse' in args else '')
    monkeypatch.setattr(job, '_one_shot_deadline', lambda *a: datetime.now(job.KST) + timedelta(seconds=30))
    calls = []

    async def cycle(config, directory, session, **kwargs):
        calls.append((session, kwargs['one_shot_tag']))
        return {'status': 'SYNTHETIC_BOUNDARY_ONLY', 'normal_messages_sent': False}

    monkeypatch.setattr(job, '_local_registered_cycle', cycle)
    for at, reason in ((start - timedelta(seconds=1), 'ONE_SHOT_SLOT_CLOSED'),
                       (end, 'ONE_SHOT_SLOT_CLOSED'),
                       (start + timedelta(days=1), 'ONE_SHOT_DATE_CLOSED')):
        result = asyncio.run(job.run_local_scheduled('unused', 'us', now=at, one_shot_tag=TAG))
        assert result['reason'] == reason
    assert not calls and not (tmp_path / 'runs').exists()
    result = asyncio.run(job.run_local_scheduled('unused', 'us', now=start, one_shot_tag=TAG))
    assert result['status'] == 'SYNTHETIC_BOUNDARY_ONLY'
    assert calls == [('2026-11-23', TAG)]
    root = tmp_path / 'runs' / 'one-shot' / '2026-11-24' / TAG
    intent = load_json(root / 'intent.json')
    assert intent['max_http'] == 710 and intent['max_models'] == 42
    assert intent['source_seconds'] == 1800 and intent['model_per_call_seconds'] == 600
    assert intent['normal_messages_sent'] is False
    again = asyncio.run(job.run_local_scheduled('unused', 'us', now=start, one_shot_tag=TAG))
    assert again['reason'] == 'SESSION_ALREADY_CONSUMED' and len(calls) == 1
