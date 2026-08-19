# Phase 8.5.4.2 Validation

As of: `2026-08-19 KST`

## Scope

- Exchange-calendar-aware NIGHT -> preceding eligible DAY lookup.
- Shared parser/canonicalizer session basis.
- Provider raw-change audit cross-check.
- Historical holiday replay and stale-current separation.
- No feature, schema, DB, delivery or task change.

## Results

| Gate | Result |
|---|---|
| Holiday traversal | PASS: 2026-08-18 -> 2026-08-14 |
| Ordinary control | PASS: 2026-08-14 -> 2026-08-13 |
| Same-date/future DAY rejection | PASS |
| Same-contract/rollover fail-closed | PASS |
| Provider raw-change match/conflict | PASS |
| Current empty/stale separation | PASS |
| Focused night/digest/gate suite | `99 passed` |
| Expanded runtime repair suite | `494 passed` |
| Full pytest | `1074 passed`, one third-party warning |
| Ruff | PASS |
| `git diff --check` | PASS |
| Investment/Chart Knowledge parity | PASS |
| Public Action / operationId | `0.4.5` / `20/20` unique |

## Live Read-Only Probe

- Current expected 2026-08-19 row count: 0.
- Latest reconstructable source: 2026-08-18 NIGHT.
- Reference: 2026-08-14 DAY via XKRX holiday traversal.
- KOSPI200: -3.95 / -0.35945036%, provider cross-check match.
- KOSDAQ150: -10.20 / -0.68571429%, provider cross-check match.
- Freshness: `stale`; current user-visible promotion: 0.

## Boundaries

- Telegram sends: 0.
- Scheduled Task runs/config changes: 0/0.
- Pilot mutations: 0.
- DB migrations/mutations: 0/0.
- Archive/receipt rewrites: 0/0.
- Production Assist: OFF.
- Phase 8.3/KRX 8.2A experimental leakage: 0.

Local validation passes. Operating promotion remains conditional on exact implementation-SHA
GitHub Actions Test/Lint and a final main-drift check.
