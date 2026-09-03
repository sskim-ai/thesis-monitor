# 2026-09-03 US Network and Codex Natural Proof

The source monitor's technical transport completed 44/44 requests. The natural
AI path did not reach its scheduler-context DNS/TLS probe, claim-scoped Codex
state preflight, app-server initialization, or model transport because there was
no AI-ready packet for primary or backup to claim.

| Gate | Natural result |
| --- | --- |
| source transport | PASS |
| `codex-network-readiness-v1` | NOT_REACHED_NO_PENDING_PACKET |
| `codex-runtime-state-v1` | NOT_REACHED_NO_PENDING_PACKET |
| Codex app-server | NOT_REACHED_NO_PENDING_PACKET |
| signed-in model transport | NOT_REACHED |

No network or model failure type is assigned. The earliest failure belongs to the
packet's shadow numeric-semantic readiness gate and is reported as taxonomy
`OTHER`, detail `PACKET_NUMERIC_SEMANTIC_READINESS`.

- `US_NETWORK_PREFLIGHT = NOT_REACHED_NO_PENDING_PACKET`
- `US_CODEX_RUNTIME_STATE_PREFLIGHT = NOT_REACHED_NO_PENDING_PACKET`
- `US_CODEX_APP_SERVER_INITIALIZATION = NOT_REACHED_NO_PENDING_PACKET`
- `US_MODEL_TRANSPORT_REACHED = 0`

