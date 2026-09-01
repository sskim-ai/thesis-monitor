# OHLCV Secondary Source Recovery

Contract: `ohlcv-secondary-exact-row-recovery-v1`

A secondary row may replace one known-bad primary row only when provider production approval,
security identity, session, currency, adjustment basis, timestamp, scale, date, and OHLC integrity
all pass. The result preserves primary and secondary fingerprints plus recovery provenance.

The contract forbids whole-series replacement for one bad row, cross-provider averaging, corporate
action basis guessing, and unapproved or paid source introduction.

The current repository has no runtime-approved secondary historical OHLCV adapter. Massive is
limited to shadow market internals, and Alpha Vantage has no implemented historical OHLCV adapter.
The production outcome is therefore `NO_APPROVED_SECONDARY_SOURCE`; feature-scoped validity and
fail-closed finality remain the recovery mechanisms.
