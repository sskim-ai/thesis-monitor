# Phase 9.0E Complete Report

## Repository

- Branch: `codex/phase-9-0e-selective-cash-flow-user-visible-integration`
- Instruction: `docs/work-instructions/20260821-phase-9-0e-selective-cash-flow-user-visible-integration.md`
- Instruction version/commit: `1.0` / `309f5f1756d39d5972c5d4b48faaeab4862d8077`
- Instruction ZIP/content SHA-256: `a87e7f892eb299d134eed866c6f7b9ad8efbebaf987dbda495f001e91c7f7bf6` /
  `6b570a387e212d1e600c22a769755b748082204392a318f1fd55a37a18afad6f`
- Previous main: `86f41870a17fc4bec8ec43b1395323e211450fa2`
- Implementation commits: `f8c24db` and `cf31949`; cumulative SHA
  `cf3194981124de2a6f85fbe81b145ef06e1db08d`
- Implementation Actions: run `32443322364`, Test/Lint PASS
- Promotion: clean fast-forward; main/operating exact and clean
- Final report SHA: resolves from `git rev-parse origin/main` after final docs promotion
- Push: YES; force push/history rewrite: `0/0`
- Runtime visible diff: YES, only for dynamically selected subjects while mode is SELECTIVE
- Work-instruction deviations: NO

## Contract

`cash-flow-user-visible-v1` consumes the Phase 9.0B-9.0D.1 chain and never recalculates cash flow.
Default/invalid mode is OFF. Initial SELECTIVE eligibility requires US/foreign official SEC,
PIT-safe current formal full FCF, exact OCF/PPE CAPEX/FCF lineage and arithmetic, compatible
period/entity/basis/currency/unit, industry applicability, materiality, and baseline consistency.

The user-facing owner is `business_earnings`. The first rollout renders one exact number as fiscal-
period-labeled `PPE 투자 후 잉여현금흐름`; OCF and CAPEX remain lineage. Positive/negative sign is
not a verdict. No ticker allowlist, magnitude threshold, thesis mutation, warning mutation,
valuation change, FCF yield/share/EV, CCC, or ROIC is introduced.

## Selection And Preview

Run-30 US/foreign universe is `13`; selected `9`: CORZ, CRCL, GOOGL, IBM, MU, RXRX, SNDK, TSLA,
and WULF. HUT is OCF-only; SKHY is blocked; TSM/WRD are formal-lagging-provisional. The selected
fallback first-exposure length delta averages `114.33` characters. Evidence signatures suppress
identical later exposure.

Human result: material improvement `5`, minor improvement `4`, no meaningful change `4`, degraded
`0`. SNDK resolves one cash-flow Unknown. TSLA suppresses four unsupported baseline claim
occurrences and then uses H1 YTD USD PPE-only FCF Fact
`cashflow:68666c261434dab50ab88a8d` (`352,000,000`). Status and valuation mutations are `0`.

The archive-only AI preview adds the same nine facts to `business_earnings`: automatic binding `9`,
manual `0`, rejected `0`, unresolved `0`; semantic/final-language/runtime-quality errors `0`;
sentence/skeleton repetition `0/0`. The preview copy removes run-30's pre-existing unrelated
numeric-summary/typed-valuation blockers solely to isolate enrichment; immutable archives are not
rewritten.

## AI/Fallback Parity

Selected context count and exact FCF claims are `9/9`. Selection, context ID, Fact ID, period, scope,
sign, currency, freshness, and baseline suppression mismatch counts are all `0`. Fallback remains
exactly-once and is selected from the same context. A mismatch fixture hard-fails before delivery;
per-ticker optional enrichment failures suppress only that ticker.

## Negative Controls

- Run-29 KR: selected/injected `0/7`; Korean Re generic FCF not applicable.
- Feature OFF: selected/injected `0/13`; unknown mode also OFF.
- HUT OCF-only: suppressed.
- TSM/WRD lagging formal: suppressed.
- SKHY canonical unavailable: suppressed.
- Stale, lineage, CAPEX-scope, entity/basis/currency, management-FCF, unsupported valuation/advanced
  metric, and resolved-Unknown fixtures: fail closed.

## Validation

- Focused related suite: `396 passed`
- Full pytest: `1264 passed`, one upstream Starlette deprecation warning
- Operating smoke: `396 passed`
- Ruff: PASS
- `git diff --check`: PASS
- Investment/Chart Knowledge parity: PASS
- Public Action/output schema: `0.4.5` / `4`
- operationId: `20/20` unique
- Implementation exact-SHA Actions: PASS, run `32443322364`
- Final exact-SHA Actions: PASS required and resolved at final promotion
- API health: PASS after OFF staging and SELECTIVE restart

## Operating And Safety

Mode changed from OFF to `SELECTIVE_CURRENT_FORMAL_FULL_FCF` at 2026-08-21 12:31:47 KST. API was
restarted and is healthy. Four AI tasks remain ACTIVE at 08:15/08:30/16:15/16:55; KRX telemetry
remains 08:05/16:05; AI mode is shadow; Production Assist is OFF.

Manual Telegram `0`; manual Scheduled Task `0`; Pilot mutation `0`; DB mutation/migration `0`;
archive/receipt rewrite `0`; paid provider/network request `0`; Public Action/schema/task/KRX config
change `0`.

## Severity And Parallel Tracks

- Open P0: `0`
- Open material P1: `0`
- P2: optional management-FCF reconciliation, OCF-only rollout, minor first-exposure length polish,
  and KR/OpenDART period recovery (`MEDIUM_FOLLOWUP`)
- Natural AI-Assisted Delivery: `PARTIAL`, independent
- Cash Flow User Visible Natural: pending next natural US
- KRX telemetry: parallel, unchanged
- CCC / standard ROIC: `DEFERRED / DEFERRED`

`CASH_FLOW_USER_VISIBLE_ROLLOUT_READY = YES`

`NEXT_MAJOR_ARCHITECTURE_READY = YES`

Recommended next architecture: Working Capital Canonical Core for inventory and typed trade AR/AP
point-in-time Facts and comparable balance deltas. Broader cash-flow exposure waits for the natural
Phase 9.0E proof; a new P0 uses the OFF kill switch.

Final state:

```text
Phase 9.0E: DEPLOYED_SELECTIVE_PENDING_NATURAL
Cash Flow User Visible: ENABLED_SELECTIVE_PENDING_NATURAL
Cash Flow Runtime Canary: LIVE_PASS_SELECTIVE_SUBSET
Baseline Cash-Flow Consistency: CLOSED
KR OpenDART Period Recovery: MEDIUM_FOLLOWUP
CCC: DEFERRED
ROIC: DEFERRED
```

