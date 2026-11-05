# Query-time monitoring price, explicit opt-in

`scoped-monitoring-capture-selection-v1` selects the original Kiwoom-backed
ohlcv-analyst chart Owner. It never inherits V1/V2's `us_completed_closes=True`.
Strict US close IDs must be explicitly selected; those slots are optional in
this profile. Legacy production plans still require all fourteen strict closes.

The original isolated Worker captures and replays original raw twice. Its new
monitoring command uses the original parser and unchanged OHLC inspector,
selects the requested latest chart window, and records collection/source dates
separately. The live Source-only issuer replays that exact Worker artifact and
returns a versioned source capability. Cold recomputes the snapshot and rejects
FINAL/strict-close promotion. Historical raw replay never reissues a live Owner.

The display adapter labels QUERY_TIME_SNAPSHOT and NOT_CLAIMED finality. It
requires exact security/basis. A malformed or ambiguous latest row is unavailable;
older invalid rows block the dependent window without replacing prices. Valid
snapshot values do not authorize valuation denominators, technical signals,
economics, Native, AI or sends. Those consumers retain original separate gates.

For usa20590 only, a uniquely targeted, fully sealed HTTP200 source with an
original recognized OHLC enclosure failure produces a typed quality denial.
The account slot finishes without STOP. No strict Owner is issued. All unknown,
transport, envelope, identity, hash, session and quota failures remain hard
denials/stops. A nonmatching wire rejected before IO now also reaches the
original account STOP rather than being mislabeled source quality.

Old STOP state has no unique durable cause field. The recovery-review entrypoint
locks and compares the original metadata but cannot authorize reset from a bad
row plus caller JSON. It deliberately has no state-reset executor until original
cause attribution and a separate approved recovery operation are available.
Installed release metadata, scheduler, live settings and production stay OFF.
