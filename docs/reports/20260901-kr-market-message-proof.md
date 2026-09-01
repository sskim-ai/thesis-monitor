# KR Market Message Proof

## Market row

| Session | Data ready | Macro safe | Renderer | Validation | Delivery | Earliest fallback stage |
| --- | --- | --- | --- | --- | --- | --- |
| after_hours | YES | YES | deterministic market digest | safe payload; AI stock bundle rejected | sent exactly once | FALLBACK_SELECTED |

- Content SHA-256: `b363f82fc4b334d25f236c143d1c36940a0fabd01e84603a103da3c3c2a60dcb`
- Attempt count: `1`
- Sent KST: `2026-09-01T17:10:08.749557+09:00`
- Exact payload: `True`

Market data itself did not fail. The safe deterministic digest was used because delivery is bundle-oriented and the stock AI candidate did not pass.
