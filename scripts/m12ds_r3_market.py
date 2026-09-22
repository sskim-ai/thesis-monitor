"""Row-level frozen market parity; availability never overrides temporal denial."""
from copy import deepcopy
from math import isclose

from scripts import m12ds_r2_market as r2
from scripts.m12ds_r3_valuation_authority import day
from scripts.m12ds_r2_judgment_policy import number

market_schema = r2.market_schema
PROMPT = r2.PROMPT + '''
Use the full eligible market proxy set, including index, sector, style and relative-return
facts when present. A coverage label does not override a row-level unavailable flag or future
session date. Excluded rows remain unavailable. Equal-weight/sector price proxies are not
exchange breadth or investor flows. Relative returns only describe their exact source pair.'''

PROXY_SCOPES = {'market_index': ('indices', 'indices'), 'market_sector': ('sectors', 'sectors'),
                'market_style': ('style_size', 'size_context')}


def blocked(row):
    return (row.get('renderer_only') is True or row.get('source_unavailable') is True
            or row.get('state') in ('UNAVAILABLE', 'SOURCE_UNAVAILABLE', 'RENDERER_ONLY')
            or row.get('structured_state') in ('UNAVAILABLE', 'SOURCE_UNAVAILABLE', 'RENDERER_ONLY')
            or row.get('temporal_role') in ('UNAVAILABLE', 'REFERENCE_LAGGING')
            or row.get('today_signal_eligible') is False)


def market_context(packet):
    source = packet['market_context']
    adapter = source.get('adapter_context') or {}
    session = adapter.get('session_context') or source.get('session') or {}
    cutoff = session.get('latest_completed_regular_session_date')
    catalog = source.get('fact_catalog') or []
    if len({f['fact_id'] for f in catalog}) != len(catalog):
        raise ValueError('duplicate_market_fact_id')
    by_ref = {f['fact_id']: f for f in catalog}
    baseline = r2.market_context(packet)
    candidates = {}

    def add(ref, payload, reasons, origin):
        candidates[ref] = {'ref': ref, 'payload': deepcopy(payload), 'reasons': sorted(set(reasons)),
                           'origin': origin, 'source_sha256': r2.canonical_sha256(payload)}

    for fact in catalog:
        fields, ref = fact.get('fields') or {}, fact['fact_id']
        if fact.get('fact_type') in PROXY_SCOPES:
            scope, kind = PROXY_SCOPES[fact['fact_type']]
            coverage = (source.get('coverage') or {}).get(scope) or {}
            reasons = []
            if coverage.get('status') not in ('available', 'partial') or fields.get('series_code') not in coverage.get('available_series', []):
                reasons.append('coverage_not_eligible_for_series')
            if not day(cutoff) or fact.get('as_of_date') != cutoff:
                reasons.append('not_latest_completed_session')
            if blocked(fields) or blocked(fact):
                reasons.append('row_temporal_or_source_denial')
            if number(fields.get('return_pct')) is None or fields.get('quality') not in ('fresh', 'verified'):
                reasons.append('return_or_quality_unverified')
            if packet['market'] != 'us':
                reasons.append('cross_market_proxy_not_local_regime')
            add(ref, {**fact, 'kind': kind}, reasons, 'fact_catalog_proxy')
        elif not fields.get('source_fact_ids'):
            reasons = [] if ref in baseline['facts'] and not blocked(fields) and not blocked(fact) else ['not_current_eligible_fact']
            if not day(fact.get('as_of_date')) or fact.get('as_of_date', '') > packet['assessment_date']:
                reasons.append('source_availability_unverified')
            add(ref, fact, reasons, 'fact_catalog')

    for name in ('indices', 'sectors', 'size_context', 'market_flows'):
        for row in adapter.get(name) or []:
            ref = row.get('source_ref')
            if not ref or ref in candidates:
                continue
            reasons = []
            if not day(cutoff) or row.get('as_of_date') != cutoff:
                reasons.append('not_latest_completed_session')
            if blocked(row) or ref not in baseline['facts']:
                reasons.append('adapter_row_unavailable')
            if name == 'indices' and (source.get('coverage') or {}).get('local_market_indices', {}).get('status') not in ('available', 'partial'):
                reasons.append('local_index_coverage_unavailable')
            if name == 'market_flows' and (source.get('coverage') or {}).get(name, {}).get('status') != 'available':
                reasons.append('flow_coverage_unavailable')
            add(ref, {'kind': name, **row}, reasons, 'adapter_context')
    for ref, fact in baseline['facts'].items():
        if ref not in candidates and fact.get('kind') == 'breadth':
            reasons = [] if (source.get('coverage') or {}).get('breadth', {}).get('status') == 'available' else ['breadth_coverage_unavailable']
            add(ref, fact, reasons, 'adapter_breadth')
    for fact in catalog:
        fields = fact.get('fields') or {}
        parents = fields.get('source_fact_ids')
        if not parents:
            continue
        reasons = []
        if len(parents) != 2 or any(ref not in candidates or candidates[ref]['reasons'] for ref in parents):
            reasons.append('relative_inputs_not_eligible')
        if blocked(fields) or blocked(fact) or fact.get('as_of_date') != cutoff:
            reasons.append('relative_period_or_source_denial')
        if not reasons:
            values = [number(by_ref[r]['fields'].get('return_pct')) for r in parents]
            result = number(fields.get('relative_return_pct'))
            if result is None or any(v is None for v in values) or not isclose(float(values[0] - values[1]), float(result), abs_tol=1e-9):
                reasons.append('relative_arithmetic_mismatch')
        add(fact['fact_id'], {**fact, 'kind': 'relative_returns'}, reasons, 'canonical_relative_relation')
    matrix = [{k: v for k, v in row.items() if k != 'payload'} | {'eligible': not row['reasons']}
              for ref, row in sorted(candidates.items())]
    expected = sorted(row['ref'] for row in matrix if row['eligible'])
    facts = {ref: candidates[ref]['payload'] for ref in expected}
    return {'market': packet['market'].upper(), 'assessment_date': packet['assessment_date'],
            'source_market_sha256': r2.canonical_sha256(source), 'session_context': deepcopy(session),
            'facts': facts, 'suppressed_refs': sorted(set(candidates) - set(expected)),
            'parity_matrix': matrix, 'packet_eligible_refs': expected, 'request_eligible_refs': sorted(facts),
            'parity_status': 'PASS' if expected == sorted(facts) else 'FAIL',
            'export_only': True, 'stock_feedback': False}


def validate_market(row, context):
    receipt = r2.validate_market(row, context)
    if context['packet_eligible_refs'] != context['request_eligible_refs'] or context['request_eligible_refs'] != sorted(context['facts']):
        receipt['errors'].append('market_request_source_parity_mismatch')
    receipt['status'] = 'FAIL' if receipt['errors'] else 'PASS'
    return receipt
