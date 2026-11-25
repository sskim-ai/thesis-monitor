"""Compare only local-pivot recency on saved bars; never accept or render inputs.

Both calculations use the current analyzer and the original timeframe context.
The baseline substitutes the old major-window count only. Saved C52 judgments
remain separate and are never replaced by this structural diagnostic.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from unittest.mock import patch

from app.services import ohlcv_structure_service as structure
from app.services.eligible_completed_session_bars import eligible_completed_roles
from app.services.ohlcv_completed_bar_finality_service import BarFinality, assess_completed_bar_finality
from app.services.price_structure_wave_fibonacci_v3_service import normalize_completed_bars
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import bound_artifact
from scripts.c49_inspect_saved_inputs import read, snapshot

FRAMES = ('daily', 'weekly', 'monthly')
ZONE_FIELDS = ('timeframe', 'pivot_type', 'zone_low', 'zone_high', 'center', 'pivot_dates',
    'latest_reaction_date', 'reaction_score', 'recency_score', 'higher_timeframe_score',
    'bollinger_overlap', 'fibonacci_overlap', 'score', 'strength')


def saved_roles(source_root, frozen, ticker):
    """Read three existing normalized receipts; no raw replay or whole-source scan."""
    plan, native = frozen['stock_plan'], source_root / 'native' / 'stocks'
    selected = [(ordinal, entry) for ordinal, entry in enumerate(plan['reads'], 1)
                if entry['subject'] == ticker and entry['role'] in {'adjusted_' + tf for tf in FRAMES}]
    if len(selected) != 3 or {entry['role'] for _, entry in selected} != {'adjusted_' + tf for tf in FRAMES}:
        raise ValueError('SAVED_ADJUSTED_ROLES_UNAVAILABLE')
    sessions = {entry['latest_completed_session'] for _, entry in selected}
    if len(sessions) != 1 or any(entry['market'] != 'us' for _, entry in selected):
        raise ValueError('SAVED_ROLE_SESSION_OR_MARKET_MISMATCH')
    roles, artifacts = {}, {}
    for ordinal, entry in selected:
        receipt = read(native / f'role-{ordinal:03d}.receipt.json')
        if (receipt['status'] != 'CAPTURED' or receipt['entry'] != entry
                or receipt['run_id'] != plan['run_id']
                or receipt['acquisition_id'] != plan['acquisition_id']
                or receipt['plan_sha256'] != digest(plan)):
            raise ValueError('SAVED_ROLE_RECEIPT_MISMATCH')
        raw = bound_artifact(native, receipt['normalized_artifact'], receipt['normalized_sha256'])
        roles[entry['role']] = json.loads(raw)
        artifacts[entry['role']] = dict(path=receipt['normalized_artifact'],
            sha256=receipt['normalized_sha256'])
    return roles, artifacts, date.fromisoformat(next(iter(sessions)))


def completed_periods(roles, *, ticker, cutoff, observed_at):
    """Mirror the producer's calendar view, retaining original normalized columns."""
    eligible, _ = eligible_completed_roles(roles, ticker=ticker, market='us',
        cutoff=cutoff, observed_at=observed_at)
    periods = {}
    for tf in FRAMES:
        rows = eligible['adjusted_' + tf]
        states = {bar.date: bar.bar_state for bar in normalize_completed_bars(rows,
            cutoff=str(cutoff), timeframe=tf, market='US', observed_at=observed_at)}
        marked = [{**row, 'bar_state': states[str(row['date'])[:10]]}
                  if str(row['date'])[:10] in states else dict(row) for row in rows]
        periods[tf] = [row for row in marked
            if assess_completed_bar_finality(row, cutoff=cutoff).state == BarFinality.FINAL]
        if not periods[tf]:
            raise ValueError('SAVED_COMPLETED_FRAME_UNAVAILABLE:' + tf)
    return periods


def zone_summary(zone):
    return {key: zone[key] for key in ZONE_FIELDS if key in zone}


def structure_summary(result):
    groups = result['zones']
    candidates = [*groups['active'], *groups['support']]
    meaningful = [zone for zone in candidates if zone['strength'] in {'Medium', 'Strong'}]
    if meaningful:
        reason = 'MEANINGFUL_SUPPORT_AVAILABLE'
    elif not result['all_zones']:
        reason = 'NO_CONFIRMED_LOCAL_ZONES'
    elif not candidates:
        reason = 'NO_ZONE_AT_OR_BELOW_CURRENT_PRICE'
    else:
        reason = 'ONLY_WEAK_ZONES_AT_OR_BELOW_CURRENT_PRICE'
    return dict(as_of_date=result['as_of_date'], reason=reason,
        local_pivot_counts={tf: len(result['local_pivots'][tf]) for tf in FRAMES},
        zone_counts={key: len(rows) for key, rows in groups.items()},
        nearest_supports=[zone_summary(zone) for zone in meaningful[:2]],
        all_zone_scores=[zone_summary(zone) for zone in result['all_zones']],
        invalidation=result['invalidation'], risk_reward=result['risk_reward'],
        chart_state=result['chart_state'])


def compare_periods(periods, timeframes):
    major_counts = {tf: len(structure.normalize_bar_series(periods[tf], tf,
        lookback=structure.MAJOR_CONFIG[tf].lookback).bars) for tf in FRAMES}
    local_counts = {tf: len(structure.normalize_structure_bars(periods[tf],
        lookback=structure.LOCAL_PIVOT_LOOKBACKS[tf])) for tf in FRAMES}
    original_build = structure.build_price_zones

    def old_count(pivots, timeframe, *, bar_count):
        return original_build(pivots, timeframe, bar_count=major_counts[timeframe])

    with patch.object(structure, 'build_price_zones', old_count):
        before = structure.analyze_chart_structure(deepcopy(periods),
            timeframe_contexts=deepcopy(timeframes))
    after = structure.analyze_chart_structure(deepcopy(periods),
        timeframe_contexts=deepcopy(timeframes))
    latest = max(after['local_pivots']['weekly'], key=lambda row: row['index'], default=None)
    weekly = dict(local_window_count=local_counts['weekly'], major_window_count=major_counts['weekly'],
        latest_confirmed_pivot=latest,
        before_age=None if latest is None else max(0, major_counts['weekly'] - 1 - latest['index']),
        after_age=None if latest is None else max(0, local_counts['weekly'] - 1 - latest['index']))
    return dict(before=structure_summary(before), after=structure_summary(after), weekly=weekly,
        completed_windows={tf: dict(count=len(rows), first_date=rows[0]['date'],
            last_date=rows[-1]['date']) for tf, rows in periods.items()},
        timeframe_context_sha256=digest(timeframes))


def compare_saved(*, source_root, cycle, tickers):
    value = snapshot(cycle)
    source, binding = value['collection']['monitoring_input'], value['child_binding']
    frozen = read(source_root / 'production-frozen-source-plan.json')
    generation = source['source_generation_id']
    if (generation != binding['source_generation'] or generation != frozen['generation_id']
            or frozen['stock_plan']['run_id'] != generation or binding['market'] != 'us'):
        raise ValueError('SAVED_SOURCE_GENERATION_MISMATCH')
    if not tickers or len(set(tickers)) != len(tickers):
        raise ValueError('EXPLICIT_UNIQUE_TICKERS_REQUIRED')
    report = dict(contract='saved-local-recency-comparison-v1',
        purpose='OFFLINE_STRUCTURE_DIAGNOSTIC_NOT_SOURCE_ACCEPTANCE_OR_FINAL_JUDGMENT',
        source_generation=generation, cycle=str(cycle), source_root=str(source_root),
        baseline='CURRENT_CODE_WITH_PRE_C55_MAJOR_WINDOW_RECENCY_COUNT',
        after='CURRENT_CODE_WITH_LOCAL_WINDOW_RECENCY_COUNT',
        model_acceptance=False, rendered_messages=0, entries={})
    for ticker in tickers:
        row = report['entries'][ticker] = {}
        try:
            original = source['stocks'][ticker]
            stock = next(item for item in original['packet']['stocks'] if item['ticker'] == ticker)
            chart = stock['chart_context']
            old = chart.get('structure') or {}
            row['original_saved_summary'] = {key: old.get(key) for key in
                ('nearest_supports', 'nearest_resistance', 'chart_state', 'invalidation', 'risk_reward')}
            reference = stock.get('completed_bar_reference_price') or {}
            if not old or chart.get('available') is not True or reference.get('availability') != 'AVAILABLE':
                raise ValueError('SAVED_COMPLETED_STRUCTURE_CONTEXT_UNAVAILABLE')
            roles, artifacts, cutoff = saved_roles(source_root, frozen, ticker)
            if reference.get('target_session') != str(cutoff):
                raise ValueError('SAVED_REFERENCE_SESSION_MISMATCH')
            periods = completed_periods(roles, ticker=ticker, cutoff=cutoff,
                observed_at=frozen['stock_plan']['frozen_at'])
            row.update(compare_periods(periods, chart['timeframes']))
            row.update(status='COMPARED', normalized_artifacts=artifacts,
                completed_session=str(cutoff), current_daily_close=periods['daily'][-1]['close'])
        except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
            row.update(status='NOT_COMPARED', reason=str(exc) or type(exc).__name__)
    report['compared'] = sum(row['status'] == 'COMPARED' for row in report['entries'].values())
    report['not_compared'] = len(tickers) - report['compared']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--cycle', required=True, type=Path)
    parser.add_argument('--tickers', required=True, help='Explicit comma-separated subjects')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    cycle, source_root, output = args.cycle.resolve(), args.source_root.resolve(), args.output.resolve()
    if any(output == root or root in output.parents for root in (cycle, source_root)):
        raise ValueError('COMPARISON_OUTPUT_MUST_BE_OUTSIDE_ORIGINALS')
    result = compare_saved(source_root=source_root, cycle=cycle,
        tickers=[ticker.strip() for ticker in args.tickers.split(',') if ticker.strip()])
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(output), compared=result['compared'],
        not_compared=result['not_compared'], model_acceptance=False, rendered_messages=0)))


if __name__ == '__main__':
    main()
