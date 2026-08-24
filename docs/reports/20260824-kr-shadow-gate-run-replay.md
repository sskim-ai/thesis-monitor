# Run-36 KR Shadow Gate Replay

## Natural Source

- Run ID: 36
- Assessment date/market: 2026-08-24 / KR
- Natural computed packet ID: `2026-08-24-kr-run-36-b82af21dfde3`
- Analysis: 7/7 success, failure 0
- Target: completed valid XKRX session
- Before result: `packet_not_ready / shadow_cohort_activation_gate_failed`
- Packet artifacts/intents/sent: 0 / 0 / 0 of 8
- Primary/reuse/backup: all denied before packet persistence
- Retry/fallback: `no_pending_ai_delivery` / `no_held_session`

The failure prevented an immutable packet from existing. Therefore the natural packet ID and run log
are authoritative, while detailed gate fields below are a read-only reconstruction from an SQLite
backup and stored sidecars. No claim is made that mutable backing evidence reproduces the absent
packet byte for byte.

## Repaired No-Send Replay

- Replay packet ID: `2026-08-24-kr-run-36-4a057f187da2`
- Production decision: eligible; all five conditions PASS
- Shadow decision: ineligible; `shadow_numeric_semantic_gate_not_ready`
- Profile gate: ready
- Numeric registry: 1,443 entries, 1,233 registered, 210 unsupported
- Packet persisted: 1
- Packet-bound intents: 8, digest 1 plus stock 7
- Held/fallback eligible: 8/8
- Duplicate packet/intent after retry: 0/0
- AI claim: suppressed while `ready_for_ai=false`
- AI/fallback pipeline: fallback reachable
- Telegram sent in replay: 0

The replay changed only `/tmp` copies. Provider calls, production DB/Pilot, source archives, and
Telegram were untouched.
