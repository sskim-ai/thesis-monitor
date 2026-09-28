from datetime import timedelta

import pytest

from app.services.fresh_valuation_capability import denominator_scope
from app.services.unified_run_artifacts import durable_bytes, sha256_bytes
from app.services.unified_snapshot_contract import encoded
from app.services.unified_snapshot_contract import digest
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_unified_stock_acquisition import plan as plan_fixture


@pytest.mark.parametrize('ticker', ['CORZ', 'TSM', '005930', '047810'])
def test_exact_denominator_unavailability_preserves_business_and_price(tmp_path, ticker):
    with wire_clock(plan_fixture.__wrapped__().frozen_at + timedelta(seconds=4)):
        inputs = fresh_inputs(tmp_path, ticker, verified_identity=True)
    result = prepare_fresh_subject(inputs, execution_generation_id='valuation-synthetic')
    view = result['stock']['valuation_view']
    receipt = view['denominator_scope_receipt']
    assert receipt['receipt_sha256'] == digest({k: v for k, v in receipt.items() if k != 'receipt_sha256'})
    assert receipt['source_field_hashes'] and receipt['projected_metrics']
    assert all(m['status'] == 'UNAVAILABLE' and not m['owned_denominator_refs'] for m in receipt['metrics'].values())
    assert receipt['historical']['interchangeable'] is False
    assert receipt['registry']['opendart']['basic_eps'] == ['ifrs-full_basicearningslosspershare']
    assert view['price'] > 0 and all(m['numerator'] == view['price'] for m in view['metrics'])
    assert not receipt['overall_direction_use'] and not receipt['source_authority_expanded']
    assert result['readiness']['status'] == 'PASS'


def test_new_denominator_field_cannot_gain_authority_without_exact_owner():
    with pytest.raises(ValueError, match='scope_changed'):
        denominator_scope({'fields': [{'contract': 'bounded-official-financial-projection-v1',
            'metric': 'diluted_eps', 'value': 2}]}, security={'ticker': 'SYNTHETIC'})


@pytest.mark.parametrize('provider,exact', [('sec_edgar', True), ('opendart', True), ('opendart', False)])
def test_raw_exact_denominator_does_not_infer_security_share_basis(tmp_path, provider, exact):
    security = {'ticker': 'SYNTHETIC', 'canonical_security_id': 'synthetic-share'}
    if provider == 'sec_edgar':
        stage, issuer = 'companyfacts', '0000001234'
        body = {'cik': 1234, 'facts': {'us-gaap': {'EarningsPerShareDiluted': {'units': {
            'USD/shares': [{'val': 2, 'accn': '0000001234-26-000001', 'filed': '2026-08-01',
                            'start': '2026-04-01', 'end': '2026-06-30'}]}}}}}
    else:
        stage, issuer = 'statement', '00123456'
        body = {'list': [{'corp_code': issuer, 'account_id': 'ifrs-full_BasicEarningsLossPerShare' if exact else 'issuer_custom_eps',
            'account_nm': '기본주당이익', 'currency': 'KRW', 'fs_div': 'CFS', 'sj_div': 'CIS',
            'thstrm_amount': '2000', 'rcept_no': '20260801000001'}]}
    raw = encoded(body)
    durable_bytes(tmp_path / 'source.body', raw, exclusive=True)
    inputs = dict(plan=dict(security=security, provider=provider, issuer=issuer), directory=tmp_path,
                  receipts=[dict(stage=stage, artifact='source.body', raw_sha256=sha256_bytes(raw))])
    receipt = denominator_scope({'fields': []}, security=security, source_inputs=inputs)
    scope = receipt['raw_source_projection']
    assert len(scope['candidate_occurrences']) == int(exact)
    assert scope['status'] == 'UNAVAILABLE'
    assert scope['source_authority_expanded'] is False
    assert all(r['security_basis'] == r['split_basis'] == 'UNRESOLVED' for r in scope['candidate_occurrences'])
    assert scope['sources'][0]['raw_sha256'] == sha256_bytes(raw)
