# KR Fresh Live Rehearsal Registration

- Instruction path: `docs/work-instructions/20260824-1925-kr-fresh-live-rehearsal-no-delivery.md`
- Instruction version: `1.0`
- Instruction commit: `91d4e113670e9d350c5ce88c16f42499f2ebed39`
- Execution base: `91d4e113670e9d350c5ce88c16f42499f2ebed39`
- Previous main/operating: `96825de767f8ff25b59ab4451df305df5dd873cc`
- Branch: `codex/20260824-kr-fresh-live-rehearsal`
- Rehearsal ID: `2026-08-24-kr-live-rehearsal-193419`
- Run type: `MANUAL_LIVE_REHEARSAL_NO_DELIVERY`
- Created/cutoff at KST: `2026-08-24T19:34:19+09:00`
- Market: `KR`
- Source mode: `fresh_read_only`
- Delivery mode: `disabled`
- XKRX target: `2026-08-24`, completed and eligible
- Rehearsal packet: `2026-08-24-kr-run-36-51d4359299cd`
- Packet namespace: isolated `/tmp` data root; production packet path absent

This is a 19:34 fresh rehearsal, not a 16:15 reconstruction. The run-36 natural failure remains
immutable and no rehearsal value may be written into its packet, receipt, or delivery history.

The collection process used a production SQLite backup and copied canonical files under
`/tmp/thesis-monitor-kr-rehearsal-20260824-193419`. Provider retrieval ran as a staged pass after
the fixed cutoff, with provider telemetry and source observation/as-of fields retained. Production
DB, packet archives, Pilot state, and schedules were never opened for writes.
