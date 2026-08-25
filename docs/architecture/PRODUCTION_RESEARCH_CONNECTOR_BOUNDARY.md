# Production Research Connector Boundary

## Decision

`PRODUCTION_RESEARCH_CONNECTOR = NOT_AVAILABLE`.

The production Common AI Core imports no Open Research engine or verified search connector. Existing
Google News RSS and optional Naver news providers are event collectors; they do not establish an
Open Research runtime with source/entity/time verification, bounded dynamic queries, negative
evidence, and primary-source reconciliation. Their existence therefore does not satisfy the live
connector gate.

## Availability Contract

A future connector is `AVAILABLE` only when all are proven: free use, preserved source refs, bounded
query budget, non-interactive execution, production timeout, and secret-safe output. Partial proof is
`AMBIGUOUS`; absence is `NOT_AVAILABLE`.

With either non-available state, `OPEN_RESEARCH_LIVE_CANARY = BLOCKED_CONNECTOR`. No provider is
invented, no research-enhanced slot is selected, and `OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0`.
The structured market adapter and existing Free Analyst canary continue independently.

