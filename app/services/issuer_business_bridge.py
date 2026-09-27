"""Shadow-only, source-owned legal issuer identity and business scope.

The authoritative identity payload is a separately frozen input, not a name
match. The caller replays the source stock owner and its DART capture first.
No security master or valuation field is updated by this module.
"""
from copy import deepcopy
from datetime import date
from urllib.parse import urlparse

from app.services.unified_snapshot_contract import digest

CONTRACT = 'same-legal-issuer-business-evidence-bridge-v1'
REFERENCE_TYPE = 'ISSUER_LEVEL_CROSS_SECURITY_EVIDENCE'
ISSUER_METRICS = frozenset({
    'revenue', 'operating_income', 'net_income', 'operating_cash_flow',
    'ppe_capex_cash_outflow', 'free_cash_flow_ppe', 'inventory', 'receivables',
    'cash', 'interest_bearing_debt', 'issuer_business_event',
})


def identity_bridge(*, target, source, official, expected_official_sha256,
                    dart_rows, dart_receipt, cutoff):
    """Reuse qualified SEC instrument identity plus captured DART stock mapping."""
    errors = []
    evidence = official.get('evidence') or {}
    fields = official.get('field_provenance') or {}
    if digest(official) != expected_official_sha256:
        errors.append('official_identity_frozen_digest_mismatch')
    if (official.get('contract_version') != 'authoritative-security-identity-v1'
            or official.get('provider') != 'sec_official_identity'
            or official.get('source_tier') != 'tier_a_authoritative'):
        errors.append('official_identity_owner_unqualified')
    required = {
        'ticker': target.get('ticker'), 'cik': target.get('cik'),
        'ordinary_share_identifier': source.get('ticker'),
        'security_type': target.get('security_type'),
        'exchange': target.get('exchange'), 'issuer_type': target.get('issuer_type'),
    }
    for key, value in required.items():
        row = fields.get(key) or {}
        url = urlparse(str(row.get('source_url') or ''))
        try:
            temporal = date.fromisoformat(row['as_of']) <= date.fromisoformat(cutoff[:10])
            expected_prefix = '/Archives/edgar/data/' + str(int(target['cik'])) + '/'
        except (KeyError, TypeError, ValueError):
            temporal, expected_prefix = False, 'INVALID'
        if (not value or row.get('value') != value or evidence.get(key) != value
                or row.get('verification_status') != 'verified'
                or row.get('provider') != official.get('provider')
                or row.get('source_tier') != official.get('source_tier')
                or not temporal or row.get('as_of') != evidence.get('as_of_date')
                or not row.get('filing_accession')
                or row.get('filing_accession') != evidence.get('filing_accession')
                or not row.get('source_reference')
                or row.get('source_url') != evidence.get('source_url')
                or url.scheme != 'https' or url.hostname != 'www.sec.gov'
                or not url.path.startswith(expected_prefix)
                or row['filing_accession'].replace('-', '') not in url.path.split('/')):
            errors.append('official_security_field_unverified:' + key)
    if (target.get('security_type') != 'ads' or target.get('issuer_type') != 'adr'
            or source.get('security_type') != 'common_stock'
            or source.get('exchange') != 'KRX'):
        errors.append('instrument_relationship_not_supported')
    if (not isinstance(source.get('corp_code'), str) or len(source['corp_code']) != 8
            or not source['corp_code'].isdigit() or int(source['corp_code']) == 0):
        errors.append('source_legal_identifier_invalid')
    for record in (target, source):
        if not record.get('canonical_security_id') or not record.get('canonical_company_id'):
            errors.append('canonical_identity_missing')
        if record.get('identity_warnings') not in (None, '', '[]', []):
            errors.append('identity_conflict')
    if target.get('canonical_security_id') == source.get('canonical_security_id'):
        errors.append('cross_security_identity_not_distinct')
    if target.get('ordinary_share_identifier') not in (None, '', source.get('ticker')):
        errors.append('underlying_identity_conflict')
    if source.get('cik') not in (None, '', target.get('cik')):
        errors.append('issuer_cik_conflict')
    if target.get('corp_code') not in (None, '', source.get('corp_code')):
        errors.append('issuer_corp_code_conflict')
    mappings = {(r.get('stock_code'), r.get('corp_code')) for r in dart_rows}
    if (not source.get('corp_code') or mappings != {(source.get('ticker'), source.get('corp_code'))}
            or not dart_receipt or dart_receipt.get('stage') != 'discovery'
            or dart_receipt.get('HTTP_status') != 200 or dart_receipt.get('provider_status') != '000'
            or dart_receipt.get('failure_class') or not dart_receipt.get('raw_sha256')
            or not dart_receipt.get('request_sha256')):
        errors.append('official_dart_security_issuer_mapping_unverified')
    result = {
        'contract': CONTRACT, 'reference_type': REFERENCE_TYPE,
        'relationship': 'DEPOSITARY_TO_ISSUERS_OWN_ORDINARY_SECURITY',
        'status': 'FAIL' if errors else 'PASS', 'errors': sorted(set(errors)),
        'security_ticker': target.get('ticker'), 'underlying_ticker': source.get('ticker'),
        'monitored_security_id': target.get('canonical_security_id'),
        'source_security_id': source.get('canonical_security_id'),
        'target_company_id': target.get('canonical_company_id'),
        'source_company_id': source.get('canonical_company_id'),
        'issuer_id': 'DART:' + str(source.get('corp_code') or ''),
        'provider_issuer_ids': {'sec': target.get('cik'), 'opendart': source.get('corp_code')},
        'legal_issuer_id': 'legal-issuer-crosswalk:' + digest({
            'sec': target.get('cik'), 'opendart': source.get('corp_code'),
            'identity': digest(official), 'dart_receipt': digest(dart_receipt)}),
        'official_identity_sha256': digest(official), 'dart_receipt_sha256': digest(dart_receipt),
        'dart_raw_sha256': dart_receipt.get('raw_sha256'), 'cutoff': cutoff,
        'source_refs': [evidence.get('source_reference'), dart_receipt.get('logical_id')],
        'scope': 'issuer_business_only', 'security_valuation_transfer': False,
        'ISSUER_BUSINESS_EVIDENCE_ELIGIBLE': not errors,
        'SECURITY_PER_SHARE_BRIDGE_ELIGIBLE': False,
        'SECURITY_VALUATION_BRIDGE_ELIGIBLE': False,
    }
    result['receipt_sha256'] = digest(result)
    return result


def evidence_scope(*, metric, subject_scope, context_eligible, direction_eligible, denied=False):
    allowed = metric in ISSUER_METRICS and subject_scope == 'legal_issuer' and not denied
    return {'context_eligible': allowed and context_eligible is True,
            'direction_eligible': allowed and context_eligible is True and direction_eligible is True,
            'security_per_share_eligible': False, 'security_valuation_eligible': False}


def bind_comparison(projected, original, bridge, *, source_result_sha256):
    """Preserve the original dependency receipt and add a hash-bound bridge."""
    if (bridge.get('status') != 'PASS' or bridge.get('contract') != CONTRACT
            or bridge.get('receipt_sha256') != digest({k: v for k, v in bridge.items() if k != 'receipt_sha256'})):
        raise ValueError('issuer_bridge_receipt_missing_or_tampered')
    if (original.get('fact_type') != 'earnings_comparison'
            or not original.get('prose_eligible') or not original.get('interpretation_eligible')
            or projected.get('fields') != original.get('fields')
            or projected.get('field_dependency_receipts') != original.get('field_dependency_receipts')
            or projected.get('quality_receipt_sha256') != original.get('quality_receipt_sha256')
            or original['fields'].get('issuer_id') != bridge['issuer_id']
            or original['fields'].get('source_ticker') != bridge['underlying_ticker']
            or not source_result_sha256):
        raise ValueError('issuer_business_original_fact_mismatch')
    if original['fields']['metric'] not in {'revenue', 'operating_income', 'net_income'}:
        raise ValueError('issuer_business_metric_scope_denied')
    dependencies = original['field_dependency_receipts']
    for key in ('current', 'comparison'):
        occurrence = dependencies[key]
        if (occurrence.get('provider') != 'opendart' or not occurrence.get('prose_eligible')
                or occurrence.get('hard_denial_reasons')
                or occurrence['lineage'].get('source_provider') != 'opendart'):
            raise ValueError('issuer_business_original_quality_denied')
    fact = deepcopy(projected)
    fact['issuer_business_bridge'] = {
        'reference_type': REFERENCE_TYPE, 'source_provider': 'opendart',
        'bridge_receipt_sha256': bridge['receipt_sha256'],
        'monitored_security_id': bridge['monitored_security_id'],
        'legal_issuer_id': bridge['legal_issuer_id'], 'original_issuer_id': bridge['issuer_id'],
        'original_fact_id': original['fact_id'], 'original_fact_sha256': digest(original),
        'source_result_sha256': source_result_sha256,
        'source_document_id': original['fields']['source_receipt'],
        'source_occurrences': deepcopy(original['fields']['source_occurrences']),
        'scope': 'issuer_business_only', 'security_valuation_transfer': False,
    }
    return fact
