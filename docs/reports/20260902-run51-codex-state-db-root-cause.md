# Run-51 Codex State DB Root Cause

Run-51 primary and backup both passed the repaired absolute-path preflight and launched the Codex
subprocess, but neither reached model transport. The first failure was app-server initialization
against `<SIGNED_IN_CODEX_HOME>/state_5.sqlite`, which was read-only in the natural scheduler
process context.

The prior report grouped this under model transport. The corrected classification is
`LOCAL_RUNTIME_PRE_MODEL_FAILURE`, specifically
`CODEX_APP_SERVER_INITIALIZATION_FAILED_READONLY_STATE_DB`.

The repair creates private claim-scoped `CODEX_HOME` and `CODEX_SQLITE_HOME` roots, references the
existing owner-only signed-in auth file without copying it, and proves SQLite WAL write/read/rename
before invoking the model. Root execution, world-writable state, global sandbox disablement,
manual database edits, and plaintext auth copies are all zero.

- `PRE_MODEL_STATE_FAILURE_MISCLASSIFIED_AS_MODEL_TRANSPORT = 0`
- `CODEX_RUNTIME_STATE_PREFLIGHT = PASS`
- `CODEX_PRIMARY_BACKUP_STATE_CONCURRENCY = PASS`
