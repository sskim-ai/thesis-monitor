# US AI Directional Binding Root Cause

- Packet: `2026-08-25-us-run-37-7e04812311c2`
- Pre-repair hard errors: `4`
- Affected tickers: `MU`, `TSLA`
- Root cause: the canonical working-capital context retained a signed gap and direction, but the user-visible relation fact and numeric registry serialized only `fields.gap_percentage_points_abs`. The binder therefore produced an absolute-gap claim while the authored sentence asserted a comparator and `lower` direction.

Pipeline trace:

`canonical Inventory/comparator Facts -> signed working-capital relation -> user-visible context -> abs-only fact catalog -> abs numeric ref -> binder -> semantic mismatch -> uncovered number`

Exact original errors:

```text
MU:numeric_usage_semantic_mismatch:working-capital-relation:dbdfd04e725e83528d8fdd31:fields.gap_percentage_points_abs
MU:numbers_without_provenance:business_earnings.text:15.7
TSLA:numeric_usage_semantic_mismatch:working-capital-relation:36181e61768dfd580d9ede01:fields.gap_percentage_points_abs
TSLA:numbers_without_provenance:business_earnings.text:26.6
```

The visible fallback numbers and directions were correct; the rejected AI provenance ownership was not direction-compatible.
