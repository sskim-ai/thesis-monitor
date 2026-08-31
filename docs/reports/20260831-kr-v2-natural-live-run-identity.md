# 2026-08-31 KR V2 Natural Live Run Identity

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

## Canonical identity

- Run ID: `48`
- Packet ID: `2026-08-31-kr-run-48-a573c2a6f245`
- Canonical session date: `2026-08-31`
- Final packet generated: `2026-08-31T07:50:06.417917+00:00`
- Monitor run: `2026-08-31 07:05:31.472545` to `2026-08-31 07:06:34.540324` UTC; status `success`; 8 success / 0 failure
- Final packet evidence path: `data/ai_review/inbox/2026-08-31-kr-run-48-a573c2a6f245.json`
- Natural producer snapshots: `0de633eaaafa` at 16:06 KST, `0c3a0caa46a2` at 16:20 KST, final `a573c2a6f245` at 16:50 KST

## Natural ownership timeline

| Stage | KST | Result |
| --- | --- | --- |
| KR producer initial | 16:05 slot; monitor completed 16:06:34 | 8/8 monitoring success |
| KR primary AI claim | 2026-08-31T16:16:09.010+09:00 | no_pending_packet:no_eligible_unclaimed_packet; exit 0 |
| KR producer refresh | 16:20 slot | packet refreshed; still profile-gated |
| KR producer final | 16:50 slot | canonical packet 2026-08-31-kr-run-48-a573c2a6f245 |
| KR backup AI claim | 2026-08-31T16:57:11.283+09:00 | no_pending_packet:no_eligible_unclaimed_packet; exit 0 |
| Fallback dispatcher | 2026-08-31T17:10:07.170731+09:00 | deterministic fallback selected |
| First delivery | 2026-08-31T17:10:09.430568+09:00 | market digest |
| Last delivery | 2026-08-31T17:10:19.733510+09:00 | eighth stock message |

`KR_PACKET_CLAIM_TIME = NOT_CLAIMED`. Both scheduled claims found no eligible packet because the final packet had `ready_for_ai=false`; neither task owned or mutated a claim.
