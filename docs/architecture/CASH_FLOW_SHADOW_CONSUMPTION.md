# Cash Flow Shadow Consumption

Contract: `cash-flow-shadow-consumption-v1`

## Problem

Canonical OCF, PPE CAPEX, and PPE-only FCF can be correct but still unsuitable for a historical or current investment decision. Filing availability, formal-period freshness, comparable periods, industry meaning, materiality, and previously unresolved Unknowns must be checked before AI reasoning consumes a Fact.

## Decision

Consume `cash-flow-capital-efficiency-v1` Facts through a separate archive-only sidecar. The order is point-in-time availability, formal-filing freshness, comparable-period compatibility, industry applicability, deterministic materiality, interpretation, numeric binding, and semantic validation. Production packet schema 4, prompts, fallback, Public Action, and Telegram remain unchanged.

## Why

This keeps three different questions separate: whether a Fact is canonical, whether it is current enough for the decision, and whether it is material enough to mention. It also permits a valid issuer-level foreign-currency FCF while preventing stale-as-current language, unsupported security-level valuation arithmetic, or generic cash-burn conclusions.

## Rejected Alternative

Rejected alternatives include adding every eligible OCF/CAPEX/FCF tuple to prose, using day-count freshness thresholds, treating a later provisional earnings period as aligned cash flow, substituting an older safe period for a newer blocked formal period, calculating growth percentages across negative bases, and changing a thesis or valuation state from cash flow alone.

## Safety Constraint

Historical replay uses only Facts whose official filing date is on or before the assessment cutoff. Missing source dates fail closed. YTD, QTD, FY, and TTM comparisons require the same metric, duration class, issuer, currency/unit, entity scope, statement basis, semantic scope, and comparable fiscal position. Unsupported FCF yield, per-share FCF, EV/FCF, P/FCF, CCC, ROIC, and runway calculations are rejected.

## Selection States

- `CURRENT_FORMAL`: the primary cash-flow period matches the latest validated formal financial period.
- `FORMAL_LAGGING_PROVISIONAL`: the Fact remains valid but a later official preliminary earnings period prevents current-period use.
- `STALE_FORMAL`: a newer formal period exists and the older safe cash flow is not a current substitute.
- `BLOCKED`: canonical facts or required alignment metadata are unavailable.
- `NOT_APPLICABLE`: generic enterprise cash-flow reasoning does not apply, including insurance.

Usage is independently typed as full FCF, OCF-only, CAPEX-only, latest-formal context-only, suppressed, or not applicable. OCF-only evidence never implies FCF.

## Comparison And Meaning

FY compares with prior FY, YTD with prior-year comparable YTD, QTD with comparable QTD, and TTM only with safely derived comparable TTM. Relations are sign-aware: positive higher/lower, negative less/more negative, and sign transitions. The service creates no good/bad score and no percentage growth.

Exact cash-flow numbers belong to `business_earnings`. Core judgment may summarize meaning without repeating the exact value. Valuation and price sections do not own cash-flow numbers in this phase. A fresh full Fact resolves a generic cash-flow-missing Unknown; partial, lagging, blocked, and not-applicable cases retain a precise limitation instead.

## Industry Interpretation

The Phase 9.0A applicability matrix remains authoritative. Cloud investment is paired with Cloud growth and margin, memory with ASP/mix/inventory and cycle position, HPC with build-out, energization or billing and financing, biotech with cash burn but no inferred runway, automotive with margin and growth investment, and insurance with no generic enterprise FCF reasoning. Negative FCF is a Fact, not an automatic thesis verdict.

## Archive Proof

The immutable run-28 US baseline and run-29 KR negative control differ only by the archive sidecar. Across 20 subjects, 12 pass consumption eligibility and 10 are materially rendered: nine full FCF and one OCF-only. TSM and WRD remain latest-formal context-only because later provisional periods exist; six KR non-financial subjects remain blocked; Korean Re is not applicable.

All 10 rendered numeric claims bind automatically to Phase 9.0B Fact IDs. Manual, rejected, unresolved, semantic-error, future-use, stale-as-current, and KR numeric-injection counts are zero. Eight of 17 cash-flow Unknowns are resolved, eight remain valid, and one insurance Unknown is suppressed as not applicable. Runtime quality and final language pass for the run-28 before/after pair and run-29 negative control.

## Runtime Boundary

Phase 9.0C is archive-only. Its service is imported by tests and the evidence generator, not production packet, task, API, fallback, or delivery modules. User-visible cash-flow remains disabled. The next eligible step is a delivery-isolated natural runtime shadow canary, not Telegram exposure.
