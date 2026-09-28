import asyncio
from copy import deepcopy

import httpx
import pytest

from app.services.native_completed_market import select_completed_daily_rows
from app.services.secret_safe_redirect import redirect_metadata
from app.services.sealed_fresh_dispatch import SealedDispatcher, wire_identity
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.unified_live_source_transport import SourceSafetyStop
from tests.test_r9_rev11_sealed_dispatch import CONFIG, OWNER, ROOT, descriptor, plan

SECRET = 'fixture_private_api_key_123'
DART = 'https://opendart.fss.or.kr/api/list.json'
PARAMS = dict(crtfc_key=SECRET, corp_code='00123456', bgn_de='20260101', end_de='20260928',
              page_no='1', page_count='100')


def dart_request(params=None):
    return httpx.Request('GET', DART, params=params or PARAMS)


def test_redirect_metadata_positive_is_not_follow_authority():
    req = dart_request()
    meta = redirect_metadata(req, httpx.Response(302, headers={'Location':str(req.url),
        'Content-Type':'application/json','Set-Cookie':SECRET}), (SECRET,))
    assert meta.route_class == 'EXACT_SAME_API_SEMANTICS'
    assert meta.same_origin and not meta.follow_authorized
    assert SECRET not in meta.model_dump_json()
    assert meta.query_keys == tuple(sorted(PARAMS))


@pytest.mark.parametrize('kind', ['cross_origin','downgrade','path','corp_code','bgn_de','end_de',
    'page_no','page_count','extra_query','missing','ambiguous','invalid','login','credential_path'])
def test_redirect_mutations_are_unresolved_and_secret_safe(kind):
    req = dart_request()
    target = str(req.url)
    headers = {}
    if kind in PARAMS:
        target = str(dart_request(PARAMS | {kind:'changed'}).url)
    elif kind == 'extra_query':
        target += '&extra='+SECRET
    elif kind == 'cross_origin':
        target = target.replace('opendart.fss.or.kr','evil.example')
    elif kind == 'downgrade':
        target = target.replace('https:','http:')
    elif kind == 'path':
        target = target.replace('list.json','fnlttSinglAcntAll.json')
    elif kind == 'login':
        target = 'https://opendart.fss.or.kr/login?token='+SECRET
    elif kind == 'credential_path':
        target = 'https://opendart.fss.or.kr/'+SECRET
    elif kind == 'invalid':
        target = 'https://[invalid'
    if kind == 'ambiguous':
        headers = [('location',target),('location',target)]
    elif kind != 'missing':
        headers = {'location':target}
    meta = redirect_metadata(req,httpx.Response(302,headers=headers),(SECRET,))
    assert meta.route_class == 'UNRESOLVED' and not meta.follow_authorized
    assert SECRET not in meta.model_dump_json()


def source_run(tmp_path, provider, req, **changes):
    d = descriptor(provider+':test',provider=provider,request_json=wire_identity(req,(SECRET,)),
                   transient_retry_max=0,**changes)
    p = plan(d)
    r = SealedDispatcher(plan=p,root=tmp_path/'run',rev10_receipt=ROOT,owners={'test-owner':OWNER},
        config_identities={provider:CONFIG},credential_presence={provider:True},secrets=(SECRET,))
    return r


@pytest.mark.parametrize('status',[200,301,302,307,308])
def test_dart_never_follows_or_retries_redirect(tmp_path,status):
    req = dart_request()
    run = source_run(tmp_path,'opendart',req)
    calls=[]
    def send(r):
        calls.append(r)
        return httpx.Response(status,json={'status':'000','list':[]},headers={'location':str(req.url)})
    transport=SealedSourceTransport(run,httpx.MockTransport(send),providers={'opendart'})
    response=asyncio.run(transport.handle_async_request(req))
    assert response.status_code==status and len(calls)==1
    final=run.results['opendart:test']
    assert final['status']==('PASS' if status==200 else 'FAILED')
    if status!=200:
        assert final['attempts'][0]['redirect_metadata']['follow_authorized'] is False
    assert all(SECRET.encode() not in p.read_bytes() for p in run.root.rglob('*') if p.is_file())


def ecos_request():
    return httpx.Request('GET',f'https://ecos.bok.or.kr/api/KeyStatisticList/{SECRET}/json/kr/1/100')


def test_ecos_public_preselection_keeps_exact_wire(tmp_path):
    req=ecos_request()
    run=source_run(tmp_path,'ecos',req)
    transport=SealedSourceTransport(run,httpx.MockTransport(lambda _:httpx.Response(200,json={'ok':True})),providers={'ecos'})
    assert asyncio.run(transport.handle_async_request(req)).status_code==200
    assert run.results['ecos:test']['status']=='PASS'
    assert all(SECRET.encode() not in p.read_bytes() for p in run.root.rglob('*') if p.is_file())


@pytest.mark.parametrize('change', ['host','operation','cycle','start','end','extra_query','credential','missing_credential',
    'extra_header','method'])
def test_ecos_wrong_wire_no_transport(tmp_path,change):
    req=ecos_request()
    run=source_run(tmp_path,'ecos',req)
    url=str(req.url)
    changes={'host':('ecos.bok.or.kr','evil.example'),'operation':('KeyStatisticList','StatisticSearch'),
        'cycle':('/kr/','/en/'),'start':('/1/100','/2/100'),'end':('/1/100','/1/99'),
        'credential':(SECRET,'wrong_private_key'),'missing_credential':(SECRET,'')}
    if change in changes:
        url=url.replace(*changes[change])
    if change=='extra_query':
        url+='?unexpected=1'
    bad=httpx.Request('POST' if change=='method' else 'GET',url,headers={'X-Extra':'1'} if change=='extra_header' else {})
    calls=[]
    transport=SealedSourceTransport(run,httpx.MockTransport(lambda r:calls.append(r)),providers={'ecos'})
    with pytest.raises(SourceSafetyStop):
        asyncio.run(transport.handle_async_request(bad))
    assert not calls


def test_ecos_wrong_config_and_generation_denied(tmp_path):
    req=ecos_request()
    d=descriptor('ecos:test',provider='ecos',request_json=wire_identity(req,(SECRET,)))
    with pytest.raises(ValueError):
        plan(d,generation_id='different')
    with pytest.raises(ValueError):
        SealedDispatcher(plan=plan(d),root=tmp_path/'wrong',rev10_receipt=ROOT,owners={'test-owner':OWNER},
            config_identities={'ecos':'c'*64},credential_presence={'ecos':True},secrets=(SECRET,))


@pytest.mark.parametrize('field',['corp_code','bgn_de','end_de','page_no','page_count','host','extra'])
def test_dart_mutated_request_not_dispatched(tmp_path,field):
    req=dart_request()
    run=source_run(tmp_path,'opendart',req)
    params=PARAMS | ({field:'wrong'} if field!='host' else {})
    bad=dart_request(params)
    if field=='host':
        bad=httpx.Request('GET',str(bad.url).replace('opendart.fss.or.kr','evil.example'))
    calls=[]
    transport=SealedSourceTransport(run,httpx.MockTransport(lambda r:calls.append(r)),providers={'opendart'})
    with pytest.raises(SourceSafetyStop):
        asyncio.run(transport.handle_async_request(bad))
    assert calls==[]


def test_diagnostic_requires_official_json_not_html(tmp_path):
    from scripts.r9_rev12_dart_diagnostic import classify
    body=tmp_path/'response.body'
    body.write_bytes(b'<html>login</html>')
    final={'attempts':[{'status':200,'artifact':body.name}]}
    assert classify(final,tmp_path).endswith('UNRESOLVED')
    body.write_bytes(b'{"status":"000","list":[]}')
    assert classify(final,tmp_path)=='DIRECT_OFFICIAL_API_200'
    final['attempts'].append(final['attempts'][0])
    with pytest.raises(ValueError,match='exact_one_attempt'):
        classify(final,tmp_path)


@pytest.mark.parametrize('symbol',['SPY','QQQ','IWM','XLB','GENERIC'])
def test_completed_selector_excludes_later_without_mutation(symbol):
    rows=[dict(date=d,close=i+1,symbol=symbol) for i,d in enumerate(('2026-09-24','2026-09-25','2026-09-28'))]
    before=deepcopy(rows)
    assert [r['date'] for r in select_completed_daily_rows(rows,target_session='2026-09-25',count=2)]==[
        '2026-09-24','2026-09-25']
    assert rows==before


@pytest.mark.parametrize('dates,code', [(['2026-09-24','2026-09-28'],'target_completed_session_missing'),
    (['2026-09-23','2026-09-25'],'adjacent_completed_baseline_missing'),
    (['2026-09-24','2026-09-25','2026-09-25'],'duplicate_session')])
def test_completed_selector_no_stale_or_duplicate_fallback(dates,code):
    with pytest.raises(ValueError,match=code):
        select_completed_daily_rows([dict(date=d,close=1) for d in dates],target_session='2026-09-25',count=2)


def test_disk_guard_is_not_lowered(monkeypatch,tmp_path):
    from types import SimpleNamespace
    from scripts import r9_rev11_live as live
    monkeypatch.setattr(live.shutil,'disk_usage',lambda _:SimpleNamespace(total=30*1024**3,used=21*1024**3,free=9*1024**3))
    with pytest.raises(SourceSafetyStop,match='DISK_GUARD'):
        live.require_disk_capacity(tmp_path)
    monkeypatch.setattr(live.shutil,'disk_usage',lambda _:SimpleNamespace(total=30*1024**3,used=20*1024**3,free=10*1024**3))
    assert live.require_disk_capacity(tmp_path)['free']==10*1024**3
