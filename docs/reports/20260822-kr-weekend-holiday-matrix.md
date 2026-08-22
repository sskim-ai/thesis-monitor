# KR Producer Weekend And Holiday Matrix

| Case | Target | Eligible | Analysis/providers | Packet/intents | Telegram | Exit |
| --- | --- | --- | --- | --- | --- | --- |
| Sat 2026-08-22 | none | no | 0 / 0 | 0 / 0 | 0 | safe no-op |
| Sun 2026-08-23 | none | no | 0 / 0 | 0 / 0 | 0 | safe no-op |
| Holiday 2026-08-17 | none | no | 0 / 0 | 0 / 0 | 0 | safe no-op |
| Consecutive holiday 2026-09-24/25 | none | no | 0 / 0 | 0 / 0 | 0 | safe no-op |
| Normal Mon 2026-08-24 | same day | yes | normal | packet-bound | normal contract | normal |
| Day after holiday 2026-08-18 | same day | yes | normal | packet-bound | normal contract | normal |
| Special closure 2026-12-31 | none | no | 0 / 0 | 0 / 0 | 0 | safe no-op |

The 16:05, 16:20, and 16:50 producer entries independently return the same result on a no-target
date. Raw packet-less rows are ignored by 16:22/16:25/16:30 retry checks, and 17:10 returns
`no_held_session`, pending count 0, sent count 0. Schedules were not changed.
