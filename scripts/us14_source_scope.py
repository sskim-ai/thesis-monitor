"""Exact primary/issuer/context scope; never authorize a hidden KR stock run."""
from app.services.auxiliary_issuer_financial_owner import AuxiliaryIssuerDependency
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE
from app.services.sealed_fresh_dispatch import ProviderPlan
from app.services.unified_snapshot_contract import digest


def require_us14_plan(frozen):
    stock = StockPlan.model_validate(frozen['stock_plan'])
    candidate = frozen['candidate']
    subjects = set(UNIVERSE['us'])
    if (frozen.get('scope') != 'US14_ONLY' or stock.universe != {'us':UNIVERSE['us']}
            or set(frozen['sessions']) != {'us'} or candidate.get('scope') != 'US14_ONLY'
            or candidate['stock_plan'] != stock.model_dump(mode='json')
            or set(candidate['current_subjects']) != subjects or len(candidate['current_subjects']) != len(subjects)
            or candidate['primary_monitored_subjects'] != list(UNIVERSE['us'])
            or candidate['auxiliary_issuer_subjects'] != ['000660']
            or set(candidate['financial_plans']) != subjects|{'000660'}
            or candidate['kr_market_reads']
            or {r['ticker'] for r in frozen['security_records']} != subjects
            or len(frozen['security_records']) != len(subjects)
            or {r['subject'] for r in frozen['news_reads']} != subjects
            or len(frozen['news_reads']) != len(subjects)
            or set(frozen.get('valuation_slots',{})) - subjects):
        raise ValueError('us14_primary_auxiliary_scope_mismatch')
    dependencies = candidate['auxiliary_issuer_dependencies']
    if set(dependencies) != {'000660'}:
        raise ValueError('us14_exact_auxiliary_dependency_required')
    dep = AuxiliaryIssuerDependency.model_validate(dependencies['000660'])
    if (dep.run_id != stock.run_id or dep.cutoff != stock.frozen_at
            or dep.source_plan_sha256 != digest(candidate['financial_plans']['000660'])
            or candidate['plan_sha256'] != digest({k:v for k,v in candidate.items() if k!='plan_sha256'})):
        raise ValueError('us14_auxiliary_plan_binding_mismatch')
    for descriptor in ProviderPlan.model_validate(frozen['plan']).descriptors:
        if descriptor.subject == '000660':
            if descriptor.consumer_role != 'financial:000660' or descriptor.provider != 'opendart':
                raise ValueError('us14_auxiliary_security_role_forbidden')
        elif descriptor.market == 'kr':
            if descriptor.consumer_role != 'ecos:USDKRW' and not descriptor.consumer_role.startswith('night:KOSPI200:'):
                raise ValueError('us14_undeclared_kr_context')
        if descriptor.consumer_role.startswith(('stock:kr:', 'kr_market:', 'events:000660', 'valuation:000660')):
            raise ValueError('us14_kr_stock_or_market_forbidden')
    return dep
