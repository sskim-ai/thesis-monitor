"""Mandatory REV11 source coverage, using the existing Market display owners."""
from app.services.market_display_plan import build_display_plan, US_MACRO
from app.services.macro_source_time import CONTRACT as TIME_CONTRACT
from app.services.unified_snapshot_contract import digest
from scripts.r2b_r5_market_adapter import project_sealed_market_context


def check_projection(projected, market, publications=None):
    packet, context = projected['packet'], projected['context']
    source = packet['market_context']
    display = build_display_plan(source, market=market, assessment_date=packet['assessment_date'],
        eligible_refs=context['request_eligible_refs'])
    facts = source['fact_catalog']
    by_id = {f['fact_id']:f for f in facts}
    selected = {by_id[ref]['fields'].get('series_code') for item in display.items
        if item.status == 'AVAILABLE' for ref in item.fact_ids}
    missing = []
    if market == 'us':
        missing = sorted({'SPY','QQQ','IWM',*US_MACRO}-selected)
        dollar = [f for f in facts if f['fields'].get('series_code') == 'DTWEXBGS']
        valid = False
        if len(dollar) == 1:
            f = dollar[0]
            temporal = f['fields'].get('publication_context') or {}
            valid = (f['fact_id'] in context['request_eligible_refs']
                and temporal.get('contract') == TIME_CONTRACT
                and temporal.get('latest_available_at_query_time') is True
                and temporal.get('display_eligible') is True
                and temporal.get('freshness_state') in {'CURRENT_SESSION_OR_DATE','LATEST_PUBLISHED_VERIFIED'}
                and temporal.get('series_code') == 'DTWEXBGS'
                and temporal.get('observation_date') == f['as_of_date'] <= packet['assessment_date']
                and bool(temporal.get('response_sha256'))
                and any(r['fact_id'] == f['fact_id'] and r.get('registered') is True
                    and r.get('prose_allowed') is True for r in source['numeric_registry']))
        if not valid:
            missing.append('DTWEXBGS')
    else:
        if 'USDKRW' not in selected:
            from app.services.latest_published_fx import display_receipt
            owned_unavailable = bool(publications
                and publications.get('contract') == 'fresh-publication-replay-v1'
                and display_receipt(publications, display.completed_session)['status'] == 'TYPED_UNAVAILABLE')
            if not owned_unavailable:
                missing.append('USDKRW')
        indices = {f['fields'].get('symbol') for f in facts if f['fact_type']=='market_cross_section_index'
            and f['fact_id'] in context['request_eligible_refs'] and f['as_of_date']==display.completed_session}
        missing.extend(sorted({'KOSPI','KOSDAQ'}-indices))
    return dict(status='PASS' if not missing else 'SOURCE_PARTIAL', market=market,
        mandatory_missing=missing, display_plan=display.model_dump(mode='json'),
        source_sha256=digest(source), sector_or_night_horizon_unavailable_is_not_a_failure=True)


def qualify_markets(whole):
    return {m:check_projection(project_sealed_market_context(whole['packets'][m],whole['seed'],whole['authority_graph'],
        expected_authority_sha256=whole['authority_graph_sha256']),m,
        publications=whole['authority_graph'].get('publication_context')) for m in ('us','kr')}
