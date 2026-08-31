# Onboarding Readiness Root Cause

## Finding

Both registration paths set `active=true` before security, profile, baseline, and decision prerequisites were complete. The AI profile gate then evaluated the global active universe, so incomplete `047810` and `CPNG` could suppress an unrelated market and ready peers.

The first operating reconciliation exposed one bounded legacy selector defect: seven US subjects began with a provisional assessment followed by a final assessment, while the fallback selected the first row. Repair `6521d50` now selects an explicit initial baseline first and otherwise the earliest final legacy assessment. Coverage converged `14 -> 21` without relaxing any readiness requirement.

## Repair

Registration now records intent as pending, one validator owns activation, and packet readiness is scoped to a frozen market cohort. Profile loss is handled per subject.

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
