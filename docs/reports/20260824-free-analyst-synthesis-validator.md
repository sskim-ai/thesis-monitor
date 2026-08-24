# Evidence-Locked Free Analyst Synthesis Validator

The shadow validator rejects an analysis item unless its support type is classified, every evidence
reference exists, the typed rule has all required evidence sections, and bounded claim language
preserves uncertainty. Direct facts must remain source spans. New synthesis cannot carry numbers;
all exact numbers therefore stay in already-bound direct evidence.

Typed rules distinguish Inventory, insurance applicability, order-to-cash, contract-asset recovery,
fleet reinvestment, HPC execution, platform revenue quality, current-formal FCF, memory-cycle FCF,
expectation thresholds, positioning, price/execution, and temporal boundaries. A generic evidence
reference is not wildcard approval.

| Negative control | Result | Rejections | 
|---|---|---:|
| hidden_arithmetic_rejections | PASS | 1 |
| external_knowledge_rejections | PASS | 1 |
| unsupported_causality_rejections | PASS | 1 |
| stronger_than_evidence_rejections | PASS | 1 |
| temporal_leakage_rejections | PASS | 1 |
| trade_ar_leak_rejections | PASS | 1 |

Existing numeric, semantic, temporal, language, price/RR, valuation-basis, working-capital, and FCF
validators remain unchanged. The synthesis validator is additive and shadow-only.
