# Pending Versus Retry Root Cause

## Root cause

`_queue_scoped_notifications` treated analysis reuse as a new delivery generation. It overwrote
the packet-bound AI metadata on rows already owned by the primary accepted generation.
`hold_ai_assisted_pilot_session` only preserved metadata for an exact packet ID. The backup packet
therefore moved the rows from `ai_assisted_pending` to `held` under a different packet.

The outer pending scanner saw held rows, but `retry_pending_ai_assisted_deliveries` accepted only
rows whose inner state was `ai_assisted_pending`. Its result was `no_pending_ai_delivery` even
though the primary archive reported pending `9`.

## Repair

- All AI-owned states preserve the original owner across analysis reuse.
- Retry discovery and execution share the same persisted state vocabulary.
- A fresh DB process discovers `packet_bound_pending_hold`, `held`, and `ai_assisted_pending`.
- A dry-run outer status may be reactivated only when metadata is AI pending and the new process is
  explicitly non-dry-run.
- Machine-readable stage receipts record pending, discovery, claim, send, fallback, and dedupe.

Focused tests cover analysis reuse, fresh Session recovery, dry-run process transition, and the
original pending/retry split.
