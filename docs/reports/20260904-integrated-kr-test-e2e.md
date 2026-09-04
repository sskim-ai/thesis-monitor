# 2026-09-04 Integrated KR TEST E2E

The combined branch ran the real KR production path against an isolated SQLite copy and the dedicated TEST sink.

| Gate | Result |
|---|---|
| Packet | `2026-09-03-kr-run-54-f19bb379daa7` |
| Source ready / candidate / accepted | `9/9/9` |
| Signed-in xhigh stock results | `8/8` |
| Lease renewals / fencing | `19 / PASS` |
| Healthy backup | `SAFE_NOOP_PRIMARY_ACTIVE` |
| Validator | `completed` |
| TEST market / stocks | `1/8` |
| Fallback / duplicate | `0/0` |
| Production recipient / DB / scheduler | `0/0/0` |

No raw recipient identifier is stored. Structured Autonomy promotion was `0`.
