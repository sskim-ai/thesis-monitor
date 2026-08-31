# Incident Replay: KR Global Gate

Old behavior: incomplete 047810 and CPNG entered the global active profile gate and suppressed KR V2.

Repaired fixture: incomplete subjects are pending, target-market selection runs first, and ready peers continue. A profile that disappears after activation is excluded as `company_profile_not_ready_at_packet_cutoff` without suppressing other ready subjects.

`INCIDENT_20260831_REPLAY = PASS`.

- Master instruction commit: `8da71e7`
- Base: `ecd01297f81d0b68aaf95ecfe866721b6aa2c104`
- Implementation: `2c4b973`
- Active / ready-active / active-incomplete: `21 / 21 / 0`
- 047810: `ACTIVE_READY`; blockers: `none`
- CPNG: `PENDING_SAFE`; blockers: `INITIAL_EVIDENCE, INITIAL_BASELINE_ASSESSMENT, DECISION_READINESS`
- Test sink: `22/22`; exact: `TRUE`
- Local validation: `PASS`
- CI: `PASS`
- CI run: `33385383279`
