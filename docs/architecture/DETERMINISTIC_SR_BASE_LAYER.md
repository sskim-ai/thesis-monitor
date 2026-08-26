# Deterministic SR Base Layer

Contract: `deterministic-sr-base-layer-v1`.

The engine builds monthly, weekly, and daily deterministic maps before wave or Fibonacci work.
Accepted base families are confirmed pivot groups, canonical Bollinger references, and validated
balance boxes. Fibonacci is never a base-SR source. Each timeframe emits a current zone, nearest
support/resistance, major support/resistance, additional zones, and an explicit missing-side state.

The base remains valid for `NO_VALID_WAVE`, `NO_STABLE_FIB`, and
`NO_MEANINGFUL_SR_OVERLAP`. Missing is never filled with current price or a projected number.
