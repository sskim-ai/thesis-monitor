# OHLCV Structure Engine v2

## Problem

OHLCV data without deterministic structure leaves support, resistance, swings, invalidation, and
risk/reward unavailable. Letting Codex calculate them would violate fact provenance. The first engine
also needed correction for truncated-index alignment, timeframe scoring, monthly invalidation, and
anchor confidence.

## Decision

`app/services/ohlcv_structure_service.py` implements `ohlcv-structure-v2` on adjusted technical
OHLCV. It produces detailed audit output and a compact AI packet summary. Existing provider
Bollinger, volume ratio, RSI, and MACD values remain authoritative where available.

## Why

Deterministic calculation makes chart structure repeatable, testable, and provenance-bound while
keeping the model focused on interpretation.

## Rejected Alternatives

- Reusing Local Pivots as Major Swings or Fibonacci anchors.
- Calculating indicators inside the AI Review service.
- Using unadjusted historical-valuation prices for technical structure.
- Skipping a nearer monthly support to manufacture a farther daily/weekly invalidation.
- Choosing a farther resistance to improve risk/reward.

## Safety Constraints

- Local Pivot is not Major Swing.
- Chart `INVALID` is not thesis invalidation.
- Chart states are context, not trading commands.
- Adjusted technical price is separate from unadjusted historical valuation price.
- Monthly invalidation is undefined and fails closed; dependent risk/reward is unavailable.
- Major Base with unverified pre-base regime is at most Medium confidence.

## Wilder ATR14

True range is the maximum of current high-low and both gaps to prior close. Initial ATR14 is the mean
of the first 14 true ranges. Subsequent values use Wilder recursion:

```text
ATR[t] = (ATR[t-1] * 13 + TR[t]) / 14
```

ATR controls prominence, merge tolerance, padding, swing reversal, invalidation, and volatility
normalization. It is not a signal.

## Local Pivot Engine

Local Pivots serve support, resistance, boxes, repeated reaction zones, and Bollinger overlap only.

| Timeframe | Window | Confirmation | Minimum prominence |
|---|---:|---:|---|
| Daily | 5/5 | 10 bars | max(2%, 1.0 ATR) |
| Weekly | 3/3 | 5 bars | max(3%, 1.25 ATR) |
| Monthly | 2/2 | 3 bars | max(5%, 1.5 ATR) |

Equal-price ties select the highest-volume bar, then the middle bar. Similar prices are grouped around
the group median. Merge tolerance is max(center percentage, 0.5 ATR): 1.75% daily, 2.25% weekly,
3.00% monthly. Zones receive ATR/percentage padding and deterministic largest-gap splitting when they
exceed the 5%/7%/10% width cap.

Support lies below current price, resistance above it, and an active zone contains current price.
Support and resistance are ordered by actual price distance, not strength score.

## Zone Strength and Boxes

Zone ranking combines reaction count, recency, true higher-timeframe overlap, Bollinger overlap, and
Major-Swing Fibonacci overlap. Higher timeframes are directional:

```text
Daily -> Weekly, Monthly
Weekly -> Monthly
Monthly -> none
```

Scores 8-12 are Strong, 5-7 Medium, and 0-4 Weak. The score ranks chart zones only. Boxes require the
timeframe width limit, at least 60% closes inside, and two reactions at each boundary.

## Major Swing Engine

Major Swings consume raw normalized OHLCV and ATR, never Local Pivot objects. Weekly is primary when
sufficient, daily is fallback, and monthly provides long-term confirmation. ATR ZigZag reversal uses
the larger of percentage and ATR thresholds:

| Timeframe | Percentage | ATR multiple | Minimum leg |
|---|---:|---:|---:|
| Daily | 8% | 2.5 | 10 bars |
| Weekly | 12% | 2.5 | 4 bars |
| Monthly | 18% | 2.0 | 2 bars |

Canonical `NormalizedBarSeries` is shared by detection and anchor selection. Every swing and anchor
must satisfy `bars[index].date == date`, including a 300-source-bar to 156-week analysis truncation.

## Major Anchors

- Major Base Low requires the rise threshold and prior major-high break. High confidence additionally
  requires a verified pre-base decline or sideways regime; otherwise confidence is capped at Medium.
- Breakout Start uses a weekly close above the prior 20-week highest close. Volume ratio at least 1.2
  strengthens confidence; missing historical volume retains the anchor but caps confidence at Medium.
- First Higher-Low is at least 5% above Major Base and requires a later prior-high break.

Each anchor stores type, timeframe, date, index, price, source, confidence, selection reasons, and
blocking unknowns.

## Elliott and Fibonacci

Elliott is tentative and uses only Major Swings. Wave 2 cannot break the Wave 1 start; Wave 3 must
make a higher high. Wave 4 overlap reduces confidence and may indicate a diagonal rather than forcing
deletion. Low-confidence counts are audit-only.

Fibonacci uses verified Major Base, Breakout Start, or First Higher-Low anchors. Retracements are
0.382, 0.5, and 0.618; extensions are 0.618, 1.0, 1.618, and 2.618. Anchor index/date mismatch suppresses
Fibonacci. Medium-confidence anchors are context but cannot be the sole core reason; low confidence is
audit-only.

## Invalidation and Risk/Reward

Daily support invalidation uses 0.5 daily ATR or 1.0%, whichever is larger. Weekly support uses 0.5
weekly ATR or 1.5%. Monthly support returns `monthly_invalidation_contract_undefined` and withholds
risk/reward.

Hard invalidation requires two daily closes or one weekly close below invalidation. An accelerated
failure requires close below invalidation, volume ratio at least 1.2, and verified distribution. A
wick-only breach that closes back above remains pending.

Risk/reward uses current or explicitly labeled scenario entry, structural invalidation, and the lower
bound of the nearest Strong/Medium resistance. Missing target or invalidation means unavailable.

The compact selected Strong/Medium support, resistance, RR, invalidation, chart state, and stable zone
identity are persisted in `monitoring-state-v1`. Registered thesis support is not substituted when a
dynamic structure input is missing.

## Chart State

Internal priority is `INVALID`, `TRIM`, `CONFIRM_ENTRY`, `SECOND_SUPPORT_ENTRY`, `SUPPORT_ENTRY`,
`HOLD`, then `WAIT`. State output includes confidence, reasons, and blocking unknowns. Missing US
investor-flow data limits supply-dependent confidence; it is never assumed neutral.
