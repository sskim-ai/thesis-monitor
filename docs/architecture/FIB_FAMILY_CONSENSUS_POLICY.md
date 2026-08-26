# Fib Family Consensus Policy

## Contract

`fib-family-consensus-v1` evaluates a frozen set of validated hypotheses family by family.

States are:

- `EXACT_INVARIANT`: required pivot refs and confirmation states match.
- `PRICE_EQUIVALENT`: refs differ, but every ratio remains in the same visible zone and structural
  role under the existing timeframe confluence tolerance.
- `MATERIAL_VARIATION`: visible zone, role, degree, or confirmation basis differs materially.
- `NOT_APPLICABLE`: the formula does not apply to the wave state.
- `INSUFFICIENT`: a required endpoint or provenance field is unavailable.

Only exact-invariant and price-equivalent families are eligible. Tolerances are not widened.
Price-equivalent sources retain the complete candidate-set provenance, and correlated Fib sources
remain one evidence family for scoring.

## Membership Semantics

`family-consensus-membership-audit-v1` separates active consensus members from diagnostic context.
An ID enters the active family-consensus universe only when a repeated run actually selects it or
an `AMBIGUOUS` result explicitly lists it as a competing hypothesis. The optional alternative on a
`SELECTED` result remains diagnostic unless another run promotes that ID through one of those two
paths. Invalid, wrong-ticker, same-as-selected, and wrong-degree alternatives are rejected and
cannot enter either the active or diagnostic set.

Each audit preserves per-run selected, alternative, ambiguous, active, and diagnostic IDs with one
of `ACTUALLY_SELECTED`, `EXPLICIT_AMBIGUOUS_COMPETITOR`,
`PROMOTED_ALTERNATIVE_BY_OTHER_RUN`, or `DIAGNOSTIC_ALTERNATIVE_ONLY`. This prevents a runner-up
explanation from suppressing otherwise stable Fibonacci while preserving true conflicts such as
cross-run selection changes and explicit ambiguity sets.

Technical-zone display formatting is downstream of every numeric and eligibility decision. Raw
zone bounds, Fibonacci values, confluence values, provenance, and registry numerics retain full
`Decimal` precision. The shadow renderer uses currency-aware outward rounding and automatically
reduces the display quantum when coarse rounding would change support, resistance, or current-zone
classification.

`GRAND_CYCLE` output has the `LONG_HORIZON_CONTEXT` role and is limited to the monthly shadow map.
It cannot become primary current resistance merely because no current-cycle count is available.
