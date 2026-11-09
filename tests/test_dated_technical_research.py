import asyncio,hashlib,json,os,subprocess,sys
from datetime import date,datetime,timezone
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.services import ohlcv_client as cli
from app.services.provider_native_technical import MAX_COUNTS
from app.services.ohlcv_structure_service import LOCAL_PIVOT_LOOKBACKS

NOW=datetime(2026,11,9,14,0,tzinfo=timezone.utc)


def client(monkeypatch,market,fault=None):
    symbol='047810' if market=='kr' else 'CORZ'
    wire=next(r for r in json.loads((Path(os.environ['C21W_EVIDENCE'])/'SERVICE_MOCK.json').read_text()) if r['symbol']==symbol)
    payload=json.loads(wire['body']);hits=[]
    if fault=='bad_ohlc':payload['periods']['daily'][-2]['low']=99999
    if fault=='latest_only':payload['periods']['daily']=payload['periods']['daily'][-1:]
    body=json.dumps(payload).encode()
    def send(request):
        hits.append(dict(request.url.params))
        assert not any(k.lower().startswith('x-native') for k in request.headers)
        assert request.url.params['market']==market.upper()
        return httpx.Response(200,content=body,headers=wire['headers'])
    monkeypatch.setattr(cli,'get_settings',lambda:Settings(_env_file=None,
        ohlcv_base_url='https://native.invalid',monitor_retry_attempts=1))
    return cli.OhlcvClient(transport=httpx.MockTransport(send)),symbol,hits,body


def fetch(c,symbol,market,out):
    return asyncio.run(c.fetch_dated_daily_research(symbol=symbol,market=market,
        history_through=date(2026,11,6),observed_at=NOW,output=out,run_id='C21W_OFFLINE'))


def test_two_markets_history_native38_pivot_sr_no_send(monkeypatch,tmp_path):
    from app.services import packet_owned_technical_context_service as packet
    from app.services import price_structure_wave_fibonacci_v3_service as structure
    def forbidden(*a,**k):raise AssertionError('NATIVE_INDICATOR_RECALCULATED')
    monkeypatch.setattr(packet,'build_multi_timeframe_feature_packet',forbidden)
    monkeypatch.setattr(structure,'_bollinger_sources',forbidden)
    monkeypatch.setattr(structure,'_provisional_bollinger_sources',forbidden)
    assert MAX_COUNTS=={'daily':1000,'weekly':700,'monthly':300}
    assert LOCAL_PIVOT_LOOKBACKS=={'daily':300,'weekly':120,'monthly':60}
    outputs=[]
    for market in ('kr','us'):
        c,symbol,hits,body=client(monkeypatch,market);out=tmp_path/market
        context,receipt=fetch(c,symbol,market,out)
        assert len(hits)==1 and hits[0]['indicator_limit']=='5'
        assert receipt['returned_count']==86 and receipt['usable_count']==85
        assert receipt['last_historical_session']=='2026-11-06' and receipt['body_sha256']==hashlib.sha256(body).hexdigest()
        raw=json.loads(body)['periods']['daily'][-2]['indicators']
        native=context.technical_context_payload()['native_view']['periods']['daily']
        assert native['indicators']==raw and len(raw)==38 and raw['MA288'] is None
        assert context.decision.current_price is None and c.completion_verifier is None
        preview=json.loads((out/'NO_SEND.json').read_text())
        assert preview['SR']['numeric_bindings'] and preview['NO_SEND']
        assert (out/'response.body').read_bytes()==body
        assert not context.supply.available if market=='us' else context.supply.available
        outputs.append(preview)
    (Path(os.environ['C21W_EVIDENCE'])/'TWO_MARKET_NO_SEND.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2))


@pytest.mark.parametrize('fault',['bad_ohlc','latest_only'])
def test_incomplete_and_invalid_never_generate_levels(monkeypatch,tmp_path,fault):
    c,symbol,hits,body=client(monkeypatch,'kr',fault)
    with pytest.raises(ValueError):fetch(c,symbol,'kr',tmp_path/fault)
    assert len(hits)==1 and not (tmp_path/fault/'NO_SEND.json').exists()
    assert (tmp_path/fault/'response.body').read_bytes()==body


def test_command_without_live_is_plan_only():
    script=Path(__file__).resolve().parents[1]/'scripts/dated_ohlcv_canary.py'
    result=subprocess.check_output([sys.executable,'-B',str(script),'--history-through','2026-11-06','--output','/private/tmp/C21W_NOT_CREATED'],text=True)
    assert json.loads(result)['mode']=='PLAN_ONLY_NO_HTTP'
