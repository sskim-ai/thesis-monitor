from copy import deepcopy
from datetime import date
import pytest

from app.services.vnext_dated_calendar import calendar_for_range, POLICY
from app.services.vnext_timeframe_views import analytic_view
from app.services.vnext_dated_technical_owner import _view
from app.services.vnext_dated_technical_appendix import build_appendix, render_appendix
from app.services.vnext_no_send_controller import cycle_from_packet
from test_vnext_dated_technical_owner import source, owner, kw


@pytest.mark.parametrize('day',['2026-06-03','2026-07-17'])
def test_official_holiday_is_opt_in_and_legacy_unchanged(day):
    args=dict(start=date(2026,1,1),end=date(2026,12,31))
    _,legacy=calendar_for_range('KR',**args)
    _,new=calendar_for_range('KR',**args,policy=POLICY)
    assert legacy.is_session(day) and not new.is_session(day)
    assert calendar_for_range('KR',**args)[1] is legacy


@pytest.mark.parametrize('start,end',[('2026-06-02','2026-06-04'),('2026-07-16','2026-07-20')])
def test_known_holiday_continuity_without_fabricated_bar(start,end):
    rows=[dict(date=d,open=10,high=12,low=9,close=11,volume=100) for d in (start,end)]
    before=deepcopy(rows)
    assert analytic_view(rows,timeframe='daily',market='KR',session=end)['count']==1
    new=analytic_view(rows,timeframe='daily',market='KR',session=end,calendar_policy=POLICY)
    assert new['rows']==before and len(rows)==2


@pytest.mark.parametrize('day',['2026-08-17','2026-09-24','2026-09-25','2026-10-05','2026-10-09'])
def test_other_official_holidays_remain_closed(day):
    args=dict(start=date(2026,1,1),end=date(2026,12,31))
    assert not calendar_for_range('KR',**args)[1].is_session(day)
    assert not calendar_for_range('KR',**args,policy=POLICY)[1].is_session(day)


def test_unknown_policy_and_real_trading_gap_not_waived():
    with pytest.raises(ValueError,match='policy_unknown'):
        calendar_for_range('KR',start=date(2026,1,1),end=date(2026,12,31),policy='caller-forged')
    rows=[dict(date=d,open=10,high=12,low=9,close=11,volume=100) for d in ('2026-07-20','2026-07-22')]
    v=analytic_view(rows,timeframe='daily',market='KR',session='2026-07-22',calendar_policy=POLICY)
    assert v['count']==1 and 'PERIOD_GAP_OR_DUPLICATE' in v['first_invalid']['reasons']


def test_monthly_excluded_provider_period_stays_dated():
    s=source(market='KR',tf='monthly',n=30)
    # Reproduce the original parser selection excluding the October raw row.
    s['rows']=s['rows'][:-1];s['requested_source_session']='2026-10-30'
    assert _view(s)['count']==0
    v=_view(s,POLICY)
    assert v['count']==29 and v['session']=='2026-09-30'
    assert all(r['date']<'2026-10-01' for r in v['rows'])


def test_close_time_and_incomplete_month_not_inferred_from_row_date():
    from app.services.price_structure_wave_fibonacci_v3_service import _latest_completed_session
    import pandas as pd
    _,cal=calendar_for_range('KR',start=date(2026,10,1),end=date(2026,10,31),policy=POLICY)
    assert str(_latest_completed_session(cal,pd.Timestamp('2026-10-30T06:29:59Z')))[:10]=='2026-10-29'
    assert str(_latest_completed_session(cal,pd.Timestamp('2026-10-30T06:30:01Z')))[:10]=='2026-10-30'


@pytest.mark.parametrize('code',['UNSEEN_US','UNSEEN_ADS','UNSEEN_BANK'])
def test_appendix_live_owner_not_new_judgment(monkeypatch,code):
    s=source(code=code,n=260);o=owner(monkeypatch,[s]);p=build_appendix(o,security=s['security'],cutoff=kw(s)['cutoff'])
    role=p['roles']['daily'];assert role['count']==259
    assert role['indicators']['sma_200']['fact']['minimum_history']==200
    assert role['indicators']['sma_200']['status']=='DATED_NOT_CURRENT'
    assert not any(p[k] for k in ('current_price','timing','newbuyer','holder','overall','send'))
    text=render_appendix(p);assert 'sma_200' in text and 'mean(close, 200)' in text and '2026-10-28' in text
    with pytest.raises(ValueError,match='live_original_owner'):
        build_appendix(p,security=s['security'],cutoff=kw(s)['cutoff'])
    o.revoke()
    with pytest.raises(ValueError,match='revoked'):
        build_appendix(o,security=s['security'],cutoff=kw(s)['cutoff'])


def test_short_history_no_sma200_and_bad_last_bar_not_promoted(monkeypatch):
    s=source(n=67);s['rows'][-1]['close']=1;o=owner(monkeypatch,[s]);before=deepcopy(s)
    a=build_appendix(o,security=s['security'],cutoff=kw(s)['cutoff'])
    assert a['roles']['daily']['indicators']['sma_200']['status']=='INSUFFICIENT_HISTORY'
    assert a['roles']['daily']['count']==66 and s==before
    wrong=dict(s['security'],ticker='CROSS_TICKER')
    with pytest.raises(ValueError,match='security'):build_appendix(o,security=wrong,cutoff=kw(s)['cutoff'])


def test_cycle_uses_price_generation_not_optional_monthly():
    sec=dict(country='KR',exchange='KRX',canonical_security_id='UNSEEN')
    reg=dict(security=sec,registration_version='r1')
    p=dict(base=dict(public_security=sec,run_id='original-price-generation',
        evidence=[dict(field='completed_close',data=dict(calendar=dict(session='2026-10-29')))]),
        dated_technical_scopes=[dict(source_generation='monthly-generation')])
    c=cycle_from_packet(registration=reg,packet=p,correction_epoch='new-proof')
    assert c['source_generation']=='original-price-generation' and c['session']=='2026-10-29'
    p['base']['evidence'].append(dict(field='completed_close',data=dict(calendar=dict(session='2026-10-28'))))
    with pytest.raises(ValueError,match='exact_price_packet'):cycle_from_packet(registration=reg,packet=p,correction_epoch='new-proof')
