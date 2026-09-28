import asyncio
from copy import deepcopy
from datetime import timedelta

import pytest

from app.services.current_fresh_valuation import CurrentMultiple, CurrentValuationView, valuation_numeric_bindings
from app.services.detailed_stock_message_service import _valuation_rows
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_source_policy import UnifiedSourcePolicy
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from scripts.m12ds_r4_offline_capture import capture_payload
from tests.rev8_source_fixtures import fresh_inputs, POLICY


def valuation_inputs(root, *, current_only=True, negative=False):
    policy = UnifiedSourcePolicy(POLICY.allowed_providers | {'finnhub'})
    inputs = fresh_inputs(root, 'IBM', current_only=current_only, verified_identity=True, policy=policy)
    plan = inputs['technical_inputs']['plan']
    session = next(r.latest_completed_session for r in plan.reads if r.subject == 'IBM')
    payload = dict(symbol='IBM', metricAsOf=session, currency='USD', metric={
        'epsTTM': -2 if negative else 2, 'peTTM': None if negative else 10,
        'pbQuarterly': 1.5, 'forwardPE': 8})
    raw = encoded(payload)
    receipt = dict(provider='finnhub', run_id=plan.run_id, acquisition_class='FRESH_CURRENT_RUN',
        security_sha256=digest(inputs['financial_inputs']['plan']['security']), source_sha256=sha256_bytes(raw),
        http_status=200, requested_at=plan.frozen_at.isoformat(),
        received_at=(plan.frozen_at + timedelta(seconds=2)).isoformat(),
        request=dict(method='GET', route='https://finnhub.io/api/v1/stock/metric', params={'symbol':'IBM', 'metric':'all'}))
    inputs['valuation_inputs'] = dict(raw=raw, receipt=receipt, policy=policy, run_started_at=plan.frozen_at,
        cutoff=plan.frozen_at + timedelta(minutes=1))
    return inputs


@pytest.mark.parametrize('negative', [False, True])
def test_native_metrics_cannot_bootstrap_direction_and_detailed_unknown_capture(tmp_path, negative):
    from tests.test_r9_rev9_context_only import unknown_decision
    from app.services.detailed_stock_message_service import build_unknown_plan
    from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
    from app.services.accepted_decision_v2_service import render_accepted_v2_production
    inputs = valuation_inputs(tmp_path, negative=negative)
    result = prepare_fresh_subject(inputs, execution_generation_id='offline-valuation')
    assert result['readiness']['decision_mode'] == 'UNKNOWN_LIMIT'
    source = result['stock']
    view = CurrentValuationView.model_validate(source['valuation_view'])
    per, pbr, forward = view.metrics
    assert per.status == ('NOT_MEANINGFUL' if negative else 'QUALIFIED')
    assert pbr.status == 'QUALIFIED' and pbr.value == 1.5
    assert forward.status == 'UNAVAILABLE' and forward.estimate_horizon is None
    assert all(not row.overall_direction_use for row in view.metrics)
    assert not per.entry_use_eligible and per.numerator_role == 'CURRENT_PRICE_CONTEXT_ONLY'
    bindings = valuation_numeric_bindings(view)
    assert bindings['PBR']['registry']['semantic_type'] == 'price_to_book'
    assert bindings['PBR']['registry']['value'] == pbr.value
    plan = build_unknown_plan(source_stock=source, source_authority=result['authority'],
        local_seed=inputs['technical_inputs']['local_seed'], decision=unknown_decision(result['prepared']),
        execution_generation_id='offline-valuation', valuation=view)
    ep = DecisionEvidencePacket.model_validate(source['evidence_packet'])
    rendered = render_accepted_v2_production(ep, plan)
    assert ('PER: N/M' if negative else 'PER: 10.00배') in rendered.text
    assert 'PBR: 1.50배' in rendered.text and 'fPER: 판단 자료 부족' in rendered.text
    capture = asyncio.run(capture_payload(dict(type='thesis_assessment', text=rendered.text,
                                              ticker='IBM', use_llm=False)))
    assert capture['prepared_text'] == rendered.text and capture['network_requests'] == 0
    assert all(row.numeric_registry_keys for row in plan.rows
               if row.section == 'valuation' and '배' in row.text)


@pytest.mark.parametrize('change', ['old_run', 'old_read', 'symbol', 'hash', 'provider', 'security', 'route'])
def test_native_receipt_fail_closed(tmp_path, change):
    inputs = valuation_inputs(tmp_path)
    native = inputs['valuation_inputs']
    receipt = native['receipt']
    if change == 'old_run':
        receipt['run_id'] = 'old'
    elif change == 'old_read':
        receipt['requested_at'] = '2025-01-01T00:00:00+00:00'
    elif change == 'symbol':
        receipt['request']['params']['symbol'] = 'OTHER'
    elif change == 'hash':
        native['raw'] = b'{}'
    elif change == 'provider':
        receipt['provider'] = 'alpha_vantage'
    elif change == 'security':
        receipt['security_sha256'] = '0' * 64
    else:
        receipt['request']['route'] = 'https://other.invalid'
    with pytest.raises(ValueError, match='fresh_native_valuation'):
        prepare_fresh_subject(inputs, execution_generation_id='offline-valuation')


@pytest.mark.parametrize('change', ['currency', 'share_class', 'old_metric', 'missing_currency', 'missing_asof'])
def test_native_semantic_incompatibility_is_unavailable(tmp_path, change):
    import json
    inputs = valuation_inputs(tmp_path)
    native = inputs['valuation_inputs']
    payload = json.loads(native['raw'])
    if change.startswith('missing_'):
        del payload['currency' if change == 'missing_currency' else 'metricAsOf']
    else:
        payload[{'currency':'currency', 'share_class':'shareClass', 'old_metric':'metricAsOf'}[change]] = {
            'currency':'KRW', 'share_class':'preferred', 'old_metric':'2024-01-01'}[change]
    native['raw'] = encoded(payload)
    native['receipt']['source_sha256'] = sha256_bytes(native['raw'])
    result = prepare_fresh_subject(inputs, execution_generation_id='offline-valuation')
    assert all(m['status'] == 'UNAVAILABLE' for m in result['stock']['valuation_view']['metrics'])


@pytest.mark.parametrize('change', ['negative_value', 'no_source', 'no_date', 'fake_nm', 'future_horizon_missing'])
def test_typed_state_cannot_display_unowned_value(change):
    row = dict(metric='PER', status='QUALIFIED', value=10, numerator=20, denominator=2,
        denominator_period='TTM', publication_date='2026-09-25', latest_published=True,
        source_method='finnhub_native_current_metric', input_hashes=('a'*64,), denial_reason=None,
        display_eligible=True, entry_use_eligible=True)
    if change == 'negative_value':
        row['value'] = -1
    elif change == 'no_source':
        row['input_hashes'] = ()
    elif change == 'no_date':
        row['publication_date'] = None
    elif change == 'fake_nm':
        row.update(status='NOT_MEANINGFUL', value=None)
    else:
        row['metric'] = 'fPER'
    with pytest.raises(ValueError):
        CurrentMultiple(**row)


def test_section_rejects_resigned_numerator_mismatch(tmp_path):
    result = prepare_fresh_subject(valuation_inputs(tmp_path), execution_generation_id='offline-valuation')
    value = deepcopy(result['stock']['valuation_view'])
    value['metrics'][0]['numerator'] = 99
    with pytest.raises(ValueError, match='numerator_mismatch'):
        _valuation_rows(CurrentValuationView.model_validate(value))
