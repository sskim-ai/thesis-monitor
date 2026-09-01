# V2 Codex CLI Path Contract

Contract: `v2-codex-cli-path-v1`

## Ownership

Persisted claim paths may remain repository-relative. The V2 runtime owns the conversion from a
persisted path to an invocation path and resolves every relative path against the repository root
derived from the runtime module location. Process launch cwd never owns this conversion.

Before a signed-in Codex subprocess starts, `cwd`, prompt, output, log, and output schema are
canonical absolute paths. The runtime verifies that cwd, prompt, schema, output parent, and log
parent exist. A failed check raises `V2CLIPathPreconditionError` before a model call and is not
retried as a transport failure.

## Natural Shape

```text
claim.final_output_path = data/ai_review/outbox/<claim>.json
  -> repository root / data/ai_review/outbox/<claim>.json
  -> accepted_v2_production_paths(...)
  -> repository root / data/ai_review/claims/<claim>.decision-v2-schema.json
```

The schema path contains `data/ai_review/claims` exactly once. Primary, backup, schema repair, and
subject repair invocations share `_invoke_signed_in_codex`; there is no market-specific path logic.

## Safe Telemetry

The preflight log records booleans only: absolute cwd/schema, cwd/schema/prompt existence, and
output/log parent existence. User-facing output never receives raw filesystem paths.

