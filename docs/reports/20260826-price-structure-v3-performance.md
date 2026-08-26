# Price Structure v3 Performance

- Provider calls: `20`; cache hits: `0` (initial frozen backfill).
- Median collection per stock: `1621.626 ms`.
- Median deterministic compute per stock: `33.586 ms`.
- P95 deterministic compute per stock: `53.041 ms`.
- KR deterministic runtime: `286.120 ms`.
- US deterministic runtime: `274.967 ms`.
- Full-watchlist deterministic runtime: `561.087 ms`.
- Frozen archive bytes: `10835812`.
- Evidence JSON bytes: `8500383`.

Cache design: security/timeframe/adjustment-version key, immutable historical backfill, incremental
completed-bar updates, and version-aware revision replacement. Production scheduling is unchanged.
