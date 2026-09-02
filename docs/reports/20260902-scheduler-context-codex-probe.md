# Scheduler-Context Codex Probe

The host scheduler-context probe used the production invocation helper, isolated state, signed-in
Codex, `gpt-5.6-sol`, `xhigh`, read-only sandboxing, and a strict one-field JSON schema. It reached
the model and returned the expected object.

The sanitized receipt records `PASS`, zero Telegram import/send, and zero database mutation. Raw
Codex logs and session identifiers are excluded from reports and the final bundle.

- App-server initialization: `PASS`
- SQLite WAL preflight: `PASS`
- Model reached: `PASS`
- Production send: `0`
