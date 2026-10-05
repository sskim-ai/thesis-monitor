"""V2 companion for a planned but unavailable price. V1 remains numeric."""
from typing import Literal
from copy import deepcopy

from pydantic import model_validator

from app.services.completed_price_state import CurrentPriceState, require_runtime
from app.services.current_fresh_valuation import CurrentMultiple, CurrentValuationView
from app.services.provider_native_valuation_snapshot import (
    INPUT_CONTRACT, derive_provider_snapshots, derive_forward_snapshot,
)
from app.services.unified_snapshot_contract import digest

CONTRACT = 'current-fresh-valuation-unavailable-price-v2'


class UnavailablePriceMultiple(CurrentMultiple):
    numerator: None = None
    price_dependency: Literal['CURRENT_PRICE_ARITHMETIC_REQUIRED', 'CURRENT_PRICE_CONTEXT_ONLY']
    price_state_ref: str

    @model_validator(mode='after')
    def scoped(self):
        if len(self.price_state_ref) != 64:
            raise ValueError('valuation_price_denial_ref_required')
        if self.native_snapshot is not None:
            if self.price_dependency != 'CURRENT_PRICE_CONTEXT_ONLY':
                raise ValueError('native_price_dependency_mismatch')
        elif (self.price_dependency != 'CURRENT_PRICE_ARITHMETIC_REQUIRED'
                or self.status != 'UNAVAILABLE' or self.denial_reason != 'CURRENT_PRICE_UNAVAILABLE'
                or self.input_hashes != (self.price_state_ref,)):
            raise ValueError('derived_price_denial_scope')
        return self


class UnavailablePriceValuationView(CurrentValuationView):
    contract: Literal['current-fresh-valuation-unavailable-price-v2'] = CONTRACT
    price: None = None
    price_state: CurrentPriceState
    metrics: tuple[UnavailablePriceMultiple, ...]

    @model_validator(mode='after')
    def price_scope(self):
        state = require_runtime(self.price_state)
        if state.state == 'AVAILABLE' or (state.ticker, state.security_id, state.source_generation, state.target_session) != (
                self.ticker, self.security_id, self.run_id, self.price_session):
            raise ValueError('valuation_unavailable_price_identity')
        if (self.security_basis_receipt is not None or self.unadjusted_price_binding is not None
                or self.price_basis != 'UNAVAILABLE_COMPLETED_CLOSE'
                or any(m.price_state_ref != state.receipt_sha256 for m in self.metrics)
                or len({m.metric for m in self.metrics}) != len(self.metrics)):
            raise ValueError('valuation_unavailable_price_scope')
        return self


def derive(*, ticker, run_id, security, price, projection, price_state, native_input):
    state = require_runtime(price_state)
    if (price.get('contract') != 'current-price-context-v2' or price.get('current_price') is not None
            or price.get('price_state') != state.model_dump(mode='json')):
        raise ValueError('unavailable_price_context_binding')
    # No denominator, action, or share arithmetic is consumed after this failed
    # price prerequisite. The typed price owner, not static dataflow, owns denial.
    metrics = tuple(UnavailablePriceMultiple(metric=m, status='UNAVAILABLE',
        source_method='price_prerequisite_short_circuit', denial_reason='CURRENT_PRICE_UNAVAILABLE',
        input_hashes=(state.receipt_sha256,), price_state_ref=state.receipt_sha256,
        price_dependency='CURRENT_PRICE_ARITHMETIC_REQUIRED') for m in ('PER', 'PBR', 'fPER'))
    if native_input is not None and native_input.get('contract') == INPUT_CONTRACT:
        snapshots = derive_provider_snapshots(native_input, security=security, run_id=run_id)
        if native_input['receipt']['provider'] == 'finnhub':
            snapshots += (derive_forward_snapshot(native_input, security=security, run_id=run_id),)
        metrics = tuple(UnavailablePriceMultiple(metric=s.metric, status='QUALIFIED' if s.display_eligible else 'UNAVAILABLE',
            numerator_role='CURRENT_PRICE_CONTEXT_ONLY', price_dependency='CURRENT_PRICE_CONTEXT_ONLY',
            price_state_ref=state.receipt_sha256, value=s.value, source_method='provider_native_latest_snapshot',
            input_hashes=(s.snapshot_sha256, s.raw_sha256, s.source_receipt_sha256),
            denial_reason=None if s.display_eligible else s.state, display_eligible=s.display_eligible,
            native_snapshot=s) for s in snapshots) + ((metrics[2],) if len(snapshots) == 2 else ())
    elif native_input is not None:
        # Acquisition-denied or legacy native inputs cannot be represented as a
        # price-arithmetic denial. They need their own native source owner.
        raise ValueError('unavailable_price_native_source_owner_required')
    return UnavailablePriceValuationView(ticker=ticker, security_id=security['canonical_security_id'],
        run_id=run_id, currency=price['currency'], price_session=state.target_session,
        price_basis='UNAVAILABLE_COMPLETED_CLOSE', price_context_sha256=digest(price),
        security_sha256=digest(security), financial_projection_sha256=digest(projection),
        owner_output_sha256=digest([state.model_dump(mode='json'), [m.model_dump(mode='json') for m in metrics]]),
        metrics=metrics, price_state=state)


def parse_view(value):
    contract = value.get('contract') if isinstance(value, dict) else value.contract
    cls = UnavailablePriceValuationView if contract == CONTRACT else CurrentValuationView
    return cls.model_validate(value)


def shadow_request_context(context, source_stock):
    """Adapt only typed missing-price input to the frozen B2 mapping shape."""
    view = parse_view(source_stock['valuation_view'])
    if view.price is not None:
        return context
    stock = source_stock['packet']['stocks'][0]
    state = view.price_state
    if (source_stock['current_price_state'] != state.model_dump(mode='json')
            or stock['current_price_context'].get('price_state') != state.model_dump(mode='json')
            or view.price_context_sha256 != digest(stock['current_price_context'])
            or context['ticker'] != view.ticker
            or context.get('current_price') is not None):
        raise ValueError('shadow_unavailable_price_input_mismatch')
    result = deepcopy(context)
    result['current_price'] = dict(value=None, currency=view.currency, basis=view.price_basis,
        as_of=None, ref_id=None, price_state_ref=state.receipt_sha256, availability=state.state)
    return result
