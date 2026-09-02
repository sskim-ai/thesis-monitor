# KR Candidate Validation

- attempt 1: `rejected`, 2 errors, 134 automatic bindings
  - `market_review:numeric_fact_ref_redundant_authored_label:m_kospi_breadth:core_judgment.text:market_advance_ratio`
  - `market_review:numeric_fact_ref_redundant_authored_label:m_kosdaq_breadth:core_judgment.text:market_advance_ratio`
- attempt 2: `rejected`, 15 errors, 136 automatic bindings
  - `000660:numeric_usage_direction_mismatch:working-capital-relation:38a9a0707d38e538ccdb2e7e:fields.gap_percentage_points_signed`
  - `000660:numbers_without_provenance:business_earnings.text:2.1`
  - `000660:inventory_direction_wording_mismatch`
  - `003690:holder_decision_variable_missing`
  - `005490:numeric_usage_semantic_mismatch:working-capital-relation:ab1a9a616bcd8d6023b2db06:fields.gap_percentage_points_signed`
  - `005490:numeric_usage_direction_mismatch:working-capital-relation:ab1a9a616bcd8d6023b2db06:fields.gap_percentage_points_signed`
  - `005490:numbers_without_provenance:business_earnings.text:7.1`
  - `005490:inventory_direction_wording_mismatch`
  - `005930:numeric_usage_semantic_mismatch:working-capital-relation:4b43f129a5c3b9dbca52fa29:fields.gap_percentage_points_signed`
  - `005930:numeric_usage_direction_mismatch:working-capital-relation:4b43f129a5c3b9dbca52fa29:fields.gap_percentage_points_signed`
  - `005930:numbers_without_provenance:business_earnings.text:35.8`
  - `005930:inventory_direction_wording_mismatch`
  - `000660:valuation_interpretation_scope_economic_scope_mismatch:v_quality_earnings`
  - `010120:valuation_interpretation_scope_economic_scope_mismatch:v_unknown_pe`
  - `012450:valuation_interpretation_scope_economic_scope_mismatch:v_unknown_pe`

The correction attempt did not converge. Thresholds and validators were unchanged. `KR_PHANTOM_NUMERIC_ERRORS = 0`; manual numeric bindings and unresolved raw numeric claims were 0, while semantic/direction/scope checks correctly rejected the bundle. `KR_FINAL_VALIDATION_PASS_COUNT = 0`; `KR_FINAL_VALIDATION_REJECT_COUNT = 2` bundle attempts; production terminal messages were `FALLBACK = 9`.
