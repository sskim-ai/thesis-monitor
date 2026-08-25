# 2026-08-25 Inventory User-Visible Natural Proof

- Mode: `SELECTIVE_INVENTORY`
- Selected: `2`
- Detached canary: `COMPLETE_PASS`
- Numeric binding: `{'automatic': 2, 'manual': 0, 'rejected': 0, 'unresolved': 0}`

| Ticker | Status | Freshness | Selected | Balance date | Relation | Suppression |
|---|---|---|---:|---|---|---|
| CORZ | SUPPRESSED | BLOCKED | False | 2026-06-30 | - | no_material_current_relation, working_capital_context_blocked |
| CRCL | SUPPRESSED | BLOCKED | False | 2026-06-30 | - | no_material_current_relation, working_capital_context_blocked |
| GOOGL | SUPPRESSED | BLOCKED | False | 2026-06-30 | - | no_material_current_relation, working_capital_context_blocked |
| HUT | SUPPRESSED | BLOCKED | False | 2026-06-30 | - | no_material_current_relation, working_capital_context_blocked |
| IBM | SUPPRESSED | BLOCKED | False | 2026-06-30 | - | no_material_current_relation, working_capital_context_blocked |
| MU | READY | CURRENT_FORMAL | True | 2026-05-28 | working-capital-relation:dbdfd04e725e83528d8fdd31 | - |
| RXRX | SUPPRESSED | BLOCKED | False | 2026-06-30 | - | no_material_current_relation, working_capital_context_blocked |
| SKHY | SUPPRESSED | BLOCKED | False | - | - | no_material_current_relation, working_capital_context_blocked |
| SNDK | SUPPRESSED | BLOCKED | False | 2026-07-03 | - | no_material_current_relation, working_capital_context_blocked |
| TSLA | READY | CURRENT_FORMAL | True | 2026-06-30 | working-capital-relation:36181e61768dfd580d9ede01 | - |
| TSM | CONTEXT_ONLY | FORMAL_LAGGING_PROVISIONAL | False | 2024-12-31 | working-capital-relation:d91d3ba923be232bf99652a4 | newer_provisional_period_not_balance_aligned |
| WRD | SUPPRESSED | BLOCKED | False | 2025-06-30 | - | no_material_current_relation, working_capital_context_blocked |
| WULF | SUPPRESSED | BLOCKED | False | 2026-06-30 | - | no_material_current_relation, working_capital_context_blocked |

## MU

- Context: `wc-visible-751bfe9a98f85e530e1d4a21`
- Relation: `working-capital-relation:dbdfd04e725e83528d8fdd31`
- Balance semantic: `us-gaap:InventoryNet` / scope `total`
- Fact refs: `working-capital-reported:2a5dd10bfd88a91b65bcc777, working-capital-reported:00d1a7bd62280782e2efae65, working-capital-reported:d7dc274bbdea5cd2c57c0a62, working-capital-reported:076714324caa61d396cf62d0, working-capital-derived:50745dd0f6eb60120c37579e, working-capital-derived:9b1463bee52b77a325a1ba6e`
- Delivered wording: `재고 증가율은 매출원가 증가율보다 15.7%p 밑돌았습니다. ASP·제품 믹스·메모리 수요와 함께 확인하며 사이클 방향을 확정하지 않습니다.`

## TSLA

- Context: `wc-visible-760462535f2541f89fda7334`
- Relation: `working-capital-relation:36181e61768dfd580d9ede01`
- Balance semantic: `us-gaap:InventoryNet` / scope `total`
- Fact refs: `working-capital-reported:73fe4f1d304b6cadfde50b24, working-capital-reported:5986216e8dc1e64113c1efd6, working-capital-reported:0ca5b1287df9208349d139b7, working-capital-reported:450f903e4792967c35cb82ba, working-capital-derived:278cf0f9df9a28a8c5d28258, working-capital-derived:e15492a3fff9dff0ab3c7273`
- Delivered wording: `재고 증가율은 매출 증가율보다 26.6%p 밑돌았습니다. 인도량·인센티브·제품 믹스와 함께 확인하며 수요 방향을 확정하지 않습니다.`

The delivered wording uses total Inventory, exact PIT-compatible relation/date, and cautious `가능성` language. It does not claim demand collapse, oversupply, Inventory Days, CCC, or hidden FCF.

`INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS`
