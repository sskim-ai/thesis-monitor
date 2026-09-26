# Unified Snapshot Pipeline

## Work Instruction Freeze

Task: M12DS-R6-R5F-R1. Base: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.
The attached work instruction is preserved under `docs/work-instructions`.
This worktree is local only. No scheduler activation, provider/model calls,
production delivery, database mutation, main merge, or deployment is part of
offline validation. Existing investment policy and sealed evidence are unchanged.

## Implementation Plan

1. Inventory app automations and launchd paths, including fallback and delivery
   retry paths. Preserve the actual before state and prepare a migration plan.
2. Implement a single-cycle, process-locked, durable snapshot state machine.
   Collection retries use original wall-clock slots and fresh whole attempts.
3. Bind collection receipts, all downstream stages, and delivery to immutable
   run/snapshot identities. Reject stale, future, incomplete, or mixed inputs.
4. Implement bounded terminal failure finalization, operational notification,
   sanitized immutable debug ZIP, and atomic local iCloud copy verification.
5. Exercise both exchanges, all collection retry slots, downstream failures,
   concurrency/crash safety, and output integrity offline.
6. Evaluate concrete production adapter parity separately from orchestration
   fixtures. Do not label fixture success as production integration proof.
7. Run full validation, publish local report ZIP/SHA to the established iCloud
   destinations, and report any unresolved promotion blocker explicitly.

## Source Contract

Accepted data is `QUERY_TIME_SNAPSHOT`; `finality_claim=NOT_CLAIMED`.
The timestamp is a collection timestamp, not certified immutable close evidence.
Source session, identity, basis, schema, hashes, and complete production role
coverage remain mandatory. Alpha Vantage and Massive are not called.

## Destination

Existing local reports use the iCloud Drive `Thesis Monitor` directory. Runtime
configuration must explicitly supply that destination; application code must
not embed a developer home path. A local hash-verified copy is not evidence of
Apple server or remote-device synchronization.
