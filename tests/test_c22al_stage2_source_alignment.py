"""Changed Stage2 source roles and absence branch; synthetic input/CLI only."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from tests.test_c22ak_financial_onboarding import case, raw_source, context
from tests.test_preconfirmation_decision_v2_service import _candidate
from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2FundamentalCoreCandidate, accepted_v2_fundamental_core_sha256,
    accepted_v2_stage2_ref_catalog_manifest, accepted_v2_stage2_output_schema,
    accepted_v2_production_prompt, validate_accepted_v2_candidate_ownership,
    validate_accepted_v2_stage2_candidate, accepted_v2_maturity_atomic_claim_catalog,
)
from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionCandidate, Stage2MarketExpectationAssessment,
    eligible_stage2_expectation_refs,
)


def synthetic_stage2(value, core=None):
    """Fresh synthetic model-shaped candidate, never an edit of a rejected output."""
    ownership = value.evidence_ownership[0]
    economic = ownership.core_ref_ids[0]
    timing = next(iter(ownership.timing_ref_ids), economic)
    claim = lambda ref, text: EvidenceClaim(text=text, evidence_refs=(ref,))
    if core is None:
        core = AcceptedV2FundamentalCoreCandidate(ticker=value.selected_subjects[0], decision='BUY',
            directional_balance={'buy': 6, 'sell': 4},
            buy_drivers=(claim(economic, '모의 사업 근거가 방향을 지지합니다.'),),
            sell_drivers=(claim(economic, '같은 근거의 지속성은 미확인입니다.'),),
            balance_summary='모의 근거의 방향과 지속성을 함께 검토합니다.', confidence='MEDIUM',
            decisive_reason=claim(economic, '모의 사업 근거를 검토합니다.'),
            holder_axis={'stance': 'HOLDABLE', 'reason': claim(economic, '모의 사업 기준을 유지합니다.')})
    payload = _candidate().model_dump(mode='json')
    def remap(row):
        if isinstance(row, dict):
            if 'evidence_refs' in row:
                row['evidence_refs'] = [economic]
                row['text'] = '모의 원본의 범위에서 조건을 검토합니다.'
            for child in row.values():
                remap(child)
        elif isinstance(row, list):
            for child in row:
                remap(child)
    remap(payload)
    payload.update(core.model_dump(mode='json'))
    payload['fundamental_core_sha256'] = accepted_v2_fundamental_core_sha256(core)
    payload['new_buyer_axis']['reason']['evidence_refs'] = [timing]
    payload['timing_basis']['evidence_refs'] = [timing]
    payload['market_expectation'] = dict(level='unknown', basis=None,
        unavailable_reason='NO_ELIGIBLE_EXPECTATION_SOURCE')
    payload['pricing_requirement'].update(requirement='UNKNOWN', expectation_basis=None)
    atomic = accepted_v2_maturity_atomic_claim_catalog(core)
    maturity = payload['driver_maturity'][0]
    source_dates = {row.ref_id: row.as_of for row in value.evidence_packets[0].evidence}
    maturity.update(supporting_claim_refs=[atomic[0].claim_ref], contradicting_claim_refs=[],
        supporting_evidence_refs=list(atomic[0].parent_source_refs), contradicting_evidence_refs=[],
        as_of=max(source_dates[ref][:10] for ref in atomic[0].parent_source_refs))
    payload['upgrade_condition']['text'] = '모의 사업 조건이 개선되면 재평가합니다.'
    payload['downgrade_condition']['text'] = '모의 사업 조건이 악화되면 재평가합니다.'
    payload['pre_confirmation_buy'] = core.decision == 'BUY'
    if core.decision != 'BUY':
        payload['preconfirmation_buy_explanation'] = None
    return core, PreconfirmationDecisionCandidate.model_validate(payload)


def test_complete_original_merge_keeps_quality_timing_and_prospective_roles(case):
    value = context(case)
    owned = value.evidence_ownership[0]
    assert owned.core_ref_ids
    assert owned.quality_ref_ids and owned.timing_ref_ids and owned.prospective_ref_ids
    assert not set(owned.quality_ref_ids) & set(owned.core_ref_ids)
    assert not set(owned.prospective_ref_ids) & set(owned.core_ref_ids)
    manifest = accepted_v2_stage2_ref_catalog_manifest(value)
    assert owned.stage2_ref_ids <= set(manifest['allowed_refs'])


def test_unknown_absence_schema_prompt_and_original_semantics_agree(case):
    value = context(case)
    core, candidate = synthetic_stage2(value)
    result = validate_accepted_v2_stage2_candidate(value.evidence_packets[0], candidate, core,
        value.evidence_ownership[0])
    assert result.valid, result.errors
    schema = accepted_v2_stage2_output_schema(value, fundamental_cores=(core,))
    branch = schema['properties']['candidates']['items']['anyOf'][0]
    expectation = branch['properties']['market_expectation']['properties']
    assert expectation['basis'] == {'type': 'null'}
    assert expectation['level']['const'] == candidate.market_expectation.level
    assert branch['properties']['pricing_requirement']['properties']['expectation_basis'] == {'type': 'null'}
    assert schema['$defs']['EvidenceClaim']['properties']['evidence_refs']['minItems'] == 1
    assert 'basis=null' in accepted_v2_production_prompt(value, fundamental_cores=(core,))
    assert candidate.decision == 'BUY' and candidate.new_buyer_axis.stance == 'ATTRACTIVE'


def test_null_basis_is_local_not_a_global_evidence_claim_relaxation(case):
    with pytest.raises(ValidationError):
        EvidenceClaim(text='무근거 모의 주장입니다.', evidence_refs=[])
    with pytest.raises(ValidationError, match='uncited_expectation_requires_typed_unknown'):
        Stage2MarketExpectationAssessment(level='low', basis=None,
            unavailable_reason='NO_ELIGIBLE_EXPECTATION_SOURCE')
    value = context(case)
    core, candidate = synthetic_stage2(value)
    payload = candidate.model_dump(mode='json')
    payload['pricing_requirement']['requirement'] = 'BASE_CASE_REQUIRED'
    with pytest.raises(ValidationError, match='uncited_expectation_pricing_must_be_unknown'):
        PreconfirmationDecisionCandidate.model_validate(payload)


def test_unowned_user_expectation_never_becomes_an_independent_observation(case):
    value = context(case)
    assert not eligible_stage2_expectation_refs(value.evidence_packets[0])
    core, candidate = synthetic_stage2(value)
    payload = candidate.model_dump(mode='json')
    generic = next(row for row in value.evidence_packets[0].evidence if row.category == 'expectations')
    payload['market_expectation'] = dict(level='low', basis=dict(text='가설만 인용한 모의 해석입니다.',
        evidence_refs=[generic.ref_id]), unavailable_reason=None)
    bad = PreconfirmationDecisionCandidate.model_validate(payload)
    validation = validate_accepted_v2_stage2_candidate(value.evidence_packets[0], bad, core,
        value.evidence_ownership[0])
    assert not validation.valid


def test_all_stage2_claims_reject_audit_or_foreign_refs_not_only_new_buyer(case):
    value = context(case)
    core, candidate = synthetic_stage2(value)
    payload = candidate.model_dump(mode='json')
    payload['scenarios']['base']['expectation_and_valuation']['evidence_refs'] = ['FOREIGN:expectations']
    bad = PreconfirmationDecisionCandidate.model_validate(payload)
    assert any('stage2_ref_outside_owned_evidence' in error for error in
        validate_accepted_v2_candidate_ownership(bad, core, value.evidence_ownership[0]))


def test_frozen_core_cannot_be_changed_by_timing_or_unknown(case):
    value = context(case)
    core, candidate = synthetic_stage2(value)
    changed = candidate.model_copy(update={'balance_summary': '가격 때문에 사업 방향을 변경한 모의 문장입니다.'})
    assert 'price_timing_stage_mutated_fundamental_core' in validate_accepted_v2_candidate_ownership(
        changed, core, value.evidence_ownership[0])
    assert not validate_accepted_v2_candidate_ownership(candidate, core, value.evidence_ownership[0])


def test_quality_cannot_supply_a_business_core_or_valuation_denominator(case):
    value = context(case)
    core, candidate = synthetic_stage2(value)
    bad = core.model_copy(update={'buy_drivers': (EvidenceClaim(text='품질 한계를 방향 근거로 바꾼 모의 주장입니다.',
        evidence_refs=(value.evidence_ownership[0].quality_ref_ids[0],)),)})
    from app.services.accepted_decision_v2_runtime_service import validate_accepted_v2_fundamental_core
    assert any('noncore_ref_in_fundamental_core' in error for error in
        validate_accepted_v2_fundamental_core(bad, value.evidence_ownership[0]))
    payload = candidate.model_dump(mode='json')
    payload['pricing_requirement']['valuation_basis']['evidence_refs'] = [value.evidence_ownership[0].prospective_ref_ids[0]]
    altered = PreconfirmationDecisionCandidate.model_validate(payload)
    assert 'prospective_hypothesis_in_pricing_evidence' in validate_accepted_v2_candidate_ownership(
        altered, core, value.evidence_ownership[0])


def test_expectation_present_branch_requires_exact_citation_but_not_fake_production_grant(case):
    # Scope-unit test only: real independent-expectation Producer is unavailable
    # in the retained campaign. No production proof is fabricated for this branch.
    from app.services.preconfirmation_decision_v2_service import _claim_categories
    from app.services.cross_market_decision_engine_service import DecisionEvidenceRef, DecisionEvidencePacket
    from app.services.fundamental_input_policy import source_use
    packet = DecisionEvidencePacket(packet_id='synthetic-scope', ticker='SYNTHETIC', company_name='Synthetic',
        market='us', assessment_date='2026-11-11', horizon='research', evidence=(DecisionEvidenceRef(
            ref_id='scope-only-expectation', category='expectations', label='Synthetic scope only',
            statement='Synthetic only, not an admitted financial fact', as_of='2026-11-11',
            source_ref='stock.fact_catalog.synthetic', source_use=source_use(
                source_ref='stock.fact_catalog.synthetic', security_id='SYNTHETIC',
                canonical=True, typed_financial=True)),), prohibited_claims=(), evidence_sha256='synthetic')
    assert eligible_stage2_expectation_refs(packet) == {'scope-only-expectation'}
    from app.services.direction_timing_ownership_service import build_owned_evidence_packet
    with pytest.raises(ValueError, match='fundamental_source_use_producer_mismatch'):
        build_owned_evidence_packet(packet, stock={'fact_catalog': []})


def test_future_and_identity_changes_still_reject_original_handoff(case):
    from app.services.onboarding_decision_service import _validate_campaign_financial_source, _canonical_sha
    fin = case['source']['financial_inputs']
    retained = dict(source_generation=fin['plan']['run_id'], plan_sha256=_canonical_sha(fin['plan']),
        receipts_sha256=_canonical_sha(fin['receipts']), acquisition_sha256=_canonical_sha(fin['acquisition']),
        use='DATED_ONBOARDING_EVIDENCE_NOT_OPERATING_SOURCE')
    ledger = SimpleNamespace(identity={'children': {'us': dict(generation='NEW_CAMPAIGN',
        retained_onboarding_source=retained)}})
    _validate_campaign_financial_source(ledger, case['item'], {'financial_inputs': fin})
    ledger.identity['children']['us']['retained_onboarding_source']['receipts_sha256'] = '0'*64
    with pytest.raises(ValueError, match='campaign_generation_mismatch'):
        _validate_campaign_financial_source(ledger, case['item'], {'financial_inputs': fin})
    from app.services.onboarding_evidence_service import initial_evidence_fingerprint
    case['evidence']['thesis_version'] += 1
    case['evidence']['fingerprint'] = initial_evidence_fingerprint(case['evidence'])
    with pytest.raises(ValueError):
        context(case)


def test_native_reference_replay_rejects_missing_original_body_and_unexpected_periods():
    from app.services.dated_chart_reference import technical_context_from_references
    with pytest.raises(ValueError):
        technical_context_from_references({}, ticker='SYNTHETIC', market='us',
            period_sources={'quarterly': {}})


def test_original_registration_first_session_gate_after_synthetic_stage2(tmp_path, case):
    value = context(case)
    core, candidate = synthetic_stage2(value)
    assert validate_accepted_v2_stage2_candidate(value.evidence_packets[0], candidate, core,
        value.evidence_ownership[0]).valid
    from tests.test_prospective_class_c_owner import fixture, issue
    (tmp_path/'eligible').mkdir()
    (tmp_path/'future').mkdir()
    approval, capture, _ = fixture(tmp_path/'eligible')
    owner, document = issue(approval, capture)
    assert document['universe']['eligible_subjects']
    # This is an isolated synthetic SQLite, not a real registration or grant.
    approval, capture, _ = fixture(tmp_path/'future', mutation=
        "UPDATE watchlistitem SET first_eligible_session='2099-01-01'")
    with pytest.raises(ValueError, match='NO_ELIGIBLE_SUBJECT_FOR_MARKET'):
        issue(approval, capture)


def test_full_source_and_monitoring_cannot_be_replaced_by_onboarding_core(tmp_path):
    from app.services.selected_source_preparation import prepare_child
    from app.services.production_monitoring_session import ProductionMonitoringSession
    with pytest.raises(ValueError, match='selected_source_preparation_default_off'):
        prepare_child(root=tmp_path, frozen={}, outcome={}, policy=None, registration_owner=None)
    with pytest.raises(ValueError, match='production_monitoring_current_cohort_gap'):
        ProductionMonitoringSession(tmp_path, market='us', generation_id='synthetic',
            source=dict(prepared={}, stocks={}, markets={'us': {}}, source_generation_id='synthetic'))
    assert not list(tmp_path.rglob('*.accepted.json'))
