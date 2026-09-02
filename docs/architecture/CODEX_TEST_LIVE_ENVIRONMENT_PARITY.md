# Codex Test and Live Environment Parity

Test and natural scheduler invocations share one helper for executable selection, absolute
artifact paths, model, effort, sandbox, schema, and claim-scoped runtime state. A scheduler-context
probe must reach the model and return the exact constrained JSON object before readiness is
claimed.

Allowed differences are limited to immutable packet identity, claim namespace, artifact output
directory, and delivery destination. Test-sink routing is loaded from the canonical secret path,
must differ from the production recipient, and may not create a production delivery intent.

An in-process unit test proves the contract but is not natural-live proof. A host probe proves
local state and app-server initialization; a frozen packet replay proves generation and accepted
decision validation. The next ordinary scheduled run remains the only natural-live confirmation.
