"""Restore current-context source permissions without changing regime policy."""
from copy import deepcopy

from app.services.market_current_context_service import current_context_eligible, kr_sector_alias
from app.services.market_numeric_claim_service import numeric_catalog
from scripts import m12ds_r4_r4_market as previous
from app.macro.publication import PUBLICATION_SERIES, publication_freshness

PROMPT = previous.PROMPT
numeric_boundary = previous.numeric_boundary


def _directional_facts(context):
    return {ref: fact for ref, fact in context['facts'].items()
            if (fact.get('publication_freshness') or {}).get('current_direction_eligible') is not False}


def market_schema(context):
    return previous.market_schema({**context, 'facts': _directional_facts(context)})


def validate_market(row, context):
    receipt = previous.validate_market(row, context)
    directional = _directional_facts(context)
    if any(ref not in directional for ref in row['supporting_refs'] + row['contradicting_refs']):
        receipt['errors'].append('lagged_publication_used_for_current_direction')
    receipt['status'] = 'FAIL' if receipt['errors'] else 'PASS'
    return receipt


def market_context(packet):
    context = previous.market_context(packet)
    source = packet['market_context']
    completed = source['session']['latest_completed_regular_session_date']
    matrix = {r['ref']: r for r in context['parity_matrix']}
    for fact in source.get('fact_catalog', []):
        fields = fact.get('fields') or {}
        freshness = None
        if fields.get('provider') == 'fred' and fields.get('series_code') in PUBLICATION_SERIES:
            freshness = publication_freshness(fields.get('publication_receipt'), fields['series_code'],
                fact.get('as_of_date'), completed=completed, assessed=packet['assessment_date'])
            if not freshness['factual_display_eligible']:
                context['facts'].pop(fact['fact_id'], None)
                matrix[fact['fact_id']].update(eligible=False, reasons=['publication_freshness_unverified_or_expired'])
                continue
        eligible = (packet['market'] == 'us' and current_context_eligible(fact, completed, packet['assessment_date']))
        eligible |= packet['market'] == 'kr' and kr_sector_alias(fact, source, completed, context['facts'])
        if not eligible:
            continue
        ref = fact['fact_id']
        context['facts'][ref] = {**deepcopy(fact), 'usage': 'CURRENT_CONTEXT_NOT_NEW_DAILY_SIGNAL'}
        if freshness is not None:
            context['facts'][ref]['publication_freshness'] = freshness
            if not freshness['current_direction_eligible']:
                context['facts'][ref]['usage'] = 'LATEST_PUBLISHED_CONTEXT_ONLY_NOT_CURRENT_DIRECTION'
        matrix[ref].update(eligible=True, reasons=[], current_context_receipt='verified_source_occurrence')
    context['parity_matrix'] = [matrix[r] for r in sorted(matrix)]
    context['packet_eligible_refs'] = sorted(r for r in matrix if matrix[r]['eligible'])
    context['request_eligible_refs'] = sorted(context['facts'])
    context['suppressed_refs'] = sorted(set(matrix) - set(context['facts']))
    context['parity_status'] = 'PASS' if context['packet_eligible_refs'] == context['request_eligible_refs'] else 'FAIL'
    context['numeric_catalog'] = numeric_catalog(source, market=packet['market'],
        assessment_date=packet['assessment_date'], eligible_refs=context['request_eligible_refs'])
    return context
