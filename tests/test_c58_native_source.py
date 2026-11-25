"""Native sidecars through the real KR/US Source assembler, without live IO."""
from copy import deepcopy
from datetime import date
import json

import pytest

from app.services import packet_owned_technical_context_service as packets
from app.services import unified_stock_anomaly_scope as components
from app.services import unified_stock_owner as owner
from app.services.completed_price_state import bind_source
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.kiwoom_completed_close_owner import materialize_price_context
from app.services.provider_native_technical import INDICATORS, build_owned_provider_native_view
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import encoded
from scripts.unified_stock_source_worker import native_indicator_projection
from tests.test_c56_source_numeric import no_external as no_external
from tests.test_c56_source_numeric import _bars, source_inputs
from tests.test_c58_native_indicator_acquisition import load_original_engine
from tests.test_unified_stock_owner import freeze_hashes


def _native_and_roles(technical):
    roles, native = {}, {}
    for role, receipt in technical['receipts'].items():
        roles[role] = json.loads(technical['artifacts'][receipt['normalized_artifact']])
        if role.startswith('adjusted_'):
            native[role.removeprefix('adjusted_')] = json.loads(
                technical['artifacts'][receipt['native_indicators']['artifact']])
    return roles, native


def refresh_native_source(inputs):
    """Rebind a synthetic producer artifact through the actual source adapters."""
    technical = inputs['technical_inputs']
    roles, native = _native_and_roles(technical)
    plan, ticker = technical['plan'], technical['ticker']
    read = next(row for row in plan.reads if row.subject == ticker)
    if read.market == 'us':
        technical = bind_source(technical, source=technical['completed_price_source'], artifacts={},
            security=inputs['financial_inputs']['plan']['security'])
    else:
        technical['components'] = components.materialize_source_components(ticker=ticker,
            market=read.market, cutoff=date.fromisoformat(read.latest_completed_session),
            observed_at=plan.frozen_at.isoformat(), roles=roles, completed_session=True,
            native_indicators=native)
    inputs['technical_inputs'] = freeze_hashes(technical)
    return inputs


def native_source_inputs(root, ticker):
    """C56 calendar/financial fixture plus real original-engine worker sidecars."""
    inputs = source_inputs(root, ticker)
    engine_root = root / 'native-indicator-engine'
    engine_root.mkdir(parents=True, exist_ok=True)
    engine = load_original_engine(engine_root)
    technical = inputs['technical_inputs']
    for read in technical['plan'].reads:
        if read.subject != ticker or not read.role.startswith('adjusted_'):
            continue
        receipt = technical['receipts'][read.role]
        rows = json.loads(technical['artifacts'][receipt['normalized_artifact']])
        projection = native_indicator_projection(rows, read.model_dump(mode='json'),
            receipt['normalized_sha256'], engine=engine)
        assert projection['status'] == 'AVAILABLE'
        payload = encoded(projection)
        name = receipt['normalized_artifact'] + '.indicators.json'
        technical['artifacts'][name] = payload
        receipt['native_indicators'] = dict(artifact=name, sha256=sha256_bytes(payload))
    return refresh_native_source(inputs)


def forbid_tm_indicators(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Native Source called a TM basic indicator calculator')
    monkeypatch.setattr(packets, 'build_multi_timeframe_feature_packet', forbidden)
    monkeypatch.setattr(components, 'build_packet_owned_technical_context', forbidden)
    monkeypatch.setattr(components, '_feature_facts', forbidden)
    monkeypatch.setattr(owner, 'build_packet_owned_technical_context', forbidden)
    from app.services import price_structure_wave_fibonacci_v3_service as v3
    monkeypatch.setattr(v3, '_bollinger_sources', forbidden)
    monkeypatch.setattr(v3, '_provisional_bollinger_sources', forbidden)


@pytest.mark.parametrize('ticker', ['005930', 'CORZ'])
def test_original_values_reach_real_source_and_structures_without_tm_math(tmp_path, monkeypatch, ticker):
    inputs = native_source_inputs(tmp_path, ticker)
    before = deepcopy(inputs)
    _, supplied = _native_and_roles(inputs['technical_inputs'])
    forbid_tm_indicators(monkeypatch)
    result = assemble_fresh_stock(**inputs)
    assert result['status'] == 'PASS' and result['mandatory_missing'] == []
    assert result['numeric_registry_unregistered'] == []
    assert inputs == before
    stock = result['packet']['stocks'][0]
    technical = stock['technical_context']
    assert technical['features'] is None
    assert technical['native_view']['allowed_use'] == 'MONITORING_TECHNICAL'
    assert technical['native_view']['current_price_qualified'] is False
    assert stock['chart_context']['structure']['atr']['daily']['available']
    for tf, period in technical['native_view']['periods'].items():
        expected = next(row['indicators'] for row in supplied[tf]['rows']
                        if row['date'] == period['completed_as_of'])
        assert period['indicators'] == {field: expected.get(field) for field in INDICATORS}
        assert period['returned_count'] == supplied[tf]['calculation_row_count']
        assert all(row['bar_state'] == 'COMPLETE' for row in period['rows'])
        assert technical['quality'][{'daily': 'D', 'weekly': 'W', 'monthly': 'M'}[tf]]['usable_for_current_reasoning']
    daily = stock['chart_context']['timeframes']['daily']
    original = technical['native_view']['periods']['daily']['indicators']
    assert daily['rsi_14'] == original['RSI14']
    assert daily['macd'] == original['MACD']
    assert daily['volume_ratio_20'] == original['VOLUME_RATIO_20']
    assert not any(row['ref_id'].startswith('technical-feature:') for row in result['evidence_packet']['evidence'])
    monthly = technical['native_view']['periods']['monthly']
    assert monthly['completed_as_of'] != supplied['monthly']['rows'][-1]['date']
    assert monthly['indicators']['MA288'] is None
    assert monthly['indicators']['MACD_OSC_320_640_9'] is not None
    assert monthly['indicator_quality']['MACD_OSC_320_640_9'] == 'PROVIDER_NATIVE'


def test_missing_native_values_never_fall_back_to_tm_indicators(tmp_path, monkeypatch):
    inputs = native_source_inputs(tmp_path, '005930')
    technical = inputs['technical_inputs']
    receipt = technical['receipts']['adjusted_daily']
    descriptor = receipt['native_indicators']
    payload = json.loads(technical['artifacts'][descriptor['artifact']])
    payload.update(status='UNAVAILABLE', reason='ORIGINAL_INDICATOR_ENGINE_ERROR_ValueError', rows=[])
    raw = encoded(payload)
    descriptor['sha256'] = sha256_bytes(raw)
    technical['artifacts'][descriptor['artifact']] = raw
    forbid_tm_indicators(monkeypatch)
    refresh_native_source(inputs)
    result = assemble_fresh_stock(**inputs)
    assert result['status'] == 'PASS'
    stock = result['packet']['stocks'][0]
    context = stock['technical_context']
    assert context['features'] is None
    assert context['native_view']['periods']['daily']['status'] == 'UNAVAILABLE'
    assert not context['quality']['D']['usable_for_current_reasoning']
    assert stock['chart_context']['timeframes']['daily']['rsi_14'] is None
    assert stock['chart_context']['timeframes']['daily']['volume_ratio_20'] is None
    assert not any(row['label'].startswith('daily:provider-native:')
                   for row in result['evidence_packet']['evidence'])


def test_us_price_fallback_preserves_native_audit_without_recalculation(tmp_path, monkeypatch):
    inputs = native_source_inputs(tmp_path, 'CORZ')
    technical = inputs['technical_inputs']
    roles, native = _native_and_roles(technical)
    read = next(row for row in technical['plan'].reads if row.subject == 'CORZ')
    kwargs = dict(roles=roles, ticker='CORZ', market='us',
        cutoff=date.fromisoformat(read.latest_completed_session),
        observed_at=technical['plan'].frozen_at.isoformat(), native_indicators=native)
    forbid_tm_indicators(monkeypatch)
    value = materialize_price_context(current_price=100, projection_ref='synthetic-price-owner',
        compatibility={'status': 'UNPROVEN'}, **kwargs)
    context, _ = owner._technical(value, roles, **{key: val for key, val in kwargs.items() if key != 'roles'})
    assert context.features is None and context.native_view is not None
    assert all(not row.usable_for_current_reasoning for row in context.quality.values())
    assert value['current_price'] == 100
    assert context.status == 'UNAVAILABLE'


def test_native_artifact_binding_cannot_be_relabelled(tmp_path):
    inputs = native_source_inputs(tmp_path, '005930')
    receipt = inputs['technical_inputs']['receipts']['adjusted_daily']
    descriptor = receipt['native_indicators']
    value = json.loads(inputs['technical_inputs']['artifacts'][descriptor['artifact']])
    value['source_normalized_sha256'] = '0' * 64
    raw = encoded(value)
    inputs['technical_inputs']['artifacts'][descriptor['artifact']] = raw
    descriptor['sha256'] = sha256_bytes(raw)
    freeze_hashes(inputs['technical_inputs'])
    with pytest.raises(ValueError, match='native_indicator_source_binding_mismatch'):
        assemble_fresh_stock(**inputs)


def test_invalid_history_cannot_disappear_before_native_integrity_review(tmp_path):
    engine = load_original_engine(tmp_path)
    rows = [{**row, 'bar_state': 'COMPLETE'}
            for row in _bars('kr', '2026-09-25')['adjusted_daily'][-60:]]
    rows[-8]['close'] = -1
    before = deepcopy(rows)
    payload = native_indicator_projection(rows, {'entry_id': 'kr:005930:adjusted_daily'},
        sha256_bytes(encoded(rows)), engine=engine)
    # The original EMA can return a finite result despite the malformed source.
    assert payload['status'] == 'AVAILABLE'
    assert payload['rows'][-1]['indicators']['MACD'] is not None
    view = build_owned_provider_native_view(ticker='005930', market='kr', periods={'daily': rows},
        native_indicators={'daily': payload}, cutoff=date(2026, 9, 25))
    assert view.periods['daily'].status == 'INVALID'
    assert view.periods['daily'].indicators['MACD'] is None
    assert 'NATIVE_INDICATOR_SOURCE_ROWS_INVALID' in view.periods['daily'].reasons
    assert rows == before


def test_normal_partial_and_future_rows_do_not_invalidate_completed_native_values(tmp_path):
    engine = load_original_engine(tmp_path)
    rows = [{**row, 'bar_state': 'COMPLETE'}
            for row in _bars('kr', '2026-09-24')['adjusted_daily'][-60:]]
    completed_day = rows[-1]['date']
    rows += [dict(rows[-1], date='2026-09-25', bar_state='PARTIAL'),
             dict(rows[-1], date='2026-09-28', bar_state='COMPLETE')]
    payload = native_indicator_projection(rows, {'entry_id': 'kr:005930:adjusted_daily'},
        sha256_bytes(encoded(rows)), engine=engine)
    expected = next(row['indicators'] for row in payload['rows'] if row['date'] == completed_day)
    view = build_owned_provider_native_view(ticker='005930', market='kr', periods={'daily': rows},
        native_indicators={'daily': payload}, cutoff=date(2026, 9, 25))
    period = view.periods['daily']
    assert period.status == 'AVAILABLE' and period.completed_as_of == completed_day
    assert period.indicators == expected
    assert period.quarantined_count == 2
    assert all(row['date'] <= completed_day for row in period.rows)
