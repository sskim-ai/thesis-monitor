# Phase 9.1A Complete Report

## Repository

- Repository: `sskim-ai/thesis-monitor`
- Branch: `codex/phase-9-1a-working-capital-evidence-architecture`
- Operating/main base: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- Work-instruction commit: `eaaadb1ac4fb5c9a7d3486ecc8274708c285ff79`
- Implementation commit: `0d3b42715fc8964fe053d72e0ecc979fb78b14cc`
- Final branch SHA: resolve with `git rev-parse HEAD`; documentation commits are intentionally not self-referential
- Push: `origin/codex/phase-9-1a-working-capital-evidence-architecture`
- Main/operating promotion: `PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`
- Main/operating SHA at completion: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- Development and operating working trees: clean at their respective committed SHAs after finalization
- Runtime/user-visible behavior diff: `0`

Phase 9.1A was performed from the immutable instruction commit. The implementation is a linear
descendant. Promotion was intentionally not combined with the protected KR natural window; this is
an operating-safety defer, not an architecture failure.

## Contract

`working-capital-evidence-v1` extends the existing financial Fact architecture. It does not create a
parallel truth store. The three point-in-time families are total Inventory, exact trade AR/AP, and
separate broad AR/AP. Revenue and COGS are compatible duration facts used only for typed comparison.

- Inventory: total inventory only; no silent component aggregation.
- AR: `TRADE_PLUS_SEPARATE_BROAD`; broad/current or trade-and-other AR is never renamed trade AR.
- AP: `TRADE_PLUS_SEPARATE_BROAD`; broad/current or trade-and-other AP is never renamed trade AP.
- Scope: current/noncurrent/total and issuer-reported net/gross scope are preserved.
- Primary comparable: prior fiscal year, same fiscal quarter, exact semantic, currency/unit, entity,
  statement basis, and authoritative source version.
- Revenue/COGS: same compatible filing period; Q2/Q3 YTD is preferred.
- PIT: source availability must be on or before a replay cutoff.
- Provisional earnings: never creates a balance-sheet period or relabels an older formal balance.

## Active Universe

The active runtime universe contains 20 subjects: KR 7 and US/foreign 13. Financial types are 18
non-financial, one pre-profit biotech, and one insurance/reinsurance subject. Industry distribution:
memory/semiconductor 6, HPC/data center 3, cloud/platform/software 2, and one each in automotive,
steel/materials, transport/logistics, industrial EPC, aerospace EPC, biotech,
insurance/reinsurance, special financial-like, and general non-financial.

## Providers

- SEC Company Facts official stored cache: 13 hits, 0 misses, 0 live calls.
- OpenDART official full statements: 12 bounded read-only requests, 12 successes, 0 failures.
- OpenDART generation cache: 12 hits, 0 misses.
- OpenDART scope: six active KR non-financial issuers, 2026/2025 half-year CFS only.
- New paid provider/API/subscription: `0 / 0 / 0`.
- Secrets in reports: `0`.

The bounded OpenDART acquisition does not crawl other years/forms and does not attempt the separate
KR cash-flow period-context recovery.

## Coverage

| Metric | Eligible | Partial | Blocked | N/A |
|---|---:|---:|---:|---:|
| Total Inventory | 11 | 3 | 5 | 1 |
| Exact trade AR | 6 | 1 | 12 | 1 |
| Separate broad AR | 9 | 3 | 7 | 1 |
| Exact trade AP | 8 | 1 | 10 | 1 |
| Separate broad AP | 10 | 1 | 8 | 1 |

`PARTIAL` means a safe current Fact exists but a compatible prior-year comparable is unavailable.
`BLOCKED` means no safe current semantic or compatible evidence exists. Missing is never zero.

## Relations

Deterministic balance relations preserve exact Fact inputs. Absolute delta is current minus prior;
YoY percent is emitted only with a positive prior denominator. Cross-growth relations compare two
already safe YoY facts and do not emit good/bad or thesis verdicts.

| Relation | Eligible | Blocked | N/A |
|---|---:|---:|---:|
| AR vs revenue | 14 | 5 | 1 |
| Inventory vs revenue | 11 | 8 | 1 |
| Inventory vs COGS | 11 | 8 | 1 |
| AP vs COGS | 14 | 5 | 1 |

COGS-relative relations are selective exact-semantic relations. Contract assets, accrued
liabilities, other receivables/payables, and purchases are not silently substituted.

## Representative Proofs

- KR memory, `000660` Inventory: 2026-06-30 Fact
  `working-capital-reported:b742cc7afdc66afa6d7e1135` versus 2025-06-30 Fact
  `working-capital-reported:3d542b94d368f70add0d6170`; CFS KRW; `BALANCE_INCREASED`.
- US platform, `GOOGL` broad AR: 2026-06-30 Fact
  `working-capital-reported:173c00a08ebaaa117ff3753e` versus 2025-06-30 Fact
  `working-capital-reported:0e317adeb7323c084c405429`; USD; broad AR remains non-trade.
- Non-calendar memory, `MU` Inventory: 2026-05-28 Fact
  `working-capital-reported:2a5dd10bfd88a91b65bcc777` versus 2025-05-29 Fact
  `working-capital-reported:00d1a7bd62280782e2efae65`; issuer fiscal Q3, not calendar-quarter inference.
- Foreign issuer, `TSM` Inventory: issuer-level USD Fact is eligible without ADR share/price basis.
- HPC, `CORZ` broad AR: 2025-03-31 versus 2024-03-31 is eligible; an FY-end comparative republished
  in a Q1 filing is not relabeled as fiscal Q1.
- Biotech, `RXRX` broad AP: eligible evidence remains context-only; no generic quality verdict.
- Insurance, `003690`: generic industrial working-capital relations are `NOT_APPLICABLE`.

Every proof in the coverage JSON preserves exact document, occurrence, semantic, source availability,
payload SHA, balance date, filing date, currency/unit, entity/basis, Fact IDs, and relation inputs.

## KR And Period Safety

Six KR non-financial issuers have safe 2026-06-30 versus 2025-06-30 CFS point-in-time evidence. This
is independent of the unresolved OpenDART cash-flow duration context: balance dates are explicit and
are not promoted from cash-flow rows. CFS and OFS are never mixed. Korean Re remains not applicable.

A repaired fiscal-context defect is permanently tested: a prior FY-end balance republished in a Q1
filing cannot become a Q1 comparable. Source frame/annual context and an approximately one-fiscal-
year date compatibility check must agree. Non-calendar issuers retain their actual fiscal identity.

## Industry Applicability

Memory/semiconductor, automotive, and steel/materials treat Inventory as primary. Industrial/EPC
and transport use AR/AP only when exact semantics support order-to-cash or collection context.
Cloud/software treats broad AR/AP as secondary. HPC relations remain construction/billing context,
not a generic cash-burn verdict. Biotech and special financial-like subjects remain context-only.
Insurance/reinsurance is not applicable to generic industrial working-capital reasoning.

## Advanced Ratios

- `DSO_READY_FOR_IMPLEMENTATION = DEFER`
- `INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = DEFER`
- `DPO_READY_FOR_IMPLEMENTATION = DEFER`
- `CCC_READY_FOR_IMPLEMENTATION = DEFER`

The architecture intentionally stops at raw balances, comparable deltas, YoY growth, and selective
cross-growth relations. Average balances, purchases semantics, and complete compatible components do
not yet support safe portfolio-wide day ratios or CCC.

## Validation

- Focused working-capital/cash-flow tests: `61 passed`.
- Broader financial/runtime regression: `206 passed`.
- Full pytest: `1288 passed, 1 third-party deprecation warning`.
- Deterministic generator: identical SHA-256 outputs before/after rerun.
- Ruff: PASS.
- `git diff --check`: PASS.
- Investment Knowledge v3 parity: PASS.
- Chart Knowledge v1 parity: PASS.
- Public Action: `0.4.5`; operationId `20/20 unique`; schema `4`.
- Documentation links/state JSON: PASS.
- Implementation exact-SHA Actions run `32447178183`: Test PASS, Lint PASS.
- Final-main CI: not required yet because promotion is deferred.

## Operating Safety

- Operating/main remains `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`, clean.
- API health: PASS; no restart performed.
- Phase 9.0E mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`, unchanged.
- Four AI tasks: ACTIVE at 08:15, 08:30, 16:15, and 16:55 KST; changes/manual runs `0 / 0`.
- KRX telemetry: 08:05/16:05 LaunchAgent unchanged; manual runs `0`.
- Telegram/manual task/Pilot/DB/archive mutations: `0 / 0 / 0 / 0 / 0`.
- Production Assist: `OFF`.

## Severity And Parallel Tracks

- Open P0: `0`.
- Open material P1: `0`.
- P2: prior-quarter relations, inventory components, management-specific contract assets, and
  prerequisites for DSO/Inventory Days/DPO/CCC.
- Phase 9.0E natural user-visible proof: pending next natural US review.
- KR natural cycle: protected; separate review required before promotion.
- KRX publication telemetry: continues independently.
- KR cash-flow period recovery: medium follow-up, not a 9.1B blocker.

## Final Gate

The canonical raw semantics, PIT identity, fiscal comparability, source/basis/currency/unit rules,
coverage matrix, US/KR/foreign/non-calendar/insurance proofs, relation formulas, CI, and zero-runtime-
diff boundary are closed. Selective coverage is sufficient; unsupported subjects remain fail-closed.

`PHASE_9_1B_READY = YES`

`PHASE_9_1B_SCOPE = SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE`

Recommended next phase: **Phase 9.1B - Canonical Working Capital Core**, limited to the approved raw
metrics, prior-year comparable deltas/YoY, and selective four cross-growth relations. Advanced day
ratios and all user-visible consumption remain outside scope.
