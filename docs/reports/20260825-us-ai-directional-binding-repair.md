# US AI Directional Binding Repair

Contract: `working-capital-relation-semantics-v1`.

The relation fact now preserves signed and absolute gaps, direction, lhs/rhs semantics, comparison basis, date/scope, relation ID, and input Fact IDs. Directional prose binds only `fields.gap_percentage_points_signed`; the binder displays its absolute magnitude while retaining the signed canonical claim value. Absolute gap remains non-directional.

Legacy packet upgrades: `2`. Archive rewrites: `0`.

| Ticker | Field | Signed value | Display | Comparator |
| --- | --- | --- | --- | --- |
| MU | fields.gap_percentage_points_signed | -15.733907740801747 | 15.7%p | COGS |
| TSLA | fields.gap_percentage_points_signed | -26.63218129057952 | 26.6%p | Revenue |
