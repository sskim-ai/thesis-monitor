# Reporting Closeout Recovery

## Experiment outcome

- FIRST: `16/16`
- A: `16/16`
- B: `FAILED_0/16`
- C: `NOT_RUN`
- Readiness: `NOT_READY_TRANSPORT_TIMEOUT`
- Retirement reason: `INCOMPLETE_A_B_C_AFTER_FULL_COHORT_EXPOSURE`

## A to B ordering

A completed normally before B was requested. All eight A transport receipts passed with exit code 0 and parsed output, all eight output-identity checks passed, and all eight partial semantic audits passed with zero issues. The last A receipt completed at `2026-09-07T10:27:24.110484Z`; B Core batch 1 started at `2026-09-07T10:27:24.428058Z`, 0.317574 seconds later.

## B failure

B Core batch 1 reached the configured 1,800-second watchdog and exited with signal 15. It produced no stdout/output file, left no orphan process, created one terminal timeout receipt, and was not retried by the orchestration. Stderr records one Codex CLI internal sampling retry after a WebSocket disconnect. No capacity-error message was present, so model capacity failure is not proven; the primary classification is `WATCHDOG_TRANSPORT_TIMEOUT_AFTER_WEBSOCKET_DISCONNECT`.

## Report recovery

After the terminal B result was already persisted, the reused final-report helper raised `KeyError: registry_count` because the current merged registry report uses newer field names. A temporary report clone supplied factual compatibility aliases to the unchanged helper. Only the derived completion/state were copied back. No source proof, model output, prompt, schema, validator, candidate, architecture, or production behavior was changed, and no model call occurred during recovery.

The four original source-proof SHA-256 values are recorded in the companion JSON and remain unchanged.
