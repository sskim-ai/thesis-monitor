# 2026-08-25 KR Natural Production Review

## Identity

| Item | Value |
| --- | --- |
| Run ID | `38` |
| Packet ID | `2026-08-25-kr-run-38-6cd8c5d5091b` |
| Assessment date | `2026-08-25` |
| Source monitor start | `2026-08-25 16:05:31.441646 KST` |
| Packet created | `2026-08-25 16:06:11.582752 KST` |
| Expected / actual | `8 / 8` |
| Final terminal send | `2026-08-25T17:10:15.802848+09:00` |
| Final mode | `deterministic_fallback` |
| Aggregate receipt | `delivery-result.json sha256:8663b9a16793be3f15722d33df4c087e8145ab2b959f6b4c61b08a508ea2752d` |

## Natural AI Path

| Path | Observed at KST | Error count | Terminal result |
| --- | --- | --- | --- |
| primary | 2026-08-25T16:29:14+09:00 | 230 | rejected, fallback eligibility preserved |
| primary | 2026-08-25T16:30:18+09:00 | 8 | rejected, fallback eligibility preserved |
| backup | 2026-08-25T16:58:44+09:00 | 21 | rejected, fallback eligibility preserved |
| backup | 2026-08-25T17:00:41+09:00 | 2 | rejected, fallback eligibility preserved |

The final candidate was rejected at `2026-08-25 17:00:42 KST` for exactly:

```text
000660:numeric_fact_ref_fact_not_declared:s000660_val_pbr:valuation:current
000660:numeric_fact_ref_fact_not_declared:s000660_val_hist_pb:valuation:current
```

The validated-output gate therefore prevented Free Analyst candidate construction and the Adaptive
selector from running. The 17:10 supported fallback then sent all eight slots.

## Delivery Result

- `KR_PRODUCTION_NATURAL = LIVE_PASS`
- AI candidate delivered: `0`
- Deterministic fallback delivered: `8`
- Duplicates / orphans / packetless intents: `0 / 0 / 0`
- Exactly once: `PASS`
- Receipt integrity: `PASS`
