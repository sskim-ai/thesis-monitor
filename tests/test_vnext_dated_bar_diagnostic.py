from copy import deepcopy

import pytest

from app.services.market_session import _exchange_calendar
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows, canonical_fingerprint
from app.services.vnext_research_store import digest
from app.services.vnext_timeframe_views import analytic_view, DATED_DIAGNOSTIC_CONTRACT


def specimen(count=100):
    dates=_exchange_calendar('XNYS').sessions_in_range('2026-01-02','2026-10-29')[-count:]
    rows=[dict(date=str(d.date()),open=10.,high=12.,low=9.,close=11.,volume=100.) for d in dates]
    rows[-1]['close']=8.
    return rows


def dated(rows, **kwargs):
    issues=inspect_normalized_ohlcv_rows([rows[-1]],timeframe='daily').issues
    evidence=dict(raw_source_generation='original',parent_raw_sha256=digest(rows),
        original_current_owner_status='POLICY_DENIED',anomalies=[dict(date=i.bar_date,
        reason=str(i.violation),row_sha256=i.row_fingerprint) for i in issues])
    args=dict(timeframe='daily',market='US',session='2026-10-29',
        lagged_end_policy=DATED_DIAGNOSTIC_CONTRACT,terminal_evidence=evidence)
    args.update(kwargs)
    return analytic_view(rows,**args)


@pytest.mark.parametrize('count',[100,79])
def test_exact_dated_suffix_without_current_or_research_grant(count):
    rows=specimen(count); before=deepcopy(rows)
    strict=analytic_view(rows,timeframe='daily',market='US',session='2026-10-29')
    projected=dated(rows)
    assert strict['count']==0 and not inspect_normalized_ohlcv_rows(rows,timeframe='daily').valid
    assert projected['valid_contiguous_count']==count-1
    assert projected['analysis_as_of']=='2026-10-28' and projected['stale_sessions']==1
    assert projected['requested_target_session']=='2026-10-29'
    assert projected['scope']=='DATED_DIAGNOSTIC_ONLY'
    assert not projected['research_admission'] and not projected['current_price_complete']
    assert projected['current_price_owner']=='DENIED' and rows==before
    assert dated(rows)==projected


@pytest.mark.parametrize('change', ['middle_bad','duplicate','missing_session','ordering',
    'future','missing_target','wrong_basis','provisional','volume','unknown_calendar',
    'weekly','derived','wrong_policy','forged_anomaly','valid_latest','extra_terminal_anomaly'])
def test_dated_projection_fails_closed(change):
    rows=specimen();kw={}
    if change=='middle_bad':rows[-4]['close']=8.
    elif change=='duplicate':rows[-4]=deepcopy(rows[-3])
    elif change=='missing_session':rows.pop(-4)
    elif change=='ordering':rows[-5],rows[-4]=rows[-4],rows[-5]
    elif change=='future':rows[-1]['date']='2026-10-30'
    elif change=='missing_target':rows.pop()
    elif change=='wrong_basis':rows[-4]['price_basis']='unadjusted'
    elif change=='provisional':rows[-1]['bar_state']='PROVISIONAL'
    elif change=='volume':rows[-4]['volume']=float('nan')
    elif change=='unknown_calendar':kw['market']='UNKNOWN'
    elif change=='weekly':kw['timeframe']='weekly'
    elif change=='derived':kw['source_kind']='DERIVED_FROM_DAILY'
    elif change=='wrong_policy':kw['lagged_end_policy']='unreviewed'
    elif change=='forged_anomaly':kw['terminal_evidence']={'anomalies':[]}
    elif change=='valid_latest':
        rows[-1]['close']=11.
        kw['terminal_evidence']={'anomalies':[]}
    elif change=='extra_terminal_anomaly':rows[-2]['close']=8.
    with pytest.raises(ValueError):dated(rows,**kw)


def test_quote_does_not_contaminate_diagnostic_rows_or_digest():
    first=specimen();second=deepcopy(first);second[-1]['close']=7.
    one,two=dated(first),dated(second)
    assert one['rows']==two['rows'] and one['rows_sha256']==two['rows_sha256']
    assert one['view_sha256']!=two['view_sha256']
    assert not one['economic_direction_authority'] and not one['original_owner_grant']


def test_no_caller_json_can_be_an_original_owner():
    from app.services.vnext_timeframe_views import replay_dated_diagnostic
    with pytest.raises(ValueError,match='original_dated_replay_owner_required'):
        replay_dated_diagnostic({'allowed_use':'DATED_ANALYTIC_RESEARCH_ONLY'},'UNSEEN',
            source_sha='0'*64,session='2026-10-29',as_of='2026-10-30T03:00:00+00:00',
            parser_root=None,parser_pins=None)
