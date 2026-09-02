# Codex Natural Network Transport Contract

Contract: `codex-network-readiness-v1`

## Boundary

Natural V2 decision generation uses one transport boundary for US and KR, primary and backup:

```text
stock_decision.generate
  -> accepted_decision_v2_runtime.generate
  -> DNS readiness
  -> TCP/TLS readiness
  -> isolated signed-in Codex runtime state
  -> Codex app-server and model request
```

The readiness probe runs before each expensive Codex subprocess. It does not read or claim a stock
packet, import Telegram, write an accepted decision, or mutate the database.

## Failure Taxonomy

- `LOCAL_DNS_RESOLUTION_FAILURE`
- `LOCAL_NETWORK_CONNECTIVITY_FAILURE`
- `TLS_HANDSHAKE_FAILURE`
- `CODEX_APP_SERVER_TRANSPORT_FAILURE`
- `MODEL_PROVIDER_RESPONSE_FAILURE`
- `MODEL_TIMEOUT`
- `MODEL_RATE_LIMIT`

DNS markers take precedence over downstream WebSocket and HTTPS fallback messages. Runtime-state
failures retain the separate `LOCAL_CODEX_RUNTIME_STATE_NOT_READY` contract.

## Retry Contract

The readiness probe makes at most three DNS/TCP/TLS attempts with fixed `0.5s` and `1.5s`
backoff. If readiness remains false, the model subprocess does not start. A Codex subprocess may be
retried once only for transient DNS, connectivity, TLS, or app-server transport failures. All
attempts share the caller's original timeout deadline.

Rate limits, model timeouts, provider response failures, path errors, runtime-state errors, and
schema/semantic failures are not transport-retried.

## Security

The probe uses the operating system resolver and default TLS trust store. It does not hardcode a
resolver, edit hosts, disable certificate verification, run as root, copy credentials, or expose
addresses, tokens, auth headers, cookies, or recipient identifiers.

