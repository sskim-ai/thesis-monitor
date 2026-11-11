import asyncio
from datetime import date,datetime,timezone
import hashlib,json
from pathlib import Path
import httpx
import pytest
from tests.test_c22s_source_only import capture,rows,CUTOFF,DATES,ROOT
from app.services.krx_source_only import issue_source_only_parent,collect_source_only


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
