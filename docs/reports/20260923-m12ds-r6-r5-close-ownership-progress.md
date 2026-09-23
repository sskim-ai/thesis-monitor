# M12DS-R6-R5 Ownership Decision: Cutoff Observation Pending

## Authority

Base: `33bb3cb666bd0063aba9444afe7d5f062fefac62`.
Work instruction is committed before implementation/provider qualification on
`codex/m12ds-r6-r5-kiwoom-close-owner`. Original ZIP contents are preserved in that
commit; only three Markdown trailing-space occurrences are subsequently removed.
The R4 report hash remains
`7c0e70b7a09232130a4988b7797c80ab92d1010a390610e90071d6f5e2717920`.

No main merge, remote push, deployment, production scheduling, send, recipient
intent, decision/warning DB write, notification mutation, or broker action.

## Completed Now

R4's 22 comparisons are retained with source timestamps, route/basis identities,
O/H/L/C and available hashes. Classification is strictly
`PRODUCTION_ROUTE_SAME_DATE_CLOSE_NOT_REPRODUCIBLY_FINAL`.
There is no assertion of upstream mutation. The prior upstream wire and historical
loaded gateway SHA are not reconstructable. Current gateway checkout SHA is only
current checkout identity, not proof of what the old process loaded.

R5 explicitly authorizes usa20100 as qualification-only. A single bounded sweep
at 18:42 KST (05:42 EDT) queried SPY, SOXX, XLC: one raw daily, one adjusted daily,
one quote each. Nine read-only data calls, one token acquisition, zero retries.

| Symbol | Exchange | Quote base_close_pric | Matched Dated Row |
| --- | --- | ---: | --- |
| SPY | NY | 773.3800 | 2026-09-22 |
| SOXX | ND | 572.7800 | 2026-09-22 |
| XLC | NY | 113.5300 | 2026-09-22 |

All four previous O/H/L/C fields match uniquely to the target dated row. The same
selected date's raw and adjusted O/H/L/C are equal, and current price minus base
close equals the provider's signed delta exactly. Full raw bodies, hashes and
actual KST/UTC/ET timestamps are preserved outside Git.

This is **exact numeric alignment in the observed premarket context**, not proof
that the undated quote owns the just-completed same-day session in after-hours.
Quote basis is not declared by the endpoint. The bounded reconciliation reason
is exact raw/adjusted four-field equality on the matched date, not an invented
quote adjustment flag. The current-price directional sign is not a negative price.

## Pending Actual Time Evidence

No new production-cutoff evidence exists yet. The next configured observation is
September 24, 08:05/08:10/08:15/08:20 KST, targeting the September 23 US session.
Each manual attempt is frozen to 22 adjusted daily requests plus raw daily and
quote requests for the three diagnostic symbols. Maximum 28 calls per sample,
112 across four cutoff samples, then one 28-call next-premarket sample.

The manual observer is **prepared, not launched and not scheduled**. No overnight
process or automation was registered. It rejects wrong dates/windows before
authentication, verifies frozen route/plan hashes, records missed windows rather
than backdating, uses zero retries, and preserves failures without substitution.
All cutoff evidence must be acquired in the configured minute. This conservative
diagnostic rule does not change production freshness thresholds.

The delayed comparison checks the same target date and basis after day rollover.
It is qualification-only, not a production lookahead dependency. One equality
does not erase R4's 19 changed closes. No typed production v2 owner is created
before the actual ownership decision passes.

## Local Code and Verification

- `scripts/m12ds_r6_r5_close_ownership.py`: identity/currency checks, exact
  previous-OHLC alignment, basis reconciliation, target-versus-previous-session
  value distinction, actual cutoff binding, delayed same-date comparison.
- `scripts/m12ds_r6_r5_cutoff_observer.py`: bounded manual collection with frozen
  requests; no model/delivery/DB/scheduler surface.
- Tests cover ambiguous equal values, same-day mislabeling, wrong routes, missing
  currency/date context, raw/adjusted mismatches, exact delta, no automatic
  authority promotion, wrong-window rejection before network, and no retries.

Exact-SHA focused/full pytest, Ruff, diff, Knowledge and Action results live in
the private report's `validation/final.json`. Existing KR post-close, KR8 quote
basis, night D/W/M, macro informational separation, and price-structure contracts
remain unchanged. No new skip/xfail is introduced.

## Gate

`M12DS_R6_R5_CUTOFF_OBSERVATION_PENDING`.

The final Kiwoom decision is deliberately null until actual cutoff plus delayed
historical evidence exists. This is a planned future observation, not a technical
collection failure, so `KIWOOM_REGULAR_CLOSE_OWNER_UNRESOLVED` is not asserted.
Neither PASS nor NOT_AVAILABLE is invented from premarket evidence. Model calls,
Market/Core/A/B and 24-message capture are all zero. No success-review ZIP exists.

When the bounded samples are complete, adjudicate once: the old latest-row owner
cannot pass while R4 drift is unexplained; an alternative quote owner must prove
target-session ownership for the full required universe, not merely the subset.
If no tested owner satisfies that contract, report external settled-close source
requirements and stop. No new provider is authorized here.
