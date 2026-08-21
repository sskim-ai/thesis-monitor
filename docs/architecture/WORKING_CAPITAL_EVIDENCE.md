# Working Capital Evidence Architecture

Contract: `working-capital-evidence-v1`

## Decision

Working-capital evidence extends the canonical financial lineage model. Inventory, receivables, and payables are point-in-time Facts keyed by `balance_date`; revenue and COGS are duration Facts used only when issuer fiscal period, exact semantic, currency/unit, entity scope, statement basis, and source version align.

The exact canonical raw metric names are:

- `inventory`: total inventory semantic only; component aggregation is prohibited unless separately proven.
- `trade_accounts_receivable`: exact trade semantic only.
- `accounts_receivable_broad`: broad/current or trade-and-other receivables, never renamed trade AR.
- `trade_accounts_payable`: exact trade semantic only.
- `accounts_payable_broad`: broad/current or trade-and-other payables, never renamed trade AP.

`AR_INITIAL_SCOPE = TRADE_PLUS_SEPARATE_BROAD`

`AP_INITIAL_SCOPE = TRADE_PLUS_SEPARATE_BROAD`

Current/noncurrent scope is preserved from the source. No automatic summation or AR gross-up occurs. SEC facts retain issuer-reported scope; OpenDART CFS is consolidated and never mixed with OFS.

## Comparable Rule

The primary pair is the same issuer fiscal quarter in the prior fiscal year with the same exact semantic, currency/unit, entity scope, statement basis, and authoritative source version. Q2 versus prior FY-end is not YoY. Non-calendar issuers use fiscal identity rather than calendar-quarter assumptions. Restated values use the latest authoritative occurrence while preserving the economic period from the earliest official occurrence.

Absolute delta is `current - prior`. YoY percentage is calculated only when the prior balance is positive. Missing or zero is never substituted. A negative normalized balance is blocked for source review.

Revenue and COGS relations require the same filing and matching fiscal period end/type. Q2/Q3 YTD is preferred. Relation output is factual (`BALANCE_INCREASED`, `AR_GROWTH_GT_REVENUE_GROWTH`, and related typed identities), never a good/bad or thesis verdict.

## Point-In-Time And Freshness

Every Fact retains filing/source availability. Historical replay requires `source_available_at <= cutoff`. A newer provisional earnings period without a formal balance sheet yields `FORMAL_LAGGING_PROVISIONAL`; the older balance is not relabeled as the provisional quarter. No 30/60/90-day threshold is introduced.

## Industry And Safety

Inventory is primary for memory, automotive, and steel/materials; AR is primary for industrial/project and transport subjects where semantics are safe. Contract assets are not trade AR. Accrued liabilities are not trade AP. Insurance/reinsurance is `NOT_APPLICABLE`; biotech and special financial-like platforms remain context-only unless business-specific evidence supports more.

No DSO, Inventory Days, DPO, CCC, AI packet, fallback, Public Action, snapshot, thesis-state, warning, or user-visible behavior is implemented in Phase 9.1A.
