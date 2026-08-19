# Run-26 AI Validation Repair

## Before

- `RXRX:numeric_usage_semantic_mismatch:valuation:current:fields.historical_pb_statistics.current_value`
- `RXRX:numbers_without_provenance:valuation_analysis.text:1.8`
- `WULF:numeric_usage_semantic_mismatch:valuation:current:fields.historical_pb_statistics.current_value`
- `WULF:numbers_without_provenance:valuation_analysis.text:52.91`
- `CORZ:valuation_interpretation_metric_span_mismatch:corz_val_quality:earnings`
- `CORZ:valuation_interpretation_unknown_occurrence_uncovered:valuation_analysis.text`

## Repair

- Visible current PBR references now bind to `fields.price_to_book` when the base
  value and historical `current_value` are equal. Historical median and percentile
  keep their own semantics.
- The phrase `실적 기반 가치평가` is recognized as an earnings metric span, so the
  CORZ quality-unknown occurrence is exactly covered without relaxing validation.
- The archived ambiguous night-futures facts and their prose were removed from the
  repaired packet copy.

## After

- Binding errors: `0`
- Typed valuation errors: `0`
- Full validator errors: `0`
- Result: `PASSED`
- Manual numeric bindings: `0`
- Original delivery replay: `0`
