# KR Valuation Numeric-Ref Negative Controls

Implementation: `b39c2ea38a8d5d3466889a9da394df05ad95701a`

| Control | Expected | Result |
| --- | --- | --- |
| safe current PBR with `valuation:book` declaration | allow | PASS |
| safe historical PBR percentile with `valuation:historical_pb` declaration | allow | PASS |
| undeclared parent/typed valuation ref | reject | PASS |
| historical declaration owning current PBR | reject | PASS |
| PBR source with denied security basis | reject | PASS |
| provider multiple reversed into BVPS | reject by existing basis contract | PASS |

Focused command:

```text
pytest -q tests/test_numeric_label_binding.py tests/test_ai_review_service.py \
  -k 'numeric_fact_reference or typed_valuation or pbr'
```

Result: `18 passed, 218 deselected`.

The full numeric-label suite also passed: `58 passed`. No threshold, allowlist
wildcard, or ticker exception was introduced.

