# V2 Stock Message Renderer Contract

## Ownership

The V2 stock renderer consumes only an accepted decision. A raw candidate cannot become the final
decision, and the daily-review path cannot override a valid accepted V2 result.

The renderer owns deterministic presentation scaffolding. Business, valuation, price-structure,
and market facts retain their existing canonical owners and validators.

## Common Disclaimer

The former common order/automation disclaimer is not rendered in KR or US BUY, HOLD, or SELL stock
messages. Its removal does not change decision safety, accepted-decision authority, validation,
order sizing, automated trading, or Production Assist state.

## Consistency

Every integration artifact records the evidence fingerprint, prior accepted decision, fresh
candidate, adjudication, and fresh accepted decision. A changed accepted result requires changed
evidence plus a valid final adjudication. Same-evidence churn fails closed.

## Boundaries

- production and canary renderers share the disclaimer omission;
- archive-only research disclaimers may remain where they describe an experimental artifact;
- exact numeric claims remain governed by the existing numeric and semantic validators;
- no decision-policy, valuation, Price Structure, recipient, or scheduler change is implied.
