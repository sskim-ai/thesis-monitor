# KR Afternoon Canary Simulation

- Evidence class: `CURRENT_CODE_REPLAY`
- Policy: market `<=1`, stock `<=2`, total `<=3`
- Eligible: `8`
- Selected: `3`
- Selected keys: `market:2026-08-25-kr-run-38-6cd8c5d5091b, stock:012450, stock:000660`
- Scoped runtime quality: `PASSED`
- Delivery: `0`

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

The repaired prerequisite permits a non-zero deterministic selection while preserving the configured `1/2/3` ceiling.
