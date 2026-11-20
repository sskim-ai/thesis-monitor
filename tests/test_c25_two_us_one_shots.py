"""Finite 06:10/08:10 entry boundaries; synthetic cycles, no Source/model calls."""
import asyncio
from datetime import datetime as RealDateTime
import fcntl
import json

import pytest

from app.jobs import unified_market_snapshot as job
from tests.test_local_launchd_entry import configuration, code_pin

FIRST='us-20261121-0610a1b2'
SECOND='us-20261121-0810c3d4'


def clock(monkeypatch, value):
    stamp=RealDateTime.fromisoformat(value)
    class FixedDateTime(RealDateTime):
        @classmethod
        def now(cls, tz=None):
            return stamp.astimezone(tz) if tz else stamp.replace(tzinfo=None)
    monkeypatch.setattr(job,'datetime',FixedDateTime)
    return stamp


def test_only_two_exact_us_full_tags_and_completed_calendar(monkeypatch):
    assert set(job.US_FULL_20261121_SLOTS)=={FIRST,SECOND}
    for tag,hour in ((FIRST,6),(SECOND,8)):
        assert job.one_shot_scope('us',tag) is False
        now=clock(monkeypatch,f'2026-11-21T{hour:02d}:10:00+09:00')
        assert str(job.latest_one_shot_session('us',now,one_shot_tag=tag))=='2026-11-20'
        start,end=job._us_full_one_shot_window(tag)
        assert (end-start).total_seconds()==600 and start==now
    assert job.latest_one_shot_us_session(RealDateTime.fromisoformat('2026-11-21T05:59:00+09:00'),one_shot_tag=FIRST) is None
    for market,tag in (('kr',FIRST),('us','us-20261121-0610ffff'),('us','us2-20261121-0610a1b2'),
        ('us','us-20271121-0610a1b2')):
        with pytest.raises(ValueError,match='one_shot_tag_scope_invalid'):
            job.one_shot_scope(market,tag)


def test_previous_tags_and_routine_policy_are_unchanged():
    for market,tag,expected in (('us','us-20261120-12345678',False),
        ('us','us2-20261120-12345678',True),('us','us5-20261120-12345678',True),
        ('kr','kr-20261120-12345678',False)):
        assert job.one_shot_scope(market,tag) is expected
    now=RealDateTime.fromisoformat('2026-11-20T06:10:00+09:00')
    assert str(job.latest_one_shot_us_session(now))=='2026-11-19'
    assert job.latest_one_shot_us_session(RealDateTime.fromisoformat('2026-11-21T06:10:00+09:00')) is None
    from app.services.unified_market_run import target_session
    assert str(target_session('us',RealDateTime.fromisoformat('2026-11-21T06:10:00+09:00')))=='2026-11-20'
    assert sum(job.LOCAL_CAPS['us'].values())==710 and sum(job.LOCAL_CAPS['kr'].values())==332


def test_early_late_wrong_year_and_wrong_slot_never_start(tmp_path,monkeypatch):
    path,_=configuration(tmp_path)
    monkeypatch.setattr(job,'_local_registered_cycle',lambda *a,**kw:pytest.fail('must_not_start'))
    for tag,stamp in ((FIRST,'2026-11-21T06:09:59+09:00'),(FIRST,'2026-11-21T06:20:00+09:00'),
        (FIRST,'2026-11-21T08:10:00+09:00'),(SECOND,'2026-11-21T08:09:59+09:00'),
        (SECOND,'2026-11-21T08:20:00+09:00'),(SECOND,'2027-11-21T08:10:00+09:00')):
        now=clock(monkeypatch,stamp)
        result=asyncio.run(job.run_local_scheduled(path,'us',now=now,one_shot_tag=tag))
        assert result['status']=='NO_RUN' and not result['normal_messages_sent']
    assert not (tmp_path/'runs').exists()


def test_two_slots_have_distinct_intents_in_same_root_and_no_replay(tmp_path,monkeypatch):
    path,_=configuration(tmp_path);code_pin(monkeypatch);seen=[]
    async def cycle(config,directory,session,**kwargs):
        seen.append((directory,session,kwargs['one_shot_tag']))
        return dict(status='SYNTHETIC_NO_SEND',normal_messages_sent=False)
    monkeypatch.setattr(job,'_local_registered_cycle',cycle)
    for tag,hour in ((FIRST,6),(SECOND,8)):
        now=clock(monkeypatch,f'2026-11-21T{hour:02d}:10:00+09:00')
        assert asyncio.run(job.run_local_scheduled(path,'us',now=now,one_shot_tag=tag))['status']=='SYNTHETIC_NO_SEND'
        assert asyncio.run(job.run_local_scheduled(path,'us',now=now,one_shot_tag=tag))['reason']=='SESSION_ALREADY_CONSUMED'
        root=tmp_path/'runs/one-shot/2026-11-21'
        assert json.loads((root/(tag+'.intent.json')).read_text())['date']=='2026-11-21'
        intent=json.loads((root/tag/'intent.json').read_text())
        assert intent['one_shot_date']=='2026-11-21' and intent['session']=='2026-11-20'
        assert intent['max_http']==710 and intent['max_models']==42 and intent['source_seconds']==1800
        assert intent['b2_retry_policy']==job.B2_PER_TICKER_ONE_RETRY_V1 and not intent['normal_messages_sent']
    assert len(seen)==2 and seen[0][0]!=seen[1][0]
    assert not (tmp_path/'runs/one-shot/2026-11-21/intent.json').exists()


def test_second_slot_no_run_if_shared_lease_busy(tmp_path,monkeypatch):
    path,_=configuration(tmp_path);code_pin(monkeypatch)
    now=clock(monkeypatch,'2026-11-21T08:10:00+09:00')
    monkeypatch.setattr(job,'_local_registered_cycle',lambda *a,**kw:pytest.fail('busy_must_not_start'))
    with (tmp_path/'pair.lease').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=asyncio.run(job.run_local_scheduled(path,'us',now=now,one_shot_tag=SECOND))
    assert result==dict(status='NO_RUN',reason='NO_RUN_LOCK_BUSY',normal_messages_sent=False)
    assert not list((tmp_path/'runs').rglob('intent.json'))


def test_failure_consumed_and_per_slot_deadlines_remain_finite(tmp_path,monkeypatch):
    assert job._one_shot_deadline(FIRST).isoformat()=='2026-11-21T10:40:00+09:00'
    assert job._one_shot_deadline(SECOND).isoformat()=='2026-11-21T12:40:00+09:00'
    assert job._one_shot_deadline('us-20261120-12345678').isoformat()=='2026-11-21T00:00:00+09:00'
    path,_=configuration(tmp_path);code_pin(monkeypatch)
    now=clock(monkeypatch,'2026-11-21T06:10:00+09:00');calls=[]
    async def fail(*a,**kw):
        calls.append(True);raise RuntimeError('synthetic_value_must_not_be_logged')
    monkeypatch.setattr(job,'_local_registered_cycle',fail)
    with pytest.raises(RuntimeError):
        asyncio.run(job.run_local_scheduled(path,'us',now=now,one_shot_tag=FIRST))
    assert asyncio.run(job.run_local_scheduled(path,'us',now=now,one_shot_tag=FIRST))['reason']=='SESSION_ALREADY_CONSUMED'
    terminal=tmp_path/'runs/one-shot/2026-11-21'/FIRST/'terminal.json'
    assert len(calls)==1 and 'synthetic_value' not in terminal.read_text()
    assert json.loads(terminal.read_text())['status']=='STOPPED_NO_SEND'
