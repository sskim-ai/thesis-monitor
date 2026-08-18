# Phase 8.2A.1 Current-Session Readiness

Date: 2026-08-18
Contract: `krx-publication-readiness-v1`
Current status: `MARKET_COMPLETED_PROVIDER_PENDING`
Current-session readiness: PARTIAL

## State Machine

| State | Meaning | Full current snapshot |
|---|---|---|
| `MARKET_NOT_COMPLETED` | XKRX target session is not completed | Denied |
| `MARKET_COMPLETED_PROVIDER_PENDING` | Completed session; all core endpoints returned empty HTTP 200 | Denied |
| `PROVIDER_PARTIAL` | Only part of the required endpoint/identity bundle is ready | Denied |
| `PROVIDER_COMPLETE` | All core endpoints are non-empty, exact-date, identity-valid | Allowed |
| `PROVIDER_ERROR` | HTTP, network, or schema failure | Denied |
| `STALE_PROVIDER_DATE` | Provider rows do not match the target completed session | Denied |

No individual partial Fact is promoted in Phase 8.2A.1. Archive collection remains an explicit exact-
date operation; future current integration must pass this preflight first.

## 2026-08-18 Observation

XKRX classified 2026-08-18 as the latest completed regular session. At
`2026-08-18T20:27:09.594575+09:00` the four core endpoints returned:

| Endpoint | HTTP | Rows | Endpoint state | Latency ms |
|---|---:|---:|---|---:|
| `sto/stk_bydd_trd` | 200 | 0 | EMPTY | 124.3 |
| `sto/ksq_bydd_trd` | 200 | 0 | EMPTY | 139.2 |
| `idx/kospi_dd_trd` | 200 | 0 | EMPTY | 107.2 |
| `idx/kosdaq_dd_trd` | 200 | 0 | EMPTY | 75.2 |

This is provider publication pending, not market-open, provider-error, no-data-zero, or a promotable
current snapshot. The payload exposes no explicit publication timestamp. First non-empty and first
complete observations are both `NOT_YET_OBSERVED`.

## Future Observation

Proposed shadow windows are 15:35, 15:45, 16:00, 16:05, and 16:10 KST. They are a measurement plan,
not a production schedule. Reference metadata can remain cached; each window needs only four core
calls, well inside the documented 10,000-call daily limit. One normal-session complete observation
would make readiness STRONG PARTIAL; 3-5 sessions are recommended before CLOSED consideration.
