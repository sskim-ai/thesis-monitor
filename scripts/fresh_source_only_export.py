"""Read-only, allowlisted evidence projection for independent blind review.

This is not a model request materializer. Source objects, source authority and
model contracts are never rewritten to satisfy the review archive.
"""
from copy import deepcopy
import json

from app.services.current_fresh_valuation import CurrentValuationView
from app.services.selected_financial_owner import SelectedFinancialOwnerEnvelope
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_stock_owner import reject_downstream
from scripts.m12da_source_use_contract import canonical_sha256


CONTRACT = 'fresh-owner-source-only-review-v1'
EXCLUDED = frozenset({
    'model_output', 'market_output', 'core_output', 'pass_a_output', 'pass_b_output',
    'raw_response', 'raw_responses', 'accepted_result', 'accepted_results',
    'ai_confidence', 'ai_new_buyer', 'ai_holder', 'ai_reevaluation',
    'external_judgment', 'independent_assessment', 'human_comparison',
    'prompt', 'system_prompt', 'model_prompt', 'output_schema', 'target_label',
})
EXCLUDED_CATEGORIES = (
    'Market/Core/A/B outputs', 'AI decisions/balance/confidence/axis labels',
    'rendered messages', 'raw model responses/accepted results',
    'prior independent judgment/comparison', 'prompts/schemas/model policy routing',
)
SOURCE_CATEGORIES = ('identity', 'financial', 'events', 'price', 'technical',
                     'quality', 'valuation', 'flow_positioning', 'provenance')


def _generation(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('source_only_generation_nonempty_string_required')
    return value


def resolve_full_source_generation_identity(whole_source):
    """Current serialized owner; a legacy alias may corroborate, never replace it."""
    seed = whole_source.get('seed')
    if not isinstance(seed, dict) or 'parent_run_id' not in seed:
        raise ValueError('source_only_parent_generation_required')
    parent = _generation(seed['parent_run_id'])
    if 'run_id' in seed and _generation(seed['run_id']) != parent:
        raise ValueError('source_only_seed_generation_conflict')
    return parent


def source_only_generation_preflight(whole_source, *, source_view_generation_id,
                                     provider_generation_id, kis_generation_id):
    generation = resolve_full_source_generation_identity(whole_source)
    identities = dict(source_view=source_view_generation_id, provider=provider_generation_id,
                      kis=kis_generation_id)
    for role, value in identities.items():
        if _generation(value) != generation:
            raise ValueError('source_only_' + role + '_generation_mismatch')
    return dict(status='PASS', generation_id=generation, identity_path='seed.parent_run_id',
                identities={'full_source': generation, **identities}, identity_rewritten=False)


def reject_review_contamination(value):
    reject_downstream(value)
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in EXCLUDED:
                raise ValueError('source_only_downstream_forbidden:' + key)
            reject_review_contamination(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_review_contamination(child)
    elif isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try:
            parsed = json.loads(value)
        except ValueError:
            return
        reject_review_contamination(parsed)


def _select(value, keys):
    return {key: deepcopy(value[key]) for key in keys if key in value}


def _financial(stock, facts):
    if not stock.get('selected_financial_owner'):
        raise ValueError('source_only_selected_financial_owner_required')
    owner = SelectedFinancialOwnerEnvelope.model_validate(
        stock['selected_financial_owner']).model_dump(mode='json')
    if (owner['envelope_sha256'] != digest({k: v for k, v in owner.items() if k != 'envelope_sha256'})
            or owner['monitored_security'] != stock['ticker']
            or stock['input_hashes']['selected_financial_owner'] != owner['envelope_sha256']):
        raise ValueError('source_only_selected_financial_owner_mismatch')
    ids = owner['selected_fact_ids']
    graph = stock['financial_source_graph']
    catalog = {fact['fact_id']: fact for fact in facts}
    if (len(catalog) != len(facts) or len(ids) != len(set(ids)) or set(ids) != set(graph)
            or not set(ids) <= set(catalog)
            or set(stock['comparative_fact_refs']) != {'canonical:' + i for i in ids}):
        raise ValueError('source_only_financial_fact_set_mismatch')
    for fact_id in ids:
        node = graph[fact_id]
        if (node != stock['source_graph'].get(fact_id)
                or node['fact_sha256'] != digest(catalog[fact_id])):
            raise ValueError('source_only_financial_source_binding_mismatch')
    if not owner['bridge_receipt'] and owner['selected_projection_sha256'] != digest(stock['projection']):
        raise ValueError('source_only_selected_projection_mismatch')
    if owner['bridge_receipt'] != stock.get('issuer_business_bridge'):
        raise ValueError('source_only_selected_bridge_mismatch')
    return dict(selected_financial_owner=owner, financial_source_graph=deepcopy(graph),
                financial_state=deepcopy(stock['financial_state']),
                comparison_denials=deepcopy(stock['comparison_denials']),
                acquisition_denials=deepcopy(stock['acquisition_denials']),
                context_fact_refs=deepcopy(stock['context_fact_refs']),
                selected_field_location='facts selected by selected_financial_owner.selected_fact_ids',
                direct_projection_role='UNSELECTED_DIRECT_OWNER' if owner['bridge_receipt'] else 'SELECTED_DIRECT_OWNER',
                selected_source_fields=None if owner['bridge_receipt'] else _select(stock['projection'], (
                    'fields', 'comparisons', 'comparison_applicability', 'denials', 'freshness',
                    'financial_field_completeness', 'source_completeness', 'context_eligible',
                    'direction_eligible', 'latest_selected_period_unavailable')))


def _valuation(stock, subject):
    value = stock['valuation_view']
    CurrentValuationView.model_validate(value)
    if (value != subject['current_valuation_view'] or value['ticker'] != stock['ticker']
            or value['run_id'] != stock['fresh_run_id']
            or value['price_context_sha256'] != digest(subject['current_price_context'])
            or stock['input_hashes']['valuation'] != digest(value)):
        raise ValueError('source_only_valuation_binding_mismatch')
    for metric in value['metrics']:
        if metric['status'] == 'QUALIFIED' and metric['source_method'] == 'provider_native_latest_snapshot':
            native = metric.get('native_snapshot') or {}
            if not native.get('source_receipt_sha256') or not native.get('raw_sha256'):
                raise ValueError('source_only_valuation_receipt_required')
    result = _select(value, (
        'contract', 'ticker', 'security_id', 'run_id', 'currency', 'price', 'price_session',
        'price_basis', 'price_context_sha256', 'security_sha256', 'financial_projection_sha256',
        'owner_output_sha256', 'metrics', 'historical_distribution', 'overall_direction_use',
        'unadjusted_price_binding', 'security_basis_receipt'))
    # Unqualified historical denominator candidates are not current facts.
    # Preserve their exact identity and denial, not a giant historical inventory.
    result['denominator_scope_receipt'] = _select(value.get('denominator_scope_receipt') or {}, (
        'contract', 'status', 'reason', 'limitations', 'receipt_sha256', 'source_authority_expanded'))
    result['original_valuation_view_sha256'] = digest(value)
    result['omitted_denominator_inventory_sha256'] = digest(value.get('denominator_candidate_inventory', []))
    return result


def source_only_fresh_stock(stock, authority):
    if stock.get('contract') != 'fresh-financial-stock-owner-v1':
        raise ValueError('source_only_fresh_contract_required')
    reject_review_contamination(stock)
    reject_review_contamination(authority)
    packet = stock['packet']
    if (len(packet['stocks']) != 1 or packet['stocks'][0]['ticker'] != stock['ticker']
            or packet['market'] != stock['market']
            or packet['source_time_domains']['run_id'] != stock['fresh_run_id']
            or stock['diagnostic_packet_sha256'] != digest(packet)
            or stock['packet_sha256'] not in (None, digest(packet))):
        raise ValueError('source_only_packet_identity_mismatch')
    source_authority = authority['authority']
    if source_authority['authority_manifest_sha256'] != canonical_sha256(
            {k: v for k, v in source_authority.items() if k != 'authority_manifest_sha256'}):
        raise ValueError('source_only_authority_hash_mismatch')
    subject = packet['stocks'][0]
    facts = deepcopy(subject['fact_catalog'])
    result = dict(contract=CONTRACT, ticker=stock['ticker'], market=stock['market'],
                  generation_id=stock['fresh_run_id'],
                  identity=_select(subject, ('ticker', 'company_name', 'sector', 'industry',
                                              'business_model', 'revenue_sources')),
                  source_time_domains=deepcopy(packet['source_time_domains']),
                  source_object_sha256=digest(stock), original_source_packet_sha256=digest(packet),
                  facts=facts, financial=_financial(stock, facts),
                  price=dict(current_price_context=deepcopy(subject['current_price_context']),
                             completed_session_current_price=deepcopy(stock['completed_session_current_price'])),
                  technical=_select(subject, ('technical_context', 'chart_context')),
                  quality=dict(quality_view=deepcopy(stock['quality_view']),
                               data_cautions=deepcopy(subject['data_cautions']),
                               mandatory_missing=deepcopy(stock['mandatory_missing'])),
                  valuation=_valuation(stock, subject),
                  events=_select(stock, ('event_view', 'event_fact_refs')),
                  flow_positioning=deepcopy(subject['price_and_positioning']),
                  provenance=_select(stock, ('source_graph', 'evidence_reference_graph',
                                             'numeric_registry_graph', 'component_binding', 'input_hashes')),
                  data_use_authority=deepcopy(source_authority))
    reject_review_contamination(result)
    return result


def source_only_market(packet, *, generation_id):
    source = packet['market_sources']
    if source['run_id'] != generation_id or packet['market'] not in UNIVERSE:
        raise ValueError('source_only_market_generation_mismatch')
    reject_review_contamination(packet)
    result = dict(contract=CONTRACT, market=packet['market'], generation_id=generation_id,
                  original_whole_packet_sha256=digest(packet),
                  **_select(packet, ('market_sources', 'night_and_publication_context',
                                    'optional_denials', 'publication_context')))
    reject_review_contamination(result)
    return result


def project_cohort(whole, *, generation_id, whole_source_sha256):
    return _project_cohort(whole, generation_id=generation_id,
        whole_source_sha256=whole_source_sha256, universe=UNIVERSE)


def project_us14_cohort(whole, *, generation_id, whole_source_sha256):
    from app.services.unified_full_source_cohort import FreshUSSourceRunSeed
    seed = FreshUSSourceRunSeed.model_validate(whole['seed'])
    if seed.parent_run_id != generation_id:
        raise ValueError('source_only_us14_generation_mismatch')
    auxiliary = whole['authority_graph'].get('auxiliary_issuers')
    if not auxiliary or set(auxiliary) != {'000660'} or digest(auxiliary) != seed.auxiliary_issuer_set_sha256:
        raise ValueError('source_only_us14_auxiliary_binding_mismatch')
    result = _project_cohort(whole, generation_id=generation_id,
        whole_source_sha256=whole_source_sha256, universe=seed.universe)
    result['audit'].update(scope='US14_ONLY', auxiliary_issuer_set_sha256=seed.auxiliary_issuer_set_sha256)
    return result


def _project_cohort(whole, *, generation_id, whole_source_sha256, universe):
    if digest(whole) != whole_source_sha256 or set(whole['packets']) != set(universe):
        raise ValueError('source_only_whole_identity_mismatch')
    expected = {t for ts in universe.values() for t in ts}
    if set(whole['authority_graph']['stocks']) != expected:
        raise ValueError('source_only_authority_roster_mismatch')
    stocks, markets, rows = {}, {}, []
    for market, tickers in universe.items():
        packet = whole['packets'][market]
        if packet['market'] != market or set(packet['stocks']) != set(tickers):
            raise ValueError('source_only_exact_roster_required')
        for ticker in tickers:
            stock = packet['stocks'][ticker]
            if stock['ticker'] != ticker or stock['market'] != market or stock['fresh_run_id'] != generation_id:
                raise ValueError('source_only_stock_generation_mismatch')
            projected = source_only_fresh_stock(stock, whole['authority_graph']['stocks'][ticker])
            stocks[ticker] = projected
            rows.append(dict(ticker=ticker, market=market, generation_id=generation_id,
                             projection_sha256=digest(projected), source_object_sha256=digest(stock),
                             selected_fact_count=len(projected['financial']['selected_financial_owner']['selected_fact_ids']),
                             categories=list(SOURCE_CATEGORIES), status='PASS'))
        markets[market] = source_only_market(packet, generation_id=generation_id)
    audit = dict(contract=CONTRACT, status='PASS', generation_id=generation_id,
                 whole_source_sha256=whole_source_sha256, included_subjects=sorted(stocks),
                 stock_count=len(stocks), market_count=len(markets), rows=rows,
                 markets={m: dict(projection_sha256=digest(p), source_object_sha256=digest(whole['packets'][m]))
                          for m, p in markets.items()},
                 included_source_categories=list(SOURCE_CATEGORIES),
                 excluded_downstream_categories=list(EXCLUDED_CATEGORIES),
                 downstream_exclusion='RECURSIVE_INPUT_AND_OUTPUT_REJECTION_PLUS_ALLOWLIST',
                 legacy_reconstruction=False, model_output_reads=0, provider_calls=0)
    return dict(stocks=stocks, markets=markets, audit=audit)
