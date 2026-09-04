# US Primary State at 08:20

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Classification

`PRIMARY_STATE_AT_0820 = RUNNING_ACTIVE`

Direct session events bracket `08:20`: a primary tool output was recorded at `08:20:00.125 KST`, another tool invocation at `08:20:15.365`, and continuous reasoning/tool activity followed. At `08:21:18.264` the primary explicitly reported that packet gates passed and all 14 US securities were present.

No PID or heartbeat key was persisted for the outer Codex automation, so PID-level liveness is `MISSING_FROM_NATURAL_ARTIFACTS`. Session event activity is sufficient to reject `PROCESS_MISSING`, `NOT_STARTED`, and `RUNNING_STALLED`.

At `08:20:04.232304`, the component that ran was the fourth daily producer attempt. It reused monitor run 55 and retained `held_for_ai_review`; it did not inspect primary process state.
