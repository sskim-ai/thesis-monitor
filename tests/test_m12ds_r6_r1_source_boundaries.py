"""Keep observed rejection mechanisms closed; these are not fabricated repairs."""
from copy import deepcopy
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.macro.providers.market import completed_market_bars
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService
from app.services.ohlcv_client import OhlcvClient


AT = datetime(2026, 9, 23, 12, 53, tzinfo=ZoneInfo('Asia/Seoul'))


def test_raw_current_us_bar_without_finality_still_denied():
    payload = {'meta': {'provider': 'kiwoom', 'adjusted': True}, 'periods': {'daily': [
        dict(date='2026-09-18', open=761.31, high=762, low=757.971, close=761.69),
        dict(date='2026-09-21', open=766.251, high=774.89, low=766.03, close=773.5),
        dict(date='2026-09-22', open=774.03, high=775.14, low=772.57, close=774.12),
    ]}}
    before = deepcopy(payload)
    with pytest.raises(ValueError, match='completed_session_and_previous_close_required'):
        completed_market_bars(payload, AT)
    assert payload == before
    # An actual source finality marker is sufficient; receipt dates are never shifted.
    payload['periods']['daily'][-1]['bar_state'] = 'FINAL'
    assert completed_market_bars(payload, AT)[0]['date'] == '2026-09-22'
    for bar in payload['periods']['daily']:
        bar['date'] = '2026-09-04'
    with pytest.raises(ValueError):
        completed_market_bars(payload, AT)


def test_kr_observed_current_and_target_history_cannot_mix():
    current = dict(cur_prc='+7037.88', flu_rt='+0.28')
    sectors = {'all_inds_idex': [dict(stk_cd='001', **current)]}
    history = {'inds_cur_prc_daly_rept': [
        dict(dt_n='20260923', cur_prc_n='+7041.21', flu_rt_n='+0.33'),
        dict(dt_n='20260922', cur_prc_n='+7017.91', flu_rt_n='+0.15')]}
    with pytest.raises(ValueError, match='current/historical index mismatch'):
        KiwoomKrMarketContextService._validate_session_identity(session_date=date(2026, 9, 22),
            observed_at=AT, current=current, sectors=sectors, history=history, market='KOSPI', code='001')
    history['inds_cur_prc_daly_rept'] = []
    with pytest.raises(ValueError, match='historical session identity is missing'):
        KiwoomKrMarketContextService._validate_session_identity(session_date=date(2026, 9, 22),
            observed_at=AT, current=current, sectors=sectors, history=history, market='KOSPI', code='001')


def test_price_adjustment_is_source_metadata_not_label_coercion():
    payload = dict(meta=dict(provider='kiwoom', adjusted=True), resolved_symbol={'code':'000660'},
        periods={'daily':[dict(date='2026-09-23', open=100,high=110,low=90,close=101)]})
    bars, _, provider = OhlcvClient._decode_period_payload(payload,ticker='000660',period='daily',adjusted=True)
    assert provider == 'kiwoom' and bars[0]['date'] == '2026-09-23'
    payload['meta']['adjusted'] = False
    with pytest.raises(ValueError, match='ohlcv_adjustment_basis_mismatch'):
        OhlcvClient._decode_period_payload(payload,ticker='000660',period='daily',adjusted=True)
