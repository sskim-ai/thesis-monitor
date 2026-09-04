# Live-Path E2E Contract

The rehearsal uses the real modules and persistence boundaries:

1. `python -m app.jobs.monitor_daily --market kr`
2. persisted SQLite notification rows and normal packet paths
3. normal claim and daily-review validator CLI
4. real signed-in Codex CLI V2 generator with `gpt-5.6-sol / xhigh`
5. normal selector, renderer, runtime-quality gate, and enqueue transaction
6. a separate `retry-delivery` process
7. the real Telegram adapter redirected to the existing dedicated TEST sink
8. real backup entrypoint and fallback CLI checks

Production data was copied to an isolated root and a consistent SQLite backup was used. All live
providers were disabled. Recipient values and tokens are absent from artifacts. Production
recipient send, production state mutation, manual Scheduled Task, and main merge are all zero.

The accepted V2 model artifact was generated on the same frozen E2E packet. After a validator claim
refresh, its top-level claim binding was replaced and revalidated; the original artifact and SHA
are retained. This is reported as real-model artifact reuse, not as an untouched single-claim run.
