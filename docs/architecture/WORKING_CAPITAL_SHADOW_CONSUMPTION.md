# Working Capital Shadow Consumption

Contract: `working-capital-shadow-consumption-v1`.

## Problem

Canonical working-capital evidence can be correct yet stale, semantically broader than trade-only,
causally ambiguous, or irrelevant to a daily investment decision. Sending every eligible relation
would create numeric clutter and false precision.

## Decision

Phase 9.1C consumes the Phase 9.1B canonical `FinancialFact` and `WorkingCapitalRelation` objects without recalculating balances, YoY growth, or relation gaps. A sidecar applies source-availability PIT, latest-formal freshness, exact trade/broad semantic labels, industry applicability, and materiality before selecting at most one primary relation.

The selected relation keeps its canonical relation ID, six input Fact IDs, direction, and percentage-point gap. Exact numbers are owned only by `business_earnings`. Broad AR/AP can never be rendered as trade AR/AP. Contract assets and accrued liabilities remain separate. Cautious interpretation may identify a check, but it cannot assign collection, demand, supplier-payment, liquidity, thesis, warning, or valuation causality.

Unknowns resolve as `RESOLVED_EXACT`, narrow as `RESOLVED_BROAD_ONLY`, or remain `STILL_VALID`, `STALE_CONTEXT_ONLY`, or `NOT_APPLICABLE`. A compatible same-formal-period cash-flow context may qualify the relation, but Phase 9.1C never recomputes or causally explains OCF/FCF.

## Why

The separation keeps evidence correctness, currentness, semantic precision, materiality, and
interpretation as independent gates. It lets high-value Inventory or exact Trade AR evidence improve
analysis without forcing broad AP or low-value relations into every subject.

## Rejected Alternative

The phase rejects a full five-metric dump, broad-to-trade relabeling, arbitrary significance scores,
AI-side subtraction, causal verdicts, and automatic DSO/Inventory Days/DPO/CCC derivation.

## Safety Constraint

The service is archive-only. Production packet, AI prompt, Telegram, fallback, Public Action `0.4.5`, schema `4`, and Phase 9.0E rollout mode are unchanged.
