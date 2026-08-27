# 2026-08-27 US Morning Core ETF Data

## Canonical Completed-Session Set

The production macro briefing and packet agree on the `2026-08-26` completed US regular session. Values come from the existing production OHLCV analyst; returns are backend-owned, not AI-calculated.

| Symbol | Close | Return | Observation | Packet state | Digest use |
|---|---:|---:|---|---|---|
| SPY | `$766.08` | `+0.0222%` | `2026-08-26` | `CURRENT_DIRECTIONAL` | material omission |
| QQQ | `$711.37` | `+0.0915%` | `2026-08-26` | `CURRENT_DIRECTIONAL` | material omission |
| IWM | `$298.93` | `-0.1003%` | `2026-08-26` | `CURRENT_DIRECTIONAL` | material omission |
| SOXX | `$515.40` | `+0.2607%` | `2026-08-26` | `CURRENT_DIRECTIONAL` | material omission |
| RSP | `$222.11` | `+0.1533%` | `2026-08-26` | `CURRENT_DIRECTIONAL` | material omission |

The packet also owns `QQQ-SPY +0.0693pp`, `RSP-SPY +0.1311pp`, and `SOXX-SPY +0.2385pp`. None entered `market-review.json`, the deterministic digest, or the delivered concise market digest.

The values and session identity are correct, so `US_CORE_ETF_SESSION_MATCH=PASS`. The downstream omission is separately classified as material P1; this report does not reinterpret it as a source or session failure.
