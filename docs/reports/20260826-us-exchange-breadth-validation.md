# US Exchange Breadth Validation

`US_BREADTH_MESSAGE_VALIDATION = PASS`

- Focused parser/adapter/fail-open tests: 35 passed.
- Full pytest: 1,580 passed, 1 deprecation warning.
- Ruff: PASS.
- `git diff --check`: PASS.
- Action schema generation check: PASS.
- Fact mismatch, unsupported numeric, session conflict, scope mislabel, intraday promotion,
  partial-universe promotion, default zero, hidden arithmetic, unsupported causality, semantic
  ownership error, material information loss, and Trade AR leak: all 0.
- Investment/Chart knowledge parity, Public Action 0.4.5, 20/20 operationIds, schema 4: unchanged.
