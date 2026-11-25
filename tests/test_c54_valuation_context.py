"""Synthetic native valuation wires through existing coverage, B2 and renderer.

These tests exercise input availability and economic-judgment capabilities;
they do not certify a real stock's attractiveness or call a provider/model.
"""
from copy import deepcopy
from zoneinfo import ZoneInfo

import pytest

from app.services import new_buyer_input_owner as base_owner
from app.services import new_buyer_request_owner as owner
from app.services import new_buyer_v2_contract as contract
from app.services.current_fresh_valuation import CurrentValuationView
from app.services.detailed_stock_message_service import _valuation_rows
from app.services.provider_valuation_calibration_context import calibration_context
from app.services.unified_snapshot_contract import digest
from tests.test_newbuyer_b2_shadow import inputs as base_inputs
from tests.test_newbuyer_b2_v2 import outputs, validate
from tests.test_newbuyer_b2_v2_coverage import compose, source


def _multiples(body, *, per=None, pbr=None, forward=None):
    if 'metric' in body:
        body['metric'].update(peTTM=per, pbQuarterly=pbr, forwardPE=forward)
    else:
        body.update(per=per, pbr=pbr)


def _request(source_owner):
    result = compose(source_owner)
    context = calibration_context(source_owner.stock['valuation_view'])
    args = base_inputs(context)
    # A supplied business observation remains separate from valuation facts.
    core = args['core']
    core['atomic_claims'][0]['claim'] = dict(
        text='Fictional supplied business observation', evidence_refs=['source:business'])
    core['binding_sha256'] = digest(dict(atomic=core['atomic_claims'], effects=core['effects']))
    args['context']['r2_policy_capability']['core_binding_sha256'] = core['binding_sha256']
    before = deepcopy({k: v for k, v in args.items() if k != 'settings'})
    base = base_owner.build_request(**args)
    request = owner.build_request(enabled=True, v1_request=base,
        coverage=result['coverage'], census=result['census'],
        coverage_sha=result['coverage']['receipt_sha256'],
        census_sha=result['census']['receipt_sha256'], legacy_records=[])
    assert {k: v for k, v in args.items() if k != 'settings'} == before
    return request, base['subject']


@pytest.mark.parametrize('ticker', ['IBM', '005930'])
def test_native_pbr_reaches_b2_without_separate_asset_permission(tmp_path, ticker):
    current = source(tmp_path, ticker=ticker,
        mutate_native=lambda body: _multiples(body, pbr=0.7))
    before = digest(current.stock)
    request, subject = _request(current)
    model = request['provider_request']['input']
    facts = model['qualified_usable_valuation_facts']
    assert len(facts) == 1
    fact = next(iter(facts.values()))
    assert fact['metric'] == 'PBR' and fact['metadata']['value'] == 0.7
    assert fact['source_kind'] == 'ATOMIC_PROVIDER_SNAPSHOT'
    assert 'asset_relevance_proven' not in fact
    assert model['valuation_evaluability']['evaluability_state'] == 'EVALUABLE'
    assert not model['all_metrics_unusable_proof_ref']
    assert {row['metric']: row['state'] for row in
        request['backend_audit']['metric_resolution']}['PBR'] == 'USABLE'
    assert subject['frozen_overall'] == 'BUY'
    assert subject['frozen_holder'] == {'holder': 'HOLDABLE'}
    assert subject['absolute_discount'] is None
    assert not {'EPS', 'BPS', 'FY1_EPS'} & {f['metric'] for f in facts.values()}
    assert digest(current.stock) == before


@pytest.mark.parametrize('pbr', [0.7, 5.0])
def test_usable_pbr_does_not_force_supportive_or_permit_free_unresolved(tmp_path, pbr):
    request, _ = _request(source(tmp_path,
        mutate_native=lambda body: _multiples(body, pbr=pbr)))
    rows = outputs(request)
    assert {r['valuation_context']['state'] for r in rows} == {
        'SUPPORTIVE', 'NEUTRAL', 'BURDENSOME'}
    neutral = next(r for r in rows if r['valuation_context']['state'] == 'NEUTRAL')
    assert neutral['new_buyer'] == 'WAIT' and neutral['reason_class'] == 'VALUATION_NEUTRAL'
    assert validate(neutral, request)['status'] == 'PASS'
    assert validate(neutral, request)['economic_correctness_proven'] is False
    rejected = deepcopy(neutral)
    rejected['valuation_context']['state'] = 'UNRESOLVED'
    assert validate(rejected, request)['status'] == 'FAIL'
    prompt = request['provider_request']['prompt']
    assert 'A low PBR alone does not establish' in prompt
    assert 'profitability/ROE or financial context' in prompt
    assert 'Do not invent those observations' in prompt


def test_unresolved_requires_actual_unusable_per_pbr_and_forward(tmp_path):
    request, _ = _request(source(tmp_path, mutate_native=_multiples))
    model = request['provider_request']['input']
    assert not model['qualified_usable_valuation_facts']
    assert model['valuation_evaluability']['evaluability_state'] == 'ALL_RELEVANT_METRICS_UNUSABLE'
    assert {r['metric']: r['state'] for r in request['backend_audit']['metric_resolution']} == {
        'PER': 'UNUSABLE_TYPED_DENIAL', 'PBR': 'UNUSABLE_TYPED_DENIAL',
        'FORWARD_PE': 'UNUSABLE_TYPED_DENIAL'}
    rows = outputs(request)
    assert len(rows) == 1 and rows[0]['valuation_context']['state'] == 'UNRESOLVED'
    assert rows[0]['new_buyer'] == 'WAIT' and validate(rows[0], request)['status'] == 'PASS'


def test_missing_pbr_does_not_remove_per_or_user_approved_fy1(tmp_path):
    request, _ = _request(source(tmp_path,
        mutate_native=lambda body: _multiples(body, per=12.3, forward=7)))
    model = request['provider_request']['input']
    facts = {f['metric']: f for f in model['qualified_usable_valuation_facts'].values()}
    assert set(facts) == {'PER', 'FORWARD_PE'}
    assert facts['PER']['metadata']['value'] == 12.3
    forward = facts['FORWARD_PE']['metadata']
    assert forward['value'] == 7 and forward['horizon_authority'] == 'USER_AUTHORIZED_PRODUCT_POLICY'
    assert forward['canonical_horizon'] == 'FY1' and forward['provider_horizon'] is None
    assert model['valuation_evaluability']['evaluability_state'] == 'EVALUABLE'
    assert contract.states(model) == ['SUPPORTIVE', 'NEUTRAL', 'BURDENSOME']


@pytest.mark.parametrize('ticker', ['IBM', '005930'])
def test_unknown_metric_date_is_labeled_query_time_not_metric_date(tmp_path, ticker):
    value = CurrentValuationView.model_validate(source(tmp_path, ticker=ticker).stock['valuation_view'])
    before = value.model_dump(mode='json')
    rows = _valuation_rows(value)
    by_metric = {m.metric: m for m in value.metrics}
    for row in rows:
        metric = by_metric[row.row_id.split(':')[-1]]
        if metric.native_snapshot is None or not metric.display_eligible:
            continue
        native = metric.native_snapshot
        queried = native.retrieval_timestamp.astimezone(ZoneInfo('Asia/Seoul'))
        assert native.metric_asof is None
        assert '지표 기준일 미제공 · 조회 ' + queried.strftime('%Y-%m-%d %H:%M KST') in row.text
        assert '지표 기준일 ' + queried.date().isoformat() not in row.text
    assert value.model_dump(mode='json') == before
    if ticker == 'IBM':
        assert any('fPER(FY1)' in row.text and 'FY1 제품 정책 기준' in row.text for row in rows)


def test_explicit_provider_metric_date_is_displayed_as_metric_date(tmp_path):
    def provided_date(body):
        body['metricAsOf'] = '2026-09-26'
    value = CurrentValuationView.model_validate(
        source(tmp_path, mutate_native=provided_date).stock['valuation_view'])
    rows = _valuation_rows(value)
    for metric in (m for m in value.metrics if m.metric in {'PER', 'PBR'}):
        row = next(r for r in rows if r.row_id.endswith(':' + metric.metric))
        assert metric.native_snapshot.metric_asof.isoformat() == '2026-09-26'
        assert '지표 기준일 2026-09-26' in row.text
        assert '기준일 미제공' not in row.text and '조회 ' not in row.text


def test_existing_kis_current_fy1_scope_and_dated_research_are_preserved():
    from app.services.kr_forward_valuation_context import calibration_context as kr_context
    from app.services.kr_forward_valuation_message import valuation_rows
    from tests.test_kr_forward_valuation_integration import view
    current = view()
    subject = base_owner.build_request(**base_inputs(kr_context(current)))['subject']
    facts = list(subject['facts'].values())
    assert len(facts) == 1 and facts[0]['metric'] == 'CURRENT_FY1_FPER'
    assert facts[0]['source_kind'] == 'KIS_HOUSE_RESEARCH_NOT_CONSENSUS'
    assert facts[0]['metadata']['estimate_date'] and facts[0]['metadata']['price_date']
    rendered = '\n'.join(row.text for row in valuation_rows(current))
    assert '2026-09-30 정규장 종가 기준' in rendered and '2026-07-01 추정' in rendered
    assert 'KIS 리서치 fPER(FY1)' in rendered
