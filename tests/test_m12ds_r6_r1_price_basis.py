from copy import deepcopy

import pytest

from app.services.current_price_basis_service import (
    legacy_price_basis, price_basis_context, price_basis_label, validate_quote_context,
)
from app.services.accepted_calibration_message_service import calibration_render, digest
from tests.test_m12ds_r4_r4_presentation import bound_plan


def quote(basis='adjusted_intraday'):
    return dict(contract='current-price-context-v1', availability='ready',
        as_of_date='2026-09-23', price_basis=basis,
        price_basis_context=price_basis_context(basis), currency='KRW',
        active_support=dict(available=True, zone_low=100, zone_high=101, source='dynamic', timeframe='daily'),
        active_resistance=dict(available=False))


@pytest.mark.parametrize('legacy,phase,adjustment,label', [
    ('intraday', 'INTRADAY', 'RAW', '장중 관측'),
    ('adjusted_intraday', 'INTRADAY', 'ADJUSTED', '조정가격 기준 장중 관측'),
    ('close', 'CLOSE', 'RAW', '종가'),
    ('adjusted_close', 'CLOSE', 'ADJUSTED', '조정 종가'),
])
def test_basis_shared_producer_validation_renderer(legacy, phase, adjustment, label):
    q = quote(legacy)
    basis = validate_quote_context(q, '2026-09-23')
    assert (basis['phase'], basis['adjustment']) == (phase, adjustment)
    assert legacy_price_basis(intraday=phase=='INTRADAY', adjusted=adjustment=='ADJUSTED') == legacy
    assert price_basis_label(basis) == label
    packet, plan = bound_plan()
    q['as_of_date'] = packet.assessment_date
    receipt = {**plan.acceptance, 'quote_context_sha256': digest(q)}
    plan = plan.model_copy(update=dict(quote_context=q, acceptance=receipt, acceptance_sha256=digest(receipt)))
    before = deepcopy(plan.decision)
    rendered = calibration_render(packet, plan).text
    assert label in rendered and '기술적 지지: 100 ~ 101 KRW' in rendered
    assert before == plan.decision


@pytest.mark.parametrize('key,value,error', [
    ('price_basis', 'guessed', 'accepted_quote_basis_invalid'),
    ('price_basis', ['intraday'], 'accepted_quote_basis_invalid'),
    ('as_of_date', '2026-09-22', 'accepted_quote_asof_invalid'),
    ('as_of_date', '2026-09-24', 'accepted_quote_asof_invalid'),
    ('availability', 'unavailable', 'accepted_quote_availability_invalid'),
    ('contract', 'unknown', 'accepted_quote_contract_invalid'),
    ('price_basis_context', {}, 'accepted_quote_basis_binding_invalid'),
])
def test_independent_typed_denials(key, value, error):
    q = quote()
    q[key] = value
    with pytest.raises(ValueError, match=error):
        validate_quote_context(q, '2026-09-23')


def test_stale_close_independent_of_valid_basis():
    q = quote('close')
    q.update(as_of_date='2026-09-21', latest_completed_regular_session_date='2026-09-22')
    with pytest.raises(ValueError, match='accepted_quote_asof_invalid'):
        validate_quote_context(q, '2026-09-23')
