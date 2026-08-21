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

No DSO, Inventory Days, DPO, CCC, AI packet, fallback, Public Action, thesis-state, warning, or user-visible behavior is implemented in Phase 9.1A.

## Phase 9.1B Canonical Core

Phase 9.1B implements the approved selective core without changing the source adapters or creating a parallel truth store. `working_capital_core_service` consumes the Phase 9.1A `FinancialFact` stream after `source_available_at <= as_of_date` filtering and produces an audit-only per-issuer snapshot.

The canonical raw families remain `inventory`, `trade_accounts_receivable`, `accounts_receivable_broad`, `trade_accounts_payable`, and `accounts_payable_broad`. Each metric independently selects its latest safe current Fact and exact prior-year same-fiscal-quarter comparable. A missing metric never blocks another metric.

Safe pairs produce two deterministic `DERIVED_METRIC` Facts:

- `working_capital_balance_delta = current - prior` in the reported currency/unit.
- `working_capital_balance_yoy_growth = (current - prior) / prior * 100` as a dimensionless percent, only when prior is positive.

Compatible Revenue/COGS pairs produce `financial_flow_yoy_growth` Facts. Structured `YOY_GROWTH_COMPARISON` relations then retain the balance metric and exact semantic/scope, flow metric and semantic, four raw Fact IDs, both canonical YoY Fact IDs, direction, percentage-point gap, formula, derivation version, eligibility, and cautions. Trade and broad AR/AP therefore cannot collapse in relation identity.

The derivation version is `working-capital-evidence-v1:canonical-core-v1`. Repeated input processing yields the same Fact and relation IDs. Hard-tainted, unavailable, future, mismatched, non-comparable, or non-positive-denominator inputs fail closed. Restatement policy and source availability propagate to every derived Fact.

The 20-subject implementation reproduces the Phase 9.1A metric coverage with zero newly blocked families. It audits 160 selected reported Facts, 44 delta Facts, 44 balance YoY Facts, 31 flow YoY Facts, and 53 fully lined structured relations with zero arithmetic, provenance, or idempotency errors. Korean Re remains `NOT_APPLICABLE`; KR non-financial balance-sheet evidence remains independent of the unresolved OpenDART cash-flow duration context.

The canonical snapshot is used only by tests and `scripts/phase9_1b_evidence.py`. It is not imported into production packets, AI context, Telegram, fallback, Public Action, schema 4, assessment state, warning lifecycle, or database storage. DSO, Inventory Days, DPO, CCC, standard ROIC, contract assets, inventory component aggregation, accrued-liability decomposition, and prior-quarter lifecycle remain deferred.
