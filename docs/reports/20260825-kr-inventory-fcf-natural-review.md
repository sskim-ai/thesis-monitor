# 2026-08-25 KR Inventory / FCF Natural Review

## User-Visible Selection

| Ticker | Inventory | Metric | Relation | Direction | Display | Balance date | Context ID | FCF state | FCF reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000660 | SELECTED | inventory | inventory_vs_cogs | LOWER | 2.1%p | 2026-06-30 | wc-visible-8f7b1b1f2fa2150a006a96c2 | SUPPRESSED | initial_market_or_source_scope_excluded |
| 003690 | SUPPRESSED | Not selected | Not selected | Not selected | Not selected | Not selected | Not selected | NOT_APPLICABLE | financial_industry_not_applicable |
| 005490 | SELECTED | inventory | inventory_vs_revenue | GREATER | 7.1%p | 2026-06-30 | wc-visible-01e5d201dad2daff7a2beea4 | SUPPRESSED | initial_market_or_source_scope_excluded |
| 005930 | SELECTED | inventory | inventory_vs_cogs | GREATER | 35.8%p | 2026-06-30 | wc-visible-eca82f51687c7790f9dce5c0 | SUPPRESSED | initial_market_or_source_scope_excluded |
| 010120 | SUPPRESSED | Not selected | Not selected | Not selected | Not selected | Not selected | Not selected | SUPPRESSED | initial_market_or_source_scope_excluded |
| 012450 | SELECTED | inventory | inventory_vs_revenue | LOWER | 27.1%p | 2026-06-30 | wc-visible-4c02afd1355f4ee06c1d1ef6 | SUPPRESSED | initial_market_or_source_scope_excluded |
| 086280 | SUPPRESSED | Not selected | Not selected | Not selected | Not selected | Not selected | Not selected | SUPPRESSED | initial_market_or_source_scope_excluded |

The four selected Inventory relations use exact total Inventory semantics, PIT `PASS`, balance date
`2026-06-30`, and cautious directional wording. No demand, oversupply, Inventory Days, CCC, or hidden
FCF claim was introduced.

## Inventory Lineage

| Ticker | Relation ID | Selected Fact IDs |
| --- | --- | --- |
| 000660 | `working-capital-relation:38a9a0707d38e538ccdb2e7e` | `working-capital-reported:b742cc7afdc66afa6d7e1135`, `working-capital-reported:3d542b94d368f70add0d6170`, `working-capital-reported:e82f96805a456becf97cc6f2`, `working-capital-reported:7fe8e5e809b98ce4701caf99`, `working-capital-derived:76bafa4ff3bc5b672001b37f`, `working-capital-derived:06d86117c3f4ba6209336c5c` |
| 005490 | `working-capital-relation:ab1a9a616bcd8d6023b2db06` | `working-capital-reported:8eb93ea161575e8239c3b49a`, `working-capital-reported:57f4cb34ba90e597a438ef41`, `working-capital-reported:e49769235bd25c78c4d0413d`, `working-capital-reported:cda0eade6f371725e4dda70a`, `working-capital-derived:c443106cc507b5d6c464f833`, `working-capital-derived:9e40436bfef8c3e37e8ba6aa` |
| 005930 | `working-capital-relation:4b43f129a5c3b9dbca52fa29` | `working-capital-reported:a2f1219fd2a751859537f817`, `working-capital-reported:ee70a0ad53bfc98289edae27`, `working-capital-reported:3a7d30e63279040add6dd0ee`, `working-capital-reported:77acb257b2ddead3be5ede82`, `working-capital-derived:cabc0285c12ba1e945788d0e`, `working-capital-derived:0e7a663e3ca101307dfb04cb` |
| 012450 | `working-capital-relation:dcc70619e17d5fe312caee22` | `working-capital-reported:2b9475e4313020e1d43e4d3d`, `working-capital-reported:87773f2a21f767de6b5884b7`, `working-capital-reported:76cdc2c19635b30ca3832d76`, `working-capital-reported:684f98bae49e240e7190042b`, `working-capital-derived:202450830ef87dcccdc5504b`, `working-capital-derived:96889525987e78d2a8282fa1` |

## Trade AR Shadow Guard

The natural working-capital shadow canary selected exact Trade AR for `010120` (Trade AR growth
18.0%p above Revenue growth) and `086280` (40.0%p above). Both used current formal 2026-06-30 facts,
PIT `PASS`, and exact `CurrentTradeReceivables` semantics. Numeric binding was `6 automatic / 0
manual / 0 rejected / 0 unresolved`; production influence, Telegram delivery, assessment mutation,
and warning mutation were all zero.

## Cash Flow

Phase 9.0E selected no KR FCF context. Six non-financial names were source-scope suppressed and
Korean Re remained `NOT_APPLICABLE`. The independent cash-flow shadow canary completed `PASS`, but
there was no rendered user-visible FCF context and no FCF/Inventory coexistence case.

```text
INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS
TRADE_AR_NATURAL_PROOF = LIVE_PASS
PHASE_9_0E_KR_REGRESSION = NOT_OBSERVED
Trade AR user-visible = 0
Broad AR user-visible = 0
AP user-visible = 0
```
