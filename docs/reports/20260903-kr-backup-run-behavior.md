# 2026-09-03 KR Backup Run Behavior

`BACKUP_BEHAVIOR = DEDUPE_SUPPRESSED`

## 16:20

- Scheduler observed at `16:20:01.866945+09:00`
- Analysis action: `reuse`
- Analysis status: `already_completed`
- Packet: `2026-09-03-kr-run-54-b081eb8a0619`
- Artifact set: deterministic messages only
- Delivery receipt: absent
- Actual sent count: 0
- Kiwoom market-context calls: 42/42 success

This was not `NOOP_PRIMARY_ALREADY_DELIVERED`: the 16:05 AI-assisted candidate was still unsent. It was an analysis dedupe/reuse path that did not produce a duplicate delivery.

## 16:50 And 17:10

The 16:50 invocation also reused run 54 and created packet `78ed269de3df`. The 17:10 fallback scheduler selected that held packet and sent its deterministic market + KR8 set, 9/9.

The semantic text set of all three deterministic artifacts is identical after removing packet/delivery metadata. No ticker was sent twice and no V2 message was sent alongside fallback.

