import ast
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import us_dated_source_sr as sr
from app.services.detailed_stock_message_v2 import _us_sr_rows
from app.services.kiwoom_completed_close_owner import historical_only_roles
from app.services.market_session import us_market_session
from app.services.unified_snapshot_contract import digest


@pytest.fixture
def data(monkeypatch):
    cutoff, observed = '2026-11-18', '2026-11-19T08:10:00+09:00'
    def bar(day):
        return dict(date=day, open=100, high=110, low=90, close=105, volume=1000)
    periods = dict(daily=[bar('2026-11-17'), bar(cutoff)],
        weekly=[bar('2026-11-09'), bar('2026-11-16')],
        monthly=[bar('2026-10-01'), bar('2026-11-02')])
    receipts = {'adjusted_' + tf: dict(run_id='source-one', acquisition_id='source-one:stock',
        plan_sha256='a'*64, status='CAPTURED', pages=[{}], normalized_sha256=digest(rows),
        entry=dict(market='us', subject='MU', canonical_security_id='security-one', adjusted=True,
            latest_completed_session=cutoff, timeframe=tf, role='adjusted_' + tf)) for tf, rows in periods.items()}
    calls = []
    def runtime(**kwargs):
        calls.append(deepcopy(kwargs))
        return dict(as_of=kwargs['cutoff'], current_quote=None, native_current_price_qualified=False,
            partial_bar_used_for_pivot_confirmation=0)
    zone = dict(semantic_type='NEAR_SUPPORT', fact_ref='zone:one', source_refs=['pivot:one'],
        source_timeframes=['daily'], currency='USD', security_basis='US_LISTED:MU', as_of=cutoff,
        adjustment_basis='provider_adjusted_price_v1', raw_low='90', raw_high='95')
    rollout = SimpleNamespace(render_validation_errors=(), numeric_bindings=[zone], displayed_zone_ids=['zone:one'])
    monkeypatch.setattr(sr, 'build_us_price_structure_runtime_context', runtime)
    monkeypatch.setattr(sr, 'build_us_price_structure_rollout_decision', lambda *a, **k: rollout)
    args = dict(enabled=True, ticker='MU', security_id='security-one', generation='source-one',
        cutoff=cutoff, observed_at=observed, periods=periods, receipts=receipts, provider_limit=1000)
    return args, calls, rollout


def source_for(ref, args):
    fact = dict(fact_id='price:current', fields=dict(current_price=123))
    roles = {role: dict(receipt_sha256=digest(receipt), normalized_sha256=receipt['normalized_sha256'])
        for role, receipt in args['receipts'].items()}
    return dict(fresh_run_id='source-one',
        completed_session_current_price=dict(adjustment_basis='regular_close', current_price=123,
            technical_compatibility=dict(status='UNPROVEN', technical_target_injection_allowed=False)),
        packet=dict(source_time_domains=dict(run_id='source-one', started_at=args['observed_at']),
            stocks=[dict(ticker='MU', fact_catalog=[fact], chart_context=dict(
                timeframes=dict(daily=dict(as_of_date='2026-11-17')),
                structure=dict(price_structure_v3=ref)))]),
        source_graph={'price:current': dict(source='sealed_stock_roles', ticker='MU',
            fact_sha256=digest(fact), roles=roles)})


def test_us_exchange_session_progression_holiday_and_early_close():
    assert str(us_market_session(datetime.fromisoformat('2026-11-19T08:10:00+09:00')).latest_completed_regular_session_date) == '2026-11-18'
    assert str(us_market_session(datetime.fromisoformat('2026-11-20T08:10:00+09:00')).latest_completed_regular_session_date) == '2026-11-19'
    assert str(us_market_session(datetime.fromisoformat('2026-11-27T08:10:00+09:00')).latest_completed_regular_session_date) == '2026-11-25'
    assert str(us_market_session(datetime.fromisoformat('2026-11-27T12:59:00-05:00')).latest_completed_regular_session_date) == '2026-11-25'
    assert str(us_market_session(datetime.fromisoformat('2026-11-27T13:01:00-05:00')).latest_completed_regular_session_date) == '2026-11-27'


def test_latest_original_reference_does_not_change_isolated_technical_or_quote(data):
    args, calls, rollout = data
    before = digest(args)
    roles = {'adjusted_' + tf: rows for tf, rows in args['periods'].items()}
    isolated = historical_only_roles(roles, cutoff=date.fromisoformat(args['cutoff']))
    result = sr.attach({}, **args)['price_structure_v3']
    assert len(calls) == 1 and calls[0]['raw_by_timeframe']['daily'][-1]['date'] == args['cutoff']
    assert isolated['adjusted_daily'][-1]['date'] == '2026-11-17'
    assert result['as_of'] == result['completed_sources']['daily']['completed'] == args['cutoff']
    assert not result['eligible_for_current_price'] and not result['eligible_for_b2_timing']
    assert digest(args) == before
    next_day = deepcopy(args)
    next_day.update(cutoff='2026-11-19', observed_at='2026-11-20T08:10:00+09:00')
    next_day['periods']['daily'].append(dict(next_day['periods']['daily'][-1], date='2026-11-19'))
    for tf in ('daily', 'weekly', 'monthly'):
        next_day['receipts']['adjusted_' + tf]['entry']['latest_completed_session'] = '2026-11-19'
    rollout.numeric_bindings[0]['as_of'] = '2026-11-19'
    advanced = sr.attach({}, **next_day)['price_structure_v3']
    assert advanced['as_of'] == calls[-1]['raw_by_timeframe']['daily'][-1]['date'] == '2026-11-19'


def test_explicit_partial_wrong_session_and_receipt_denied_before_engine(data):
    args, calls, _ = data
    for mutation in ('partial', 'missing_target', 'wrong_subject', 'wrong_generation', 'wrong_adjustment', 'kst_date'):
        changed = deepcopy(args)
        if mutation == 'partial':
            changed['periods']['daily'][-1]['bar_state'] = 'PARTIAL'
        elif mutation == 'missing_target':
            changed['periods']['daily'].pop()
        elif mutation == 'kst_date':
            changed['cutoff'] = '2026-11-19'
        elif mutation == 'wrong_generation':
            changed['receipts']['adjusted_daily']['run_id'] = 'other'
        else:
            field, value = ('subject', 'OTHER') if mutation == 'wrong_subject' else ('adjusted', False)
            changed['receipts']['adjusted_daily']['entry'][field] = value
        assert sr.attach({}, **changed) == {}
    assert not calls


def test_only_completed_wm_periods_reach_existing_engine(data):
    args, calls, _ = data
    ref = sr.attach({}, **args)['price_structure_v3']
    assert [r['date'] for r in calls[0]['raw_by_timeframe']['weekly']] == ['2026-11-09']
    assert [r['date'] for r in calls[0]['raw_by_timeframe']['monthly']] == ['2026-10-01']
    assert ref['completed_sources']['weekly']['completed'] == '2026-11-13'
    assert ref['completed_sources']['monthly']['completed'] == '2026-10-30'
    assert args['periods']['weekly'][-1]['date'] == '2026-11-16'
    changed = deepcopy(args)
    changed['periods']['weekly'] = [changed['periods']['weekly'][-1]]
    assert sr.attach({}, **changed) == {}
    assert len(calls) == 1


def test_renderer_independent_reference_date_and_source_bindings(data):
    args, _, _ = data
    ref = sr.attach({}, **args)['price_structure_v3']
    source = source_for(ref, args)
    before = digest(source)
    packet = SimpleNamespace(market='us', ticker='MU')
    axes = dict(entry_timing=dict(state='UNRESOLVED'))
    def render(value):
        base = SimpleNamespace(source_stock=value, source_generation_id='source-one',
            accepted_calibration=SimpleNamespace(entries={}))
        return _us_sr_rows(packet, base, axes, 'security-one')
    rows = render(source)
    text = '\n'.join(row.text for row in rows)
    assert len(rows) == 2 and text.count(args['cutoff']) == 1
    assert '조정봉' in rows[0].text and '진입 관찰 지지 구간과 구분' in rows[0].text
    assert '참고 가까운 지지: $90.00–$95.00' in rows[1].text
    assert 'B2' not in text and '123' not in text and digest(source) == before
    for mutation in ('ref_date', 'target_date', 'receipt', 'source_missing', 'raw_basis', 'promoted', 'period_end', 'fake_zone'):
        changed = deepcopy(source)
        item = changed['packet']['stocks'][0]['chart_context']['structure']['price_structure_v3']
        if mutation == 'ref_date':
            item['as_of'] = '2026-11-17'
        elif mutation == 'target_date':
            item['target_session'] = '2026-11-19'
        elif mutation == 'receipt':
            item['completed_sources']['daily']['receipt_sha256'] = '0'*64
        elif mutation == 'source_missing':
            changed['source_graph'] = {}
        elif mutation == 'raw_basis':
            item['adjustment_basis'] = 'regular_close'
        elif mutation == 'promoted':
            item['eligible_for_b2_timing'] = True
        elif mutation == 'period_end':
            item['completed_sources']['weekly']['completed'] = '2026-11-20'
        else:
            item['zones'][0]['low'] = '-1'
        assert not render(changed)
    assert source['completed_session_current_price']['technical_compatibility']['status'] == 'UNPROVEN'


def test_zero_eligible_zones_are_not_fabricated(data):
    args, calls, rollout = data
    rollout.numeric_bindings = []
    assert sr.attach({}, **args) == {} and len(calls) == 1


def test_actual_assembly_selects_original_roles_only_at_dated_attach():
    import app.services.unified_stock_owner as module
    tree = ast.parse(Path(module.__file__).read_text())
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == 'attach')
    selector = next(k.value for k in call.keywords if k.arg == 'periods')
    assert isinstance(selector, ast.DictComp)
    assert isinstance(selector.value, ast.Subscript) and selector.value.value.id == 'roles'
    owning_try = next(n for n in ast.walk(tree) if isinstance(n, ast.Try) and call in list(ast.walk(n)))
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == 'require_complete_stock_window' for n in ast.walk(owning_try))
    # Guard the existing general isolation function by its exact baseline bytes elsewhere;
    # this test only verifies the production call argument, not a synthetic Source admission.


def test_existing_source_parent_hash_rejects_altered_original_receipt(data):
    from app.services.unified_stock_owner import _exact
    args, calls, _ = data
    original = args['receipts']
    _exact(original, digest(original))
    changed = deepcopy(original)
    changed['adjusted_daily']['normalized_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='frozen_input_hash_mismatch'):
        _exact(changed, digest(original))
    assert not calls
