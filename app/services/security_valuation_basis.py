"""Security valuation capability over exact acquired denominator occurrences.

This owner records missing authority; hashes and issuer identity alone cannot
grant share-class or corporate-action compatibility. No fetch or persistence.
"""
from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest


UnavailableState = Literal[
    'UNAVAILABLE_SECURITY_BASIS', 'UNAVAILABLE_DENOMINATOR',
    'UNAVAILABLE_ESTIMATE_HORIZON', 'UNAVAILABLE_SOURCE_QUALITY',
    'UNAVAILABLE_OTHER_TYPED_REASON',
]


class SecurityValuationBasisReceipt(ContractModel):
    """A denial receipt, not an assertion of authority by the caller.

    The currently acquired source routes have no class/split materializer.
    QUALIFIED is deliberately not representable until that owner is present.
    """
    contract: Literal['security-valuation-basis-v1'] = 'security-valuation-basis-v1'
    ticker: str
    run_id: str
    monitored_security_id: str
    provider_security_id: str | None
    security_class: str | None
    listing_exchange: str | None
    currency: str
    price_adjustment_basis: str
    corporate_action_split_basis: Literal['UNRESOLVED'] = 'UNRESOLVED'
    denominator_adjustment_basis: Literal['UNRESOLVED'] = 'UNRESOLVED'
    as_of: date
    security_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    price_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    candidate_inventory_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    provenance_refs: tuple[str, ...]
    status: Literal['UNAVAILABLE_SECURITY_BASIS'] = 'UNAVAILABLE_SECURITY_BASIS'
    denial_reasons: tuple[str, ...] = Field(min_length=1)
    overall_direction_use: Literal[False] = False
    security_valuation_transfer: Literal[False] = False
    basis_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def bound_receipt(self):
        if self.basis_sha256 != digest(self.model_dump(mode='json', exclude={'basis_sha256'})):
            raise ValueError('security_valuation_basis_receipt_mismatch')
        return self


class ValuationCandidate(ContractModel):
    occurrence_id: str
    metric: str
    semantic: str
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    raw_row_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_row_ordinal: int = Field(ge=0)
    filing_accession: str | None
    period_start: str | None
    period_end: str | None
    period_type: Literal['DURATION_UNRESOLVED', 'INSTANT', 'UNRESOLVED']
    source_fiscal_period_label: str | None
    statement_basis: str
    currency_unit: str | None
    security_class_dimensions: Literal['UNRESOLVED'] = 'UNRESOLVED'
    split_basis: Literal['UNRESOLVED'] = 'UNRESOLVED'
    publication_date: str | None
    revision_state: Literal['LATEST_REPORTED_OCCURRENCE', 'SUPERSEDED_OCCURRENCE', 'UNRESOLVED']
    selected: Literal[False] = False
    exclusion_reasons: tuple[str, ...] = Field(min_length=1)


def candidate_inventory(raw_scope):
    """Inventory every row before selection; never annualize interim EPS.

    Only exact same-period/concept/unit/basis occurrences have a revision
    relationship. Newer unresolved rows remain excluded; no older fallback.
    """
    candidates = []
    for candidate in (raw_scope or {}).get('candidate_occurrences', []):
        row = candidate['source_occurrence']
        sec = 'val' in row and 'accn' in row
        start = row.get('start') if sec else None
        end = row.get('end') if sec else None
        publication = row.get('filed') if sec else None
        period_type = 'UNRESOLVED'
        if sec and end:
            if not start:
                period_type = 'INSTANT'
            else:
                # Filing focus is not occurrence duration. Fiscal metadata and
                # class authority must be joined by a separate source owner.
                period_type = 'DURATION_UNRESOLVED'
        elif not sec and row.get('sj_div') == 'BS':
            # The account endpoint supplies no verified instant context here.
            period_type = 'UNRESOLVED'
        reasons = ['SECURITY_CLASS_DIMENSIONS_UNRESOLVED', 'SPLIT_BASIS_UNRESOLVED']
        if period_type in {'UNRESOLVED', 'DURATION_UNRESOLVED'}:
            reasons.append('EXACT_DENOMINATOR_PERIOD_UNQUALIFIED')
        if not publication:
            reasons.append('PUBLICATION_DATE_UNVERIFIED')
        if candidate['metric'] in {'common_equity', 'owners_parent_equity'}:
            reasons.append('COMMON_CLASS_EQUITY_ATTRIBUTION_UNQUALIFIED')
        if candidate['metric'] == 'common_shares_outstanding':
            reasons.append('POINT_IN_TIME_COMMON_CLASS_SHARES_UNQUALIFIED')
        candidates.append(ValuationCandidate(
            occurrence_id='valuation-occurrence:' + digest(candidate), metric=candidate['metric'],
            semantic=candidate['semantic'], source_sha256=candidate['raw_sha256'],
            raw_row_sha256=digest(row), source_row_ordinal=candidate['source_row_ordinal'],
            filing_accession=row.get('accn') if sec else row.get('rcept_no'),
            period_start=start, period_end=end, period_type=period_type,
            source_fiscal_period_label=row.get('fp') if sec else row.get('reprt_code'),
            statement_basis='UNRESOLVED' if sec else row.get('fs_div') or 'UNRESOLVED',
            currency_unit=candidate.get('unit') if sec else row.get('currency'),
            publication_date=publication, revision_state='UNRESOLVED', exclusion_reasons=tuple(reasons)))
    groups = {}
    for candidate in candidates:
        if candidate.period_end and candidate.publication_date:
            key = (candidate.metric, candidate.semantic, candidate.period_start, candidate.period_end,
                   candidate.statement_basis, candidate.currency_unit)
            groups.setdefault(key, []).append(candidate)
    states = {}
    for group in groups.values():
        latest = max(c.publication_date for c in group)
        for candidate in group:
            states[candidate.occurrence_id] = ('LATEST_REPORTED_OCCURRENCE'
                if candidate.publication_date == latest else 'SUPERSEDED_OCCURRENCE')
    output = []
    for candidate in candidates:
        state = states.get(candidate.occurrence_id, 'UNRESOLVED')
        reasons = candidate.exclusion_reasons
        if state == 'SUPERSEDED_OCCURRENCE':
            reasons += ('NEWER_SAME_PERIOD_OCCURRENCE_EXISTS_NO_STALE_FALLBACK',)
        output.append(ValuationCandidate.model_validate({**candidate.model_dump(),
            'revision_state': state, 'exclusion_reasons': reasons}).model_dump(mode='json'))
    return output


def unresolved_basis(*, ticker, run_id, security, price, inventory, issuer_bridge=None):
    reasons = ['NO_ACQUIRED_SECURITY_CLASS_SPLIT_AUTHORITY_OWNER']
    if issuer_bridge:
        reasons.append('ISSUER_BRIDGE_CANNOT_GRANT_SECURITY_VALUATION')
    if security.get('security_type') in {'adr', 'ads'} or security.get('issuer_type') == 'adr':
        reasons.append('EXACT_ADR_CONVERSION_BASIS_UNPROVEN')
    if price.get('price_basis') not in {'close', 'regular_close'}:
        reasons.append('UNADJUSTED_CURRENT_PRICE_OWNER_UNPROVEN')
    values = dict(ticker=ticker, run_id=run_id,
        monitored_security_id=security['canonical_security_id'],
        provider_security_id=security.get('figi'), security_class=security.get('share_class'),
        listing_exchange=security.get('exchange'), currency=price['currency'],
        price_adjustment_basis=price['price_basis'], as_of=str(price['as_of_date']),
        security_sha256=digest(security), price_sha256=digest(price),
        candidate_inventory_sha256=digest(inventory),
        provenance_refs=tuple(sorted({row['source_sha256'] for row in inventory})),
        denial_reasons=tuple(reasons))
    # Include model defaults in the digest without allowing a caller to sign a
    # QUALIFIED state; the type admits only the acquired route's actual scope.
    values.update(contract='security-valuation-basis-v1', corporate_action_split_basis='UNRESOLVED',
        denominator_adjustment_basis='UNRESOLVED', status='UNAVAILABLE_SECURITY_BASIS',
        overall_direction_use=False, security_valuation_transfer=False)
    return SecurityValuationBasisReceipt(**values, basis_sha256=digest(values))


def unavailable_state(*, metric, reason) -> UnavailableState:
    if metric == 'fPER':
        return 'UNAVAILABLE_ESTIMATE_HORIZON'
    if reason in {
        'TRADED_SECURITY_UNADJUSTED_PRICE_BASIS_UNQUALIFIED',
        'TRADED_SECURITY_PER_SHARE_BASIS_REQUIRES_SEPARATE_QUALIFICATION',
        'ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY',
        'NATIVE_SECURITY_IDENTITY_UNQUALIFIED', 'NATIVE_SOURCE_CURRENCY_MISSING_OR_MISMATCH',
        'NATIVE_SOURCE_SHARE_CLASS_MISSING', 'NATIVE_SOURCE_SHARE_CLASS_MISMATCH',
        'NATIVE_SECURITY_SPLIT_DENOMINATOR_AUTHORITY_OWNER_ABSENT',
    }:
        return 'UNAVAILABLE_SECURITY_BASIS'
    if reason in {'NATIVE_SOURCE_ASOF_MISSING_OR_NOT_CURRENT_PRICE_SESSION',
                  'NATIVE_SOURCE_ASOF_AFTER_CUTOFF', 'NATIVE_DENOMINATOR_VALUE_INVALID'}:
        return 'UNAVAILABLE_SOURCE_QUALITY'
    if reason in {'FRESH_REPORTED_BUSINESS_SCOPE_HAS_NO_QUALIFIED_VALUATION_DENOMINATOR',
                  'NATIVE_METRIC_VALUE_UNAVAILABLE'}:
        return 'UNAVAILABLE_DENOMINATOR'
    return 'UNAVAILABLE_OTHER_TYPED_REASON'
