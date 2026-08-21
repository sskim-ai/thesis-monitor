# 2026-08-21 KR Investor-Flow Validation

## Focused

- Participant/reconciliation, OHLCV mapping, fallback, and semantic grounding: PASS
- Focused integration result: 298 passed
- Final cleaned-diff focused rerun: 252 passed
- Active-universe read-only audit: 7/7 provider success, 21/21 windows complete
- Numeric identity: PASS; no residual-derived numeric category
- Unsupported attribution after: 0
- AI/fallback context parity: PASS

## Full Regression

- Full pytest: 1,347 passed, 1 dependency deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Public Action exact unchanged-base dynamic-schema comparison: PASS
- Public Action version: `0.4.5`
- operationId: 20/20 unique
- Output schema: `4`
- Dynamic Public Action schema matched the unchanged-base schema byte-for-byte after canonical JSON
  serialization (`sha256=9b222919dc741f674f312468bf0febbaf82a6fbe511ada44c93e32c03de2b667`).

## Boundaries

- Public Action: `0.4.5`, unchanged
- Output schema: `4`, unchanged
- Supply score formula: unchanged
- Price/RR, valuation, cash flow, working capital, night futures, KRX telemetry: unchanged
- Manual Telegram/task/Pilot/DB: 0
- Production Assist: OFF

## Exact-SHA CI

- Work-instruction commit: `e9d7c73cf6f25b2423b55a6899465e86441316d1`
- Implementation commit: `47fc87e2a9189556a7206065fdb759f3603ce497`
- GitHub Actions run: `32480802390`
- Test: PASS
- Lint: PASS
