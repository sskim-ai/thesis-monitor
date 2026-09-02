# US Scheduler Ownership

| Owner | Schedule | Actual start | Actual end | State | Claim |
| --- | --- | --- | --- | --- | --- |
| source monitor | 08:05 | 2026-09-02T08:05:31.099249+09:00 | 2026-09-02T08:06:47.048664+09:00 | success | producer |
| codex-us-primary | 08:15 | 2026-09-02T08:16:53.822000+09:00 | 2026-09-02T08:32:45.078000+09:00 | PENDING_REVIEW | afd76205-7401-4912-a8a6-4711fd214e1b |
| codex-us-backup | 08:30 | 2026-09-02T08:30:53.840000+09:00 | 2026-09-02T08:36:37.338000+09:00 | PENDING_REVIEW | 47594101-6ad0-497e-962d-4c1b208f5fe4 |
| fallback dispatcher | 08:40 | 2026-09-02T08:40:06.555445+09:00 | 2026-09-02T08:40:25.203862+09:00 | sent | terminal |

The primary and backup claims were sequential. The terminal persisted outbox belongs to the backup claim; delivery attempts were one per message.

- `MULTIPLE_US_PRODUCERS_OWNED_SAME_PACKET = 0`
- `UNOWNED_US_RETRY = 0`
- `US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF = 0`
