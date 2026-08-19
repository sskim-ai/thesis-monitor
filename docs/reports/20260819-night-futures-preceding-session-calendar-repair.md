# Night Futures Preceding-Session Calendar Repair

As of: `2026-08-19 KST`

## Root Cause

Classification: `CALENDAR_TRAVERSAL_BUG`.

The collector already queried a bounded seven-calendar-day window, which included the required
2026-08-14 provider payload. Availability failed after collection because both the parser and the
canonical session validator required:

```text
reference_date = NIGHT BAS_DD - 1 calendar day
```

For 2026-08-18 NIGHT this selected 2026-08-17. XKRX marks 2026-08-17 as a non-session, so the
existing code never considered the available 2026-08-14 DAY row. The issue was not a missing query
range, cache miss, contract mismatch or provider row-order problem.

## Repair

The shared market-session utility now returns the latest XKRX session strictly before a NIGHT
session date. The parser and `night-futures-session-basis-v1` canonical validator call the same
utility. It has no weekday fallback: if an authoritative calendar result cannot be obtained, the
pair remains unavailable.

Selection now requires:

1. completed NIGHT row;
2. latest preceding eligible XKRX DAY date;
3. identical product, contract code and maturity;
4. strictly earlier exchange-session ordering;
5. valid reference price;
6. deterministic backend point/percent calculation;
7. provider raw-change agreement when that field exists;
8. current-session freshness before user-visible promotion.

The policy does not search farther back after a contract mismatch. It also never selects a DAY row
with the same or a future `BAS_DD`.

## Provider And Cache Boundary

The KRX endpoint accepts one `basDd` per request. The existing bounded lookback is retained; no
unbounded or retry-based traversal was introduced. Current NIGHT freshness is independent of the
historical DAY reference: an old verified pair is never substituted when the expected current row
is empty.

KRX daily rows do not provide a row-level timestamp. The repair does not fabricate one. Temporal
ordering is proved by XKRX session dates and the explicit DAY/NIGHT contract; source record IDs and
payload SHA256 values remain attached to both rows.

## Safety Result

- Same-date DAY fallback: 0.
- Future DAY selection: 0.
- Cross-contract linkage: 0.
- Provider change used as the calculation source: 0.
- Stale historical pair promoted as current: 0.
- Instrument/date-specific production exceptions: 0.

The repair restores a valid reference when one exists without weakening any Phase 8.5.4 fail-closed
gate.
