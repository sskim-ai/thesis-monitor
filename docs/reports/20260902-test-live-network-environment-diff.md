# Test / Live Network Environment Diff

| Context | DNS/TLS | App server/model | First boundary |
|---|---:|---:|---|
| prior scheduler-context signed-in smoke | PASS | PASS | none |
| 2026-09-02 KR natural | FAIL | model not reached | DNS resolution |
| restricted test sandbox negative control | FAIL | not started | DNS resolution |
| 2026-09-02 host preflight after repair | PASS | PASS | none |

The natural log proves that binary discovery, signed-in state, runtime-state initialization, model
selection, and prompt submission happened before resolver failure. The host probe later passed in
one DNS/TLS attempt and one Codex transport attempt. The restricted test sandbox failed in three
bounded resolver attempts and correctly did not launch Codex.

`TEST_LIVE_NETWORK_FIRST_DIVERGENCE = scheduler_execution_resolver_availability`

No evidence supports changing `PATH`, `HOME`, `CODEX_HOME`, TLS trust, proxy settings, scheduler
ownership, or task timing. The repair therefore adds observation and bounded handling at the
existing owner instead of changing host networking.

