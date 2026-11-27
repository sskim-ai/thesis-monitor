from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal

import pytest

from app.services.preopen_applicability import assess_stock, compare_price


CUTOFF = datetime.fromisoformat('2026-11-30T08:55:00-05:00')
OPENING = date(2026, 11, 30)


@pytest.fixture
def row():
    return dict(status='COMPLETE', overall='BUY', economic='ATTRACTIVE', entry_quality='SUPPORTED',
                action_class='REVIEW_NOW', preopen=dict(
                    market='us', security_id='us:security', currency='USD',
                    price_basis='unadjusted_close', price_precision=.01, close=100,
                    technical_state='SUPPORTIVE', active_material_risk=False,
                    support=dict(candidate_id='selected', low=95, high=105),
                    current_scenario=dict(target=120, target_basis={'timeframe': 'daily'},
                                          stop=90, stop_ref='canonical:selected', status='intact',
                                          rr=2, applicable_from=100),
                    support_scenario=dict(target=120, target_basis='SAME_AS_CURRENT',
                                          intersection='DISPLAYABLE', rr2_low=95, rr2_high=100),
                    economics=dict(candidate_id='selected-economic', origin='OWN', side='LOW',
                                   price=100, status='CONDITIONAL', price_basis='unadjusted_close'),
                ))


@pytest.fixture
def quote():
    return dict(market='us', security_id='us:security', currency='USD',
                adjustment_basis='unadjusted', share_basis_comparable=True,
                value=100, observation_timestamp='2026-11-30T08:53:00-05:00',
                market_session='pre_market', latency_seconds=30, max_age_seconds=180,
                source='test provider')


def compare(row, quote):
    return compare_price(row, opening_session=OPENING, cutoff=CUTOFF, quote=quote)


def assess(row, quote=None, **options):
    return assess_stock(row, opening_session=OPENING, cutoff=CUTOFF, quote=quote, **options)


def test_confirm_existing_conditions_without_changing_the_accepted_row(row, quote):
    original = deepcopy(row)
    result = assess(row, quote, coverage='CHECKED')
    assert result.review == 'CONFIRMED'
    assert result.price.scenario == 'CURRENT'
    assert result.price.reference_rr == Decimal('2')
    assert result.price.close_change_pct == 0
    assert result.price.in_rr2
    assert result.price.preference_relation == 'AT_OR_BELOW'
    assert result.price.preference_conditional
    assert row == original


@pytest.mark.parametrize(('field', 'value', 'status'), [
    ('observation_timestamp', None, 'OBSERVATION_UNVERIFIED'),
    ('observation_timestamp', '2026-11-30T08:54:00', 'OBSERVATION_UNVERIFIED'),
    ('observation_timestamp', '2026-11-30T08:56:00-05:00', 'OBSERVATION_UNVERIFIED'),
    ('observation_timestamp', '2026-11-27T18:00:00-05:00', 'OBSERVATION_UNVERIFIED'),
    ('observation_timestamp', '2026-11-30T08:51:59-05:00', 'OBSERVATION_UNVERIFIED'),
    ('market_session', 'regular_close', 'OBSERVATION_UNVERIFIED'),
    ('source', '', 'OBSERVATION_UNVERIFIED'),
    ('latency_seconds', 181, 'OBSERVATION_UNVERIFIED'),
    ('latency_seconds', None, 'OBSERVATION_UNVERIFIED'),
    ('adjustment_basis', 'adjusted', 'BASIS_UNVERIFIED'),
    ('share_basis_comparable', False, 'BASIS_UNVERIFIED'),
    ('security_id', 'us:other-security', 'BASIS_UNVERIFIED'),
    ('currency', 'KRW', 'BASIS_UNVERIFIED'),
])
def test_preopen_price_requires_eligible_provider_observation(row, quote, field, value, status):
    quote[field] = value
    quote['retrieved_at'] = '2026-11-30T08:54:00-05:00'
    checked = compare(row, quote)
    assert not checked.confirmed
    assert checked.status == status


def test_lower_quote_uses_separate_band_target_and_never_assumes_old_far_target(row, quote):
    band = row['preopen']['support_scenario']
    band.update(target=114, target_basis={'timeframe': 'weekly'}, rr2_high=98)
    quote['value'] = 98
    row.update(action_class='WAIT', entry_quality='CAUTION')
    row['preopen']['entry_reason'] = 'CURRENT_PRICE_RISK_REWARD_CONDITIONAL'
    result = assess(row, quote, coverage='CHECKED')
    assert result.review == 'CONFIRMED_CONDITIONAL'
    assert result.price.scenario == 'SUPPORT'
    assert result.price.reference_rr == 2
    assert result.price.close_change_pct == -2

    band['assumption'] = 'HYPOTHETICAL_REAPPROACH'
    assert compare(row, quote).reference_rr is None
    quote['value'] = 94
    band['assumption'] = None
    assert compare(row, quote).reference_rr is None


def test_unresolved_current_barrier_and_unauthorized_targets_do_not_supply_rr(row, quote):
    row['preopen']['support_scenario']['target'] = None
    row['preopen']['current_scenario']['possible_barrier'] = 110
    assert compare(row, quote).status == 'RR_UNVERIFIED'
    row['preopen']['current_scenario'].update(possible_barrier=None, target_basis=None)
    assert compare(row, quote).reference_rr is None


@pytest.mark.parametrize(('value', 'status'), [(90, 'STOP_REACHED'), (120, 'TARGET_REACHED')])
def test_reaching_original_stop_or_target_preserves_structure_and_suppresses_rr(
        row, quote, value, status):
    quote['value'] = value
    result = assess(row, quote, coverage='CHECKED')
    assert result.price.status == status
    assert result.review == 'NOT_APPLICABLE'
    assert result.price.reference_rr is None
    assert row['economic'] == 'ATTRACTIVE'


def test_reference_rr_does_not_round_its_way_into_an_eligible_entry(row, quote):
    quote['value'] = '100.001'
    price = compare(row, quote)
    assert price.rr_label == '2배 미만'
    assert not price.rr_at_least_two
    assert not price.in_rr2


def test_preferred_boundary_only_describes_price_relation(row, quote):
    quote['value'] = 99
    row['preopen']['economics']['price'] = '98.999'
    checked = assess(row, quote, coverage='CHECKED')
    assert checked.price.preference_relation == 'ABOVE'
    assert checked.price.rr_at_least_two
    assert checked.review == 'UNCONFIRMED'
    assert row['economic'] == 'ATTRACTIVE'
    row['preopen']['economics']['price_basis'] = None
    assert compare(row, quote).preference_relation == 'UNCONFIRMED'


@pytest.mark.parametrize(('section', 'field', 'value'), [
    ('row', 'overall', 'SELL'), ('row', 'economic', 'AVOID'),
    ('row', 'entry_quality', 'BLOCKED'), ('base', 'active_material_risk', True),
    ('base', 'technical_state', 'ADVERSE'),
])
def test_favorable_quote_does_not_waive_frozen_risk(row, quote, section, field, value):
    (row if section == 'row' else row['preopen'])[field] = value
    assert assess(row, quote, coverage='CHECKED').review == 'NOT_APPLICABLE'


def test_known_official_change_differs_from_title_date_ambiguity_and_failed_coverage(row, quote):
    event = dict(official=True, material=True, incremental='CONFIRMED',
                 published_at='2026-11-30T08:20:00-05:00')
    result = assess(row, quote, coverage='CHECKED', events=[event])
    assert '재평가' in result.action
    assert result.review == 'UNCONFIRMED'

    for uncertain in (dict(event, official=False), dict(event, timestamp_uncertain=True),
                      dict(event, incremental='UNCONFIRMED'),
                      dict(event, published_at='2026-11-30')):
        result = assess(row, quote, coverage='CHECKED', events=[uncertain])
        assert '내용·시점 확인' in result.state
        assert '재평가' not in result.action
        assert result.review == 'UNCONFIRMED'

    assert '변경 범위 미확인' in assess(row, quote).state
    assert assess(row, quote).review == 'UNCONFIRMED'


def test_prior_limit_legacy_and_missing_prices_are_not_counted(row, quote):
    assert '장전 가격 미확보' in assess(row, coverage='CHECKED').state
    assert assess(row).review == 'UNCONFIRMED'
    assert not assess(row, quote, prior_reference=True).price.confirmed
    limited = dict(row, status='UNKNOWN_LIMIT')
    assert not assess(limited, quote).price.confirmed
    legacy = {k: v for k, v in row.items() if k != 'preopen'}
    assert not assess(legacy, quote).price.confirmed
