# KR + US Market Adapter Cross-Market Gates

- Evidence classes: `IMMUTABLE_NATURAL_EVIDENCE` + `CURRENT_CODE_REPLAY`

```text
REPLAY_STATE = COMPLETE
CURRENT_MAIN = c7816cabf2898f18883f59286be818932b4a26c1
OPERATING = c7816cabf2898f18883f59286be818932b4a26c1

KR_VALUATION_REPLAY = PASS
US_MARKET_ADAPTER_REPLAY = PARTIAL
KR_MARKET_ADAPTER_REPLAY = PARTIAL
KR_MARKET_DIGEST_DOMESTIC_DATA_REPLAY = INSUFFICIENT

US_FREE_ANALYST_REPLAY = PASS
KR_FREE_ANALYST_REPLAY = PASS
US_ADAPTIVE_REPLAY = PASS
KR_ADAPTIVE_REPLAY = PASS

US_CANARY_SIMULATED_SELECTED = 3
KR_CANARY_SIMULATED_SELECTED = 3

KR_US_REASONING_SCHEMA_COMMON = PASS
COMMON_MARKET_ADAPTER_CROSS_MARKET_REPLAY = PARTIAL

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0
MARKET_CONTEXT_UNIT_CONFLICT = 0
MARKET_CONTEXT_DEFAULT_ZERO = 0

SUPPLEMENTAL_COLLECTION_REQUIRED = NO
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
PRODUCTION_RESEARCH_CONNECTOR = NOT_AVAILABLE

CODE_CORRECTNESS = PASS
NATURAL_LIVE_PROOF = DEPLOYED_PENDING_NATURAL
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
P2_BACKLOG = 4
NEXT_ACTION = WAIT_FOR_US_STRUCTURED_ADAPTER_NATURAL_CANARY
```

The cross-market result is a safe `PARTIAL`: both common contracts and hard gates pass, while unavailable breadth/flow stays Unknown. P2 backlog: KR domestic structured acquisition, US breadth/equal-weight depth, unsupported US participant flow, and existing full-cohort synthesis repetition.

## Validation

- Current-code immutable replay: US `14/14`, KR `8/8`
- Focused adapter/numeric/Free Analyst/Adaptive/AI review tests: `306 passed`
- Documentation tests: `4 passed`
- Public Action/schema/operationId health tests: `9 passed`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Investment Knowledge v3 checksum/parity: `559ad45e...` / `PASS`
- Chart Knowledge v1 checksum/parity: `beee6455...` / `PASS`
- Public Action / schema / operationId: `0.4.5 / 4 / 20 of 20 unique`
- Full replay-branch suite: `1537 passed`
- Existing exact-main GitHub Actions: `32833551337 PASS`
- Runtime code diff: `0`
