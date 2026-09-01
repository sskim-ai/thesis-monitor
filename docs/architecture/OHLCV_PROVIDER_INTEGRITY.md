# OHLCV Provider Integrity

Contract: `ohlcv-provider-integrity-v1`

The provider boundary validates normalized D/W/M bars before feature generation. It requires a
valid ISO session date, finite positive O/H/L/C, nonnegative volume, ordered unique timestamps, and
the exact OHLC enclosure invariants. Invalid values are never clipped, swapped, interpolated,
dropped to claim current coverage, or copied from another session or security.

One immediate content refetch is allowed after a malformed HTTP-success response. A valid second
response is `PROVIDER_REFETCH_RECOVERED`. Repeated identical malformed specimens are
`STABLE_BAD_SOURCE`; differing malformed specimens are `INTERMITTENT_BAD_SOURCE`. Both unresolved
classes remain `INVALID`. Transport retry policy remains separate and bounded.

Acquisition telemetry records provider, ticker, timeframe, adjustment mode, first bad stage,
violation, sanitized OHLC specimen, row and payload fingerprints, refetch outcome, and aggregate
validated/invalid/recovered/unresolved counts. No ticker-specific bypass exists.

