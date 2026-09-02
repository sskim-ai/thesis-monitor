# 2026-09-03 Night-Futures Temporary Suppression

## Result

`NIGHT_FUTURES_USER_FACING_TEMP_SUPPRESSED = PASS`

Internal reason: `SESSION_DATE_CONVENTION_PENDING`.

## User-Facing Paths

| Path | Result |
| --- | --- |
| US full market message | Night block and night fact IDs suppressed |
| US daily-digest fallback | Fresh/partial/stale night block suppressed |
| Morning macro notification | Night block and night-only cautions suppressed |
| AI market-message fallback | Night change and night caution block suppressed |

The internal reason is not exposed in message prose. No replacement warning is
rendered because it would preserve the same unresolved semantic as user-facing
content.

## Preserved Evidence

- KRX and Kiwoom collectors: unchanged
- session-date mapping: unchanged
- raw capture and publication telemetry: unchanged
- history and daily/weekly/monthly aggregation: unchanged
- internal night-futures summarization: unchanged

The renderer tests retain populated night-futures and DWM inputs while proving the
output and returned user-facing fact IDs are empty.

## Deterministic Test Clock

Six existing KRX probe tests implicitly used the wall clock and returned
`unfinalized` before 06:00 KST. They now pass explicit post-finality observation
times. Production collection logic and finality rules were not changed.

## Gate Values

- `NIGHT_FUTURES_SESSION_ARCHITECTURE_CHANGED = 0`
- `US_NIGHT_FUTURES_USER_FACING_COUNT = 0`
- `REAL_YIELD_PRIMARY_USER_BLOCK_REINTRODUCED = 0`
