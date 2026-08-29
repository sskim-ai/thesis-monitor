# BUY Positive Fixture

Current natural decisions contain no BUY. BUY rendering was therefore tested only with two
historical canonical fixtures, never as current production state.

| Ticker | Fixture as-of | Numeric binding | Payload chars | Result |
|---|---|---|---:|---|
| `003690` | `2026-08-28` | `3/3` automatic | 1368 | PASS |
| `GOOGL` | `2026-08-29` | `3/3` automatic | 2726 | PASS |

Every fixture starts with `TEST FIXTURE - BUY path verification` semantics and explicitly states
that it is not the current decision or production state. Production sends, production intents,
state mutation, and historical-BUY-as-current events were all `0`.

`BUY_PATH_TEST_FIXTURE=PASS`; `NATURAL_BUY_LIVE_PROOF=PENDING`.
