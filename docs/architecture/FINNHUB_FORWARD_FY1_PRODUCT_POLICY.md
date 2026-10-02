# Finnhub Forward FY1 Product Policy

REV45 separates a product interpretation from provider-documented semantics.
The immutable REV44 documentation capture did not reproduce a field-specific
FY1 definition. `FINNHUB_FORWARD_FY1_PROVENANCE` therefore remains null.

Under the user-authorized `finnhub-forwardpe-fy1-product-policy-v1`, a qualified
Finnhub `forwardPE` is a provider-native atomic ratio with canonical horizon FY1
and display label `fPER(FY1)`. Its horizon authority is
`USER_AUTHORIZED_PRODUCT_POLICY`, not `OFFICIAL_FIELD_DEFINITION`.
`provider_horizon` and `provider_definition` remain null. The rendering caveat
identifies this as a FY1 product-policy interpretation of a Finnhub snapshot.
No implied EPS, denominator owner, current-price recomputation, or price target
is created. REV44 captures and previous serialized evidence are not rewritten.

## Scoped Identity

`finnhub-direct-us-provider-identity-v2` applies only to `peTTM`, `pbQuarterly`
and `forwardPE`. A canonical direct/common US equity must have matching request,
profile and metric symbols, compatible normalized US listing venue and USD
currency, and same-generation receipt bindings. A separate SEC identity receipt
is optional supporting evidence; when present, a contradictory receipt still
denies use. Canonical identity rules for filings, prices, events and other
providers are unchanged. Issuer domicile alone is not a listing conflict.

Exact US exchange aliases are normalized; foreign exchange names are not.
Historical Toronto HUT evidence and depositary/remapped SKHY, TSM and WRD
evidence remain denied. A missing, nonpositive or invalid forward ratio remains
unavailable independently of PER/PBR availability.

## Consumption

The ratio is available only for valuation display and Pass B NewBuyer/Holder
context, with an exact FORWARD_PE fact reference. Core, Pass A and Overall
business direction remain excluded. Product-policy metadata is validated against
the pinned policy, and a caller cannot substitute an official definition.

## Staged Execution Boundary

The REV45 instruction requires US14 source/model/message proof before KR8.
The inherited fresh runner currently supports ALL22 and KR8_ONLY. Its SKHY
issuer bridge consumes the same-generation 000660 financial owner plus its
technical/local baseline. This is not permission to collect KR8 early, reuse
old 000660 data, remove SKHY, or relax the whole-cohort count/hash contract.
The existing ALL22 model runner also owns a 24-message capture contract.

A US-only execution path needs an explicitly bound auxiliary issuer source
contract and scoped source/replay/model completeness checks before live use.
Policy tests or historical corpus replay alone do not qualify that live path,
and do not authorize KR proof, main integration, or deployment.
