# XKRX Role-target Idempotency

Night telemetry loads attempts by expected NIGHT target across up to 14 later
wall-clock dates. The same role/target is a no-op even when restart seconds
differ. Terminal readiness or the 09:15 horizon is target-terminal. A distinct
later role remains allowed after a nonterminal earlier attempt.

KRX publication telemetry uses target-date archives. The same scheduled slot is
`target_already_observed`; any `PROVIDER_COMPLETE` record makes the target
`target_already_terminal`. Pending records remain retryable at a later natural
slot.

Tests prove repeated invocation, process-restart timing, terminal suppression,
pending retry, and Saturday-to-Sunday deduplication. Duplicate logical provider
observations: 0 in covered cases.

