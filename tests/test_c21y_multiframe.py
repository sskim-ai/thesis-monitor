import asyncio,hashlib,json
from datetime import date,datetime,timezone
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.services import ohlcv_client as cli
from app.services.dated_multiframe_research import period_end,select_historical,fetch_wm,assemble

DAILY=Path('/private/tmp/c21x-daily-canary-20261109/us-CORZ')
NOW=datetime(2026,11,9,tzinfo=timezone.utc)


def rows(labels):
    return [dict(date=d,open=10.,high=12.,low=9.,close=11.,volume=100.) for d in labels]


def test_calendar_labels_unchanged_short_weekly_and_future_excluded():
    bars=rows(['2026-10-19','2026-10-26','2026-11-02','2026-11-09'])
    used,excluded,ends=select_historical(bars,timeframe='weekly',market='us',cutoff=date(2026,11,5))
    assert len(used)==2 and used[-1]['date']=='2026-10-26'
    assert ends['2026-10-26']=='2026-10-30'
    assert [r['date'] for r in bars]==['2026-10-19','2026-10-26','2026-11-02','2026-11-09']
    assert {e['reason'] for e in excluded}=={'latest_ambiguous_period_excluded','period_ends_after_analysis_cutoff'}
    assert period_end(date(2026,10,1),'monthly','us')==date(2026,10,30)


def test_monthly_short_history_and_invalid_bar():
    bars=rows(['2026-08-03','2026-09-01','2026-10-01','2026-11-02'])
    bars[1]['completion_state']='PROVISIONAL'
    used,excluded,ends=select_historical(bars,timeframe='monthly',market='kr',cutoff=date(2026,11,6))
    assert len(used)==2 and ends['2026-10-01']=='2026-10-30'
    bars[0]['high']=1
    with pytest.raises(ValueError,match='invalid_historical'):select_historical(bars,timeframe='monthly',market='kr',cutoff=date(2026,11,6))


def client(monkeypatch,transport=None):
    monkeypatch.setattr(cli,'get_settings',lambda:Settings(_env_file=None,ohlcv_base_url='https://native.invalid'))
    return cli.OhlcvClient(transport=transport)


def test_http_parameters_raw_hash_short_count_and_native_null_preserved(monkeypatch,tmp_path):
    payload=json.loads((DAILY/'response.body').read_text())
    bars=rows(['2026-08-03','2026-09-01','2026-10-01','2026-11-02'])
    native=dict(payload['periods']['daily'][-1]['indicators']);native['RSI14']=None
    for b in bars:b['indicators']=native.copy()
    payload['periods']={'monthly':bars};body=json.dumps(payload).encode();hits=[]
    def handle(r):
        hits.append(r)
        assert dict(r.url.params)==dict(symbol='CORZ',market='US',periods='monthly',count='300',include_indicators='true',indicator_limit='5',adjusted='true',include_investor_flows='false')
        return httpx.Response(200,content=body,headers={'X-Research-Physical-Count':'2','X-Research-Budget-Instance':'test','X-Research-Budget-Protocol':'simple-research-budget-v1'})
    decoded,receipt=asyncio.run(fetch_wm(client(monkeypatch,httpx.MockTransport(handle)),symbol='CORZ',market='us',timeframe='monthly',observed_at=NOW,analysis_cutoff=date(2026,11,5),output=tmp_path/'wm',run_id='C21Y_TEST',remaining=44))
    assert len(hits)==1 and receipt['returned']==4 and receipt['used']==3
    assert receipt['body_sha256']==hashlib.sha256(body).hexdigest()
    assert (tmp_path/'wm/response.body').read_bytes()==body
    assert decoded[-2]['indicators']['RSI14'] is None


def test_real_daily_reuse_original_packet_native_values_and_SR(monkeypatch,tmp_path):
    c=client(monkeypatch)
    p=json.loads((DAILY/'response.body').read_text())
    sources={}
    for tf,labels in [('weekly',['2026-10-05','2026-10-12','2026-10-19','2026-10-26','2026-11-02']),('monthly',['2026-06-01','2026-07-01','2026-08-03','2026-09-01','2026-10-01'])]:
        p['periods']={tf:rows(labels)}
        for b in p['periods'][tf]:b['indicators']=json.loads((DAILY/'response.body').read_text())['periods']['daily'][-1]['indicators']
        decoded,_,_=c._decode_period_payload(p,ticker='CORZ',period=tf,adjusted=True,response_body_sha256=hashlib.sha256(json.dumps(p).encode()).hexdigest())
        sources[tf]=(decoded,{})
    result=assemble(c,daily_root=DAILY,wm_sources=sources,symbol='CORZ',market='us',observed_at=NOW,output=tmp_path/'combined')
    assert result['models_called']==0 and not result['current_price_qualified']
    assert result['SR']['numeric_bindings']
    prompt=result['model_input_preview']
    assert 'provider_native' in prompt['technical_context_quality']
    assert '41.07789855072463' in json.dumps(prompt)
    assert c.completion_verifier is None
