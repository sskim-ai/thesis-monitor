"""Mandatory REV11 source coverage, using the existing Market display owners."""
from app.services.market_display_plan import build_display_plan, US_MACRO
from app.services.unified_snapshot_contract import digest
from scripts.r2b_r5_market_adapter import project_sealed_market_context


def check_projection(projected, market, publications=None):
    if 'display' not in projected.get('views', {}):
        raise ValueError('market_display_view_required')
    packet, context = projected['packet'], projected['context']
    source = packet['market_context']
    display = build_display_plan(source, market=market, assessment_date=packet['assessment_date'],
        eligible_refs=context['request_eligible_refs'], display_view=projected['views']['display'])
    facts = source['fact_catalog']
    by_id = {f['fact_id']:f for f in facts}
    selected = {by_id[ref]['fields'].get('series_code') for item in display.items
        if item.status == 'AVAILABLE' for ref in item.fact_ids}
    missing = []
    if market == 'us':
        missing = sorted({'SPY','QQQ','IWM',*US_MACRO}-selected)
    else:
        if 'USDKRW' not in selected:
            from app.services.latest_published_fx import display_receipt
            owned_unavailable = bool(publications
                and publications.get('contract') == 'fresh-publication-replay-v1'
                and display_receipt(publications, display.completed_session)['status'] == 'TYPED_UNAVAILABLE')
            if not owned_unavailable:
                missing.append('USDKRW')
        indices = {by_id[ref]['fields'].get('symbol') for item in display.items
                   if item.block_id == 'indices' and item.status == 'AVAILABLE' for ref in item.fact_ids}
        missing.extend(sorted({'KOSPI','KOSDAQ'}-indices))
    return dict(status='PASS' if not missing else 'SOURCE_PARTIAL', market=market,
        mandatory_missing=missing, display_plan=display.model_dump(mode='json'),
        market_views=projected['views'],
        source_sha256=digest(source), sector_or_night_horizon_unavailable_is_not_a_failure=True)


def qualify_markets(whole):
    result = {}
    scope = whole['seed'].get('scope')
    expected = {'us'} if scope == 'US14_ONLY' else {'kr'} if scope == 'KR8_ONLY' else {'us','kr'}
    if set(whole['packets']) != expected:
        raise ValueError('market_qualification_scope_mismatch')
    for market in sorted(expected):
        projections = [project_sealed_market_context(whole['packets'][market], whole['seed'], whole['authority_graph'],
            expected_authority_sha256=whole['authority_graph_sha256']) for _ in range(2)]
        if digest(projections[0]) != digest(projections[1]):
            raise ValueError('market_view_replay_mismatch')
        result[market] = check_projection(projections[0], market,
            publications=whole['authority_graph'].get('publication_context'))
        result[market]['view_replay'] = dict(status='PASS', first_sha256=digest(projections[0]['views']),
            second_sha256=digest(projections[1]['views']), source_sha256=digest(whole['packets'][market]))
    return result
