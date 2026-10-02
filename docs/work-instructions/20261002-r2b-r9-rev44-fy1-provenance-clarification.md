# REV44 In-Flight FY1 Clarification

The user reports the following definition in Finnhub Basic Financials:
"Forward P/E ratio using analyst estimates for the next fiscal year."
The user supplied https://finnhub.io/docs/api/ownership and asked to select
Basic Financials. This is a user-reported observation, not a captured official
field definition yet.

Required mapping after official field-specific capture and SHA sealing:

- forward_horizon_state: PROVIDER_FORWARD_HORIZON_FY1
- provider_horizon: NEXT_FISCAL_YEAR
- estimate_basis: ANALYST_ESTIMATES
- qualification_state: QUALIFIED_PROVIDER_NATIVE_FY1_FORWARD_PE
- display_label: fPER(FY1)

Existing sealed metric responses must be reused. No data API call, model call,
message generation, implied EPS, or FY1 EPS owner may result from this change.
ADR/home-security exclusion, Overall=false, Core/A exclusion and Pass-B
NewBuyer/Holder-only ownership remain unchanged.

The current capture of that exact link, the Basic Financials page, linked
Swagger and official OpenAPI does not reproduce the field-specific definition.
Browser navigation to Basic Financials shows only a generic metric map. Retain
the unqualified-horizon state until the official definition is captured; never
mislabel the user assertion or a synthetic test as Finnhub-owned provenance.

The user's subsequent clarification confirms the visible documentation only
contains the ratio, and proposes FY1 because no NTM weighting parameters are
returned. This is an inference, not field-specific official evidence. A provider
can return an internally computed NTM multiple without exposing its weights.
The absence of parameters does not establish FY1. Keep the approved atomic
UNSPECIFIED snapshot path; FY1 activation remains unproven.
