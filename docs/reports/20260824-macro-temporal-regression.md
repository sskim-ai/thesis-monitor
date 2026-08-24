# 2026-08-24 Macro Temporal Regression

## Replay

- Immutable run-35 weekend/no-new-session replay: PASS.
- Normal after-close replay using 2026-08-22 vs 2026-08-21 briefings: PASS.
- Normal replay current series: BAMLH0A0HYM2, DFII10, DGS10, IWM, QQQ, SOXX, SPY, T10YIE,
  VIXCLS.
- Normal replay retained SOXX relative performance and VIX as current important changes.
- Weekend/holiday/mixed/revision/early-close matrix: PASS.
- Provider calls for replay: 0.

## Tests

- Focused macro temporal/digest/market-intelligence/monitor/session suite: 61 passed.
- Final focused digest suite after language refinement: 40 passed.
- Full pytest: 1,416 passed, 1 third-party deprecation warning.
- Ruff: PASS.
- `git diff --check`: PASS.

## Preserved Contracts

| Surface | Result |
|---|---|
| Phase 9.0E cash-flow user-visible path | no contract/mode change |
| Inventory mode | unchanged (`SELECTIVE_INVENTORY` external operating state) |
| Trade AR | unchanged/OFF |
| KR investor flow | unchanged |
| KR producer guard | unchanged |
| KRX role-target/publication logic | unchanged |
| Night-futures pairing/deadline | unchanged |
| Price/support/resistance/RR | unchanged |
| Valuation | unchanged |
| Exactly-once/receipts | unchanged |
| AI schema / Public Action | schema 4 / 0.4.5 unchanged |
| operationId | 20/20 unique |
| Investment Knowledge v3 | SHA `559ad45e...a5a9d18`, parity PASS |
| Chart Knowledge v1 | SHA `beee6455...0ede19b`, parity PASS |

## Runtime Operations

Manual Telegram 0; manual Scheduled Task 0; provider recreation 0; DB mutation 0; Pilot mutation 0;
archive rewrite 0; Production Assist remains OFF.
