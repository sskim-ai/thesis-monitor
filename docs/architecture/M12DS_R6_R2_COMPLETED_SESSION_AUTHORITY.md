# R6-R2 Completed-Session Authority Audit

Task: `M12DS-R6-R2-20260923`. Continuation base:
`196b3f82f2a17fdb882339deda99490b7e0dbb60`.

The original instruction is frozen at `aa2dc35381640e63181bc2ab259ae64c80fd7c37`.
Only instruction whitespace is normalized afterward. Raw responses and runtime
receipts remain outside Git. No production module or judgment policy is changed.

## Production Cutoff

Repository launchd definitions and installed definitions agree. Host timezone is
Asia/Seoul; the four Codex task times match the documented scheduled-task owner.
The four AI tasks are PAUSED, and the collection/fallback/delivery launchd jobs are
disabled. This audit identifies their configured timing, not a completed live run.

| Market | Source collection | AI primary / backup | Fallback |
| --- | --- | --- | --- |
| US | 08:05, then 08:10/15/20 gate attempts | 08:15 / 08:30 | 08:40 |
| KR | 16:05, 16:20, 16:50 | 16:15 / 16:55 | 17:10 |

At 2026-09-23 08:05 KST, US exchange-local time is September 22 19:05 EDT.
September 22 regular trading is complete but after-hours can still be active.
Neither the schedule nor wall-clock passage establishes the last quote as the
settled regular close. During standard time the same KST slot is 18:05 EST.

At September 23 16:05 KST, the KR target is the same-day completed regular session.
The noon diagnostic targeted September 22 and is not proof of a production defect.
The receipt uses the existing exchange-calendar dependency without weekday fallback.
Acquisition timestamps are actual response times; a later probe is not backdated
to 08:05 or 16:05.

## Inspected Routes

| Route | Configuration / owner | Completed regular-close conclusion |
| --- | --- | --- |
| OHLCV analyst `/ohlcv`, Kiwoom `usa06012` | Active primary; `app/macro/providers/market.py` | Latest `cur_prc` owns CURRENT_QUOTE, no propagated settled field/finality. Denied. |
| Local stock-screener Kiwoom daily chart | Same `usa06012` field mapping | Not an independent semantic owner. |
| Kiwoom `usa10100` stock information, `usa10099` list | Neighboring read-only identity helpers | No existing session-bound close contract in thesis-monitor; identity/list is not close finality. Not invoked. |
| Massive grouped daily | Implemented shadow-only market internals; no configured key | Not available. General daily OHLC description is not a verified production-cutoff receipt. |
| Alpha Vantage prices | Key present; general price policy lists it; concrete PriceProvider is a stub | No GLOBAL_QUOTE/daily OHLCV adapter or approved regular-close/session contract. A key is not an implemented route. |
| Finnhub | Key present; multiples/estimates role | No approved completed-close adapter. |
| FMP / Sharadar | Keys absent; fundamental / historical PIT roles | Not configured for this requirement. |
| Secondary OHLCV recovery registry | `approved_runtime_secondary_sources()` is empty | No implicit fallback. |

The bounded live probe requests only SPY and XLC via the existing OHLCV route.
Both return HTTP 200 and September 18/21/22 rows, but fail
`completed_session_and_previous_close_required`. XLC's prior 429/502 is not
reproduced in this probe. Neither source-authority failure is retryable. Current
probe raw SHA values are in the private report, not Git.

## KR Route Disposition

Normal scheduled execution is the instruction's post-close Case A, not Case B.
Existing `ka20001` current index + `ka20003` venue-sector snapshot + `ka20009`
date-owned index history are the candidate owners. Existing comparison is exact
numeric equality for level and return; no new tolerance is introduced.

The actual same-date post-close response must additionally prove exchange CLOSED,
collection after the owned close, unique composite identity and response-date
binding. A before-close snapshot is never relabeled. KOSPI/KOSDAQ ranking
taxonomies remain separate. No new KR probe, ranking, or
`kr-post-close-sector-session-v1` success receipt is fabricated after the US stop.

## Authorization Boundary

Terminal: `M12DS_R6_R2_US_SETTLED_CLOSE_ROUTE_REQUIRES_USER_AUTHORIZATION`.

Needed: an approved provider field/daily endpoint that owns settled regular close,
exact current/previous exchange dates and compatible adjustment basis, available
at the real US cutoff without next-session lookahead. Also required: full
SPY/QQQ/IWM and sector-universe coverage, including XLC.

Configured candidate, not activated: Alpha Vantage default EOD GLOBAL_QUOTE or
daily OHLCV. The official documentation describes default EOD updates, but that
alone is not proof of its exact publication clock, adjustment compatibility,
regular-session-only semantics, ETF coverage, or account entitlement at 08:05 KST.
A bounded documentation/schema/live qualification plus a typed adapter would need
separate approval before using that route here.

Unconfigured alternative, not activated: Massive Daily Ticker Summary separates
closing price and pre-/after-market fields. Configuration, authorization, cutoff
availability, and full universe coverage would still need proof. No subscription,
new credential, or external provider was added.

Official references:
- [Alpha Vantage documentation](https://www.alphavantage.co/documentation/#latestprice)
- [Massive stocks API overview](https://massive.com/docs/rest/stocks/overview)
- [Kiwoom REST guide](https://openapi.kiwoom.com/guide/apiguide)

## Deferred By Stop

- Macro latest-available informational display is authorized by R2 but not
  implemented here; R1's strict direction-evidence rejection remains unchanged.
- No newly sourced KR 8/8 message proof, night D/W/M proof, or 24-message capture.
- No Market/Core/A/B, scheduler change, DB write, Telegram send, merge, push, deploy.
- Prior R6/R1 results retain their original status and SHA values.
