# 2026-08-26 US Morning Structured Context Audit

## Verdict

`US_COMPLETED_SESSION = PASS`

`US_STRUCTURED_MARKET_CONTEXT = PARTIAL`

`US_SECTOR_CONTEXT = PARTIAL`

The packet used the completed `2026-08-25` US regular session and preserved temporal roles correctly. However, some current structured observations acquired by the production macro job did not cross the briefing/packet boundary.

## Packet-Visible Current Facts

| Fact | Value | Source | Session / observation | Role |
|---|---:|---|---|---|
| SPY return | `+0.3196%` | OHLCV analyst | `2026-08-25 us_regular` | current |
| QQQ return | `+0.6229%` | OHLCV analyst | `2026-08-25 us_regular` | current |
| IWM return | `+0.4229%` | OHLCV analyst | `2026-08-25 us_regular` | current |
| SOXX return | `+1.5568%` | OHLCV analyst | `2026-08-25 us_regular` | current |
| QQQ minus SPY | `+0.3033pp` | backend relation | same completed session | current |
| SOXX minus SPY | `+1.2372pp` | backend relation | same completed session | current |
| DGS10 change | `-4bp` | FRED | `2026-08-24` official occurrence | current by temporal contract |
| DFII10 change | `-2bp` | FRED | `2026-08-24` official occurrence | current by temporal contract |
| T10YIE change | `0bp` | FRED | `2026-08-25` | current |
| VIX return | `+4.7588%` | FRED | `2026-08-24` official occurrence | current by temporal contract |
| Broad dollar | `-0.7065%` | FRED | `2026-08-21` | reference-lagging |
| USD/KRW | `+0.2677%` | ECOS | `2026-08-25` | reference-lagging |
| WTI | `+2.0172%` | FRED | `2026-08-18` | reference-lagging |

All packet-visible relative facts use the same session and backend arithmetic. No AI arithmetic or incomplete session promotion was found.

## Acquired But Dropped

The production `macroobservation` rows also contained current-session RSP and sector proxies:

| Fact | Acquisition state | Packet state | Safe use |
|---|---|---|---|
| RSP | current level `221.77`; no prior value | marked missing | level/context only; no daily direction |
| XLF | current return `+0.1546%` | missing | directional sector context eligible |
| XLE | current return `-1.6638%` | missing | directional sector context eligible |
| XLB/XLI/XLK/XLP/XLRE/XLU/XLV/XLY | current first observation; no prior | missing | non-directional only |
| XLC | provider HTTP failure | missing | fail-closed |

This caused the digest to omit a material, safely available energy-versus-financial dispersion and to lose the equal-weight level path. It did not create a wrong number, but it is material information loss and therefore P1.

## Bounded Repair

Propagate acquired style/sector observations through the briefing adapter using existing prior-value and temporal eligibility gates. First-observation-only values must remain non-directional, while XLE/XLF may carry session direction. Keep XLC unavailable. Re-run an immutable packet replay, then require a later natural proof.
