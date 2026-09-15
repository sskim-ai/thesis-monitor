# Business Delta Evidence Capability

Contract: `business-delta-evidence-capability-v1`

This contract classifies the complete pre-model Core evidence catalog for each
issuer. It does not infer investment direction and it does not rewrite model
output.

## Capabilities

- `UNCHANGED_ONLY`: no evidence establishes an observed change against a prior
  or baseline state. The structured-output enum is restricted to `UNCHANGED`.
- `AI_JUDGMENT`: at least one verified observed change is available. The model
  may select any business-thesis-change state, subject to grounding validation.
- `INPUT_AMBIGUOUS`: change-like evidence is present but its lineage or baseline
  cannot be classified safely. Model invocation stops before generation.

## Evidence Roles

- `ELIGIBLE_OBSERVED_CHANGE`: verified comparison, typed monitoring transition,
  or dated issuer event with explicit baseline and current state.
- `THESIS_BASELINE_CONTEXT`: stored thesis, driver, or configured condition.
- `CURRENT_CONTEXT_ONLY`: a current single-point business or financial fact.
- `EXCLUDED_NON_BUSINESS_DELTA`: valuation, expectations, macro, price,
  technical, supply, or other non-business-change evidence.
- `AMBIGUOUS_CHANGE_LINEAGE`: change-like evidence without sufficient lineage.

The complete Core catalog remains available for absolute direction, risk,
valuation, reevaluation conditions, and stance. The capability gate only limits
`business_thesis_change`.

## Generation Boundary

Monolithic Core and two-stage Stage 1 receive the same
`business_delta_evidence_view` and the same per-ticker enum. Stage 2 does not
own business-thesis change. A changed state must cite an eligible delta ref;
`UNRESOLVED` requires conflicting or genuinely ambiguous eligible evidence.

The legacy hard validator remains active. There are no ticker exceptions,
evidence-count thresholds, score rules, majority votes, or post-model rewrites.
