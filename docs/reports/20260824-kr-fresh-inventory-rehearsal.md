# KR Fresh Inventory Rehearsal

Three of seven subjects selected Inventory under `SELECTIVE_INVENTORY`:

| Ticker | Relation | Display | Balance date | Context |
|---|---|---:|---|---|
| 000660 | Inventory vs COGS | 2.1%p lower | 2026-06-30 | `wc-visible-770e781f7bc17c62a0d0b9a8` |
| 005490 | Inventory vs revenue | 7.1%p greater | 2026-06-30 | `wc-visible-3bf923f9576b427cb8970899` |
| 005930 | Inventory vs COGS | 35.8%p greater | 2026-06-30 | `wc-visible-5550b2e3e74ca3463ceb0db8` |

All three are `exact_total_inventory`, `CURRENT_FORMAL`, PIT PASS, and bound to six canonical
Fact/relation inputs each. Fallback wording uses one cautious relation, adds industry context, and
does not infer demand, oversupply, Inventory Days, or CCC. Cash-flow user-visible selection was 0
for the KR cohort, so there was no duplicate FCF/Inventory accounting block.

New exact Trade AR enrichment: 0. Broad AR enrichment: 0. AP enrichment: 0. LS ELECTRIC retains one
pre-existing qualitative thesis watch item mentioning receivables and inventory; it has no new AR
Fact, exact number, context ID, or working-capital enrichment.

The AI candidate was not generated, so the mandatory AI/fallback parity leg was not exercised.
Accordingly the full rehearsal state cannot be PASS even though canonical selection and fallback
rendering are safe.

`INVENTORY_USER_VISIBLE_REHEARSAL = FAIL (AI_PARITY_NOT_OBSERVED)`
