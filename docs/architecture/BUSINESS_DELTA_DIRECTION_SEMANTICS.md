# Business Delta Direction Semantics

Contracts:

- `business-delta-evidence-capability-v1`
- `financial-comparison-direction-v1`

This extension preserves the M12AI capability gate and adds one canonical
source of direction metadata for verified typed financial comparisons. It
does not choose `business_thesis_change`; the model continues to own
materiality and thesis relevance.

## Safe Polarity Registry

The bounded higher-is-stronger registry contains only:

- `operating_cash_flow`
- `ocf_less_ppe_capex`

For a verified prior-year-comparable observation with matching period type,
duration, currency, unit scale, entity scope, statement basis, attribution
basis, evidence status, and derivation identity:

- current greater than prior supports `STRENGTHENED`
- current less than prior supports `WEAKENED`
- equal values emit no direction hint

Values are read from canonical typed evidence and compared with `Decimal`.
Rendered English or Korean wording is not a direction source.

## Context-Dependent Metrics

Inventory, receivables, working-capital balances, capital expenditure,
non-operating financial effects, cash balances, and sector-specific regulatory
metrics do not have universal polarity in this contract. They may remain
`ELIGIBLE_OBSERVED_CHANGE` while carrying no direction hint. This is a valid
AI-judgment surface, not missing data.

## Projection

The data flow is:

```text
canonical typed financial comparison
  -> BusinessDeltaEvidenceItem.supported_change_directions
  -> BusinessDeltaEvidenceView.eligible_change_direction_hints
```

The view projects non-empty item hints without recomputation. The projection
audit must report zero mismatches.

## Mixed Evidence

A changed state still requires at least one selected eligible observed-change
reference. A hard contradiction is proven only when all selected eligible
direction-capable evidence is known and none supports the chosen state. Safe
opposite-direction evidence is counterevidence, not an automatic rejection,
when another selected ref supports the observed direction. A genuinely
direction-unspecified eligible observation also leaves economic direction to
the model.

`UNRESOLVED` remains limited to selected conflicting directions or selected
eligible observations whose direction is genuinely unspecified. Baseline,
single-point, market-expectation, price, technical, and supply evidence cannot
serve as an unspecified-direction escape hatch.

## Safety Boundary

This contract adds no ticker exceptions, scores, evidence-count thresholds,
majority votes, post-model rewrites, provider fetches, production sends, or
monitoring mutations. Monolithic Core and two-stage Stage 1 consume the same
projected view and dynamic enum.
