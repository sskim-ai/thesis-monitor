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
the canonical daily `requested_count` remains 1200. A 1000-row daily result is explicit
`PARTIAL_SAFE` with `provider_limit`; it is not a short listing and is never represented as full
1200 coverage. `PARTIAL` remains the separate state for short listing or shorter available history.

The provider limit is passed to the long-history normalizer. Missing rows are not padded, daily
history is not reconstructed from weekly/monthly data, and no unsupported provider fallback is
introduced. A current incomplete daily bar may provide provisional context but cannot confirm a
pivot or enter completed-count coverage.

## Verified Provider Boundary

The supported `/ohlcv` contract exposes neither continuation tokens nor cursor, offset, before,
start-date, or end-date parameters. The endpoint rejects `count=1200` with HTTP 422. Although the
upstream Kiwoom adapter uses native continuation internally, thesis-monitor cannot resume that
continuation through its official interface. Unknown date parameters are ignored and return the
latest window again, so they cannot be used for safe chaining.

The existing `ohlcv-1200-backfill-cache-v1` code defines merge safety but has no runtime persistent
bar store or production fetch path. Immutable backfill reports are audit fixtures and must not be
loaded as a fresh runtime cache. The verified current policy is therefore
`VERIFIED_PARTIAL_SAFE_1000`, not a silent 1000-bar budget.

## Eligibility

A daily failure or verified provider-limited partial does not erase safe weekly/monthly structure.
`ELIGIBLE_SR_ONLY` remains possible
when a completed higher-timeframe source and a user-visible eligible zone exist. If all timeframe
coverage is failed, the KR rollout decision is `BLOCKED`. Coverage status and proximity semantics
are independent gates.
