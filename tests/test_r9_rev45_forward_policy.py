"""Provider/listing identity is scoped to atomic ratios, not global identity."""
from copy import deepcopy

import pytest

from app.services import provider_native_valuation_snapshot as native
from app.services.provider_valuation_calibration_context import calibration_context, validate_calibration_output
from app.services.security_identity_service import identity_source_tier
from app.services.unified_snapshot_contract import digest
from tests.rev28_native_fixtures import native_input, security
from tests.test_r9_rev28_native_snapshot import alter
from tests import test_r9_rev29_valuation_integration as rev29


def snapshots(sec, inputs):
    return (*native.derive_provider_snapshots(inputs, security=sec, run_id='fictional-snapshot'),
            native.derive_forward_snapshot(inputs, security=sec, run_id='fictional-snapshot'))


def no_official(sec):
    inputs = native_input(sec)
    inputs['identity_inputs'].pop('official_identity')
    inputs['identity_inputs'].pop('official_identity_sha256')
    return inputs


def test_provider_identity_does_not_grant_global_authoritative_identity():
    sec = security()
    sec.update(identity_provider='local', identity_quality='inferred')
    inputs = no_official(sec)
    assert identity_source_tier('local', 'inferred') != 'tier_a_authoritative'
    for row in snapshots(sec, inputs):
        assert row.display_eligible
        receipt = row.security_identity_receipt
        assert receipt['contract'] == 'finnhub-direct-us-provider-identity-v2'
        assert receipt['official_identity_role'] == 'OPTIONAL_SUPPORTING_EVIDENCE'
        assert receipt['official_identity_present'] is False
        assert set(receipt['allowed_fields']) == {'peTTM', 'pbQuarterly', 'forwardPE'}
    assert identity_source_tier('local', 'inferred') != 'tier_a_authoritative'


@pytest.mark.parametrize('canonical,reported', [
    ('NASDAQ', 'NASDAQ'), ('NASDAQ', 'NASDAQ GLOBAL SELECT MARKET'),
    ('NASDAQ', 'NASDAQ GLOBAL MARKET'), ('NASDAQ', 'NASDAQ CAPITAL MARKET'),
    ('NASDAQ', 'NASDAQ NMS - GLOBAL MARKET'), ('NYSE', 'NYSE'),
    ('NYSE', 'NEW YORK STOCK EXCHANGE'), ('NYSE', 'NEW YORK STOCK EXCHANGE, INC.'),
])
def test_us_listing_aliases(canonical, reported):
    sec = security()
    sec['exchange'] = canonical
    inputs = no_official(sec)
    alter(inputs['identity_inputs']['profile'], lambda b: b.update(exchange=reported))
    assert all(r.display_eligible for r in snapshots(sec, inputs))


@pytest.mark.parametrize('exchange', ['TORONTO STOCK EXCHANGE', 'NASDAQ COPENHAGEN', 'TWSE', 'KRX', 'OTHER', ''])
def test_foreign_or_unknown_exchange_is_never_normalized_to_us(exchange):
    sec = security()
    inputs = no_official(sec)
    alter(inputs['identity_inputs']['profile'], lambda b: b.update(exchange=exchange))
    assert not any(r.display_eligible for r in snapshots(sec, inputs))


@pytest.mark.parametrize('case', ['profile_symbol', 'metric_symbol', 'currency', 'preferred', 'country', 'generation'])
def test_identity_v2_negative_controls(case):
    sec = security()
    if case == 'preferred':
        sec['security_type'] = 'preferred_stock'
    if case == 'country':
        sec['country'] = 'CA'
    inputs = no_official(sec)
    profile = inputs['identity_inputs']['profile']
    if case == 'profile_symbol':
        alter(profile, lambda b: b.update(ticker='OTHER'))
    elif case == 'metric_symbol':
        alter(inputs, lambda b: b.update(symbol='OTHER'))
    elif case == 'currency':
        alter(profile, lambda b: b.update(currency='CAD'))
    elif case == 'generation':
        profile['receipt']['run_id'] = 'old-generation'
        with pytest.raises(ValueError, match='receipt_mismatch'):
            snapshots(sec, inputs)
        return
    assert not any(r.display_eligible for r in snapshots(sec, inputs))


def test_foreign_domicile_is_not_a_foreign_listing():
    sec = security()
    inputs = no_official(sec)
    alter(inputs['identity_inputs']['profile'], lambda b: b.update(country='CA'))
    assert all(r.display_eligible for r in snapshots(sec, inputs))


def test_user_policy_does_not_rewrite_official_provenance_or_eps():
    sec = security()
    row = snapshots(sec, no_official(sec))[-1]
    assert row.state == native.FORWARD_FY1_QUALIFIED
    assert row.canonical_horizon == 'FY1'
    assert row.provider_horizon is row.provider_definition is None
    assert row.horizon_policy['REV44_document_capture_FY1_definition'] == 'NOT_REPRODUCED'
    assert row.underlying_denominator_period is None
    assert not row.same_session_recomputation and not row.overall_direction_use
    for field, value in [('horizon_authority', 'OFFICIAL_FIELD_DEFINITION'),
                         ('provider_horizon', 'NEXT_FISCAL_YEAR'),
                         ('provider_definition', {'source': 'not captured'})]:
        payload = row.model_dump(mode='json')
        payload[field] = value
        payload['snapshot_sha256'] = digest({k: v for k, v in payload.items() if k != 'snapshot_sha256'})
        with pytest.raises(ValueError, match='product_policy_binding'):
            native.ProviderNativeForwardValuationSnapshot.model_validate(payload)


def test_unset_policy_cannot_infer_fy1(monkeypatch):
    monkeypatch.setattr(native, 'FINNHUB_FORWARD_FY1_PRODUCT_POLICY', None)
    row = snapshots(security(), native_input(security()))[-1]
    assert row.state == native.FORWARD_QUALIFIED
    assert row.canonical_horizon is row.horizon_authority is row.horizon_policy is None
    assert row.display_label == 'Finnhub Forward P/E'


def test_fper_wording_requires_the_forward_ratio_ref(tmp_path):
    context = calibration_context(rev29.valuation.__wrapped__(tmp_path)[0])
    forward = next(r for r in context['metric_states'] if r['metric'] == 'FORWARD_PE')
    per = next(r for r in context['metric_states'] if r['metric'] == 'PER')
    raw = dict(overall=dict(overall_reason='business evidence'),
        new_buyer_axis=dict(new_buyer_reason='fPER valuation context', new_buyer_valuation_refs=[forward['fact_ref']]),
        holder_axis=dict(holder_reason='business conditions', holder_valuation_refs=[]))
    assert validate_calibration_output(raw, context)['status'] == 'PASS'
    wrong = deepcopy(raw)
    wrong['new_buyer_axis']['new_buyer_valuation_refs'] = [per['fact_ref']]
    with pytest.raises(ValueError, match='requires_axis_ref'):
        validate_calibration_output(wrong, context)
