# Cross-Ticker Contamination Controls

047810 profile provenance is `opendart_company` and CPNG provenance is `sec_submissions`. The validator and profile adapter use exact ticker/security rows; no peer profile or assessment is copied.

Test messages are generated from each ticker's own thesis and latest assessment. 047810 does not inherit 012450 facts, and CPNG does not inherit another US consumer profile.

`CROSS_TICKER_ONBOARDING_FACT_CONTAMINATION = 0`.

- Master instruction commit: `8da71e7`
- Base: `ecd01297f81d0b68aaf95ecfe866721b6aa2c104`
- Implementation: `2c4b973`
- Active / ready-active / active-incomplete: `21 / 21 / 0`
- 047810: `ACTIVE_READY`; blockers: `none`
- CPNG: `PENDING_SAFE`; blockers: `INITIAL_EVIDENCE, INITIAL_BASELINE_ASSESSMENT, DECISION_READINESS`
- Test sink: `22/22`; exact: `TRUE`
- Local validation: `PASS`
- CI: `PENDING`
