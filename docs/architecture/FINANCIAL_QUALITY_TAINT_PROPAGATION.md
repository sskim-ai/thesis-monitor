# Financial Quality Taint Propagation

## Status

- Contract: `financial-quality-taint-v1`
- Experimental policy: `daily-review-v3.10`
- Output schema: `4` (unchanged)
- Production status: experimental branch only; not merged or deployed

## Problem

Financial validation could identify a critical profitability outlier while the AI packet still exposed the affected revenue, profit, margin, EPS, and valuation numbers as normal canonical facts. The binder and validator then correctly approved provenance for a fact that should not have been eligible for user prose.

The failure boundary was `PACKET / CANONICALIZATION`, not AI wording, rendering, or provenance matching.

## Decision

Every financial field used by the AI packet receives a deterministic quality record:

- `verified_usable`: validated and eligible for prose.
- `caution_usable`: eligible with an explicit quality limitation.
- `denied`: retained for audit but unavailable to prose, binding, and interpretation.
- `unknown`: eligibility cannot be established.

Each record carries source period/type, reason codes, dependency fields, prose eligibility, denial reason, and decision version. A separate nonnumeric `financial_quality:<period>` fact lets the AI explain a hold without citing a denied earnings fact.

## Critical Reasons

The contract denies affected fields for hard financial errors, financial-statement basis warnings, period-mapping failures, revenue/profit relationship failures, and critical operating/net-margin outliers. `preliminary_profitability_outlier` represents the same critical preliminary branch.

An official source confirms provenance, not economic sanity. It does not override a critical outlier.

## Lineage

Taint is field-local and dependency-aware.

Direct affected fields include revenue, operating income, operating margin, and their QoQ/YoY changes. When the latest preliminary period participates in their denominator chain, taint also reaches TTM EPS, trailing PER, modeled forward EPS/fPER, and the current earnings-based historical percentile or valuation state.

Independent facts stay available when their own lineage is clean. Examples include current price, OHLCV structure, support/resistance, RR, KR investor flow, and book-value metrics. Independent provider consensus also remains available when it does not depend on the denied input.

## Packet And Registry

Raw values remain in the immutable financial snapshot and packet for audit. Their registry rows have:

```json
{
  "financial_quality_state": "denied",
  "prose_allowed": false,
  "canonical_display_value": null,
  "approved_display_variants": [],
  "denial_reason": "..."
}
```

The binder rejects a placeholder referencing such a row. The validator also rejects raw numeric prose and qualitative interpretation that cites an entirely denied financial fact. A number-free, specific Unknown may cite the separate financial-quality fact.

## Fallback

The deterministic fallback applies the same eligibility boundary before rendering. It suppresses denied earnings and PE-dependent values and interpretations while preserving independent price, chart, supply, and book-value facts. Delivery retry continues to reuse the same persisted payload and does not recollect or recalculate data.

## Why

Blocking only the final number would leave derived valuation and narrative conclusions alive. Taint propagation closes the dependency chain at the deterministic source and gives AI, binder, validator, and fallback one consistent boundary.

## Rejected Alternatives

- Prompt-only avoidance: the unsafe fact would remain canonical and reusable.
- Renderer deletion: semantic repair after validation breaks provenance and delivery identity.
- Validator relaxation or exception: it would bless the wrong packet contract.
- Ticker-specific blocklist: it would not protect another issuer with the same data-quality failure.
- Replacing the value with an estimate or conversion: Unknown must not become a guessed fact.
- Removing all valuation: it would discard independent clean book-value or consensus facts.

## Safety Constraints

- `Fact != Interpretation != Unknown`
- `Security Price Currency != Issuer Financial Currency`
- `Chart INVALID != Thesis INVALID`
- Stored raw values are not user-visible eligibility.
- No ticker hard-codes, manual overrides, exchange-rate inference, or ADR conversion.
- No DB migration, Public Action change, output-schema change, Knowledge change, or renderer semantic rewrite.

## Validation Evidence

The Phase 7.2.3 isolated retrospective uses the read-only 2026-08-14 KR database backup. SK hynix has three critical reasons and 13 denied numeric registry entries; the corrected preview has no denied-number leakage, automatic binding only, and zero validator errors. All six other KR stocks retain clean eligible facts. The corrected US payload is byte-identical because all 13 US stocks have zero newly denied registry entries.

See:

- [KR corrected preview](../reports/20260814-kr-v310-financial-quality-corrected-preview.md)
- [KR eligibility matrix](../reports/20260814-kr-financial-eligibility-matrix.json)
- [KR cross-section audit](../reports/20260814-kr-financial-cross-section-sanity-audit.json)
- [US revalidation](../reports/20260815-us-v310-financial-quality-revalidation.json)
- [Phase 7.2.3 readiness](../reports/20260815-phase7-2-3-financial-quality-readiness.md)
