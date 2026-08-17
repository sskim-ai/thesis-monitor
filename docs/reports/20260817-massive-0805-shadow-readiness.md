# Massive 08:05 Shadow Readiness And Provider Semantics

## Status

`Massive 08:05 Readiness = NOT_YET_OBSERVED`.

The 2026-08-14 grouped session is complete, but its cached collection was made after 08:05 KST. It
is capability evidence, not an on-time normal-day shadow observation. Three to five normal US
sessions are still required before production timing eligibility can be decided.

## Live Sanity Check

On 2026-08-17, a sanitized live check returned HTTP 200 for both grouped daily and reference ticker
endpoints. The grouped response contained 12,424 rows for 2026-08-14. A one-row reference request
was paginated and successful. Neither response exposed `X-RateLimit-*` nor `Retry-After` headers.
Two additional one-row reference requests completed consecutively in 0.649 and 0.570 seconds with
HTTP 200. This demonstrates limited burst acceptance, not unlimited entitlement.

Massive's current Stocks Basic pricing states five API calls per minute. The provider therefore keeps
conservative 12-second pacing. The prior report's 14.24 seconds is summed HTTP response latency for
14 pages; it is not pagination wall time and does not contradict client-side pacing. Live 429 was not
intentionally provoked. Mock integration tests verify bounded retry and `Retry-After` handling.

Official references:

- [Massive Stocks pricing](https://massive.com/pricing?product=stocks)
- [Massive adjusted decimal volume](https://massive.com/knowledge-base/article/why-does-volume-return-as-a-decimal-value-from-the-aggregates-endpoint)
- [Massive split-adjustment semantics](https://massive.com/knowledge-base/article/is-massives-stock-data-adjusted-for-splits-or-dividends)

## Reference Cache Policy

Reference metadata is no longer refreshed in every 08:05 critical path. The provider reuses the
latest verified cache for at most one XNYS session. This permits Friday reference metadata on
Monday, including an intervening US holiday, while forcing refresh after the next exchange session.
The current and previous grouped session caches remain exact-date inputs.

Minimum intended 08:05 calls:

1. current grouped session;
2. previous grouped session only when its exact-date cache is absent;
3. reference refresh only when the one-trading-day cache is unavailable.

Every cache retains session/request date, adjusted flag where applicable, row count validation,
response hash, fetch time, and sanitized provider response metadata. Missing, duplicate, stale, or
wrong-session rows fail closed.

## Volume And Value Semantics

The grouped request uses `adjusted=true`. Massive documents that aggregate volume can become decimal
after split adjustment. The 2026-08-14 sample has decimal volumes and a total near
10,949,744,095.506, so it is canonicalized as `split_adjusted_aggregate_volume`, not “total shares
traded.” It stays audit-only in user-facing market intelligence.

`sum(close * adjusted volume)` is
`deterministic_close_times_adjusted_volume_estimate`. It is not official consolidated market
turnover and also remains audit-only. A user-visible liquidity semantic requires an official raw
or explicitly labeled comparable source.

## Shadow Telemetry Contract

`massive-0805-shadow-v1` records target session, observation time, grouped row count, reference cache
age, breadth counts, previous-session completeness, calculation finish time, provider latency,
errors, and source hashes. Readiness values are `READY_AT_0805`, `LATE_BUT_BEFORE_0815`,
`LATE_AFTER_0815`, `INCOMPLETE`, or `PROVIDER_ERROR`.

The recorder is shadow-only. It does not send Telegram, mutate Pilot state, or register a production
provider or Scheduled Task.
