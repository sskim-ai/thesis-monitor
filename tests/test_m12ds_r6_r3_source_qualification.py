from copy import deepcopy
from datetime import date, datetime
from hashlib import sha256
import json

import pytest

from app.macro.providers.market import MARKET_SYMBOLS
from app.services.current_price_basis_service import price_basis_context
from scripts.m12ds_r6_r2_cutoff_audit import KST
from scripts.m12ds_r6_r3_source_qualification import (
    alpha_daily_inspection, kiwoom_daily_inspection, kr_post_close_receipt,
    latest_available_information, universe_coverage,
)

TARGET, PREVIOUS = date(2026, 9, 22), date(2026, 9, 21)


def us():
    return dict(api_id='usa06012', endpoint='/api/us/chart', http_status=200,
        request=dict(stex_tp='NY', stk_cd='SPY', upd_stkpc_tp='1', exrt_appl_tp='0'),
        raw_response_sha256='a'*64, response=dict(return_code=0, result_list=[
            dict(dt=d, open_pric='100', high_pric='104', low_pric='99', cur_prc='102',
                acc_trde_qty='1000', upd_stkpc_tp='') for d in ('20260922', '20260921')]))


def inspect_us(envelope, **kwargs):
    return kiwoom_daily_inspection(envelope, target=TARGET, previous=PREVIOUS, **kwargs)


def test_daily_context_close_is_not_settled_authority():
    result = inspect_us(us())
    assert result['close_owner'] == 'DATED_DAILY_BAR_CLOSE'
    assert result['pair'][0]['close'] == '102'
    assert result['adjustment'] == 'ADJUSTED'
    assert result['regular_session_finality'] == 'UNPROVEN'
    assert not result['current_direction_eligible'] and not result['lookahead_used']


@pytest.mark.parametrize('api_id,endpoint', [('usa20100','/api/us/quote'), ('ka10001','/api/dostk/stkinfo')])
def test_same_key_quote_is_never_daily_close(api_id, endpoint):
    envelope = us()
    envelope.update(api_id=api_id, endpoint=endpoint)
    result = inspect_us(envelope)
    assert result == dict(close_owner='CURRENT_QUOTE', current_direction_eligible=False, pair=None)


@pytest.mark.parametrize('field,value', [('dt',''), ('dt','20260920'), ('dt','20260923'),
    ('upd_stkpc_tp','0'), ('cur_prc','105'), ('high_pric','NaN'), ('acc_trde_qty','-1')])
def test_invalid_daily_row_fails_closed(field, value):
    envelope = us()
    envelope['response']['result_list'][0][field] = value
    with pytest.raises(ValueError):
        inspect_us(envelope)


def test_no_later_row_dependency_or_afterhours_finality_upgrade():
    envelope = us()
    envelope['response']['result_list'][0]['cur_prc'] = '103'
    assert not inspect_us(envelope)['current_direction_eligible']
    with pytest.raises(ValueError):
        inspect_us(envelope, interval='weekly')
    envelope['response']['result_list'].append({**envelope['response']['result_list'][0], 'dt':'20260923'})
    with pytest.raises(ValueError):
        inspect_us(envelope)


def test_complete_universe_cannot_shrink_or_duplicate():
    assert universe_coverage(MARKET_SYMBOLS)['status'] == 'PASS'
    assert universe_coverage(['SPY','QQQ','IWM'])['status'] == 'FAIL'
    assert 'XLRE' in universe_coverage(set(MARKET_SYMBOLS)-{'XLRE'})['missing']
    assert universe_coverage([*MARKET_SYMBOLS,'SPY'])['status'] == 'FAIL'


def alpha():
    return {'Meta Data': {'2. Symbol':'SPY','5. Time Zone':'US/Eastern'}, 'Time Series (Daily)': {
        d: {'1. open':'100','2. high':'104','3. low':'99','4. close':'102','5. volume':'1000'}
        for d in ('2026-09-22','2026-09-21')}}


def inspect_alpha(payload, function='TIME_SERIES_DAILY'):
    return alpha_daily_inspection(payload, function=function, symbol='SPY', target=TARGET, previous=PREVIOUS)


def test_alpha_daily_schema_does_not_assert_account_or_cutoff():
    result = inspect_alpha(alpha())
    assert result['adjustment'] == 'RAW' and result['pair'][0]['close'] == '102'
    assert not result['current_direction_eligible'] and result['sustainable_account_limit'] == 'UNPROVEN'


@pytest.mark.parametrize('key', ['Information','Note','Error Message'])
def test_alpha_provider_limit_is_not_zero_data_or_retry(key):
    result = inspect_alpha({key:'blocked'})
    assert result['status'] == 'RATE_ENTITLEMENT_OR_PROVIDER_DENIED' and result['pair'] is None


@pytest.mark.parametrize('function', ['GLOBAL_QUOTE','TIME_SERIES_DAILY_ADJUSTED'])
def test_alpha_other_endpoint_cannot_be_promoted(function):
    with pytest.raises(ValueError):
        inspect_alpha(alpha(), function)


def test_alpha_malformed_and_mixed_basis():
    with pytest.raises(KeyError):
        inspect_alpha({})
    payload = alpha()
    payload['Time Series (Daily)']['2026-09-22']['5. adjusted close'] = '100'
    with pytest.raises(ValueError):
        inspect_alpha(payload)


def kr(market='KOSPI'):
    code, venue = ('001','0') if market == 'KOSPI' else ('101','1')
    start = '2026-09-23T16:05:00+09:00'
    composite = dict(stk_cd=code, stk_nm=market, cur_prc='1000.00', flu_rt='+1.00', flo_stk_num='100')
    sectors = [composite, *[dict(stk_cd=str(int(code)+i+4).zfill(3), stk_nm='sector '+str(i),
        cur_prc='100', flu_rt=change, flo_stk_num='10') for i, change in enumerate(['2.00','2.00','-1.00','0.00'])]]
    payloads = {
        'ka20001':dict(cur_prc='+1000.00',flu_rt='+1.00'),
        'ka20003':dict(all_inds_idex=sectors),
        'ka20009':dict(inds_cur_prc_daly_rept=[dict(dt_n='20260923',cur_prc_n='1000',flu_rt_n='1')])}
    return {action:dict(api_id=action, endpoint='/api/dostk/sect',
        request=dict(inds_cd=code, **({'mrkt_tp':venue} if action!='ka20003' else {})),
        started_at=start, received_at=start, http_status=200, continuation=False,
        raw_response_sha256=str(i+1)*64, response=dict(return_code=0, **payload))
        for i,(action,payload) in enumerate(payloads.items())}


@pytest.mark.parametrize('market', ['KOSPI','KOSDAQ'])
def test_kr_postclose_exact_parity_and_stable_ranking(market):
    envelope = kr(market)
    result = kr_post_close_receipt(market,envelope)
    envelope['ka20003']['response']['all_inds_idex'].reverse()
    repeated = kr_post_close_receipt(market,envelope)
    assert result['top3'] == repeated['top3']
    assert result['bottom3'] == repeated['bottom3']
    assert result['candidate_sha256'] == repeated['candidate_sha256']
    assert result['regular_session_state'] == 'CLOSED' and result['tolerance'] == 0
    assert result['market'] == market and len(result['source_raw_hashes']) == 3


@pytest.mark.parametrize('mutation', ['before_close','level','return','date','venue','continuation','missing_action','duplicate'])
def test_kr_negative_controls(mutation):
    envelope = kr()
    if mutation == 'before_close':
        envelope['ka20001']['started_at'] = '2026-09-23T14:00:00+09:00'
    elif mutation == 'level':
        envelope['ka20001']['response']['cur_prc'] = '1000.000000000000001'
    elif mutation == 'return':
        envelope['ka20001']['response']['flu_rt'] = '1.01'
    elif mutation == 'date':
        envelope['ka20009']['response']['inds_cur_prc_daly_rept'][0]['dt_n'] = '20260922'
    elif mutation == 'venue':
        envelope['ka20003']['request']['inds_cd'] = '101'
    elif mutation == 'continuation':
        envelope['ka20003']['continuation'] = True
    elif mutation == 'missing_action':
        del envelope['ka20009']
    else:
        envelope['ka20003']['response']['all_inds_idex'].append(deepcopy(envelope['ka20003']['response']['all_inds_idex'][1]))
    with pytest.raises(ValueError):
        kr_post_close_receipt('KOSPI', envelope)


def test_size_and_zero_listed_derivative_rows_do_not_rank_as_sectors():
    envelope = kr()
    rows = envelope['ka20003']['response']['all_inds_idex']
    rows.extend([dict(stk_cd=code,stk_nm='not sector',cur_prc='100',flu_rt='99',flo_stk_num=count)
        for code,count in [('002','100'),('603','0')]])
    result = kr_post_close_receipt('KOSPI',envelope)
    assert set(result['excluded_codes']) == {'001','002','603'}


def macro():
    body = json.dumps({'observations':[{'date':'2026-09-21','value':'64.50'}]})
    url = 'https://fred.stlouisfed.org/series/DCOILWTICO'
    return dict(provider='fred', source_url=url, request=dict(series_id='DCOILWTICO'), http_status=200,
        raw_body=body, raw_response_sha256=sha256(body.encode()).hexdigest(),
        received_at='2026-09-23T16:00:00+09:00', publication_receipt=dict(
            contract='fred-published-observation-v1',provider='fred',series_code='DCOILWTICO',
            source_url=url,source_sha256='f'*64,expected_observation_date='2026-09-21',
            published_at='2026-09-22T12:00:00-05:00',next_publication_due='2026-09-23T00:00:00-04:00',current=False))


def inspect_macro(envelope):
    return latest_available_information(envelope,series='DCOILWTICO',as_of=datetime(2026,9,23,16,5,tzinfo=KST))


def test_expired_publication_can_be_dated_information_never_direction():
    result = inspect_macro(macro())
    assert result['value'] == '64.50' and '2026-09-21' in result['label']
    assert result['display_eligible'] and not result['current_direction_eligible']
    assert result['direction_fact_refs'] == [] and result['renderer_scope'] == 'INFORMATION_ONLY'


@pytest.mark.parametrize('mutation', ['hash','untrusted','future','nan','wrong_date','wrong_series'])
def test_macro_untrusted_rows_not_displayed(mutation):
    envelope = macro()
    if mutation == 'hash':
        envelope['raw_response_sha256'] = '0'*64
    elif mutation == 'untrusted':
        envelope['provider'] = 'unknown'
    elif mutation == 'future':
        envelope['received_at'] = '2026-09-24T16:00:00+09:00'
    elif mutation == 'nan':
        envelope['raw_body'] = envelope['raw_body'].replace('64.50','NaN')
        envelope['raw_response_sha256'] = sha256(envelope['raw_body'].encode()).hexdigest()
    elif mutation == 'wrong_date':
        envelope['publication_receipt']['expected_observation_date'] = '2026-09-22'
    else:
        envelope['request']['series_id'] = 'DGS10'
    with pytest.raises(ValueError):
        inspect_macro(envelope)


def test_kr_intraday_adjustment_contract_not_changed():
    result = price_basis_context('adjusted_intraday')
    assert result['phase'] == 'INTRADAY'
    assert result['adjustment'] == 'ADJUSTED'


def test_exact_previous_exchange_session_not_arbitrary_older_bar():
    envelope = us()
    envelope['response']['result_list'][1]['dt'] = '20260918'
    with pytest.raises(ValueError, match='previous_exchange_session_required'):
        kiwoom_daily_inspection(envelope, target=TARGET, previous=date(2026,9,18))


def test_kr_cross_venue_cannot_be_combined():
    envelope = kr('KOSPI')
    envelope['ka20003'] = kr('KOSDAQ')['ka20003']
    with pytest.raises(ValueError):
        kr_post_close_receipt('KOSPI', envelope)


@pytest.mark.parametrize('field,value', [('cur_prc','NaN'), ('flu_rt','Infinity')])
def test_kr_malformed_numeric_is_not_exact_parity(field, value):
    envelope = kr()
    envelope['ka20001']['response'][field] = value
    with pytest.raises(ValueError):
        kr_post_close_receipt('KOSPI', envelope)


def test_afterhours_wall_clock_does_not_grant_us_authority():
    envelope = us()
    envelope['received_at'] = '2026-09-23T08:05:00+09:00'
    assert inspect_us(envelope)['regular_session_finality'] == 'UNPROVEN'


def test_kr_style_rows_excluded_by_existing_taxonomy():
    envelope = kr('KOSDAQ')
    envelope['ka20003']['response']['all_inds_idex'].append(
        dict(stk_cd='138',stk_nm='KOSDAQ 100',cur_prc='100',flu_rt='99',flo_stk_num='100'))
    assert '138' in kr_post_close_receipt('KOSDAQ',envelope)['excluded_codes']


def test_kr_scalar_and_exact_history_row_do_not_require_unconsumed_pages():
    envelope = kr()
    envelope['ka20001']['continuation'] = True
    envelope['ka20009']['continuation'] = True
    result = kr_post_close_receipt('KOSPI',envelope)
    assert result['status'] == 'PASS'
    assert result['continuation']['ka20009']
    envelope['ka20003']['continuation'] = True
    with pytest.raises(ValueError):
        kr_post_close_receipt('KOSPI',envelope)
