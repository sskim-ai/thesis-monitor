# Phase 9.0C Shadow AI Preview

Archive-only candidate derived from the repaired run-28/run-29 baselines plus the cash-flow sidecar. Telegram send: `0`.

| Ticker | Freshness | Usage | Human result | Primary Fact |
|---|---|---|---|---|
| 000660 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 003690 | NOT_APPLICABLE | NOT_APPLICABLE | MINOR_IMPROVEMENT | - |
| 005490 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 005930 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 010120 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 012450 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| 086280 | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| CORZ | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:1b8f3742f33dd3b66f8f7673 |
| CRCL | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:402041c63553616360d17391 |
| GOOGL | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:ddb47708bf7d36a4c0b0c7d2 |
| HUT | CURRENT_FORMAL | OCF_ONLY_CONTEXT | MINOR_IMPROVEMENT | cashflow-reported:d046f43a5cbb928c6aa1fdd1 |
| IBM | CURRENT_FORMAL | FULL_FCF_CONTEXT | MINOR_IMPROVEMENT | cashflow:a158304539a9269c66f6d2cb |
| MU | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:96e9c3b873f3678d4dec0ff3 |
| RXRX | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:498c289d4304c0822d861ec3 |
| SKHY | BLOCKED | SUPPRESSED | NO_MEANINGFUL_CHANGE | - |
| SNDK | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:1b8db0b46c63ae9369231151 |
| TSLA | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:68666c261434dab50ab88a8d |
| TSM | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | MINOR_IMPROVEMENT | cashflow:f5f8d7130aaff3c4a0f0a2a1 |
| WRD | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | NO_MEANINGFUL_CHANGE | cashflow:46c15133a15f9cb2c4b839c1 |
| WULF | CURRENT_FORMAL | FULL_FCF_CONTEXT | MATERIAL_IMPROVEMENT | cashflow:6fd003ea029e4d7b03f681f3 |

## Numeric And Semantic Safety

- Automatic cash-flow bindings: `10`
- Manual/rejected/unresolved: `0/0/0`
- Semantic validation errors: `0`
- Status delta candidates: `0`; persisted: `0`

## Message Quality

- Run-28 baseline hard checks: `True`
- Run-28 enriched hard checks: `True`
- Run-29 negative-control hard checks: `True`
- Average stock-message length change: `3.66%`

The bounded increase comes from 10 selectively rendered contexts, not a 20-stock numeric dump.
Substantive repetition, typed skeleton repetition, generic Unknown, and generic next-check counts
remain zero; no subject is classified `DEGRADED`.
