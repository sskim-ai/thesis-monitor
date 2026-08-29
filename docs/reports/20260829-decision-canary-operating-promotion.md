# Decision Canary Operating Promotion

Status: `PASS`

Promotion occurred only after focused/full tests, Ruff, diff, documentation, and exact-SHA CI
passed. The promoted lineage contains:

- instruction: `c62ddff`
- implementation: `a639d326a578bb7f3a2c53b1df31723bfb2b9829`
- validated report/persistent-state commit at activation: `3131b56a08bd30afa7f4aee55163d6065d3e826b`
- final documentation commit: resolve from Git; this report does not self-reference its SHA

Operating configuration after promotion:

- `DECISION_ENGINE_CANARY_ENABLED=true`
- `DECISION_ENGINE_STATE=canary`
- KR subjects exactly `003690,000660`
- US subjects exactly `GOOGL,RXRX`
- continuity state installed under the existing decision-canary archive path
- global decision block disabled
- Production Assist OFF

Operating verification after activation returned `enabled=true`, `state=canary`, exact configured
subjects, and continuity state `canary` with four entries. The first state-install invocation lacked
the repository import path and exited before writing; the corrected `PYTHONPATH=.` invocation
installed all four entries and returned PASS. The operating Git checkout remained clean and equal
to origin/main.

No task schedule, Public Action, output schema, database, assessment, fallback contract, Telegram
recipient, or automated-trading setting changes. No manual production message is sent. The first
proof must come from the next natural cycles.

GitHub Actions run `33244716691` passed Test and Lint on promoted main
`3131b56a08bd30afa7f4aee55163d6065d3e826b`. No API restart was needed because each Scheduled Task
starts a fresh CLI process and reads the operating environment at invocation time.
