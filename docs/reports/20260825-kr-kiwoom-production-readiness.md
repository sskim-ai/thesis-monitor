# KR Kiwoom Production Readiness

## Decision

`KIWOOM_KR_MARKET_CONTEXT = PARTIAL`

`PRODUCTION_READY = YES`

Safe partial is deliberate: index, breadth, size/sector, and aggregate market flow are validated;
KOSDAQ concentration is validated; KOSPI concentration remains blocked. Adapter failure cannot
block packet creation. Full mode remains OFF, canary remains 1/2/3, Open Research production is 0,
and Production Assist remains OFF.

## Validation

- Focused: 101 passed.
- Full pytest: 1569 passed, 1 upstream warning.
- Ruff: PASS.
- Diff check: PASS.
- Replay: 8/8 PASS.
- Public Action 0.4.5 and schema 4: unchanged.
- User-visible delivery during this task: 0.

Open P0: 0. Open material P1: 0. Next action is the first naturally scheduled eligible KR proof;
no manual task or Telegram run is authorized.
