# Structured Industry And Prose Numeric Validation

## Scope

- Base: `2afd66269d6c07d4f042355dde25a9b6bf94fa49`
- Knowledge: v3.0, SHA-256 `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` (unchanged)
- AI output schema: `1` -> `2`
- Analysis policy: `daily-review-v3` -> `daily-review-v3.1`
- Runtime mode: Shadow; no official assessment, warning, notification, or Telegram mutation
- DB migration: none
- Public Action: unchanged at `0.4.5`, 20/20 operationIds

## Structured Industry Routing

The previous router concatenated structured identity, business-model text, and thesis text before
taking the first keyword match. A thematic word could therefore replace the company's primary
industry framework.

The new order is structured industry, structured sector, structured business model, then structured
revenue sources. A verified subtype such as DRAM/NAND/HBM may refine semiconductor to memory. Thesis
text is excluded from primary selection and may add only a known thematic secondary framework.
Ambiguous structured input remains `general` with low confidence instead of forcing a specialist
framework. Segment dominance is used only when an explicit percentage identifies a unique leader.

| Fixture | Structured industry | Business model | Thesis keyword | Old primary risk | New primary | Secondary | Confidence |
|---|---|---|---|---|---|---|---|
| Semiconductor/cloud | Semiconductors | GPU and memory devices | cloud CAPEX | memory/cloud | semiconductor | hyperscaler CAPEX, memory segment | high |
| Insurance/recurring | Insurance | recurring premium revenue | digital distribution | SaaS | insurance | none | high |
| EPC/data center | Construction / EPC | engineering projects | data center | cloud | EPC/construction | hyperscaler CAPEX | high |
| Bank/platform | Banking | digital platform | platform engagement | cloud | bank | none | high |
| Holding/subsidiary | Holding company | semiconductor subsidiaries | portfolio discount | holding/semiconductor ambiguity | holding company | semiconductor exposure | high |
| Biotech/royalty | Biotech | recurring royalty income | royalty growth | SaaS | biotech | none | high |
| Memory subtype | Semiconductors | DRAM and NAND memory | cloud demand | broad semiconductor | memory | none | high |
| Unknown | absent | absent | generic cloud wording | cloud | general | none unless a known thematic route matches | low |

High-confidence primary frameworks are mandatory in `frameworks_used`; a missing primary or a
framework outside the routed allowlist is rejected. Common frameworks such as Market Expectations,
Earnings Quality, Macro Transmission, and Risk/Kill Condition remain available. Low-confidence input
does not force an industry-specific framework.

## Numeric Provenance

Each numeric registry entry now includes `semantic_type` and deterministic
`approved_display_variants`. Every AI numeric claim must provide:

- exact `fact_id` and `field_path`
- raw backend `value` and `unit`
- exact `semantic_type`
- exact prose `text_ref`
- a labeled `usage` substring that appears in that prose field

The validator scans market and stock prose fields independently. A claim contributes coverage only
after fact, field, value, unit, semantic, display, and text-location checks all pass. Dates, quarter
labels, and narrowly defined structural counts are excluded; financial numbers are not.

| Case | Result |
|---|---|
| Operating margin `11.3%`, exact fact/field/text | pass |
| Summary uses revenue growth `100%`; price `100` claim points to holder view | reject: uncovered summary occurrence |
| Same numeric value but price claim labeled as revenue growth | reject: semantic mismatch |
| KRW `319000000000` displayed as contract amount `3,190억원` | pass via existing compact formatter |
| Share ratio `0.1095%` displayed as about `0.11%` | pass via approved rounding |
| Share ratio `0.1095%` displayed as about `0.2%` | reject |
| Signed market changes `-3.17%` and `+0.67%` | pass with exact market prose claims |
| Existing PER `20x` plus invented margin `10%` | PER passes; invented derived number is rejected |

Modeled-versus-consensus wording and historical comparability checks remain separate hard guards.
An unavailable historical percentile never enters the numeric registry and cannot be cited.

## Real Monitored-Stock Smoke

The operational database currently has 21 monitored companies. Their `Company.industry`, `sector`,
`business_units`, and `revenue_sources` fields are all empty. All 21 therefore route to
`primary=general`, `secondary=[]`, `source=unclassified`, `confidence=low`. This is the intended safe
result: thesis prose is not used to invent primary company identity. Structured company-profile
population is an input-quality follow-up, not a ticker-specific router exception.

## Validation

- Baseline: `479 passed`, one pre-existing Starlette/httpx deprecation warning
- Focused AI Review suite: `32 passed`
- Full pytest after changes: `489 passed`, same warning
- Ruff: passed
- `git diff --check`: passed
- Knowledge v3 canonical/runtime checksum: unchanged and covered by tests
- Skill/output schema validation: passed in focused and full suites
- GitHub Actions: pending at report creation

## Remaining Gaps

- Operational company classification fields need a generic, verified population workflow before
  monitored-stock reviews can routinely use high-confidence specialized primary frameworks.
- Production Assist remains disabled. New `daily-review-v3.1` Shadow results require 5-10 trading
  days of review before any messaging decision.
