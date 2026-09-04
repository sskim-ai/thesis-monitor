# 2026-09-04 US Claim Lease Renewal Contract

Claims now persist `owner`, `claim_id`, `fencing_token`, `claim_generation`, `lease_expires_at`, `last_heartbeat_at`, `last_renewed_at`, `heartbeat_count`, and terminal ownership state.

`renew_ai_review_claim` takes the packet lock and renews only when both owner and fencing token still match. Reclaim creates a new claim ID/fencing token and increments the generation. A stale owner receives `ownership_lost` and cannot renew or finalize.

The `_ClaimLeaseHeartbeat` daemon thread starts before model work, renews immediately, and continues at the configured 60-second interval while model, validator, and correction subprocess calls block the caller. It stops at the safe boundary and exposes ownership loss to the parent.

| Gate | Result |
|---|---|
| Claim renewal implemented | `PASS` |
| Owner match required | `PASS` |
| Fencing-token match required | `PASS` |
| Blocking-call heartbeat | `PASS` |
| E2E renewal count | `444` |
| E2E fencing token preserved | `PASS` |
| Static-duration-only repair | `0` |
