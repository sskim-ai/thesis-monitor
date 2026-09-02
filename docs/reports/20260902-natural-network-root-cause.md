# Natural Network Root Cause

## Frozen Evidence

The 2026-09-02 KR natural V2 log entered the signed-in Codex CLI with the expected binary, model
`gpt-5.6-sol`, `xhigh` reasoning, read-only sandbox, and initialized app-server session. At
`08:02:41Z`, its first model-transport failure was:

```text
failed to lookup address information: nodename nor servname provided, or not known
```

WebSocket retries then failed, HTTPS fallback was attempted, and the request remained in network
reconnect backoff until interruption at `08:06:31Z`. No model response was received.

## Classification

`NATURAL_NETWORK_FAILURE_REPRODUCED = PASS`

`NATURAL_NETWORK_FIRST_FAILURE_BOUNDARY = LOCAL_DNS_RESOLUTION_FAILURE`

The previous runtime collapsed this into
`signed_in_codex_cli_v2_production_generation_failed`. The repaired classifier gives DNS markers
precedence over the WebSocket and generic connect messages that follow them.

## Scope

This was not a packet, schema, accepted-decision, Telegram, runtime-state ownership, or model
reasoning failure. Functional deterministic fallback delivery remained separate. No public DNS,
hosts, TLS, root, firewall, or credential workaround was introduced.

