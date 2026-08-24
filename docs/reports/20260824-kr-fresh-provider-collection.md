# KR Fresh Provider Collection

## Scope

- Cutoff: `2026-08-24T19:34:19+09:00`
- Collection pass: one normal KR analysis pass on the isolated DB/data copy
- Active KR universe: `000660`, `003690`, `005490`, `005930`, `010120`, `012450`, `086280`
- Analysis: 7/7 success; failure 0
- New paid source or ad hoc supplemental fetch: 0

## Calls

| Provider | Success | Failure | Skip | Classification |
|---|---:|---:|---:|---|
| Google News RSS | 7 | 0 | 0 | `FRESH_RECOLLECTED` |
| Naver News | 7 | 0 | 0 | `FRESH_RECOLLECTED` |
| OpenDART | 7 | 0 | 0 | `FRESH_RECOLLECTED` official filing query |
| OHLCV Analyst | 28 | 0 | 0 | `FRESH_RECOLLECTED` daily/weekly/monthly/valuation basis |
| SEC EDGAR | 0 | 0 | 7 | `UNAVAILABLE` / not applicable to KR subjects |
| Alpha Vantage | 0 | 0 | 7 | `UNAVAILABLE` / not applicable |
| Company IR | 0 | 0 | 7 | `UNAVAILABLE` / not configured |

Success 49, failure 0, skip 21, cache-hit 0. The calls were recorded at approximately
`19:38:13-19:38:52 KST`. Retrieval followed the fixed cutoff as the production path's staged
collection pass; price observations retained the cutoff and provider rows retained actual attempt
and completion timestamps.

The already-completed KR-close FX record was `REUSED_CANONICAL` with no supplemental refetch. The
morning macro briefing, working-capital lineage, and cash-flow lineage were also reused canonical
evidence. Run 36 was used only as `REUSED_IMMUTABLE_REFERENCE` in the behavior comparison.
