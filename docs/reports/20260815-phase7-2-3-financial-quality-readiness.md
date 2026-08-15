# Phase 7.2.3 Financial Quality Taint Readiness

## Repository State

- Repository: `sskim-ai/thesis-monitor`
- Experimental branch: `codex/phase-7-2-relational-reasoning`
- Required base: `27e5fa59634abfcaf7a257b030c465300182273b`
- Implementation commit: `015d6e93bea4204a7ec39b53c357a108aa129c70`
- Production main and operating checkout: `7d9f59fa1b5bc6034ea5cc9620482b39e4a96f07` (unchanged)
- Experimental policy: `daily-review-v3.10`
- Production policy: `daily-review-v3.9` (unchanged)
- Actual Pilot: KR `1/5`, US `1/5`
- Production Assist: disabled

This work is isolated experimental evidence. It has not been merged, deployed, scheduled, or sent to Telegram.

## Root Cause Confirmation

The 2026-06-30 SK hynix preliminary snapshot came from OpenDART and carried:

- `net_income_exceeds_revenue`
- `unusually_high_or_low_operating_margin`
- aggregate `preliminary_profitability_outlier`

The previous packet recorded the warning but still registered the affected earnings and earnings-derived valuation rows as `prose_allowed=true`. The binder and validator therefore did their jobs against an unsafe canonical eligibility decision. The root cause is `PACKET / CANONICALIZATION`, with `DATA QUALITY / NUMERIC_PROVENANCE / CALCULATION LINEAGE` as secondary layers. It is not an AI wording or renderer defect.

## Implementation

`financial-quality-taint-v1` assigns field-level quality, reason codes, source identity, dependency fields, prose eligibility, and a denial reason. Critical direct earnings fields taint TTM EPS, trailing PER, modeled forward EPS/fPER, and earnings-based historical PE state when they share the affected denominator. Independent book-value facts stay available.

Raw values remain auditable, while denied registry entries have no canonical display or approved display variants. Denied placeholders fail binding; raw numeric prose and qualitative citation of the denied earnings fact fail validation. A separate nonnumeric quality fact supports a specific Unknown. The deterministic fallback applies the same sanitized financial view before rendering.

## SK Hynix Before And After

Before, seven unsafe numeric claims appeared in the preview: revenue, operating margin, revenue YoY, operating-income YoY, trailing PER, modeled fPER, and a business conclusion derived from them.

After:

- 13 direct or derived registry rows are denied.
- Revenue, operating income, margin, QoQ/YoY, TTM EPS, trailing PER, modeled forward EPS/fPER, and current historical PE position are unavailable to prose.
- Current price, OHLCV structure, dynamic resistance, 1/5/20-day supply, current PBR, modeled fPBR, and historical PB percentile remain available.
- The corrected message explains the exact financial-quality hold and the next official facts required to update it.
- Previously rendered denied usage leakage: `0`.

The full message is in the [corrected KR preview](20260814-kr-v310-financial-quality-corrected-preview.md).

## KR Retrospective

- Session/run: `2026-08-14`, run `17`, `after_hours/final`
- Source DB backup SHA-256: `23451ab3ac99b08b203c6dd736f31aac1ced1f1603be2a387d2ce2a0d22018a1`
- Previous packet: `2026-08-14-kr-run-17-6c707522601d`
- Corrected packet: `2026-08-14-kr-run-17-cbfc8bd24224`
- Corrected packet file SHA-256: `6ea2e2e9c9b562fafe6ee518fd4734271bd74263804c7c5398c3a5c4df211e70`
- Active/packet/output/rendered stocks: `7/7/7/7`
- Tickers: `000660`, `003690`, `005490`, `005930`, `010120`, `012450`, `086280`
- Logical messages: market `1` + stocks `7`
- Automatic bindings: `141`; manual `0`
- Formatter errors/unresolved placeholders: `0/0`
- Validator: `PASS`, errors `0`
- Observer/holder distinct: `7/7`
- Substantive sentence repetition across 3+ stocks: `0`
- Denied numeric leakage: `0`

The prior SK message used seven tainted claims. The corrected message uses three independent book-value fields across five occurrences. All price and six 1/5/20-day supply claims remain bound.

## KR Cross-Section Sanity

All seven stocks were checked for period scope, unit scale, revenue/profit relationships, margin arithmetic, QoQ/YoY periods, preliminary/full-statement selection, EPS/share basis, price basis, valuation lineage, and eligibility.

| Ticker | Source | Period handling | Critical denial |
| --- | --- | --- | --- |
| 000660 | OpenDART preliminary Q2 | reported single quarter | Yes, 13 registry rows |
| 003690 | OpenDART full Q1 | reported single quarter | No |
| 005490 | OpenDART full Q2 | half-year cumulative less prior cumulative | No |
| 005930 | OpenDART full Q1 | reported single quarter | No |
| 010120 | OpenDART preliminary Q2 | reported single quarter | No |
| 012450 | OpenDART preliminary Q2 | reported single quarter | No |
| 086280 | OpenDART preliminary Q2 | reported single quarter | No |

Samsung Electronics was not treated as an assumed error. Its revenue, operating income, net income, and reported margin are internally consistent; the retained prior-year Q1 row independently reproduces both reported YoY rates. There is no matching critical quality flag.

Some reported YoY rates for other issuers could not be independently reconstructed from a prior-year row retained in this backup. No contradiction was found, but the missing comparison row is a lineage-audit limitation rather than proof of correctness.

## US Revalidation

The existing corrected output for `2026-08-15-us-run-18-dca26c59bb82` was replayed against a packet built from the same read-only snapshot with the new quality eligibility.

- Market/stocks: `1/13`
- Automatic bindings: `168`; manual `0`
- Binder errors: `0`
- Validator: `PASS`, errors `0`
- Newly denied financial rows across 13 stocks: `0`
- Existing/revalidated Telegram payload SHA-256: `7498f859abd69ad2adff1ae5d8242e0e7b23fa96b65417b3dc0879f4ccf4e7c5`
- Payload byte diff: none
- TSM: security price `USD`, financial statements `TWD`
- TSLA/WRD unsafe monetary amounts remain absent

## Deterministic Fallback

Failure-injection tests confirm that a critical financial outlier removes affected earnings and earnings-based valuation from fallback prose while retaining price, chart, supply, and independent book-value facts. The fallback gives a specific validation hold. Existing persisted-payload retry and single-delivery tests remain green.

## Isolation

- Telegram sends: `0`
- Operating DB/archive/assessment writes: `0/0/0`
- Pilot mutations: `0`
- Scheduled Task changes: `0`
- Main or operating checkout changes: `0`
- Production Assist changes: `0`

The experiment used a SQLite-consistent copy in `/tmp`; packet generation and validation did not open the operating database for writes.

## Contracts

- DB migration: none
- Public Action: `0.4.5`; operationId `20/20` unique
- Output schema: `4`
- OHLCV / Pilot / Renderer: `v2 / v3 / v3`
- Investment Knowledge v3 SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge v1 SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

## Validation

- Focused financial-quality and packet tests: PASS
- Full pytest: `714 passed`
- Ruff: PASS
- `git diff --check`: PASS
- Validation artifact commit: `d01ac031f649531f93bc439d34a6572c24a3ccba`
- GitHub Actions: Test and Lint PASS ([run 31877893058](https://github.com/sskim-ai/thesis-monitor/actions/runs/31877893058))

## Artifacts

- [Architecture contract](../architecture/FINANCIAL_QUALITY_TAINT_PROPAGATION.md)
- [KR corrected full preview](20260814-kr-v310-financial-quality-corrected-preview.md)
- [KR eligibility matrix](20260814-kr-financial-eligibility-matrix.json)
- [KR cross-section sanity audit](20260814-kr-financial-cross-section-sanity-audit.json)
- [KR numeric binding](20260814-kr-v310-financial-quality-binding.json)
- [KR validator result](20260814-kr-v310-financial-quality-validation.json)
- [KR quality audit](20260814-kr-v310-financial-quality-audit.json)
- [US revalidation](20260815-us-v310-financial-quality-revalidation.json)

## Remaining Gaps

- The corrected Preview and lineage audit still require human review before any main merge or deployment decision.
- The next natural live v3.10 session is not authorized; production remains v3.9.
- Prior-year comparison rows are unavailable in this backup for some reported YoY facts, so those rates are not independently reconstructed in this experiment.
