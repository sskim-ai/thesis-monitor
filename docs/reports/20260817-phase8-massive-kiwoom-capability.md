# Phase 8 Massive / Kiwoom Capability Report

## Decision Summary

| Capability | Status | Decision |
|---|---|---|
| Massive full US daily cross-section | SUPPORTED | Implemented as shadow provider |
| Massive reference security metadata | SUPPORTED | Required for common-equity universe filtering |
| Massive 08:05 KST completeness | PARTIAL | Weekday shadow timing still required |
| Kiwoom KR index primitives | PARTIAL | Official OCX/FID documentation; no configured gateway proof |
| Kiwoom direct market breadth | PARTIAL | `업종등락` FIDs documented; registration/universe unverified |
| Kiwoom all-stock multi-row | PARTIAL | `CommKwRqData` documented; production row/page bound unverified |
| Kiwoom market investor flow | NOT_CONFIGURED | No gateway/KOA aggregate TR evidence |
| KRX primary | PENDING_PROVIDER_APPROVAL | Approval/activation not yet verified |

Neither provider is wired into production Telegram or Scheduled Tasks. Massive and Kiwoom roles are
shadow and bridge-shadow respectively.

## Current Provider Inventory

| Provider | Market | Purpose | Endpoint/TR | Config | Raw / canonical | Freshness, cache, retry | Production role |
|---|---|---|---|---|---|---|---|
| KRX Open API | KR | Night futures | official derivatives endpoint | `KRX_OPEN_API_KEY` | JSON / night-futures Fact | session gate, bounded retry | active partial macro context |
| Kiwoom probe | KR | Night-futures capability | `/v1/night-futures/capabilities` | gateway fixture/URL | strict gateway schema / none | probe only | disabled |
| Massive | US | Full daily stocks cross-section | grouped daily + reference tickers | `MASSIVE_API_KEY` | cached JSON / `MarketCrossSection` | atomic date cache, 5/min | new shadow |
| OpenDART | KR | filings, earnings, capital actions | OpenDART APIs | `OPENDART_API_KEY` | provider rows / financial Facts | provider caches, bounded retry | active |
| Federal Reserve | US | central-bank events | official calendar | none | event rows / macro event | scheduled refresh | active |
| FRED | US | rates, credit, USD, VIX/oil series | FRED series | `FRED_API_KEY` | observations / macro Facts | provider schedule/cache | active when configured |
| EIA | US | energy | EIA API | `EIA_API_KEY` | observations / macro Facts | provider schedule/cache | optional |
| ECOS | KR | Korean macro/FX | ECOS API | `ECOS_API_KEY` | observations / macro Facts | provider schedule/cache | optional |
| OHLCV Analyst | US/KR | daily price, ETF proxies, chart structure | local `/ohlcv` | local API key | bars / chart and macro Facts | local service cache/retry | active |
| Finnhub | US | earnings | provider API | `FINNHUB_API_KEY` | provider response / earnings Fact | provider timeout/cache | optional |
| Alpha Vantage | US/FX | optional fundamentals/FX | provider API | `ALPHA_VANTAGE_API_KEY` | cached provider response / optional Fact | request budget + cache | optional |
| FMP | US | optional fundamentals | provider API | `FMP_API_KEY` | cached response / optional Fact | provider timeout/cache | optional |
| Sharadar | US | optional fundamentals | provider API | `SHARADAR_API_KEY` | cached response / optional Fact | provider timeout/cache | optional |

## Massive Live Probe

The free key successfully called grouped daily stocks for 2026-08-14 and 2026-08-13. The current
session returned 12,424 rows in 1.572 seconds with adjusted bars, zero duplicate tickers, zero missing
close, and zero missing volume. Fields were ticker, OHLC, volume, VWAP, transaction count, and bar
timestamp.

The active US reference universe required 14 pages and returned 13,110 rows. The provider rate limiter
kept pagination at the documented five requests/minute. A 2024-08-13 request, beyond the free history
entitlement on the probe date, returned HTTP 403 `NOT_AUTHORIZED`, confirming the two-year limit in a
live response.

After reference filtering and same-ticker previous adjusted-close checks:

| Metric | 2026-08-14 |
|---|---:|
| Eligible securities | 5,461 |
| Advance / decline / unchanged | 2,772 / 2,502 / 187 |
| Advance ratio | 50.760% |
| A/D ratio | 1.108x |
| Median security return | +0.042% |
| Equal-weight security return | +0.229% |
| Total volume | 10,949,744,095.506 |
| Close-times-volume value | $614,178,243,240.38 |
| SPY proxy return | -0.198% |
| SPY-minus-equal-weight gap | -0.427%p |

The value metric is not an official consolidated tape turnover amount; it is deterministic
`close * volume`. The SPY gap is a broad cap-weight proxy comparison, not whole-market cap-weight
breadth. The detailed sanitized result is in
[the capability JSON](20260817-phase8-massive-capability.json).

The Friday data was available during the Monday probe. Exact 08:05 KST prior-session completeness was
not observed on a normal weekday, so that operational readiness remains PARTIAL pending 3-5 scheduled
shadow captures.

## Kiwoom Capability Matrix

| Metric | Status | TR/function evidence | Notes |
|---|---|---|---|
| KOSPI | PARTIAL | `업종지수` real-time FIDs | index identity/registration not gateway-verified |
| KOSDAQ | PARTIAL | `업종지수` real-time FIDs | same limitation |
| KOSPI200 | PARTIAL | documented index/futures primitives | snapshot contract not gateway-verified |
| KOSDAQ150 | NOT_CONFIGURED | no gateway evidence | do not infer support |
| Market breadth | PARTIAL | `업종등락` FIDs 251-257 | denominator/universe and registration unverified |
| All-stock multi-row | PARTIAL | `CommKwRqData` | code-list request; safe row/page bound unverified |
| Sector breadth | PARTIAL | industry index/change primitives | taxonomy is Kiwoom-specific |
| Foreign market flow | NOT_CONFIGURED | no verified aggregate TR | unavailable, not zero |
| Institution market flow | NOT_CONFIGURED | no verified aggregate TR | unavailable, not zero |
| Retail market flow | NOT_CONFIGURED | no verified aggregate TR | unavailable, not zero |

No Windows gateway is currently configured, so there was no live Kiwoom call. The bridge provider
will reject canonical collection unless capability evidence is explicitly SUPPORTED, KOA-verified,
efficient, and denominator-safe. Account or credential fields are rejected recursively.

## Rate-Limit Analysis

Per-ticker breadth would require roughly 2,000-3,000 requests and exceed the stated 1,000/hour bound,
so it is rejected. A future direct summary is expected to require 1-4 requests/session. A bounded
multi-row plan may use at most 20 pages in the initial gate: 20 requests/session, under 5/second,
100/minute, and 1,000/hour when paced. Actual pages/request must be measured in KOA Studio before
promotion from PARTIAL.

## KRX Future Mapping

| KRX primary metric | Kiwoom candidate | Reconciliation |
|---|---|---|
| KOSPI/KOSDAQ close and return | `업종지수` | exact identity, date, and official rounding |
| advance/decline/unchanged | `업종등락` or bounded rows | exact after universe exclusions |
| eligible count | filtered official list | compare ETF/preferred/REIT/SPAC/suspended/new listing rules |
| sector return/counts | Kiwoom industry taxonomy | preserve taxonomy; explicit mapping only |
| foreign/institution/retail amount | verified aggregate TR only | normalize units, otherwise unavailable |

At least five trading days are required before metric-level fallback can be considered.

## Gap Status

| Gap | Status |
|---|---|
| US breadth | CLOSED for capability/implementation; shadow timing remains |
| KR breadth | PARTIAL |
| KR market flow | OPEN |
| Sector participation | PARTIAL, price proxy only for US |
| KRX primary | PENDING_PROVIDER_APPROVAL |

## Safety And Mutation

- Provider/network calls: Massive capability only; Kiwoom 0.
- Telegram sends: 0.
- Operating DB, archive, assessment, and Pilot mutations: 0.
- Scheduled Task and operating checkout changes: 0.
- Production Assist remains OFF.
- No key or account information is stored in repository artifacts.
