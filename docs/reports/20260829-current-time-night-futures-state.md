# Current-Time Night-Futures State

- Execution time (KST): `2026-08-29T21:16:59.579875+09:00`
- Mode: read-only current-time E2E test

## Canonical Gate

| Item | Result |
|---|---|
| Expected latest night session | `2026-08-29` |
| Latest returned verified pair | `2026-08-28` |
| Freshness | `stale` |
| Canonicalization | `PASS` |
| Current state | **SOURCE_LIMITATION_SAFE** |
| Stale value visible | `0` |

The current expected session returned no row. A verified prior-session pair exists but remained suppressed; no freshness bypass was used.
