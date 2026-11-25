"""Synthetic provider wires only; no report directory or accepted AI output."""
from copy import deepcopy
from dataclasses import replace
import inspect
from pathlib import Path

import pytest

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.unified_source_policy import UnifiedSourcePolicy
from scripts import newbuyer_b2_v2_coverage as c
from scripts.kis_current_fy1_owner import current_fper
from tests.rev8_source_fixtures import fresh_inputs, POLICY
from tests.rev28_native_fixtures import native_input
from tests.test_kis_no_estimate_owner import inputs as empty_inputs, payload
from tests.test_unified_stock_acquisition import plan as plan_fixture


def source(tmp_path, ticker='IBM', generation='fictional-generation-one', *, negative=False, empty=False,
           mutate_native=None):
    plan = plan_fixture.__wrapped__().model_copy(update={'run_id': generation})
    policy = UnifiedSourcePolicy(POLICY.allowed_providers | frozenset({'finnhub', 'kiwoom_rest'}))
    inputs = fresh_inputs(tmp_path, ticker, verified_identity=True, policy=policy, plan=plan)
    security = inputs['financial_inputs']['plan']['security']
    inputs['valuation_inputs'] = native_input(security, start=plan.frozen_at, run=generation,
        policy=policy, negative=negative)
    if mutate_native is not None:
        from tests.test_r9_rev28_native_snapshot import alter
        alter(inputs['valuation_inputs'], mutate_native)
    stock = assemble_fresh_stock(**inputs)
    assert stock['status'] == 'PASS'
    extra = {}
    if empty:
        evidence = empty_inputs(ticker)
        p = {k:v for k,v in evidence['plan'].items() if k != 'receipt_sha256'}
        p.update(generation_id=generation, as_of=plan.frozen_at.isoformat(), securities={ticker: security})
        evidence['plan'] = c.sealed(p)
        evidence['generation'] = generation
        evidence['request']['plan_sha256'] = evidence['plan']['receipt_sha256']
        evidence['receipt']['request'] = deepcopy(evidence['request'])
        eps = dict(state='UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE', value=None)
        row = dict(security_code=ticker, eps=eps, provider_per=eps, price=None, action=None,
            current_fper=current_fper(eps, None, None))
        extra = dict(kis_row=row, kis_plan=evidence['plan'], availability_inputs=evidence,
                     kis_corpus_sha256=c.digest(row))
    return c.SourceOwners(generation=generation, stock=stock, security=security,
        collection_receipt_sha256=c.digest(dict(fixture='source-only', generation=generation)), **extra)


def compose(owner):
    ticker = owner.stock['ticker']
    owners = {ticker: owner}
    seal = c.seal_inputs(owners, subjects=[ticker], semantics_version=c.SEMANTICS)
    return c.compose(owners, subjects=[ticker], generations={ticker: owner.generation},
        input_seal=seal, input_seal_sha256=seal['receipt_sha256'], semantics_version=c.SEMANTICS)


def test_parameterized_new_generation_same_semantics(tmp_path):
    first = compose(source(tmp_path / 'one'))
    second = compose(source(tmp_path / 'two', generation='fictional-generation-two'))
    assert first['coverage']['coverage_complete'] and second['coverage']['coverage_complete']
    assert first['coverage']['source_generations'] == ['fictional-generation-one']
    assert second['coverage']['source_generations'] == ['fictional-generation-two']
    def semantics(result):
        return [(r['metric'],r['category'],r['required'],r['coverage_disposition'],r['owner_state'],r['scope_level'])
                for r in result['coverage']['rows'][0]['categories']]
    assert semantics(first) == semantics(second)
    assert first['coverage']['receipt_sha256'] != second['coverage']['receipt_sha256']
    assert len(first['coverage']['rows'][0]['categories']) == 34
    assert first['producer']['model_authority_inputs'] == 0


def test_metric_denial_does_not_block_alternate_owner(tmp_path):
    result = compose(source(tmp_path, negative=True))
    metrics = {r['metric']: r['state'] for r in result['resolutions']['IBM']['metrics']}
    assert metrics == {'PER': 'UNUSABLE_TYPED_DENIAL', 'FORWARD_PE': 'USABLE', 'PBR': 'USABLE'}
    assert result['resolutions']['IBM']['evaluability']['evaluability_state'] == 'EVALUABLE'
    assert all(b['scope_level'] == 'METRIC_SCOPED' for b in result['census']['rows'])


@pytest.mark.parametrize('bad', ['generation', 'temporal', 'decision_version', 'field_eligibility', 'raw_hash', 'historical_model', 'source_hash'])
def test_provenance_fail_closed_even_with_new_input_seal(tmp_path, bad):
    owner = source(tmp_path)
    if bad == 'generation':
        owner = replace(owner, generation='unrelated-generation')
    elif bad == 'temporal':
        owner.stock['valuation_view']['metrics'][0]['native_snapshot']['retrieval_timestamp'] = None
    elif bad == 'decision_version':
        owner.stock['quality_view']['fact']['fields']['decision_version'] = None
    elif bad == 'field_eligibility':
        owner.stock['valuation_view']['metrics'][0]['native_snapshot'].pop('new_buyer_valuation_context_eligible')
    elif bad == 'raw_hash':
        owner.stock['valuation_view']['metrics'][0]['native_snapshot']['raw_sha256'] = ''
    elif bad == 'historical_model':
        owner.stock['core'] = {'accepted_claims': ['not a source owner']}
    else:
        owner.stock['packet_sha256'] = 'f' * 64
    with pytest.raises((ValueError, KeyError)):
        compose(owner)


@pytest.mark.parametrize('malformed', [False, True])
def test_normal_empty_identity_scope_and_malformed_fail_closed(tmp_path, malformed):
    owner = source(tmp_path, ticker='005930', empty=True)
    if malformed:
        payload(owner.availability_inputs, lambda p: p.update(output3={}))
    result = compose(owner)
    row = result['coverage']['rows'][0]
    if malformed:
        assert not row['coverage_complete'] and result['census'] is None and not result['resolutions']
        assert result['coverage']['unresolved_required_cells'] == 9
    else:
        assert row['coverage_complete']
        metric = [c for c in row['categories'] if c['metric'] == 'CURRENT_FY1_FPER']
        assert len(metric) == 11
        for cell in metric:
            if cell['coverage_disposition'] == 'PROVEN_APPLICABLE':
                assert cell['owner_field_eligibility']['positive_returned_identity'] is False
        assert {b['scope_level'] for b in result['census']['rows']} == {'METRIC_SCOPED'}
        states = {r['metric']:r['state'] for r in result['resolutions']['005930']['metrics']}
        assert states['PER'] == 'USABLE' and states['CURRENT_FY1_FPER'] == 'UNUSABLE_TYPED_DENIAL'


def test_qualified_kis_branch_covers_required_and_nonapplicable_categories():
    from app.services.kr_forward_valuation_context import KrForwardValuationView, calibration_context
    from tests.test_kr_forward_valuation_integration import view
    from tests import test_kis_exact_action_guard as actions
    original = view()
    row = deepcopy(original.kis)
    row['action'] = actions.g.compatibility_receipt(row['eps'], row['price'],
        {variant: actions.family(variant) for variant in actions.g.VARIANTS})
    row['current_fper'] = current_fper(row['eps'], row['price'], row['action'])
    typed = KrForwardValuationView.model_validate({**original.model_dump(mode='json'), 'kis': row})
    context = calibration_context(typed)
    ref = next(m['fact_ref'] for m in context['metric_states'] if m['metric'] == 'CURRENT_FY1_FPER')
    cells = [c.cells.kis_cell(req, typed.native.ticker, ref,
        {'valuation_view': typed.native.model_dump(mode='json')}, typed.kis, c.digest(context))
        for req in c.cells.requirements('CURRENT_FY1_FPER', 'DERIVED_KIS')]
    assert typed.kis['current_fper']['state'] == 'QUALIFIED'
    assert len(cells) == 11 and not any(cell['missing_fields'] for cell in cells)
    assert sum(cell['coverage_disposition'] == 'PROVEN_APPLICABLE'
        and cell['owner_state'] == 'QUALIFIED' for cell in cells) == 9
    nonapplicable = [cell for cell in cells if cell['coverage_disposition'] == 'PROVEN_NOT_APPLICABLE']
    assert {cell['category'] for cell in nonapplicable} == {'BUSINESS_SOURCE_QUALITY', 'DEPOSITARY_OR_ADR_CONVERSION'}
    assert all(cell['owner_state'] is None
        and cell['owner_field_eligibility']['metric_branch'] == 'KIS_FY1_PRICE_EPS:QUALIFIED'
        and row['current_fper']['receipt_sha256'] in cell['input_refs'] for cell in nonapplicable)


def test_input_hash_drift_and_accidental_model_api_rejected(tmp_path):
    owner = source(tmp_path)
    seal = c.seal_inputs({'IBM': owner}, subjects=['IBM'], semantics_version=c.SEMANTICS)
    owner.stock['ticker'] = 'OTHER'
    with pytest.raises(ValueError, match='source_seal_drift'):
        c.compose({'IBM': owner}, subjects=['IBM'], generations={'IBM': owner.generation},
            input_seal=seal, input_seal_sha256=seal['receipt_sha256'], semantics_version=c.SEMANTICS)
    with pytest.raises(TypeError):
        c.SourceOwners(core={'accepted': True})
    with pytest.raises(ValueError, match='source_owner_input_required'):
        c.source_binding({'core': {'accepted': True}})


def test_runtime_producer_has_no_historical_or_model_dependency():
    text = inspect.getsource(c) + inspect.getsource(c.cells)
    assert '/Users/' not in text and 'Reports/' not in text and '2026-10-02' not in text
    assert 'rev55' not in text.lower() and 'rev57' not in text.lower()
    assert not any(t in text for t in ('003690', '010120', 'IBM', 'GOOGL'))


def test_current_inputs_do_not_require_a_reviewed_source_hash_list(tmp_path, monkeypatch):
    owner = source(tmp_path)
    original = Path.read_bytes
    def changed(path):
        if path.name in {'new_buyer_input_owner.py', 'newbuyer_coverage_dataflow.json'}:
            raise AssertionError('coverage_must_not_read_source_review_allowlist')
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', changed)
    result = compose(owner)
    assert result['coverage']['coverage_complete']
    assert result['resolutions']['IBM']['evaluability']['evaluability_state'] == 'EVALUABLE'


def test_current_input_seal_rejects_legacy_dataflow_seal_without_migration(tmp_path):
    owner = source(tmp_path)
    owners = {'IBM': owner}
    current = c.seal_inputs(owners, subjects=['IBM'], semantics_version=c.SEMANTICS)
    assert current['contract'] == 'FreshSourceCoverageInputsV2'
    assert 'dataflow_sha256' not in current
    legacy_semantics = 'REV56B_CATEGORY_CELLS_PLUS_REV56C_NO_ESTIMATE_SCOPE'
    legacy = c.sealed(dict(contract='FreshSourceCoverageInputsV1', subjects=['IBM'],
        semantics_version=legacy_semantics, rows=current['rows'],
        dataflow_sha256='1' * 64, model_inputs_used=False))
    before = deepcopy(legacy)
    with pytest.raises(ValueError):
        c.compose(owners, subjects=['IBM'], generations={'IBM': owner.generation},
            input_seal=legacy, input_seal_sha256=legacy['receipt_sha256'], semantics_version=c.SEMANTICS)
    assert legacy == before
    with pytest.raises(ValueError, match='unsupported_coverage_semantics'):
        c.seal_inputs(owners, subjects=['IBM'], semantics_version=legacy_semantics)


@pytest.mark.parametrize('bad', ['native_value', 'denominator', 'price_role', 'source_method',
    'security', 'price_session'])
def test_resealed_input_cannot_change_atomic_metric_contract(tmp_path, bad):
    owner = source(tmp_path)
    view = deepcopy(owner.stock['valuation_view'])
    owner.stock['valuation_view'] = view
    metric = next(m for m in view['metrics'] if m['metric'] == 'PER')
    if bad == 'native_value':
        metric['value'] += 1
    elif bad == 'denominator':
        metric['denominator'] = 1
    elif bad == 'price_role':
        metric['numerator_role'] = 'CURRENT_PRICE'
    elif bad == 'source_method':
        metric['source_method'] = 'existing_derived_trailing_owner_scope_checked'
    elif bad == 'security':
        owner = replace(owner, security=deepcopy(owner.security))
        owner.security['canonical_security_id'] = 'unrelated-security'
    else:
        view['price_session'] = '1900-01-01'
    # A new content hash cannot make the altered typed calculation valid.
    owner.stock['input_hashes']['valuation'] = c.digest(view)
    expected = ('fresh_coverage:security_binding' if bad == 'security'
        else 'valuation_view_basis_binding_mismatch' if bad == 'price_session'
        else 'valuation_atomic_snapshot_scope_mismatch')
    with pytest.raises(ValueError, match=expected):
        compose(owner)


def unavailable_owner(tmp_path, *, native):
    from tests.test_completed_price_state import unavailable_inputs
    inputs = unavailable_inputs(tmp_path, 'IBM', native=native)
    stock = assemble_fresh_stock(**inputs)
    assert stock['status'] == 'PASS'
    return c.SourceOwners(generation=stock['fresh_run_id'], stock=stock,
        security=inputs['financial_inputs']['plan']['security'],
        collection_receipt_sha256=c.digest('fictional-current-price-collection'))


@pytest.mark.parametrize('native', [False, True])
def test_unavailable_price_branch_keeps_independent_native_metrics(tmp_path, native):
    result = compose(unavailable_owner(tmp_path, native=native))
    assert result['coverage']['coverage_complete']
    assert result['resolutions']['IBM']['evaluability']['evaluability_state'] == (
        'EVALUABLE' if native else 'ALL_RELEVANT_METRICS_UNUSABLE')
    cells = result['coverage']['rows'][0]['categories']
    for cell in cells:
        if cell['coverage_disposition'] == 'PROVEN_NOT_APPLICABLE':
            assert cell['owner_field_eligibility']['metric_branch'] == (
                'ATOMIC_PROVIDER_SNAPSHOT_CONTEXT_ONLY' if native else 'PRICE_PREREQUISITE_UNAVAILABLE')
            assert cell['owner_state'] is None
    if not native:
        assert {cell['category'] for cell in cells if cell['owner_state'] == 'DENIED'} == {
            'PRICE_TO_SECURITY_BINDING', 'VALUATION_SOURCE_QUALITY'}


def test_unavailable_price_branch_rejects_resealed_denominator(tmp_path):
    owner = unavailable_owner(tmp_path, native=False)
    view = deepcopy(owner.stock['valuation_view'])
    owner.stock['valuation_view'] = view
    next(m for m in view['metrics'] if m['metric'] == 'PER')['denominator'] = 1
    owner.stock['input_hashes']['valuation'] = c.digest(view)
    with pytest.raises(ValueError, match='price_prerequisite_coverage_scope'):
        compose(owner)


def test_producer_semantics_never_grants_current_state(tmp_path):
    result = compose(source(tmp_path))
    nonapplicable = []
    for cell in result['coverage']['rows'][0]['categories']:
        if cell['coverage_proof_kind'] == 'PRODUCER_SEMANTICS':
            nonapplicable.append(cell)
            assert cell['coverage_disposition'] == 'PROVEN_NOT_APPLICABLE'
            assert cell['owner_state'] is None and cell['required'] is False
            assert cell['owner_decision_version'] == 'CURRENT_TYPED_METRIC_BRANCH_V1'
            assert cell['owner_field_eligibility']['metric_branch'] == 'ATOMIC_PROVIDER_SNAPSHOT_CONTEXT_ONLY'
            assert cell['input_refs'] and not any(ref.endswith('.py') for ref in cell['input_refs'])
            assert 'AUDITED' not in cell['owner_decision_version']
            assert 'STATIC_CODE_DATAFLOW' not in cell['owner_temporal_scope']
    assert nonapplicable
    row = deepcopy(result['coverage']['rows'][0])
    cell = next(c for c in row['categories'] if c['coverage_proof_kind'] == 'PRODUCER_SEMANTICS')
    cell.update(coverage_disposition='PROVEN_APPLICABLE', owner_state='QUALIFIED',
        applies_to_metric_refs=[cell['metric_ref']], owner_as_of='2026-10-01')
    with pytest.raises(ValueError, match='v2_current_category_ownership_gap'):
        c.policy.metric_resolution(dict(ticker='IBM', security_id=row['canonical_security_id'],
            source_generation_id=row['source_generation'], facts=c.qualified_facts(
                {'valuation_context': result['contexts']['IBM']}, 'IBM', row['source_generation'])),
            row, result['census'])


def test_business_temporal_and_decision_metadata_cannot_be_self_sealed_into_authority(tmp_path):
    owner = source(tmp_path)
    quality = owner.stock['quality_view']
    quality['receipt']['owner_outputs'][0]['metadata']['filing_date'] = None
    quality['receipt'] = c.sealed({k:v for k,v in quality['receipt'].items() if k != 'receipt_sha256'})
    owner.stock['input_hashes']['quality'] = c.digest(quality)
    with pytest.raises(ValueError, match='business_owner_replay'):
        compose(owner)
