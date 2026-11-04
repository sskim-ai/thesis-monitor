"""Synthetic source replay through actual issuer/native owners, never real grants."""
from copy import deepcopy
from datetime import timedelta

import pytest

from app.services.canonical_source_inputs import fresh_authority_inputs
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.fundamental_input_policy import InputSourceClass
from app.services.unified_snapshot_contract import digest
from scripts.m12dr_financial_source_authority import build_source_authority
from tests.rev9_source_fixtures import bridge_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_reported_business_native_projection import window
from tests.test_unified_stock_acquisition import plan as plan_fixture
from scripts.m12ds_r2_judgment_policy import attribution_only_refs, materialize_core
from scripts.m12ds_r2_schemas import core_schema


@pytest.fixture
def source(tmp_path):
    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        target, _ = bridge_inputs(tmp_path)
    target.update(reported_comparison_business=True, source_window=window(plan))
    return target


def test_real_owner_chain_issues_only_issuer_context(source):
    result = assemble_fresh_stock(**source)
    stock = result['packet']['stocks'][0]
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    authority = build_source_authority(**fresh_authority_inputs(result, source))
    records = {row['ref_id']: row for row in authority['authority']['authority_records']}
    refs = set(result['comparative_fact_refs'])
    assert refs and refs <= owned.core_refs
    for ref in evidence.evidence:
        if ref.reported_business:
            assert ref.source_use.source_class == InputSourceClass.REPORTED_ISSUER_CONTEXT
            assert ref.source_use.core_current_fact is False
    for ref in evidence.evidence:
        if ref.ref_id not in refs:
            continue
        assert ref.reported_business.kind == 'ISSUER_CONTEXT'
        assert ref.reported_business.allowed_uses == ('CONTEXT',)
        assert ref.source_use.source_class == InputSourceClass.REPORTED_ISSUER_CONTEXT
        assert ref.source_use.core_current_fact is False
        assert records[ref.ref_id]['allowed_uses'] == ['CONTEXT']
        assert 'OVERALL_DIRECTION' in records[ref.ref_id]['prohibited_uses']
        assert not ref.reported_business.security_valuation_transfer
        assert not ref.reported_business.recurrence_verified
    assert stock['current_valuation_denial']
    assert owned == build_owned_evidence_packet(evidence, stock=stock)


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
    ref = next(r for r in evidence.evidence if r.reported_business and r.reported_business.kind == 'ISSUER_CONTEXT')
    update = {'kind': 'COMPARISON'} if change == 'kind' else {'allowed_uses': ('CONTEXT', 'OVERALL_DIRECTION')}
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
@pytest.mark.parametrize('kind', ['ISSUER_CONTEXT', 'QUALITY'])
def test_issuer_attribution_cannot_change_security_economic_judgment(source, effect, kind):
    result = assemble_fresh_stock(**source)
    inputs = fresh_authority_inputs(result, source)
    authority = build_source_authority(**inputs)['authority']
    metadata = inputs['source_metadata']
    refs = {r['ref_id'] for r in metadata if (r.get('reported_business') or {}).get('kind') == kind}
    assert refs
    assert refs <= attribution_only_refs(metadata, authority)
    context = {result['ticker']: dict(metadata=metadata, authority=authority)}
    try:
        schema = core_schema(context)
    except ValueError as exc:
        assert str(exc) == 'core_source_empty'
    else:
        import json
        assert all(ref not in json.dumps(schema) for ref in refs)
    raw = dict(claims=[dict(effect=effect, text='Issuer-only uncertainty cannot change this security stance',
        evidence_refs=[sorted(refs)[0]], observation_ids=[], materiality='CONTEXT_ONLY')])
    with pytest.raises(ValueError, match='historical_attribution_not_economic_claim_authority'):
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
