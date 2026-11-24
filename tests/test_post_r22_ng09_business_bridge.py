"""Synthetic source replay through actual issuer/native owners, never real grants."""
from copy import deepcopy
from datetime import timedelta

import pytest

from app.services.canonical_source_inputs import fresh_authority_inputs
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.fundamental_input_policy import InputSourceClass
from app.services.reported_business_projection import COMPARISON_USES
from app.services.unified_snapshot_contract import digest
from scripts.m12dr_financial_source_authority import build_source_authority
from tests.rev9_source_fixtures import bridge_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_reported_business_native_projection import window
from tests.test_unified_stock_acquisition import plan as plan_fixture
from scripts.m12ds_r2_judgment_policy import attribution_only_refs, frozen_fact_fields, materialize_core, observations
from scripts.m12ds_r2_schemas import core_schema


@pytest.fixture
def source(tmp_path):
    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        target, _ = bridge_inputs(tmp_path)
    target.update(reported_comparison_business=True, source_window=window(plan))
    return target


def test_real_current_issuer_owner_reaches_comparisons_observations_and_preflight(source):
    from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject

    result = assemble_fresh_stock(**source)
    stock = result['packet']['stocks'][0]
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    authority = build_source_authority(**fresh_authority_inputs(result, source))
    records = {row['ref_id']: row for row in authority['authority']['authority_records']}
    refs = set(result['comparative_fact_refs'])
    assert refs and refs <= owned.core_refs
    for ref in evidence.evidence:
        if ref.ref_id not in refs:
            continue
        assert ref.reported_business.kind == 'COMPARISON'
        assert ref.reported_business.allowed_uses == COMPARISON_USES
        assert ref.source_use.source_class == InputSourceClass.REPORTED_BUSINESS_COMPARISON
        assert ref.source_use.core_current_fact is True
        assert set(records[ref.ref_id]['allowed_uses']) == set(COMPARISON_USES)
        assert {'VALUATION', 'ENTRY', 'PRICE_ENTRY_CONTEXT'} <= set(records[ref.ref_id]['prohibited_uses'])
        assert not ref.reported_business.security_valuation_transfer
        assert not ref.reported_business.recurrence_verified
    quality_ref = result['quality_view']['receipt']['canonical_ref']
    assert set(records[quality_ref]['allowed_uses']) == {'CONTEXT', 'CONFIDENCE'}
    assert 'OVERALL_DIRECTION' in records[quality_ref]['prohibited_uses']
    assert stock['current_valuation_denial']
    assert not result['issuer_business_bridge']['SECURITY_VALUATION_BRIDGE_ELIGIBLE']
    assert not result['issuer_business_bridge']['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE']
    assert owned == build_owned_evidence_packet(evidence, stock=stock)
    inputs = fresh_authority_inputs(result, source)
    fields = frozen_fact_fields(result['packet'], result['ticker'], inputs['source_metadata'])
    observed = observations(inputs['source_metadata'], authority['authority'], fields)
    assert {row['metric'] for row in observed.values()} == {'revenue', 'operating_income'}
    assert {row['source_ref'] for row in observed.values()} <= refs
    assert not refs & attribution_only_refs(inputs['source_metadata'], authority['authority'])

    prepared = prepare_fresh_subject(source, execution_generation_id='c49-current-issuer-offline')
    assert prepared['prepared']['mode'] == 'EVIDENCE_BASED'
    assert prepared['prepared']['core_input']['observed_propositions']
    assert prepared['readiness']['status'] == 'PASS'
    assert all(prepared['readiness'][stage] == 'PASS' for stage in ('Core', 'A', 'B', 'NewBuyer', 'Holder'))
    assert prepared['readiness']['a_materialization']['status'] == 'PASS'


def test_denied_original_income_never_becomes_an_issuer_observation(source, tmp_path):
    from app.services.bounded_financial_stock_owner import assemble
    from app.services.fresh_financial_stock_owner import fresh_stock_baseline
    from tests.rev8_source_fixtures import fresh_inputs

    plan = source['technical_inputs']['plan']
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        underlying = fresh_inputs(tmp_path / 'denied-issuer', '000660', denied_quality=True, plan=plan)
    source_owner = dict(baseline=fresh_stock_baseline(underlying['technical_inputs']),
        local_seed=underlying['technical_inputs']['local_seed'], **underlying['financial_inputs'])
    original = assemble(**source_owner)
    assert any(bundle['quality']['fields']['current.net_income']['state'] == 'denied'
               for bundle in original['projection']['quality_bundles'])
    bridge = source['financial_inputs']['issuer_business']
    bridge.update(source_inputs=source_owner, source_result_sha256=digest(original))
    result = assemble_fresh_stock(**source)
    inputs = fresh_authority_inputs(result, source)
    authority = build_source_authority(**inputs)['authority']
    fields = frozen_fact_fields(result['packet'], result['ticker'], inputs['source_metadata'])
    observed = observations(inputs['source_metadata'], authority, fields)
    assert result['quality_view']['receipt']['state'] == 'denied'
    assert not any(row['metric'] == 'net_income' for row in observed.values())
    quality_ref = result['quality_view']['receipt']['canonical_ref']
    record = next(row for row in authority['authority_records'] if row['ref_id'] == quality_ref)
    assert record['source_family'] == 'typed_quality'
    assert set(record['allowed_uses']) == {'CONTEXT', 'CONFIDENCE'}
    assert 'OVERALL_DIRECTION' in record['prohibited_uses']


@pytest.mark.parametrize('mutation', ['issuer', 'underlying', 'exchange', 'security_type',
    'official_hash', 'source_generation', 'source_issuer', 'source_period', 'raw', 'source_result'])
def test_original_bridge_fail_closed_before_native_issuance(source, mutation):
    fin = source['financial_inputs']
    bridge = fin['issuer_business']
    original = bridge['source_inputs']
    if mutation == 'issuer':
        fin['plan']['security']['cik'] = '9999'
    elif mutation == 'underlying':
        bridge['official_identity']['evidence']['ordinary_share_identifier'] = '999999'
        bridge['official_identity_sha256'] = digest(bridge['official_identity'])
    elif mutation in {'exchange', 'security_type'}:
        fin['plan']['security'][mutation] = 'ETF' if mutation == 'security_type' else 'OTHER'
        fin['plan']['identity_sha256'] = digest(fin['plan']['security'])
    elif mutation == 'official_hash':
        bridge['official_identity_sha256'] = '0' * 64
    elif mutation == 'source_generation':
        original['plan']['run_id'] = 'old-generation'
    elif mutation in {'source_issuer', 'source_period'}:
        original['plan']['cutoff' if mutation == 'source_period' else 'issuer'] = 'invalid'
    elif mutation == 'raw':
        receipt = next(r for r in original['receipts'] if r.get('artifact'))
        path = original['directory'] / receipt['artifact']
        path.write_bytes(path.read_bytes() + b' ')
    else:
        bridge['source_result_sha256'] = '0' * 64
    with pytest.raises((ValueError, KeyError)):
        assemble_fresh_stock(**source)


@pytest.mark.parametrize('change', ['kind', 'use', 'statement', 'issuer', 'generation'])
def test_actual_native_consumer_rejects_scope_broadening(source, change):
    result = assemble_fresh_stock(**source)
    stock = result['packet']['stocks'][0]
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    ref = next(r for r in evidence.evidence if r.reported_business and r.reported_business.kind == 'COMPARISON')
    update = {'kind': 'ISSUER_CONTEXT'} if change == 'kind' else {'allowed_uses': (*COMPARISON_USES, 'VALUATION')}
    if change == 'issuer':
        update = {'issuer_id': 'CIK:wrong'}
    elif change == 'generation':
        update = {'source_generation': 'old'}
    altered = ref.model_copy(update={'statement': 'Issuer growth authorizes BUY'}) if change == 'statement' else ref.model_copy(
        update={'reported_business': ref.reported_business.model_copy(update=update)})
    packet = evidence.model_copy(update={'evidence': tuple(altered if r.ref_id == ref.ref_id else r for r in evidence.evidence)})
    with pytest.raises(ValueError):
        build_owned_evidence_packet(packet, stock=stock)


def test_caller_rehash_cannot_issue_bridge_context(source):
    result = assemble_fresh_stock(**source)
    stock = deepcopy(result['packet']['stocks'][0])
    payload = stock['reported_business_projection']['payload']
    payload['entries'][next(iter(payload['entries']))]['allowed_uses'] = ['CONTEXT', 'OVERALL_DIRECTION']
    stock['reported_business_projection']['signature'] = digest(payload)
    with pytest.raises(ValueError, match='unissued_or_changed'):
        build_decision_evidence_packet(packet=result['packet'], stock=stock)


@pytest.mark.parametrize('effect', ['CONFIDENCE_ONLY', 'DATA_QUALITY_ONLY'])
def test_current_issuer_quality_keeps_nondirectional_quality_channel(source, effect):
    result = assemble_fresh_stock(**source)
    inputs = fresh_authority_inputs(result, source)
    authority = build_source_authority(**inputs)['authority']
    metadata = inputs['source_metadata']
    refs = {r['ref_id'] for r in metadata if (r.get('reported_business') or {}).get('kind') == 'QUALITY'}
    assert refs
    assert not refs & attribution_only_refs(metadata, authority)
    context = {result['ticker']: dict(metadata=metadata, authority=authority)}
    assert core_schema(context)
    raw = dict(claims=[dict(effect=effect, text='Source-owned issuer financial quality limit.',
        evidence_refs=[sorted(refs)[0]], observation_ids=[], materiality='CONTEXT_ONLY')])
    core = materialize_core(result['ticker'], raw, metadata, authority)
    assert {row['effect'] for row in core['effects'].values()} == {effect}
    assert not any(row['source_ref'] in refs for row in core['observations'].values())
    raw['claims'][0]['effect'] = 'DIRECTIONAL_POSITIVE'
    with pytest.raises(ValueError, match='direction_effect_observation_mismatch'):
        materialize_core(result['ticker'], raw, metadata, authority)


def test_untyped_legacy_bridge_cannot_regain_direction_permission(source):
    from scripts.m12cn_policy_contract import build_subject_catalog
    source['reported_comparison_business'] = False
    result = assemble_fresh_stock(**source)
    inputs = fresh_authority_inputs(result, source)
    refs = set(result['comparative_fact_refs'])
    refs.add(result['quality_view']['receipt']['canonical_ref'])
    context = dict(evidence_packets=[result['evidence_packet']], evidence_ownership=[dict(
        ticker=result['ticker'], core_ref_ids=sorted(refs), timing_ref_ids=[])])
    inputs['catalog'] = build_subject_catalog(context=context, ticker=result['ticker'], atomic_claims=[])
    inputs['source_metadata'] = [r for r in result['evidence_packet']['evidence'] if r['ref_id'] in refs]
    authority = build_source_authority(**inputs)['authority']
    rows = {r['ref_id']: r for r in authority['authority_records']}
    for ref in refs:
        assert rows[ref]['allowed_uses'] == ['CONTEXT']
        assert rows[ref]['source_family'] == 'ISSUER_REPORTED_CONTEXT'
    assert refs <= attribution_only_refs(inputs['source_metadata'], authority)
