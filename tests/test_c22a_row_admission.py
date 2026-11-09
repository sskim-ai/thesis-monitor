import hashlib,json
from copy import deepcopy
from datetime import date,datetime
from pathlib import Path
import pytest
from app.services.dated_bar_admission import admit_rows
from app.services.ohlcv_client import OhlcvClient
from app.services.dated_multiframe_research import assemble
from app.config import Settings
R=Path('/Users/sskim/Documents/Codex/2026-07-04/the');H=R/'maintenance/20261109-c22a'


def decode(ticker,tf,path):
    raw=Path(path).read_bytes();bars,_,_=OhlcvClient._decode_period_payload(json.loads(raw),ticker=ticker,period=tf,adjusted=True,response_body_sha256=hashlib.sha256(raw).hexdigest())
    return raw,bars


def check_old(tf,path):
    raw,bars=decode('CPNG',tf,path);clean,qa=admit_rows(bars,ticker='CPNG',market='us',timeframe=tf,cutoff=date(2026,11,6))
    assert len(clean)==len(bars)-1 and qa['bad_date']=='2023-06-05' and qa['kind']=='OLD_ISOLATED_PRICE_ROW'
    assert clean[-1]['indicators']==bars[-1]['indicators'] and all(b['date']!='2023-06-05' for b in clean)
    assert Path(path).read_bytes()==raw


def test_CPNG_daily_old_isolated_row_accepted_no_model_warning():
    check_old('daily','/private/tmp/c21z-native22-continuation-20261109/us-CPNG/daily/response.body')
    result=json.loads((H/'derived/CPNG/combined/NO_SEND.json').read_text())
    text=json.dumps(result).lower()
    assert all(s not in text for s in ['degraded_single_bad_bar','historical_bad_bar','quality_warning','old_isolated_price_row'])
    assert result['SR']['numeric_bindings'] and not result['current_price_qualified']


def test_CPNG_weekly_old_isolated_native_null_preserved():
    check_old('weekly','/private/tmp/c21z-native22-role-continuation-20261109/us-CPNG/weekly/response.body')
    result=json.loads((H/'derived/CPNG/combined/NO_SEND.json').read_text());p=result['technical_input']['native_view']['periods']['weekly']
    raw=json.loads(Path('/private/tmp/c21z-native22-role-continuation-20261109/us-CPNG/weekly/response.body').read_text())
    row=next(r for r in raw['periods']['weekly'] if r['date']==p['completed_as_of'])
    assert p['indicators']==row['indicators'] and any(v is None for v in p['indicators'].values())


def test_recent_latest_is_dated_history_not_old_policy():
    raw,bars=decode('TSM','daily','/private/tmp/c21z-native22-20261109/us-TSM/daily/response.body')
    clean,qa=admit_rows(bars,ticker='TSM',market='us',timeframe='daily',cutoff=date(2026,11,6))
    assert qa['kind']=='RECENT_LATEST_PRICE_ROW_DATED_HISTORY_ONLY' and clean[-1]['date']=='2026-11-05'
    result=json.loads((H/'derived/TSM/combined/NO_SEND.json').read_text())
    assert result['daily_as_of']=='2026-11-05' and not result['current_price_qualified']


def test_multiple_errors_and_source_mutation_remain_blocked():
    from app.services.unified_snapshot_contract import digest
    _,bars=decode('CPNG','daily','/private/tmp/c21z-native22-continuation-20261109/us-CPNG/daily/response.body')
    tampered=deepcopy(bars);tampered[0]['high']=0.01
    with pytest.raises(ValueError,match='source_binding'):admit_rows(tampered,ticker='CPNG',market='us',timeframe='daily',cutoff=date(2026,11,6))
    tampered[0]['_native_capture']['normalized_bar_sha256']=digest({k:v for k,v in tampered[0].items() if k!='_native_capture'})
    with pytest.raises(ValueError,match='not_isolated'):admit_rows(tampered,ticker='CPNG',market='us',timeframe='daily',cutoff=date(2026,11,6))
    mixed=deepcopy(bars);mixed[0]['_native_capture']['response_body_sha256']='0'*64
    with pytest.raises(ValueError,match='source_binding'):admit_rows(mixed,ticker='CPNG',market='us',timeframe='daily',cutoff=date(2026,11,6))
