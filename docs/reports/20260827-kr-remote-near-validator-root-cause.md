# KR Remote-Near Validator Root Cause

The prior gate asserted engine state but did not bind final rendered labels back to zone provenance.
The new validator compares every structured SR line with a numeric binding carrying `fact_ref`,
`proximity_tier`, `active_relevance`, and distance/source metadata. It rejects ineligible near,
major, or long-horizon labels, unbound lines, duplicate user-visible semantics, and one zone owning
multiple SR semantics.

The supplied old 000660 section fails as expected under this validator.
