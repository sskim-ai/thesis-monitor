# Phase 9.1E AI/Fallback Preview

Both preview channels consume the same `working_capital-user-visible-v1` context and preserve the
same context ID, metric family, relation ID, six canonical Fact IDs, balance date, semantic scope,
direction, displayed value, Unknown resolution, suppression reason, and numeric owner.

| Ticker | Family | Primary relation | Preview |
| --- | --- | --- | --- |
| 000660 | Inventory | Inventory vs COGS, `2.1%p` lower | memory ASP/mix/cycle check |
| 005490 | Inventory | Inventory vs revenue, `7.1%p` higher | steel spread/raw material/volume check |
| 005930 | Inventory | Inventory vs COGS, `35.8%p` higher | memory ASP/mix/cycle check |
| 010120 | exact Trade AR | Trade AR vs revenue, `18.0%p` higher | order-to-cash follow-up |
| 086280 | exact Trade AR | Trade AR vs revenue, `40.0%p` higher | transport collection follow-up |

The preview uses one relation and one exact number. It does not render balance tuples, DSO, CCC,
customer stress, demand collapse, thesis change, or valuation change. AI/fallback parity mismatches
are zero. All contexts remain `ai_enabled=false`, `fallback_enabled=false`, and
`user_visible_enabled=false` because the operating feature mode is `OFF`.
