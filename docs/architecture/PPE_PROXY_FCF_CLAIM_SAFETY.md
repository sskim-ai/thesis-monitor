# PPE-Only Cash-Conversion Claim Safety

Contract: `ppe-proxy-fcf-claim-polarity-v1`

## Boundary

`ocf_less_ppe_capex` is a derived cash-conversion proxy. It is not a
management-defined or full free-cash-flow metric. Its canonical fact identity,
arithmetic, period, currency, and lineage remain unchanged.

## Model-Facing Projection

The canonical fact type `cash_flow_fcf_ppe` is projected to models as:

```text
label = cash_conversion_ocf_less_ppe
metric_refs = []
financial_context.metric = ocf_less_ppe_capex
```

The empty metric-reference tuple is intentional. The current checkpoint metric
vocabulary has no safe identifier for this proxy, and `FCF` would overstate its
scope.

## Output Claims

The semantic validator classifies FCF wording within bounded clauses.
Descriptions such as `OCF less PPE acquisition cash outflow` and explicit
disclaimers such as `not FCF` are allowed. Affirmative, numeric, or proxy-as-FCF
attributions remain hard failures when supported only by the PPE proxy.

Negation applies only to its local clause. A later clause such as `but this is
effectively FCF` remains an affirmative violation. A disclaimer in one field
also cannot mask an affirmative FCF attribution in another candidate-owned
field.

## Non-Goals

This contract does not reconstruct missing non-PPE capital spending, rename
canonical storage facts, change public schemas, alter production delivery, or
add a new checkpoint metric.
