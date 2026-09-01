# OHLCV Corporate Action Normalization

Corporate action is a diagnosis, not a candle-repair heuristic. A large move or malformed OHLC
relationship alone never proves a split, reverse split, distribution, ADR ratio change, or ticker
change.

The current provider owns adjusted-bar production. Thesis Monitor does not apply a second action
factor. Deterministic fixtures verify that hypothetical split, reverse-split, and no-split pairs
have one uniform O/H/L/C factor and that mixed-field adjustment is rejected. ADR ratio adjustment
is not implemented and cannot be used for recovery.

If system-side normalization is introduced later, it must preserve the raw occurrence, official
action identity and effective session, exact price and volume factors, security identity, source
fingerprints, and a new cache/source version. Until then, unresolved action semantics remain
invalid or unavailable.

