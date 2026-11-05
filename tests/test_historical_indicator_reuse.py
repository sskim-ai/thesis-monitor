import hashlib
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
import pytest
from app.services.historical_indicator_reuse import load_engine,project_indicators,cached_project
from app.services.scoped_source_plan import ScopedStockRead
from app.services.market_session import exchange_calendar

@pytest.fixture
def inputs():
    root=Path('/Users/sskim/Codex/ohlcv-analyst');code=(root/'app/indicators/technical.py').read_bytes()
    engine=load_engine(root,hashlib.sha256(code).hexdigest())
    return dict(engine=engine,algorithm_sha256=hashlib.sha256(code).hexdigest(),
        observed_at=datetime(2026,11,5,6,tzinfo=timezone.utc),generation='SYNTHETIC_TEST_ONLY',raw_sha256=['a'*64])

def read(timeframe='daily',count=300):
    role={'daily':'adjusted_daily','weekly':'adjusted_weekly','monthly':'adjusted_monthly'}[timeframe]
    return ScopedStockRead(entry_id='us:UNSEEN:'+role,market='us',subject='UNSEEN',canonical_security_id='test-security',
        exchange='ND',route='/api/us/chart',api_id={'daily':'usa06012','weekly':'usa06013','monthly':'usa06014'}[timeframe],
        role=role,timeframe=timeframe,adjusted=True,count=count,max_pages=min(12,count//100+2),query_date='20261105',
        latest_completed_session='2026-11-04',market_state='TEST_ONLY')

def rows(timeframe='daily',n=80):
    cal=exchange_calendar.get_calendar('XNYS',start='2019-12-01',end='2026-11-10')
    days=[s.date() for s in cal.sessions_in_range('2020-01-01','2026-11-04')]
    if timeframe=='weekly':days=list({d.isocalendar()[:2]:d for d in days}.values())
    if timeframe=='monthly':days=list({(d.year,d.month):d for d in days}.values())
    days=days[-n:]
    return [dict(date=d.isoformat(),open=100+i%7,high=110+i%7,low=90+i%7,close=101+i%5,volume=1000+i) for i,d in enumerate(days)]

@pytest.mark.parametrize('timeframe',['daily','weekly','monthly'])
def test_exact_existing_engine_and_timeframe_labels(inputs,timeframe):
    data=rows(timeframe);r=read(timeframe)
    p=project_indicators(data,read=r,**inputs)
    expected=inputs['engine'].indicator_dict(inputs['engine'].add_indicators(pd.DataFrame(data)).iloc[-1])
    assert p['bars'][-1]['indicators']==expected
    assert set(expected)==set(inputs['engine'].INDICATOR_COLUMNS) and 'MA20' not in expected
    assert p['indicator_requirements']['RETURN_20D']['period_unit']=={'daily':'TRADING_DAY_BARS','weekly':'WEEK_BARS','monthly':'MONTH_BARS'}[timeframe]
    assert p['current_eligibility'] is False and p['investor_flows']=='NOT_FETCHED'

def test_short_history_preserves_original_numbers_not_warmup_gate(inputs):
    p=project_indicators(rows('monthly',18),read=read('monthly'),**inputs)
    assert p['valid_bars']==18 and p['bars'][-1]['indicators']['MA33'] is None
    assert p['bars'][-1]['indicators']['MACD_OSC_320_640_9'] is not None
    assert p['latest_availability']['MACD_OSC_320_640_9']['status']=='CALCULATED_WITH_LIMITED_HISTORY'
    assert p['bars'][-1]['indicators']['RSI14'] is not None

@pytest.mark.parametrize('position',[-1,35])
def test_invalid_source_never_spliced_or_repaired(inputs,position):
    data=rows();data[position]['close']=80
    p=project_indicators(data,read=read(),**inputs)
    assert p['valid_bars']==len(data)-1 and len(p['invalid_rows'])==1
    if position==-1:assert p['last_valid_as_of']==data[-2]['date'] and p['scope']=='AS_OF_HISTORICAL_ONLY'
    else:assert p['bars'][35]['contiguous_valid_bars']==1 and p['bars'][35]['indicators']['MA33'] is None

def test_cache_does_not_call_engine_again(inputs,tmp_path,monkeypatch):
    data=rows();opts=dict(read=read(),**inputs)
    path,first,computed=cached_project(tmp_path/'cache',data,**opts);assert computed
    monkeypatch.setattr(inputs['engine'],'add_indicators',lambda _: (_ for _ in ()).throw(AssertionError('recalculated')))
    _,again,computed=cached_project(tmp_path/'cache',data,**opts)
    assert not computed and first==again and path.is_file()

def test_duplicate_dates_do_not_bridge_contiguous_windows(inputs):
    data=rows();data.insert(35,dict(data[35]))
    p=project_indicators(data,read=read(),**inputs)
    assert len(p['invalid_rows'])==2 and p['bars'][35]['contiguous_valid_bars']==1
