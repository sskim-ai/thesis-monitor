# Onboarding Idempotency

Repeated registration for the same normalized ticker preserves one watchlist row and does not create a second thesis version when the payload is unchanged. Pending retry keeps its original registration time. Existing ready subjects retain activation time on an identical request.

`ONBOARDING_IDEMPOTENT = PASS`.

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
