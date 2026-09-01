# Technical Feature Dependency Registry

Contract: `technical-feature-dependency-registry-v1`

Every emitted technical fact records dependency kind, start/end, bar count, dependency SHA-256,
and classification.

## Finite Dependencies

The exact implementation's `minimum_history` owns the dependency window for close, returns,
rolling range/drawdown, SMA, trend sequence, realized volatility, gap, Bollinger, ROC, stochastic,
volume ratio, CMF, MFI, and Donchian facts. An old malformed row outside that exact suffix cannot
taint the fact.

## Recursive Full-History Dependencies

EMA, MACD, RSI, ATR, ADX/DMI, and OBV use seeded recursive or cumulative implementations. Their
current values depend on all normalized history supplied to the engine. They remain blocked when a
malformed row falls anywhere in that history; no finite warmup approximation is claimed.

## Classifications

- `SAFE`
- `SAFE_INDEPENDENT_OF_BAD_ROW`
- `SAFE_AFTER_PROVEN_WARMUP` (reserved until equivalence is proven)
- `UNSAFE_DEPENDS_ON_BAD_ROW`
- `UNAVAILABLE_OTHER_REASON`

Dropping a bad row from inside a feature dependency and calling the result equivalent is forbidden.
