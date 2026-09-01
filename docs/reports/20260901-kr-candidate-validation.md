# KR Candidate Validation

## Legacy validation timeline

Primary initial errors (`8`):

- `000660:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`
- `003690:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`
- `005490:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`
- `005930:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`
- `010120:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`
- `012450:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`
- `047810:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`
- `086280:numeric_fact_ref_raw_postposition:p_price:price_positioning.text`

Primary final errors (`7`):

- `047810:numbers_without_provenance:core_judgment.text:21,50`
- `047810:numbers_without_provenance:business_earnings.text:21,50`
- `047810:numbers_without_provenance:price_positioning.new_observer_view:21,50`
- `047810:numbers_without_provenance:supply_analysis.text:21,50`
- `047810:numbers_without_provenance:valuation_analysis.text:21,50`
- `047810:numbers_without_provenance:priority_watch[0]:21,50`
- `000660:valuation_interpretation_evidence_invalid:v_quality_earnings:quality_unknown:earnings`

Backup initial errors (`10`):

- `market_review:numeric_fact_ref_semantic_not_supported:kospi_return:market:cross-section:index:KOSPI:fields.return_pct`
- `market_review:numeric_fact_ref_semantic_not_supported:kosdaq_return:market:cross-section:index:KOSDAQ:fields.return_pct`
- `000660:industry_reasoning_span_not_unique:industry_missing_driver`
- `003690:industry_reasoning_span_not_unique:industry_missing_driver`
- `005490:industry_reasoning_span_not_unique:industry_missing_driver`
- `005930:industry_reasoning_span_not_unique:industry_missing_driver`
- `010120:industry_reasoning_span_not_unique:industry_missing_driver`
- `012450:industry_reasoning_span_not_unique:industry_missing_driver`
- `047810:industry_reasoning_span_not_unique:industry_missing_driver`
- `086280:industry_reasoning_span_not_unique:industry_missing_driver`

Backup final errors (`7`):

- `005930:unsupported_risk_reward_comparison:core_judgment.text`
- `047810:numbers_without_provenance:unknowns[0]:21,50`
- `047810:numbers_without_provenance:business_earnings.text:21,50`
- `047810:numbers_without_provenance:price_positioning.new_observer_view:21,50`
- `047810:numbers_without_provenance:valuation_analysis.text:21,50`
- `047810:numbers_without_provenance:priority_watch[0]:21,50`
- `047810:numbers_without_provenance:next_checks[0]:21,50`

The `21,50` errors are phantom numeric detections from the product names `KF-21` and `FA-50`. The 005930 RR error is a genuine semantic guard. These are secondary because the V2 path had already failed before model invocation.
