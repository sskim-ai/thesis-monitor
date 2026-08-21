# Phase 9.1E Numeric And Semantic Validation

| Gate | Result |
| --- | --- |
| numeric binding | 5 automatic, 0 manual/rejected/unresolved |
| duplicate context IDs | 0 |
| AI/fallback parity errors | 0 |
| semantic/causal errors | 0 |
| resolved-Unknown contradictions | 0 |
| exact preview repetitions | 0 |
| runtime quality | PASS |

Every displayed value comes from the single Phase 9.1D numeric claim owned by `business_earnings`
and remains attached to its canonical relation and input Fact IDs. The formatter preserves the
relation direction and one decimal percentage-point display; the preview performs no arithmetic.

The semantic guard accepts exact total Inventory and exact Trade AR only. It rejects inventory
components, broad AR, contract assets, all AP, stale/non-current relations, wrong PIT, wrong owner,
missing lineage, DSO/Inventory Days/DPO/CCC, unsupported causality, and WC-only thesis or valuation
changes. An exact Trade AR relation never becomes a claim that customers are failing to pay.
