# Decision Canary Operating Promotion

Promotion is authorized only after focused/full tests, Ruff, diff, documentation, and exact-SHA CI
pass. The promoted lineage must contain:

- instruction: `c62ddff`
- implementation: `a639d326a578bb7f3a2c53b1df31723bfb2b9829`
- report/persistent-state commit: resolve from Git; this report does not self-reference its SHA

Operating configuration after promotion:

- `DECISION_ENGINE_CANARY_ENABLED=true`
- `DECISION_ENGINE_STATE=canary`
- KR subjects exactly `003690,000660`
- US subjects exactly `GOOGL,RXRX`
- continuity state installed under the existing decision-canary archive path
- global decision block disabled
- Production Assist OFF

No task schedule, Public Action, output schema, database, assessment, fallback contract, Telegram
recipient, or automated-trading setting changes. No manual production message is sent. The first
proof must come from the next natural cycles.
