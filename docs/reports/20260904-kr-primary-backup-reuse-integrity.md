# 2026-09-04 KR Primary / Backup / Reuse Integrity

## Primary

- Packet `2026-09-04-kr-run-56-ea785fbd2c9e`
- Claim `939e44d1-3e85-4b31-9a20-ab53bd742ad5`
- Regular accepted 9/9 and delivered 9/9.
- Primary V2 interrupted before a persisted candidate batch.

## Backup

- Packet `2026-09-04-kr-run-56-6a9ef43bb878`
- Different claim and packet identity; no primary candidate reuse.
- V2 accepted 8/8, `gpt-5.6-sol`, `xhigh`.
- Context-ready 17:02:31.994; accepted artifact 17:30:19.026 KST.
- Receipt: message quality PASS, 8 messages, 0 errors, 0 manual/unresolved numeric claims, 0 repeated substantive spans.
- Lease renewals 28; fencing preserved; schema repairs 1; candidate repairs 2.
- Transport/network probes 6/6; retry recovery 0.
- Production send 0; raw candidate visible 0.

## Result

- `REUSE_METADATA_INTEGRITY=NOT_APPLICABLE`: there was no same-packet primary-candidate reuse path to evaluate.
- Cross-packet identity integrity: PASS.
- Backup delivery state: `dedupe_complete`, count 9, `authoritative_delivery_already_sent`.
- No metadata copied across claim boundaries and no backup Telegram send.
