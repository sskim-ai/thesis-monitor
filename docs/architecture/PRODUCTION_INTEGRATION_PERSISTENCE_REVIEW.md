# Production Integration / Persistence Review

## Status

M12BL audits the integrated-main persistence boundary downstream of the frozen
`directional-core-semantic-audit-v1` contract. It is an offline, local-only
review. It does not add a production adapter, change a public schema, migrate a
database, enqueue a notification, send a message, resume a schedule, or call a
model/provider.

The authoritative decision is:

```text
BLOCKING_PRODUCTION_PERSISTENCE_CONTRACT_GAP
```

The canonical semantic layer and the M12BJ 22-name final compositions remain
valid frozen inputs. The blocker is downstream: the current persistence surface
cannot require or preserve their acceptance identity and typed semantics.

## Current Paths

Two paths write `ThesisAssessment`:

```text
recordThesisAssessment action
  -> monitoring_service.record_assessment
  -> ThesisAssessment + WatchlistItem
  -> commit

daily monitor
  -> direct ThesisAssessment create/update
  -> per-ticker commit
  -> monitoring-state persistence
  -> notification queue
  -> delivery
```

The action schema accepts the existing user-facing assessment fields. It has no
enforceable fields for generation identity, packet/final/core/stance hashes,
canonical semantic receipt, final-composition status, core immutability, or
quarantine. Unknown receipt fields are discarded during validation. Therefore a
schema-valid payload with no canonical receipt, or even one carrying ignored
`FAIL`/quarantine extras, can reach `record_assessment`.

`accepted_decision_v2` state is a delivery-continuity file, not the assessment
repository. It is updated only after complete AI-assisted delivery and carries
neither the M12BI receipt nor a generation-order stale guard. The two-stage
directional candidates currently have no production persistence adapter.

## Fidelity Gaps

The target schema separately exposes new-buyer and holder text, but it cannot
losslessly preserve their structured stance evidence. The canonical business
delta vocabulary also differs from the persisted assessment vocabulary without
a versioned mapping table. Market expectation, confidence, risk, unknown
treatment, evidence references, and security/share-basis provenance are lossy or
unmapped.

These are proof-critical missing persistence identities:

```text
generation id
packet hash
final composed candidate hash
canonical semantic audit contract/status
source evidence snapshot identity
finalization status
core hash
stance hash
quarantine marker
```

Model identity and effort are useful but noncritical to this gate. Ticker and
assessment date already persist, although the action-supplied date does not
prove generation identity.

## Lifecycle Findings

The ephemeral SQLite harness uses the real schema and services while keeping all
production effects at zero. It proves:

- Same ticker/date upserts to one mutable assessment row.
- A stale assessment can overwrite `WatchlistItem.latest_*` metadata.
- Accepted V2 state can be replaced by an older assessment date.
- Same-date warning replay keeps the warning ID but changes `open` to
  `escalated`, so semantic replay is not idempotent.
- Notification uniqueness suppresses an exact same-date duplicate, but there is
  no canonical-acceptance or stale-generation gate.
- Caller rollback protects the individual action transaction after injected
  failure; the full daily assessment/state/queue lifecycle is not one explicit
  atomic or recoverable unit.
- Korean six-digit strings retain zeros, while short numeric strings are not
  normalized to the canonical six-digit identity and integer input is rejected.

## Required Next Contract

No broad repair is made in M12BL. Before a fresh proof or production integration,
define and approve a canonical acceptance persistence contract with:

1. An immutable accepted-output identity and canonical receipt.
2. Lossless, versioned mappings for business delta, market expectation,
   new-buyer, holder, confidence, risk, and evidence provenance.
3. A monotonic stale-generation guard for current-state projections.
4. Explicit assessment, warning, queue, and retry transaction semantics.
5. Idempotency keys that distinguish history from replay.
6. A migration and backward-compatible read strategy, followed by local
   upgrade/rollback proof.

Until that contract exists, all 22 frozen M12BJ outputs remain ineligible for
production persistence despite passing canonical semantic and final-composition
checks. Fresh real proof, main merge, deployment, and production readiness are
`NOT_READY`.
