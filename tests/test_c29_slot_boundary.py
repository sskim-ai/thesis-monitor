"""Only the new C29 finite slot and unobservable-quota entry boundary."""
import asyncio
from datetime import datetime as DateTime,timedelta
import fcntl
import inspect
import json
import socket

import pytest

from app.jobs import unified_market_snapshot as job
from tests.test_local_launchd_entry import configuration,code_pin

TAG='us-20261121-c29a6b3d'
START=DateTime.fromisoformat('2026-11-21T11:40:00+09:00')


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args,**kwargs):raise AssertionError('C29_TEST_EXTERNAL_IO_DENIED')
    monkeypatch.setattr(socket.socket,'connect',denied)
    monkeypatch.setattr(socket,'getaddrinfo',denied)
    class Clock(DateTime):
        @classmethod
        def now(cls,tz=None):return START.astimezone(tz) if tz else START.replace(tzinfo=None)
    monkeypatch.setattr(job,'datetime',Clock)


def test_new_exact_slot_market_year_session_and_ten_minute_window(tmp_path,monkeypatch):
    assert job._us_full_one_shot_window(TAG)==(START,START+timedelta(minutes=10))
    assert job._one_shot_deadline(TAG)==START+timedelta(hours=4,minutes=30)
    assert str(job.latest_one_shot_us_session(START,one_shot_tag=TAG))=='2026-11-20'
    assert job.one_shot_scope('us',TAG) is False
    for market,tag in (('kr',TAG),('us',TAG+'f'),('us','us-20271121-c29a6b3d')):
        with pytest.raises(ValueError,match='tag_scope_invalid'):job.one_shot_scope(market,tag)
    path,_=configuration(tmp_path)
    monkeypatch.setattr(job,'_local_registered_cycle',lambda *a,**kw:pytest.fail('window_closed'))
    for at in (START-timedelta(seconds=1),START+timedelta(minutes=10),START.replace(year=2027)):
        assert asyncio.run(job.run_local_scheduled(path,'us',now=at,one_shot_tag=TAG))['status']=='NO_RUN'
    assert not (tmp_path/'runs').exists()


def test_unobservable_quota_does_not_add_gate_or_change_original_physical_caps(tmp_path,monkeypatch):
    path,_=configuration(tmp_path);code_pin(monkeypatch);seen=[]
    async def cycle(config,directory,session,**kwargs):
        seen.append(session)
        return dict(status='SYNTHETIC_NO_SEND',normal_messages_sent=False)
    original=inspect.getsource(job._local_registered_cycle)
    assert 'local_schedule_frozen_plan_exceeds_original_caps' in original
    assert "stop_on_first_external_failure=True" in original
    assert "optional_news_429='SELECTED_US_OPTIONAL_NEWS_429_V1'" in original
    assert 'PROVIDER_QUOTA_ADMISSION' not in original and 'quota_remaining' not in original
    monkeypatch.setattr(job,'_local_registered_cycle',cycle)
    result=asyncio.run(job.run_local_scheduled(path,'us',now=START,one_shot_tag=TAG))
    assert result['status']=='SYNTHETIC_NO_SEND' and seen==['2026-11-20']
    intent=json.loads((tmp_path/'runs/one-shot/2026-11-21'/TAG/'intent.json').read_bytes())
    assert (intent['max_http'],intent['max_models'],intent['source_seconds'])==(710,42,1800)
    assert intent['b2_retry_policy']==job.B2_PER_TICKER_ONE_RETRY_V1


def test_shared_lease_and_failed_consumption_still_prevent_campaign_retry(tmp_path,monkeypatch):
    path,_=configuration(tmp_path);code_pin(monkeypatch);seen=[]
    async def cycle(*args,**kwargs):
        seen.append(True)
        raise RuntimeError('fixture_only_no_provider_error')
    monkeypatch.setattr(job,'_local_registered_cycle',cycle)
    with (tmp_path/'pair.lease').open('rb') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert asyncio.run(job.run_local_scheduled(path,'us',now=START,one_shot_tag=TAG))['reason']=='NO_RUN_LOCK_BUSY'
    with pytest.raises(RuntimeError):asyncio.run(job.run_local_scheduled(path,'us',now=START,one_shot_tag=TAG))
    assert asyncio.run(job.run_local_scheduled(path,'us',now=START,one_shot_tag=TAG))['reason']=='SESSION_ALREADY_CONSUMED'
    assert len(seen)==1
