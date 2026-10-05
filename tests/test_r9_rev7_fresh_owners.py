from copy import deepcopy

import pytest

from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_owner import assemble_stock, validate_assembled
from tests.test_unified_stock_owner import source as existing_source, freeze_hashes


@pytest.fixture
def source():
    from app.services.completed_price_state import bind_source
    from tests.completed_price_fixtures import source as completed_source
    value = existing_source.__wrapped__()
    security = next(r['record'] for role in value['local_seed']['roles'].values()
                    for r in role['records'] if r['table'] == 'securitymaster')
    close_source, artifacts = completed_source(value['plan'], security)
    return bind_source(value, source=close_source, artifacts=artifacts, security=security)


def test_fresh_technical_baseline_has_no_stored_financial_facts(source):
    source['financial'] = None
    source['fresh_financial_pending'] = True
    freeze_hashes(source)
    result = assemble_stock(**source)
    assert result['status'] == 'BLOCKED'
    assert result['observed_business_cardinality'] == 0
    assert result['financial_state']['status'] == 'UNAVAILABLE'
    assert not any(f['fact_type'] in {'earnings', 'earnings_comparison', 'financial_quality'}
                   for f in result['packet']['stocks'][0]['fact_catalog'])
    assert validate_assembled(result, expected_result_sha256=digest(result)) is False


def test_fresh_pending_rejects_financial_carryin_even_if_hash_valid(source):
    source['fresh_financial_pending'] = True
    with pytest.raises(ValueError, match='must_not_import'):
        assemble_stock(**source)


def quality_fixture(source):
    from scripts.m12dr_financial_source_authority import source_quality, comparative_facts
    from app.services.financial_observation_quality_service import digest as quality_digest
    record = next(r['record'] for r in source['financial']['projection']['records']
                  if r['table'] == 'financialsnapshot')
    # A real canonical source row, but no fabricated comparison. An absent pair
    # must fail quality binding rather than turn into a clean confidence fact.
    inputs = dict(ticker='CORZ', cutoff='2026-09-26', formal=record,
                  comparison=None, preliminary=None, foreign_candidates=[])
    bundle = dict(source_inputs=inputs, source_inputs_sha256=quality_digest(inputs), source_generation_id='fresh')
    bundle['quality'] = source_quality(bundle)
    return dict(quality_bundles=[bundle], snapshots=[record]), comparative_facts(
        bundle['quality'], ticker='CORZ', issuer_id='CIK:1234')


def test_quality_cannot_invent_current_comparison(source):
    from app.services.canonical_business_quality_owner import derive_fresh
    projection, facts = quality_fixture(source)
    assert not facts
    with pytest.raises(ValueError, match='EXPECTED_BUSINESS_QUALITY'):
        derive_fresh(projection=projection, facts=facts, ticker='CORZ', security_id='security-CORZ', run_id='fresh')


def test_valuation_optional_denominators_not_silently_adopted(source):
    from app.services.current_fresh_valuation import derive_current_valuation, verify_current_valuation
    projection, _ = quality_fixture(source)
    security = next(r['record'] for v in source['local_seed']['roles'].values() for r in v['records']
                    if r['table'] == 'securitymaster')
    price = dict(contract='current-price-context-v1', availability='legacy_only',
                 current_price=100, currency='USD', as_of_date='2026-09-25', price_basis='adjusted_close')
    inputs = dict(ticker='CORZ', run_id='fresh', security=security, price=price, projection=projection)
    view = derive_current_valuation(**inputs)
    assert verify_current_valuation(view, **inputs)
    assert len(view.metrics) == 3
    assert all(m.status == 'UNAVAILABLE' and m.value is None and not m.overall_direction_use for m in view.metrics)
    assert view.metrics[2].estimate_horizon is None
    assert not view.metrics[2].latest_published
    mutation = view.model_copy(update={'price': 99})
    with pytest.raises(ValueError, match='replay_mismatch'):
        verify_current_valuation(mutation, **inputs)
    prior = deepcopy(projection)
    prior['quality_bundles'][0]['source_generation_id'] = 'old'
    with pytest.raises(ValueError, match='generation_or_security'):
        derive_current_valuation(**{**inputs, 'projection': prior})


def test_valuation_cross_security_is_rejected(source):
    from app.services.current_fresh_valuation import derive_current_valuation
    projection, _ = quality_fixture(source)
    with pytest.raises(ValueError, match='security_identity'):
        derive_current_valuation(ticker='CORZ', run_id='fresh', security={'ticker': 'TSM'},
                                 price={}, projection=projection)


def test_fresh_quality_reuses_selected_field_taint_and_exact_generation():
    from tests.test_r2b_r3_quality_owner import bundle_for
    from scripts.m12dr_financial_source_authority import comparative_facts
    from app.services.canonical_business_quality_owner import derive_fresh
    bundle = bundle_for('sec_companyfacts')
    facts = comparative_facts(bundle['quality'], ticker='FICTIVE', issuer_id='CIK:0000001234')
    inputs = dict(projection={'quality_bundles': [bundle]}, facts=facts, ticker='FICTIVE',
                  security_id='security-fixture', run_id='synthetic-source')
    first = derive_fresh(**inputs)
    assert first == derive_fresh(**inputs)
    assert first['receipt']['directional_use_allowed'] is False
    assert 'sec_business_occurrence_conflict' in first['fact']['fields']['reason_codes']
    assert first['fact']['input_fact_ids'] == sorted(f['fact_id'] for f in facts)
    with pytest.raises(ValueError, match='generation_or_subject'):
        derive_fresh(**{**inputs, 'run_id': 'new-generation'})


def test_raw_current_financial_to_quality_valuation_and_existing_stock(tmp_path, source, monkeypatch):
    from tests import test_bounded_financial_acquisition as fixtures
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    original_plan = fixtures.plan
    def plan(*args, **kwargs):
        value = original_plan(*args, **kwargs)
        value.update(run_id=source['plan'].run_id, cutoff=source['plan'].frozen_at.isoformat())
        return value
    monkeypatch.setattr(fixtures, 'plan', plan)
    source['financial'] = None
    freeze_hashes(source)
    security = next(r['record'] for c in source['local_seed']['roles'].values() for r in c['records']
                    if r['table'] == 'securitymaster')
    p, a, receipts = fixtures.sec_fixture(tmp_path, ticker='CORZ', cik='1234', security=security)
    inputs = dict(technical_inputs=source, financial_inputs=dict(plan=p, acquisition=a,
                  directory=tmp_path, receipts=receipts))
    result = assemble_fresh_stock(**inputs)
    assert result['status'] == 'PASS', result['mandatory_missing']
    assert result == assemble_fresh_stock(**inputs)
    assert result['quality_view']['receipt']['source_generation_id'] == source['plan'].run_id
    assert result['quality_view']['receipt']['state'] == 'verified_usable'
    assert result['valuation_view']['run_id'] == source['plan'].run_id
    assert len(result['valuation_view']['metrics']) == 3
    assert len(result['comparative_fact_refs']) == 2
    assert result['packet']['source_time_domains']['scope'] == 'FRESH_CURRENT_RUN'
    assert result['complete_source_adapter_qualified'] is False
    from app.services import bounded_financial_stock_owner as owner
    assemble = owner.assemble
    def denied(**kwargs):
        value = assemble(**kwargs)
        value['acquisition_denials'] = ['fixture_financial_source_denied']
        value['status'] = 'BLOCKED'
        return value
    monkeypatch.setattr(owner, 'assemble', denied)
    blocked = assemble_fresh_stock(**inputs)
    assert blocked['status'] == 'BLOCKED'
    assert 'fresh_financial_acquisition:source_denied' in blocked['mandatory_missing']
    assert blocked['packet_sha256'] is None
    monkeypatch.setattr(owner, 'assemble', assemble)
    before = deepcopy(receipts)
    receipts[0]['started_at'] = '2025-01-01T00:00:00+00:00'
    with pytest.raises(ValueError, match='predates_generation'):
        assemble_fresh_stock(**inputs)
    receipts[:] = before
    (tmp_path / a['companyfacts_artifact']).write_bytes(b'{}')
    with pytest.raises(ValueError, match='raw_receipt_hash_mismatch'):
        assemble_fresh_stock(**inputs)
