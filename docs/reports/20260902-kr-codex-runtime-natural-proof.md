# KR Codex Runtime Natural Proof

Both natural claims created decision-v2 context for all eight subjects and launched signed-in Codex CLI `0.148.0-alpha.9` in read-only mode with model `gpt-5.6-sol` and reasoning effort `xhigh`.

The claim-scoped runtime-state preflight and CLI/app-server startup passed far enough to emit the runtime header and submit the model request. The model transport then failed DNS resolution to `chatgpt.com`; WebSocket retries, HTTPS fallback, and bounded network waits exhausted before each task was interrupted.

- `KR_CODEX_RUNTIME_STATE_PREFLIGHT = PASS`
- `KR_CODEX_APP_SERVER_INITIALIZATION = PASS`
- `KR_V2_MODEL_CALL_REACHED = true`
- model response returned: `false`
- root cause: `NETWORK_DNS_TRANSPORT_FAILURE`
