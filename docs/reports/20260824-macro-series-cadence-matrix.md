# 2026-08-24 Macro Series Cadence Matrix

The latest observation dates below come from the immutable 2026-08-24 briefing. Cadence comes from
the repository provider registry because the old briefing serializer dropped `frequency`.

| Series | Provider | Contract cadence | Basis | Latest observation | Role in replay | Today signal | Important changes | Regime/reference |
|---|---|---|---|---|---|---:|---:|---:|
| SPY | ohlcv_analyst | daily | XNYS session | 2026-08-21 | PRIOR_MARKET_SESSION | no | prior-labeled | yes |
| QQQ | ohlcv_analyst | daily | XNYS session | 2026-08-21 | PRIOR_MARKET_SESSION | no | prior-labeled | yes |
| IWM | ohlcv_analyst | daily | XNYS session | 2026-08-21 | PRIOR_MARKET_SESSION | no | prior-labeled | yes |
| SOXX | ohlcv_analyst | daily | XNYS session | 2026-08-21 | PRIOR_MARKET_SESSION | no | prior-labeled | yes |
| DGS10 | FRED | daily | official release | 2026-08-20 | REFERENCE_LAGGING | no | no | yes |
| DFII10 | FRED | daily | official release | 2026-08-20 | REFERENCE_LAGGING | no | no | yes |
| T10YIE | FRED | daily | official release | 2026-08-21 | REFERENCE_LAGGING | no | no | yes |
| BAMLH0A0HYM2 | FRED | daily | official release | 2026-08-20 | REFERENCE_LAGGING | no | no | yes |
| DTWEXBGS | FRED | daily series, lagging publication | official release | 2026-08-14 | REFERENCE_LAGGING | no | no | yes |
| USDKRW | ECOS KeyStatistic | provider cycle field | collection-date surrogate | 2026-08-23 stored | REFERENCE_LAGGING | no | no | yes |
| DCOILWTICO | FRED | daily | official release | 2026-08-18 | REFERENCE_LAGGING | no | no | yes |
| VIXCLS | FRED | daily | official release | 2026-08-20 | REFERENCE_LAGGING | no | no | yes |
| KRX_KOSPI200_NIGHT_FUT | KRX | daily | dedicated night-session pair | 2026-08-21 | stale by existing gate | no | no | no |
| KRX_KOSDAQ150_NIGHT_FUT | KRX | daily | dedicated night-session pair | 2026-08-21 | stale by existing gate | no | no | no |

## Exact Retrieval Times

- SPY/QQQ/IWM/SOXX: 2026-08-21 23:05:26 UTC range.
- DGS10/DFII10/T10YIE/BAMLH0A0HYM2/VIXCLS: 2026-08-21 23:05:09 UTC range.
- DTWEXBGS: 2026-08-17 23:05:08 UTC.
- WTI: 2026-08-19 23:05:10 UTC.
- USD/KRW: 2026-08-23 23:05:09 UTC, but this is collection timing rather than a verified source
  occurrence date.
- Night futures: retrieved 2026-08-22 23:20:06 UTC and already marked `stale`.

No provider was called for this audit. Request/success/failure/cache-hit counts are all 0.
