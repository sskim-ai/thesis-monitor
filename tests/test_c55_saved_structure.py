"""Bounded saved-source diagnostics do not rerun acceptance or alter originals."""
from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
import json
from math import sin
import socket

import pytest

from app.services import ohlcv_structure_service as structure
from app.services.unified_snapshot_contract import digest, encoded
from scripts import c55_compare_saved_structure as diagnostic


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('SAVED_COMPARISON_NETWORK_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def saved_case(tmp_path, *, weekly_count=160):
    source_root, cycle = tmp_path / 'source', tmp_path / 'original-consumer'
    observed, generation = '2026-11-25T00:10:00+00:00', 'original-source'
    def bar(day, close):
        return dict(date=str(day), open=close, high=close + 1, low=close - 1,
            close=close, volume=100, retained_provider_column='unchanged')
    daily = [bar(date(2026, 11, day), 100 + day / 10)
             for day in range(2, 26) if date(2026, 11, day).weekday() < 5]
    daily[-1]['close'] = daily[-1]['open'] = 999
    daily[-1]['high'], daily[-1]['low'] = 1000, 998
    weekly = [bar(date(2026, 11, 23) - timedelta(weeks=weekly_count - 1 - i), 100 + 10 * sin(i / 5))
              for i in range(weekly_count)]
    monthly = [bar(date(2026, month, 1 if month != 11 else 2), 100) for month in (9, 10, 11)]
    roles = dict(adjusted_daily=daily, adjusted_weekly=weekly, adjusted_monthly=monthly)
    entries = [dict(subject='SAMPLE', role=role, timeframe=role.removeprefix('adjusted_'),
        market='us', latest_completed_session='2026-11-24') for role in roles]
    plan = dict(run_id=generation, acquisition_id='captured-once', frozen_at=observed, reads=entries)
    frozen = dict(generation_id=generation, stock_plan=plan)
    write(source_root / 'production-frozen-source-plan.json', frozen)
    native = source_root / 'native' / 'stocks'
    for ordinal, entry in enumerate(entries, 1):
        name = f'role-{ordinal:03d}.normalized.json'
        raw = encoded(roles[entry['role']])
        write(native / name, roles[entry['role']])
        write(native / f'role-{ordinal:03d}.receipt.json', dict(status='CAPTURED', entry=entry,
            run_id=generation, acquisition_id=plan['acquisition_id'], plan_sha256=digest(plan),
            normalized_artifact=name, normalized_sha256=sha256(raw).hexdigest()))
    timeframes = dict(daily=dict(quality='available', as_of_date='2026-11-24',
        volume_ratio_20=1.2, bollinger_upper={}), weekly={}, monthly={})
    stock = dict(ticker='SAMPLE', chart_context=dict(available=True, timeframes=timeframes,
        structure=dict(nearest_supports=[], chart_state=dict(state='ORIGINAL_C52_STATE'))),
        completed_bar_reference_price=dict(availability='AVAILABLE', target_session='2026-11-24'))
    snapshot = dict(child_binding=dict(run_id=cycle.name, source_generation=generation, market='us'),
        collection=dict(monitoring_input=dict(source_generation_id=generation,
            stocks=dict(SAMPLE=dict(packet=dict(stocks=[stock]))))))
    pin = digest(snapshot)
    write(cycle / 'snapshots' / (pin + '.json'), snapshot)
    write(cycle / 'b2' / 'request.json', dict(storage_contract='prepared-research-request-reference-v1',
        header=dict(stage='B2', run_id=cycle.name, snapshot_sha256=pin), snapshot_ref=f'snapshots/{pin}.json'))
    return source_root, cycle, roles, timeframes


def test_saved_roles_use_real_completed_projection_and_only_recency_changes(tmp_path):
    source_root, cycle, roles, timeframes = saved_case(tmp_path)
    originals = {str(path): path.read_bytes() for path in tmp_path.rglob('*.json')}
    build = structure.build_price_zones
    result = diagnostic.compare_saved(source_root=source_root, cycle=cycle, tickers=['SAMPLE'])
    row = result['entries']['SAMPLE']
    assert row['status'] == 'COMPARED', row
    assert row['weekly']['local_window_count'] == 120
    assert row['weekly']['major_window_count'] == 156
    assert row['weekly']['before_age'] - row['weekly']['after_age'] == 36
    assert row['before']['all_zone_scores'] != row['after']['all_zone_scores']
    assert row['before']['local_pivot_counts'] == row['after']['local_pivot_counts']
    assert row['completed_windows']['daily']['last_date'] == '2026-11-24'
    assert row['completed_windows']['weekly']['last_date'] == '2026-11-16'
    assert row['completed_windows']['monthly']['last_date'] == '2026-10-01'
    assert row['current_daily_close'] == 102.4
    assert row['timeframe_context_sha256'] == digest(timeframes)
    assert row['original_saved_summary']['chart_state'] == {'state': 'ORIGINAL_C52_STATE'}
    assert structure.build_price_zones is build
    assert {str(path): path.read_bytes() for path in tmp_path.rglob('*.json')} == originals
    assert result['model_acceptance'] is False and result['rendered_messages'] == 0
    source_copy = deepcopy(roles)
    periods = diagnostic.completed_periods(roles, ticker='SAMPLE', cutoff=date(2026, 11, 24),
        observed_at='2026-11-25T00:10:00+00:00')
    assert all(row['retained_provider_column'] == 'unchanged' for rows in periods.values() for row in rows)
    assert roles == source_copy


def test_short_weekly_history_has_no_recency_difference(tmp_path):
    source_root, cycle, _, _ = saved_case(tmp_path, weekly_count=100)
    report = diagnostic.compare_saved(source_root=source_root, cycle=cycle, tickers=['SAMPLE'])
    row = report['entries']['SAMPLE']
    assert row['status'] == 'COMPARED', row
    assert row['weekly']['local_window_count'] == row['weekly']['major_window_count'] == 99
    assert row['before'] == row['after']


def test_changed_normalized_artifact_is_reported_without_repair(tmp_path):
    source_root, cycle, _, _ = saved_case(tmp_path)
    path = source_root / 'native' / 'stocks' / 'role-002.normalized.json'
    path.write_bytes(path.read_bytes() + b' ')
    changed = path.read_bytes()
    report = diagnostic.compare_saved(source_root=source_root, cycle=cycle, tickers=['SAMPLE'])
    row = report['entries']['SAMPLE']
    assert row['status'] == 'NOT_COMPARED'
    assert row['reason'] == 'stock_artifact_hash_mismatch'
    assert 'before' not in row and 'after' not in row and path.read_bytes() == changed


def test_missing_subject_does_not_prevent_other_saved_subject_comparison(tmp_path):
    source_root, cycle, _, _ = saved_case(tmp_path, weekly_count=100)
    report = diagnostic.compare_saved(source_root=source_root, cycle=cycle, tickers=['MISSING', 'SAMPLE'])
    assert report['compared'] == report['not_compared'] == 1
    assert report['entries']['MISSING']['status'] == 'NOT_COMPARED'
    assert report['entries']['MISSING']['reason']
    assert 'before' not in report['entries']['MISSING']
    assert report['entries']['SAMPLE']['status'] == 'COMPARED'
