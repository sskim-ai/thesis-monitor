"""Market narrative and final fact rendering share the typed numeric boundary."""
from app.services.market_numeric_claim_service import (
    numeric_catalog, validate_catalog, narrative_errors, NUMERIC_FREE_RULE, PROSE_FIELDS,
)
from scripts import m12ds_r4_r1_market as previous
from copy import deepcopy
import re

NIGHT_EXCLUSION_NOTICE = '한국 야간선물은 이번 미국 점검의 입력에서 제외했습니다.'
PROMPT = previous.PROMPT + "\n" + NUMERIC_FREE_RULE + "\nDated aggregate flow references are context only, not directional citation refs or stock attribution. Do not infer BUY/SELL or market expectations from these amounts alone." + "\nWhen korean_night_futures.state is EXCLUDED_BEFORE_COLLECTION, omit Korean night futures from all narrative fields. No price, change, direction or market inference may be based on them. The backend adds the exclusion notice. Other eligible market facts remain usable."


def excluded_night_narrative_errors(row, context, *, fields=PROSE_FIELDS):
    """The exclusion notice belongs to the backend, never to model inference."""
    if context.get('korean_night_futures', {}).get('state') != 'EXCLUDED_BEFORE_COLLECTION':
        return []
    errors = []
    for key in fields:
        text = str(row.get(key, ''))
        # This exclusion concerns Korea's night market, not named US futures.
        text = re.sub(r'(?:미국|나스닥|US|U\.S\.|Nasdaq)\s*(?:야간\s*선물|(?:night|overnight)\s+futures)',
            '', text, flags=re.IGNORECASE)
        if re.search(r'야간\s*선물|(?:KRX|KOSPI|KOSDAQ|Korean)[ -]*(?:\d+[ -]*)?(?:night|overnight)[ -]*futures',
                text, flags=re.IGNORECASE):
            errors.append('excluded_korean_night_futures_narrative:' + key)
    return errors


def market_context(packet):
    context = previous.market_context(packet)
    context['numeric_catalog'] = numeric_catalog(packet['market_context'],market=packet['market'],
        assessment_date=packet['assessment_date'],eligible_refs=context['request_eligible_refs'])
    reference=packet['market_context'].get('aggregate_flow_reference')
    if reference is not None:
        context['dated_aggregate_flow_references']=dict(value=deepcopy(reference['value']),
            economic_use=False,directional_citation_eligible=False,stock_attribution=False)
    night = packet['market_context'].get('night_futures_ownership') or {}
    if night.get('state') == 'EXCLUDED_BEFORE_COLLECTION':
        context['korean_night_futures'] = dict(state=night['state'], collected=False,
            economic_use=False, directional_citation_eligible=False)
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
    receipt['errors'] += excluded_night_narrative_errors(row, context)
    receipt['status'] = 'FAIL' if receipt['errors'] else 'PASS'
    return receipt


def numeric_boundary(context,source):
    return validate_catalog(context['numeric_catalog'],source)
