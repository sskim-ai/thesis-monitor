# US Primary Model Runtime

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Review authoring model

`PRIMARY_MODEL_STATE = COMPLETED`. The scheduled Codex Desktop automation (`gpt-5.6-sol`, reasoning `high`) inspected the immutable packet and persisted a market review plus 14 stock reviews with 125 numeric references. Candidate SHA-256: `3dfaea9ce0643e56a676b6740cae7aedab2a7f01fdff090265923c4562d4b276`.

## Nested V2 decision canary

`PRIMARY_V2_CANARY_MODEL_STATE = FAILED_TLS`. The claim-scoped signed-in CLI used Codex `0.148.0-alpha.15`, `gpt-5.6-sol`, `xhigh`, read-only sandbox, and reached the request path at `08:30:09.290378`. Its first `UnknownIssuer` occurred at `08:30:13.659620`; WebSocket retries fell back to HTTPS but continued network waits. It produced zero model results and was interrupted, exit `130`, at `08:35:15.425`.

The wrapper reported `LOCAL_NETWORK_CONNECTIVITY_FAILURE` because its marker is `unknown issuer` with a space while the CLI emitted `UnknownIssuer`. The raw symptom is a TLS certificate failure.
