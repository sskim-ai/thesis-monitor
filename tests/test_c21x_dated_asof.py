"""Only new as-of boundary checks; sealed C21W service bytes reused offline."""
import asyncio,json,os
from datetime import date,datetime,timezone
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.services import ohlcv_client as cli

NOW=datetime(2026,11,9,14,0,tzinfo=timezone.utc)


@pytest.mark.parametrize('trim,raw_end,expected',[(False,'2026-11-09','2026-11-06'),(True,'2026-11-06','2026-11-05')])
def test_actual_historical_asof_not_observation_or_price_owner(monkeypatch,tmp_path,trim,raw_end,expected):
    root=Path(os.environ['C21W_SEALED_EVIDENCE'])
    record=next(r for r in json.loads((root/'SERVICE_MOCK.json').read_text()) if r['symbol']=='CORZ')
    payload=json.loads(record['body'])
    if trim:payload['periods']['daily']=payload['periods']['daily'][:-1]
    body=json.dumps(payload).encode();hits=[]
    def handle(request):
        hits.append(1);return httpx.Response(200,content=body,headers=record['headers'])
    monkeypatch.setattr(cli,'get_settings',lambda:Settings(_env_file=None,
        ohlcv_base_url='https://native.invalid',monitor_retry_attempts=1))
    client=cli.OhlcvClient(transport=httpx.MockTransport(handle))
    context,receipt=asyncio.run(client.fetch_dated_daily_research(symbol='CORZ',market='us',
        history_through=date(2026,11,6),observed_at=NOW,output=tmp_path/'capture',run_id='C21X_OFFLINE'))
    preview=json.loads((tmp_path/'capture/NO_SEND.json').read_text())
    assert receipt['latest_raw_date']==raw_end and receipt['actual_historical_as_of']==expected
    assert receipt['effective_analysis_as_of']==expected and receipt['history_through']=='2026-11-06'
    assert receipt['observed_at']==NOW.isoformat() and receipt['latest_completed_session']=='2026-11-06'
    assert context.chart.structure['price_structure_v3']['as_of']==expected
    assert context.technical_context_payload()['native_view']['cutoff']==expected
    assert 'daily_history_as_of_mismatch' not in preview['SR']['denial_reasons']
    assert preview['SR']['numeric_bindings'] and context.decision.current_price is None
    assert context.decision.latest_completed_regular_session_date=='2026-11-06'
    assert context.chart.as_of_date==expected and hits==[1]
    assert client.completion_verifier is None
    assert all('bar_state' not in row for row in json.loads((tmp_path/'capture/valid-historical-bars.json').read_text()))
    out=Path(os.environ['C21X_EVIDENCE']);out.mkdir(exist_ok=True)
    (out/('TRIMMED.json' if trim else 'ORIGINAL.json')).write_text(json.dumps(preview,ensure_ascii=False,indent=2))
