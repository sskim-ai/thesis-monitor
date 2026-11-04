"""Explicit dated public-packet enrichment, never a source/consumer grant."""
import copy
from app.services.vnext_codex_research import numeric_catalog
from app.services.vnext_research_store import digest
from app.services.vnext_price_zones import numeric_price_catalog

CONTRACT = 'vnext-dated-research-enrichment-v1'


def enrich_reported_amount(base, amount_packet, *, original_qualified_fact):
    """Join one original-replayed observation without replacing any base field."""
    packets = (base, amount_packet)
    if any(p.get('holdings_included') is not False or p.get('user_thesis_included') is not False
           or p.get('strict_native') is not False or p.get('live_authority') is not False for p in packets):
        raise ValueError('public_reference_scope_required')
    if (base['case'] != amount_packet['case'] or
            base['public_security'] != amount_packet['public_security']):
        raise ValueError('enrichment_security_mismatch')
    if len(amount_packet['evidence']) != 1:
        raise ValueError('single_amount_required')
    e = amount_packet['evidence'][0]
    fields = original_qualified_fact['fields']
    expected = {k: original_qualified_fact[k] for k in
                ('fields', 'as_of_date', 'quality_contract', 'quality_receipt_sha256')}
    if (e['data'] != expected or e['field'] != 'financial.' + fields['metric']
            or e['status'] != 'SOURCE_REFERENCE'
            or fields['source_ticker'] != base['case']):
        raise ValueError('original_reported_amount_mismatch')
    if (fields.get('observation_only') is not True or
            any(fields.get(k) is not False for k in
                ('comparison_eligible', 'recurrence_verified', 'valuation_denominator_eligible', 'strict_owner_issued'))):
        raise ValueError('dated_amount_scope_broadened')
    if any(x['field'] == e['field'] for x in base['evidence']):
        raise ValueError('existing_field_replacement_denied')
    result = copy.deepcopy(base)
    result['evidence'].append(copy.deepcopy(e))
    result['missing'] = [x for x in result['missing'] if x['field'] != e['field']]
    result['numeric_catalog'] = numeric_catalog(result) + numeric_price_catalog(result)
    result['enrichment_lineage'] = dict(contract=CONTRACT, base_packet_sha256=digest(base),
        amount_packet_sha256=digest(amount_packet), original_fact_sha256=digest(original_qualified_fact),
        base_run=base['run_id'], amount_run=amount_packet['run_id'], new_collection=False,
        added_ref=e['ref'], original_source_generation=fields['source_generation'],
        original_raw_sha256=fields['original_raw_sha256'], source_birth_relabelled=False,
        economic_or_native_authority_issued=False)
    return result


def amount_consumption(validation, packet):
    """Citation coverage is an observation, not an economic-quality score."""
    ref = packet.get('enrichment_lineage', {}).get('added_ref')
    rows = [r for r in validation['numeric_claims'] if r['fact_id'] == ref]
    rendered = validation['rendered']
    drivers = [d for side in ('economic_drivers_positive', 'economic_drivers_negative')
               for d in rendered[side] if ref in d['refs']]
    return dict(added_ref=ref, numeric_occurrences=rows, cited_drivers=drivers,
                cited=bool(rows or drivers), quality_improvement_inferred=False)
