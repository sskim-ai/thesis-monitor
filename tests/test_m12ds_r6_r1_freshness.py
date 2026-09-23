from datetime import datetime
from copy import deepcopy
from zoneinfo import ZoneInfo

from app.macro.publication import publication_receipt, publication_freshness
from app.services.market_numeric_claim_service import numeric_catalog
from tests.test_m12ds_r6_information_coverage import html


KST = ZoneInfo('Asia/Seoul')


def test_expected_lag_is_visible_not_current_direction_and_expired_is_stale():
    at = datetime(2026, 9, 23, 8, tzinfo=KST)
    receipt = publication_receipt(html(), 'DCOILWTICO', at)
    result = publication_freshness(receipt, 'DCOILWTICO', '2026-09-15',
        completed='2026-09-22', assessed='2026-09-23')
    assert result['state'] == 'LATEST_PUBLISHED_WITH_LAG'
    assert result['factual_display_eligible'] and not result['current_direction_eligible']
    future = {**receipt, 'assessed_at': '2026-09-24T08:00:00+09:00'}
    assert publication_freshness(future, 'DCOILWTICO', '2026-09-15',
        completed='2026-09-23', assessed='2026-09-24')['state'] == 'STALE_UNEXPECTED'


def test_weekend_holiday_calendar_owns_release_not_host_age():
    at = datetime(2026, 9, 8, 8, tzinfo=KST)
    receipt = publication_receipt(html('2026-09-04', 'Sep 4, 2026 3:16 PM CDT', 'Sep 8, 2026'), 'DGS10', at)
    result = publication_freshness(receipt, 'DGS10', '2026-09-04',
        completed='2026-09-04', assessed='2026-09-08')
    assert result['state'] == 'CURRENT_BY_PROVIDER_CALENDAR'
    assert publication_freshness(None, 'DGS10', '2026-09-04',
        completed='2026-09-04', assessed='2026-09-08')['state'] == 'STALE_UNEXPECTED'


def test_other_series_do_not_inherit_h15_release_clock():
    at = datetime(2026, 9, 23, 14, tzinfo=KST)
    for series in ('DFII10', 'T10YIE', 'BAMLH0A0HYM2', 'VIXCLS'):
        receipt = publication_receipt(html('2026-09-22', 'Sep 22, 2026 3:16 PM CDT', 'Sep 23, 2026'), series, at)
        assert receipt['next_publication_due'].endswith('T00:00:00-04:00')
        assert publication_freshness(receipt, series, '2026-09-22',
            completed='2026-09-22', assessed='2026-09-23')['state'] == 'STALE_UNEXPECTED'


def test_numeric_label_and_stale_suppression_without_reclassifying_daily_signal():
    at = datetime(2026, 9, 23, 8, tzinfo=KST)
    receipt = publication_receipt(html(), 'DCOILWTICO', at)
    fact = dict(fact_id='oil', fact_type='market_oil', as_of_date='2026-09-15', fields=dict(
        provider='fred', series_code='DCOILWTICO', label='WTI', quality='fresh',
        price_usd_per_barrel=70, today_signal_eligible=False, publication_receipt=receipt))
    source = dict(session=dict(market='us', assessment_date='2026-09-23',latest_completed_regular_session_date='2026-09-22'),
        fact_catalog=[fact], numeric_registry=[dict(fact_id='oil', field_path='fields.price_usd_per_barrel',
            value=70, unit='USD_per_barrel', scope='market', registered=True, prose_allowed=True)])
    before = deepcopy(source)
    catalog = numeric_catalog(source, market='us',assessment_date='2026-09-23',eligible_refs=['oil'])
    claim = catalog['claims'][1]
    assert '최신 공표값(관측 지연)' in claim['rendered_text'] and '현재 방향 판단 제외' in claim['rendered_text']
    assert not claim['metadata']['publication_freshness']['current_direction_eligible']
    assert source == before
    fact['fields']['publication_receipt'] = None
    fact['fields'].update(today_signal_eligible=True, temporal_role='CURRENT_OBSERVATION')
    catalog = numeric_catalog(source, market='us',assessment_date='2026-09-23',eligible_refs=['oil'])
    assert len(catalog['claims']) == 1


def test_lagged_refs_cannot_own_direction_in_schema_or_validator():
    from scripts import m12ds_r6_market as market
    from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema
    facts = {'oil': {'publication_freshness': {'current_direction_eligible': False}}}
    context = dict(market='US', facts=facts, packet_eligible_refs=['oil'], request_eligible_refs=['oil'])
    row = dict(market='US', regime='DATA_INSUFFICIENT', confidence='LOW', breadth_state='자료 없음',
        leadership='자료 없음', flows_or_participation='자료 없음', rates_or_macro_context='지연 공표값은 판단에서 제외',
        supporting_refs=['oil'], contradicting_refs=[])
    assert validate_json_schema(row, market.market_schema(context))
    assert 'lagged_publication_used_for_current_direction' in market.validate_market(row, context)['errors']
    row['supporting_refs'] = []
    assert not validate_json_schema(row, market.market_schema(context))
    assert market.validate_market(row, context)['status'] == 'PASS'
