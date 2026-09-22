"""Restore current-context source permissions without changing regime policy."""
from copy import deepcopy

from app.services.market_current_context_service import current_context_eligible, kr_sector_alias
from app.services.market_numeric_claim_service import numeric_catalog
from scripts import m12ds_r4_r4_market as previous

PROMPT = previous.PROMPT
market_schema = previous.market_schema
validate_market = previous.validate_market
numeric_boundary = previous.numeric_boundary


def market_context(packet):
    context = previous.market_context(packet)
    source = packet['market_context']
    completed = source['session']['latest_completed_regular_session_date']
    matrix = {r['ref']: r for r in context['parity_matrix']}
    for fact in source.get('fact_catalog', []):
        eligible = (packet['market'] == 'us' and current_context_eligible(fact, completed, packet['assessment_date']))
        eligible |= packet['market'] == 'kr' and kr_sector_alias(fact, source, completed, context['facts'])
        if not eligible:
            continue
        ref = fact['fact_id']
        context['facts'][ref] = {**deepcopy(fact), 'usage': 'CURRENT_CONTEXT_NOT_NEW_DAILY_SIGNAL'}
        matrix[ref].update(eligible=True, reasons=[], current_context_receipt='verified_source_occurrence')
    context['parity_matrix'] = [matrix[r] for r in sorted(matrix)]
    context['packet_eligible_refs'] = sorted(r for r in matrix if matrix[r]['eligible'])
    context['request_eligible_refs'] = sorted(context['facts'])
    context['suppressed_refs'] = sorted(set(matrix) - set(context['facts']))
    context['parity_status'] = 'PASS' if context['packet_eligible_refs'] == context['request_eligible_refs'] else 'FAIL'
    context['numeric_catalog'] = numeric_catalog(source, market=packet['market'],
        assessment_date=packet['assessment_date'], eligible_refs=context['request_eligible_refs'])
    return context
