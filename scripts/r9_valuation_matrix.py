"""Fictional raw-wire negative controls over the exact current valuation owner."""
from copy import deepcopy
import json

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.current_fresh_valuation import CurrentValuationView
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes


def replay_matrix(stocks, inputs):
    qualified = [t for t, s in stocks.items() if 'valuation_inputs' in inputs[t]
                 and any(r['metric'] == 'PER' and r['status'] == 'QUALIFIED' for r in s['valuation_view']['metrics'])]
    if not qualified:
        raise ValueError('matrix_native_qualified_source_required')
    base = inputs[sorted(qualified)[0]]
    rows = []
    for t, stock in stocks.items():
        view = CurrentValuationView.model_validate(stock['valuation_view'])
        scope = view.denominator_scope_receipt
        if not scope or scope['receipt_sha256'] != digest({k: v for k, v in scope.items() if k != 'receipt_sha256'}):
            raise ValueError('matrix_denominator_capability_receipt_missing')
        raw_scope = scope['raw_source_projection']
        if not raw_scope or raw_scope['receipt_sha256'] != digest({k: v for k, v in raw_scope.items() if k != 'receipt_sha256'}):
            raise ValueError('matrix_raw_denominator_projection_missing')
        if any(r.overall_direction_use or r.numerator != view.price for r in view.metrics):
            raise ValueError('matrix_direction_or_current_price_leakage')
        rows.append(dict(case='current:' + t, output_sha256=digest(view.model_dump(mode='json')),
                         states={r.metric: r.status for r in view.metrics}, scope=scope))
    states = {(m['metric'], m['status']) for s in stocks.values() for m in s['valuation_view']['metrics']}
    required = {('PER', 'QUALIFIED'), ('PBR', 'QUALIFIED'), ('PER', 'NOT_MEANINGFUL'),
                ('PER', 'UNAVAILABLE'), ('PBR', 'UNAVAILABLE'), ('fPER', 'UNAVAILABLE')}
    if not required <= states:
        raise ValueError('matrix_typed_state_coverage_incomplete')
    for case in ('negative_eps', 'nonpositive_book', 'missing_horizon', 'currency', 'share_class', 'missing_asof', 'old_asof'):
        variant = deepcopy(base)
        native = variant['valuation_inputs']
        body = json.loads(native['raw'])
        metric, expected = 'PER', 'UNAVAILABLE'
        if case == 'negative_eps':
            body['metric'].update(epsTTM=-2, peTTM=None)
            expected = 'NOT_MEANINGFUL'
        elif case == 'nonpositive_book':
            body['metric'].update(pbQuarterly=0, pbAnnual=2)
            metric = 'PBR'
        elif case == 'missing_horizon':
            body['metric']['forwardPE'] = 8
            metric = 'fPER'
        elif case == 'currency':
            body['currency'] = 'EUR'
        elif case == 'share_class':
            body['shareClass'] = 'unowned_preferred'
        elif case == 'missing_asof':
            body.pop('metricAsOf', None)
            body.pop('asOfDate', None)
        else:
            body['metricAsOf'] = '2000-01-01'
        native['raw'] = encoded(body)
        native['receipt']['source_sha256'] = sha256_bytes(native['raw'])
        view = assemble_fresh_stock(**variant)['valuation_view']
        row = next(r for r in view['metrics'] if r['metric'] == metric)
        if row['status'] != expected or row['overall_direction_use'] or row['entry_use_eligible']:
            raise ValueError('matrix_negative_control_failed:' + case)
        rows.append(dict(case=case, synthetic_variant=True, native_raw=body, native_receipt=native['receipt'],
                         expected=expected, actual=row['status'], output=view))
    variant = deepcopy(base)
    variant['valuation_inputs']['receipt']['security_sha256'] = '0' * 64
    try:
        assemble_fresh_stock(**variant)
    except ValueError as exc:
        if str(exc) != 'fresh_native_valuation_receipt_mismatch':
            raise
        rows.append(dict(case='wrong_current_security', rejection=str(exc)))
    else:
        raise ValueError('matrix_wrong_security_not_rejected')
    current = stocks[sorted(qualified)[0]]['valuation_view']
    for forged in ('COMPATIBLE', 'QUALIFIED'):
        try:
            CurrentValuationView.model_validate({**current, 'historical_distribution': forged})
        except ValueError:
            rows.append(dict(case='unowned_historical_' + forged, rejection='typed_historical_scope'))
        else:
            raise ValueError('matrix_unowned_historical_not_rejected')
    return dict(status='PASS', rows=rows, matrix_sha256=digest(rows),
        optional_unavailable_is_not_stock_failure=True, qualified_fper_owner_present=False,
        deterministic_denominator_status='UNAVAILABLE_IN_CURRENT_BOUNDED_PROJECTION',
        historical_comparison='NO_COMPATIBLE_VERSIONED_DISTRIBUTION_OWNER', new_sources=0, provider_calls=0)
