# Canonical Acceptance Persistence V2

## Status

M12BM closes the contract-design gap identified by M12BL. It is an offline,
local-only design. It does not change a database model, run a migration, alter
runtime persistence, enqueue or send a notification, call a model/provider, or
resume monitoring.

The design result is:

```text
PERSISTENCE_V2_CONTRACT_DESIGN_COMPLETE
```

The selected architecture is Option C: a new immutable
`AcceptedAssessmentV2` history, a separate derived current-state row, and
explicit warning transition and transactional outbox tables. Existing
`ThesisAssessment` records remain the legacy/manual store and are never
retroactively declared canonically accepted.

## One-Way Trust Boundary

The only canonical automated path is:

```text
frozen source evidence
  -> canonical semantic audit PASS
  -> final composition PASS
  -> core immutability PASS
  -> trusted internal receipt issuer
  -> CanonicalAcceptanceReceiptV1
  -> deterministic eligibility verifier
  -> one atomic assessment application transaction
       - immutable accepted history
       - stale-safe current state
       - warning transition events
       - notification outbox rows
  -> commit
  -> external delivery worker
```

Persistence never classifies prose, repairs candidates, infers a stance,
recomputes Business Delta, or converts a configured signal into fulfillment.
The verifier checks the frozen proof envelope; it does not rerun semantic
validation.

There is initially one trusted issuer:

```text
canonical_two_stage_finalizer_v1
```

It accepts only an internal frozen finalization result. No public request model
contains a receipt field, and no external route can invoke receipt issuance or
canonical application. The content hashes are tamper-evidence, not a substitute
for this interface boundary or a host-security signature.

## Source Domains

Exactly three persistence source domains are defined:

| Source domain | Storage | Canonical automation eligible |
| --- | --- | --- |
| `CANONICAL_MODEL_ACCEPTED` | `accepted_assessment_v2` | Yes, with a verified `ACCEPTED` receipt |
| `MANUAL_USER_AUTHORED` | legacy `thesisassessment` plus source registry | No |
| `LEGACY_UNVERIFIED` | legacy `thesisassessment` plus source registry | No |

The existing `recordThesisAssessment` action remains available for manual
history. Its ordinary request/response contract remains compatible, but it can
never mint or submit canonical acceptance. Reserved receipt, issuer,
acceptance, generation, and canonical-provenance fields are rejected at the
boundary instead of silently trusted. Manual writes may continue the legacy
compatibility metadata behavior until a separately approved cutover, but they
never advance V2 current state, V2 warnings, or V2 outbox rows.

All pre-V2 rows are backfilled only with `LEGACY_UNVERIFIED`. No packet hash,
semantic PASS, receipt, or provenance is fabricated.

## CanonicalAcceptanceReceiptV1

The receipt has exactly 25 fields:

1. `receipt_contract_version`
2. `acceptance_id`
3. `receipt_hash`
4. `receipt_status`
5. `trusted_issuer_id`
6. `generation_id`
7. `generation_generated_at`
8. `ticker`
9. `thesis_version`
10. `assessment_date`
11. `effective_at`
12. `accepted_at`
13. `source_packet_id`
14. `packet_hash`
15. `source_evidence_snapshot_identity`
16. `accepted_payload_contract_version`
17. `canonical_serialization_contract`
18. `final_composed_candidate_hash`
19. `canonical_semantic_audit_contract`
20. `canonical_semantic_audit_status`
21. `finalization_status`
22. `core_immutability_status`
23. `core_hash`
24. `stance_hash`
25. `quarantine_reason_codes`

`receipt_status` is `ACCEPTED`, `REJECTED`, or `QUARANTINED`.
`LEGACY_UNVERIFIED` is deliberately not a receipt status because no receipt
exists for those rows. Only `ACCEPTED` may be inserted into the canonical
tables.

The serialization contract is the proof pipeline's existing canonical JSON:
UTF-8, sorted keys, compact separators, and explicit JSON values. Existing
`core_hash` and `stance_hash` values are referenced unchanged.

### Acceptance identity

```text
acceptance_id =
  "ca1_" + sha256(
    canonical_json({
      "domain": "canonical-acceptance-id-v1",
      "receipt_material": all 25 receipt fields except
                          acceptance_id, receipt_hash, accepted_at
    })
  )
```

`accepted_at` is excluded because wall-clock issuance time cannot change the
identity of an otherwise identical accepted result. It remains in the immutable
receipt and is covered by `receipt_hash`.

```text
receipt_hash = sha256(
  canonical_json({
    "domain": "canonical-acceptance-receipt-hash-v1",
    "receipt": all receipt fields except receipt_hash
  })
)
```

This gives the same result the same acceptance identity, distinguishes ticker,
generation, thesis version, source snapshot, and final candidate changes, and
detects envelope tampering. Receipt issuance for one generation/ticker is
single-valued: a second different candidate for the same slot is a conflict,
not a replacement.

`source_evidence_snapshot_identity` is a versioned object whose digest is bound
to the frozen packet bytes. It records the packet contract, SHA-256 algorithm,
packet digest, subject ticker, and optional independently available component
hashes. Missing optional component hashes remain null; they are not inferred.

## Eligibility

The deterministic eligibility result vocabulary is:

```text
ELIGIBLE_CANONICAL
INELIGIBLE_MANUAL_ONLY
INELIGIBLE_LEGACY_UNVERIFIED
REJECTED_INVALID_RECEIPT
REJECTED_STALE
REJECTED_QUARANTINED
IDEMPOTENT_ALREADY_APPLIED
```

Canonical eligibility requires a supported receipt contract, a trusted issuer,
valid content hashes, exact ticker/date/thesis/payload identity, present source
snapshot identity, `ACCEPTED`, semantic/finalization/core-immutability PASS, and
no quarantine reason. Staleness does not delete a valid immutable history row;
it blocks current-state, warning, and outbox advancement and returns
`REJECTED_STALE` for those derived effects.

## AcceptedAssessmentV2

`accepted_assessment_v2` is append-only and keyed by `acceptance_id`. It stores:

- Exact subject, thesis version, business date, effective timestamp, generation
  timestamp, and total ordering key.
- Exact typed `overall_direction`, directional balance, hold lean,
  `directional_confidence`, and canonical Business Delta.
- The complete versioned final accepted candidate JSON and its SHA-256 as the
  lossless authority.
- Exact versioned extracts for business, earnings, valuation, market
  expectation, risk, sector, driver, dominant-evidence, uncertainty,
  core-judgment, unknown, new-buyer, holder, and reevaluation structures.
- Exact evidence references and the versioned security/ADR/currency provenance
  projection from the receipt-bound packet.

The extracted columns are query aids, not competing truth. On insert, a pure
schema validator proves that every extract equals the corresponding field in
the hash-bound canonical payload. A mismatch rejects the entire transaction.

The V2 store does not invent legacy `confirmed_facts`,
`inferred_implications`, or generic `summary`. It retains the accepted typed
claims, including exact `core_investment_judgment`. Legacy/manual paths retain
their historical presentation fields.

### Typed field policy

| Concept | Canonical V2 policy |
| --- | --- |
| Overall direction | Exact `BUY/HOLD/SELL` |
| Directional balance | Exact `{buy, sell}` half-step pair |
| Hold lean | Exact enum |
| Confidence | Exact `LOW/MEDIUM/HIGH`; no float synthesis |
| Business Delta | Exact `STRENGTHENED/UNCHANGED/WEAKENED/UNRESOLVED` |
| New buyer | Exact structured stance, summary, condition, and refs |
| Holder | Exact structured stance, summary, invalidation condition, and refs |
| Market expectation | Exact accepted `DirectionalClaim`; no invented expectation level |
| Valuation | Exact accepted `DirectionalClaim`; no legacy impact inference |
| Earnings impact | Exact accepted `DirectionalClaim`; no legacy enum inference |
| Risk | Exact accepted `risk_context` claim; no scalar risk synthesis |
| Unknowns | Versioned structured objects with refs, treatment, and negative basis |
| Security basis | Versioned packet projection with null for absent fields |

The versioned legacy Business Delta projection is:

```text
STRENGTHENED -> strengthened
UNCHANGED    -> no_material_change
WEAKENED     -> weakened
UNRESOLVED   -> null / unsupported
```

No legacy projection is allowed for canonical confidence, risk, valuation
impact, or earnings impact. A read requiring a missing legacy value must return
an explicit unsupported marker through an internal compatibility envelope; it
must not coerce a value.

## History And Current State

Immutable history and current state are separate.

`monitoring_current_state_v2` has one row per ticker and stores the latest
acceptance pointer, the four ordering components, row version, latest business
date, thesis version, and allowed current-state metadata. The total order is:

```text
(
  effective_at_utc,
  generation_generated_at_utc,
  generation_id,
  acceptance_id
)
```

All timestamps are offset-aware and normalized to UTC before comparison.
`assessment_date` remains a business date and never serves as a concurrency
version. `accepted_at` and database insertion order are audit information, not
ordering inputs.

Current-state advancement uses a database-level compare-and-swap. A transaction
inserts immutable history and advances current state only when the incoming
tuple is strictly greater. Equal acceptance is an idempotent no-op. A lower
tuple may be retained as valid history but cannot alter current state, warning
state, or outbox. SQLite uses `BEGIN IMMEDIATE` plus a conditional update/insert;
other databases use an equivalent conditional update or row lock. Python locks
are never the correctness mechanism.

## Warnings

V2 uses the repository's real business states:

```text
open
escalated
resolved
```

`invalid_provenance` is not a business lifecycle state in V2. Invalid evidence
is rejected or quarantined before warning application.

A warning identity is content-addressed over ticker, thesis version, warning
type, condition identity, and condition-contract version. Every observation and
transition references an accepted `acceptance_id`. No prose classifier runs in
persistence.

A transition requires an explicit trusted `CanonicalWarningObservationV1`
whose evidence references are a subset of the receipt-bound accepted/source
evidence. If no such observation is available, the accepted assessment can
persist but warning state does not change.

Observation values are `CONFIRMED`, `WORSENED`, `RECOVERED`, and `UNRESOLVED`.
The state machine is:

| Current | Observation | Next | Material transition |
| --- | --- | --- | --- |
| absent | `CONFIRMED` or `WORSENED` | `open` | Yes |
| absent | `RECOVERED` or `UNRESOLVED` | absent | No |
| `open` | `CONFIRMED` | `open` | No |
| `open` | `WORSENED` | `escalated` | Yes |
| `open` | `RECOVERED` | `resolved` | Yes |
| `open` | `UNRESOLVED` | `open` | No |
| `escalated` | `CONFIRMED` or `WORSENED` | `escalated` | No |
| `escalated` | `RECOVERED` | `resolved` | Yes |
| `escalated` | `UNRESOLVED` | `escalated` | No |
| `resolved` | `CONFIRMED` or `WORSENED` | `open` | Yes, new episode |
| `resolved` | `RECOVERED` or `UNRESOLVED` | `resolved` | No |

The same acceptance replay is rejected before this table. A genuinely newer,
different same-date acceptance may escalate only when it carries a validated
`WORSENED` observation. Call count and date equality never escalate.

```text
warning_transition_id = sha256(canonical_json({
  "domain": "warning-transition-v2",
  "warning_identity": ...,
  "episode": ...,
  "from_state": ...,
  "to_state": ...,
  "triggering_acceptance_id": ...,
  "transition_reason_version": ...
}))
```

The transition table has a unique transition ID, so replay produces no second
event. The mutable warning-state row uses the same stale-safe ordering and row
version as current state.

## Transactional Outbox

Two notification event kinds are intentionally distinct:

```text
DAILY_SUMMARY_NOTIFICATION
MATERIAL_STATE_TRANSITION_NOTIFICATION
```

A daily event is authorized by a schedule/run slot and an accepted current
assessment. Its source event identity is content-addressed over schedule-run ID,
ticker, acceptance ID, channel, and payload version. A material event is keyed
by `warning_transition_id`, channel, and payload version. Manual, legacy,
invalid, quarantined, duplicate, and stale inputs produce no V2 outbox row.

The unique key is `(source_event_id, channel, payload_version)`. The assessment
application transaction verifies the receipt, inserts history, conditionally
advances current state, applies eligible warning transitions, and inserts
outbox rows before one commit. Any pre-commit failure rolls back the entire
unit. External delivery occurs only after commit.

Post-commit delivery failure leaves a stable pending outbox row. Retries reuse
the same acceptance, transition, and outbox identities. Attempt metadata may
change; semantic payload and source identity may not. Exhausted bounded retries
move the row to `dead_letter` for explicit review.

## Failure Semantics

| Failure point | Required result |
| --- | --- |
| Receipt or payload verification | Reject before transaction; no writes |
| Immutable insert conflict, same bytes | `IDEMPOTENT_ALREADY_APPLIED` |
| Immutable insert conflict, different bytes | Rollback and integrity error |
| Current-state incoming order lower | Keep valid history; `NO_OP_STALE` for derived state |
| CAS loses to a higher concurrent order | Reread; stale no-op or bounded retry |
| Warning validation/transition insert | Rollback assessment application transaction |
| Outbox insert | Rollback assessment application transaction |
| Crash after commit before send | Pending outbox survives; retry-safe |
| Send failure | Pending/retry or dead-letter; no assessment rollback |

## Schema Plan

The bounded implementation adds seven tables without altering or deleting
legacy rows:

```text
canonical_acceptance_receipt_v1
accepted_assessment_v2
monitoring_current_state_v2
assessment_source_registry_v2
warning_state_v2
warning_transition_v2
notification_outbox_v2
```

Foreign keys connect accepted assessment to receipt, current state to accepted
history, warning transitions to accepted history and warning state, and outbox
rows to their source event. Unique constraints enforce generation/ticker
single-valued issuance, acceptance idempotency, transition idempotency, and
outbox dedupe. Indexes cover ticker plus ordering columns, assessment date,
warning state, and pending outbox scheduling.

The migration is forward-only because canonical accepted history and event
identities must never be silently downgraded into mutable legacy rows. Rollback
means disabling the V2 writer/read preference while preserving the new tables;
destructive down-migration is prohibited. The old code remains able to ignore
new tables.

Upgrade order:

1. Create and verify V2 tables, constraints, and indexes in an ephemeral DB.
2. Backfill every existing `ThesisAssessment.id` into the source registry as
   `LEGACY_UNVERIFIED` without modifying the row.
3. Deploy V2 receipt verification and persistence services disabled by default.
4. Run frozen positive/negative and race/failure fixtures locally.
5. Enable dual-read observation, still without external side effects.
6. Separately authorize writer cutover and later notification delivery.

## Read Compatibility

The existing public `recordThesisAssessment` and legacy history response remain
legacy/manual contracts. They do not accept or expose canonical receipt fields
in M12BN.

Internal V2 reads return a discriminated envelope with `source_domain`,
`automation_eligible`, receipt identity, and the typed canonical payload. A
current review prefers `monitoring_current_state_v2` only when its acceptance
and payload reverify; otherwise it fails closed to an explicit unavailable
state rather than silently substituting a manual/legacy row. A separate history
reader can union canonical and legacy/manual records while preserving source
domain and ordering. Same-date canonical generations remain distinct.

No accepted assessment creates a new thesis version. Thesis registration and
versioning, accepted history, current state, warnings, and notification delivery
remain separate lifecycle concepts.

## Next Proof

M12BN is bounded to implementation and local replay. It must prove, without
production effects:

- 22/22 frozen M12BJ positives issue and verify receipts, persist losslessly,
  and replay with zero duplicates.
- The 16 historical canonical failures, missing/tampered/quarantined receipts,
  and invalid source domains produce zero canonical/warning/outbox writes.
- Same-date distinct generations remain immutable and deterministically ordered.
- Stale and concurrent races end with the greatest ordering key.
- Warning replay, escalation, recovery, and recurrence are acceptance-driven.
- Transaction failure injection leaves either the complete pre-commit state or
  the complete committed state.
- Existing manual/legacy reads remain compatible and externally supplied
  receipt fields cannot cross the trust boundary.

Fresh real proof, main merge, deployment, production persistence, notification
delivery, and schedule resume remain `NOT_READY` until that local proof passes.

## M12BN Local Implementation Status

M12BN implements the frozen contract on local/ephemeral SQLite only. The
implementation is fixed at `2cd59975650a05021e4bbd6376b4db30aa02efe6` on
`codex/20260914-persistence-v2-local-proof-m12bn` and remains disabled by
default in production settings.

The executable proof covers all seven V2 tables, deterministic 25-field
receipt issuance and verification, immutable accepted history, four-component
total ordering with bounded current-state CAS retry, acceptance-driven warning
transitions, transactional outbox creation, fake-only post-commit dispatch,
manual/legacy source classification, and receipt-verified dual reads. V2 uses
independent SQLAlchemy metadata, so importing the implementation cannot cause
the legacy production `SQLModel.metadata.create_all()` path to create V2
tables.

The frozen M12BJ cohort persists and reads back `22/22` without payload or
provenance loss. The historical fresh canonical failures remain rejected
`16/16`; they are not reclassified. Duplicate, stale, race, tamper, failure,
timezone, ticker, warning, outbox, and migration fixtures pass. Focused tests
are `33/33`, the existing persistence regression set is `80/80`, and the full
local suite is `3988/3988` with one dependency warning. Ruff and diff checks
pass, and model/semantic/policy hashes remain unchanged.

The result is `PERSISTENCE_V2_LOCAL_IMPLEMENTATION_PROOF_PASS`. This authorizes
only a separately instructed `NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE`.
It does not authorize production migration, writer/read cutover, warning or
outbox delivery enablement, schedule resume, main merge, deployment, or remote
push.
