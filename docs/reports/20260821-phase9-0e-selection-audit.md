# Phase 9.0E Selection Audit

## Replay Identity

- Source packet: `2026-08-21-us-run-30-5a3b7c1c4390`
- Immutable archive rewrites: `0`
- Mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- US/foreign subjects: `13`
- Selected: `9`
- Suppressed: `4`

## Result

| Ticker | Result | Reason | Primary period | Primary FCF Fact |
|---|---|---|---|---|
| CORZ | SELECTED | existing cash-flow driver | 2026-06-30 YTD | `cashflow:1b8f3742f33dd3b66f8f7673` |
| CRCL | SELECTED | existing cash-flow driver | 2026-06-30 YTD | `cashflow:402041c63553616360d17391` |
| GOOGL | SELECTED | existing cash-flow driver | 2026-06-30 YTD | `cashflow:ddb47708bf7d36a4c0b0c7d2` |
| HUT | SUPPRESSED | OCF-only; initial user-visible scope requires full FCF | - | - |
| IBM | SELECTED | existing cash-flow driver | 2026-06-30 YTD | `cashflow:a158304539a9269c66f6d2cb` |
| MU | SELECTED | existing cash-flow driver | 2026-05-28 YTD | `cashflow:96e9c3b873f3678d4dec0ff3` |
| RXRX | SELECTED | existing cash-flow driver | 2026-06-30 YTD | `cashflow:498c289d4304c0822d861ec3` |
| SKHY | SUPPRESSED | canonical cash-flow Fact unavailable | - | - |
| SNDK | SELECTED | existing cash-flow Unknown resolved | 2026-07-03 FY | `cashflow:1b8db0b46c63ae9369231151` |
| TSLA | SELECTED | existing cash-flow driver after baseline consistency | 2026-06-30 YTD | `cashflow:68666c261434dab50ab88a8d` |
| TSM | SUPPRESSED | newer provisional period not cash-flow aligned | - | - |
| WRD | SUPPRESSED | newer provisional period not cash-flow aligned | - | - |
| WULF | SELECTED | existing cash-flow driver | 2026-06-30 YTD | `cashflow:6fd003ea029e4d7b03f681f3` |

Suppression counts are OCF-only `1`, canonical blocked `1`, and formal-lagging-provisional `2`.
No stale case appears in this packet; stale fixtures fail closed in tests.

## Negative Controls

- Run-29 KR: `7/7` not selected. Six non-financial subjects are outside initial market/source
  scope; Korean Re is `NOT_APPLICABLE`.
- Feature OFF: `13/13` not selected and user-visible cash-flow blocks `0`.
- Insurance generic enterprise FCF: not applicable.
- No ticker/date/value allowlist is used; classifications are contract results.

## Value Add

Human audit classifies the 13 US/foreign subjects as material improvement `5`, minor improvement
`4`, no meaningful change `4`, and degraded `0`. Selected fallback messages add an average `114.33`
characters on first exposure. Delta-first evidence signatures suppress unchanged later exposure.

