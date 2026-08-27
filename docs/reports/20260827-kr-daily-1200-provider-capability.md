# KR Daily 1200 Provider Capability

## Decision

`DAILY_1200_PROVIDER_CAPABILITY = PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW`

This decision applies to the supported official `/ohlcv` consumption contract used by
thesis-monitor. It does not claim that the upstream Kiwoom chart API lacks native continuation;
the provider implementation uses `cont-yn` and `next-key` internally. Those continuation tokens
are not exposed to thesis-monitor, however, and the official endpoint rejects `count > 1000`.

## Contract Evidence

- `/ohlcv` accepts `symbol`, `market`, `periods`, `count`, indicator flags, `adjusted`, and investor
  flow selection.
- OpenAPI and `app/api/ohlcv.py` in the provider service set `count` to `1..1000`.
- No cursor, continuation token, offset, before date, start date, or end date is exposed.
- `count=1200` returns HTTP 422 with `less_than_equal` and maximum 1000.
- Unknown `end_date` is not consumed by the endpoint and does not move the returned window.

## Cache Audit

`ohlcv-1200-backfill-cache-v1` supplies identity, merge, dedupe, chronology, and gap-validation
types. It has no runtime persistence or source-fetch implementation and is not called by the
production OHLCV client. `20260826-v3-daily-1200-backfill.json` is an immutable audit archive with
a fixed cutoff, not a fresh production cache. Loading that report into runtime would create a
parallel stale truth source and is not allowed.

Therefore neither `EXACT_1200_SUPPORTED_BY_PAGINATION`,
`EXACT_1200_SUPPORTED_BY_DATE_WINDOW`, nor
`EXACT_1200_SUPPORTED_BY_EXISTING_CACHE_LAYER` is available through the current supported
thesis-monitor provider contract.

## Provider Policy

- Existing official/free provider retained.
- New provider: `0`.
- Paid provider/API: `0`.
- Synthetic history: `0`.
