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
