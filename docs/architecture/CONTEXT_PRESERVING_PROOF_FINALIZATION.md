# Context-Preserving Proof Finalization

Contract: `context-preserving-proof-finalization-v1`

## Boundary

`DirectionalCoreBatch` is a model-context contract. It accepts one to four
candidates and remains unchanged. A repetition-level or cohort-level proof
aggregate is not a model context and must not be represented by that schema.

## Fictional Finalization

For every `(repetition, context)` pair, Stage 1 and Stage 2 must identify the
same ticker set. The finalizer validates the context's composed candidates in a
`DirectionalCoreBatch` of at most four candidates, then stores each validated
row in an ordinary aggregate list keyed by `(repetition, ticker)`.

The aggregate requires exact coverage, no duplicate identity, no omitted row,
matching Stage 1 and Stage 2 invocation lineage, and an unchanged core hash.
Across two contexts and three repetitions this yields 24 unique rows without
constructing an eight-candidate model batch.

## Monitored Shadow Finalization

Each monolithic, Stage 1, and Stage 2 context is validated independently. The
cohort audit joins context-validated rows by ticker and retains all invocation
IDs and the core snapshot hash. A 22-name cohort therefore remains six model
contexts and one ordinary 22-row proof aggregate.

## Hard Failures

The finalizer fails closed on missing or duplicate candidates, context
membership mismatch, generation mismatch, context size above four, ticker
crossover, core mutation, or incomplete aggregate identity coverage.

It does not alter prompts, model schemas, evidence capability, financial
direction semantics, ownership, thresholds, rendering, or model output.
