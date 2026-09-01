# Technical Context Freshness

Daily bars are compared with the expected completed session. Weekly/monthly rows retain their own
completed-period semantics. A stale daily row is not exposed as current evidence, while safe W/M
facts can remain usable. Future bars are invalid.

Controls:

- expected daily mismatch -> `PARTIAL_SAFE`, daily `STALE`, no daily evidence ref.
- missing W/M -> `PARTIAL_SAFE`, daily evidence retained.
- malformed OHLC -> subject `INVALID`.
- no safe rows after bounded acquisition -> `UNAVAILABLE`.

`OHLCV_FRESHNESS_USES_NAIVE_WALLCLOCK_ONLY = 0`

`STALE_DAILY_CACHE_PRESENTED_AS_CURRENT = 0`
