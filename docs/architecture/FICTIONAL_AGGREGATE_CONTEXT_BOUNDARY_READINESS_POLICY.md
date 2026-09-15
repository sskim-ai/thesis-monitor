# Fictional Aggregate Context Boundary and Readiness Policy

## Status

Contract: `fictional-aggregate-context-boundary-readiness-policy-v1`

This contract is local proof-harness infrastructure. It does not change model
prompts, model schemas, production packets, public schemas, or delivery paths.

## Context boundary

`DirectionalCoreBatch` is a model-call batch and contains at most four
candidates. A fictional proof with two contexts is finalized as two independent
four-candidate batches. Only validated audit rows are aggregated across contexts.

Every aggregate row retains repetition, context, ticker, Stage-1 source hash,
Stage-2 stance hash, composition hash, pre-compose core hash, and post-compose
core hash. Missing, duplicate, or cross-context identities fail closed.

## Readiness boundary

Objective failures remain hard gates. These include schema and semantic errors,
invalid evidence references, core mutation, context identity loss, runtime
failure, and provider or production side effects.

Semantically valid repetition variance is diagnostic. Primary direction,
business-delta materiality, new-buyer stance, holder stance, and same-direction
calibration variance do not independently fail readiness. No fixture-specific
decision enum is a generic readiness requirement.

## Frozen proof reuse

A completed frozen model proof may be re-finalized without new model calls only
when all model-facing prompts, schemas, evidence views, projections, ownership
rules, receipts, and outputs remain unchanged. The immutable source archive is
never rewritten. The derived replay state may bind to the repaired harness hash,
with the original state and hashes retained in the audit output.

## Monitored shadow

After formal fictional acceptance, the active monitored cohort is rebuilt from
existing frozen local packets. Monolithic, Stage 1, and Stage 2 consume the same
packet hash for each ticker. Provider fetches and production side effects remain
zero. Decision differences are policy diagnostics unless an objective semantic,
identity, grounding, mutation, or runtime failure is present.

## Handoff

A clean complete cohort is handed to
`DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN`. It does not
authorize a fresh unseen proof, a main merge, deployment, or monitoring resume.
