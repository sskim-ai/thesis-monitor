# Rehearsal 19:34 Inventory Parity

`SELECTIVE_INVENTORY` selected three subjects and produced zero AI/fallback mismatches.

| Ticker | Balance date | Relation | Display | AI | Fallback |
|---|---|---|---:|---|---|
| 000660 | 2026-06-30 | inventory growth below COGS growth | 2.1%p | present | present |
| 005490 | 2026-06-30 | inventory growth above revenue growth | 7.1%p | present | present |
| 005930 | 2026-06-30 | inventory growth above COGS growth | 35.8%p | present | present |

All three AI claims reference their canonical working-capital relation IDs. Exact Trade AR,
broad AR, and AP user-visible enrichments are each zero.

`INVENTORY_USER_VISIBLE_REHEARSAL = PASS`.
