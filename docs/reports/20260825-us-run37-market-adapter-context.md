# US Run-37 Market Adapter Context

- Evidence class: `CURRENT_CODE_REPLAY`
- Mandatory input: stored packet facts only
- Adapter result: `PARTIAL`

| Field | Value |
| --- | --- |
| contract | market-context-adapter-v1 |
| indices | IWM, QQQ, SPY |
| breadth | UNKNOWN |
| sectors | 반도체 |
| size context | 0 |
| market flows | 0 |
| deterministic relations | 2 |
| session | after_hours / final |
| publication | UNKNOWN |
| data gaps | breadth_unavailable, coverage:breadth:not_provided_by_backend, coverage:market_flows:not_provided_by_backend, size_context_unavailable, us_participant_flow_not_supported |

## Deterministic Relations

| Metric | Formula | Inputs | Result | Unit | Date |
| --- | --- | --- | --- | --- | --- |
| relative_return | subject_return_pct - benchmark_return_pct | market:index:QQQ, market:index:SPY | -0.7041999999999999 | pct_point | 2026-08-24 |
| relative_return | subject_return_pct - benchmark_return_pct | market:sector:SOXX, market:index:SPY | -2.3733 | pct_point | 2026-08-24 |

Breadth remains Unknown and US participant flow remains unsupported. No KR foreign/institution/retail semantics were introduced. Hidden arithmetic, unit conflicts, and session mismatch are all `0`.

`US_MARKET_ADAPTER_REPLAY = PARTIAL`
