"""Completed adjusted bars, independent regular prices, and unchanged B2 rights."""
from copy import deepcopy
from datetime import date
import json

import pytest

from app.services import completed_price_state as state_owner
from app.services.completed_session_current_price import project_completed_price
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.unified_snapshot_contract import digest
from tests.completed_price_fixtures import source
from tests.rev8_source_fixtures import fresh_inputs
from tests.test_completed_price_state import unavailable_inputs
from tests.test_completed_session_current_price import bind_rows, price_inputs


@pytest.mark.parametrize('mutation', [
    {'close': 89}, {'close': 111}, {'open': 111}, {'low': 111},
    {'close': None}, {'close': True}, {'close': 0}, {'close': -1},
    {'close': 'NaN'}, {'close': 'Infinity'}, {'volume': -1},
    {'bar_state': 'PARTIAL'}, {'bar_state': 'IN_PROGRESS'},
    {'is_partial': True}, {'complete': False},
])
def test_target_invalid_or_partial_is_never_clamped(mutation):
    args = price_inputs(old={})
    rows = json.loads(args['artifact_reader']('rows', args['receipt']['normalized_sha256']))
    rows[-1].update(mutation)
    projection = project_completed_price(**bind_rows(args, rows))
    assert projection.availability == 'UNAVAILABLE'
    assert projection.current_price is projection.price_as_of is projection.selected_row is None
    assert rows[-1].items() >= mutation.items()


def test_timestamp_not_relabelled_and_future_is_not_target():
    for field in ('2026-09-22T16:00:00-04:00', '2026-09-22T16:00:00'):
        args = price_inputs()
        rows = json.loads(args['artifact_reader']('rows', args['receipt']['normalized_sha256']))
        rows[-1]['date'] = field
        projection = project_completed_price(**bind_rows(args, rows))
        assert projection.availability == 'UNAVAILABLE'
        assert 'TARGET_ROW_NOT_EXACT_SESSION_DATE' in projection.denial_reasons
    args = price_inputs(later={})
    rows = json.loads(args['artifact_reader']('rows', args['receipt']['normalized_sha256']))[1:]
    assert project_completed_price(**bind_rows(args, rows)).current_price is None


@pytest.mark.parametrize('field,value', [('currency', 'KRW'), ('ticker', 'OTHER'),
    ('canonical_security_id', 'OTHER'), ('exchange', 'WRONG')])
def test_security_identity_and_currency_are_exact(field, value):
    args = price_inputs()
    args['security'] = dict(args['security'], **{field: value})
    with pytest.raises(ValueError, match='security_currency_basis'):
        project_completed_price(**args)


@pytest.mark.parametrize('field,value', [('api_id', 'usa20590'), ('adjusted', False)])
def test_regular_quote_cannot_masquerade_as_adjusted_role(field, value):
    args = price_inputs()
    old = args['read']
    args['read'] = old.model_copy(update={field: value})
    args['plan'] = args['plan'].model_copy(update={'reads': tuple(
        args['read'] if r == old else r for r in args['plan'].reads)})
    with pytest.raises(ValueError, match='source_role'):
        project_completed_price(**args)


def test_raw_and_normalized_hashes_remain_mandatory():
    for mutate in ('raw', 'normalized'):
        args = price_inputs()
        if mutate == 'raw':
            args['receipt']['pages'][0]['source_sha256'] = '0' * 64
        else:
            args['receipt']['normalized_sha256'] = '0' * 64
        with pytest.raises((ValueError, AssertionError)):
            project_completed_price(**args)


@pytest.mark.parametrize('field,value', [('stk_cd', 'OTHER'), ('stex_tp', 'WRONG'),
    ('upd_stkpc_tp', '0')])
def test_sealed_wire_symbol_exchange_and_adjustment_not_inferred(field, value):
    args = price_inputs()
    page = args['receipt']['pages'][0]
    page['request']['payload'][field] = value
    page['request_sha256'] = digest(page['request'])
    with pytest.raises(ValueError, match='stock_page_.*mismatch'):
        project_completed_price(**args)


def test_naive_receipt_time_is_not_assumed_utc():
    args = price_inputs()
    args['receipt']['completed_at'] = '2026-09-23T08:10:00'
    with pytest.raises(ValueError, match='receipt_time'):
        project_completed_price(**args)


def bound_inputs(root, *, kind='available', value=105, native=False):
    from app.services.unified_source_policy import UnifiedSourcePolicy
    from tests.rev8_source_fixtures import POLICY
    policy = UnifiedSourcePolicy(POLICY.allowed_providers | {'finnhub', 'kiwoom_rest'})
    inputs = fresh_inputs(root, 'IBM', verified_identity=True, completed_price=False, policy=policy)
    tech = inputs['technical_inputs']
    security = inputs['financial_inputs']['plan']['security']
    src, artifacts = source(tech['plan'], security, value=value, kind=kind)
    inputs['technical_inputs'] = state_owner.bind_source(tech, source=src,
        artifacts=artifacts, security=security)
    if native:
        from tests.rev28_native_fixtures import native_input
        inputs['valuation_inputs'] = native_input(security, start=tech['plan'].frozen_at,
            run=tech['plan'].run_id, policy=policy)
    return inputs


@pytest.mark.parametrize('kind', ['available', 'missing'])
def test_healthy_adjusted_price_survives_independent_regular_denial(tmp_path, kind):
    inputs = bound_inputs(tmp_path, kind=kind)
    result = assemble_fresh_stock(**inputs)
    stock = result['packet']['stocks'][0]
    reference = result['completed_bar_reference_price']
    assert result['status'] == 'PASS'
    assert reference['availability'] == 'AVAILABLE'
    assert stock['current_price_context']['current_price'] == reference['current_price']
    assert stock['current_price_context']['price_basis'] == 'adjusted_close'
    assert result['completed_session_current_price'] == reference
    assert stock['completed_bar_reference_price']['realtime'] is False
    assert stock['completed_bar_reference_price']['exchange_certified'] is False
    # Legacy fixtures contain weekend daily rows: keep the valid price, not unsafe W/M.
    assert not stock['chart_context']['available']
    assert inputs['technical_inputs']['components']['completed_bar_reference_chart_qualified'] is False
    assert all(m['status'] == 'UNAVAILABLE' for m in result['valuation_view']['metrics'])


@pytest.mark.parametrize('regular', [105, 999, None])
def test_independent_price_comparison_does_not_prove_conversion(tmp_path, regular):
    if regular is None:
        probe = fresh_inputs(tmp_path, 'IBM', verified_identity=True, completed_price=False)
        tech = probe['technical_inputs']
        receipt = tech['receipts']['adjusted_daily']
        regular = json.loads(tech['artifacts'][receipt['normalized_artifact']])[-1]['close']
        tmp_path = tmp_path / 'equal'
    result = assemble_fresh_stock(**bound_inputs(tmp_path, value=regular))
    stock = result['packet']['stocks'][0]
    comparison = stock['independent_price_basis_comparison']
    assert stock['current_price_context']['price_basis'] == 'adjusted_close'
    equal = stock['current_price_context']['current_price'] == regular
    assert comparison['classification'] == ('SAME_VALUE_DISTINCT_DECLARED_BASIS' if equal
        else 'DIFFERENT_VALUES_DISTINCT_DECLARED_BASIS')
    assert comparison['basis_equivalence_proven'] is False
    assert comparison['corporate_action_conversion'] == 'NOT_PROVEN_NOT_INFERRED'
    assert result['current_price_state']['numeric_owner']['current_price'] == regular


@pytest.mark.parametrize('regular', ['available', 'missing'])
def test_invalid_adjusted_price_keeps_only_independent_fallback(tmp_path, regular):
    inputs = unavailable_inputs(tmp_path, 'IBM', regular, native=True)
    result = assemble_fresh_stock(**inputs)
    stock = result['packet']['stocks'][0]
    assert result['completed_bar_reference_price']['availability'] == 'UNAVAILABLE'
    assert not stock['chart_context']['available']
    assert stock['technical_chart_state']['timing_state'] == 'UNRESOLVED'
    assert stock['current_price_context']['current_price'] == (105 if regular == 'available' else None)
    for metric in result['valuation_view']['metrics']:
        assert metric['status'] == 'QUALIFIED'
        assert metric['value'] in (12.3, 1.5, 7.0)
        if regular == 'missing':
            assert metric['numerator'] is None
            assert metric['price_dependency'] == 'CURRENT_PRICE_CONTEXT_ONLY'
        else:
            assert metric['numerator'] == 105
            assert metric['numerator_role'] == 'CURRENT_PRICE_CONTEXT_ONLY'


def test_native_ratios_survive_without_adjusted_unadjusted_denominator_conversion(tmp_path):
    result = assemble_fresh_stock(**bound_inputs(tmp_path, native=True, kind='missing'))
    assert result['completed_bar_reference_price']['availability'] == 'AVAILABLE'
    assert [m['value'] for m in result['valuation_view']['metrics']] == [12.3, 1.5, 7.0]
    assert all(m['status'] == 'QUALIFIED' and m['denominator'] is None
        and m['numerator_role'] == 'CURRENT_PRICE_CONTEXT_ONLY'
        and m['source_method'] == 'provider_native_latest_snapshot'
        for m in result['valuation_view']['metrics'])


def test_component_tamper_and_unrelated_error_not_swallowed(tmp_path, monkeypatch):
    inputs = bound_inputs(tmp_path)
    tech = inputs['technical_inputs']
    from app.services import unified_stock_anomaly_scope as scope
    from app.services.unified_stock_acquisition import decode_owned_role
    from app.services.unified_stock_owner import assemble_stock
    daily = next(r for r in tech['plan'].reads if r.subject == 'IBM' and r.role == 'adjusted_daily')
    reader = lambda path, expected: tech['artifacts'][path]
    roles = {r.role: decode_owned_role(tech['plan'], r, tech['receipts'][r.role], reader)
        for r in tech['plan'].reads if r.subject == 'IBM'}
    security = inputs['financial_inputs']['plan']['security']
    projection = project_completed_price(plan=tech['plan'], read=daily,
        receipt=tech['receipts'][daily.role], artifact_reader=reader, security=security, currency='USD')
    params = dict(state=state_owner.project_state(source=tech['completed_price_source'],
        plan=tech['plan'], read=daily, security=security, artifact_reader=reader),
        roles=roles, ticker='IBM', market='us', cutoff=date.fromisoformat(daily.latest_completed_session),
        observed_at=tech['plan'].frozen_at.isoformat(), completed_bar_reference=projection)
    monkeypatch.setattr(scope, 'materialize_source_components', lambda **kw: (_ for _ in ()).throw(
        ValueError('UNRELATED_INTEGRITY_FAILURE')))
    with pytest.raises(ValueError, match='UNRELATED_INTEGRITY_FAILURE'):
        state_owner.materialize_state(**params)
    changed = deepcopy(roles)
    changed['adjusted_daily'][-1]['close'] += 1
    with pytest.raises(ValueError, match='source_row_mismatch'):
        state_owner.materialize_state(**dict(params, roles=changed))
    tech['components']['completed_bar_reference_price_sha256'] = '0' * 64
    tech['expected_hashes']['components'] = digest(tech['components'])
    monkeypatch.undo()
    with pytest.raises(ValueError, match='component.*mismatch'):
        assemble_stock(**tech, fresh_financial_pending=True)


def test_changed_price_input_cannot_reuse_old_model_output():
    from scripts import newbuyer_b2_v2_shadow as shadow
    from tests.test_newbuyer_b2_v2 import inputs, outputs, validate
    before = shadow.build_request(**inputs())
    after = shadow.build_request(**inputs(timing='WAIT_FOR_ZONE'))
    assert before['request_sha256'] != after['request_sha256']
    assert validate(outputs(before)[0], after)['status'] == 'FAIL'


@pytest.mark.parametrize('mutation', ['compact', 'security', 'selected'])
def test_assembled_reference_readback_rejects_resealed_drift(tmp_path, mutation):
    from app.services.unified_stock_owner import assemble_stock, validate_assembled
    from app.services.completed_session_current_price import CompletedSessionCurrentPriceProjection
    inputs = bound_inputs(tmp_path)
    result = assemble_stock(**inputs['technical_inputs'], fresh_financial_pending=True)
    # Pure technical fixture has no business admission: validation must retain BLOCKED.
    assert validate_assembled(result, expected_result_sha256=digest(result)) is False
    if mutation == 'compact':
        result['packet']['stocks'][0]['completed_bar_reference_price']['value'] += 1
    elif mutation == 'selected':
        result['completed_session_current_price'] = result['current_price_state']['numeric_owner']
    else:
        ref = result['completed_bar_reference_price']
        ref['canonical_security_id'] = 'OTHER'
        ref['projection_sha256'] = digest({k: v for k, v in ref.items() if k != 'projection_sha256'})
        result['packet']['stocks'][0]['completed_bar_reference_price'] = (
            CompletedSessionCurrentPriceProjection.model_validate(ref).analysis_reference())
    with pytest.raises(ValueError, match='completed_bar_reference'):
        validate_assembled(result, expected_result_sha256=digest(result))
