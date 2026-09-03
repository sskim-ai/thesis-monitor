# Shadow Entry-Zone Contract

Entry zones must be traceable to the frozen price map. `NONE` is valid when a business or risk gate makes a numeric entry inappropriate. A zone is not a target and cannot be invented from prose.

| Ticker | Entry type | Codex zone | Independent quality | Canonical basis |
| --- | --- | --- | --- | --- |
| CORZ | SUPPORT | 12.91-13.46 | SUPPORTED | canonical:chart:structure:nearest_supports:1, canonical:chart:structure:risk_reward:support_entry |
| CPNG | SUPPORT | 14.73-15.22 | SUPPORTED | canonical:chart:structure:nearest_supports:1, canonical:chart:structure:risk_reward:support_entry |
| CRCL | SUPPORT | 82.01-86.53 | SUPPORTED | canonical:chart:structure:nearest_supports:1, canonical:chart:structure:state |
| GOOGL | SUPPORT | 312.37-321.88 | SUPPORTED | canonical:chart:structure:nearest_supports:1, canonical:chart:structure:risk_reward:support_entry |
| HUT | BREAKOUT_CONFIRMATION | 97 | SUPPORTED | canonical:chart:stored_price_rules, decision-evidence:b939d70a17422e43c177 |
| IBM | BREAKOUT_CONFIRMATION | 250 | SUPPORTED | canonical:chart:stored_price_rules, canonical:monitoring:confirmation_transition |
| MU | SUPPORT | 867.52-911.75 | SUPPORTED | canonical:chart:structure:nearest_supports:1 |
| RXRX | NONE | withheld | NOT_ACTIONABLE | none |
| SKHY | BREAKOUT_CONFIRMATION | 163 | SUPPORTED | canonical:chart:stored_price_rules |
| SNDK | SUPPORT | 1,100-1,125 | SUPPORTED | canonical:chart:stored_price_rules |
| TSLA | NONE | withheld | NOT_ACTIONABLE | decision-evidence:0cbb33d247bc3d3facec, canonical:valuation:historical_pe, canonical:chart:structure:state |
| TSM | BREAKOUT_CONFIRMATION | 432 | SUPPORTED | canonical:chart:stored_price_rules, canonical:chart:price_transition, canonical:chart:structure:state |
| WRD | BREAKOUT_CONFIRMATION | 6.68 | SUPPORTED | canonical:chart:stored_price_rules, decision-evidence:5ba1286806d9b069c093, decision-evidence:8b7f93a5f707ad6158af |
| WULF | BREAKOUT_CONFIRMATION | 18.4 | SUPPORTED | canonical:chart:stored_price_rules, decision-evidence:ede656d249779160185b |

Supported numeric entry zones: `12/12 rendered numeric zones`. `RXRX` and `TSLA` deliberately withheld numeric entries; neither withholding is a validation failure.
