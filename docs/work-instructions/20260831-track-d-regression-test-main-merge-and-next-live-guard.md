# Track D — Regression, Main Merge, and Next-Live Guard

Reproduce the 2026-08-31 failure:
incomplete new KR/US subjects previously blocked KR v2 globally.

Require repaired behavior:
- market isolation
- subject fail-closed
- peers continue
- pre/post cutoff semantics
- idempotency

Run non-production test sink for all eligible current KR/US subjects.

No production resend of 2026-08-31 KR messages.
No scheduler change.

Merge only after P0/P1 = 0/0 and all readiness gates PASS.
