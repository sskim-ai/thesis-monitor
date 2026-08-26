# Price Structure v3 Ambiguity Set

## Contract

`price-structure-v3-ambiguity-set-v1` distinguishes known-candidate ambiguity from insufficient
structure.

`SELECTED` carries one valid hypothesis ID and may carry one supplied alternative. `AMBIGUOUS`
may carry two or three supplied competing IDs and an optional backend class ID. `INSUFFICIENT_STRUCTURE`
carries no IDs.

The validator rejects unknown IDs, mixed tickers, mixed degrees, invalid class membership,
future endpoints, and replay-context mismatch. Once validated, the deterministic consensus
universe is the union of selected, alternative, and competing IDs returned by the current trial.

An ambiguous set is never reduced to one member by the backend. If no family survives consensus,
all Fib is omitted while deterministic support/resistance remains.
