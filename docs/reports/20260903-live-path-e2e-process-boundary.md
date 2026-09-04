# Live-Path E2E Process Boundary

The validator process persisted nine AI-pending rows and exited. A separate retry CLI process
opened a fresh DB session, discovered the nine obligations, and invoked the normal delivery
function. The transition receipt contains `delivery_discovered_by_retry` with count `9`.

The isolated validator initially used dry-run transport. Its outer row status was `dry_run` while
authoritative AI metadata remained `ai_assisted_pending`. The repair permits reactivation only when
the later process is explicitly non-dry-run. A dedicated unit test covers this transition.

After send, a third process recovered the missing archive marker from terminal rows. It recorded
`archive_completion_recovery=true`, `telegram_resent=false`, analysis/packet/renderer rerun false,
and sent count `9` from persisted state.
