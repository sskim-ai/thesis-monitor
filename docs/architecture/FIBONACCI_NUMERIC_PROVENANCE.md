# Fibonacci Numeric Provenance

## Calculation Boundary

The selector chooses only low, high, and optional correction-low pivot IDs. The backend validates
those IDs and calculates:

```text
retracement = H - (H - L) * ratio
extension   = C + (H - L) * ratio
```

Retracement ratios are 0.382, 0.500, and 0.618. Extension ratios are 0.618, 1.000, 1.618, and 2.618.
Arithmetic uses `Decimal`; outputs are rounded to six decimal places with half-up rounding.

## Level Provenance

Every `FibonacciLevel` records:

- ticker and timeframe;
- mode and ratio;
- calculated price and currency;
- low/high/correction anchor refs;
- formula and calculation version;
- adjustment basis and as-of date;
- deterministic level ID and rounding rule.

An invalid or cross-timeframe anchor suppresses that timeframe's Fibonacci only. AI-calculated
prices and unregistered numeric levels are forbidden.

## Value Gate

All valid ratios may exist in the audit object. The shadow renderer keeps at most two levels per
timeframe and only when a level overlaps selected SR, current price, or strict cross-timeframe
confluence under existing merge tolerances. Calculation availability does not force prose exposure.
