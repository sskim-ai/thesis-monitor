# US Cross-Message Synthesis Specificity Audit

Date: 2026-08-26 KST
Packet: `2026-08-25-us-run-37-7e04812311c2`
Contract: `cross-message-synthesis-specificity-v1`

## Batch Result

| Measure | Before | After |
|---|---:|---:|
| claim-bearing synthesis lines | 18 | 17 |
| generic shared lines | 8 | 0 |
| entity-specific shared-structure lines | 0 | 3 |
| entity-specific unique lines | 10 | 14 |
| cross-industry generic repetition | 4 | 0 |
| same-industry acceptable overlap | 0 | 1 |
| messages missing discriminator when support exists | 4 | 0 |

Before-repair rejected keys were `stock:CORZ`, `stock:HUT`, `stock:TSM`, and `stock:WULF`.
After repair, rejected keys are empty.

## Interpretation

The three remaining shared-structure lines belong to the actual HPC/data-center cohort. The batch
contract counts one legitimate same-industry overlap because the shared structure is accompanied by
entity-specific evidence. It does not demand cosmetic lexical novelty.

TSM is no longer in that cohort. Its post-repair owner is `semiconductor_foundry`, with supported
`foundry_advanced_node` and `foundry_wafer_asp` discriminators. CRCL remains the positive control
and preserves `stablecoin_reserve_income` plus `stablecoin_non_interest_revenue`.

## Human Review

| Classification | Count |
|---|---:|
| MATERIAL_IMPROVEMENT | 4 |
| GOOD_CURRENT_STATE | 10 |
| MINOR_IMPROVEMENT | 0 |
| NO_MEANINGFUL_CHANGE | 0 |
| REGRESSION | 0 |

The four material improvements are CORZ, HUT, WULF, and TSM.

`US_CROSS_INDUSTRY_GENERIC_REPETITION = PASS`
`US_SAME_INDUSTRY_OVERLAP_HANDLING = PASS`
