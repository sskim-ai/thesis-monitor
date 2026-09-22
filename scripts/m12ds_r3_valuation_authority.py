"""Exact frozen security/denominator lineage, never a tag-wide valuation grant."""
from copy import deepcopy
from datetime import date
from math import isclose

from app.services.cross_market_decision_engine_service import _compact
from app.services.financial_quality_service import CRITICAL_REASON_CODES, PROSE_USABLE_STATES
from scripts.m12da_source_use_contract import SourceUse, canonical_sha256
from scripts.m12ds_r2_judgment_policy import number

CONTRACT = 'm12ds-r3-exact-earnings-valuation-authority-v1'
FACTS = {
    'valuation:trailing_earnings': ('ttm_eps', 'trailing_pe'),
    'valuation:consensus_forward_earnings': ('forward_eps', 'forward_pe'),
    'valuation:modeled_forward_earnings': ('forward_eps', 'forward_pe'),
}


def day(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def earnings_receipt(row, stock, packet, record):
    fid = str(row.get('source_ref', '')).removeprefix('stock.fact_catalog.')
    errors = []
    receipt = {'contract': CONTRACT, 'ticker': stock['ticker'], 'ref_id': row['ref_id'],
               'source_metadata_sha256': canonical_sha256(row), 'errors': errors,
               'numeric_prose_permission_changed': False}
    matches = [f for f in stock.get('fact_catalog', []) if f.get('fact_id') == fid]
    if fid not in FACTS or len(matches) != 1:
        return {**receipt, 'status': 'FAIL', 'errors': ['exact_earnings_fact_missing']}
    fact, val = matches[0], stock.get('valuation') or {}
    receipt['frozen_fact_sha256'] = canonical_sha256(fact)
    receipt['valuation_owner_sha256'] = canonical_sha256(val)
    if (row.get('ref_id') != 'canonical:' + fid or row.get('statement') != _compact(fact.get('fields', {}))
            or row.get('as_of') != fact.get('as_of_date') or row.get('label') != 'valuation_interpretation'
            or record.get('source_metadata_sha256') != canonical_sha256(row)):
        errors.append('exact_source_owner_or_metadata_digest_mismatch')
    if not day(fact.get('as_of_date')) or not day(packet.get('assessment_date')) or fact.get('as_of_date', '') > packet['assessment_date']:
        errors.append('source_availability_unknown')
    if (val.get('security_identity_decision_version') != 'security-identity-v2'
            or val.get('security_identity_verification_status') != 'verified'
            or val.get('security_identity_state') != 'verified_non_depositary'
            or val.get('resolved_security_type') != 'common_stock'
            or val.get('is_depositary_security') is not False
            or val.get('security_identity_conflict_reasons')):
        errors.append('same_traded_non_depositary_security_unverified')
    currency = val.get('currency')
    if not currency or currency != val.get('eps_currency') or val.get('eps_security_basis') != 'current_security':
        errors.append('eps_currency_or_security_denominator_unverified')
    if fact.get('valuation_scope') != 'listed_security' or fact.get('interpretation_eligible') is not True or fact.get('prose_eligible') is not True:
        errors.append('field_interpretation_or_prose_ineligible')
    trailing = fid == 'valuation:trailing_earnings'
    eps_key, multiple_key = FACTS[fid]
    fields = fact.get('fields') or {}
    if not fields or set(fields) - set(FACTS[fid]) or eps_key not in fields:
        errors.append('unexpected_or_missing_earnings_fields')
    quality_fields = (val.get('financial_quality') or {}).get('fields') or {}
    for name, value in fields.items():
        quality = (fact.get('field_quality') or {}).get('fields.' + name) or {}
        if (number(value) is None or value != val.get(name) or not quality or quality != quality_fields.get(name)
                or quality.get('decision_version') != 'financial-quality-taint-v2'
                or quality.get('state') not in PROSE_USABLE_STATES or quality.get('prose_eligible') is not True
                or quality.get('lineage_verification_status') != 'verified' or quality.get('denial_reason')
                or set(quality.get('quality_reason_codes') or []) & CRITICAL_REASON_CODES):
            errors.append('unverified_or_denied_field:' + name)
    if val.get(multiple_key + '_basis_status') != 'directly_comparable' or val.get(multiple_key + '_basis_conflict') is not False:
        errors.append('security_multiple_basis_unverified')
    if trailing:
        series = val.get('earnings_quarter_series') or []
        periods = [q.get('period') for q in series]
        q = (fact.get('field_quality') or {}).get('fields.ttm_eps') or {}
        if (val.get('ttm_eps_usable') is not True or val.get('ttm_contains_preliminary') is not False
                or len(series) != 4 or any(not day(p) for p in periods)
                or periods != sorted(set(periods)) or periods != q.get('dependency_periods')
                or not periods or val.get('ttm_period_start') != periods[0] or val.get('ttm_period_end') != periods[-1]
                or q.get('source_type') != 'derived_trailing'
                or q.get('dependency_fields') != ['earnings_quarter_series.eps']):
            errors.append('ttm_period_or_dependency_owner_unverified')
        if len(series) == 4 and all(day(p) for p in periods):
            gaps = [(date.fromisoformat(b) - date.fromisoformat(a)).days for a, b in zip(periods, periods[1:])]
            if not all(70 <= d <= 110 for d in gaps):
                errors.append('ttm_quarter_sequence_incompatible')
        for item in series:
            if (item.get('normalized_eps_usable') is not True or item.get('context_usable') is not True
                    or item.get('eps_security_basis') != 'current_security' or item.get('eps_currency') != currency
                    or item.get('share_basis') not in ('reported_diluted_eps', 'reported_basic_eps')
                    or number(item.get('eps')) is None or not day(item.get('filing'))
                    or item.get('filing', '') > packet['assessment_date']):
                errors.append('quarter_security_share_or_availability_unverified')
        if series and all(number(q.get('eps')) is not None for q in series) and number(val.get('ttm_eps')) is not None:
            if not isclose(sum(q['eps'] for q in series), val['ttm_eps'], rel_tol=1e-9, abs_tol=1e-9):
                errors.append('ttm_denominator_arithmetic_mismatch')
        if len({q.get('share_basis') for q in series}) != 1:
            errors.append('mixed_share_basis')
        receipt['denominator_periods'] = periods
    else:
        # Forward ownership must exist on this same frozen security, never inferred from TTM.
        quality = (fact.get('field_quality') or {}).get('fields.forward_eps') or {}
        if (fid != 'valuation:consensus_forward_earnings'
                or val.get('forward_pe_source') != 'consensus_forward' or not day(val.get('forward_pe_input_period'))
                or val.get('forward_pe_input_period', '') <= packet['assessment_date']
                or val.get('forward_eps_security_basis') != 'current_security'
                or val.get('forward_eps_currency') != currency
                or val.get('forward_eps_share_basis') not in ('diluted_eps', 'basic_eps')
                or quality.get('source_type') != 'consensus_forward'
                or quality.get('dependency_fields') != ['independent_provider_consensus', 'verified_per_security_basis']
                or quality.get('dependency_periods') != [val.get('forward_pe_input_period')]):
            errors.append('forward_denominator_owner_or_period_unverified')
        receipt['denominator_periods'] = [val.get('forward_pe_input_period')]
    receipt['status'] = 'FAIL' if errors else 'PASS'
    return receipt


def extend_authority(base, *, packet, evidence_packet, metadata):
    result = deepcopy(base)
    ticker = evidence_packet['ticker']
    stock = next(s for s in packet['stocks'] if s['ticker'] == ticker)
    frozen = base['frozen_binding']
    if (frozen['source_packet_sha256'] != canonical_sha256(packet)
            or frozen['stock_sha256'] != canonical_sha256(stock)
            or frozen['evidence_packet_sha256'] != canonical_sha256(evidence_packet)):
        raise ValueError('valuation_authority_current_input_drift')
    rows = {r['ref_id']: r for r in metadata}
    source_rows = {r['ref_id']: r for r in evidence_packet['evidence']}
    receipts = []
    for record in result['authority']['authority_records']:
        row = rows[record['ref_id']]
        if row != source_rows.get(row['ref_id']):
            raise ValueError('valuation_authority_metadata_not_frozen')
        if row.get('source_ref', '').removeprefix('stock.fact_catalog.') not in FACTS:
            continue
        receipt = earnings_receipt(row, stock, packet, record)
        if record['source_family'] not in ('unclassified', 'typed_valuation'):
            receipt['errors'].append('existing_restrictive_owner_not_replaced')
            receipt['status'] = 'FAIL'
        receipt['previous_allowed_uses'] = record['allowed_uses'][:]
        if receipt['status'] == 'PASS':
            allowed = set(record['allowed_uses']) | {SourceUse.VALUATION.value, SourceUse.ENTRY.value, SourceUse.PRICE_ENTRY_CONTEXT.value}
            record.update(allowed_uses=sorted(allowed), prohibited_uses=sorted({u.value for u in SourceUse} - allowed),
                          authority_state='RESOLVED', authority_basis=CONTRACT,
                          source_family='EXACT_SECURITY_EARNINGS_VALUATION', source_scope='valuation_and_entry_only',
                          denial_reasons=['ungranted_uses_remain_prohibited'],
                          earnings_valuation_receipt_sha256=canonical_sha256(receipt))
        receipt['final_allowed_uses'] = record['allowed_uses'][:]
        receipts.append(receipt)
    manifest = result['authority']
    manifest['exact_earnings_valuation_contract'] = CONTRACT
    manifest['exact_earnings_valuation_receipts_sha256'] = canonical_sha256(receipts)
    manifest.pop('authority_manifest_sha256')
    manifest['authority_manifest_sha256'] = canonical_sha256(manifest)
    result['earnings_valuation_receipts'] = receipts
    return result
