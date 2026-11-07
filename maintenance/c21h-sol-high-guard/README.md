# C21H fresh one-subject issuance

This runner starts from PR30's corrected control-response path policy. The
existing `TASK` literal selects the pinned Sol/High guard capability; it is not
the logical run, invocation, thread, approval, or ledger identity. Rust
`scope_matches` validates an immutable, digest-pinned fresh scope root and its
exact ledger; `reserve` binds the stage, thread, request, account, source and
input, and denies repeats. C21H adds an independent run ID, fresh request,
empty runtime, absent journal, frozen current approval and an exclusive start
marker. The old scope/approval/journal/ledger is never used as an execution grant.

`maintenance.c21h_sol_canary --execute-once` requires `TM_C21H_TASK_ROOT`, a
prepared private scope, code freeze, and a separate current user approval.
The default path does not run. It reuses the original AnalysisView, manual
host, StageController, parent restore and dated NO-SEND consumer. There is no
retry or initialization-continuation mode. It stops at the first actual failure.

The four dated valuation facts and all original restrictions remain unchanged.
Financial HTTP, operating DB, sending and scheduling are outside this runner.
The original C21G host binary and control receipt isolation proof are reused;
there is no Rust build or repeated full suite. Three focused tests cover fresh
paths, stale grants and unchanged capability binding. Actual live acceptance
must be reported separately from these tests.
