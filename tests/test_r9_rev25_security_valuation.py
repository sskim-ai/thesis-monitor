"""Offline authority negatives; synthetic numbers are not provider proof."""
from copy import deepcopy
import json

import pytest
from pydantic import ValidationError

from app.services.current_fresh_valuation import CurrentMultiple, CurrentValuationView
from app.services.security_valuation_basis import (
    SecurityValuationBasisReceipt, candidate_inventory, unresolved_basis,
)
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from tests.test_r9_rev9_valuation import valuation_inputs


def occurrence(**overrides):
    raw = dict(start='2025-01-01', end='2025-12-31', filed='2026-02-01',
               val=2, accn='a', fp='FY', form='10-K')
    raw.update(overrides)
    return dict(metric='diluted_eps', semantic='us-gaap:EarningsPerShareDiluted', unit='USD/shares',
        raw_sha256='a'*64, source_row_ordinal=0, source_occurrence=raw,
        security_basis='UNRESOLVED', split_basis='UNRESOLVED')


def test_inventory_precedes_selection_preserves_latest_unresolved_without_value_fallback():
    rows = [occurrence(), occurrence(val=-5, filed='2026-03-01', accn='b'),
            occurrence(start='2026-04-01', end='2026-06-30', filed='2026-08-01', fp='Q2', accn='c')]
    inventory = candidate_inventory(dict(candidate_occurrences=rows))
    assert len(inventory) == 3 and not any(r['selected'] for r in inventory)
    assert inventory[0]['revision_state'] == 'SUPERSEDED_OCCURRENCE'
    assert inventory[1]['revision_state'] == 'LATEST_REPORTED_OCCURRENCE'
    assert inventory[2]['period_type'] == 'DURATION_UNRESOLVED'
    assert inventory[2]['source_fiscal_period_label'] == 'Q2'
    changed = deepcopy(rows)
    for row in changed:
        row['source_occurrence']['val'] = 999999
    second = candidate_inventory(dict(candidate_occurrences=changed))
    assert [r['exclusion_reasons'] for r in inventory] == [r['exclusion_reasons'] for r in second]


@pytest.mark.parametrize('metric', ['common_equity', 'owners_parent_equity', 'common_shares_outstanding'])
def test_instant_and_dart_candidates_never_imply_class_attribution(metric):
    row = occurrence()
    row['metric'] = metric
    del row['source_occurrence']['start']
    dart = dict(row, source_row_ordinal=1, source_occurrence=dict(
        rcept_no='20260801000001', fs_div='CFS', sj_div='BS', currency='KRW',
        reprt_code='11012', account_detail='-', thstrm_amount='200'))
    inventory = candidate_inventory(dict(candidate_occurrences=[row, dart]))
    assert inventory[0]['period_type'] == 'INSTANT'
    assert inventory[1]['period_type'] == 'UNRESOLVED'
    assert inventory[1]['statement_basis'] == 'CFS'
    assert inventory[1]['publication_date'] is None
    assert all(r['security_class_dimensions'] == r['split_basis'] == 'UNRESOLVED' for r in inventory)


@pytest.mark.parametrize('adr', [False, True])
def test_basis_receipt_roundtrip_and_no_forged_qualification(adr):
    security = dict(ticker='X', canonical_security_id='security-X', exchange='NYSE',
                    share_class='Class A', security_type='ads' if adr else 'common_stock')
    price = dict(currency='USD', price_basis='adjusted_close', as_of_date='2026-09-29')
    receipt = unresolved_basis(ticker='X', run_id='offline', security=security, price=price, inventory=[])
    value = receipt.model_dump(mode='json')
    assert SecurityValuationBasisReceipt.model_validate(value) == receipt
    value['security_class'] = 'Class B'
    with pytest.raises(ValueError, match='receipt_mismatch'):
        SecurityValuationBasisReceipt.model_validate(value)
    value['status'] = 'QUALIFIED'
    value['basis_sha256'] = digest({k: v for k, v in value.items() if k != 'basis_sha256'})
    with pytest.raises(ValidationError):
        SecurityValuationBasisReceipt.model_validate(value)


@pytest.mark.parametrize('negative', [False, True])
@pytest.mark.parametrize('invented_split', [False, True])
def test_native_wire_cannot_self_declare_missing_split_owner(tmp_path, negative, invented_split):
    inputs = valuation_inputs(tmp_path, negative=negative)
    inputs['financial_inputs']['plan']['security']['share_class'] = 'Class A'
    native = inputs['valuation_inputs']
    native['receipt']['security_sha256'] = digest(inputs['financial_inputs']['plan']['security'])
    payload = json.loads(native['raw'])
    payload['shareClass'] = 'Class A'
    if invented_split:
        payload['splitBasis'] = 'compatible'
    native['raw'] = encoded(payload)
    native['receipt']['source_sha256'] = sha256_bytes(native['raw'])
    # Exercise the adapter directly: no mutated acquisition plan is signed.
    from app.services.current_fresh_valuation import _native_metrics
    metrics = tuple(CurrentMultiple(metric=m, status='UNAVAILABLE', numerator=20,
        source_method='test', input_hashes=('a'*64,), denial_reason='NOT_OWNED') for m in ('PER', 'PBR', 'fPER'))
    session = payload['metricAsOf']
    rows = _native_metrics(metrics, native, ticker='IBM', run_id=native['receipt']['run_id'],
        price=dict(as_of_date=session, currency='USD', current_price=20),
        security=inputs['financial_inputs']['plan']['security'])
    assert [m.ownership_state for m in rows] == [
        'UNAVAILABLE_SECURITY_BASIS', 'UNAVAILABLE_SECURITY_BASIS', 'UNAVAILABLE_ESTIMATE_HORIZON']
    assert all(m.value is None and m.denominator is None and not m.display_eligible for m in rows)


def test_metric_independent_state_and_no_overall_grant():
    base = dict(numerator=20, source_method='contract-unit-fixture', input_hashes=('a'*64,))
    qualified = CurrentMultiple(metric='PER', status='QUALIFIED', value=10, denominator=2,
        denominator_period='TTM', publication_date='2026-09-29', latest_published=True,
        display_eligible=True, denial_reason=None, **base)
    forward = CurrentMultiple(metric='fPER', status='UNAVAILABLE', denial_reason='NO_ESTIMATE', **base)
    assert qualified.ownership_state == 'QUALIFIED' and forward.ownership_state == 'UNAVAILABLE_ESTIMATE_HORIZON'
    with pytest.raises(ValueError, match='ownership_state_mismatch'):
        CurrentMultiple(**{**forward.model_dump(), 'ownership_state': 'QUALIFIED'})
    with pytest.raises(ValidationError):
        CurrentMultiple(**{**qualified.model_dump(), 'overall_direction_use': True})


def test_integrated_receipt_pure_replay_and_registry(tmp_path):
    inputs = valuation_inputs(tmp_path)
    a = prepare_fresh_subject(inputs, execution_generation_id='offline-valuation')
    b = prepare_fresh_subject(inputs, execution_generation_id='offline-valuation')
    assert a == b
    view = CurrentValuationView.model_validate(a['stock']['valuation_view'])
    assert view.security_basis_receipt.status == 'UNAVAILABLE_SECURITY_BASIS'
    changed = view.model_dump(mode='json')
    changed['denominator_candidate_inventory'] = [dict(fabricated=True)]
    with pytest.raises(ValueError, match='basis_binding_mismatch'):
        CurrentValuationView.model_validate(changed)
    changed = view.model_dump(mode='json')
    changed['metrics'][0].update(status='QUALIFIED', ownership_state='QUALIFIED', value=10,
        denominator=2, denominator_period='TTM', publication_date='2026-09-29', latest_published=True,
        source_method='fabricated', denial_reason=None, display_eligible=True)
    with pytest.raises(ValueError, match='unresolved_basis_cannot_display_number'):
        CurrentValuationView.model_validate(changed)
    from app.services.whole_source_code_owner_registry import WholeSourceCodeOwnerRegistry
    from pathlib import Path
    registry = WholeSourceCodeOwnerRegistry.freeze(Path(__file__).resolve().parents[1])
    assert 'app/services/security_valuation_basis.py' in registry.fingerprints
    assert registry.verify(Path(__file__).resolve().parents[1], fingerprints=registry.fingerprints,
                           expected_sha256=registry.sha256) == registry
