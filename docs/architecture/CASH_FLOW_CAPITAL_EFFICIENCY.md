# Cash Flow / Capital Efficiency Architecture

Contract: `cash-flow-capital-efficiency-v1`

## Problem

Existing financial lineage safely covers earnings and selected balance-sheet facts, but it does not close cash-flow period identity, PPE CAPEX scope, FCF derivation, working-capital dependencies, or standard ROIC denominator safety across the active universe.

## Decision

Extend the existing lineage contracts with an occurrence-bound cash-flow and capital-efficiency contract. Phase 9.0A closes the evidence architecture; Phase 9.0B implements the selective OCF, PPE-CAPEX, and FCF canonical core as internal shadow evidence. Phase 9.0C consumes those Facts only through a point-in-time and freshness-gated archive sidecar. None connects cash-flow facts to production packets or user-visible messages.

## Why

Cash-flow values become decision-useful only after their period, entity, statement, currency, semantic, and source occurrence agree. Selective safe coverage is preferable to either broad unsafe arithmetic or waiting for universal coverage.

## Rejected Alternative

Rejected alternatives include annualizing interim cash flow, treating total investing outflow as CAPEX, mixing CFS and OFS facts, importing management FCF as backend FCF, using all cash as excess cash, and blocking issuer-level foreign cash flow solely because an ADR ratio is unavailable.

## Safety Constraint

Missing or ambiguous dependencies produce `BLOCKED`, `PARTIAL`, or `NOT_APPLICABLE`. No reverse engineering, proxy substitution, cross-currency arithmetic, production packet mutation, renderer change, or user-visible integration is allowed in Phase 9.0A or 9.0B.

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

## Canonical Implementation

Phase 9.0B implements three exact metrics: `operating_cash_flow`,
`ppe_capex_cash_outflow`, and `free_cash_flow_ppe`. Official SEC Company Facts occurrences are
accepted only through the reviewed semantic registry. Generic investing cash flow, acquisitions,
securities purchases, intangibles, and broad productive-asset concepts are explicit denials.

Reported Fact IDs include issuer, metric, period, entity/basis, currency, and source occurrence.
Derived Fact IDs include their ordered input Fact IDs. `REPORTED`, `DERIVED_PERIOD`, and
`DERIVED_METRIC` are distinct types. The latest filing is value/version authority; when a later
filing republishes a comparative column with the later filing's `fy`, the economic fiscal context
comes from the earliest official occurrence for the same semantic, start/end, and unit. No dates
are guessed.

Every FCF uses exactly two eligible Facts from the same period, currency/unit, entity scope,
statement basis, and source-document chain. Input quality taint, source conflict, or missing
metadata blocks derivation. The internal derivation window retains the latest fiscal year plus the
two prior fiscal years needed for QTD/TTM construction; official source dates remain unchanged.

The active-universe implementation reproduces the Phase 9.0A coverage with no status drift: OCF
`12 eligible / 7 partial / 1 blocked`, PPE CAPEX `11 / 6 / 2 / 1 not applicable`, and FCF
`11 eligible / 8 blocked / 1 not applicable`. Across the stored SEC evidence, all 191 derived FCF
Facts have complete input lineage and exact Decimal arithmetic. KR OpenDART cash-flow rows remain
unpromoted because period context is unresolved; generic insurance FCF remains not applicable.

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

Phase 9.0C implements `cash-flow-shadow-consumption-v1` for archive-only interpretation. It checks source availability at replay cutoff, formal-period freshness, strict comparable periods, industry applicability, and materiality before rendering. Exact numbers bind only to Phase 9.0B Fact IDs under `business_earnings`; resolved cash-flow Unknowns are suppressed or replaced with the next evidence gap. Stale and later-provisional cases remain context-only, and unsupported yield/per-share/ROIC/CCC claims fail validation.

The 20-subject replay yields 12 consumption-eligible contexts and 10 material uses: nine full FCF and one OCF-only. TSM and WRD are formal-lagging-provisional context-only, six KR non-financial subjects remain blocked, and Korean Re is not applicable. Production packet, prompt, fallback, Public Action, renderer, Telegram, and database behavior remain unchanged.

## Selective User-Visible Boundary

Phase 9.0E adds `cash-flow-user-visible-v1` without changing the canonical formulas. The first
rollout accepts only US/foreign SEC current-formal full-FCF contexts and renders one PPE-only FCF
number under business/earnings ownership. OCF-only, KR, insurance generic FCF, lagging or stale
periods, security-level FCF valuation, CCC, and standard ROIC remain excluded. The operating mode
is kill-switchable and defaults/fails safe to OFF. Natural user-visible proof is pending.
