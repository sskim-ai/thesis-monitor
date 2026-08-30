# V2 Production Feature State

Operating feature state after main promotion:

```text
VISIBLE_STOCK_DECISION_ENGINE = V2_ACCEPTED
V2_PRODUCTION_ENABLED = true
FULL_MONITORED_STOCK_COVERAGE_TARGET = true
V1_VISIBLE_DECISION_ENGINE = false
V1_ROLLBACK_AVAILABLE = true
PRODUCTION_ASSIST = OFF
```

Only the four owned V2/rollback keys were atomically updated in the existing secret path. No raw
recipient value was read into a report or repository. Settings validation and
`v2_accepted_production_armed()` both return true.

The API and OHLCV LaunchAgents remain running and both `/health` endpoints return `ok`. A restart
was unnecessary because natural review jobs launch fresh Python processes from the operating
checkout. No Scheduled Task was manually run.
