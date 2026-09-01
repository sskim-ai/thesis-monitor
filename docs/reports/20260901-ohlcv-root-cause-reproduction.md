# OHLCV Root-Cause Reproduction

## Result

`OHLCV_PRIMARY_ROOT_CAUSE = PROCESS_NAMESPACE_MISMATCH`

Run 49 reached `accepted_decision_v2_runtime.prepare_context` after the source monitor had already
completed 14/14 subjects. That function opened a new local `httpx` connection to
`127.0.0.1:8765`; the restricted process returned `httpcore.ConnectError` before any candidate was
generated.

The lower-level cause was reproduced on 2026-09-01 KST:

- LaunchAgent `com.seungsoo.ohlcv-analyst`: running, `KeepAlive=1`, `RunAtLoad=1`.
- LaunchAgent bind: `127.0.0.1:8765`.
- application configuration: `http://127.0.0.1:8765`.
- approved host health call: `{"status":"ok"}`.
- data probe: CPNG resolved, latest daily bar `2026-08-31`.
- restricted Python `httpx` call: `ConnectError: [Errno 1] Operation not permitted`.

This rules out service-not-running and host/port mismatch. Contributing factors were a duplicate
decision-stage fetch, no packet-owned technical artifact, and cohort-wide exception propagation.

`ROOT_CAUSE_ASSUMED_WITHOUT_REPRODUCTION = 0`
