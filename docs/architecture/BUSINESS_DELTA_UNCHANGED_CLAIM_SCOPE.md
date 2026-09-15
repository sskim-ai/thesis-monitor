# Business-Delta UNCHANGED Claim Scope

Contract: `business-delta-unchanged-claim-scope-v1`

## Boundary

This contract is a post-model validation layer for
`business_thesis_context.text` when `BusinessDeltaEvidenceView` exposes only
`UNCHANGED`. It does not change the prompt, schema, evidence view, source
packet, or candidate.

The validator classifies each sentence-like clause as one of:

- `CURRENT_CHANGE_ASSERTION`
- `CONFIGURED_CONDITION_REFERENCE`
- `EXPLICIT_NO_OBSERVED_CHANGE`
- `CONFIGURED_CONDITION_NOT_FULFILLED`
- `CURRENT_CONDITION_FULFILLED`
- `BASELINE_THESIS_DESCRIPTION`
- `UNKNOWN_OR_AMBIGUOUS`

Only `CURRENT_CHANGE_ASSERTION` and `CURRENT_CONDITION_FULFILLED` contradict
an `UNCHANGED_ONLY` capability.

## Semantics

A configured strengthening or weakening condition is a monitoring rule, not
evidence that the thesis has changed. A statement that the condition is not
met, or that no observed change is confirmed, is valid `UNCHANGED` context.

An affirmative statement that the thesis strengthened or weakened remains a
hard failure. An affirmative statement that a configured condition was met is
also a hard failure. Negation is local: an earlier negative condition clause
cannot suppress a later affirmative current-change claim.

The Korean and English patterns implement the same distinctions. Unknown or
ambiguous wording is not upgraded into a current change by lexical proximity
alone.

## Ownership

`BusinessDeltaEvidenceView` remains the sole source of pre-model evidence
capability and direction semantics. The claim classifier reads only the final
candidate text and contributes post-model validation audit metadata. It does
not create another evidence view or rederive evidence eligibility.

The M12AR PPE-only cash-conversion and FCF claim-scope contract remains frozen.
No cash-flow semantics are changed by this contract.
