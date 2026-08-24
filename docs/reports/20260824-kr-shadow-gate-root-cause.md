# 2026-08-24 KR Shadow Gate Root Cause

## Finding

`ROOT_CAUSE_BRANCH = C`

Run 36 completed all seven KR assessments, but `write_ai_review_packet()` returned
`shadow_cohort_activation_gate_failed`. The producer correctly created no packet-bound delivery
intent after that denial, so the 16:15 primary, retries, 16:55 backup, and 17:10 fallback had no
reachable session. Sent count was 0/8, duplicate count 0, and new orphan count 0.

The failing shadow condition was numeric-semantic cohort readiness. Reconstructing the run exposes
210 unsupported numeric paths: seven tickers, three horizons, and ten investor-flow reconciliation
audit fields per horizon. The fields are valid internal reconciliation diagnostics, but are not
registered for AI prose. Company-profile coverage is 20/20.

## Why It Was Wrong

Commit `108a93721d267e8c6e1acf0693aa1e1e8e9bb6b4` introduced the gate for Daily Review v3.2 Shadow
activation. Its report says a packet is claimable only after profile and numeric registry coverage
passes. Later packet-before-intent delivery architecture made the inbox packet a prerequisite for
both AI and deterministic fallback. The old write guard therefore converted an AI-only readiness
failure into a production outage.

The numeric gate must still block AI claims. It must not erase a production-safe deterministic
packet when fallback is available.

## Repair Surface

- `app/services/ai_review_service.py`: separate shadow readiness from production persistence,
  isolate shadow exceptions, and make packet identity independent of shadow state.
- `tests/test_ai_review_service.py`: positive isolation, true production blockers, idempotency,
  Inventory-only, and write-failure fixtures.
- `tests/test_kr_producer_delivery_integrity.py`: packet ordering and fallback reachability when
  shadow is suppressed.

Implementation SHA: `64086c4af7735dcbe2fd3f5093f4167952a280e0`.
