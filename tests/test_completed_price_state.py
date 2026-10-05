import json

import pytest

from app.services import completed_price_state as c
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.unavailable_price_valuation import parse_view
from app.services.unified_snapshot_contract import digest
from tests.completed_price_fixtures import source, reseal_final
from tests.rev10_cohort_fixtures import plan_and_securities
from tests.rev8_source_fixtures import fresh_inputs


def project(kind='available'):
    plan, securities = plan_and_securities()
    security = securities['us'][0]
    read = next(r for r in plan.reads if r.subject == security['ticker'] and r.role == 'adjusted_daily')
    src, artifacts = source(plan, security, kind=kind)
    args = dict(source=src, plan=plan, read=read, security=security,
                artifact_reader=lambda path, sha: artifacts[path])
    return args, artifacts


@pytest.mark.parametrize('kind,state', [('available', 'AVAILABLE'), ('transport', c.SOURCE_FAILED),
    ('http', c.SOURCE_FAILED), ('provider_failed', c.SOURCE_FAILED), ('missing', 'DENIED_TARGET_ROW_MISSING'),
    ('integrity', 'DENIED_TARGET_ROW_INTEGRITY'), ('field_missing', 'DENIED_TARGET_ROW_INTEGRITY')])
def test_typed_attempt_and_semantic_failures(kind, state):
    args, artifacts = project(kind)
    before = dict(artifacts)
    value = c.project_state(**args)
    assert value.state == state
    assert value.numeric_owner is not None if state == 'AVAILABLE' else value.numeric_owner is None
    assert value.raw_sha256 is None if kind == 'transport' else value.raw_sha256 is not None
    assert artifacts == before
    assert c.CurrentPriceState.model_validate(value.model_dump(mode='json')) == value


def test_missing_slot_is_not_runtime_denial():
    args, _ = project()
    args['source']['provider_plan']['descriptors'] = []
    state = c.project_state(**args)
    assert state.state == c.PLAN_GAP and not state.attempt_refs and state.raw_sha256 is None
    with pytest.raises(ValueError, match=c.PLAN_GAP):
        c.require_runtime(state)
    with pytest.raises(ValueError, match=c.PLAN_GAP):
        c.require_plan(args['source']['provider_plan'], args['plan'])


def test_no_chart_owner_promotion():
    args, _ = project()
    d = args['source']['provider_plan']['descriptors'][0]
    d['endpoint_operation'] = 'usa06012'
    with pytest.raises(ValueError):
        c.project_state(**args)


def test_unknown_receipt_error_is_not_subject_denial():
    args, artifacts = project('transport')
    reseal_final(args['source'], artifacts, lambda f: f.update(status='SYSTEMIC_STOP'))
    with pytest.raises(ValueError, match='attempt_contract_gap'):
        c.project_state(**args)
    with pytest.raises(RuntimeError):
        c.project_state(**dict(args, artifact_reader=lambda *a: (_ for _ in ()).throw(RuntimeError('systemic'))))


def test_acquired_security_binding_failure_is_scoped():
    args, _ = project()
    args['security'] = dict(args['security'], exchange='WRONG')
    state = c.project_state(**args)
    assert state.state == 'DENIED_SECURITY_OR_SESSION_BINDING'
    assert state.raw_sha256 and state.numeric_owner is None


def test_receipt_drift_and_unattempted_plan_are_not_provider_denials():
    args, artifacts = project('transport')
    reseal_final(args['source'], artifacts, lambda f: f.update(attempts=[]))
    with pytest.raises(ValueError, match='attempt_contract_gap'):
        c.project_state(**args)


def unavailable_inputs(root, ticker, kind='missing', *, native=False):
    from tests.rev28_native_fixtures import native_input
    from app.services.unified_source_policy import UnifiedSourcePolicy
    from tests.rev8_source_fixtures import POLICY
    policy = UnifiedSourcePolicy(POLICY.allowed_providers | {'finnhub', 'kiwoom_rest'})
    inputs = fresh_inputs(root, ticker, verified_identity=True, completed_price=False, policy=policy)
    tech = inputs['technical_inputs']
    security = inputs['financial_inputs']['plan']['security']
    src, artifacts = source(tech['plan'], security, kind=kind)
    inputs['technical_inputs'] = c.bind_source(tech, source=src, artifacts=artifacts, security=security)
    if native:
        inputs['valuation_inputs'] = native_input(security, start=tech['plan'].frozen_at,
            run=tech['plan'].run_id, policy=policy)
    return inputs


@pytest.mark.parametrize('native', [False, True])
def test_common_fresh_owner_carries_scoped_state_without_fake_numerator(tmp_path, native):
    result = assemble_fresh_stock(**unavailable_inputs(tmp_path, 'IBM', native=native))
    assert result['status'] == 'PASS', result['mandatory_missing']
    view = parse_view(result['valuation_view'])
    assert view.price is None and all(m.numerator is None for m in view.metrics)
    assert result['packet']['stocks'][0]['current_price_context']['contract'] == 'current-price-context-v2'
    assert result['ownership']
    assert all(m.status == ('QUALIFIED' if native else 'UNAVAILABLE') for m in view.metrics)
    assert all(m.price_dependency == ('CURRENT_PRICE_CONTEXT_ONLY' if native else 'CURRENT_PRICE_ARITHMETIC_REQUIRED') for m in view.metrics)


def test_cohort_price_denial_is_subject_local(tmp_path):
    rows = [assemble_fresh_stock(**unavailable_inputs(tmp_path/t, t, kind))
            for t, kind in [('IBM', 'available'), ('MU', 'missing'), ('GOOGL', 'available')]]
    assert [r['status'] for r in rows] == ['PASS'] * 3
    assert [r['valuation_view']['price'] is None for r in rows] == [False, True, False]


def test_valid_price_bad_chart_keeps_domains_separate(tmp_path):
    from app.services.unified_run_artifacts import sha256_bytes
    from app.services.unified_snapshot_contract import encoded
    inputs = unavailable_inputs(tmp_path, 'IBM', 'available')
    tech = inputs['technical_inputs']
    receipt = tech['receipts']['adjusted_daily']
    rows = json.loads(tech['artifacts'][receipt['normalized_artifact']])
    rows[-1]['close'] = rows[-1]['high'] + 1
    # Keep normalized/raw fixture bytes and their receipt hashes consistent.
    raw = encoded(dict(return_code=0, result_list=rows))
    page = receipt['pages'][0]
    tech['artifacts'][page['artifact']] = raw
    page['source_sha256'] = sha256_bytes(raw)
    normalized = encoded(rows)
    tech['artifacts'][receipt['normalized_artifact']] = normalized
    receipt['normalized_sha256'] = sha256_bytes(normalized)
    tech['expected_hashes']['receipts'] = digest(tech['receipts'])
    src = tech.pop('completed_price_source')
    price_names = set(tech['artifacts']) - {r['normalized_artifact'] for r in tech['receipts'].values()} - {
        p['artifact'] for r in tech['receipts'].values() for p in r['pages']}
    artifacts = {k: tech['artifacts'].pop(k) for k in price_names}
    inputs['technical_inputs'] = c.bind_source(tech, source=src, artifacts=artifacts,
                                               security=inputs['financial_inputs']['plan']['security'])
    result = assemble_fresh_stock(**inputs)
    assert result['status'] == 'PASS'
    stock = result['packet']['stocks'][0]
    assert stock['current_price_state']['state'] == 'AVAILABLE' and stock['current_price_context']['current_price'] == 105
    assert stock['technical_chart_state']['state'] == 'DENIED_TARGET_ROW_INTEGRITY'
    assert stock['technical_chart_state']['timing_state'] == 'UNRESOLVED'
    assert stock['technical_chart_state']['integrity']['issues']


def test_technical_denial_cohort_continues_through_all_subjects(tmp_path):
    processed = []
    for ticker in ('MU', 'IBM', 'GOOGL'):
        if ticker == 'IBM':
            test_valid_price_bad_chart_keeps_domains_separate(tmp_path/ticker)
        else:
            row = assemble_fresh_stock(**unavailable_inputs(tmp_path/ticker, ticker, 'available'))
            assert row['status'] == 'PASS' and row['current_price_state']['state'] == 'AVAILABLE'
        processed.append(ticker)
    assert processed == ['MU', 'IBM', 'GOOGL']


def test_full_future_plan_has_exact_budgeted_14_close_slots():
    from tests.test_r9_rev11_full_plan import compiled
    stock, _, out = compiled()
    slots = c.require_plan(out['plan'], stock)
    assert len(slots) == len({d.subject for d in slots}) == 14
    assert all(d.mandatory and d.endpoint_operation == 'usa20590' and d.max_transport_attempts == 3 for d in slots)
    assert len([d for d in out['plan'].descriptors if d.consumer_role.startswith('stock:')]) >= 88


def test_completed_close_collection_uses_sealed_slots_and_budget(tmp_path):
    import asyncio
    from types import SimpleNamespace
    import httpx
    from app.services.sealed_fresh_dispatch import SealedDispatcher
    from app.services.sealed_source_transport import SealedSourceTransport
    from app.services.sealed_completed_price import collect_one
    from tests.test_r9_rev11_full_plan import compiled
    from tests.test_r9_rev11_sealed_dispatch import ROOT
    stock, args, out = compiled()
    calls = []
    def mock(request):
        calls.append((request.url.path, request.headers.get('api-id')))
        return httpx.Response(200, json={'return_code': 0, 'token': 'fixture-token',
            'expires_dt': '20990101000000'} if request.url.path == '/oauth2/token' else
            {'return_code': 0, 'result_list': []})
    run = SealedDispatcher(plan=out['plan'], root=tmp_path/'run', rev10_receipt=ROOT,
        owners=out['owners'], config_identities=args['config_identities'],
        credential_presence={p: True for p in args['config_identities']}, secrets=('PLAN_CREDENTIAL', 'fixture-token'))
    transport = SealedSourceTransport(run, httpx.MockTransport(mock), providers={'kiwoom'})
    settings = SimpleNamespace(kiwoom_app_key='PLAN_CREDENTIAL', kiwoom_secret_key='PLAN_CREDENTIAL',
        kiwoom_rest_base_url='https://api.kiwoom.com', kiwoom_rest_request_interval_seconds=0)
    slots = c.require_plan(out['plan'], stock)
    async def execute():
        for slot in slots:
            result = await collect_one(slot=slot, settings=settings, sealed=transport)
            assert result['status'] == 'PASS'
    asyncio.run(execute())
    assert calls.count(('/api/us/mrkcond', 'usa20590')) == 14
    assert calls.count(('/oauth2/token', None)) == 1
    assert len(run.used) == 15


def test_plan_gap_cannot_assemble_before_model(tmp_path):
    with pytest.raises(ValueError, match=c.PLAN_GAP):
        assemble_fresh_stock(**fresh_inputs(tmp_path, 'IBM', completed_price=False))


def test_unavailable_descriptor_preserves_source_and_rejects_hash_drift(tmp_path):
    from scripts.r2b_r9_full_fresh_requalification import load_stock_inputs
    from tests.rev9_source_fixtures import write_descriptor
    inputs = unavailable_inputs(tmp_path/'raw', 'IBM')
    descriptor = write_descriptor(tmp_path, inputs)
    loaded = load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])
    assert assemble_fresh_stock(**inputs) == assemble_fresh_stock(**loaded)
    descriptor['completed_price_source']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='artifact_hash_mismatch'):
        load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])


@pytest.mark.parametrize('native', [False, True])
def test_unavailable_price_through_actual_core_a_b_and_frozen_b2_builder(tmp_path, native):
    from types import SimpleNamespace
    from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
    from scripts.r9_offline_stage_replay import replay_stages, core_inputs, a_inputs
    from scripts import newbuyer_b2_shadow as v1
    from scripts import newbuyer_b2_v2_shadow as v2
    from scripts.newbuyer_b2_v2_coverage import SourceOwners
    from tests.test_newbuyer_b2_v2_coverage import compose
    from tests.rev10_stage_fixtures import synthetic_outputs
    from tests.test_newbuyer_b2_contract import instantiate
    from app.services.provider_valuation_calibration_context import calibration_context
    from app.services.unavailable_price_valuation import shadow_request_context
    inputs = unavailable_inputs(tmp_path, 'IBM', native=native)
    result = prepare_fresh_subject(inputs, execution_generation_id='fictional-price-denial')
    assert result['readiness']['status'] == 'PASS' and result['prepared']['mode'] == 'EVIDENCE_BASED'
    raw = synthetic_outputs(result, 'fictional-price-denial', inputs['technical_inputs']['local_seed'])
    proof = replay_stages(result, 'fictional-price-denial', raw)
    assert proof['status'] == 'PASS'
    assert '정식 종가 확인 불가' in proof['capture']['prepared_text']
    state = a_inputs(result, core_inputs(result, 'fictional-price-denial', raw['core']), raw['a'])
    state['b_context']['valuation_context'] = calibration_context(result['stock']['valuation_view'])
    request = v1.build_request(settings=SimpleNamespace(newbuyer_qualified_valuation_shadow=True),
        context=shadow_request_context(state['b_context'], result['stock']),
        accepted=proof['accepted_outputs']['b'], core=state['core'],
        pass_a=state['a'], source_generation_id=result['stock']['fresh_run_id'])
    subject = request['subject']
    assert subject['current_price']['value'] is None
    owners = SourceOwners(generation=result['stock']['fresh_run_id'], stock=result['stock'],
        security=inputs['financial_inputs']['plan']['security'], collection_receipt_sha256=digest('fixture'))
    coverage = compose(owners)
    records = [dict(ticker='IBM', claim_ref=r['claim_ref'], effect='CONFIDENCE_ONLY',
        existing_materiality=r['claim']['materiality'], legacy_claim_sha256=digest(r))
        for r in subject['frozen_business_claims'] if r['claim_ref'] in subject['capability']['confidence']]
    req = v2.build_request(enabled=True, v1_request=request, coverage=coverage['coverage'],
        census=coverage['census'], coverage_sha=coverage['coverage']['receipt_sha256'],
        census_sha=coverage['census']['receipt_sha256'], legacy_records=records)
    payload = v2.provider_payload(req, expected_request_sha256=req['request_sha256'])
    assert req['provider_dialect_validation']['status'] == 'PASS'
    assert payload['input']['valuation_evaluability']['evaluability_state'] == (
        'EVALUABLE' if native else 'ALL_RELEVANT_METRICS_UNUSABLE')
    assert payload['input']['timing_state'] == 'UNRESOLVED'
    for branch in req['output_schema']['anyOf']:
        output = {'new_buyer_shadow': instantiate(branch)}
        assert v2.validate_result(output, req, expected_request_sha256=req['request_sha256'])['status'] == 'PASS'


@pytest.mark.parametrize('mutation', ['security', 'time', 'horizon', 'source'])
def test_native_metric_independent_negative_controls(tmp_path, mutation):
    from app.services.unified_run_artifacts import sha256_bytes
    from app.services.unified_snapshot_contract import encoded
    inputs = unavailable_inputs(tmp_path, 'IBM', native=True)
    native = inputs['valuation_inputs']
    if mutation == 'source':
        native['receipt']['security_sha256'] = '0' * 64
        with pytest.raises(ValueError, match='native_snapshot_source_receipt_mismatch'):
            assemble_fresh_stock(**inputs)
        return
    body = json.loads(native['raw'])
    if mutation == 'security':
        body['shareClass'] = 'unowned_class'
    elif mutation == 'time':
        body['metricAsOf'] = '2000-01-01'
    else:
        body['metric']['forwardPE'] = None
    native['raw'] = encoded(body)
    native['receipt']['source_sha256'] = sha256_bytes(native['raw'])
    view = parse_view(assemble_fresh_stock(**inputs)['valuation_view'])
    assert view.price is None
    if mutation == 'horizon':
        assert next(m for m in view.metrics if m.metric == 'FORWARD_PE').status == 'UNAVAILABLE'
        assert next(m for m in view.metrics if m.metric == 'PER').status == 'QUALIFIED'
    else:
        assert all(m.status == 'UNAVAILABLE' for m in view.metrics)
    forged = view.model_dump(mode='json')
    forged['metrics'][0]['numerator'] = 1
    with pytest.raises(ValueError):
        parse_view(forged)
