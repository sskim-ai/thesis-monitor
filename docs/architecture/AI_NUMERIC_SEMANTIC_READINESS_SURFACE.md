# AI Numeric-Semantic Readiness Surface

Contract: `ai-numeric-semantic-consumer-surface-v1`.

## Flow

```text
canonical facts
-> consumer-scope projection
-> existing numeric-semantic registry validation
-> consumer readiness
```

The existing numeric semantic resolver, provenance rules, units, prose eligibility, and
unsupported-number behavior are unchanged. Projection occurs before coverage aggregation and
uses only structured consumer ownership.

## Diagnostics

Each result records:

- `consumer`
- `total_entry_count`
- `included_fact_count`
- `included_numeric_count`
- `excluded_nonconsumer_fact_count`
- `excluded_nonconsumer_numeric_count`
- `unsupported_included_numeric_count`
- safe exclusion identities with `NOT_IN_CONSUMER_SCOPE`

The existing `entry_count`, registration, prose eligibility, unsupported list, and readiness
fields continue to describe only included entries. Unclassified entries remain included.

## Prompt Parity

`build_decision_evidence_packet` applies the same `STOCK_V2` fact projection before creating
canonical evidence references. Every included stock numeric occurrence must have a fact in that
prompt surface. Standalone market occurrences cannot enter the stock prompt implicitly; a
selected market transmission is copied into the stock catalog with explicit `STOCK_V2`
ownership.

