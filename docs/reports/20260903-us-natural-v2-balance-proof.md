# 2026-09-03 US Natural V2 Balance Proof

## Result

`US_V2_NATURAL_LIVE = FAIL_SAFE_FALLBACK`.

| Gate | Result |
| --- | ---: |
| Context subjects | 14 |
| AI candidate generated | 0 |
| Accepted V2 plans | 0 |
| Explicit V2 blocks | 0 |
| Visible directional balances | 0 |
| Deterministic fallback stock messages | 14 |

The source packet did not pass the numeric semantic readiness gate, so primary and
backup automations correctly found no pending review packet. The signed-in model,
candidate validation, adjudication, and accepted ownership stages were never
reached. Consequently no raw candidate balance was rendered and no prior decision
was carried forward as a synthetic current balance.

## Earliest Failure

The earliest failure is the packet builder's shadow numeric-semantic gate. Raw
night-futures collection remained in the packet as required, while temporary
user-facing suppression removed the rendered block. Two `reference_price` fields
were nevertheless evaluated as unsupported numeric semantics, making
`ready_for_ai=false`.

This is a material P1 availability regression, not a P0 content error: no unsafe
V2 decision was sent and the deterministic fallback remained exact. The bounded
follow-up is to reconcile preserved night-futures raw fields with the packet
numeric registry or exclude non-consumable suppressed fields from shadow readiness,
without re-enabling night-futures prose.

- `US_ACCEPTED_READY_COUNT = 0`
- `US_EXPLICIT_V2_COUNT = 0`
- `US_BALANCE_VISIBLE_COUNT = 0`
- `US_FALLBACK_STOCK_COUNT = 14`
- `US_UNEXPLAINED_BALANCE_JUMP = 0`

