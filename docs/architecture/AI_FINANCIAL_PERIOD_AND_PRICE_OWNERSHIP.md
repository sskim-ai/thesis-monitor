# AI Financial Period and Price Ownership

Status: implemented by `cash-flow-period-identity-v1` and the existing
`current-price-context-v1` ownership model.

## Cash-flow period identity

`cash_flow_user_visible` is the canonical AI-facing source for selected PPE-only
FCF. It exposes the canonical fiscal period label, duration basis, fiscal year,
fiscal quarter, YTD/FY flags, allowed claims, forbidden claims, currency, scope,
and Fact ID. The model must reproduce `required_period_label` exactly. It may
not annualize, convert a fiscal period to a calendar period, or call YTD a
standalone quarter.

The number remains owned by `business_earnings`; the contract changes no FCF
arithmetic and preserves the `OCF - PPE CAPEX` scope.

## Current-price ownership

Exact price structure belongs to `price_context`, with prose ownership in
`price_positioning.text`. `price_fact_ownership` is derived only from the stock's
canonical Fact catalog and state-grounding requirements. It identifies current
price, support, resistance, current RR, RR transition, invalidation, and
confirmation references.

The AI may declare only `allowed_fact_ids`. When current RR is unavailable, the
canonical RR ID is listed under `unavailable_fact_ids`; the model may describe
the supplied blocking reason but cannot invent the Fact ID or an RR number.

## Validation boundary

The validator still rejects absent fiscal identity, YTD/QTD/FY mislabeling,
annualization, unknown Fact IDs, and unsupported arithmetic. Runtime quality
still checks numeric ownership and typed repetition. No threshold was relaxed.

