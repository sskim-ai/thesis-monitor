# KR Afternoon Current-Code Adapter Replay

- Evidence class: `CURRENT_CODE_REPLAY`
- Packet: `2026-08-25-kr-run-38-6cd8c5d5091b`
- Run ID: `38`
- Generated: `2026-08-25T07:06:11.582752+00:00`
- Actual delivery: `deterministic_fallback` / `8/8`
- Current validation errors: `0`
- Free Analyst eligible: `8/8`
- Adaptive safe terminal outputs: `8/8`
- Scoped runtime quality: `PASSED`
- Provider recollection / delivery: `0 / 0`

| Slot | Eligible | Renderer | Selected | Reason |
| --- | --- | --- | --- | --- |
| __DAILY_DIGEST_KR__ | True | CONCISE_HYBRID | True | validated_material_candidate_within_canary_limits |
| 000660 | True | CONCISE_HYBRID | True | validated_material_candidate_within_canary_limits |
| 003690 | True | CONCISE_HYBRID | False | eligible_not_selected_within_canary_limits |
| 005490 | True | DIRECT_ANALYST | False | eligible_not_selected_within_canary_limits |
| 005930 | True | CONCISE_HYBRID | False | eligible_not_selected_within_canary_limits |
| 010120 | True | CONCISE_HYBRID | False | eligible_not_selected_within_canary_limits |
| 012450 | True | DIRECT_ANALYST | True | validated_material_candidate_within_canary_limits |
| 086280 | True | CONCISE_HYBRID | False | eligible_not_selected_within_canary_limits |

Regression evidence preserved from the same immutable packet: stock-level 1D/5D/20D participant reconciliation `21/21 PASS`; residual attribution, institution double count, and timeless mixed-window claims `0`; Inventory total semantics and PIT `PASS`; Trade AR/Broad AR/AP user-visible `0/0/0`; macro false-current claims `0`.

`KR_INVESTOR_FLOW_REPLAY = PASS`

`KR_INVENTORY_REPLAY = PASS`

`TRADE_AR_USER_VISIBLE_REPLAY = 0`

`PHASE_9_0E_KR_REPLAY = NOT_OBSERVED`

`KR_MACRO_TEMPORAL_REPLAY = PASS`

`KR_FREE_ANALYST_REPLAY = PASS`

`KR_ADAPTIVE_REPLAY = PASS`
