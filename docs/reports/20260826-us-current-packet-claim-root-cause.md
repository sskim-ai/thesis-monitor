# 2026-08-26 US Current Packet Claim Root Cause

## Natural Evidence

- Target completed session: `2026-08-25`
- Current packet: `2026-08-26-us-run-39-d55fe527c8e9`
- Current packet ready: `08:20:05.947023 KST`
- Primary claim activity: `08:20:43 KST`
- Backup current-packet validation complete: `08:42:13.004674 KST`
- Deadline fallback start: `08:40:05.020926 KST`

The primary worker claimed a pending run-37 packet before run-39 existed. `claim_next_ai_review_packet()` deduplicated by market, assessment date, and monitor run, then sorted newest eligible inbox candidates, but it did not require the packet's completed US target session to equal the session expected at claim time.

Consequences:

- `STALE_PENDING_PACKET_CLAIM = 1` before repair.
- The old packet consumed the primary canary opportunity and failed validation.
- The backup later claimed the correct run-39 packet, but its successful validation finished about 128 seconds after fallback started.
- Delivery remained safe and exactly once; this was an ownership/timing P1, not a duplicate-send P0.

Root cause: missing target-session identity at the claim boundary, not an inadequate fallback grace period.
