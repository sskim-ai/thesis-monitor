"""Actual raw owners and producer; all data/model outputs here are synthetic."""
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.reported_business_projection import issue
from app.services.canonical_source_inputs import fresh_authority_inputs
from scripts.m12dr_financial_source_authority import build_source_authority
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from tests.rev8_source_fixtures import fresh_inputs, POLICY
from tests.rev10_source_fixtures import wire_clock
from tests.test_unified_stock_acquisition import plan as plan_fixture


@pytest.fixture
def source(tmp_path):
    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        inputs = fresh_inputs(tmp_path, 'CORZ', verified_identity=True,
                              financial_scale=1_000_000, plan=plan)
    return {**inputs, 'reported_comparison_business': True, 'source_window': window(plan)}


def window(plan):
    return dict(run_id=plan.run_id, collection_started_at=plan.frozen_at.isoformat(),
        source_query_cutoff=(plan.frozen_at + timedelta(seconds=10)).isoformat(),
        business_availability_cutoff=(plan.frozen_at + timedelta(seconds=30)).isoformat())


def test_original_raw_to_native_comparative_and_quality(source):
    result = assemble_fresh_stock(**source)
    assert result['status'] == 'PASS'
    stock = result['packet']['stocks'][0]
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    assert set(result['comparative_fact_refs']) <= owned.core_refs
    assert result['quality_view']['receipt']['canonical_ref'] in owned.core_refs
    authority = build_source_authority(**fresh_authority_inputs(result, source))
    records = {row['ref_id']: row for row in authority['authority']['authority_records']}
    for ref in result['comparative_fact_refs']:
        assert set(records[ref]['allowed_uses']) == {'CONTEXT', 'BUSINESS_CONTEXT', 'PASS_A_ARCHETYPE', 'OVERALL_DIRECTION'}
    assert 'OVERALL_DIRECTION' not in records[result['quality_view']['receipt']['canonical_ref']]['allowed_uses']
    prepared = prepare_fresh_subject(source, execution_generation_id=source['technical_inputs']['plan'].run_id)
    assert prepared['prepared']['mode'] == 'EVIDENCE_BASED'
    assert prepared['readiness']['status'] == 'PASS'


def test_unissued_property_cannot_become_native_input(source):
    result = assemble_fresh_stock(**source)
    stock = deepcopy(result['packet']['stocks'][0])
    stock['reported_business_projection']['signature'] = '0' * 64
    with pytest.raises(ValueError, match='business_projection_unissued_or_changed'):
        build_decision_evidence_packet(packet=result['packet'], stock=stock)


@pytest.mark.parametrize('field,value', [('delta', 0), ('issuer_id', 'CIK:9999999999'),
    ('period_end', '2027-06-30'), ('currency', 'KRW'), ('recurrence_verified', True)])
def test_signed_fact_mutation_rejected(source, field, value):
    result = assemble_fresh_stock(**source)
    stock = deepcopy(result['packet']['stocks'][0])
    fact = next(f for f in stock['fact_catalog'] if f['fact_type'] == 'earnings_comparison')
    fact['fields'][field] = value
    with pytest.raises(ValueError, match='business_projection_native_binding'):
        build_decision_evidence_packet(packet=result['packet'], stock=stock)


def test_caller_cannot_issue_from_public_hashes():
    with pytest.raises(ValueError, match='business_backend_replay_permit_required'):
        issue(stock={}, packet={}, facts=[], plan={}, acquisition={}, projection={}, selected_owner={},
              quality={}, bridge=None)


def test_typed_packet_mutation_rejected_by_actual_owned_builder(source):
    result = assemble_fresh_stock(**source)
    stock = result['packet']['stocks'][0]
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    ref = next(r for r in evidence.evidence if r.reported_business and r.reported_business.kind == 'COMPARISON')
    altered = ref.model_copy(update={'statement': 'Unsupported cause and future profit 999999'})
    forged = evidence.model_copy(update={'evidence': tuple(altered if r.ref_id == ref.ref_id else r for r in evidence.evidence)})
    with pytest.raises(ValueError, match='business_native_projection_mismatch'):
        build_owned_evidence_packet(forged, stock=stock)


def test_historical_context_is_not_business_permission(source):
    source['reported_comparison_context'] = True
    with pytest.raises(ValueError, match='business_historical_context_not_direction'):
        assemble_fresh_stock(**source)


def test_opt_in_off_keeps_compatibility_excluded(source):
    source['reported_comparison_business'] = False
    result = assemble_fresh_stock(**source)
    stock = result['packet']['stocks'][0]
    owned = build_owned_evidence_packet(build_decision_evidence_packet(packet=result['packet'], stock=stock), stock=stock)
    assert not set(result['comparative_fact_refs']) & owned.core_refs


def test_original_raw_alteration_fails_before_native_admission(source):
    fin = source['financial_inputs']
    receipt = next(r for r in fin['receipts'] if r.get('artifact') and r.get('raw_sha256'))
    path = fin['directory']/receipt['artifact']
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):
        assemble_fresh_stock(**source)


def test_source_qualified_evidence_based_core_a_b_overall_holder(source):
    from scripts.r9_offline_stage_replay import replay_stages
    from tests.rev10_stage_fixtures import synthetic_outputs
    result = prepare_fresh_subject(source, execution_generation_id='ng07-synthetic-native-positive')
    assert result['prepared']['mode'] == 'EVIDENCE_BASED'
    outputs = synthetic_outputs(result, 'ng07-synthetic-native-positive', source['technical_inputs']['local_seed'])
    proof = replay_stages(result, 'ng07-synthetic-native-positive', outputs)
    assert proof['status'] == 'PASS'
    assert proof['synthetic_only'] and proof['external_model_calls'] == 0
    assert proof['stage_receipts']['a']['semantic']['status'] == 'PASS'
    assert proof['stage_receipts']['b']['status'] == 'PASS'
    assert proof['capture']['production_sends'] == proof['capture']['network_requests'] == 0
    assert proof['accepted_outputs']['core']['atomic_claims']


@pytest.mark.parametrize('field,value', [('ticker', 'OTHER'), ('packet_id', 'other-invocation'),
    ('assessment_date', '2026-09-22'), ('market', 'kr')])
def test_wrong_consumption_identity(source, field, value):
    result = assemble_fresh_stock(**source)
    stock = result['packet']['stocks'][0]
    evidence = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    with pytest.raises(ValueError):
        build_owned_evidence_packet(evidence.model_copy(update={field: value}), stock=stock)


def test_quality_cannot_substitute_for_business(source):
    result = assemble_fresh_stock(**source)
    stock = deepcopy(result['packet']['stocks'][0])
    fact = next(f for f in stock['fact_catalog'] if f['fact_type'] == 'financial_quality')
    fact['fields']['state'] = 'verified_usable' if fact['fields']['state'] != 'verified_usable' else 'denied'
    with pytest.raises(ValueError, match='business_projection_native_binding'):
        build_decision_evidence_packet(packet=result['packet'], stock=stock)


@pytest.mark.parametrize('key,value', [('run_id', 'another-generation'), ('issuer', '9999')])
def test_original_owner_identity_cannot_be_rehashed(source, key, value):
    source['financial_inputs']['plan'][key] = value
    with pytest.raises(ValueError):
        assemble_fresh_stock(**source)


def test_same_invocation_lookup_idempotent(source):
    result = assemble_fresh_stock(**source)
    stock = result['packet']['stocks'][0]
    first = build_decision_evidence_packet(packet=result['packet'], stock=stock)
    assert first == build_decision_evidence_packet(packet=result['packet'], stock=stock)
    assert build_owned_evidence_packet(first, stock=stock) == build_owned_evidence_packet(first, stock=stock)


def test_actual_b2_request_with_source_owned_valuation(tmp_path, record_property):
    from app.services.unified_source_policy import UnifiedSourcePolicy
    from app.services import new_buyer_input_owner, new_buyer_request_owner
    from scripts import newbuyer_b2_v2_coverage as coverage
    from scripts.r9_offline_stage_replay import replay_stages, core_inputs, a_inputs
    from tests.rev28_native_fixtures import native_input
    from tests.rev10_stage_fixtures import synthetic_outputs
    from tests.test_newbuyer_b2_v2 import outputs, validate
    from tests.test_newbuyer_b2_v2_coverage import compose

    plan = plan_fixture.__wrapped__()
    policy = UnifiedSourcePolicy(POLICY.allowed_providers | frozenset({'finnhub', 'kiwoom_rest'}))
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        inputs = fresh_inputs(tmp_path, 'CORZ', verified_identity=True,
                              financial_scale=1_000_000, plan=plan, policy=policy)
    inputs['reported_comparison_business'] = True
    inputs['source_window'] = window(plan)
    security = inputs['financial_inputs']['plan']['security']
    inputs['valuation_inputs'] = native_input(security, start=plan.frozen_at, run=plan.run_id, policy=policy)
    generation = 'ng07-synthetic-complete-native-consumer'
    result = prepare_fresh_subject(inputs, execution_generation_id=generation)
    assert result['prepared']['mode'] == 'EVIDENCE_BASED'
    raw = synthetic_outputs(result, generation, inputs['technical_inputs']['local_seed'])
    replay = replay_stages(result, generation, raw)
    state = a_inputs(result, core_inputs(result, generation, raw['core']), raw['a'])
    owned = coverage.SourceOwners(generation=plan.run_id, stock=result['stock'], security=security,
        collection_receipt_sha256=coverage.digest(dict(fixture='source-only', generation=plan.run_id)))
    valuation = compose(owned)
    assert valuation['coverage']['coverage_complete'] and valuation['census']
    state['b_context']['valuation_context'] = valuation['contexts']['CORZ']
    v1 = new_buyer_input_owner.build_request(settings=SimpleNamespace(newbuyer_qualified_valuation_shadow=True),
        context=state['b_context'], accepted=replay['accepted_outputs']['b'], core=state['core'],
        pass_a=state['a'], source_generation_id=plan.run_id)
    legacy = []
    subject = v1['subject']
    for ref in subject['capability']['confidence'] + subject['capability']['quality']:
        claim = next(row for row in subject['frozen_business_claims'] if row['claim_ref'] == ref)
        effect = state['core']['effects'][ref]
        legacy.append(dict(ticker='CORZ', claim_ref=ref, effect=effect['effect'],
            existing_materiality=effect['materiality'], legacy_claim_sha256=coverage.digest(claim)))
    request = new_buyer_request_owner.build_request(enabled=True, v1_request=v1,
        coverage=valuation['coverage'], census=valuation['census'],
        coverage_sha=valuation['coverage']['receipt_sha256'], census_sha=valuation['census']['receipt_sha256'],
        legacy_records=legacy)
    rows = outputs(request)
    checks = [validate(row, request) for row in rows]
    assert rows and all(check['status'] == 'PASS' for check in checks)
    record_property('ng07_business_positive', dict(provenance='SYNTHETIC_SOURCE_AND_MODEL_OUTPUT_ONLY',
        mode=result['prepared']['mode'], generation=generation, source_generation=plan.run_id,
        replay=replay, coverage=valuation, b2_request=request, b2_outputs=rows, b2_validation=checks,
        live_model_calls=0, production_sends=0, production_B2_activation=False))


@pytest.mark.parametrize('value', ['false', 'true', 1, [], None])
def test_opt_in_requires_exact_boolean(source, value):
    source['reported_comparison_business'] = value
    with pytest.raises(ValueError, match='business_opt_in_requires_boolean'):
        assemble_fresh_stock(**source)


def test_explicit_availability_window_required(source):
    source.pop('source_window')
    with pytest.raises(ValueError, match='business_explicit_availability_window_required'):
        assemble_fresh_stock(**source)


def test_response_after_projection_is_rejected(source):
    start=source['technical_inputs']['plan'].frozen_at
    source['source_window'].update(source_query_cutoff=start.isoformat(),
                                  business_availability_cutoff=start.isoformat())
    with pytest.raises(ValueError, match='response_after_business_availability'):
        assemble_fresh_stock(**source)


@pytest.mark.parametrize('field', ['market', 'generated_at', 'source_time_domains'])
def test_outer_packet_binding(source, field):
    result = assemble_fresh_stock(**source)
    packet = deepcopy(result['packet'])
    packet[field] = {'scope': 'forged'} if field == 'source_time_domains' else ('kr' if field == 'market' else '2026-09-01T00:00:00+00:00')
    with pytest.raises(ValueError, match='business_outer_packet_binding'):
        build_decision_evidence_packet(packet=packet, stock=packet['stocks'][0])


def test_conflicting_metric_does_not_deny_independent_comparison(tmp_path):
    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        inputs = fresh_inputs(tmp_path, 'CORZ', verified_identity=True, conflict=True,
                              financial_scale=1_000_000, plan=plan)
    result = assemble_fresh_stock(**inputs, source_window=window(plan), reported_comparison_business=True)
    stock = result['packet']['stocks'][0]
    comparisons = [f for f in stock['fact_catalog'] if 'canonical:' + f['fact_id'] in result['comparative_fact_refs']]
    assert {f['fields']['metric'] for f in comparisons} == {'operating_income'}
    owned = build_owned_evidence_packet(build_decision_evidence_packet(packet=result['packet'], stock=stock), stock=stock)
    assert set(result['comparative_fact_refs']) <= owned.core_refs


def test_missing_required_price_owner_cannot_issue_business(tmp_path, monkeypatch):
    plan = plan_fixture.__wrapped__()
    with wire_clock(plan.frozen_at + timedelta(seconds=4)):
        inputs = fresh_inputs(tmp_path, 'CORZ', verified_identity=True, completed_price=False, plan=plan)
    monkeypatch.setattr('app.services.reported_business_projection.issue',
                        lambda **kwargs: pytest.fail('Missing mandatory source reached issuance'))
    with pytest.raises(ValueError, match='PLAN_GAP_REQUIRED_OWNER_NOT_REQUESTED'):
        assemble_fresh_stock(**inputs, source_window=window(plan), reported_comparison_business=True)
