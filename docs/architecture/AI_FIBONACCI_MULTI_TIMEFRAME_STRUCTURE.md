# AI Fibonacci Multi-Timeframe Structure

## Status

`multi-timeframe-price-structure-shadow-v2` is a shadow-only interpretation contract. It does not
change the production packet, current AI prompt, fallback, Telegram delivery, price rules, or
official assessment state.

## Ownership

```text
canonical adjusted OHLCV
  -> deterministic completed-bar structure
  -> timeframe-owned pivots and SR candidates
  -> AI/reference selector chooses canonical IDs and meaning
  -> validator checks identity, timeframe, chronology, and cutoff
  -> backend calculates Fibonacci and confluence
  -> shadow renderer
```

The selector never supplies a calculated price. The backend never chooses a business thesis. An
anchor slot that fails validation is omitted without invalidating valid independent timeframes.

## Hierarchy

- `MONTHLY = structural`: major cycle, large base, major prior high, structural retracement.
- `WEEKLY = intermediate`: multi-week trend, pullback, breakout/retest, intermediate boundaries.
- `DAILY = tactical`: nearest reaction zone, recent swing, rejection, reclaim.

Structural order is always monthly, weekly, daily. Proximity is reported separately and cannot
promote a daily level to structural ownership.

## Safety

- Completed adjusted bars only for anchor evidence.
- Pivot `confirmed_at` must be on or before the replay cutoff.
- Every selected ID must exist under the same ticker and timeframe.
- Fibonacci arithmetic uses `Decimal` and registered formulas.
- Confluence uses the minimum existing timeframe merge tolerance and complete-link grouping.
- No target, stop, buy/sell command, or thesis mutation is produced.
- User-visible routing remains disabled.

## Implementation

- Service: `app/services/multi_timeframe_price_structure_service.py`
- Variable selector boundary: `app/services/variable_ai_anchor_selection_service.py`
- Archive generator: `scripts/phase20260826_ai_fibonacci_multi_timeframe_v2.py`
- Variable trial generator: `scripts/phase20260826_variable_ai_anchor_repair.py`
- Focused tests: `tests/test_multi_timeframe_price_structure_service.py`

## Variable Selection Closure

The original v2 archive repeated `reference_select_price_structure()` and therefore proved only a
deterministic reference harness. The bounded closure adds an actual variable selector trial over
`price-only-ai-anchor-packet-v1`. The prompt contains raw candle context and canonical IDs but no
reference anchor or precomputed Fibonacci. Backend validation and all Fibonacci arithmetic remain
unchanged. Per-timeframe failure preserves deterministic SR and suppresses only that timeframe's
Fibonacci.
