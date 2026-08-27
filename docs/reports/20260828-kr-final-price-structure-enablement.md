# KR Final Price Structure Enablement

`KR_PRICE_STRUCTURE_ENABLED = true`

The second-stage smoke rebuilt all seven monitored KR subjects: 7/7 `ELIGIBLE_SR_ONLY`, unsafe
target/stop 0, look-ahead 0, partial-bar pivot 0. The US negative control remained blocked by the
KR market-scope guard.

Rollback: set `KR_PRICE_STRUCTURE_V3_ENABLED=false` in the canonical environment and restart the
service. TOP3 may remain independently enabled.
