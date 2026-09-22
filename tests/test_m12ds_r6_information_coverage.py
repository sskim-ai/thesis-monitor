import asyncio
from copy import deepcopy
from datetime import date, datetime
import json
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.macro.publication import publication_receipt, publication_current
from app.macro.providers.market import completed_market_bars
from app.services.market_current_context_service import current_context_eligible
from app.services.market_current_context_service import kr_sector_alias
from app.services.market_numeric_claim_service import numeric_catalog, validate_catalog
from app.services.us_full_message_service import _night_timeframe_line
from app.services.krx_night_history_service import build_same_contract_timeframes, store_normalized_bar
from app.services.krx_night_month_backfill_service import backfill_selected_month
from app.services.accepted_calibration_message_service import calibration_render, digest
from tests.test_krx_night_history_service import _bar, _row
from tests.test_m12ds_r4_r4_presentation import bound_plan

KST = ZoneInfo('Asia/Seoul')
AT = datetime(2026, 9, 22, 8, tzinfo=KST)


def html(end='2026-09-15', updated='Sep 16, 2026 12:17 PM CDT', next_='Sep 23, 2026'):
    return (f'<meta name="dcterms:PeriodOfTime" content="start:2000-01-01; end:{end};">'
            f'<span class="updated-text default-text" title="{updated}"></span>'
            f'<span class="updated-text text-link" title="{next_}"></span>').encode()


def test_wti_daily_observations_follow_official_weekly_publication_not_age():
    receipt = publication_receipt(html(), 'DCOILWTICO', AT)
    assert publication_current(receipt, 'DCOILWTICO', '2026-09-15', AT)
    assert not publication_current(receipt, 'DCOILWTICO', '2026-09-14', AT)
    assert not publication_current(receipt, 'DCOILWTICO', '2026-09-15', datetime(2026, 9, 24, tzinfo=KST))
    assert not publication_current(receipt, 'DGS10', '2026-09-15', AT)
    assert not publication_current(receipt, 'DCOILWTICO', '2026-09-15', datetime(2026, 9, 15, tzinfo=KST))
    with pytest.raises(ValueError):
        publication_receipt(b'<html>no dates</html>', 'DCOILWTICO', AT)


def test_h15_published_prior_business_day_is_current_and_next_release_clock_is_exact():
    receipt = publication_receipt(html('2026-09-18', 'Sep 21, 2026 3:16 PM CDT', 'Sep 22, 2026'), 'DGS10', AT)
    assert publication_current(receipt, 'DGS10', '2026-09-18', AT)
    assert not publication_current(receipt, 'DGS10', '2026-09-18', datetime(2026, 9, 23, 5, 15, tzinfo=KST))


def bars():
    return {'meta': {'provider':'kiwoom'}, 'periods': {'daily': [
        dict(date=d, open=100, high=110, low=90, close=c)
        for d,c in [('2026-09-18',100),('2026-09-21',105),('2026-09-22',109)]]}}


def test_completed_source_row_not_latest_intraday_or_host_date_shift():
    data = bars()
    old = deepcopy(data)
    current, previous, receipt = completed_market_bars(data, AT)
    assert current['date'] == '2026-09-21' and current['close'] == 105
    assert previous['date'] == '2026-09-18' and previous['close'] == 100
    assert receipt['dates_relabelled'] is False and data == old
    data['periods']['daily'][1]['date'] = '2026-09-22T00:00:00+00:00'
    assert completed_market_bars(data, AT)[0]['date'] == '2026-09-21'
    data['periods']['daily'][1]['date'] = '2026-09-22T00:00:00'
    with pytest.raises(ValueError, match='ambiguous'):
        completed_market_bars(data, AT)


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'unknown_owner', 'bad_ohlc'])
def test_session_selection_fails_closed(change):
    data = bars()
    if change == 'missing':
        data['periods']['daily'].pop(1)
    elif change == 'duplicate':
        data['periods']['daily'].append(data['periods']['daily'][1])
    elif change == 'unknown_owner':
        data['meta']['provider'] = 'unknown'
    else:
        data['periods']['daily'][1]['close'] = 999
    with pytest.raises(ValueError):
        completed_market_bars(data, AT)


def test_current_context_does_not_rewrite_daily_delta_denial():
    receipt = publication_receipt(html(), 'DCOILWTICO', AT)
    fact = dict(fact_id='oil', fact_type='market_oil', as_of_date='2026-09-15', fields=dict(
        series_code='DCOILWTICO', provider='fred', quality='fresh', publication_receipt=receipt,
        today_signal_eligible=False, structured_state='REFERENCE_LAGGING'))
    original = deepcopy(fact)
    assert current_context_eligible(fact, '2026-09-21', '2026-09-22')
    assert fact == original
    fact['fields']['source_unavailable'] = True
    assert not current_context_eligible(fact, '2026-09-21', '2026-09-22')


def sector_source(market='us'):
    source = dict(session=dict(market=market,assessment_date='2026-09-22',latest_completed_regular_session_date='2026-09-21'),
                  fact_catalog=[],numeric_registry=[],adapter_context={'sectors':[]})
    for i, (code, value) in enumerate([('XLB',1),('XLC',2),('XLE',2),('XLF',-1),('XLI',-2),('XLK',-3)]):
        ref = 'sector:'+code
        fields = dict(label=code, series_code=code, return_pct=value, quality='fresh',
                      today_signal_eligible=True,temporal_role='CURRENT_OBSERVATION')
        fact = dict(fact_id=ref, fact_type='market_sector',as_of_date='2026-09-21',fields=fields)
        source['fact_catalog'].append(fact)
        source['numeric_registry'].append(dict(fact_id=ref,field_path='fields.return_pct',value=value,
            unit='pct',registered=True,prose_allowed=True,scope='market'))
    return source


def test_sector_top_bottom_is_deterministic_and_no_cross_session():
    source = sector_source()
    refs = [f['fact_id'] for f in source['fact_catalog']]
    def make():
        return numeric_catalog(source,market='us',assessment_date='2026-09-22',eligible_refs=refs)
    catalog = make()
    ranks = [c for c in catalog['claims'] if c['claim_type']=='SECTOR_RANKING']
    assert ranks[0]['input_fact_refs'] == ['sector:XLC','sector:XLE','sector:XLB']
    assert ranks[1]['input_fact_refs'] == ['sector:XLK','sector:XLI','sector:XLF']
    source['fact_catalog'].reverse()
    assert [c['rendered_text'] for c in make()['claims']] == [c['rendered_text'] for c in catalog['claims']]
    source['fact_catalog'][0]['as_of_date'] = '2026-09-18'
    assert 'sector:XLK' not in [r for c in make()['claims'] for r in c['input_fact_refs']]
    assert validate_catalog(catalog,source)['status']=='FAIL'


def test_stock_asof_and_support_resistance_independent_of_entry_ranges():
    packet, base = bound_plan()
    quote = dict(contract='current-price-context-v1', availability='partial',as_of_date=packet.assessment_date,
        price_basis='close', currency='USD',active_support=dict(available=True,zone_low=10,zone_high=11,source='dynamic',timeframe='daily'),
        active_resistance={'available':False})
    receipt = {**base.acceptance,'entries_sha256':digest({}),'quote_context_sha256':digest(quote)}
    plan = base.model_copy(update=dict(entries={},quote_context=quote,acceptance=receipt,acceptance_sha256=digest(receipt)))
    rendered = calibration_render(packet,plan).text
    assert '가격 자료 기준:' in rendered and '기술적 지지: 10.00 ~ 11.00 USD' in rendered
    assert '기술적 저항: 미확인' in rendered
    assert '가격 흐름 관찰 구간:' not in rendered and '기업가치 기준 진입 범위:' not in rendered


def test_valid_in_progress_ohlc_not_hidden_by_missing_return(tmp_path):
    store_normalized_bar(tmp_path,_bar(date(2026,9,21)))
    frames = build_same_contract_timeframes(tmp_path,instrument_root='KOSPI200',reference_date=date(2026,9,21))
    text = _night_timeframe_line(frames.weekly, '주봉')
    assert '진행중' in text and '고가 103.00' in text and '저가 99.00' in text
    assert '포함 1/1 거래일' in text and '등락률 미확인' in text and '자료 부족' not in text
    assert not frames.weekly.missing_dates and frames.weekly.future_expected_dates


def test_official_month_backfill_caches_raw_same_contract_and_excludes_future_weekends(tmp_path):
    queried=[]
    def handler(request):
        day=request.url.params['basDd']
        queried.append(day)
        return httpx.Response(200,json={'OutBlock_1':[_row(day=day)]})
    selected=[SimpleNamespace(session_date=date(2026,9,4),product='KOSPI200',contract_code='A0169000')]
    receipt=asyncio.run(backfill_selected_month(tmp_path,selected,
        as_of=datetime(2026,9,5,8,tzinfo=KST),transport=httpx.MockTransport(handler)))
    assert queried==['20260901','20260902','20260903','20260904']
    assert receipt['coverage'][0]['missing_dates']==[] and receipt['request_count']==4
    assert all(len(r['raw_payload_sha256'])==64 for r in receipt['rows'])
    repeat=asyncio.run(backfill_selected_month(tmp_path,selected,
        as_of=datetime(2026,9,5,8,tzinfo=KST),transport=httpx.MockTransport(handler)))
    assert repeat['request_count']==0 and len(queried)==4
    assert json.dumps(receipt).find('Kiwoom') == -1


@pytest.mark.parametrize('as_of', [datetime(2026,9,19,8,tzinfo=KST), datetime(2026,9,20,8,tzinfo=KST)])
def test_weekend_uses_actual_friday_session(as_of):
    data=bars()
    data['periods']['daily']=[dict(date=d,open=100,high=110,low=90,close=101,bar_state='FINAL')
                             for d in ('2026-09-16','2026-09-17','2026-09-18')]
    data['meta']['provider']='native-final'
    latest,previous,_=completed_market_bars(data,as_of)
    assert latest['date']=='2026-09-18' and previous['date']=='2026-09-17'


def test_us_holiday_has_no_fabricated_session():
    data=bars()
    data['periods']['daily']=[dict(date=d,open=100,high=110,low=90,close=101,bar_state='FINAL')
                             for d in ('2026-09-03','2026-09-04','2026-09-07')]
    latest,previous,_=completed_market_bars(data,datetime(2026,9,8,8,tzinfo=KST))
    assert latest['date']=='2026-09-04' and previous['date']=='2026-09-03'


def test_kr_rank_alias_binds_canonical_taxonomy_value_and_session():
    source=sector_source('kr')
    source['fact_catalog']=[]
    source['numeric_registry']=[]
    refs=[]
    for scope in ('KOSPI','KOSDAQ'):
        for i,value in enumerate((1,2,-1)):
            ref=f'canonical:{scope}:{i}'
            alias=f'kiwoom:{scope}:{i}'
            name=f'업종 {chr(65+i)}'
            fields=dict(market_scope=scope,taxonomy='kiwoom-sector-index-v1',metric_role='actual_sector_breadth',
                        source_ref=alias,sector=name,sector_code=str(i),return_pct=value)
            fact=dict(fact_id=ref,fact_type='market_cross_section_sector',as_of_date='2026-09-21',source='KIWOOM_REST',fields=fields)
            source['fact_catalog'].append(fact)
            source['numeric_registry'].append(dict(fact_id=ref,field_path='fields.return_pct',value=value,
                unit='pct',registered=True,prose_allowed=True,scope='market'))
            source['adapter_context']['sectors'].append(dict(source_ref=alias,name=name,market_scope=scope,
                as_of_date='2026-09-21',state='CURRENT_DIRECTIONAL',return_pct=value))
            refs.append(alias)
    catalog=numeric_catalog(source,market='kr',assessment_date='2026-09-22',eligible_refs=refs)
    ranks=[c for c in catalog['claims'] if c['claim_type']=='SECTOR_RANKING']
    assert len(ranks)==4 and {r['metadata']['scope'] for r in ranks}=={'KOSPI','KOSDAQ'}
    for claim in ranks:
        assert all(claim['metadata']['scope'] in ref for ref in claim['input_fact_refs'])
    fact=source['fact_catalog'][0]
    assert kr_sector_alias(fact,source,'2026-09-21',refs)
    fact['fields']['return_pct']=99
    assert not kr_sector_alias(fact,source,'2026-09-21',refs)
    fact['fields']['return_pct']=1
    fact['fields']['taxonomy']='guessed'
    assert not kr_sector_alias(fact,source,'2026-09-21',refs)


@pytest.mark.parametrize('support,resistance',[(True,True),(False,True),(False,False)])
def test_stock_technical_sides_do_not_substitute_tactical_or_fundamental(support,resistance):
    packet,base=bound_plan()
    zone=dict(available=True,zone_low=10,zone_high=11,source='dynamic',timeframe='daily')
    quote=dict(contract='current-price-context-v1',availability='partial',as_of_date=packet.assessment_date,
        price_basis='close',currency='USD',active_support={**zone,'available':support},
        active_resistance={**zone,'available':resistance})
    receipt={**base.acceptance,'quote_context_sha256':digest(quote)}
    plan=base.model_copy(update=dict(quote_context=quote,acceptance=receipt,acceptance_sha256=digest(receipt)))
    before=deepcopy(plan.decision)
    text=calibration_render(packet,plan).text
    assert ('기술적 지지: 미확인' in text) == (not support)
    assert ('기술적 저항: 미확인' in text) == (not resistance)
    assert '가격 흐름 관찰 구간: 12,346 ~ 23,457 KRW' in text
    assert plan.decision==before
