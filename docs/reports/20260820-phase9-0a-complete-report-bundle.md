# Phase 9.0A Complete Report Bundle

Generated: `2026-08-20T00:00:00+09:00`

Contract: `cash-flow-capital-efficiency-v1`

Boundary: architecture/evidence only; user-visible runtime changes `0`

# Cash Flow / Capital Efficiency Architecture

Contract: `cash-flow-capital-efficiency-v1`

## Problem

Existing financial lineage safely covers earnings and selected balance-sheet facts, but it does not close cash-flow period identity, PPE CAPEX scope, FCF derivation, working-capital dependencies, or standard ROIC denominator safety across the active universe.

## Decision

Extend the existing lineage contracts with an occurrence-bound cash-flow and capital-efficiency contract. Implement only deterministic eligibility and audit tooling in Phase 9.0A; do not connect it to production runtime or user-visible messages.

## Why

Cash-flow values become decision-useful only after their period, entity, statement, currency, semantic, and source occurrence agree. Selective safe coverage is preferable to either broad unsafe arithmetic or waiting for universal coverage.

## Rejected Alternative

Rejected alternatives include annualizing interim cash flow, treating total investing outflow as CAPEX, mixing CFS and OFS facts, importing management FCF as backend FCF, using all cash as excess cash, and blocking issuer-level foreign cash flow solely because an ADR ratio is unavailable.

## Safety Constraint

Missing or ambiguous dependencies produce `BLOCKED`, `PARTIAL`, or `NOT_APPLICABLE`. No reverse engineering, proxy substitution, cross-currency arithmetic, production packet mutation, renderer change, or user-visible integration is allowed in Phase 9.0A.

## Ownership And Lineage

This contract extends `financial-lineage-v2`, `financial-quality-taint-v2`, and `security-identity-v2`. It does not create a parallel truth store. Every reported fact retains issuer, period, currency/unit, entity scope, statement basis, document/accession, filing date, source occurrence, raw SHA-256, source sign, and semantic mapping. Every derived fact requires input fact IDs and an explicit formula.

## Period Model

- Flow facts are explicitly `QTD`, `YTD`, `FY`, or `TTM`; balance facts are `POINT_IN_TIME`.
- Verified fiscal Q1 YTD may also represent QTD when its duration is quarter-like.
- Q2/Q3 QTD is `current YTD - adjacent prior-quarter YTD` only under identical issuer, fiscal year start, semantic, currency/unit, entity scope, statement basis, and restatement policy.
- TTM is `prior FY + current YTD - prior comparable YTD` only under the same compatibility rules and issuer fiscal calendar.
- Annualization such as Q1 times four is prohibited.

## OCF, CAPEX, And FCF

- OCF means signed net cash provided by or used in operating activities. EBITDA, operating income, and net income are not proxies.
- Baseline CAPEX is positive-magnitude cash paid to acquire PPE. Total investing cash flow, acquisitions, securities purchases, intangibles, and capitalized software are excluded from the baseline.
- Intangibles and software remain separately typed components. They are never silently added to PPE CAPEX.
- Backend baseline FCF is `OCF - PPE-only CAPEX cash outflow`, with same period, currency/unit, entity scope, and statement basis.
- Company-reported non-GAAP FCF remains a separate management metric and never replaces backend-derived FCF.

## Working Capital

Inventory, trade AR, and trade AP are point-in-time raw facts. Broad receivable/payable totals are `PARTIAL`, not trade balances. The first implementation layer is balance deltas against a comparable date. DSO requires average trade AR and compatible revenue; inventory days requires average inventory and COGS; standard DPO requires purchases and average trade AP. CCC exists only when all three typed components are safe.

## ROIC

Standard ROIC requires compatible EBIT, a valid effective tax rate, beginning/end equity and interest-bearing debt, a verified excess-cash policy, and average invested capital. Total cash is never silently treated as excess cash. Insurance is excluded from generic ROIC. Until an excess-cash policy exists, standard ROIC is deferred.

## Issuer And Security Boundary

Issuer-level OCF, CAPEX, and margins may remain eligible for foreign issuers without an ADR ratio when statement lineage is safe. FCF/share, FCF yield, and EV/FCF require verified security/share, market-cap, currency, FX, and depositary basis. Cross-currency arithmetic is prohibited.

## Industry Applicability

| Framework | OCF | CAPEX/FCF | Inventory/AR/AP | CCC | ROIC |
|---|---|---|---|---|---|
| memory / foundry | PRIMARY | PRIMARY | PRIMARY | SECONDARY | CONTEXT_ONLY |
| cloud / platform / software | PRIMARY | PRIMARY | SECONDARY | CONTEXT_ONLY | SELECTIVE |
| automotive | PRIMARY | PRIMARY | PRIMARY | SECONDARY | SELECTIVE |
| transport / steel / industrial / EPC | PRIMARY | PRIMARY | PRIMARY | SECONDARY | SELECTIVE |
| HPC / data-center | PRIMARY | PRIMARY | SECONDARY | CONTEXT_ONLY | DEFERRED |
| biotech | PRIMARY as burn | PRIMARY as burn | CONTEXT_ONLY | NOT_APPLICABLE | NOT_APPLICABLE |
| insurance / reinsurance | CONTEXT_ONLY | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |

## AI Consumption Boundary

Architecture only in Phase 9.0A. Future AI input must keep facts separate from interpretation, remain delta-first, avoid automatic thesis changes, and expose missing data only when decision-relevant. No user-visible packet, prompt, fallback, or renderer changes are made here.


---

# Phase 9.0A Provider Coverage

## Source Hierarchy

1. Formal official statement
2. Official structured filing
3. Verified official earnings release
4. Existing validated structured provider

OpenDART stored evidence is reused for KR. SEC Company Facts official XBRL is used read-only for CIK-backed issuers. New paid sources and API keys: `0`.

## Call Audit

- SEC source-acquisition network requests: `12`
- SEC source-acquisition network successes: `12`
- SEC failures: `0`
- SEC payloads already present before acquisition: `1`
- Deterministic replay cache hits in final generation: `13`
- OpenDART live calls: `0`
- OpenDART stored provider calls represented by Phase 8.1.1: `22`
- OpenDART stored XBRL cache hits: `7`

Official references: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [OpenDART full financial statements](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020).


---

# Phase 9.0A Active Universe Coverage

Active stocks: `20`; KR `7`; US/foreign `13`; financial `1`.

| Metric | Eligible | Partial | Blocked | N/A |
|---|---:|---:|---:|---:|
| ocf | 12 | 7 | 1 | 0 |
| capex_ppe | 11 | 6 | 2 | 1 |
| fcf | 11 | 0 | 8 | 1 |
| revenue | 17 | 1 | 2 | 0 |
| inventory | 14 | 0 | 5 | 1 |
| ar | 0 | 11 | 8 | 1 |
| ap | 0 | 8 | 11 | 1 |
| cogs | 11 | 0 | 8 | 1 |
| ocf_margin | 11 | 0 | 8 | 1 |
| fcf_margin | 11 | 0 | 8 | 1 |
| capex_intensity | 10 | 0 | 9 | 1 |
| cash_conversion | 11 | 0 | 8 | 1 |
| dso | 0 | 0 | 19 | 1 |
| inventory_days | 0 | 0 | 19 | 1 |
| dpo | 0 | 0 | 19 | 1 |
| ccc | 0 | 0 | 19 | 1 |
| roic | 0 | 0 | 19 | 1 |

| Ticker | Industry | ocf | capex_ppe | fcf | inventory | ar | ap | cogs | ccc | roic |
|---|---|---|---|---|---|---|---|---|---|---|
| 000660 | memory_semiconductor | PARTIAL | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| 003690 | insurance_reinsurance | PARTIAL | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |
| 005490 | steel_materials | PARTIAL | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| 005930 | memory_semiconductor | PARTIAL | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| 010120 | industrial_epc | PARTIAL | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| 012450 | aerospace_epc | PARTIAL | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| 086280 | transport_logistics | PARTIAL | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| CORZ | hpc_data_center | ELIGIBLE | ELIGIBLE | ELIGIBLE | BLOCKED | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |
| CRCL | general_non_financial | ELIGIBLE | ELIGIBLE | ELIGIBLE | BLOCKED | PARTIAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| GOOGL | cloud_platform_software | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |
| HUT | hpc_data_center | ELIGIBLE | BLOCKED | BLOCKED | BLOCKED | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |
| IBM | cloud_platform_software | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |
| MU | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED |
| RXRX | biotech | ELIGIBLE | ELIGIBLE | ELIGIBLE | BLOCKED | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |
| SKHY | memory_semiconductor | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| SNDK | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | PARTIAL | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED |
| TSLA | automotive | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |
| TSM | memory_semiconductor | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | BLOCKED | BLOCKED | ELIGIBLE | BLOCKED | BLOCKED |
| WRD | general_non_financial | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |
| WULF | hpc_data_center | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE | PARTIAL | PARTIAL | ELIGIBLE | BLOCKED | BLOCKED |

`ELIGIBLE` requires lineage, not merely field presence. Each blocked or partial cell has a machine-readable reason in the coverage JSON.


---

# Phase 9.0A Cash-Flow Lineage Audit

The SEC audit retains exact namespace/tag, accession, form, filed date, start/end, unit, value, fiscal year/period, and payload SHA. FCF pairs require the same accession, start, end, and unit. The KR audit preserves OpenDART receipt, CFS/OFS, statement section, taxonomy tag, source row identity, amount, and denial reason.

KR evidence found exact OCF and PPE/intangible rows, but the existing XBRL matcher could not prove a unique CF period context. Therefore KR OCF is `PARTIAL`, CAPEX is `PARTIAL`, and FCF is `BLOCKED`; no value is promoted. SEC eligible pairs are issuer-level and do not authorize security-level per-share or yield arithmetic.

## Representative Proofs

- **KR non-financial industrial**: `000660`; OCF `PARTIAL`, CAPEX `PARTIAL`, FCF `BLOCKED`
- **US domestic issuer**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **non-calendar fiscal issuer**: `MU`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **foreign issuer / ADR**: `TSM`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **capex-heavy data-center**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **pre-profit biotech**: `RXRX`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **financial / insurance exclusion**: `003690`; OCF `PARTIAL`, CAPEX `NOT_APPLICABLE`, FCF `NOT_APPLICABLE`


---

# Phase 9.0A FCF Eligibility Matrix

Baseline: `OCF - positive-magnitude PPE-only cash outflow`.

- OCF eligible: `12`
- PPE CAPEX eligible: `11`
- FCF eligible: `11`
- FCF partial: `0`
- FCF blocked: `8`
- FCF not applicable: `1`

Intangibles and capitalized software remain separate. Acquisitions and total investing cash flow are excluded. Management FCF and backend FCF remain different metrics.


---

# Phase 9.0A Working-Capital Eligibility

- Inventory eligible: `14`
- Trade AR eligible: `0`; broad/partial: `11`
- Trade AP eligible: `0`; broad/partial: `8`
- Full CCC eligible: `0`

Phase 9.0B does not include CCC. Raw balances and comparable-date deltas are the first safe layer. DSO, inventory days, DPO, and CCC are deferred until average typed balances and compatible flow denominators exist.


---

# Phase 9.0A ROIC Eligibility

Standard safe: `0`. Blocked: `19`. Not applicable: `1`.

Decision: `ROIC_DEFERRED`. Existing data does not provide a verified excess-cash policy across the eligible universe. Phase 9.0B must not label `Equity + Debt - All Cash` as standard invested capital. A later selective implementation may proceed only with explicit excess-cash evidence and average balance inputs.


---

# Phase 9.0A Industry Applicability

OCF/CAPEX/FCF are primary for memory, foundry, platform, automotive, transport, steel, industrial, and HPC/data-center subjects when lineage is safe. Biotech uses OCF/FCF as burn and runway context, not automatic thesis weakening. Insurance/reinsurance uses P/B-ROE, combined ratio, investment income, and capital adequacy; generic corporate FCF, CCC, and ROIC are not primary and are marked not applicable.

Single-quarter working-capital swings and peak-cycle FCF never become automatic structural thesis changes. Industry interpretation remains downstream of canonical evidence.


---

# Phase 9.0A Representative Lineage Proofs

- **KR non-financial industrial**: `000660`; OCF `PARTIAL`, CAPEX `PARTIAL`, FCF `BLOCKED`
- **US domestic issuer**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **non-calendar fiscal issuer**: `MU`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **foreign issuer / ADR**: `TSM`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **capex-heavy data-center**: `CORZ`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **pre-profit biotech**: `RXRX`; OCF `ELIGIBLE`, CAPEX `ELIGIBLE`, FCF `ELIGIBLE`
- **financial / insurance exclusion**: `003690`; OCF `PARTIAL`, CAPEX `NOT_APPLICABLE`, FCF `NOT_APPLICABLE`

The selected tickers are derived from the active universe and taxonomy, not production exceptions. Full occurrence details and reasons are in `20260820-phase9-0a-coverage.json`.


---

# Phase 9.0A Readiness

## Closed Definitions

- Period model: `QTD/YTD/FY/TTM/POINT_IN_TIME`, strict fiscal alignment, no annualization.
- OCF: exact operating-activities cash flow only.
- CAPEX: PPE-only cash outflow baseline; intangibles/software separate.
- FCF: same-period, same-unit, same-entity/basis OCF less PPE CAPEX.
- Working capital: raw balances and deltas first; CCC deferred.
- ROIC: deferred until verified excess-cash policy; insurance excluded.
- Foreign/ADR: issuer-level ratios may be safe; security-level yield/per-share metrics remain blocked without security/FX basis.
- Provisional earnings: no missing cash-flow inference.

Open P0: `0`. Open P1: `0`. P2 backlog: management-FCF reconciliation breadth, CCC coverage, excess-cash policy/ROIC, and user-visible wording for a later phase.

`PHASE_9_0B_READY = YES`

`PHASE_9_0B_SCOPE = SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`

Recommended next phase: Phase 9.0B canonical OCF/PPE-CAPEX/FCF core implementation for evidence-eligible issuers, fail-closed elsewhere. Working capital follows after raw balance coverage; advanced ROIC remains deferred.


---

# Phase 9.0A Validation And Operating Safety

- Branch: `codex/phase-9-0a-cash-flow-capital-efficiency-architecture`
- Base: `2c2aacf1df25a3d0483a14ecf19857ea9c1371b9`
- Contract/generator tests: 35 passed
- Focused regression: 278 passed
- Full pytest: 1,155 passed; 1 existing dependency deprecation warning
- Ruff / diff / JSON: PASS / PASS / PASS
- Investment Knowledge / Chart Knowledge: PASS / PASS
- Public Action / operationId: `0.4.5` / 20 of 20 unique
- Runtime imports, packet changes, renderer changes, DB schema changes: 0
- Manual Telegram / Task / Pilot / DB mutations: 0 / 0 / 0 / 0
- Production Assist: OFF
- AI-review automations: four ACTIVE, configuration changes 0
- KRX telemetry: 08:05/16:05 calendar-loaded, last exit 0, user-visible integration 0
- API restart: 0; architecture-only unimported contract

The architecture implementation and its final documentation are both exact-SHA CI gated.

# Repository And Promotion

- Previous main: `2c2aacf1df25a3d0483a14ecf19857ea9c1371b9`
- Implementation SHA: `68a35c68cacd03a6f430abb6ff4d9b3e622449a6`
- Implementation Actions: run `32361906260`, Test/Lint PASS
- Final documentation SHA: `HEAD`, resolved by `git rev-parse origin/main`
- Final documentation Actions: Test/Lint PASS required before final main fast-forward
- Main promotion: `YES`, clean linear fast-forward
- Operating sync: `YES`, clean fast-forward to `origin/main`
- API restart: `NO`, runtime import/behavior changed 0
- Runtime behavior changed: `NO`

# Final Gate

Open P0: `0`

Open P1: `0`

`PHASE_9_0B_READY = YES`

`PHASE_9_0B_SCOPE = SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`
