# Legacy Macro / Shadow Registry Validation

| Check | Result |
|---|---|
| Focused macro/registry/replay tests | 271 PASS |
| Full pytest | 1,436 PASS, 1 dependency warning |
| Ruff | PASS |
| `git diff --check` | PASS |
| Knowledge v3 sync/checksum | PASS, 33,624 bytes / 704 lines |
| Chart Knowledge parity | PASS |
| Public Action | 0.4.5 unchanged |
| Output schema | 4 unchanged |
| operationId | 20/20 unique |
| Immutable replay | PASS |
| AI numeric / semantic / language / quality | PASS / PASS / PASS / PASS |
| Numeric binding | automatic 84; manual legacy 3; rejected 0; unresolved 0 |
| Fallback bundle | 1 digest + 7 stocks; duplicate/orphan 0/0 |
| Inventory parity | 3/3 PASS |
| Macro temporal / investor flow | PASS / PASS |
| Production DB / Telegram / manual task / Pilot | 0 / 0 / 0 / 0 |
| Implementation exact-SHA Actions | run 32725115091, Test/Lint PASS |

The sole pytest warning is the existing Starlette/httpx deprecation warning. No threshold, public
schema, task configuration, provider, feature mode, or database migration changed.
