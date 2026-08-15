# Financial Quality Taint Propagation

## Status

- Decision contract: `financial-quality-taint-v2`
- Experimental policy: `daily-review-v3.10`
- Output schema: `4` (unchanged)
- Production status: experimental branch only; not merged or deployed

## Problem

Financial validation can find a critical profitability outlier while the packet still contains the raw value for audit. User-visible eligibility must therefore be a separate deterministic decision. Phase 7.2.3 introduced this decision, but two gaps remained:

1. TTM taint used `ttm_contains_preliminary` as a proxy instead of checking the exact denominator periods. A critical full statement or an older critical quarter could remain in trailing EPS/PER.
2. A mixed aggregate valuation Fact could contain denied PER and allowed PBR. A number-free interpretation could cite the aggregate Fact and bypass field-level denial.

The failure boundary is `CALCULATION_LINEAGE / PACKET / NUMERIC_PROVENANCE / VALIDATION`, not AI style or rendering.

## Decision

Every financial or valuation field receives an independent lineage record:

- `verified_usable`: exact lineage and basis are verified.
- `caution_usable`: lineage is verified but the source or method requires an explicit limitation.
- `denied`: an actual dependency contains a critical quality failure.
- `unknown`: the dependency period, source, or security basis cannot be verified.

Only `verified_usable` and `caution_usable` are eligible for user prose. Each record stores source period/type/provider, dependency fields and periods, denominator period, reason codes, eligibility, denial reason, lineage verification status, and decision version.

## Trailing Lineage

TTM EPS and trailing PER use the exact `earnings_quarter_series` selected for the denominator. Taint is the intersection of critical source periods and those dependency periods.

- Critical preliminary period in TTM: deny TTM EPS and trailing PER.
- Critical full-statement period in TTM: deny the same fields.
- Older critical quarter in TTM: deny the same fields even when the latest quarter is clean.
- Critical direct period outside TTM: deny direct earnings only; retain trailing values only when the four-quarter lineage and per-share basis are independently verified.
- Unknown dependency set: remain `unknown`; never promote to verified.

`ttm_contains_preliminary` remains descriptive metadata and is not an eligibility gate.

Historical PE current value and percentile depend only on current trailing PER plus the historical distribution. Modeled or consensus forward status cannot taint clean historical trailing PE.

## Forward Lineage

Modeled forward EPS/fPER follows the exact modeled input periods, forecast method, denominator period, currency, and security basis. Any critical modeled input denies only the modeled-forward earnings family.

Independent provider consensus remains separate when source identity, estimate period, currency, security basis, consensus status, and independence contract are verified. Trailing taint does not automatically deny an independent consensus; unknown consensus basis remains `unknown`.

## Book Lineage

BVPS, current PBR, forward BVPS/fPBR, and historical PB use their own book-value denominator periods and basis metadata. The latest earnings period is never copied into a book field as a fallback.

A clean book denominator can remain eligible when earnings are tainted. A missing period, ADR/share-basis conflict, currency conflict, or unverified book lineage remains `unknown` or `denied` according to the existing valuation basis contract.

## Interpretation Fence

The aggregate `valuation:current` Fact remains available as the numeric registry source, but it is not eligible for interpretation when its fields have mixed eligibility. User interpretation must cite a lineage-homogeneous Fact:

- `valuation:trailing_earnings`
- `valuation:modeled_forward_earnings`
- `valuation:consensus_forward_earnings`
- `valuation:book`
- `valuation:modeled_forward_book`
- `valuation:consensus_forward_book`
- `valuation:historical_pe`
- `valuation:historical_pb`

These interpretation Facts do not duplicate numeric registry rows. A denied or unknown homogeneous Fact, or an ineligible mixed aggregate Fact, causes validator rejection even when the text contains no number. The boundary is Fact identity and lineage metadata, not a keyword blacklist.

A separate `financial_quality:<period>` Fact permits a specific number-free explanation such as holding earnings-multiple interpretation until the period and units are verified.

## Packet And Registry

Raw values remain in immutable snapshots for audit. Non-eligible registry rows have:

```json
{
  "financial_quality_state": "denied_or_unknown",
  "prose_allowed": false,
  "canonical_display_value": null,
  "approved_display_variants": []
}
```

The binder rejects their placeholders. The validator rejects raw-number workarounds and interpretation references to denied, unknown, or mixed-lineage Facts.

## Fallback Persistence

New valuation snapshots persist `financial_quality_source_metadata` inside the existing assessment JSON. This is an internal backward-compatible field and requires no database migration. It contains the exact TTM, modeled-forward, modeled-forward-book, direct-field, and book denominator records selected during valuation calculation.

The deterministic fallback rebuilds the same v2 quality state from this persisted metadata. It preserves safe price, chart, supply, consensus, and book facts while suppressing non-eligible earnings/PE values and conclusions. Delivery retry continues to reuse the same persisted payload without recollection, reanalysis, or rerendering.

For older assessments that predate persisted metadata, the AI packet builder reconstructs point-in-time lineage from FinancialSnapshot rows available by the assessment's calculation timestamp. If exact lineage cannot be reconstructed, the field remains `unknown`.

## Why

Eligibility must follow actual economic dependencies. Source type, value presence, or a broad aggregate warning is not a substitute for denominator lineage. Homogeneous interpretation Facts also make the validator a real safety boundary instead of relying on AI wording discipline.

## Rejected Alternatives

- Prompt-only avoidance: unsafe Facts would remain reusable.
- Renderer deletion or rewriting: semantic repair after validation breaks payload identity.
- Regex-only qualitative blocking: wording can change while the unsafe lineage remains.
- Ticker-specific blocklists: they do not protect another issuer with the same defect.
- Tainting all valuation: it removes independent book or consensus facts.
- Treating full statements as inherently safe: official provenance does not prove economic sanity.
- Copying the earnings period into book lineage: unknown is not a guessed source.

## Safety Constraints

- `Fact != Interpretation != Unknown`
- `Security Price Currency != Issuer Financial Currency`
- `Trailing != Modeled Forward != Consensus Forward != Book`
- `Chart INVALID != Thesis INVALID`
- Stored raw values are not user-visible eligibility.
- No ticker hard-codes, manual overrides, exchange-rate inference, or ADR conversion.
- No DB migration, Public Action change, output-schema change, Knowledge change, or renderer semantic rewrite.

## Validation Evidence

See:

- [Lineage dependency matrix](../reports/20260815-phase7-2-4-financial-lineage-dependency-matrix.json)
- [Qualitative validator matrix](../reports/20260815-phase7-2-4-qualitative-interpretation-validator-matrix.json)
- [Fallback matrix](../reports/20260815-phase7-2-4-fallback-validation.json)
- [KR corrected preview](../reports/20260814-kr-v310-lineage-exact-corrected-preview.md)
- [KR eligibility matrix](../reports/20260814-kr-financial-lineage-v2-eligibility-matrix.json)
- [US corrected preview](../reports/20260815-us-v310-lineage-exact-corrected-preview.md)
- [Phase 7.2.4 readiness](../reports/20260815-phase7-2-4-lineage-exact-readiness.md)
