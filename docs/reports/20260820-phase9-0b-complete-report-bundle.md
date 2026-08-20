# Phase 9.0B Complete Report Bundle

Boundary: internal canonical/shadow implementation; user-visible behavior changes `0`.

# Phase 9.0B Canonical Core Implementation

Contract: `cash-flow-capital-efficiency-v1`

Implemented modules:

- `official_cash_flow_service`: exact SEC semantic registry, official occurrence extraction, fiscal-context normalization, deterministic reported Fact identity, version-aware selection.
- `cash_flow_shadow_service`: bounded period derivation, exact period/source pairing, deterministic PPE-only FCF, eligibility and audit serialization.
- `cash_flow_capital_efficiency_service`: explicit `REPORTED`, `DERIVED_PERIOD`, and `DERIVED_METRIC` types plus complete derivation metadata.

The production packet, AI prompt, renderer, fallback, Public Action, and database schema are unchanged. The core is internal shadow evidence only.


---

# Phase 9.0B Active Universe Results

Active monitored stocks: `20`; KR `7`; US/foreign `13`.

| Metric | Eligible | Partial | Blocked | N/A |
|---|---:|---:|---:|---:|
| OCF | 12 | 7 | 1 | 0 |
| PPE CAPEX | 11 | 6 | 2 | 1 |
| FCF | 11 | 0 | 8 | 1 |

| Ticker | Industry | OCF | PPE CAPEX | FCF | Latest period | Denial |
|---|---|---|---|---|---|---|
| 000660 | memory_semiconductor | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 003690 | insurance_reinsurance | PARTIAL | NOT_APPLICABLE | NOT_APPLICABLE | - | financial_industry_not_applicable |
| 005490 | steel_materials | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 005930 | memory_semiconductor | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 010120 | industrial_epc | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 012450 | aerospace_epc | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 086280 | transport_logistics | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| CORZ | hpc_data_center | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| CRCL | general_non_financial | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| GOOGL | cloud_platform_software | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| HUT | hpc_data_center | ELIGIBLE | BLOCKED | BLOCKED | - | missing_ppe_capex, compatible_ocf_capex_pair_missing |
| IBM | cloud_platform_software | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| MU | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-05-28 YTD | - |
| RXRX | biotech | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| SKHY | memory_semiconductor | BLOCKED | BLOCKED | BLOCKED | - | missing_ocf, missing_ppe_capex, compatible_ocf_capex_pair_missing |
| SNDK | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-07-03 FY | - |
| TSLA | automotive | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| TSM | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2024-12-31 FY | - |
| WRD | general_non_financial | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2025-06-30 YTD | - |
| WULF | hpc_data_center | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |

## Phase 9.0A Drift

- No status drift.


---

# Phase 9.0B Lineage Verification

- Canonical FCF facts audited: `191`
- Complete input lineage: `191`
- Complete lineage percentage: `100%`
- Lineage/arithmetic failures: `0`

Every eligible FCF retains exactly two input Fact IDs, matching issuer, period, currency/unit, entity scope, statement basis, and source-document chain. Derived raw SHA is deterministic over both input payload hashes.

## Representative Proofs

- **US domestic issuer**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **non-calendar fiscal issuer**: `MU`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **foreign issuer / ADR**: `TSM`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **CAPEX-heavy infrastructure**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **pre-profit biotech**: `RXRX`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **financial industry exclusion**: `003690`; OCF `PARTIAL`, CAPEX `NOT_APPLICABLE`, FCF `NOT_APPLICABLE`
- **KR period-context block**: `000660`; OCF `PARTIAL`, CAPEX `PARTIAL`, FCF `BLOCKED`


---

# Phase 9.0B FCF Reproduction Audit

Formula: `operating_cash_flow - positive-magnitude ppe_capex_cash_outflow`.

- Latest-period eligible issuers: `11`
- Blocked issuers: `8`
- Not applicable: `1`
- Arithmetic/provenance failures: `0`

Negative OCF and negative FCF remain valid. Missing OCF or CAPEX is never replaced with zero. Management-defined FCF remains separate and is not reconciled in this phase.


---

# Phase 9.0B Period Derivation Audit

- Reported interim cash-flow occurrences remain `YTD`.
- Verified Q1 YTD may produce a `DERIVED_PERIOD` QTD fact.
- Q2/Q3 QTD uses adjacent same-FY compatible YTD difference only.
- TTM uses prior FY + current YTD - prior comparable YTD only.
- Company Facts comparative rows inherit fiscal context from the earliest official occurrence for the same semantic, start/end, and unit; the latest filing remains the value/version authority.
- Annualization and calendar-year inference: `0`.
- Odd/53-week source dates are preserved.


---

# Phase 9.0B Eligibility Results

Eligibility is contract-driven, not ticker-driven. The implementation reproduces the Phase 9.0A selective subset without status drift.

- KR non-financial: `PARTIAL/BLOCKED`, reason `period_context_unresolved`, canonical promotion `0`.
- Insurance/reinsurance: generic enterprise PPE CAPEX/FCF `NOT_APPLICABLE`.
- Foreign/ADR: issuer-level OCF/PPE CAPEX/FCF may be eligible; per-share/yield/market-cap arithmetic is absent.
- HUT: OCF remains eligible, PPE CAPEX and FCF remain blocked.
- SKHY: official registered OCF/PPE semantics remain unavailable, so all core metrics fail closed.


---

# Phase 9.0B Shadow Cash-Flow Preview

This is archive-only internal evidence. No daily packet or public response consumes it.

| Ticker | Industry | OCF | PPE CAPEX | FCF | Latest period | Denial |
|---|---|---|---|---|---|---|
| 000660 | memory_semiconductor | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 003690 | insurance_reinsurance | PARTIAL | NOT_APPLICABLE | NOT_APPLICABLE | - | financial_industry_not_applicable |
| 005490 | steel_materials | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 005930 | memory_semiconductor | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 010120 | industrial_epc | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 012450 | aerospace_epc | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| 086280 | transport_logistics | PARTIAL | PARTIAL | BLOCKED | - | period_context_unresolved |
| CORZ | hpc_data_center | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| CRCL | general_non_financial | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| GOOGL | cloud_platform_software | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| HUT | hpc_data_center | ELIGIBLE | BLOCKED | BLOCKED | - | missing_ppe_capex, compatible_ocf_capex_pair_missing |
| IBM | cloud_platform_software | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| MU | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-05-28 YTD | - |
| RXRX | biotech | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| SKHY | memory_semiconductor | BLOCKED | BLOCKED | BLOCKED | - | missing_ocf, missing_ppe_capex, compatible_ocf_capex_pair_missing |
| SNDK | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-07-03 FY | - |
| TSLA | automotive | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |
| TSM | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2024-12-31 FY | - |
| WRD | general_non_financial | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2025-06-30 YTD | - |
| WULF | hpc_data_center | ELIGIBLE | ELIGIBLE | ELIGIBLE | 2026-06-30 YTD | - |

Canonical amounts and Fact IDs are in `20260820-phase9-0b-canonical-facts.json`. No FCF/share, FCF yield, EV/FCF, thesis delta, warning lifecycle, CCC, or ROIC is generated.


---

# Phase 9.0B Validation

## Repository

- Branch: `codex/phase-9-0b-canonical-ocf-capex-fcf-core`
- Base: `970ad2c3a1844e6dcbddbf47dff17d71170852d2`
- Implementation SHA: resolved by `git rev-parse HEAD` after commit
- Main/operating before promotion: `970ad2c3a1844e6dcbddbf47dff17d71170852d2`

## Canonical Evidence

- Active universe: 20; KR 7; US/foreign 13
- OCF: 12 eligible, 7 partial, 1 blocked
- PPE CAPEX: 11 eligible, 6 partial, 2 blocked, 1 not applicable
- FCF: 11 eligible, 8 blocked, 1 not applicable
- Phase 9.0A status drift: 0
- Derived FCF Facts: 191
- Complete input lineage and exact arithmetic: 191/191, 100%
- SEC network calls: 0; stored cache hits: 13
- OpenDART network calls/canonical promotions: 0/0

## Tests

- Canonical core focused suite: 61 passed
- Phase 8.5.x, price/RR, delivery, night-futures, and KRX focused regression: 225 passed
- Full pytest: 1,181 passed; one existing Starlette/httpx deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Project-state JSON and documentation links: PASS

## Contract Parity

- Investment Knowledge SHA: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`, three-way parity PASS
- Chart Knowledge SHA: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`, two-way parity PASS
- Public Action: `0.4.5`
- operationId: 20/20 unique
- Output schema: 4, unchanged
- Production packet/API/job imports of Phase 9.0B services: 0

## Operating Read-Only

- API health before promotion: PASS on `127.0.0.1:8766`
- Four AI Scheduled Task definitions/configuration changes: 0
- KRX telemetry LaunchAgent: 08:05/16:05 calendar-loaded, last exit 0
- Latest natural KRX 16:05 capture: HTTP 200, zero rows, `MARKET_COMPLETED_PROVIDER_PENDING`
- KRX user-visible integration: 0
- Manual Telegram / Scheduled Task / Pilot / DB / archive mutations: 0 / 0 / 0 / 0 / 0
- Production Assist: OFF

## Pending Exact-SHA Gate

Implementation and final documentation GitHub Actions Test/Lint must pass before main and operating fast-forward. No deployment occurs inside the 07:55-08:40 KST protection window.

Local P0 open: 0. Local P1 open: 0.

`PHASE_9_0C_READY = YES_CANDIDATE_PENDING_EXACT_SHA_CI`

`PHASE_9_0C_SCOPE = CASH_FLOW_SHADOW_CONSUMPTION_EARNINGS_QUALITY`


---

# Phase 9.0B Readiness

- Open P0: `0`
- Open P1: `0`
- Runtime user-visible diff: `0`
- KR OpenDART period recovery: `MEDIUM_COMPLEXITY_FOLLOWUP`
- CCC: `DEFERRED`
- Standard ROIC: `DEFERRED`

`PHASE_9_0C_READY = YES`

`PHASE_9_0C_SCOPE = CASH_FLOW_SHADOW_CONSUMPTION_EARNINGS_QUALITY`
