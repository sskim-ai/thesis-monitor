# 2026-09-04 Market Semantic and Provenance Repair

`market:relative:IWM:SPY` had been emitted under the broad growth-relative semantic. The renderer phrase correctly meant Russell 2000 relative to S&P 500, but the semantic registry could not bind that identity.

The market adapter and registry now use `market_small_cap_relative` and `small_cap_relative_return_pct`, with subject and benchmark identity retained. Legacy IWM/SPY occurrences are upgraded in memory only when both identities and the exact relative-return field match.

This resolves both the semantic mismatch and the unbound `-0.6%` occurrence. Sector, index, futures, style, and yield semantics remain distinct; value equality alone cannot authorize a binding.

| Gate | Result |
|---|---|
| Incident market errors repaired | `2/2` |
| Exact instrument/benchmark mapping | `PASS` |
| Unsupported numeric accepted | `0` |
