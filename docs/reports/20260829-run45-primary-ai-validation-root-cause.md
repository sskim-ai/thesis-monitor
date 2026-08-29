# Run-45 Primary AI Validation Root Cause

Frozen packet: `2026-08-29-us-run-45-0e9c491532df`.

- Before: `37` errors.
- After: `0` errors.
- Root: candidate construction omitted structured ownership metadata even though the packet contained canonical evidence.

| Class | Count |
| --- | --- |
| financial_quality_denied_fact_used | 2 |
| interpretation_unknown_fact_ids | 2 |
| inventory_business_owner_fact_missing | 2 |
| inventory_label_missing | 2 |
| inventory_numeric_ownership_count | 2 |
| inventory_primary_numeric_claim_count | 2 |
| inventory_relation_not_declared | 2 |
| unknown_fact_ids | 2 |
| valuation_interpretation_numeric_occurrence_uncovered | 18 |
| valuation_interpretation_occurrence_uncovered | 1 |
| valuation_interpretation_unknown_occurrence_uncovered | 2 |

The repair runs before unchanged strict validation and records every deterministic handoff or suppression.
