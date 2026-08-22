# KR Producer Root Cause

## Incident

- Natural run: `daily_kr` run 33, 2026-08-22 Saturday
- Expected but absent packet: `2026-08-22-kr-run-33-c2491c2e78ad`
- Analysis: 7/7 success; provider activity occurred
- Unsent delivery rows: seven stocks plus one KR digest marker
- Producer attempts: 16:05, 16:20, 16:50; all ended with the same traceback

## Exact Path

1. `ops/com.seungsoo.thesis-monitor.kr-close.plist` invoked
   `python -m app.jobs.monitor_daily --market kr` without a session guard.
2. `monitor_daily._run_market_job` entered KR-close collection and `run_daily_monitor`.
3. `run_daily_monitor` created run 33, called providers, persisted seven assessments, and queued
   notification rows before packet creation.
4. `try_write_ai_review_packet` returned `not_ready` with a computed packet ID because the shadow
   cohort gate was false; no inbox file was written.
5. The old job tested only `packet_result.packet_id`, then called
   `hold_ai_assisted_pilot_session`.
6. Hold attempted to read the absent inbox file and raised `FileNotFoundError`.
7. Later producer attempts reused run 33 and the unique notification rows, then repeated the same
   missing-packet failure.

The earliest missing guard was the top of `_run_market_job`, before `_analysis_decision`, KR-close
collection, providers, `MonitorRun`, and notification creation.

The KR Codex primary/backup stayed safe because packet claim scans immutable inbox files and found
none. KRX 16:05 stayed safe because its independent `krx_same_day_publication` role target already
returned `no_valid_role_target` before provider access.

## Repair

`kr_daily_production` now resolves through `xkrx-role-target-v1` before any stateful work. KR pilot
notifications are disabled during analysis and created only after an actual packet file exists.
Packet-not-ready returns a structured zero-delivery result instead of entering hold.
