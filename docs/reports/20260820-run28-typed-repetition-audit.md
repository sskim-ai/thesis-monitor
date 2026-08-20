# Run-28 Typed Repetition Audit

Contract: `typed-template-skeleton-v1`

## Quality Delta

| Measure | Before | After |
|---|---:|---:|
| Bare/typed skeleton blockers | 5 | 0 |
| Generic numeric-summary families | 1 | 0 |
| Business ownership violations | 9 | 0 |

The typed key keeps `price_context / previous_risk_reward_ratio -> current_risk_reward_ratio` separate from `valuation / price_to_book -> historical_pb_percentile`. A repeated relation with the same text shape remains a blocker.

## RR Delta Decisions

| Ticker | Pair after | Material reasons | Suppression |
|---|---|---|---|
| CORZ | NO | none | no_material_price_transition |
| CRCL | YES | confirmation_lifecycle_transition | none |
| GOOGL | NO | none | no_material_price_transition |
| IBM | NO | none | no_material_price_transition |
| MU | YES | chart_state_transition, confirmation_lifecycle_transition, resistance_change | none |
| RXRX | YES | chart_state_transition, confirmation_lifecycle_transition | none |
| SNDK | YES | chart_state_transition | none |
| TSLA | YES | chart_state_transition, confirmation_lifecycle_transition, support_change | none |
| TSM | NO | none | no_material_price_transition |
| WRD | YES | resistance_change | none |

`canonical_zone_endpoint_contract` remains unchanged. No generic numeric-pair allowlist was added.
