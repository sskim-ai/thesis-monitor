from copy import deepcopy

import pytest

from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from scripts.r2b_r9_full_fresh_requalification import load_stock_inputs, prepare_fresh_subject
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev9_source_fixtures import bridge_inputs, write_descriptor
from tests.test_r9_rev9_valuation import valuation_inputs


@pytest.mark.parametrize('ticker,options', [
    ('CORZ', {}), ('TSM', {}), ('005930', {}), ('003690', {'insurance': True}),
    ('IBM', {'conflict': True}), ('CORZ', {'current_only': True}),
])
def test_archetype_data_descriptor_same_fresh_controller(tmp_path, ticker, options):
    inputs = fresh_inputs(tmp_path / 'raw', ticker, **options)
    descriptor = write_descriptor(tmp_path, inputs)
    loaded = load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])
    first = prepare_fresh_subject(inputs, execution_generation_id='synthetic-rev9')
    second = prepare_fresh_subject(loaded, execution_generation_id='synthetic-rev9')
    assert first == second
    assert first['stock']['status'] == first['readiness']['status'] == 'PASS'
    assert all(first['readiness'][s] == 'PASS' for s in ('Core', 'A', 'B'))
    if options.get('insurance'):
        fields = first['stock']['projection']['fields']
        assert any(r['metric'] == 'revenue' and r['semantic'] == 'ifrs-full_InsuranceRevenue' for r in fields)
        assert any(r['metric'] == 'operating_income' for r in fields)
    if options.get('conflict'):
        quality = first['stock']['quality_view']
        assert 'sec_business_occurrence_conflict' in quality['fact']['fields']['reason_codes']
        assert quality['fact'] is not None and quality['receipt']['directional_use_allowed'] is False
        effect = first['readiness']['a_materialization']
        assert effect['status'] == 'PASS'
        projection = first['readiness']['business_quality_projection']
        assert projection['effect'] == 'CONFIDENCE_ONLY' and not projection['directional_use_allowed']
        assert projection['source_refs'] == [quality['receipt']['canonical_ref']]


def test_native_valuation_descriptor_roundtrip(tmp_path):
    inputs = valuation_inputs(tmp_path / 'raw')
    descriptor = write_descriptor(tmp_path, inputs)
    loaded = load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])
    first = prepare_fresh_subject(inputs, execution_generation_id='synthetic-rev9')
    assert first == prepare_fresh_subject(loaded, execution_generation_id='synthetic-rev9')
    assert all(not m['entry_use_eligible'] for m in first['stock']['valuation_view']['metrics'])
    descriptor['valuation']['raw']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='artifact_hash_mismatch'):
        load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])


def test_issuer_bridge_descriptor_preserves_security_denial(tmp_path):
    target, source = bridge_inputs(tmp_path)
    target_descriptor = write_descriptor(tmp_path, target)
    source_descriptor = write_descriptor(tmp_path, source)
    bridge = target['financial_inputs']['issuer_business']
    path = tmp_path / 'official-identity.json'
    durable_json(path, bridge['official_identity'], exclusive=True)
    target_descriptor['issuer_bridge'] = dict(source_descriptor=source_descriptor,
        official_identity=dict(path=path.name, sha256=sha256_bytes(path.read_bytes())),
        source_result_sha256=bridge['source_result_sha256'])
    loaded = load_stock_inputs(tmp_path, target_descriptor, target['technical_inputs']['plan'])
    result = prepare_fresh_subject(loaded, execution_generation_id='synthetic-rev9')
    assert result == prepare_fresh_subject(target, execution_generation_id='synthetic-rev9')
    assert result['stock']['status'] == result['readiness']['status'] == 'PASS'
    b = result['stock']['issuer_business_bridge']
    assert b['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE'] and not b['SECURITY_VALUATION_BRIDGE_ELIGIBLE']
    assert not b['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE'] and not b['security_valuation_transfer']
    assert result['stock']['valuation_view']['currency'] == 'USD'
    assert result['stock']['valuation_view']['ticker'] == 'SKHY'
    assert all(m['status'] == 'UNAVAILABLE' for m in result['stock']['valuation_view']['metrics'])
    changed = deepcopy(target_descriptor)
    changed['issuer_bridge']['source_result_sha256'] = digest({})
    with pytest.raises(ValueError, match='source_result_hash_mismatch'):
        load_stock_inputs(tmp_path, changed, target['technical_inputs']['plan'])
