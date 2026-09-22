"""Market narrative and final fact rendering share the typed numeric boundary."""
from app.services.market_numeric_claim_service import (
    numeric_catalog, validate_catalog, narrative_errors, NUMERIC_FREE_RULE, PROSE_FIELDS,
)
from scripts import m12ds_r4_r1_market as previous

PROMPT = previous.PROMPT + "\n" + NUMERIC_FREE_RULE


def market_context(packet):
    context = previous.market_context(packet)
    context['numeric_catalog'] = numeric_catalog(packet['market_context'],market=packet['market'],
        assessment_date=packet['assessment_date'],eligible_refs=context['request_eligible_refs'])
    return context


def market_schema(context):
    schema = previous.market_schema(context)
    for key in PROSE_FIELDS:
        schema['properties'][key]['pattern'] = r'^[^0-9]*$'
        schema['properties'][key]['description'] = 'Qualitative narrative only. Numeric facts/dates/instruments are rendered by the typed backend owner.'
    return schema


def validate_market(row,context):
    receipt = previous.validate_market(row,context)
    receipt['errors'] += narrative_errors(row)
    receipt['status'] = 'FAIL' if receipt['errors'] else 'PASS'
    return receipt


def numeric_boundary(context,source):
    return validate_catalog(context['numeric_catalog'],source)
