# KR Shadow Gate Validation

| Check | Result |
|---|---|
| Targeted shadow/production gate tests | 19 PASS |
| Producer/fallback/Inventory/macro/investor-flow suite | 385 PASS |
| Run-36 no-send replay | PASS |
| Retry idempotency | PASS |
| Full pytest | 1,428 PASS, 1 pre-existing warning |
| Ruff | PASS |
| `git diff --check` | PASS |
| Packet-before-intent | PASS |
| Fallback reachable with shadow false | PASS |
| Trade AR OFF | PASS |
| Public Action | unchanged 0.4.5 |
| Output schema | unchanged 4 |
| Provider calls | 0 |
| Manual Telegram/task | 0 / 0 |
| Production DB/Pilot mutation | 0 / 0 |
| Original archive rewrite | 0 |
| Instruction SHA Actions | run 32709664393, Test/Lint PASS |
| Implementation SHA Actions | run 32711595707, Test/Lint PASS |

Investment Knowledge v3 and Chart Knowledge v1 are unmodified; their repository checksums remain
the persistent-state values. Final documentation SHA Actions and post-promotion health are recorded
after the final commit.
