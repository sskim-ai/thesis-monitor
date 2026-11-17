"""Synthetic raw responses through original owners; no live/operating DB use."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from types import SimpleNamespace

import pytest

from app.services import onboarding_decision_service as service
from app.services.accepted_decision_v2_runtime_service import (
    accepted_v2_fundamental_core_output_schema,
    accepted_v2_fundamental_core_ref_catalog_manifest,
)
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.onboarding_evidence_service import (
    INITIAL_EVIDENCE_CONTRACT, REQUIRED_PRICE_PERIODS, initial_evidence_fingerprint,
)
from tests.test_reported_business_native_projection import source as raw_source


class MemorySession:
    """Only supplies one synthetic Thesis object, never opens SQL connections."""

    def __init__(self, thesis):
        self.thesis = thesis

    def exec(self, _statement):
        return SimpleNamespace(first=lambda: self.thesis)


@pytest.fixture
def case(raw_source):
    original = assemble_fresh_stock(**raw_source)
    stock = original['packet']['stocks'][0]
    thesis = SimpleNamespace(version=stock['thesis_version'],
        time_horizon=stock['thesis'].get('time_horizon'), core_thesis=stock['thesis']['core_thesis'],
        **{key: json.dumps(stock['thesis'][key]) for key in (
            'validation_metrics', 'strengthen_signals', 'weaken_signals', 'invalidation_signals')})
    evidence = dict(contract=INITIAL_EVIDENCE_CONTRACT, ticker=stock['ticker'],
        market=original['packet']['market'], thesis_version=stock['thesis_version'],
        as_of=original['packet']['generated_at'], current_thesis={
            key: stock['thesis'][key] for key in ('core_thesis', 'validation_metrics',
                'strengthen_signals', 'weaken_signals', 'invalidation_signals')},
        current_price=100, ohlcv_feature_availability={key: {'available': True} for key in REQUIRED_PRICE_PERIODS},
        price_structure={}, valuation_context={}, market_expectations={'synthetic': 'unknown'},
        latest_safe_earnings_checkpoint={'status': 'AVAILABLE', 'period_end': '2026-06-30',
                                         'provider': 'SYNTHETIC_METADATA_NOT_FACT'},
        relevant_events=[], material_unknowns=['SYNTHETIC_ONLY'],
        material_market_context={'status': 'NOT_CHECKED'})
    evidence['fingerprint'] = initial_evidence_fingerprint(evidence)
    return dict(source=raw_source, original=original, session=MemorySession(thesis),
                item=SimpleNamespace(ticker=stock['ticker'], company_name='SYNTHETIC'), evidence=evidence)


def context(case, *, source=True):
    return service.build_onboarding_decision_context(case['session'], case['item'], case['evidence'],
        financial_source_inputs=case['source'] if source else None)


def test_metadata_only_reproduces_empty_core_without_promotion(case):
    value = context(case, source=False)
    assert value.evidence_ownership[0].core_ref_ids == ()
    with pytest.raises(ValueError, match='v2_fundamental_core_ref_catalog_empty'):
        accepted_v2_fundamental_core_output_schema(value)


def test_original_raw_producer_reaches_original_core_manifest(case):
    before = deepcopy(case['evidence'])
    value = context(case)
    refs = set(value.evidence_ownership[0].core_ref_ids)
    assert set(case['original']['comparative_fact_refs']) <= refs
    assert value.packet_id == case['original']['packet']['packet_id']
    assert accepted_v2_fundamental_core_output_schema(value)
    assert accepted_v2_fundamental_core_ref_catalog_manifest(value)
    generic = [ref for ref in value.evidence_packets[0].evidence if ref.ref_id.startswith('onboarding:')]
    assert generic and all(ref.source_use is None for ref in generic)
    assert not {ref.ref_id for ref in generic} & refs
    assert case['evidence'] == before
    # The same original financial owner can replay before operational Source
    # registration, without requiring or inventing a technical/static seed.
    case['source'] = {'financial_inputs': case['source']['financial_inputs']}
    preactivation = context(case)
    assert preactivation.packet_id.endswith(':onboarding')
    assert set(case['original']['comparative_fact_refs']) <= set(preactivation.evidence_ownership[0].core_ref_ids)
    assert accepted_v2_fundamental_core_output_schema(preactivation)


def test_caller_catalog_or_binding_cannot_replace_original_inputs(case):
    for forged in ({'packet': case['original']['packet']},
                   {'source_use': {'core_current_fact': True}},
                   {'fact_catalog': [{'fact_id': 'forged', 'source': 'canonical_financial_fact'}]}):
        case['source'] = forged
        with pytest.raises(ValueError, match='onboarding_financial_original_inputs_required'):
            context(case)


def test_compatibility_comparison_does_not_gain_core_rights(case):
    case['source']['reported_comparison_business'] = False
    with pytest.raises(ValueError, match='onboarding_typed_financial_source_unavailable'):
        context(case)


def test_wrong_subject_and_mixed_cohort_are_not_onboarding_inputs(case):
    original = case['item'].ticker
    case['item'].ticker = 'OTHER'
    with pytest.raises(ValueError, match='onboarding_financial_subject_scope_mismatch'):
        context(case)
    case['item'].ticker = original
    case['source']['technical_inputs']['local_seed']['universe']['eligible_subjects'].append('OTHER')
    with pytest.raises(ValueError, match='onboarding_financial_subject_scope_mismatch'):
        context(case)


def test_thesis_version_and_private_body_binding_reject_mismatch(case):
    case['session'].thesis.version += 1
    with pytest.raises(ValueError, match='onboarding_financial_thesis_version_mismatch'):
        context(case)
    case['session'].thesis.version -= 1
    case['session'].thesis.core_thesis = 'DIFFERENT_SYNTHETIC_USER_HYPOTHESIS'
    with pytest.raises(ValueError, match='onboarding_financial_thesis_mismatch'):
        context(case)


def test_exact_evidence_cutoff_blocks_lookahead(case):
    at = datetime.fromisoformat(case['evidence']['as_of'])
    case['evidence']['as_of'] = (at - timedelta(seconds=1)).isoformat()
    case['evidence']['fingerprint'] = initial_evidence_fingerprint(case['evidence'])
    with pytest.raises(ValueError, match='onboarding_financial_projection_after_evidence'):
        context(case)


def test_original_raw_hash_and_generation_still_enforced(case):
    case['source']['financial_inputs']['plan']['run_id'] = 'FORGED_CURRENT_GENERATION'
    with pytest.raises(ValueError, match='generation'):
        context(case)
    case['source']['financial_inputs']['plan']['run_id'] = case['source']['technical_inputs']['plan'].run_id
    fin = case['source']['financial_inputs']
    case['source'] = {'financial_inputs': fin}
    fin.update(statement_basis_policy='SYNTHETIC_POLICY', basis_execution_generation='OTHER')
    with pytest.raises(ValueError, match='basis_execution_generation_mismatch'):
        context(case)
    del fin['statement_basis_policy'], fin['basis_execution_generation']
    receipt = next(row for row in fin['receipts'] if row.get('artifact') and row.get('raw_sha256'))
    path = fin['directory'] / receipt['artifact']
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError):
        context(case)


def test_invalid_evidence_never_starts_model_or_repair(case, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(service, '_invoke_signed_in_codex', lambda **kwargs: calls.append(kwargs))
    case['evidence']['fingerprint'] = 'FORGED'
    with pytest.raises(ValueError, match='initial_evidence_fingerprint_mismatch'):
        service._generate_onboarding_accepted_decision(case['session'], case['item'], case['evidence'],
            timeout=600, data_dir=tmp_path, financial_source_inputs=case['source'])
    assert calls == [] and not list(tmp_path.rglob('*.repair.*'))


def test_selected_registration_still_rejects_pending_subject():
    import inspect
    from app.services.prospective_class_c_owner import issue_prospective_owner
    from app.services.onboarding_reconciler_service import resume_onboarding_subject
    # Static original contracts, not a synthetic production Owner issuance.
    owner = inspect.getsource(issue_prospective_owner)
    assert 'prospective_active_registration_and_thesis_required' in owner
    assert 'OnboardingAttemptMode.BACKGROUND' in inspect.getsource(resume_onboarding_subject)


def test_current_price_or_valuation_is_not_added_as_core_authority(case):
    value = context(case)
    refs = {row.ref_id: row for row in value.evidence_packets[0].evidence}
    core = value.evidence_ownership[0].core_ref_ids
    assert all(refs[key].source_ref.startswith('stock.fact_catalog.') for key in core)
    assert not any(refs[key].source_ref in ('stock.current_price_context', 'onboarding_initial_evidence.valuation_context')
                   for key in core)


def test_financial_handoff_does_not_fall_back_to_legacy_model_profile(case, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(service, '_invoke_signed_in_codex', lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ValueError, match='onboarding_financial_campaign_execution_required'):
        service.generate_onboarding_accepted_decision(case['session'], case['item'], case['evidence'],
            timeout=600, data_dir=tmp_path, financial_source_inputs=case['source'])
    assert calls == []
