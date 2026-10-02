"""Detached current-security valuation presentation over the existing owner.

No fetch, cache, persisted multiple, currency conversion or issuer bridge is
used here. A reported-business projection does not confer denominator rights.
"""

from datetime import date, datetime
import json
from typing import Literal

import httpx
from pydantic import Field, model_validator

from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.schemas.thesis import ValuationSnapshot
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.provider_native_valuation_snapshot import (
    INPUT_CONTRACT, ProviderNativeValuationSnapshot, derive_provider_snapshots,
    ProviderNativeForwardValuationSnapshot, derive_forward_snapshot,
)
from app.services.security_valuation_basis import (
    SecurityValuationBasisReceipt, UnavailableState, candidate_inventory,
    unavailable_state, unresolved_basis,
)
from app.services.valuation_snapshot_service import (
    ValuationSnapshotService, _resolve_per_share_basis_context,
)


class CurrentMultiple(ContractModel):
    metric: Literal['PER', 'PBR', 'fPER', 'FORWARD_PE']
    status: Literal['UNAVAILABLE', 'NOT_MEANINGFUL', 'QUALIFIED']
    ownership_state: Literal['QUALIFIED', 'NOT_MEANINGFUL', 'QUALIFIED_PROVIDER_LATEST_SNAPSHOT', 'QUALIFIED_PROVIDER_FORWARD_PE_SNAPSHOT_UNSPECIFIED_HORIZON', 'QUALIFIED_PROVIDER_NATIVE_FY1_FORWARD_PE'] | UnavailableState | None = None
    value: float | None = Field(default=None, allow_inf_nan=False)
    numerator: float = Field(gt=0, allow_inf_nan=False)
    numerator_role: Literal['CURRENT_PRICE', 'CURRENT_PRICE_CONTEXT_ONLY'] = 'CURRENT_PRICE'
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
    native_snapshot: ProviderNativeForwardValuationSnapshot | ProviderNativeValuationSnapshot | None = None

    @model_validator(mode='after')
    def owned_metric_state(self):
        if self.native_snapshot is not None:
            snapshot = type(self.native_snapshot).model_validate(self.native_snapshot.model_dump(mode='json'))
            qualified = snapshot.display_eligible
            expected = snapshot.state if qualified else unavailable_state(metric=self.metric, reason=snapshot.state)
            if self.ownership_state is not None and self.ownership_state != expected:
                raise ValueError('valuation_ownership_state_mismatch')
            object.__setattr__(self, 'ownership_state', expected)
            if (self.metric != snapshot.metric or self.value != snapshot.value
                    or self.status != ('QUALIFIED' if qualified else 'UNAVAILABLE')
                    or self.source_method != 'provider_native_latest_snapshot'
                    or self.display_eligible != qualified or self.entry_use_eligible
                    or self.numerator_role != 'CURRENT_PRICE_CONTEXT_ONLY'
                    or self.denominator is not None or self.denominator_period is not None
                    or self.estimate_horizon is not None or self.latest_published
                    or self.publication_date is not None
                    or self.denial_reason != (None if qualified else snapshot.state)
                    or self.input_hashes != (snapshot.snapshot_sha256, snapshot.raw_sha256, snapshot.source_receipt_sha256)):
                raise ValueError('valuation_atomic_snapshot_scope_mismatch')
            return self
        if self.metric == 'FORWARD_PE':
            raise ValueError('forward_pe_requires_atomic_provider_owner')
        expected = (unavailable_state(metric=self.metric, reason=self.denial_reason or '')
                    if self.status == 'UNAVAILABLE' else self.status)
        if self.ownership_state is not None and self.ownership_state != expected:
            raise ValueError('valuation_ownership_state_mismatch')
        object.__setattr__(self, 'ownership_state', expected)
        if (not self.input_hashes or any(len(h) != 64 or any(c not in '0123456789abcdef' for c in h)
                                       for h in self.input_hashes)):
            raise ValueError('valuation_source_binding_required')
        if self.status == 'UNAVAILABLE':
            if self.value is not None or self.display_eligible or self.entry_use_eligible or not self.denial_reason:
                raise ValueError('valuation_unavailable_state_inconsistent')
        else:
            if not self.latest_published or not self.publication_date or not self.denominator_period:
                raise ValueError('valuation_current_denominator_metadata_required')
            date.fromisoformat(self.publication_date)
            if self.status == 'QUALIFIED':
                if self.value is None or self.value <= 0 or not self.display_eligible or self.denial_reason:
                    raise ValueError('valuation_qualified_state_inconsistent')
            elif (self.value is not None or self.denominator is None or self.denominator > 0
                  or not self.display_eligible or self.entry_use_eligible):
                raise ValueError('valuation_nm_requires_nonpositive_denominator')
            if self.metric == 'fPER' and not self.estimate_horizon:
                raise ValueError('valuation_forward_horizon_required')
        if self.numerator_role == 'CURRENT_PRICE_CONTEXT_ONLY' and self.entry_use_eligible:
            raise ValueError('native_multiple_has_no_owned_current_price_arithmetic')
        if (self.source_method == 'finnhub_native_current_metric' and self.status != 'UNAVAILABLE'
                and self.numerator_role != 'CURRENT_PRICE_CONTEXT_ONLY'):
            raise ValueError('native_multiple_must_preserve_provider_price_scope')
        return self


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
    unadjusted_price_binding: dict | None = None
    denominator_scope_receipt: dict | None = None
    security_basis_receipt: SecurityValuationBasisReceipt | None = None
    denominator_candidate_inventory: tuple[dict, ...] = ()

    @model_validator(mode='after')
    def basis_receipt_binding(self):
        receipt = self.security_basis_receipt
        if receipt is not None:
            if (receipt.ticker != self.ticker or receipt.run_id != self.run_id
                    or receipt.monitored_security_id != self.security_id
                    or receipt.security_sha256 != self.security_sha256
                    or receipt.price_sha256 != self.price_context_sha256
                    or receipt.currency != self.currency or receipt.as_of != self.price_session
                    or receipt.price_adjustment_basis != self.price_basis
                    or receipt.candidate_inventory_sha256 != digest(self.denominator_candidate_inventory)):
                raise ValueError('valuation_view_basis_binding_mismatch')
            if any(metric.status != 'UNAVAILABLE' and metric.native_snapshot is None for metric in self.metrics):
                raise ValueError('valuation_unresolved_basis_cannot_display_number')
        for metric in self.metrics:
            if metric.native_snapshot is not None:
                native = metric.native_snapshot
                if (native.run_id != self.run_id or native.security_sha256 != self.security_sha256
                        or native.canonical_security_id != self.security_id
                        or native.requested_security_id != self.ticker):
                    raise ValueError('valuation_native_view_binding_mismatch')
        return self


def derive_current_valuation(*, ticker, run_id, security, price, projection, issuer_bridge=None,
                             native_input=None, unadjusted_price_binding=None, denominator_source_inputs=None):
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
    price_owned = price['price_basis'] in {'close', 'regular_close'}
    if unadjusted_price_binding is not None:
        binding = unadjusted_price_binding
        if (binding.get('contract') != 'fresh-unadjusted-price-equivalence-v1'
                or binding.get('ticker') != ticker or binding.get('run_id') != run_id
                or binding.get('adjusted') is not False or binding.get('price') != current_price
                or binding.get('as_of_date') != str(price['as_of_date'])
                or binding.get('quote_sha256') != digest(price) or not binding.get('source_sha256')):
            raise ValueError('valuation_unadjusted_price_binding_mismatch')
        price_owned = True
    snapshot = ValuationSnapshot(ticker=ticker, current_price=current_price, currency=price['currency'])
    basis = _resolve_per_share_basis_context(None, SecurityMaster.model_validate(security),
        price_currency=price['currency'], financial_currency=next((r.currency for r in rows if r.currency), None))

    def deny(_request):
        raise AssertionError('fresh_valuation_network_forbidden')

    owner = ValuationSnapshotService(transport=httpx.MockTransport(deny))
    owner._apply_derived_trailing(snapshot, rows, basis)
    from app.services.fresh_valuation_capability import denominator_scope
    scope = denominator_scope(projection, security=security, issuer_bridge=issuer_bridge,
                              source_inputs=denominator_source_inputs)
    inventory = candidate_inventory(scope.get('raw_source_projection'))
    basis_receipt = unresolved_basis(ticker=ticker, run_id=run_id, security=security, price=price,
                                    inventory=inventory, issuer_bridge=issuer_bridge)
    # The bounded revenue/operating-income/net-income collector deliberately
    # grants no EPS/book/share denominator entitlement. Preserve that boundary
    # even when companyfacts happens to contain extra financial fields.
    reason = 'FRESH_REPORTED_BUSINESS_SCOPE_HAS_NO_QUALIFIED_VALUATION_DENOMINATOR'
    if not price_owned:
        reason = 'TRADED_SECURITY_UNADJUSTED_PRICE_BASIS_UNQUALIFIED'
    if basis.is_depositary_security or basis.identity_warning:
        reason = 'TRADED_SECURITY_PER_SHARE_BASIS_REQUIRES_SEPARATE_QUALIFICATION'
    if issuer_bridge:
        reason = 'ISSUER_BRIDGE_HAS_NO_SECURITY_VALUATION_AUTHORITY'
    bindings = (digest(projection), digest(price), digest(security)) + ((digest(issuer_bridge),) if issuer_bridge else ())
    if unadjusted_price_binding is not None:
        bindings += (digest(unadjusted_price_binding),)
    metrics = tuple(CurrentMultiple(metric=metric, status='UNAVAILABLE', numerator=current_price,
        source_method='existing_derived_trailing_owner_scope_checked' if metric != 'fPER' else 'no_fresh_estimate_owner',
        input_hashes=bindings, denial_reason=reason if metric != 'fPER' else 'NO_FRESH_ESTIMATE_HORIZON_PUBLICATION_CURRENTNESS')
        for metric in ('PER', 'PBR', 'fPER'))
    if native_input is not None and native_input.get('contract') == 'provider-native-valuation-unavailable-v1':
        if (native_input['run_id'] != run_id or native_input['security_sha256'] != digest(security)
                or native_input['reason'] not in {'UNAVAILABLE_PROVIDER_REQUEST_NOT_COMPLETED', 'UNAVAILABLE_PROVIDER_RESPONSE'}
                or len(native_input['acquisition_binding']) != 64):
            raise ValueError('native_valuation_denial_binding_mismatch')
        metrics = tuple(CurrentMultiple(metric=m.metric, status='UNAVAILABLE', numerator=current_price,
            source_method='sealed_native_valuation_acquisition_denial', input_hashes=(native_input['acquisition_binding'],),
            denial_reason=native_input['reason']) if m.metric != 'fPER' else m for m in metrics)
    elif native_input is not None and native_input.get('contract') == INPUT_CONTRACT:
        snapshots = derive_provider_snapshots(native_input, security=security, run_id=run_id)
        if native_input['receipt']['provider'] == 'finnhub':
            snapshots += (derive_forward_snapshot(native_input, security=security, run_id=run_id),)
        metrics = tuple(CurrentMultiple(metric=s.metric, status='QUALIFIED' if s.display_eligible else 'UNAVAILABLE',
            numerator=current_price, numerator_role='CURRENT_PRICE_CONTEXT_ONLY', value=s.value,
            source_method='provider_native_latest_snapshot', input_hashes=(s.snapshot_sha256, s.raw_sha256, s.source_receipt_sha256),
            denial_reason=None if s.display_eligible else s.state, display_eligible=s.display_eligible, native_snapshot=s)
            for s in snapshots) + ((metrics[2],) if len(snapshots) == 2 else ())
    elif (not issuer_bridge and not basis.is_depositary_security and not basis.identity_warning
            and price_owned):
        if native_input is not None:
            metrics = _native_metrics(metrics, native_input, ticker=ticker, run_id=run_id,
                                      price=price, security=security)
    return CurrentValuationView(ticker=ticker, security_id=security['canonical_security_id'], run_id=run_id,
        currency=price['currency'], price=current_price, price_session=price['as_of_date'],
        price_basis=price['price_basis'], price_context_sha256=digest(price), security_sha256=digest(security),
        financial_projection_sha256=digest(projection), owner_output_sha256=digest(snapshot.model_dump(mode='json')),
        metrics=metrics, unadjusted_price_binding=unadjusted_price_binding, denominator_scope_receipt=scope,
        security_basis_receipt=basis_receipt, denominator_candidate_inventory=tuple(inventory))


def _native_metrics(metrics, inputs, *, ticker, run_id, price, security):
    """Read-only replay of the already configured Finnhub stock/metric wire.

    metricAsOf/asOfDate is source time, never replaced with the request clock.
    forwardPE alone has no owned horizon and therefore remains unavailable.
    """
    from app.services.unified_run_artifacts import sha256_bytes
    receipt, raw = inputs['receipt'], inputs['raw']
    inputs['policy'].require('finnhub')
    if (receipt.get('run_id') != run_id or receipt.get('provider') != 'finnhub'
            or receipt.get('acquisition_class') != 'FRESH_CURRENT_RUN'
            or receipt.get('security_sha256') != digest(security)
            or receipt.get('source_sha256') != sha256_bytes(raw) or receipt.get('http_status') != 200
            or receipt.get('request') != dict(method='GET', route='https://finnhub.io/api/v1/stock/metric',
                                            params={'symbol': ticker, 'metric': 'all'})):
        raise ValueError('fresh_native_valuation_receipt_mismatch')
    start, end = (datetime.fromisoformat(receipt[k]) for k in ('requested_at', 'received_at'))
    if (any(t.utcoffset() is None for t in (start, end, inputs['run_started_at'], inputs['cutoff']))
            or not inputs['run_started_at'] <= start <= end <= inputs['cutoff']):
        raise ValueError('fresh_native_valuation_receipt_time')
    payload = json.loads(raw)
    if payload.get('symbol') != ticker:
        raise ValueError('fresh_native_valuation_symbol_mismatch')
    as_of = payload.get('metricAsOf') or payload.get('asOfDate')
    native_hashes = (digest(receipt), sha256_bytes(raw))

    def unavailable(metric, reason):
        return CurrentMultiple(metric=metric.metric, status='UNAVAILABLE', numerator=metric.numerator,
            source_method='finnhub_native_current_metric', input_hashes=metric.input_hashes + native_hashes,
            denial_reason=reason)

    reason = None
    if as_of != str(price['as_of_date']):
        reason = 'NATIVE_SOURCE_ASOF_MISSING_OR_NOT_CURRENT_PRICE_SESSION'
    elif security.get('identity_quality') != 'verified' or security.get('security_type') != 'common_stock':
        reason = 'NATIVE_SECURITY_IDENTITY_UNQUALIFIED'
    elif payload.get('currency') != price['currency']:
        reason = 'NATIVE_SOURCE_CURRENCY_MISSING_OR_MISMATCH'
    elif not payload.get('shareClass') or not security.get('share_class'):
        reason = 'NATIVE_SOURCE_SHARE_CLASS_MISSING'
    elif payload.get('shareClass') != security.get('share_class'):
        reason = 'NATIVE_SOURCE_SHARE_CLASS_MISMATCH'
    elif date.fromisoformat(as_of) > inputs['cutoff'].date():
        reason = 'NATIVE_SOURCE_ASOF_AFTER_CUTOFF'
    # The configured wire has no qualified split/denominator authority adapter.
    # A fresh receipt or plausible native multiple cannot substitute for it.
    reason = reason or 'NATIVE_SECURITY_SPLIT_DENOMINATOR_AUTHORITY_OWNER_ABSENT'
    return tuple(unavailable(metric, 'NO_FRESH_ESTIMATE_HORIZON_PUBLICATION_CURRENTNESS'
        if metric.metric == 'fPER' else reason) for metric in metrics)


def verify_current_valuation(view, **inputs):
    if view != derive_current_valuation(**inputs):
        raise ValueError('current_valuation_replay_mismatch')
    return True


def valuation_numeric_bindings(view):
    """Use the existing valuation registry, detached from directional evidence."""
    from app.services.numeric_semantic_registry import build_numeric_registry
    fields = {'PER': 'trailing_pe', 'PBR': 'price_to_book', 'fPER': 'forward_pe', 'FORWARD_PE': 'forward_pe'}
    result = {}
    for metric in view.metrics:
        CurrentMultiple.model_validate(metric.model_dump(mode='json'))
        if metric.status != 'QUALIFIED':
            continue
        fact = dict(fact_id=f'current-valuation:{view.security_id}:{metric.metric}', fact_type='valuation',
            ticker=view.ticker, as_of_date=metric.publication_date,
            fields={fields[metric.metric]: metric.value},
            source_method=metric.source_method, input_hashes=list(metric.input_hashes),
            current_view_sha256=digest(view.model_dump(mode='json')), overall_direction_use=False)
        if metric.native_snapshot is not None:
            fact.update(provider_snapshot=metric.native_snapshot.model_dump(mode='json'),
                        retrieval_timestamp=metric.native_snapshot.retrieval_timestamp.isoformat(),
                        metric_asof=metric.native_snapshot.metric_asof.isoformat() if metric.native_snapshot.metric_asof else None)
        rows = build_numeric_registry([fact])
        if len(rows) != 1 or not rows[0]['registered'] or rows[0]['unit'] != 'x':
            raise ValueError('current_valuation_numeric_registration_failed')
        result[metric.metric] = dict(fact=fact, registry=rows[0])
    return result
