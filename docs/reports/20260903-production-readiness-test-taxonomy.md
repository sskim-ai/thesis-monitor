# Production Readiness Test Taxonomy

## Unit and contract

Use for state transitions, identity generation, quality receipt integrity, late validation,
fresh-session retry, dry-run reactivation, partial send safety, nine-row fallback, and owner
preservation. These tests may prove mechanics but cannot prove a live adapter or natural scheduler.

## Live-path E2E

Requires the real production entrypoint, normal paths, persistent DB, real selector/quality gates,
signed-in model path when applicable, process boundary, real TEST delivery adapter, backup/dedupe,
and fallback checks. It is a controlled TEST proof, not natural production proof.

## Natural production

Only the ordinary LaunchAgent cycle may establish natural live proof. Review is read-only. No
manual task or resend may be used to fill a missing natural receipt.

Reports that only render a packet or replay a candidate must be labeled `PACKET_REPLAY`,
`RENDERER_REPLAY`, or `MODEL_REPLAY`, never production-equivalent.
