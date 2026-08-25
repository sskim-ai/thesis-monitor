# Message Quality v2 Safety Parity

Across 22 replay messages:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
MATERIAL_INFORMATION_LOSS = 0
MARKET_CONTEXT_UNIT_CONFLICT = 0
MARKET_CONTEXT_DEFAULT_ZERO = 0
```

Production numeric binding was replayed before rendering: US `122` and KR `123` claims auto-bound,
with rejected/unresolved placeholders `0`. Deterministic supporting refs cannot cross entity, ticker,
market, or packet ownership. Market enrichment creates no hidden arithmetic; the US relative return
is a typed deterministic relation with exact input refs.

`COMMON_MESSAGE_QUALITY_V2 = PASS`.
