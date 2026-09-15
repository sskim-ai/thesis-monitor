# Shadow Frozen-Context Manifest

## Contract

`shadow-frozen-context-manifest-v1` is the pre-model integrity boundary for a
monitored shadow generation. The serialized writer key is
`frozen_contexts`. A historical `contexts` key may be normalized for read-only
replay, but new manifests never emit it.

If both keys are present, their normalized rows must be identical. Divergent
rows are a hard failure; the reader never guesses precedence.

## Context Row

Each row owns one context identity, one to four tickers, the canonical packet
hash for every ticker, one business-delta view hash, and five frozen inputs:

- monolithic prompt
- monolithic schema
- Stage 1 prompt
- Stage 1 schema
- Stage 2 schema

Input paths and SHA-256 values are verified before any model call. Paths must
remain beneath the generation's shadow artifact root.

## Coverage

The ordered concatenation of context tickers must equal the task-start active
universe. Context IDs are unique and sequential, tickers cannot repeat across
contexts, and no context may exceed four names. Packet file SHA-256 and
canonical JSON SHA-256 must both match the frozen packet registry.

## M12AL Boundary

M12AL changes only the shadow manifest producer, verifier, and runner plumbing.
It does not change model prompts, schemas, financial semantics, business-delta
semantics, two-stage ownership, or the context-preserving finalizer. The M12AK
formal fictional proof is reused only after function-level model-facing hashes
and unchanged semantic file hashes pass.

The stopped M12AK shadow generation is never resumed. A successful offline
historical replay authorizes a new generation ID, new invocation IDs, and a new
runtime namespace over the same verified local packets.
