# KR Price Structure Daily History

Contract: `kr-price-structure-daily-history-v1`.

## Canonical Path

```text
monitored KR ticker
-> OhlcvClient
-> local /ohlcv official/free provider interface
-> completed-bar normalization
-> ohlcv-long-history-contract-v1
-> Price Structure v3
```

Price Structure asks for daily 1200, weekly 600, and monthly 300 bars. The provider interface
accepts at most 1000 rows per request. A provider-bound request is therefore capped at 1000 while
the canonical daily `requested_count` remains 1200. A 1000-row daily result is explicit `PARTIAL`
with `provider_limit`; it is not a short listing and is never represented as full 1200 coverage.

The provider limit is passed to the long-history normalizer. Missing rows are not padded, daily
history is not reconstructed from weekly/monthly data, and no unsupported provider fallback is
introduced. A current incomplete daily bar may provide provisional context but cannot confirm a
pivot or enter completed-count coverage.

## Eligibility

A daily failure does not erase safe weekly/monthly structure. `ELIGIBLE_SR_ONLY` remains possible
when a completed higher-timeframe source and a user-visible eligible zone exist. If all timeframe
coverage is failed, the KR rollout decision is `BLOCKED`. Coverage status and proximity semantics
are independent gates.

