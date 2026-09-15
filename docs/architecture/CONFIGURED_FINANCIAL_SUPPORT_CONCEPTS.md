# Configured Financial Support Concepts

Contract: `configured-financial-support-concept-v1`

Implementation: `app/services/configured_financial_support_concept_service.py`

## Purpose

Configured thesis signals can establish that a candidate's financial claim is a
future condition about the same concept. They do not establish that the
condition is fulfilled today. This contract provides the bounded concept
identity needed for that comparison without expanding general financial
framework application scanning.

## Inputs

The helper consumes one existing `DecisionEvidenceRef` whose `source_ref` is a
configured strengthen, weaken, or invalidation signal. Signal lifecycle and
field eligibility remain owned by `ConfiguredSignalEvidenceView`.

## Mapping

Existing `net_debt`, `working_capital`, and `non_operating_interest` identities
continue to come from the existing framework vocabulary. True FCF support is
added separately:

- Structured `metric_refs` containing `FCF` maps to `free_cash_flow`.
- When structured metric refs are absent, explicit `FCF`, `free cash flow`,
  `free-cash-flow`, or `잉여현금흐름` text may map to `free_cash_flow`.
- Vague cash-flow or cash-generation language does not map to FCF.
- OCF does not map to FCF.
- OCF less PPE and PPE-only cash-conversion proxies do not map to FCF, even if
  prose labels the proxy as FCF.

The helper returns concept identity only. It does not produce current financial
evidence, change configured fulfillment state, or make a configured signal a
current directional driver.

## Validator Boundary

`financial_claim_role()` may use a matching configured concept to classify an
explicitly future, conditional, nominalized, or monitoring-obligation claim as
prospective. Current magnitude, current fulfillment, and numeric-current
language retain precedence. A current FCF assertion still requires independently
safe current FCF evidence.

## Unchanged Surfaces

The general `_FRAMEWORKS` scanner, framework application counts, financial
sector exclusions, prompt, schema, configured-signal view, business-delta view,
market-expectation view, financial evidence projection, renderer, and two-stage
model contracts are unchanged.
