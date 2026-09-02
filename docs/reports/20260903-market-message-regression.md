# 2026-09-03 Market Message Regression

## Result

`TRACK_C_MARKET_REGRESSION = PASS`

## Preserved US Sections

| Contract | Evidence |
| --- | --- |
| SPY/QQQ/IWM/SOXX/RSP | Full-message index tuple tests pass |
| Market internals | Relative-strength and equal-weight tests pass |
| Sector strength/weakness | Selected leader/laggard ownership tests pass |
| Treasury 3Y/5Y/10Y/30Y | Latest safe level and prior valid delta tests pass |
| Next checks | Required-section count and layout tests pass |

The nominal Treasury curve remains the primary rate block. The 10Y real yield is
not rendered as a primary user-facing rate block.

## Night-Futures Controls

- verified fresh pair: suppressed
- partial fresh/stale pair: block and caution suppressed
- stale pair: block and caution suppressed
- DWM sidecar: retained internally, suppressed from user output
- AI fallback market renderer: night fact prose suppressed

## Validation

Focused user-facing, collector, session mapping, history, DWM, publication
telemetry, and morning-gate suite: `202 passed`.

Full repository suite: `2142 passed`, with one upstream Starlette/httpx
deprecation warning.

The suite also fixed wall-clock dependence in six probe tests by supplying explicit
observation times. No collector or date-convention implementation changed.

- `UST_3Y_5Y_10Y_30Y_BLOCK = PASS`
- `US_NIGHT_FUTURES_SECTION_ABSENT = PASS`
- `TRACK_C_MARKET_REGRESSION = PASS`
