# Indicator Observation vs Price Interaction

| Semantic | Meaning |
|---|---|
| `indicator_observation_date` | Date on which a derived indicator value was observed |
| `last_price_interaction_date` | Last verified candle interaction with an observed-price anchor |
| `historical_interaction_count` | Verified pivot reactions or balance-box close occupancy count |
| `price_anchor_ref` | Exact observed-price evidence identity |

After repair:

- `INDICATOR_OBSERVATION_AS_PRICE_INTERACTION = 0`
- `DYNAMIC_FAMILY_FAKE_REACTION_COUNT = 0`
- `MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0`
- Visible anchored major zones: `21`

Legacy `interaction_date` remains readable for compatibility, but new dynamic-indicator producers
do not populate it. Merge logic derives price interaction metadata from confirmed anchor sources
only.
