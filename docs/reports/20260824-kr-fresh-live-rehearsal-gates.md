# KR Fresh Live Rehearsal Gates

| Gate | Result |
|---|---|
| XKRX role target | PASS |
| Fresh collection / 7-of-7 analysis | PASS |
| Packet persistence | PASS |
| Packet-bound intent integrity | PASS, 8/8 |
| AI candidate | FAIL, shadow claim suppressed |
| Deterministic fallback completeness | PASS, 8/8 |
| Deterministic fallback content safety | FAIL, macro temporal P0 |
| Inventory canonical/fallback selection | PASS, 3 selected |
| Inventory AI/fallback parity | NOT OBSERVED |
| Trade AR/AP leakage | PASS, 0 |
| Investor-flow reconciliation/attribution | PASS |
| Macro temporal honesty | FAIL |
| Price/RR | PASS |
| Valuation | PASS |
| Production mutation | PASS, 0 |

## Validation

- Focused rehearsal/regression suite: `270 passed`.
- Full pytest: `1428 passed`, one third-party deprecation warning.
- Ruff: `PASS`.
- `git diff --check`: `PASS`.
- Summary JSON parse: `PASS`.
- Investment Knowledge v3/runtime parity: `PASS`, SHA-256
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.
- Chart Knowledge v1: `PASS`, SHA-256
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`.
- Public Action: `0.4.5`; operationId: `20/20 unique`.
- Operating API health: `PASS` (`status=ok`).
- Operating/main parity: `96825de767f8ff25b59ab4451df305df5dd873cc`; clean.
- Main promotion: `NO`, because the rehearsal discovered the open macro temporal P0.

## Severity

- Open P0: 1, legacy morning briefing without temporal contract fails open as current.
- Open material P1: 0.
- P2: audit-only investor-flow numeric registry coverage; Inventory AI parity not observed because
  the shadow candidate was correctly suppressed.

## Decisions

`KR_FRESH_LIVE_REHEARSAL_READY = NO`

`KR_PRODUCTION_REPAIRED_LIVE_REHEARSAL = FAIL`

`KR_PACKET_DELIVERY_DRY_RUN = PASS`

`INVENTORY_USER_VISIBLE_REHEARSAL = FAIL`

`KR_INVESTOR_FLOW_REHEARSAL = PASS`

`MACRO_TEMPORAL_REHEARSAL = FAIL`

Natural proof remains pending for repaired packet scheduling, terminal receipt, Telegram
exactly-once delivery, selected Inventory, investor flow, and macro temporal behavior. The next work
is the bounded macro legacy-briefing compatibility repair, not another broad rehearsal.
