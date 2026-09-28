"""Detached current-security valuation presentation over the existing owner.

No fetch, cache, persisted multiple, currency conversion or issuer bridge is
used here. A reported-business projection does not confer denominator rights.
"""

from datetime import date
from typing import Literal

import httpx
from pydantic import Field

from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.schemas.thesis import ValuationSnapshot
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.valuation_snapshot_service import (
    ValuationSnapshotService, _resolve_per_share_basis_context,
)


class CurrentMultiple(ContractModel):
    metric: Literal['PER', 'PBR', 'fPER']
    status: Literal['UNAVAILABLE', 'NOT_MEANINGFUL', 'QUALIFIED']
    value: float | None = Field(default=None, allow_inf_nan=False)
    numerator: float = Field(gt=0, allow_inf_nan=False)
    denominator: float | None = Field(default=None, allow_inf_nan=False)
    denominator_period: str | None = None
    estimate_horizon: str | None = None
    publication_date: str | None = None
    latest_published: bool = False
    source_method: str
    input_hashes: tuple[str, ...]
    denial_reason: str | None
    display_eligible: bool = False
    entry_use_eligible: bool = False
    overall_direction_use: Literal[False] = False


class CurrentValuationView(ContractModel):
    contract: Literal['current-fresh-valuation-view-v1'] = 'current-fresh-valuation-view-v1'
    ticker: str
    security_id: str
    run_id: str
    currency: str
    price: float = Field(gt=0, allow_inf_nan=False)
    price_session: date
    price_basis: str
    price_context_sha256: str
    security_sha256: str
    financial_projection_sha256: str
    owner_output_sha256: str
    metrics: tuple[CurrentMultiple, ...]
    historical_distribution: Literal['UNAVAILABLE_NO_CURRENT_COMPATIBLE_OWNER'] = 'UNAVAILABLE_NO_CURRENT_COMPATIBLE_OWNER'
    overall_direction_use: Literal[False] = False


def derive_current_valuation(*, ticker, run_id, security, price, projection, issuer_bridge=None):
    if security['ticker'] != ticker or not security.get('canonical_security_id'):
        raise ValueError('valuation_security_identity_mismatch')
    if (price.get('contract') != 'current-price-context-v1' or not price.get('currency')
            or isinstance(price.get('current_price'), bool) or not price.get('current_price')):
        raise ValueError('valuation_current_price_missing')
    if issuer_bridge is not None:
        if (issuer_bridge.get('status') != 'PASS' or issuer_bridge.get('security_ticker') != ticker
                or issuer_bridge.get('monitored_security_id') != security['canonical_security_id']
                or issuer_bridge.get('security_valuation_transfer') is not False
                or issuer_bridge.get('SECURITY_PER_SHARE_BRIDGE_ELIGIBLE') is not False
                or issuer_bridge.get('SECURITY_VALUATION_BRIDGE_ELIGIBLE') is not False
                or issuer_bridge.get('receipt_sha256') != digest({k: v for k, v in issuer_bridge.items()
                                                                 if k != 'receipt_sha256'})):
            raise ValueError('valuation_issuer_bridge_scope_invalid')
    elif not projection.get('quality_bundles') or any(
        b['source_generation_id'] != run_id or b['source_inputs']['ticker'] != ticker
        for b in projection['quality_bundles']
    ):
        raise ValueError('valuation_financial_generation_or_security_mismatch')
    # The bridge may own issuer income, but never target-security denominators.
    rows = [] if issuer_bridge else [FinancialSnapshot.model_validate(r) for r in projection['snapshots']]
    if any(r.ticker != ticker for r in rows):
        raise ValueError('valuation_cross_security_denominator_denied')
    current_price = price['current_price']
    snapshot = ValuationSnapshot(ticker=ticker, current_price=current_price, currency=price['currency'])
    basis = _resolve_per_share_basis_context(None, SecurityMaster.model_validate(security),
        price_currency=price['currency'], financial_currency=next((r.currency for r in rows if r.currency), None))

    def deny(_request):
        raise AssertionError('fresh_valuation_network_forbidden')

    owner = ValuationSnapshotService(transport=httpx.MockTransport(deny))
    owner._apply_derived_trailing(snapshot, rows, basis)
    # The bounded revenue/operating-income/net-income collector deliberately
    # grants no EPS/book/share denominator entitlement. Preserve that boundary
    # even when companyfacts happens to contain extra financial fields.
    reason = 'FRESH_REPORTED_BUSINESS_SCOPE_HAS_NO_QUALIFIED_VALUATION_DENOMINATOR'
    if price['price_basis'] not in {'close', 'regular_close'}:
        reason = 'TRADED_SECURITY_UNADJUSTED_PRICE_BASIS_UNQUALIFIED'
    if basis.is_depositary_security or basis.identity_warning:
        reason = 'TRADED_SECURITY_PER_SHARE_BASIS_REQUIRES_SEPARATE_QUALIFICATION'
    if issuer_bridge:
        reason = 'ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY'
    bindings = (digest(projection), digest(price), digest(security)) + ((digest(issuer_bridge),) if issuer_bridge else ())
    metrics = tuple(CurrentMultiple(metric=metric, status='UNAVAILABLE', numerator=current_price,
        source_method='existing_derived_trailing_owner_scope_checked' if metric != 'fPER' else 'no_fresh_estimate_owner',
        input_hashes=bindings, denial_reason=reason if metric != 'fPER' else 'NO_FRESH_ESTIMATE_HORIZON_PUBLICATION_CURRENTNESS')
        for metric in ('PER', 'PBR', 'fPER'))
    return CurrentValuationView(ticker=ticker, security_id=security['canonical_security_id'], run_id=run_id,
        currency=price['currency'], price=current_price, price_session=price['as_of_date'],
        price_basis=price['price_basis'], price_context_sha256=digest(price), security_sha256=digest(security),
        financial_projection_sha256=digest(projection), owner_output_sha256=digest(snapshot.model_dump(mode='json')),
        metrics=metrics)


def verify_current_valuation(view, **inputs):
    if view != derive_current_valuation(**inputs):
        raise ValueError('current_valuation_replay_mismatch')
    return True
