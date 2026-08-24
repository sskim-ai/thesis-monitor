# Open Research Validation

| Check | Result |
|---|---|
| Focused Open Research tests | 22 passed |
| Full pytest | 1,496 passed, 1 existing dependency warning |
| Repository Ruff | PASS |
| `git diff --check` | PASS |
| Investment Knowledge v3 | PASS, SHA-256 `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Chart Knowledge v1 | PASS, SHA-256 `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5` unchanged |
| operationId | 20/20 unique |
| Output schema | `4` unchanged |
| Production-import wiring | 0 |
| Telegram / DB / Pilot / main / operating mutation | 0 |

The only pytest warning is the pre-existing Starlette/httpx deprecation warning. The shadow module imports no production jobs, schedulers, DB, delivery, or Telegram code.
