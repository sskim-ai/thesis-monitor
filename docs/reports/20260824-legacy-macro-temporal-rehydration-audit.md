# Legacy Macro Temporal Rehydration Audit

## Immutable Result

| Measure | Result |
|---|---:|
| Legacy items inspected | 12 |
| Rehydrated | 12 |
| Insufficient-metadata fail-closed | 12 |
| `CURRENT_OBSERVATION` | 0 |
| `PRIOR_MARKET_SESSION` | 4 |
| `REFERENCE_LAGGING` | 8 |
| Missing metadata defaulted current | 0 |
| False-current claims | 0 |
| Persisted source mutations | 0 |

Session-bound SPY/QQQ/IWM/SOXX facts were retained only as the prior completed market session.
Release/reference observations without proof of a new release after the prior briefing cutoff were
kept as lagging reference context.

The same derived view is consumed by `daily_digest`, `market_intelligence_service`,
`ai_review_service`, and deterministic fallback rendering. The repaired AI message explicitly says
the S&P500 move belongs to the prior completed regular session; fallback says there is no new US
cash session or daily macro observation.
