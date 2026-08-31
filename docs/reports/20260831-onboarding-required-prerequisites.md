# Onboarding Required Prerequisites

| Requirement | Blocking rule |
|---|---|
| Identity | canonical ticker, company, exchange, market |
| Security master | canonical company/security IDs, venue, country, security and issuer type |
| Company profile | official provenance and structured industry/business identity |
| Investment logic | thesis, drivers, metrics, signals, expectations, valuation |
| Initial evidence | final baseline with price, valuation, and thesis snapshots |
| Initial baseline | current thesis-version baseline occurrence |
| Decision readiness | baseline observer, holder, risk, confidence context |

Depositary per-share basis may be safe-unavailable for issuer-level monitoring, but it remains blocked for per-share valuation.

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
