# Frozen Context Input Layout Compatibility

## Status

M12BF defines `frozen-context-input-layout-v1`, the shared verifier contract
for model-call inputs captured in a frozen fictional or monitored context.

The contract changes only frozen-state verification. It does not change model
prompts, schemas, evidence views, decision semantics, or final user output.

## Supported layouts

`LEGACY_FLAT` preserves completed fictional states:

```text
<input_name>: path
<input_name>_sha256: digest
```

`NESTED_INPUTS_V1` is canonical for newly produced monitored shadow states:

```text
inputs.<input_name>.path
inputs.<input_name>.sha256
```

One frozen-context row must use one coherent layout. A row that supplies both
representations, partially mixes them, or exposes an unknown representation is
rejected before a model process starts. There is no precedence or best-effort
fallback between layouts.

## Required inputs

Fictional two-stage contexts require:

```text
stage1_prompt
stage1_schema
stage2_schema
```

Monitored shadow contexts additionally require:

```text
monolithic_prompt
monolithic_schema
```

`stage2_prompt` is not a frozen required input because the current two-stage
pipeline derives it from the frozen Stage-1 core.

## Identity checks

The shared resolver returns exactly `path`, `sha256`, and `layout`. The verifier
then requires:

- a recognized, unambiguous layout;
- a non-empty path and valid SHA-256 identity;
- the expected semantic filename;
- the expected `context-XX` directory;
- an existing regular file; and
- an exact file SHA-256 match.

Missing, changed, malformed, or ambiguous inputs fail closed. The verifier and
resolver are included in the frozen critical-code identity, so a verifier code
change requires a new generation. Historical state is never rewritten merely
to satisfy a newer consumer.

## M12BF evidence gates

Before the new monitored shadow can call the model, M12BF requires:

1. The authoritative M12BE bundle passes independent ZIP/index verification.
2. The stopped M12BE shadow resolves 30 nested input identities across six
   contexts with no missing file, ambiguity, or hash mismatch.
3. The completed M12BD fictional state resolves six legacy-flat identities
   without changing the archived state.
4. Positive and negative layout fixtures pass.
5. M12BE subject-count and exact ticker-set contracts remain unchanged.
6. Every model-facing semantic hash remains identical to the complete M12BD
   formal proof.
7. The newly frozen shadow passes the same shared verifier under its own code
   hash before any model process starts.

The stopped M12BE generation is replay evidence only and cannot be resumed.
The complete M12BD fictional proof may be reused because verifier mechanics are
outside the model-facing semantic surface.

## Operational boundary

M12BF is local-only. It performs no provider refresh, production database
mutation, monitoring registration or stop, notification write, Telegram send,
main merge, deployment, remote push, or automatic schedule resume.
