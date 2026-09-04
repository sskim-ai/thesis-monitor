# 2026-09-04 Integrated US TEST E2E

The combined branch ran the real US claim, signed-in CLI, heartbeat, fencing, finalizer, delivery adapter, and TEST Telegram path against an isolated SQLite copy.

| Gate | Result |
|---|---|
| Packet | `2026-09-04-us-run-55-54cd536c6e4d` |
| Source ready / candidate / accepted | `15/15/15` |
| Signed-in xhigh stock results | `14/14` |
| Lease renewals / fencing | `38 / PASS` |
| Healthy backup | `SAFE_NOOP_PRIMARY_ACTIVE` |
| TLS UnknownIssuer | `0` |
| Validator | `completed` |
| TEST market / stocks | `1/14` |
| Fallback / duplicate | `0/0` |
| Production recipient / DB / scheduler | `0/0/0` |

No raw recipient identifier is stored. Structured Autonomy promotion was `0`.
