# Current Canary Cleanup Regression

Same canonical evidence preserved the accepted decisions:

| Ticker | Before | After |
|---|---|---|
| 003690 | HOLD | HOLD |
| 000660 | HOLD | HOLD |
| GOOGL | HOLD | HOLD |
| RXRX | SELL | SELL |

Decision confidence, horizon, timing, directional refs, and change-condition refs also match. Base stock messages are reused intact and only the validated canary block is inserted; Price Structure and valuation calculations were not changed.

The 2026-08-30 US natural run-46 produced safe suppressed canary receipts with `ConnectError`, so it did not count as a natural proof cycle. The natural proof remains KR `0/2`, US `0/2`. Test-sink execution did not mutate the proof file or continuity-state SHA.

- `CLEANUP_CHANGED_CANARY_DECISION = 0`
- `DECISION_OUTPUT_DIFF_FROM_SAME_EVIDENCE = 0`
- `PRICE_STRUCTURE_NUMERIC_DIFF = 0`
- `VALUATION_NUMERIC_DIFF = 0`
- `CANARY_SCOPE_DIFF = 0`
- `NON_CANARY_DECISION_BLOCK_VISIBLE = 0`
- `TEST_INCREMENTED_NATURAL_CANARY_COUNTER = 0`
