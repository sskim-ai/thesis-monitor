# R9 REV6 Offline Contracts

Status: PARTIAL. No production registration, source dispatch, or model dispatch.
The work instruction is `docs/work-instructions/20260928-r2b-r9-rev6/WORK_INSTRUCTION.md`.

## Implemented

- `configured-night-product-scope-v1`: the probe, provider, history normalizer,
  replay, eligibility and display share the KOSPI200 scope. Raw source hashes
  retain the full response; selected economic values exclude other products.
- `market-selected-display-v1`: an immutable typed display plan binds each
  selected value to its fact and numeric-registry row. Internal facts remain
  intact. US index prices and changes use adjacent regular-session bars from
  the same response. Sector rankings are session/taxonomy/venue constrained,
  deterministic, and reject duplicate sector identities. KR FX requires a
  daily source observation period. Accepted market rendering can consume this
  plan; it is not automatically injected into any production plan.
- `macro-source-period-currentness-v1`: source observation period, query,
  retrieval and optional publication time are distinct. Missing/invalid ECOS
  TIME is unavailable, not query time. FRED latest selection uses the bounded
  descending response after placeholder rejection. EIA retains its source
  period but does not claim latest-publication verification on the existing
  one-row route. No arbitrary age threshold or inferred publication timestamp.
- `r9-fresh-source-run-v1`: offline candidate budgets cover all 88 stock roles,
  US market symbols, KR market pages, all22 bounded SEC/OpenDART plans, macro
  requests and bounded night-history dates. Former retained subjects are
  included only in the explicit all-subjects-fresh mode; historical defaults
  are unchanged. Static seed and current receipt guards reject old mutable
  inputs, wrong generation, out-of-window acquisition and changed bytes.

The candidate plan is explicitly `OFFLINE_CANDIDATE_NOT_QUALIFIED` with
`dispatch_allowed=false`. It is not a source acquisition receipt, a complete
provider-role plan, or a live controller.

## Still Open

1. A distinct all22 fresh controller and composition path. The old
   `unified_live_cohort_proof.py` still imports parent financial/quality/macro
   data. `compose_full_source` still binds class-C financial inputs or prior
   versioned/persisted business owners. The new bounded financial plans cover
   reported revenue/operating-income/net-income comparisons, not the entire
   fresh quality and security-valuation denominator projection. No old result
   may bridge these missing current-source interfaces.
2. Detailed stock acceptance and rendering. `AcceptedCalibrationPlan` still
   renders a compact card. Its contract does not bind the required detailed
   business, warning, monitoring, price-structure, participation and mandatory
   valuation blocks. No paragraphs may be appended after sender-boundary
   capture to hide this gap.

Both are P1 pre-network blockers. The terminal remains
`R2B_R9_REV6_PREFLIGHT_CONTRACT_GAP`. Live ECOS period proof, full-source replay,
adapter qualification, Market/Core/A/B, and 24-message capture are NOT_RUN.
Unit fixtures do not qualify a live source or a human-review payload.

## Validation Boundary

Tests run with the existing socket/DNS-denying offline plugin. Old two-product
expectations are migrated to the configured product, including the morning
gate waiting only for KOSPI200. Historical scope-audit tests continue to expect
FAIL and enumerate the additional changed files; no skip or threshold waiver
is introduced. This branch must not be deployed while the above gaps remain.
