# Monitoring Onboarding State Machine

Implemented states: `PENDING_ONBOARDING`, `READY`, `ACTIVE`, `ONBOARDING_FAILED`, and `INACTIVE`. Registration writes pending; coordinator promotion requires all seven readiness categories. Deactivation preserves history and sets `INACTIVE`.

Idempotent retry keeps one watchlist identity, one security identity, thesis version history, and existing assessments.

- Master instruction commit: `8da71e7`
- Base: `ecd01297f81d0b68aaf95ecfe866721b6aa2c104`
- Implementation: `2c4b973`
- Bounded operational repair: `6521d50`
- Active / ready-active / active-incomplete: `21 / 21 / 0`
- 047810: `ACTIVE_READY`; blockers: `none`
- CPNG: `PENDING_SAFE`; blockers: `INITIAL_EVIDENCE, INITIAL_BASELINE_ASSESSMENT, DECISION_READINESS`
- Test sink: `22/22`; exact: `TRUE`
- Local validation: `PASS`
- CI: `PASS`
- CI run: `33386496321`
- Operating convergence: `14 -> 21` active
- Runtime activation SHA: `6521d509c0598838543d6981f4905ebf5f8e153c`
