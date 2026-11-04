"""Exact REV6 public controls plus explicit current synthetic scope negatives.

No original 000660 fact or DART discovery capture is present in this allowlist.
These tests neither reconstruct those inputs nor claim a historical owner replay
or current real-source grant. Main alone runs the final focused selection.
"""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path

import pytest

from app.services.issuer_business_bridge import bind_comparison, evidence_scope, identity_bridge
from app.services.unified_snapshot_contract import digest


PUBLIC_ROOT = Path(
    '/Users/sskim/Documents/Codex/Reports/'
    '20261019-post-r22-ng16-historical-reintegration/skhy-history'
)
PUBLIC_PINS = {
    'rev6-summary.json': (1331, 'b82d93d7e1bb4f42d7c9e88396e5b96dcb3e2a22bcae698219e80bc369c7e3ce'),
    'rev6-qualified-sec-identity.json': (6163, '58d3c8acd47c20f3aa5852f53599dfd4f09395eb51d1ed257e4565dd3d006221'),
    'rev6-authority-freeze.json': (501, 'fdc3e18bbf9df2323883b3f7a16f7acb4baf49db1941fb11f110d9f3a83c7db3'),
    'rev6-issuer-identity-bridge.json': (1327, '6aefc099dbaa326d7853e5302a5562ce1d6cf270bcbf815a28944344f5eba61d'),
    'rev6-bridged-business-evidence.json': (7150, 'f653be09b82e92c708fcce8a8daca3479c8f6202910129e2653f9b74ce78c05f'),
    'rev6-original-source-field-matrix.json': (17146, '7b50159f70e175eb11da49d32baf4ba39663aed64e9ae698b4a15a03ed10a74b'),
    'rev6-security-isolation.json': (393, 'd1d19a87ee9645258956a942d1077e706694e244bbf144dcc290847b1af4f61f'),
    'rev6-offline-receipt.json': (147, '7d9e5e9be58b067423e881b5a29b88252ead30714ea3dcbe5b21396d82710cb7'),
}


def _read_public(name):
    size, expected_sha = PUBLIC_PINS[name]
    path = PUBLIC_ROOT / name
    assert not path.is_symlink()
    raw = path.read_bytes()
    assert len(raw) == size
    assert sha256(raw).hexdigest() == expected_sha
    return json.loads(raw)


@pytest.fixture
def archive():
    return {name: _read_public(name) for name in PUBLIC_PINS}


def test_exact_public_controls_bind_historical_identity_and_revenue(archive):
    official = archive['rev6-qualified-sec-identity.json']
    freeze = archive['rev6-authority-freeze.json']
    bridge = archive['rev6-issuer-identity-bridge.json']
    facts = archive['rev6-bridged-business-evidence.json']
    matrix = archive['rev6-original-source-field-matrix.json']
    assert digest(official) == freeze['qualified_identity_sha256'] == bridge['official_identity_sha256']
    assert digest({k: v for k, v in bridge.items() if k != 'receipt_sha256'}) == bridge['receipt_sha256']
    assert bridge['cutoff'] == '2026-09-27T09:33:34.100483+09:00'
    assert len(facts) == 1
    fact = facts[0]
    assert fact['issuer_projection'] == bridge
    assert fact['issuer_business_bridge']['bridge_receipt_sha256'] == bridge['receipt_sha256']
    assert fact['field_dependency_receipts'] == matrix['comparisons'][0]
    assert fact['fields']['source_ticker'] == '000660'
    assert fact['fields']['issuer_id'] == 'DART:00164779'
    assert fact['fields']['currency'] == 'KRW'
    assert (fact['fields']['period_start'], fact['fields']['period_end']) == ('2026-04-01', '2026-06-30')
    assert (fact['fields']['prior_period_start'], fact['fields']['prior_period_end']) == ('2025-04-01', '2025-06-30')
    assert fact['fields']['metric'] == 'revenue'
    assert {r['field']: r['reason'] for r in matrix['denials']} == {
        'operating_income': 'PERIOD_NOT_COMPARABLE', 'net_income': 'PERIOD_NOT_COMPARABLE',
    }
    summary = archive['rev6-summary.json']
    assert summary['complete'] == 22 and summary['controls_invariant'] == 21
    assert summary['NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED'] is False
    assert archive['rev6-offline-receipt.json']['model_calls'] == 0
    isolation = archive['rev6-security-isolation.json']
    assert isolation['source_price_technical_per_share_valuation_transfers'] == 0
    assert isolation['target_stock_before_sha256'] == isolation['stripped_after_sha256']
    assert not bridge['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE']
    assert not bridge['SECURITY_VALUATION_BRIDGE_ELIGIBLE']


def test_original_scope_keeps_archived_absolute_rows_and_denials(archive):
    rows = archive['rev6-original-source-field-matrix.json']['fields']
    for row in rows:
        scope = evidence_scope(
            metric=row['metric'], subject_scope='legal_issuer',
            context_eligible=row['context_eligible'], direction_eligible=row['direction_eligible'],
            denied=row['source_use'] == 'DENIED',
        )
        assert scope['context_eligible'] is row['context_eligible']
        assert scope['direction_eligible'] is False
        assert scope['security_per_share_eligible'] is False
        assert scope['security_valuation_eligible'] is False
    assert any(r['metric'] == 'revenue' and r['context_eligible'] for r in rows)


def test_public_identity_without_original_dart_capture_cannot_reissue_bridge(archive):
    official = archive['rev6-qualified-sec-identity.json']
    bridge = archive['rev6-issuer-identity-bridge.json']
    # A negative probe only: these metadata views are not original source inputs.
    target = {k: official['evidence'][k] for k in ('ticker', 'cik', 'security_type', 'issuer_type', 'exchange')}
    target.update(canonical_security_id=bridge['monitored_security_id'],
                  canonical_company_id=bridge['target_company_id'])
    source = dict(ticker=bridge['underlying_ticker'], corp_code=bridge['provider_issuer_ids']['opendart'],
                  canonical_security_id=bridge['source_security_id'], canonical_company_id=bridge['source_company_id'],
                  security_type='common_stock', exchange='KRX')
    result = identity_bridge(target=target, source=source, official=official,
        expected_official_sha256=bridge['official_identity_sha256'],
        dart_rows=[], dart_receipt={}, cutoff=bridge['cutoff'])
    assert result['status'] == 'FAIL'
    assert 'official_dart_security_issuer_mapping_unverified' in result['errors']
    assert result['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE'] is False


def test_added_fact_and_hash_cannot_replace_missing_original_fact(archive):
    added = archive['rev6-bridged-business-evidence.json'][0]
    bridge = archive['rev6-issuer-identity-bridge.json']
    with pytest.raises(ValueError, match='^issuer_business_original_fact_mismatch$'):
        bind_comparison(added, {}, bridge,
                        source_result_sha256=added['issuer_business_bridge']['source_result_sha256'])


@pytest.mark.parametrize('field,value', [
    ('issuer_id', 'DART:00999999'),
    ('cutoff', '2026-10-19T00:00:00+00:00'),
    ('SECURITY_PER_SHARE_BRIDGE_ELIGIBLE', True),
    ('SECURITY_VALUATION_BRIDGE_ELIGIBLE', True),
])
def test_original_binding_rejects_changed_archived_receipt(archive, field, value):
    bridge = deepcopy(archive['rev6-issuer-identity-bridge.json'])
    bridge[field] = value
    with pytest.raises(ValueError, match='^issuer_bridge_receipt_missing_or_tampered$'):
        bind_comparison({}, {}, bridge, source_result_sha256='')


@pytest.mark.parametrize('metric', ['price', 'eps', 'pe', 'pb', 'adr_ratio'])
def test_original_scope_refuses_security_transfer_even_with_issuer_permissions(metric):
    result = evidence_scope(metric=metric, subject_scope='legal_issuer',
                            context_eligible=True, direction_eligible=True)
    assert not any(result.values())


def test_archived_bridge_cannot_issue_current_context_without_original_inputs(archive):
    from app.services.reported_business_projection import _BUILDER_PERMIT, issue

    with pytest.raises(ValueError, match='^business_issuer_original_inputs_required$'):
        issue(stock={}, packet={}, facts=archive['rev6-bridged-business-evidence.json'],
              plan={'ticker': 'SKHY', 'issuer': '0002120882'}, acquisition={}, projection={},
              selected_owner={}, quality={}, bridge=archive['rev6-issuer-identity-bridge.json'],
              financial_inputs=None, _permit=_BUILDER_PERMIT)


def test_current_consumer_synthetic_context_ceiling_and_scope_broadening_denial(tmp_path):
    from app.services.canonical_source_inputs import fresh_authority_inputs
    from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
    from app.services.direction_timing_ownership_service import build_owned_evidence_packet
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from scripts.m12dr_financial_source_authority import build_source_authority
    from tests.rev9_source_fixtures import bridge_inputs
    from tests.rev10_source_fixtures import wire_clock
    from tests.test_reported_business_native_projection import window
    from tests.test_unified_stock_acquisition import plan as plan_fixture

    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        inputs, _ = bridge_inputs(tmp_path)
    inputs.update(reported_comparison_business=True, source_window=window(plan))
    result = assemble_fresh_stock(**inputs)
    stock = result['packet']['stocks'][0]
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    build_owned_evidence_packet(evidence, stock=stock)
    authority = build_source_authority(**fresh_authority_inputs(result, inputs))
    records = {r['ref_id']: r for r in authority['authority']['authority_records']}
    contexts = [r for r in evidence.evidence if r.reported_business]
    assert contexts and {r.reported_business.kind for r in contexts} == {'ISSUER_CONTEXT', 'QUALITY'}
    for row in contexts:
        assert row.reported_business.allowed_uses == ('CONTEXT',)
        assert row.reported_business.security_valuation_transfer is False
        assert row.source_use.core_current_fact is False
        assert records[row.ref_id]['allowed_uses'] == ['CONTEXT']
        assert 'OVERALL_DIRECTION' in records[row.ref_id]['prohibited_uses']
    assert stock['current_valuation_denial'] == 'ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY'
    ref = next(r for r in contexts if r.reported_business.kind == 'ISSUER_CONTEXT')
    altered = ref.model_copy(update={'reported_business': ref.reported_business.model_copy(
        update={'allowed_uses': ('CONTEXT', 'OVERALL_DIRECTION')})})
    changed = evidence.model_copy(update={'evidence': tuple(
        altered if r.ref_id == ref.ref_id else r for r in evidence.evidence)})
    with pytest.raises(ValueError):
        build_owned_evidence_packet(changed, stock=stock)
