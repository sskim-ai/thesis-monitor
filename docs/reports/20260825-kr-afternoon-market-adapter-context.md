# KR Afternoon Market Adapter Context

- Evidence class: `CURRENT_CODE_REPLAY`
- Mandatory input: stored packet facts only
- Adapter result: `PARTIAL`

| Field | Value |
| --- | --- |
| contract | market-context-adapter-v1 |
| indices | Unknown |
| breadth | UNKNOWN |
| sectors | Unknown |
| size context | 0 |
| market flows | 0 |
| deterministic relations | 0 |
| session | after_hours / final |
| publication | UNKNOWN |
| data gaps | breadth_unavailable, coverage:breadth:not_provided_by_backend, coverage:local_market_indices:kr_local_index_not_provided_by_backend, coverage:market_flows:not_provided_by_backend, local_indices_unavailable, market_flow_unavailable, sector_context_unavailable, size_context_unavailable |

KOSPI/KOSDAQ, breadth, sector/size context, market-wide KRW flow, and index contribution were not captured in the immutable packet. They remain explicit Unknowns, never zero. Overnight US/macro facts were not relabeled as local KR breadth.

`KR_MARKET_ADAPTER_REPLAY = PARTIAL`

`KR_MARKET_DIGEST_DOMESTIC_DATA_REPLAY = INSUFFICIENT`
