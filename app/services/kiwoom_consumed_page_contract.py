"""Opt-in completeness for the declared KR cross-section consumer only.

Transport exhaustion remains the default. The native consumer reads ka20001
page-one scalars and one ka20009 target row; it never reads their tail series.
ka20003 and flow owners still require exhausted pagination.
"""
from datetime import date, datetime
import json

from app.services.unified_snapshot_contract import digest

CONTRACT = 'kiwoom-cross-section-consumed-pages-v1'
SCALARS = ('cur_prc', 'flu_rt', 'rising', 'fall', 'stdns', 'upl', 'lst')


def read_dependencies(api_id, payloads, *, session, continuation):
    if not payloads or len(payloads) != len(continuation):
        raise ValueError('consumed_page_missing')
    first = payloads[0]
    if api_id == 'ka20001':
        from app.services.kiwoom_kr_market_context_service import _signed_float
        for key in SCALARS:
            _signed_float(first.get(key))
        return {'mode': 'CONSUMER_COMPLETE', 'paths': ['/' + k for k in SCALARS],
                'tail_can_affect_consumer': False}
    if api_id == 'ka20009':
        target = session.strftime('%Y%m%d')
        rows = first.get('inds_cur_prc_daly_rept')
        if not isinstance(rows, list):
            raise ValueError('target_session_rows_missing')
        matches = [i for i, r in enumerate(rows) if isinstance(r, dict) and r.get('dt_n') == target]
        if len(matches) != 1:
            raise ValueError('target_session_missing_or_ambiguous')
        # Additional captured pages cannot hide another incompatible target row.
        if any(r.get('dt_n') == target for p in payloads[1:]
               for r in p.get('inds_cur_prc_daly_rept', []) if isinstance(r, dict)):
            raise ValueError('target_session_ambiguous_across_pages')
        index = matches[0]
        from app.services.kiwoom_kr_market_context_service import _signed_float
        for key in ('cur_prc_n', 'flu_rt_n'):
            _signed_float(rows[index].get(key))
        return {'mode': 'CONSUMER_COMPLETE',
                'paths': [f'/inds_cur_prc_daly_rept/{index}/' + k for k in ('dt_n', 'cur_prc_n', 'flu_rt_n')],
                'tail_can_affect_consumer': False}
    if continuation[-1]:
        raise ValueError('transport_exhaustion_required:' + api_id)
    if api_id not in {'ka20003', 'ka10051', 'ka10066'}:
        raise ValueError('unknown_consumer_dependency')
    return {'mode': 'TRANSPORT_EXHAUSTED', 'paths': ['/'], 'tail_can_affect_consumer': True}


def qualify(graph, *, observed_at):
    """Revalidate source paths and native session ownership, not a PASS label."""
    from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService, MARKETS
    receipt = graph.receipt
    if (receipt.role, receipt.market, receipt.provider) != (
            'kr_local_indices_sectors_breadth', 'kr', 'kiwoom_rest'):
        raise ValueError('consumed_page_owner_scope_mismatch')
    if not isinstance(observed_at, datetime) or observed_at.utcoffset() is None:
        raise ValueError('consumed_page_observation_required')
    session = date.fromisoformat(receipt.session)
    reads = {r['key']: r for r in json.loads(graph.plan)['reads']}
    grouped = {}
    for child, raw, page in zip(graph.child_receipts, graph.child_bodies, graph.accepted_pages, strict=True):
        if raw is None or page is None:
            raise ValueError('consumed_page_raw_missing')
        key = child['read_key']
        read = reads[key]
        if child['request']['api_id'] != read['api_id'] or child['request']['body'] != read['body']:
            raise ValueError('consumed_page_request_mismatch')
        grouped.setdefault(key, []).append((json.loads(raw), page))
    if set(grouped) != set(reads):
        raise ValueError('consumed_page_read_set_missing')
    proofs = {}
    for key, entries in grouped.items():
        read = reads[key]
        proof = read_dependencies(read['api_id'], [p for p, _ in entries], session=session,
                                  continuation=[p['continuation'] for _, p in entries])
        proofs[key] = {**proof, 'read_key': key, 'api_id': read['api_id'],
            'session': receipt.session, 'pages': [p for _, p in entries], 'result': 'PASS'}
    for market, spec in MARKETS.items():
        for api in ('ka20001', 'ka20003', 'ka20009'):
            read = reads[market + ':' + api]
            expected = {'inds_cd': spec['code']}
            if api != 'ka20003':
                expected['mrkt_tp'] = spec['ka20001_market']
            if read['body'] != expected:
                raise ValueError('consumed_page_market_identity_mismatch')
        if json.loads(graph.plan).get("completed_session_only", False):
            KiwoomKrMarketContextService._completed_history_row(
                session_date=session, observed_at=observed_at,
                history=grouped[market + ':ka20009'][0][0])
        else:
            KiwoomKrMarketContextService._validate_session_identity(
            session_date=session, observed_at=observed_at, market=market, code=spec['code'],
            current=grouped[market + ':ka20001'][0][0],
            sectors=grouped[market + ':ka20003'][0][0],
            history=grouped[market + ':ka20009'][0][0])
    return {'contract': CONTRACT, 'reads': proofs, 'mandatory_complete': True,
            'scope': 'DECLARED_CROSS_SECTION_ONLY_NOT_PROVIDER_SERIES_COMPLETENESS',
            'observed_at': observed_at.isoformat(), 'source_plan_sha256': digest(json.loads(graph.plan))}


def dependency_ledger(graph, value, *, observed_at):
    """Per-leaf direct inputs, plus target-session validator inputs."""
    from app.services.kiwoom_kr_market_context_service import MARKETS
    proof = qualify(graph, observed_at=observed_at)
    from zoneinfo import ZoneInfo
    completed_only = (json.loads(graph.plan).get("completed_session_only", False)
        and observed_at.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat() != graph.receipt.session)
    sources = {}
    for child, raw, page in zip(graph.child_receipts, graph.child_bodies, graph.accepted_pages, strict=True):
        sources.setdefault(child['read_key'], []).append((json.loads(raw), page))
    def dep(key, path):
        page = sources[key][0][1]
        return {'read_key': key, 'source_api': proof['reads'][key]['api_id'],
                'page_identity': page['identity'], 'raw_sha256': page['raw_sha256'],
                'source_json_pointer': path, 'completion_mode': proof['reads'][key]['mode']}
    def validation(market):
        if completed_only:
            return [dep(market + ':ka20009', p) for p in proof['reads'][market + ':ka20009']['paths']]
        key = market + ':ka20003'
        rows = sources[key][0][0]['all_inds_idex']
        idx = next(i for i, row in enumerate(rows) if row.get('stk_cd') == MARKETS[market]['code'])
        return ([dep(market + ':' + api, p) for api in ('ka20001', 'ka20009')
                 for p in proof['reads'][market + ':' + api]['paths']]
                + [dep(key, f'/all_inds_idex/{idx}/' + p) for p in ('stk_cd', 'cur_prc', 'flu_rt')])
    breadth = {'advance_count': ['rising'], 'decline_count': ['fall'], 'unchanged_count': ['stdns'],
        'eligible_count': ['rising', 'fall', 'stdns'], 'advance_ratio': ['rising', 'fall'],
        'ad_ratio': ['rising', 'fall'], 'positive_return_pct': ['rising', 'fall', 'stdns'],
        'negative_return_pct': ['rising', 'fall', 'stdns'], 'limit_up_count': ['upl'], 'limit_down_count': ['lst']}
    ledger = []
    def leaves(item, path=()):
        if isinstance(item, dict):
            for k, v in item.items():
                yield from leaves(v, (*path, k))
        elif isinstance(item, list):
            for i, v in enumerate(item):
                yield from leaves(v, (*path, str(i)))
        else:
            yield path, item
    for path, scalar in leaves(value):
        field, section = path[-1], path[0]
        direct, constants, markets = [], None, []
        if section == 'indices':
            row = value[section][int(path[1])]
            markets = [row['symbol']]
            market = markets[0]
            key = market + ':ka20003'
            rows = sources[key][0][0]['all_inds_idex']
            idx = next(i for i, r in enumerate(rows) if r.get('stk_cd') == MARKETS[market]['code'])
            if field in {'close', 'return_pct'}:
                if completed_only:
                    name = {'close': 'cur_prc_n', 'return_pct': 'flu_rt_n'}[field]
                    direct = [dep(market + ':ka20009', p) for p in proof['reads'][market + ':ka20009']['paths']
                        if p.endswith('/' + name)]
                else:
                    direct = [dep(market + ':ka20001', '/' + {'close': 'cur_prc', 'return_pct': 'flu_rt'}[field])]
            elif field == 'label':
                if completed_only:
                    constants = "native_completed_index_identity"
                else:
                    direct = [dep(key, f'/all_inds_idex/{idx}/stk_nm')]
            else:
                constants = 'native_index_identity_or_optional_field'
        elif section == 'sectors':
            row = value[section][int(path[1])]
            market = row['market_scope']
            markets = [market]
            key = market + ':ka20003'
            rows = sources[key][0][0]['all_inds_idex']
            idxs = [i for i, r in enumerate(rows) if r.get('stk_cd') == row['sector_code']]
            if len(idxs) != 1:
                raise ValueError('sector_identity_ambiguous')
            mapping = {'sector': ['stk_nm'], 'sector_code': ['stk_cd'], 'return_pct': ['flu_rt'],
                       'listed_count': ['flo_stk_num'], **breadth}
            direct = [dep(key, f'/all_inds_idex/{idxs[0]}/' + p) for p in mapping.get(field, [])]
            if not direct:
                constants = 'native_sector_taxonomy_scope_or_optional_field'
        elif section in {'breadth', 'breadth_by_scope'}:
            markets = list(MARKETS) if section == 'breadth' else [value[section][int(path[1])]['scope']]
            for market in markets:
                if field == 'listed_count':
                    key = market + ':ka20003'
                    rows = sources[key][0][0]['all_inds_idex']
                    idx = next(i for i, r in enumerate(rows) if r.get('stk_cd') == MARKETS[market]['code'])
                    direct.append(dep(key, f'/all_inds_idex/{idx}/flo_stk_num'))
                else:
                    direct += [dep(market + ':ka20001', '/' + p) for p in breadth.get(field, [])]
            if not direct:
                constants = 'native_scope_or_explicit_unsupported_breadth_field'
        else:
            raise ValueError('unmapped_cross_section:' + section)
        if not direct and scalar is not None and field not in {
                'symbol', 'source_ref', 'taxonomy', 'metric_role', 'market_scope', 'scope',
                *({'label'} if completed_only else set())}:
            raise ValueError('unmapped_nonnull_consumer_field:' + '/'.join(path))
        ledger.append({'output_field': '/' + '/'.join(path), 'output_value_sha256': digest(scalar),
            'direct_sources': direct, 'session_validation_sources': [d for m in markets for d in validation(m)],
            'constant_or_denial_owner': constants, 'target_session': graph.receipt.session,
            'normalization_owner': 'KiwoomKrMarketContextService', 'tail_can_affect_field': False,
            'proof_result': 'PASS'})
    return ledger
