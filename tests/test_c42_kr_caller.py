"""Only the six newly changed KR caller boundaries; no live I/O."""
import asyncio
from datetime import datetime
import fcntl
from hashlib import sha256
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services.model_timeout_retry import B2_PER_TICKER_ONE_RETRY_V1
from tests.test_local_launchd_entry import configuration,code_pin


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*a,**kw):raise AssertionError('C42 test forbids DB, network or real worker')
    for owner,name in ((socket.socket,'connect'),(socket.socket,'connect_ex'),(sqlite3,'connect'),
                       (subprocess,'Popen'),(asyncio,'create_subprocess_exec')):
        monkeypatch.setattr(owner,name,denied)


def configured(folder):
    path,value=configuration(folder,market='kr')
    value['market_b2_timeout_retry']=True
    path.write_text(json.dumps(value))
    return path


def test_c42_exact_tag_completed_session_date_and_deadline():
    tag=job.KR_C42_20261123_TAG
    assert tag!=job.KR_RECOVERY_20261123_TAG and not job.one_shot_scope('kr',tag)
    assert str(job.latest_one_shot_session('kr',datetime.fromisoformat('2026-11-23T18:00:00+09:00'),one_shot_tag=tag))=='2026-11-23'
    for stamp in ('2026-11-23T15:20:00+09:00','2026-11-24T18:00:00+09:00','2027-11-23T18:00:00+09:00'):
        assert job.latest_one_shot_session('kr',datetime.fromisoformat(stamp),one_shot_tag=tag) is None
    assert job._one_shot_deadline(tag)==datetime.fromisoformat('2026-11-24T00:00:00+09:00')
    with pytest.raises(ValueError):job.one_shot_scope('us',tag)


def test_c42_intent27_same_policy_and_consumed_once(tmp_path,monkeypatch):
    code_pin(monkeypatch);path=configured(tmp_path);calls=[]
    async def cycle(config,directory,session,**kwargs):
        calls.append(directory);return dict(status='SYNTHETIC_NO_SEND',normal_messages_sent=False)
    monkeypatch.setattr(job,'_local_registered_cycle',cycle)
    now=datetime.fromisoformat('2026-11-23T18:00:00+09:00');tag=job.KR_C42_20261123_TAG
    value=asyncio.run(job.run_local_scheduled(path,'kr',now=now,one_shot_tag=tag))
    assert value['normal_messages_sent'] is False and len(calls)==1
    intent=json.loads((calls[0]/'intent.json').read_bytes())
    assert intent['max_models']==27 and intent['max_http']==334 and intent['market_timeout_retry_cap']==1
    assert intent['b2_retry_policy']==B2_PER_TICKER_ONE_RETRY_V1
    assert (calls[0].parent/(tag+'.intent.json')).is_file()
    assert asyncio.run(job.run_local_scheduled(path,'kr',now=now,one_shot_tag=tag))['reason']=='SESSION_ALREADY_CONSUMED'
    assert len(calls)==1


def test_original_cycle_records27_before_source_or_database(tmp_path,monkeypatch):
    from app.services.production_source_configuration import ProductionSourceConfiguration
    class BoundaryReached(Exception):pass
    runtime=tmp_path/'runtime';runtime.mkdir(mode=0o700)
    monkeypatch.setattr(job,'_local_model_runtime',lambda _:runtime)
    def stop(*a,**kw):raise BoundaryReached
    monkeypatch.setattr(ProductionSourceConfiguration,'model_validate_json',stop)
    config=SimpleNamespace(market='kr',market_b2_timeout_retry=True,kr_market_timeout_retry=False,
                           source_configuration=SimpleNamespace(read=lambda:b'{}'))
    with pytest.raises(BoundaryReached):
        asyncio.run(job._local_registered_cycle(config,tmp_path,'2026-11-23',one_shot_tag=job.KR_C42_20261123_TAG))
    row=json.loads((tmp_path/'model-runtime-preflight.json').read_bytes())
    assert row['max_models']==27 and row['market_timeout_retry_cap']==1 and row['b2_retry_policy']==B2_PER_TICKER_ONE_RETRY_V1
    assert row['before_registration_and_financial_HTTP'] is True


def test_late_start_or_next_year_refuses_full_campaign(tmp_path,monkeypatch):
    path=configured(tmp_path)
    for stamp,reason in (('2026-11-23T19:31:00+09:00','ONE_SHOT_FULL_CAMPAIGN_WINDOW_CLOSED'),
                          ('2026-11-24T18:00:00+09:00','ONE_SHOT_DATE_CLOSED'),
                          ('2027-11-23T18:00:00+09:00','ONE_SHOT_DATE_CLOSED')):
        row=asyncio.run(job.run_local_scheduled(path,'kr',now=datetime.fromisoformat(stamp),one_shot_tag=job.KR_C42_20261123_TAG))
        assert row['status']=='NO_RUN' and row['reason']==reason
    assert not (tmp_path/'runs').exists()


def test_busy_shared_lease_is_no_run_without_intent(tmp_path,monkeypatch):
    path=configured(tmp_path);code_pin(monkeypatch)
    with (tmp_path/'pair.lease').open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        row=asyncio.run(job.run_local_scheduled(path,'kr',now=datetime.fromisoformat('2026-11-23T18:00:00+09:00'),one_shot_tag=job.KR_C42_20261123_TAG))
    assert row['reason']=='NO_RUN_LOCK_BUSY'
    assert not list((tmp_path/'runs').glob('**/intent.json'))


def test_c38_and_existing_kr_pins_unchanged_no_send_default():
    baseline=Path('/Users/sskim/Documents/Codex/2026-07-04/the/maintenance/20261123-pr52-c42-kr-single-live/BEFORE.json')
    rows=json.loads(baseline.read_bytes())['protected']['protected']
    assert all(sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for r in rows.values())
    assert job.LocalScheduleConfiguration.model_fields['market_b2_timeout_retry'].default is False
    assert job.LocalScheduleConfiguration.model_fields['mode'].default=='LIVE_NO_SEND'
