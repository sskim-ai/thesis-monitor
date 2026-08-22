# KR Producer Repair Validation

- Instruction commit: `2125562a863d858ee1ab62675c31c7c13be33506`
- Implementation commit: `c26c9359b134df0a4cd697fd97e7616cc508e885`
- Focused producer/XKRX/daily tests: 50 passed
- Full pytest: 1,406 passed, 1 deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Packet failure and retry idempotency: PASS
- Pending semantics and fallback zero-send: PASS
- Reconciliation dry-run/apply/idempotency fixtures: PASS
- Production DB-copy reconciliation: PASS
- Run-33 counterfactual replay: PASS
- Weekend/holiday/normal-session matrix: PASS
- Existing AI retry/fallback suite: PASS
- Inventory / Phase 9.0E integration regression: PASS
- XKRX/KRX/night regression: PASS
- Investment Knowledge v3 / Chart Knowledge v1 parity: PASS via full suite
- Public Action: `0.4.5`; operationId: `20/20` unique; schema: `4`
- Implementation Actions: run `32565412721`, Test/Lint PASS

Schedules, Public Action, schema, Inventory selector, Trade AR, cash flow, investor flow, KRX
telemetry, night futures, message content, and Production Assist configuration changed 0.
