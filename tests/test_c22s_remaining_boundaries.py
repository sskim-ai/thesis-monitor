import asyncio
from copy import deepcopy
from datetime import date,datetime,timezone
import hashlib,json
from pathlib import Path
import httpx
import pytest
from tests.test_c22s_source_only import capture,rows,CUTOFF,DATES,ROOT
from app.services.krx_source_only import issue_source_only_parent,collect_source_only


@pytest.mark.parametrize('variant', ['ok','http_failure','gap','order','no_pair','history_policy',
    'wrong_market','wrong_generation','wrong_product','wrong_url','tamper','attempted_tail','systemic_stop'])
def test_selected_night_probe_only_closes_verified_unopened_tail(tmp_path,monkeypatch,variant):
    from datetime import timedelta
    from types import SimpleNamespace
    from urllib.parse import urlsplit
    from pydantic import TypeAdapter
    from app.jobs.probe_krx_night_futures import fetch_live_probe,KRX_FUTURES_DAILY_URL
    from app.macro.providers.base import MacroProviderResult
    from app.macro.providers.krx import materialize_night_probe
    from app.services.production_source_seal import _verified_night_probe_tail

    cutoff = datetime.fromisoformat('2026-11-10T15:10:00+09:00')
    dates = [(cutoff.date()-timedelta(days=i)).isoformat() for i in range(7)]
    ids = ['night:KOSPI200:'+d for d in dates]
    generation = 'synthetic-terminal-tail'
    descriptors = [SimpleNamespace(logical_request_id=key,provider='krx_night_futures',subject='KOSPI200',
        market='kr',consumer_role=key,endpoint_operation='fut_bydd_trd',response_binding=None,
        raw_path=f'raw/{key}/source.body',request_json=json.dumps(dict(method='GET',
            url=KRX_FUTURES_DAILY_URL+'?basDd='+day.replace('-','')))) for key,day in zip(ids,dates)]
    plan = SimpleNamespace(frozen_at=cutoff,market='us',generation_id=generation,descriptors=descriptors)
    frozen = dict(scope='SELECTED_ORIGINAL_RESEARCH_V1',selected_market='us',generation_id=generation,
        frozen_at=cutoff.isoformat(),query_kst_date=dates[0],
        candidate=dict(night_query_dates=dates,consumer_policy=dict(us_night='ORIGINAL_CURRENT_PROBE_ONLY')))
    finals, receipts = {}, []

    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value))

    def send(request):
        day=request.url.params['basDd']
        index=len(receipts)
        key=ids[index]
        night=index==0 and variant!='no_pair'
        response=httpx.Response(200,json={'OutBlock_1':[rows(day,'야간' if night else '정규',
            '101.00' if night else '100.00')]})
        artifact=descriptors[index].raw_path
        path=tmp_path/'dispatch'/artifact
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(response.content)
        raw_hash=hashlib.sha256(response.content).hexdigest()
        stamp=(cutoff+timedelta(seconds=index+1)).isoformat()
        finals[key]=dict(status='PASS',raw_sha256=raw_hash,receipt_sha256=f'fixture-{index}',
            attempts=[dict(status=200,started_at=stamp,finished_at=stamp,raw_sha256=raw_hash)])
        receipts.append(dict(sealed_logical_id=key,sealed_final_receipt_sha256=f'fixture-{index}',
            artifact=artifact,artifact_sha256=raw_hash,requested_at=stamp,received_at=stamp,
            run_id=generation,provider='krx_night_futures',outcome='HTTP_RESPONSE',http_status=200,
            request=dict(method=request.method,route=str(request.url.copy_with(query=None)),params=dict(request.url.params))))
        return response

    probe=asyncio.run(fetch_live_probe(run_date=cutoff.date(),observation_time=cutoff,api_key='dummy',
        transport=httpx.MockTransport(send),max_lookback_days=2))
    probe.live_source=True
    value=TypeAdapter(MacroProviderResult).dump_python(materialize_night_probe(probe,history_directory=tmp_path/'history'),mode='json')
    phase=dict(status='CAPTURED_NOT_QUALIFIED',value=value)
    outcome=dict(logical_results=deepcopy(finals),phases=dict(night=phase),completed_at=(cutoff+timedelta(seconds=7)).isoformat())
    if variant=='http_failure':
        finals[ids[1]]['attempts'][0]['status']=503
        outcome['logical_results']=deepcopy(finals)
    elif variant=='gap':
        finals[ids[2]]=finals.pop(ids[1])
    elif variant=='order':
        receipts.reverse()
    elif variant=='history_policy':
        frozen['candidate']['consumer_policy']['us_night']='BACKFILL_REQUIRED'
    elif variant=='wrong_market':
        frozen['selected_market']='kr'
    elif variant=='wrong_generation':
        frozen['generation_id']='other'
    elif variant=='wrong_product':
        descriptors[1].subject='KOSDAQ150'
    elif variant=='wrong_url':
        descriptors[1].request_json=descriptors[1].request_json.replace(urlsplit(KRX_FUTURES_DAILY_URL).hostname,'other.invalid')
    elif variant=='tamper':
        (tmp_path/'dispatch'/descriptors[1].raw_path).write_bytes(b'{}')
    elif variant=='attempted_tail':
        write(tmp_path/'dispatch/receipts'/ids[2]/'attempt-1.start.json',{})
    elif variant=='systemic_stop':
        outcome['phases']['systemic_stop']={}
    for index,receipt in enumerate(receipts):
        write(tmp_path/f'night/probe/receipt-{index:03}.json',receipt)
    write(tmp_path/'night/query.json',{'observed_at':cutoff.isoformat()})
    write(tmp_path/'phase-night.json',phase)
    # The sealed receipt owner itself is unchanged and exercised by the real
    # retained corpus; only the synthetic dispatch envelope is stubbed here.
    monkeypatch.setattr('app.services.production_source_seal.consume_bound_result',lambda **_:None)
    result=_verified_night_probe_tail(tmp_path,frozen,outcome,plan,finals)
    assert set(result)==(set(ids[2:]) if variant=='ok' else set())


def test_first_required_raw_identity_failure_does_not_send_second(tmp_path):
    calls=[]
    def send(request):
        calls.append(request)
        return httpx.Response(200,json={'OutBlock_1':[dict(BAS_DD='20261109',PROD_NM='코스피200 선물',MKT_NM='정규')]})
    p=issue_source_only_parent(root=tmp_path/'wire',run_id='raw-identity',exact_dates=DATES,cutoff=CUTOFF)
    v=asyncio.run(collect_source_only(p,transport=httpx.MockTransport(send),api_key='dummy'))
    assert len(calls)==1 and v['status']=='SOURCE_ONLY_PARTIAL'
    assert v['error']=='CONFIGURED_RAW_IDENTITY_MISSING'


def test_default_lookback_wire_and_serialization_not_replaced():
    from app.jobs.probe_krx_night_futures import fetch_live_probe
    seen=[]
    def send(request):
        d=request.url.params['basDd'];seen.append(d)
        return httpx.Response(200,json={'OutBlock_1':[rows(d,'정규' if d=='20261109' else '야간','100.00' if d=='20261109' else '101.00')]})
    probe=asyncio.run(fetch_live_probe(run_date=date(2026,11,10),observation_time=CUTOFF,
        api_key='dummy',transport=httpx.MockTransport(send),max_lookback_days=2))
    assert seen==['20261110','20261109'] and probe.night_session_usable
    assert 'assessment_cutoff' not in probe.model_dump(mode='json')


@pytest.mark.parametrize('at,dates,pass_daily',[
    ('2026-11-10T05:59:00+09:00',DATES,False),
    ('2026-11-07T08:10:00+09:00',(date(2026,11,6),date(2026,11,7)),True),
])
def test_receipt_clock_controls_before06_and_saturday(tmp_path,monkeypatch,at,dates,pass_daily):
    import app.services.unified_source_observer as observer
    import app.services.unified_run_acquisition as acquisition
    fixed=datetime.fromisoformat(at)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return fixed.astimezone(tz or timezone.utc)
    monkeypatch.setattr(observer,'datetime',Clock)
    monkeypatch.setattr(acquisition,'datetime',Clock)
    calls=[]
    def send(request):
        d=request.url.params['basDd'];calls.append(d)
        return httpx.Response(200,json={'OutBlock_1':[rows(d,'정규' if d==dates[0].strftime('%Y%m%d') else '야간',
            '100.00' if d==dates[0].strftime('%Y%m%d') else '101.00')]})
    p=issue_source_only_parent(root=tmp_path/'wire',run_id='clock',exact_dates=dates,cutoff=fixed)
    v=asyncio.run(collect_source_only(p,transport=httpx.MockTransport(send),api_key='dummy'))
    assert (v['status']=='SOURCE_ONLY_DAILY_PASS') is pass_daily
    assert len(calls)==2 and v['available_at']==fixed.astimezone(timezone.utc).isoformat()


def test_actual_C5R_receipts_original_parser_provider_summary_no_current_upgrade(tmp_path):
    from app.jobs.probe_krx_night_futures import parse_krx_futures_payloads,_attach_fetch_telemetry
    from app.services.krx_night_history_service import persist_krx_response
    from app.macro.providers.krx import materialize_night_probe
    from app.services.night_futures import summarize_night_futures
    diag=json.loads((ROOT/'maintenance/20261110-c22q-v2/NIGHT_DIAGNOSTIC.json').read_bytes())
    cache=next(r for r in diag['roots'] if r.get('receipt_count')==3)
    payloads={};hashes={}
    for item in cache['raw_checks']:
        r=item['receipt'];raw=(Path(cache['path'])/r['raw_relative_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==r['raw_payload_sha256']
        d=date.fromisoformat(r['query_date']);payloads[d]=json.loads(raw);hashes[d]=r['raw_payload_sha256']
        persist_krx_response(root=tmp_path/'history',query_date=d,fetched_at=datetime.fromisoformat(r['fetched_at']),http_status=200,raw_body=raw)
    actual_received=datetime.fromisoformat(cache['raw_checks'][-1]['receipt']['fetched_at'])
    probe=parse_krx_futures_payloads(payloads,fetched_at=actual_received,payload_sha256_by_date=hashes)
    probe=_attach_fetch_telemetry(probe,payloads=payloads,expected_session=date(2026,11,5),observation_time=actual_received)
    # Current classification cannot be invented for the previous day's pair.
    probe.session_freshness='stale'
    original=materialize_night_probe(probe,history_directory=tmp_path/'history')
    assert original.observations and original.observations[0].raw_payload['night_trade_date']=='2026-11-04'
    flat=[{**o.__dict__,**o.raw_payload} for o in original.observations]
    assert not summarize_night_futures({'observations':flat}).items


def test_rehashed_wrong_aggregate_role_and_full_parent_remain_denied(tmp_path):
    from app.services.krx_source_only import replay_source_only
    from app.services.unified_snapshot_contract import digest
    p,v=capture(tmp_path);receipt=json.loads((p.root/'aggregate.json').read_bytes())
    receipt['market']='kr';receipt['aggregate_sha256']=digest({k:x for k,x in receipt.items() if k!='aggregate_sha256'})
    with pytest.raises(ValueError,match='aggregate_identity'):
        replay_source_only(root=p.root,receipt=receipt,plan_sha256=p.plan_sha256,cutoff=datetime.now(timezone.utc))
    assert not v['model_use'] and not v['full_market_parent'] and not v['default_enabled']
