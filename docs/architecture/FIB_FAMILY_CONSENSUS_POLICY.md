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

`GRAND_CYCLE` output has the `LONG_HORIZON_CONTEXT` role and is limited to the monthly shadow map.
It cannot become primary current resistance merely because no current-cycle count is available.
