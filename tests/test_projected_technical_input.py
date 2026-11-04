"""Synthetic identities exercise the same input contract, never real readiness."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone, date
from types import SimpleNamespace

import pytest
from app.services import projected_technical_input as technical
from app.services.completed_session_projection import project_completed_rows
from app.services.market_session import korea_market_session, us_market_session
from app.services.technical_feature_dependency_service import assess_feature_dependency


def fixture(market='kr', ticker='UNSEEN'):
    cutoff=datetime(2026,10,22,3,tzinfo=timezone.utc)
    target=(korea_market_session if market=='kr' else us_market_session)(cutoff).latest_completed_regular_session_date
    read=SimpleNamespace(subject=ticker,market=market,market_state='CLOSED',role='adjusted_daily',
        timeframe='daily',adjusted=True,count=1000,query_date='20261022',latest_completed_session=target.isoformat(),
        entry_id=f'{market}:{ticker}:adjusted_daily',canonical_security_id='security:'+ticker)
    rows=[dict(date=(target-timedelta(days=i)).isoformat(),open=10.,high=12.,low=9.,close=11.,volume=100.) for i in range(1001)]
    selected,projection=project_completed_rows(rows,read=read,cutoff=cutoff,source_pages=[dict(sha256='a'*64)])
    return dict(read=read,cutoff=cutoff,all_rows=rows,projection=projection,rows=selected)


@pytest.mark.parametrize('market,ticker',[('kr','111111'),('us','NEWCOMMON'),('us','NEWADS'),('us','NEWLIST')])
def test_unseen_generic_original_consumer(market,ticker):
    value=technical.review_window(**fixture(market,ticker))
    assert value['status']=='TECHNICAL_INPUT_REFERENCE_PASS'
    assert value['context']['quality']['D']['usable_for_current_reasoning']
    assert not value['context']['features']['weekly']['facts']
    assert any(r.get('dependency',{}).get('dependency_kind')=='RECURSIVE_FULL_HISTORY' for r in value['feature_ledger'])
    assert all(not value[k] for k in ('technical_signal','completed_price_authority','financial_use','economic_use','D01_D02','native_use','model_use'))


@pytest.mark.parametrize('case',['rows','projection','basis','count','timeframe','security','role','cutoff','short','invalid_old'])
def test_changed_projection_and_required_history_fail(case):
    x=fixture()
    if case=='rows': x['rows'][0]['close']=10.5
    elif case=='projection': x['projection']['selected_sha256']='b'*64
    elif case=='basis': x['read'].adjusted=False
    elif case=='count': x['read'].count=73
    elif case=='timeframe': x['read'].timeframe='weekly'
    elif case=='security': x['read'].canonical_security_id='other'
    elif case=='role': x['read'].role='unadjusted_weekly_valuation'
    elif case=='cutoff': x['cutoff']+=timedelta(days=2)
    elif case=='short': x['all_rows']=x['all_rows'][:73]
    else: x['all_rows'][-1]['high']=1
    with pytest.raises(ValueError): technical.review_window(**x)


def test_pure_review_never_issues_capability_or_accepts_json():
    result=technical.review_window(**fixture())
    for cap in (result,technical.ProjectedTechnicalInput()):
        with pytest.raises(ValueError,match='issued_capability'):
            technical.consume(object(),cap,dispatcher=object(),entry_id='x',security_id='s',generation_id='g',timeframe='daily')
    with pytest.raises(ValueError,match='feature_off'):
        technical.issue(object(),object(),dispatcher=object(),entry_id='x')
    with pytest.raises(ValueError): technical.issue(object(),object(),dispatcher=object(),entry_id='x',enabled=True)


@pytest.mark.parametrize('semantic,minimum',[('sma_20',20),('ema_20',20),('rsi_14',14),('macd_line',26),('atr_14',14),('obv',2)])
def test_original_dependency_bad_row_not_ignored(semantic,minimum):
    dates=[date(2020,1,1)+timedelta(days=i) for i in range(73)]
    a=assess_feature_dependency(semantic=semantic,minimum_history=minimum,row_dates=dates,invalid_dates=[dates[0]])
    assert a.classification.value==('SAFE_INDEPENDENT_OF_BAD_ROW' if semantic=='sma_20' else 'UNSAFE_DEPENDS_ON_BAD_ROW')


@pytest.mark.parametrize('count,minimum',[(4,20),(16,200),(73,200)])
def test_feature_minimum_does_not_lower_role_horizon(count,minimum):
    dates=[date(2020,1,1)+timedelta(days=i) for i in range(count)]
    a=assess_feature_dependency(semantic='sma_200',minimum_history=minimum,row_dates=dates,invalid_dates=[])
    assert a.classification.value=='UNAVAILABLE_OTHER_REASON'
