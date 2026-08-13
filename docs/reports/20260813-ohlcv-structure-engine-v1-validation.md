# OHLCV Structure Engine v1 Validation

## Scope

- Base: `43d49a6bbf59f78d477731aee2fe1107e76bd699`
- Algorithm: `ohlcv-structure-v1`
- AI policy: `daily-review-v3.4`
- Output schema: `3`
- Price basis: adjusted technical OHLCV
- Historical valuation basis: unchanged unadjusted weekly prices
- Database migration: none
- Public Action schema: unchanged
- Production Assist: disabled

The engine is implemented in `app/services/ohlcv_structure_service.py`, outside the AI Review
service. It consumes raw OHLCV and existing provider indicators/supply; Codex only receives compact,
validated output.

## Contract Before / After

| Capability | Before | After | Fail-closed behavior |
| --- | --- | --- | --- |
| Wilder ATR14 | unavailable | available | insufficient history remains unavailable |
| Local Pivot | unavailable | daily/weekly/monthly | prominence and tie-break required |
| Support / Resistance | unavailable | zone-based | no single-pivot line |
| Box | unavailable | conditional | width/inside/touch tests required |
| Major Swing | unavailable | weekly primary, daily fallback | independent raw-bar ATR ZigZag |
| Elliott | unavailable | tentative, confidence gated | low confidence excluded from core reasoning |
| Fibonacci | unavailable | Major-Swing anchors only | no Local-Pivot anchoring |
| Invalidation | unavailable | structural, chart-only | weak/unavailable support yields unknown |
| Risk / Reward | unavailable | nearest meaningful resistance | farther resistance cannot improve RR |
| Chart State | unavailable | seven internal states | never an order or thesis state |

Trading-value ratio remains provider-unavailable. It lowers `CONFIRM_ENTRY` confidence instead of being
invented.

## Deterministic Algorithms

- ATR: Wilder initial 14-TR mean, then `(previous * 13 + TR) / 14`.
- Local Pivot: daily 5/5, weekly 3/3, monthly 2/2 windows. Equal prices choose highest volume, then the
  middle bar. Prominence uses both-side recovery and max(percent, ATR) thresholds.
- Zones: median-centered grouping, percent/ATR merge tolerance, ATR/percent padding, and deterministic
  largest-gap splitting at the width cap. Support and resistance are sorted by actual price distance.
- Boxes: timeframe width cap, 60% inside-close ratio, and two reactions at each boundary.
- Major Swing: raw-bar-only ATR ZigZag with close-based reversal and minimum-leg requirements.
- Fibonacci: long-term Major Base, medium-term First Higher-Low, and Breakout anchors with full
  date/price/timeframe/confidence provenance.
- Invalidation: structural support buffer with two-close, weekly-close, accelerated, and wick-only
  semantics. It is explicitly `chart_only`.
- RR: current or scenario entry to the nearest Strong/Medium resistance lower bound. Missing eligible
  support/resistance stays unavailable.
- State priority: INVALID, TRIM, CONFIRM_ENTRY, SECOND_SUPPORT_ENTRY, SUPPORT_ENTRY, HOLD, WAIT.

## Local / Major Separation Proof

The Major Swing detector accepts raw bar mappings and rejects Local-Pivot objects. No Local-Pivot list
is passed into Major Swing, Elliott, or Fibonacci.

Live SK hynix (`000660`) counts:

| Timeframe | Local pivots | Major swings |
| --- | ---: | ---: |
| Daily | 28 | 6 |
| Weekly | 17 | 6 |
| Monthly | 6 | 4 |

Its Fibonacci anchors came from weekly Major Swings: Major Base `2024-08-05`, Breakout/First
Higher-Low `2025-04-14`, and dominant Major High `2025-11-10`. None was mechanically copied from the
Local-Pivot collection.

## Active Universe Smoke

Read-only discovery found 20 active companies: KR 7 and US 13. All 20 returned fresh chart context and
a deterministic chart state. Coverage was:

| Output | Available |
| --- | ---: |
| ATR | 20/20 |
| Local Pivot zones | 20/20 |
| Boxes | 2/20 |
| Major Swing | 19/20 |
| Fibonacci | 17/20 |
| Invalidation | 16/20 |
| Risk / Reward | 16/20 |
| Chart State | 20/20 |

Unavailable output was evidence-driven. `SKHY` lacked enough listing history for Major Swing/Fib/RR;
`000660` and `005930` had no eligible Strong/Medium support, so invalidation and RR were not produced.

State distribution was `WAIT 17`, `SUPPORT_ENTRY 1`, and `HOLD 2`. No live ticker met the final
Strong/Medium-zone, two-close, and volume requirements for `CONFIRM_ENTRY`. These are internal
price-structure states. `HOLD` is not a new-buyer signal, `TRIM` is not a full-sale instruction, and
`CONFIRM_ENTRY` is not a recommendation.

Representative live results:

| Ticker | Type | Local D/W/M | Major D/W/M | Nearest support | Nearest resistance | RR | State |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| 000660 | KR memory | 28/17/6 | 6/6/4 | 1,190,321-1,301,679 Weak | 1,618,575-1,737,425 Weak | unknown | WAIT |
| 003690 | KR insurance | 40/18/11 | 7/4/3 | 14,159-14,571 Strong | 14,770-15,070 Medium | 0.168 | WAIT |
| 010120 | KR EPC/electrical | 33/16/7 | 6/6/8 | 191,823-203,377 Weak | 220,642-231,358 Medium | 0.127 | WAIT |
| MU | US semiconductor | 36/18/4 | 3/6/4 | 836.12-872.58 Weak | 969.38-1,012.82 Weak | 3.891 | HOLD |
| GOOGL | US general | 33/17/6 | 8/8/3 | 338.58-342.40 Weak | 343.65-353.79 Medium | 0.003 | WAIT |

US states record `verified_supply_unavailable` where supply confirmation matters; unavailable US flow
is never treated as neutral.

## AI Packet and Numeric Safety

Full pivot/zone/swing audit remains in assessment price context. AI packets include only two nearest
supports, one nearest resistance, active zones, one box per timeframe, six recent Major Swings,
selected Fib anchors, invalidation, RR, state, confidence, and blocking unknowns.

Explicit prose semantics were added for ATR, support/resistance/active zones, boxes, Major Swing,
Fibonacci, scenario entry, target, chart invalidation, price risk, and RR. Unknown semantics remain
fail-closed. Tests reject an ATR value labeled as revenue and a support value labeled as resistance.

## Validation

- Focused structure/client/AI/delivery suite: 101 passed
- Full pytest: 556 passed, 1 dependency deprecation warning
- Ruff: passed for the full repository
- `git diff --check`: passed
- Investment Knowledge v3 SHA: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge v1 SHA: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

Both Knowledge source/runtime checksum pairs are unchanged. GitHub Actions will be verified against
the exact pushed commit and recorded in the completion report.
