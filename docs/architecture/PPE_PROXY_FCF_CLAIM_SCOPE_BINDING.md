# PPE Proxy / FCF Claim Scope Binding

Status: M12AR local shadow implementation

## Boundary

The canonical `ocf_less_ppe_capex` evidence remains a PPE-only cash-conversion
proxy. It is not management-defined free cash flow and must not be presented as
such. M12AR changes only post-model claim extraction and validation. Prompts,
model schemas, evidence projection, decision ownership, and production behavior
remain unchanged.

## Claim Row Contract

`financial-claim-row-v2` binds each prose field to its own evidence scope:

- `text` and `summary` use the mapping's sibling `evidence_refs` only.
- `confirmation_business_condition` uses
  `confirmation_business_condition_refs` only.
- `business_invalidation_condition` uses
  `business_invalidation_condition_refs` only.
- summaries without refs inherit no candidate-global evidence.
- nested arrays preserve stable field paths.

Each row records its field path, text, bound refs, and field semantic role.

## PPE Proxy Safety

`ppe_only_cash_conversion_proxy_called_fcf` remains a hard failure when:

1. A claim bound to `ocf_less_ppe_capex` calls that evidence FCF, free cash
   flow, or 잉여현금흐름.
2. A claim explicitly equates the proxy with FCF, including without refs.

The presence of a valid proxy elsewhere in the candidate is not evidence that
an unrelated FCF condition refers to that proxy. Candidate-global proxy taint
is removed.

## Current FCF Safety

Removing candidate-global taint does not permit unsupported current FCF claims.
An affirmative current FCF assertion without an appropriate current FCF owner
fails separately as `unsupported_current_fcf_claim`. Configured future
confirmation/invalidation conditions and clearly unconfirmed stance summaries
do not assert a current FCF state.

## Frozen Contracts

M12AR does not change:

- financial-sector exclusion scope
- `MarketExpectationEvidenceView`
- `BusinessDeltaEvidenceView`
- QTD/YTD period semantics
- Stage 2 Korean lexical safety
- direction/timing ownership
- ADR/security basis safety
- renderer or production integration

The complete M12AQ fictional proof may be reused only after all model-facing
semantic hashes remain unchanged and its 24 Stage 1 plus 24 composed candidates
pass an offline re-audit under this validator.
