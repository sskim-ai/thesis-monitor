"""Offline stock prequalification with exact comparative financial owners.

This adapter is not a production dispatch route. Legacy controls bypass it.
Financial comparisons use the existing canonical comparative fact constructor;
no current amount by itself receives directional authority.
"""
from copy import deepcopy

from app.services.bounded_financial_projection import project
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet, stage_alias_catalogs
from app.services.numeric_semantic_registry import (
    build_numeric_registry, resolve_numeric_semantic, NumericSemanticSpec,
)
from app.services.packet_owned_technical_context_service import PacketOwnedTechnicalContext
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_owner import validate_assembled
from scripts.m12dr_financial_source_authority import comparative_facts, source_quality


def comparison_numeric_semantic(fact_type, path, fields):
    """Audit-only exact comparative binding, never a production resolver default."""
    if fact_type != 'earnings_comparison':
        return resolve_numeric_semantic(fact_type, path, fields)
    metric = fields.get('metric')
    role = {'fields.current_value':'current', 'fields.prior_comparable_value':'prior_comparable',
            'fields.delta':'difference', 'fields.growth_pct':'comparable_growth'}.get(path)
    currency = fields.get('currency')
    if metric not in {'revenue','operating_income','net_income'} or not role or currency not in {'USD','KRW','TWD','JPY','EUR','CNY'}:
        return None, 'number'
    unit = 'pct' if role=='comparable_growth' else currency
    semantic = 'reported_comparative_' + metric + '_' + role
    spec = NumericSemanticSpec(semantic, (unit,), (semantic,), (),
        'percentage' if unit=='pct' else 'currency_amount', False, 'stock')
    return spec, unit


def assemble(*, baseline, plan, acquisition, directory, receipts, local_seed):
    validate_assembled(baseline, expected_result_sha256=digest(baseline))
    if baseline['ticker'] != plan['ticker'] or baseline['market'] != plan['market']:
        raise ValueError('financial_stock_subject_mismatch')
    if digest(local_seed) != baseline['input_hashes']['local'] or digest(plan['security']) != plan['identity_sha256']:
        raise ValueError('financial_identity_input_hash_mismatch')
    identities = [r['record'] for component in local_seed['roles'].values() for r in component['records']
        if r['table']=='securitymaster' and r['record'].get('ticker')==plan['ticker']]
    if not identities or any(any(r.get(k)!=plan['security'].get(k) for k in
            ('canonical_company_id','canonical_security_id','cik','corp_code')) for r in identities):
        raise ValueError('financial_security_identity_mismatch')
    projection = project(plan, acquisition, directory, receipts)
    issuer = ('CIK:' if plan['market'] == 'us' else 'DART:') + plan['issuer']
    candidates = []
    for bundle in projection['quality_bundles']:
        quality = source_quality(bundle)
        if quality != bundle['quality']:
            raise ValueError('financial_quality_replay_changed')
        candidates.extend(comparative_facts(quality, ticker=plan['ticker'], issuer_id=issuer))
    groups = {}
    for fact in candidates:
        groups.setdefault(fact['fields']['metric'], []).append(fact)
    facts, denied = [], []
    for metric, values in groups.items():
        unique = {digest(f): f for f in values}
        if len(unique) != 1:
            denied.append({'metric': metric, 'reason': 'MULTIPLE_CURRENT_COMPARISON_OWNERS'})
        else:
            facts.extend(unique.values())
    # Preserve the complete baseline artifact; enrich only a detached packet.
    packet = deepcopy(baseline['packet'])
    packet.update(packet_id=plan['run_id'] + ':' + plan['market'], generated_at=plan['cutoff'], assessment_date=plan['cutoff'][:10])
    packet['source_time_domains'] = {**packet.get('source_time_domains', {}),
        'financial_acquisition_cutoff': plan['cutoff'], 'financial_plan_sha256': digest(plan),
        'scope': 'MIXED_TIME_SOURCE_PREQUALIFICATION_NOT_PRODUCTION_DECISION'}
    stock = packet['stocks'][0]
    stock['fact_catalog'].extend(facts)
    stock['numeric_registry'] = build_numeric_registry(stock['fact_catalog'], semantic_resolver=comparison_numeric_semantic)
    technical = PacketOwnedTechnicalContext.model_validate(stock['technical_context'])
    evidence = build_decision_evidence_packet(packet=packet, stock=stock, technical_context=technical)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    stage_alias_catalogs(owned)
    comparative_ids = {'canonical:' + f['fact_id'] for f in facts}
    consumed = [r.ref_id for r in evidence.evidence if r.ref_id in comparative_ids]
    if set(consumed) != comparative_ids:
        raise ValueError('financial_comparison_typed_ref_loss')
    missing = list(baseline['mandatory_missing'])
    if consumed:
        missing = [m for m in missing if m != 'observed_business_union:eligible_reported_financial_or_event']
    bad_numeric = [r for r in stock['numeric_registry'] if not r['registered']]
    if bad_numeric:
        missing.append('numeric_registry:unregistered_fields')
    complete = not missing and not acquisition.get('denials')
    return {'contract': 'bounded-financial-stock-owner-v1', 'ticker': plan['ticker'], 'market': plan['market'],
        'status': 'PASS' if complete else 'BLOCKED', 'mandatory_missing': sorted(set(missing)),
        'acquisition_denials': acquisition.get('denials', []), 'comparison_denials': denied,
        'baseline_sha256': digest(baseline), 'projection': projection,
        'input_hashes': {'plan': digest(plan), 'acquisition': digest(acquisition), 'receipts': digest(receipts)},
        'packet': packet, 'packet_sha256': digest(packet) if complete else None,
        'diagnostic_packet_sha256': digest(packet), 'evidence_packet': evidence.model_dump(mode='json'),
        'ownership': owned.model_dump(mode='json'), 'comparative_fact_refs': sorted(consumed),
        'observed_business_cardinality': baseline['observed_business_cardinality'] + len(consumed),
        'financial_source_graph': {f['fact_id']: {'fact_sha256': digest(f),
            'projection_sha256': digest(projection), 'plan_sha256': digest(plan),
            'occurrences': f['fields']['source_occurrences'], 'quality_receipt_sha256': f['quality_receipt_sha256']}
            for f in facts},
        'numeric_registry_unregistered': bad_numeric, 'production_dispatch_enabled': False}


def validate(result, **inputs):
    if assemble(**inputs) != result:
        raise ValueError('financial_stock_replay_mismatch')
    return result['status'] == 'PASS'
