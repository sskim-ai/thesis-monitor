# Track F — Fresh Issuer Holdout + FIRST/A/B/C

After architecture freeze:
select a completely new issuer-level holdout.

Exclude issuers from:
retired22
preflight11
prior unseen16
latest holdout16.

Target 16, preferably KR8/US8; allowed 12–20.

All must pass the frozen source-sufficiency gate.

Freeze one immutable source lock.

Run FIRST.
Only if ownership/schema/hard-safety/validator gates are clean:
run A, B, C on the exact same lock.

Measure Directional Core stability separately from Price-Timing stability.
