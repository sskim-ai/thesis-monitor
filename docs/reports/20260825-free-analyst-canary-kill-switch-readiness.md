# Free Analyst Adaptive Canary Kill-Switch Readiness

The independent rollback is supported by the existing Settings contract:

```text
FREE_ANALYST_ADAPTIVE_ENABLED=false
FREE_ANALYST_ADAPTIVE_MODE=current
```

Config validation and focused tests prove that this state makes
`free_analyst_adaptive_kill_switch_open()` and `free_analyst_adaptive_canary_armed()` false while
leaving the existing Pilot and deterministic delivery path active. The live switch was not toggled
off/on merely for demonstration before a scheduled run.

Rollback requires no schema, database, receipt, schedule, Inventory, cash-flow, or stored
investment-logic change. The next scheduled CLI process reads the disabled state; the API may be
restarted only if its cached Settings must reflect the change. Expected operational recovery is one
bounded config edit plus process reload.

`KILL_SWITCH_READINESS=PASS`.
