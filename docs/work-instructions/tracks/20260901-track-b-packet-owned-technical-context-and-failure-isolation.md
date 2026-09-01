# Track B — Packet-Owned Technical Context + Failure Isolation

Move validated OHLCV + D/W/M technical features into a packet-owned immutable technical-context artifact.

V2 decision stage consumes the packet artifact and does not make a fresh critical local HTTP fetch.

Preserve:
- no lookahead
- completed-bar semantics
- Price Structure semantics
- existing technical formulas

Add:
- FULL / PARTIAL_SAFE / UNAVAILABLE / INVALID
- timeframe-aware freshness
- approved current-safe cache policy
- subject-level isolation
- systemic outage degradation without automatic cohort death
- explicit timing insufficiency when technicals materially unavailable

Technical numerical parity is mandatory.
