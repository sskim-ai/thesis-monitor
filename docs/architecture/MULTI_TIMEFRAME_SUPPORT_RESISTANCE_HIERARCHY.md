# Multi-Timeframe Support/Resistance Hierarchy

## Separate Ownership

The existing OHLCV engine computes local zones per timeframe, then scores them together and exposes
one collapsed nearest support/resistance view. The v2 shadow layer preserves the original timeframe
on every candidate and performs selection inside each timeframe before synthesis.

| Timeframe | Role | Selection preference |
|---|---|---|
| Monthly | `PRIMARY_STRUCTURAL_ZONE` | strength, score, then proximity |
| Weekly | `INTERMEDIATE_ZONE` | strength, score, then proximity |
| Daily | `NEAREST_TACTICAL_ZONE` | proximity, then score |

Only Strong/Medium zones are selection eligible. Weak zones can remain in full-debug evidence but
cannot make a timeframe available by themselves.

## Importance vs Proximity

Monthly > weekly > daily defines structural significance. The nearest support/resistance references
are calculated independently across already-selected zones. Thus a daily zone can be nearest while a
monthly zone remains the primary structural reference.

## Conflicts

Mixed regimes are preserved. A monthly uptrend, weekly pullback, and daily resistance are rendered
as three layers, not reduced to one verdict. The synthesis may be `ALIGNED`, `MIXED`, `CONFLICTING`,
or `INSUFFICIENT` without altering the timeframe hierarchy.
