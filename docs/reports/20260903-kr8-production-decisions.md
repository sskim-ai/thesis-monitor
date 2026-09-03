# 2026-09-03 KR8 Production Decisions

## Structured Production State

All eight deterministic production payloads had `status=no_material_change` and `business_thesis_change=no_material_change`.

| Ticker | Decision label | Directional balance | Lean | New-buyer view | Holder view | Actual delivery |
|---|---|---|---|---|---|---|
| 000660 | no_material_change | not present | not present | present | present | fallback sent |
| 003690 | no_material_change | not present | not present | present | present | fallback sent |
| 005490 | no_material_change | not present | not present | present | present | fallback sent |
| 005930 | no_material_change | not present | not present | present | present | fallback sent |
| 010120 | no_material_change | not present | not present | present | present | fallback sent |
| 012450 | no_material_change | not present | not present | present | present | fallback sent |
| 047810 | no_material_change | not present | not present | present | present | fallback sent |
| 086280 | no_material_change | not present | not present | present | present | fallback sent |

The older production `new_buyer_view` and `holder_view` fields existed for 8/8. Latest shadow structured-autonomy `directional_balance` and `lean` fields were `NOT_PRESENT_IN_PRODUCTION_REVISION` for 8/8 and were not synthesized.

## Delivered Core Judgments

- `000660`: HBM4 and AI-server high-value memory demand support profitability; the next check is HBM contribution/utilization with CAPEX and FCF.
- `003690`: renewal pricing, loss-ratio discipline, investment income, and capital adequacy determine sustainable ROE and dividends.
- `005490`: steel spread recovery and recurring lithium/material earnings must convert into FCF and ROIC.
- `005930`: HBM adoption and server-memory strength must convert into DS margin, company FCF, and ROIC.
- `010120`: North American power demand must convert into orders, revenue, margin, and cash collection.
- `012450`: defense backlog must convert into delivery, margin, and contract cash collection; US expansion requires disciplined capital allocation.
- `047810`: fighter/light-attack aircraft deliveries must convert backlog into revenue, normalized margin, and cash collection.
- `086280`: shipping/CKD/logistics volume, freight rates, and margin must convert into FCF and ROIC with non-affiliate growth.

These bullets summarize the exact delivered prose; the unmodified UTF-8 messages are the authority. The accepted AI candidate was not delivered: its receipt remained pending 9/9, while the deterministic fallback was sent 9/9.

