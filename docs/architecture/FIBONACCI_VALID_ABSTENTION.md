# Fibonacci Valid Abstention

## Contract

`fibonacci-valid-abstention-v1` treats a bounded refusal to choose a swing structure as valid output,
not malformed AI output. Valid statuses are `AMBIGUOUS` and `INSUFFICIENT_STRUCTURE`; both require
null primary and alternative structure IDs.

## Behavior

- `AMBIGUOUS` means more than one canonical structure remains reasonably supported.
- `INSUFFICIENT_STRUCTURE` means the supplied completed-bar evidence does not support a defensible
  canonical structure.
- The backend records `VALID_ABSTENTION` and omits Fibonacci only for that timeframe.
- Deterministic support/resistance remains available without substitution or widening.
- Other valid timeframes continue independently.

An abstention with a non-null selection, an unknown status, a noncanonical ID, or malformed schema
is a true rejection and fails closed for the affected timeframe. It is never converted to a
reference selection or a fabricated anchor.

The actual frozen trial observed 56 valid abstentions and rejected zero of them as malformed.

