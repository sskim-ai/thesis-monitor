# 2026-08-31 KR V2 Market Data Collection

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

- Contract: `structured-market-context-v1` / `market-cross-section-v1`
- Provider: `KIWOOM_REST`
- Publication state: `AVAILABLE_CURRENT`
- Retrieved: `2026-08-31T16:50:06.417917+09:00`
- Coverage: `full`, freshness `fresh`, raw 2766, eligible 2644
- Source payload SHA256: `a2978805678688df94c58225d4103d497225a46ff9281f442580974f891a79fd`

## Indices

| Index | Close | Return % |
| --- | --- | --- |
| KOSPI | 6820.02 | 0.46 |
| KOSDAQ | 834.29 | -0.49 |

## Breadth

| Scope | Listed | Advance | Decline | Unchanged | Advance % |
| --- | --- | --- | --- | --- | --- |
| KOSPI | 943 | 366 | 489 | 54 | 42.81 |
| KOSDAQ | 1823 | 741 | 889 | 105 | 45.46 |

## Market flows

| Market | Actor | Net buy | Basis |
| --- | --- | --- | --- |
| KOSPI | foreign | -4,405억원 | KRX_NXT_INTEGRATED |
| KOSPI | institution | -8,420억원 | KRX_NXT_INTEGRATED |
| KOSPI | retail | -2,613억원 | KRX_NXT_INTEGRATED |
| KOSDAQ | foreign | -897억원 | KRX_NXT_INTEGRATED |
| KOSDAQ | institution | -2,068억원 | KRX_NXT_INTEGRATED |
| KOSDAQ | retail | 2,937억원 | KRX_NXT_INTEGRATED |

## Sector/size summary used by the exact market message

- KOSPI size: large +0.55%, mid -0.58%, small -0.18%.
- KOSDAQ size: 100 -0.77%, MID300 -0.47%, SMALL +0.23%.
- KOSPI leaders: electrical/electronics +1.22%, chemicals +1.09%, manufacturing +0.77%.
- KOSPI laggards: construction -3.85%, machinery/equipment -3.56%, metals -3.39%.
- KOSDAQ leaders: non-metal +2.31%, paper/wood +1.38%, electrical/electronics +0.84%.

Concentration was fail-closed for both KOSPI and KOSDAQ due unresolved basis/taxonomy; it was not fabricated or rendered as a confirmed fact. `KR_MARKET_DATA_COLLECTION = PASS`.

## Stock-monitor provider telemetry

| Provider | Endpoint | Status | Count | First UTC | Last UTC |
| --- | --- | --- | --- | --- | --- |
| alpha_vantage | fetch_events | skipped_not_applicable | 8 | 2026-08-31 07:05:32.637290 | 2026-08-31 07:06:27.867091 |
| company_ir | fetch_events | skipped_not_configured | 8 | 2026-08-31 07:05:32.638142 | 2026-08-31 07:06:27.867780 |
| google_news_rss | fetch_events | success | 8 | 2026-08-31 07:05:31.478260 | 2026-08-31 07:06:27.088721 |
| naver_news | fetch_events | success | 8 | 2026-08-31 07:05:32.369785 | 2026-08-31 07:06:27.563673 |
| ohlcv_analyst | ohlcv_daily | success | 8 | 2026-08-31 07:05:32.648656 | 2026-08-31 07:06:27.878627 |
| ohlcv_analyst | ohlcv_monthly | success | 8 | 2026-08-31 07:05:35.268354 | 2026-08-31 07:06:30.226941 |
| ohlcv_analyst | ohlcv_weekly | success | 8 | 2026-08-31 07:05:33.986937 | 2026-08-31 07:06:28.980798 |
| ohlcv_analyst | ohlcv_weekly_unadjusted_valuation | success | 8 | 2026-08-31 07:05:36.260212 | 2026-08-31 07:06:31.263072 |
| opendart | fetch_events | success | 8 | 2026-08-31 07:05:32.522831 | 2026-08-31 07:06:27.699765 |
| sec_edgar | fetch_events | skipped_not_applicable | 8 | 2026-08-31 07:05:32.635942 | 2026-08-31 07:06:27.865878 |
