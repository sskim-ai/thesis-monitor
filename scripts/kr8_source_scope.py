"""Explicit KR8 plan admission. Scope is checked before any provider transport."""
import json

from app.services.sealed_fresh_dispatch import ProviderPlan
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE

SCOPE = 'KR8_ONLY'
PROVIDERS = frozenset({'kiwoom', 'opendart', 'ecos', 'krx_night_futures', 'naver_news'})


def require_kr8_plan(frozen):
    if frozen.get('scope') != SCOPE:
        raise ValueError('kr8_explicit_scope_required')
    stock = StockPlan.model_validate(frozen['stock_plan'])
    candidate = frozen['candidate']
    if (stock.universe != {'kr': UNIVERSE['kr']} or
            set(frozen['sessions']) != {'kr'} or frozen['us_market_symbols'] or
            frozen['us_market_reads'] or candidate.get('scope') != SCOPE or
            set(candidate['current_subjects']) != set(UNIVERSE['kr']) or
            set(candidate['financial_plans']) != set(UNIVERSE['kr']) or
            set(candidate['macro_queries']) != {'ecos'} or
            {r['ticker'] for r in frozen['security_records']} != set(UNIVERSE['kr']) or
            {r['subject'] for r in frozen['news_reads']} != set(UNIVERSE['kr']) or
            any(r['market'] != 'kr' for r in frozen['news_reads'])):
        raise ValueError('kr8_source_scope_mismatch')
    plan = ProviderPlan.model_validate(frozen['plan'])
    if plan.generation_id != stock.run_id or plan.code_sha != stock.implementation_sha:
        raise ValueError('kr8_plan_identity_mismatch')
    for d in plan.descriptors:
        wire = json.loads(d.request_json)
        if (d.provider not in PROVIDERS or d.market not in {'kr', 'global'} or
                '/api/us/' in json.dumps(wire) or d.role_id.startswith(('us_', 'fred:', 'eia:'))):
            raise ValueError('kr8_us_only_descriptor_denied')
        if d.market == 'global' and d.role_id != 'kiwoom:credential_exchange':
            raise ValueError('kr8_unowned_global_descriptor')
    return dict(scope=SCOPE, stock_roles=len(stock.reads),
                descriptors=len(plan.descriptors), us_only_descriptors=0)
