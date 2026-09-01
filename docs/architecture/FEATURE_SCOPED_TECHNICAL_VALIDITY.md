# Feature-Scoped Technical Validity

## State Separation

The pipeline keeps `provider_raw_integrity`, `bar_finality`, `timeframe_quality`, `feature_quality`,
and `technical_aggregate_state` separate. One boolean cannot replace these states.

An invalid historical row is retained and fingerprinted. Finite facts whose exact dependency starts
after that row may remain safe; recursive facts whose initialization spans it are absent and listed
as blocked. `FULL` is never assigned while configured facts remain blocked.

## Aggregate Semantics

- `FULL`: all configured current technical facts are safe.
- `PARTIAL_SAFE`: at least one material fact/timeframe is safe and usable while another component
  is stale, unavailable, unconfirmed, or invalid.
- `UNAVAILABLE`: no safe facts were acquired.
- `INVALID`: no safe fact can be used because integrity, identity, or comparability fails across the
  available context.

V2 receives only facts from a timeframe with `usable_for_current_reasoning=true`. Component-level
invalid states and cautions remain visible, so aggregate partial coverage cannot hide an invalid
daily or weekly component.
