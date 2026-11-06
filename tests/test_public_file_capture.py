"""Synthetic storage/transport equivalence; no live qualification claims."""
import json
import asyncio
import sqlite3
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import httpx
import pytest
from app.services.public_capture_storage import FileCaptureArchive,find_capture,list_captures,run_started_at
from app.services.vnext_public_capture import PublicTransport,public_descriptor
from app.services.vnext_legacy_reuse import native_valuation_inputs
from app.services.vnext_research_store import digest,encoded
from app.services.provider_native_valuation_snapshot import derive_provider_snapshots,derive_forward_snapshot

SECURITY=dict(ticker='SYNTH',canonical_security_id='US:SYNTH',country='US',exchange='NASDAQ',
    currency='USD',security_type='common_stock',issuer_type='domestic',share_class='common')


@pytest.fixture
def archive(tmp_path):
    at=datetime.now(timezone.utc).isoformat()
    return FileCaptureArchive(tmp_path/'capture',run_id='SYNTHETIC',started_at=at,
        securities=[SECURITY],code_pins={},enabled=True)


def pair(archive):
    for endpoint,payload in [('profile2',dict(ticker='SYNTH',exchange='NASDAQ',currency='USD')),
        ('metric',dict(symbol='SYNTH',metric=dict(peTTM=12,pbQuarterly=2,forwardPE=10)))]:
        req=httpx.Request('GET','https://finnhub.io/api/v1/stock/'+endpoint,
            params=dict(symbol='SYNTH',**({'metric':'all'} if endpoint=='metric' else {}),token='TEST_KEY'))
        desc=public_descriptor(req);raw=encoded(payload);at=datetime.now(timezone.utc).isoformat()
        receipt=dict(run_id='SYNTHETIC',provider='Finnhub',raw_birth='CURRENT_HTTP',status=200,
            started_at=at,captured_at=at,raw_sha256=digest(raw),response_headers={},request=desc)
        archive.capture('SYNTHETIC','Finnhub',digest(desc),raw,receipt)


def test_default_off(tmp_path):
    with pytest.raises(ValueError,match='enable'):
        FileCaptureArchive(tmp_path/'none',run_id='X',started_at='bad',securities=[],code_pins={})
    assert not (tmp_path/'none').exists()


def test_original_snapshot_replay_and_readonly_restart(archive):
    pair(archive)
    new=FileCaptureArchive.open_read_only(archive.path.parent,expected_manifest_sha256=archive.manifest_sha256)
    a=native_valuation_inputs(new,'SYNTHETIC',SECURITY,'finnhub')
    per,pbr=derive_provider_snapshots(a,security=SECURITY,run_id='SYNTHETIC')
    assert per.display_eligible and pbr.display_eligible
    assert derive_forward_snapshot(a,security=SECURITY,run_id='SYNTHETIC').display_eligible
    assert not list(archive.path.parent.glob('*.sqlite*'))


def test_sql_and_file_native_inputs_equal(archive):
    pair(archive)
    class SQL:
        def __init__(self):
            self.db=sqlite3.connect(':memory:')
            self.db.executescript('CREATE TABLE research_run(run_id TEXT,started_at TEXT); CREATE TABLE source_capture(run_id TEXT,provider TEXT,request_key TEXT,raw_path TEXT,receipt_json TEXT);')
            self.db.execute('INSERT INTO research_run VALUES (?,?)',('SYNTHETIC',archive.run_started_at('SYNTHETIC')))
            for path,text in archive.list_captures('SYNTHETIC','Finnhub'):
                r=json.loads(text);self.db.execute('INSERT INTO source_capture VALUES (?,?,?,?,?)',
                    ('SYNTHETIC','Finnhub',digest(r['request']),path,text))
        @contextmanager
        def connect(self):yield self.db
    sql=SQL();cutoff=datetime.now(timezone.utc)
    try:
        a=native_valuation_inputs(archive,'SYNTHETIC',SECURITY,'finnhub',cutoff=cutoff)
        b=native_valuation_inputs(sql,'SYNTHETIC',SECURITY,'finnhub',cutoff=cutoff)
        assert a==b
    finally:sql.db.close()


def test_cross_run_denied(archive):
    with pytest.raises(ValueError,match='run_or_manifest'):
        archive.run_started_at('OTHER')


def test_raw_change_denied(archive):
    pair(archive);path,_=archive.list_captures('SYNTHETIC','Finnhub')[0]
    Path(path).write_bytes(b'{}')
    with pytest.raises(ValueError,match='raw_changed'):
        archive.list_captures('SYNTHETIC','Finnhub')


def test_manifest_change_denied(archive):
    archive.path.write_bytes(b'{}')
    with pytest.raises(ValueError,match='manifest'):
        archive.identities()


def test_symlink_rejected(archive,tmp_path):
    pair(archive);path,_=archive.list_captures('SYNTHETIC','Finnhub')[0]
    target=tmp_path/'substitute';target.write_bytes(Path(path).read_bytes())
    Path(path).unlink();Path(path).symlink_to(target)
    with pytest.raises(ValueError,match='symlink'):
        archive.list_captures('SYNTHETIC','Finnhub')


@pytest.mark.parametrize('status',[401,403,429])
def test_provider_hard_stop_no_second_physical_attempt(archive,status):
    asyncio.run(_hard_stop(archive,status))


async def _hard_stop(archive,status):
    from app.services.bounded_financial_acquisition import SystemicStop
    request=httpx.Request('GET','https://finnhub.io/api/v1/stock/profile2',params={'symbol':'SYNTH','token':'TEST_KEY'})
    scope=dict(limits={'Finnhub':2},requests=[{k:v for k,v in public_descriptor(request).items() if k!='page'}],allow_pagination=False)
    attempts=[]
    async def reply(r):attempts.append(1);return httpx.Response(status,content=b'{}')
    transport=PublicTransport(archive,'SYNTHETIC',scope_plan=scope,interval=0,inner=httpx.MockTransport(reply))
    try:
        await transport.handle_async_request(request)
        with pytest.raises(SystemicStop):await transport.handle_async_request(request)
        assert len(attempts)==1 and len(transport.events)==1
    finally:transport.finish()


def test_cache_does_not_rebirth_or_charge_http(archive):
    asyncio.run(_cache(archive))


async def _cache(archive):
    request=httpx.Request('GET','https://finnhub.io/api/v1/stock/profile2',params={'symbol':'SYNTH','token':'TEST_KEY'})
    scope=dict(limits={'Finnhub':1},requests=[{k:v for k,v in public_descriptor(request).items() if k!='page'}])
    transport=PublicTransport(archive,'SYNTHETIC',scope_plan=scope,interval=0,
        inner=httpx.MockTransport(lambda r:httpx.Response(200,json={'ticker':'SYNTH'})))
    try:
        await transport.handle_async_request(request)
        first=archive.list_captures('SYNTHETIC','Finnhub')
        await transport.handle_async_request(request)
        assert archive.list_captures('SYNTHETIC','Finnhub')==first
        assert len(transport.events)==1 and 'TEST_KEY' not in encoded(first).decode()
    finally:transport.finish()
