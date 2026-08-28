# Track C — US-Only Price Structure Enablement

Precondition: full-universe replay/test PASS, P0/P1 = 0/0.

Promote latest validated code with US Price Structure OFF.
Prove feature-off parity.

Then enable Price Structure only for current monitored US/foreign stocks.

Keep:
- KR runtime unchanged
- US morning market digest unchanged
- Production Assist OFF

Run full-universe post-enable smoke.

Final pre-natural state:
`US_PRICE_STRUCTURE = ENABLED_AWAITING_NATURAL_PROOF`.
