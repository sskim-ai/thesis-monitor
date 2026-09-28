"""Exact denominator capability of the current bounded business projection.

This registry documents existing concepts, not permission to divide by every
number in a filing. A new denominator owner is needed to grant such permission.
"""
import json
from pathlib import Path

from app.providers.filings import FINANCIAL_ACCOUNT_IDS
from app.services.sec_financial_snapshot_service import _CONCEPTS, _IFRS_CONCEPTS
from app.services.bounded_financial_projection import CONTRACT, METRICS
from app.services.unified_snapshot_contract import digest


def denominator_scope(projection, *, security, issuer_bridge=None, source_inputs=None):
    names = ('basic_eps', 'diluted_eps', 'common_equity', 'owners_parent_equity', 'common_shares_outstanding')
    registry = dict(
        sec_us_gaap={k: list(_CONCEPTS[k]) for k in names if k in _CONCEPTS},
        sec_ifrs={k: list(_IFRS_CONCEPTS[k]) for k in names if k in _IFRS_CONCEPTS},
        opendart={k: sorted(FINANCIAL_ACCOUNT_IDS[k]) for k in names if k in FINANCIAL_ACCOUNT_IDS})
    fields = projection.get('fields', [])
    if any(f.get('contract') != CONTRACT or f.get('metric') not in METRICS for f in fields):
        raise ValueError('valuation_business_projection_scope_changed_requires_denominator_owner')
    if issuer_bridge:
        reason = 'ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY'
    else:
        reason = 'CURRENT_PROJECTION_OMITS_SECURITY_OWNED_DENOMINATORS'
    raw_scope = _raw_denominator_scope(source_inputs, security, registry) if source_inputs else None
    receipt = dict(contract='fresh-valuation-denominator-scope-v1',
        ticker=security['ticker'], security_sha256=digest(security), projection_sha256=digest(projection),
        registry=registry, registry_sha256=digest(registry), source_projection_contract=CONTRACT,
        projected_metrics=sorted({f['metric'] for f in fields}), raw_source_projection=raw_scope,
        source_field_hashes=sorted(f['normalized_hash'] for f in fields),
        requirements=dict(PER=['exact_share_class', 'currency_per_share', 'split_basis', 'four_compatible_quarters',
                              'raw_occurrence_lineage', 'current_price_basis'],
                          PBR=['exact_share_class', 'common_equity_attribution', 'same_basis_share_count',
                               'raw_occurrence_lineage', 'current_price_basis']),
        metrics={m: dict(status='UNAVAILABLE', denial_reason=reason, owned_denominator_refs=[],
            interpretation='Unavailability in this bounded projection, not absence in the issuer filing.')
            for m in ('PER', 'PBR')},
        forward=dict(status='UNAVAILABLE', denial_reason='NO_CONFIGURED_AUTHORIZED_EXACT_ESTIMATE_HORIZON_OWNER',
            configured_native_route='/api/v1/stock/metric', forwardPE_alone_eligible=False),
        historical=dict(status='UNAVAILABLE', denial_reason='NO_VERSIONED_SECURITY_METHOD_COMPATIBLE_DISTRIBUTION',
            current_native_method='PROVIDER_NATIVE_CURRENT_MULTIPLE',
            existing_history_method='weekly_last_valid_close_unadjusted_v2',
            interchangeable=False), overall_direction_use=False, source_authority_expanded=False)
    receipt['receipt_sha256'] = digest(receipt)
    return receipt


def _raw_denominator_scope(inputs, security, registry):
    """Project exact denominator candidates without inferring share dimensions.

    Companyfacts and the current DART account-list route do not provide a
    verified binding from an occurrence to this security's share class and
    split basis. Preserve the exact candidates and that limitation separately
    from the revenue-only business projection.
    """
    from app.services.bounded_financial_projection import _raw
    plan = inputs['plan']
    if plan['security'] != security:
        raise ValueError('valuation_denominator_source_security_mismatch')
    rows, sources = [], []
    directory = Path(inputs['directory']).resolve()
    for receipt in inputs['receipts']:
        if receipt.get('failure_class') or receipt.get('stage') not in {'companyfacts', 'statement'}:
            continue
        artifact = receipt['artifact']
        relative = Path(artifact)
        if relative.is_absolute() or '..' in relative.parts or any(
            directory.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError('valuation_denominator_source_path_invalid')
        payload = json.loads(_raw(directory, artifact, inputs['receipts']))
        sources.append(dict(artifact=artifact, raw_sha256=receipt['raw_sha256'], receipt_sha256=digest(receipt)))
        if receipt['stage'] == 'companyfacts':
            if str(payload.get('cik', '')).lstrip('0') != str(plan['issuer']).lstrip('0'):
                raise ValueError('valuation_denominator_issuer_mismatch')
            for taxonomy, concepts in (('us-gaap', registry['sec_us_gaap']), ('ifrs-full', registry['sec_ifrs'])):
                for metric, tags in concepts.items():
                    for tag in tags:
                        fact = payload.get('facts', {}).get(taxonomy, {}).get(tag, {})
                        for unit, occurrences in fact.get('units', {}).items():
                            for ordinal, raw in enumerate(occurrences):
                                rows.append(dict(metric=metric, semantic=taxonomy + ':' + tag, unit=unit,
                                    source_row_ordinal=ordinal, source_occurrence=raw, raw_sha256=receipt['raw_sha256'],
                                    security_basis='UNRESOLVED', split_basis='UNRESOLVED'))
        else:
            exact = {concept: metric for metric, tags in registry['opendart'].items() for concept in tags}
            for ordinal, raw in enumerate(payload.get('list', [])):
                if str(raw.get('corp_code', '')) != plan['issuer']:
                    raise ValueError('valuation_denominator_issuer_mismatch')
                metric = exact.get(str(raw.get('account_id', '')).lower())
                if metric:
                    rows.append(dict(metric=metric, semantic=raw['account_id'], source_row_ordinal=ordinal,
                        source_occurrence=raw, raw_sha256=receipt['raw_sha256'],
                        security_basis='UNRESOLVED', split_basis='UNRESOLVED'))
    result = dict(contract='valuation-specific-source-denominator-projection-v1',
        security_sha256=digest(security), plan_sha256=digest(plan), provider=plan['provider'],
        sources=sources, candidate_occurrences=rows,
        status='UNAVAILABLE', source_authority_expanded=False,
        reason=('EXACT_DENOMINATOR_CANDIDATES_LACK_CURRENT_SECURITY_SHARE_CLASS_SPLIT_BINDING' if rows
                else 'EXACT_STANDARD_DENOMINATOR_OCCURRENCES_ABSENT_IN_ACQUIRED_STRUCTURED_SOURCE'),
        limitations=['NO_SHARE_CLASS_OR_SPLIT_INFERENCE', 'NO_TOTAL_EQUITY_UNRELATED_SHARE_DIVISION',
                     'NO_MISSING_QUARTER_OR_ANNUAL_INTERIM_SYNTHESIS'],
        absence_scope='Acquired structured source only; does not assert absence in all issuer filings.')
    result['receipt_sha256'] = digest(result)
    return result
