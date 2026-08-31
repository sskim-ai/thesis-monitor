# Market Cohort Readiness Contract

Selection key: `market + session + packet cutoff`. Pending US subjects are absent from KR evaluation and vice versa. Pending subjects in the same market are excluded while eligible peers proceed.

Incident fixture: ready US peer `PACKETUS` remains selected while `CPNG` is pending; KR `047810` is outside the US cohort. The equivalent KR/US directions are covered by the universe tests.

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
