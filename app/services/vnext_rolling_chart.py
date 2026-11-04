"""Bounded derived-price replay over cold, owner-verified CAS dependencies.

This validates a consumer projection; hashes are not source/use authority.
Callers must obtain the dependency proof from Composite/Original Source Owner.
"""
import json
import time
from datetime import date, datetime

from app.services.vnext_research_store import digest
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows

CONTRACT = 'bounded-rolling-chart-closure-v1'
DERIVED = 'owned-incremental-daily-research-v1'
MAX_DEPTH = 12
MAX_NODES = 128
MAX_BYTES = 64 * 1024**2
MAX_SECONDS = 10


def resolve_chart(entry, source_bytes, *, security=None, registry=None):
    """Original + original or derived + original. Never derived + derived."""
    root_sha = entry['source_sha']
    if root_sha not in source_bytes or digest(source_bytes[root_sha]) != root_sha:
        raise ValueError('chart_raw_source_mismatch')
    if len(source_bytes[root_sha]) > MAX_BYTES:
        raise ValueError('incremental_replay_resource_bound')
    root = json.loads(source_bytes[root_sha])
    if root.get('contract') != DERIVED:
        return root
    proof = entry['provenance']
    if entry['field'] != 'ohlcv.adjusted_daily' or proof['provider'] != 'IncrementalDailyReplay':
        raise ValueError('incremental_price_parent_authority')
    if registry is not None:
        if security is None or registry.revoked(security['canonical_security_id'], entry):
            raise ValueError('incremental_price_source_revoked')
    def key(row):
        return row['run_id'], row['raw_sha256']
    expected = [key(p) for p in root.get('parents', [])]
    if (len(expected) != 2 or len(set(expected)) != 2 or
            set(expected) != {key(p) for p in proof['dependencies']}):
        raise ValueError('incremental_price_parent_authority')
    closure = {key(p): p for p in proof['dependency_closure']}
    if len(closure) != len(proof['dependency_closure']):
        raise ValueError('incremental_duplicate_closure')
    if len(closure) > MAX_NODES:
        raise ValueError('incremental_replay_resource_bound')
    started = time.monotonic()
    active, cache, seen_bytes, dates = set(), {}, {root_sha}, set()
    total_bytes = len(source_bytes[root_sha])
    visited = set()

    def raw(k):
        nonlocal total_bytes
        visited.add(k)
        if len(visited) > MAX_NODES or time.monotonic() - started > MAX_SECONDS:
            raise ValueError('incremental_replay_resource_bound')
        if k not in closure or not closure[k].get('receipt_sha256'):
            raise ValueError('incremental_price_original_receipt_missing')
        data = source_bytes.get(k[1])
        if data is None or digest(data) != k[1]:
            raise ValueError('incremental_price_original_missing')
        if k[1] not in seen_bytes:
            seen_bytes.add(k[1]); total_bytes += len(data)
            if total_bytes > MAX_BYTES:
                raise ValueError('incremental_replay_resource_bound')
        return data

    def identity(b):
        body = b['request_body']
        reference = root['request_body']
        if any(body.get(k) != reference.get(k) for k in ('stk_cd', 'stex_tp', 'upd_stkpc_tp', 'exrt_tp')):
            raise ValueError('incremental_parent_security_or_basis')
        calendar = 'XKRX' if root['market'] == 'KR' else 'XNYS'
        currency = 'KRW' if root['market'] == 'KR' else 'USD'
        if (body.get('upd_stkpc_tp') != '1' or root['basis'].get('adjusted') is not True or
                root['basis'].get('role') != 'daily' or root['basis'].get('currency') != currency or
                root['basis'].get('calendar') != calendar or b['calendar']['calendar'] != calendar):
            raise ValueError('incremental_parent_market_or_currency')
        if security is not None and (root['basis']['security'] != security['canonical_security_id'] or
                root['market'] != security['country'] or body['stk_cd'] != security['ticker'].replace('.', '-') or
                (root['market'] == 'US' and body.get('stex_tp') !=
                 {'NASDAQ':'ND','NYSE':'NY','AMEX':'NA'}.get(security['exchange']))):
            raise ValueError('incremental_parent_registered_security')
        if b.get('contract') == DERIVED and b['basis'] != root['basis']:
            raise ValueError('incremental_parent_basis_changed')

    def visit(k, depth):
        if depth > MAX_DEPTH or k in active:
            raise ValueError('incremental_depth_or_cycle')
        if k in cache:
            return cache[k]
        active.add(k)
        b = json.loads(raw(k))
        identity(b)
        if b.get('contract') == DERIVED:
            value = merge(b, depth)
        elif b.get('kind') == 'CURRENT_CHART_REPLAY' and b.get('pages'):
            page_keys = [(k[0], p['raw_sha256']) for p in b['pages']]
            if len(page_keys) != len(set(page_keys)):
                raise ValueError('incremental_duplicate_original_page')
            for p, pk in zip(b['pages'], page_keys):
                raw(pk)
                if datetime.fromisoformat(p['captured_at']).tzinfo is None:
                    raise ValueError('incremental_original_time_missing')
            rows = b['selected']
            if not rows or rows[-1]['date'] != b['calendar']['session']:
                raise ValueError('incremental_original_session_missing')
            q = inspect_normalized_ohlcv_rows(rows, timeframe='daily',
                                            cutoff=date.fromisoformat(b['calendar']['session']))
            if not q.valid or b['quality']['valid'] is not True:
                raise ValueError('incremental_original_quality_denied')
            dates.update(r['date'] for r in rows)
            value = dict(b, pages=[dict(p, original_run=k[0]) for p in b['pages']])
        else:
            raise ValueError('incremental_price_original_chart_required')
        active.remove(k)
        cache[k] = value
        return value

    def merge(b, depth):
        from app.services.vnext_incremental_ingestion import replay_merge
        parents = [key(p) for p in b.get('parents', [])]
        if len(parents) != 2 or len(set(parents)) != 2:
            raise ValueError('incremental_duplicate_parents')
        prior, tail = (visit(k, depth + 1) for k in parents)
        if tail.get('kind') != 'CURRENT_CHART_REPLAY' or tail.get('contract') == DERIVED:
            raise ValueError('incremental_new_tail_must_be_original')
        if (prior['parser_sha256'] != tail['parser_sha256'] or b['request_body'] != tail['request_body'] or
                b['calendar'] != tail['calendar'] or b['requested_rows'] != prior['requested_rows'] or
                prior['calendar']['session'] > tail['calendar']['session'] or
                prior['calendar']['session'] == tail['calendar']['session'] and not b['correction_reason']):
            raise ValueError('incremental_price_parser_or_session_binding')
        if max(datetime.fromisoformat(p['captured_at']) for p in prior['pages']) >= min(
                datetime.fromisoformat(p['captured_at']) for p in tail['pages']):
            raise ValueError('incremental_original_capture_order')
        merged = replay_merge(b, prior, tail)
        if merged['status'] != 'MERGED_RESEARCH_WINDOW' or not merged['quality']['valid']:
            raise ValueError('incremental_merge_quality_or_gap')
        pages = {(p['original_run'], p['raw_sha256']): p for p in prior['pages'] + tail['pages']}
        return dict(b, quality=merged['quality'], parser_sha256=tail['parser_sha256'],
                    pages=list(pages.values()))

    identity(root)
    result = merge(root, 0)
    result['rolling_closure'] = dict(contract=CONTRACT, nodes=len(visited), bytes=total_bytes,
        original_unique_sessions=len(dates), selected_rows=len(result['selected']),
        max_depth=MAX_DEPTH, max_nodes=MAX_NODES, max_bytes=MAX_BYTES,
        historical_raw_preserved=True, source_owner_issued=False, strict_native=False)
    return result
