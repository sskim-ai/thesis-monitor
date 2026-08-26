# OHLCV 1200 Backfill Cache

## Contract

`ohlcv-1200-backfill-cache-v1` binds cached history to security ID, listing ID, timeframe,
adjustment basis/version, and currency. Provider-native continuation (`cont-yn` / `next-key`) is
the initial backfill path; normal operation is an incremental append or revision against the same
cache identity.

## Stitch Validation

Pages are normalized, ordered, and deduplicated only when overlapping OHLCV economics match.
Conflicting duplicates or identity/basis/currency mismatches block the result. Exchange-session
gaps remain explicit. A provider-wide closure can be excluded only as a separately recorded
calendar override, never as a silent deletion.

Long-listed subjects require 1200 complete daily bars. A current partial daily bar is retained in
addition to that history. Subjects whose complete listing history is shorter than 1200 are safe
`PARTIAL`; provider truncation without a backfill attempt is not sufficient.

## Higher Timeframes

Dedicated weekly and monthly provider series retain their own `600W / 300M` gates. Daily bars are
not padded or resampled to claim unavailable higher-timeframe coverage.
