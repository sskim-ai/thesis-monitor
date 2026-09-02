# Track A — Codex Natural Runtime-State Parity Repair

## Goal

Fix run-51's pre-model failure:

`CODEX_APP_SERVER_INITIALIZATION_FAILED_READONLY_STATE_DB`

without unsafe chmod/root/secret copying.

## Required investigation

Compare natural primary, natural backup, passing preflight/test-sink:
- UID/GID/groups
- HOME / CODEX_HOME / state-home semantics
- cwd/PATH/TMPDIR/umask
- CLI binary/version
- exact state DB and parent
- owner/mode/ACL/flags
- WAL/SHM/journal write requirements
- mount/sandbox/process namespace
- scheduler wrapper/env allowlist

Find:
`TEST_LIVE_CODEX_STATE_FIRST_DIVERGENCE`.

## Repair

Use the smallest supported runtime-state ownership/environment fix.

Do not:
- chmod 777
- run as root
- copy plaintext auth
- globally disable sandbox
- manually edit Codex DB tables

Add:
- local runtime-state readiness classification
- pre-model observability
- scheduler-context non-production app-server probe

The probe must use the same natural service environment and be unable to deliver to production.

## Proof

- scheduler-context app-server probe PASS
- primary/backup concurrency PASS
- run-51 frozen V2 replay reaches model
- candidate 14/14
- no production send
