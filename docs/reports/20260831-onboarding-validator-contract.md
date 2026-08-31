# Onboarding Validator Contract

Contract: `monitoring-onboarding-readiness-v1`. The output is persisted on the watchlist row and contains completed, blocking, and safe-unavailable requirements with stage-level evidence. Evaluation is read-only; only the coordinator applies state.

`PLACEHOLDER_PROFILE_COUNTS_AS_READY = 0` because the validator requires structured company fields as well as provenance.

- Master instruction commit: `8da71e7`
- Base: `ecd01297f81d0b68aaf95ecfe866721b6aa2c104`
- Implementation: `2c4b973`
- Active / ready-active / active-incomplete: `21 / 21 / 0`
- 047810: `ACTIVE_READY`; blockers: `none`
- CPNG: `PENDING_SAFE`; blockers: `INITIAL_EVIDENCE, INITIAL_BASELINE_ASSESSMENT, DECISION_READINESS`
- Test sink: `22/22`; exact: `TRUE`
- Local validation: `PASS`
- CI: `PENDING`
