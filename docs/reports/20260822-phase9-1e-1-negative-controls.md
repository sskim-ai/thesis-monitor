# Phase 9.1E.1 Negative Controls

| Control | Expected | Result |
| --- | --- | --- |
| mode missing/invalid | effective `OFF` | PASS |
| exact Trade AR request | reject | PASS |
| combined Inventory + Trade AR request | reject | PASS |
| broad AR/AP | no selection | PASS |
| DSO/Inventory Days/DPO/CCC | reject | PASS |
| component Inventory as total | reject | PASS |
| causal demand/collection claim | reject | PASS |
| Inventory-only thesis/valuation change | reject | PASS |
| duplicate exact `%p` outside business/earnings | reject | PASS |
| stale/future/non-PIT relation | suppress | PASS |
| incompatible cash-flow period | do not stack | PASS |
| MU/TSLA current FCF redundancy | suppress Inventory | PASS |
| feature OFF | zero packet and fallback diff | PASS |

The 9.1D canary remains detached. The Inventory user-visible selector cannot broaden the source
family, invent a ticker exception, or turn missing facts into zero. Trade AR remains
`OFF_PENDING_NATURAL_PROOF`.

