# US Candidate Validation

The packet-bound V2 candidate validator was not reached because the V2 model produced no output.

The separate daily-review candidate had an initial rejected attempt with `47` errors:

| Class | Count |
| --- | --- |
| SCHEMA_EXTRA_FIELD | 14 |
| VALUATION_INTERPRETATION_BINDING | 33 |

The terminal daily-review candidate then passed numeric binding with `124` automatic bindings, `0` manual, `0` rejected, and `0` unresolved. No product/model identifier digit was treated as a phantom standalone numeric claim.

`US_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC = 0`
