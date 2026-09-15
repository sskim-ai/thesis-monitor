# Thesis Monitor — Canonical Acceptance Persistence Contract / Schema / Lifecycle Design

## 0. Task identity

Suggested work-instruction filename:

```text
20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design.md
```

Suggested result bundle:

```text
thesis-monitor-20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design-report.zip
```

Master-workflow phase:

```text
M12BM — Canonical Acceptance Persistence Contract Design
         A. Freeze semantic single-source convergence
         B. Freeze complete monitored compatibility proof
         C. Freeze real-cohort policy validation
         D. Freeze M12BL persistence-gap evidence
         E. Define one canonical acceptance receipt
         F. Define lossless typed persisted assessment V2 contract
         G. Define immutable history + stale-safe current-state lifecycle
         H. Define warning idempotency and lifecycle semantics
         I. Define transactional notification outbox contract
         J. Define concurrency / retry / duplicate semantics
         K. Define schema migration and legacy-data compatibility
         L. Define manual vs canonical-model persistence trust domains
         M. Produce an implementation-ready bounded repair specification
         N. Do NOT implement or run fresh proof in this task
```

M12BM is a DESIGN task.

It is NOT another semantic or policy review.

Do NOT reopen:

```text
financial semantics
FCF semantics
net-debt semantics
working-capital semantics
financial-sector semantics
ConfiguredSignalEvidenceView
BusinessDeltaEvidenceView
MarketExpectationEvidenceView
decision boundary policy
holder policy
new-buyer policy
same-direction calibration policy.
```

Those are frozen.

The new problem is downstream:

```text
the current production persistence layer cannot prove
that a stored assessment was canonically accepted,
cannot represent the complete accepted two-stage semantics losslessly,
and is not stale-safe / warning-idempotent.
```

M12BM must design the contract that fixes this.

No model calls.

No provider calls.

No production writes.

No scheduler changes.

No schema migration applied to production.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260914-production-integration-persistence-review-on-integrated-main-report.zip
```

Verified SHA-256:

```text
73c038cb4640d16f596032d88863901bb0d496acf8fe182abeed7eb48395f174
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
artifact_count = 83

ZIP entries =
83 indexed payloads
+ artifact-index.json
= 84

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0.
```

Recompute independently.

---

# 2. M12BL authoritative result

M12BL:

```text
status = COMPLETE_BLOCKED

top_level_integration_result =
BLOCKING_PRODUCTION_PERSISTENCE_CONTRACT_GAP

fresh_real_proof_readiness =
NOT_READY

final_main_merge_readiness =
NOT_READY

production_readiness =
NOT_READY

next_scope =
CANONICAL_ACCEPTANCE_PERSISTENCE_CONTRACT_SCHEMA_AND_LIFECYCLE_DESIGN.
```

M12BM is exactly that scope.

---

# 3. M12BL blocker summary — freeze

The production persistence gap is not speculative.

M12BL proved:

```text
persistence_eligibility_gate_status = ABSENT

canonical_acceptance_required = false

raw_model_persistence_bypass_count = 2

proof_critical_missing_provenance_count = 10

assessment_field_mapping_lossy_count = 12

assessment_invalid_enum_mapping_count = 1

schema_compatibility_status =
BLOCKING_SCHEMA_MISMATCH

schema_migration_required = true

stale_generation_guard_status =
FAIL_ABSENT

stale replay =
FAIL_STALE_OVERWRITE

warning idempotency =
FAIL_SAME_DATE_REPEAT_ESCALATES

transaction boundary =
FAIL_CROSS_STAGE_NONATOMIC

partial-failure behavior =
GAP

concurrency safety =
PARTIAL_FILE_STATE_UNLOCKED.
```

Do not weaken these findings.

---

# 4. Current production assessment entrypoints — freeze

M12BL mapped two assessment entrypoints.

## 4.1 Action/API entrypoint

```text
POST /monitoring-items/{ticker}/assessments

operation_id =
recordThesisAssessment

service =
app/services/monitoring_service.py

repository =
ThesisAssessment + WatchlistItem

idempotency =
UNIQUE(ticker, assessment_date)
with mutable upsert

canonical acceptance gate =
false.
```

## 4.2 Daily monitoring entrypoint

```text
run_daily_monitor

service =
app/services/daily_monitor_service.py

repository =
ThesisAssessment + WatchlistItem

same ticker/date =
row update

canonical acceptance gate =
false.
```

These current contracts cannot be treated as canonical accepted-output persistence.

---

# 5. Raw/unvalidated persistence bypass — freeze

M12BL local fixtures proved:

```text
missing canonical semantic receipt
→ persisted

failed canonical semantic receipt
→ persisted

quarantine marker
→ ignored

final_composition_status
→ ignored

core_immutability_status
→ ignored.
```

Historical invalid fresh candidate fixture:

```text
expected =
REJECTED_BEFORE_PERSISTENCE

actual =
payload persisted in ephemeral repository

status =
FAIL_BYPASS_CONFIRMED.
```

This must become impossible for canonical model-produced assessments.

---

# 6. Historical fresh proof remains quarantined

Historical generation:

```text
20260907-new-issuer-proof-20260907T055608Z-0446826566f6
```

Canonical audit:

```text
16 candidates

16 canonical FAIL

BusinessDelta contract failures.
```

Required design outcome:

```text
historical fresh candidate
cannot receive a valid canonical acceptance receipt

cannot drive warning state

cannot drive current monitoring state

cannot enqueue automated notification.
```

Do not delete history.

Do not rewrite old artifacts.

---

# 7. Missing proof-critical provenance — freeze

M12BL found the current `ThesisAssessment`
cannot persist/verify these proof-critical identities:

```text
generation_id

packet_hash

final_composed_candidate_hash

canonical_semantic_audit_contract

canonical_semantic_audit_status

source_evidence_snapshot_identity

finalization_status

core_hash

stance_hash

quarantine_marker / acceptance eligibility identity.
```

Existing persisted identities include:

```text
ticker

assessment_date.
```

Model identity / effort were classified noncritical
for the acceptance receipt.

M12BM must decide the authoritative storage contract.

---

# 8. Lossy current field mapping — freeze

M12BL current mapping:

```text
business_thesis_change:
INVALID_ENUM_MAPPING
no versioned mapping

valuation_context:
LOSSY

earnings_estimate_impact:
LOSSY

market_expectation_assessment:
LOSSY

confirmed_facts:
MISSING

inferred_implications:
MISSING

unknowns:
LOSSY

summary:
MISSING

new_buyer_view:
LOSSY

holder_view:
LOSSY

risk_level:
LOSSY

confidence:
LOSSY.
```

Do not solve this by generating arbitrary free text.

Do not synthesize missing semantic fields at persistence time.

---

# 9. Current stale-overwrite failure — freeze

M12BL ephemeral replay proved:

```text
new accepted state written first

older accepted assessment replayed afterward

→ watchlist latest metadata overwritten by stale assessment

→ accepted-v2 test state overwritten by stale assessment

→ stale notification remained possible.
```

Current state ordering cannot rely only on:

```text
(ticker, assessment_date)
```

or mutable upsert.

M12BM must define a deterministic stale-safe ordering contract.

---

# 10. Current warning idempotency failure — freeze

Current warning identity is stable,
but repeated same-date confirmation changed:

```text
first =
open

same-date replay =
escalated.
```

Therefore:

```text
same acceptance replay
is not warning-idempotent.
```

M12BM must define warning transition identity
and replay semantics.

---

# 11. Current transaction gap — freeze

Current production flow has multiple boundaries.

M12BL found:

```text
record_assessment:
assessment/item/onboarding share one commit

daily_monitor:
per-ticker assessment commit
then monitoring-state / run / queue / send commits

whole effect atomic =
false

cross-stage recovery contract =
not explicit.
```

A caller-level rollback works for one action unit,
but not for the whole daily lifecycle.

M12BM must define the intended transaction/outbox model.

---

# 12. Current notification behavior — freeze

Current queue:

```text
same transition dedupe exists

but no canonical-acceptance gate

and no stale-generation gate.
```

M12BL:

```text
same_transition_queue_count = 1

queue_count_after_stale = 2

status =
PARTIAL_DEDUPE_WITHOUT_CANONICAL_OR_STALE_GATE.
```

M12BM must define queue eligibility from accepted state transitions.

---

# 13. Current concurrency gap — freeze

M12BL:

```text
accepted-state lock = false

read-modify-write lost update possible = true.
```

M12BM must define DB-level or repository-level concurrency safety.

Do not rely only on process-local locks.

---

# 14. Design principle: persistence is downstream of semantic acceptance

M12BM must establish this one-way boundary:

```text
model outputs
→ canonical semantic audit
→ final composition
→ core immutability check
→ canonical acceptance receipt
→ persistence eligibility
→ immutable accepted assessment
→ current state / warning transition / outbox.
```

Persistence must NOT:

```text
run semantic classification again

reinterpret raw candidate text

repair invalid model output

infer missing stance

infer Business Delta

convert configured signal into fulfillment.
```

No downstream semantic engine.

---

# 15. Canonical acceptance receipt — required design

Design one authoritative receipt contract,
suggested name:

```text
CanonicalAcceptanceReceiptV1
```

or repository-equivalent.

The receipt must be deterministic and immutable.

At minimum decide fields for:

```text
receipt_contract_version

acceptance_id

generation_id

ticker

assessment_date

accepted_at / ordering timestamp or equivalent

source_packet_id if available

packet_hash

source_evidence_snapshot_identity

final_composed_candidate_hash

canonical_semantic_audit_contract

canonical_semantic_audit_status

finalization_status

core_immutability_status

core_hash

stance_hash

quarantine / eligibility state

issuer / producer identity

receipt hash or content-address identity.
```

Do not automatically include model identity/effort
unless design evidence says they are needed for acceptance integrity.

---

# 16. Acceptance ID contract

Define one stable acceptance identity.

Candidate principle:

```text
acceptance_id =
deterministic content/address identity
over proof-critical receipt fields
```

or equivalent repository-appropriate UUID/content hash.

Requirements:

```text
same accepted result replay
→ same acceptance identity

different final candidate
→ different acceptance identity

different generation
→ distinguishable

different ticker
→ distinguishable

tampered receipt
→ detectable.
```

Do not use random UUID alone
if it prevents deterministic idempotency.

A random DB surrogate key may exist,
but it is not sufficient as the idempotency identity.

---

# 17. Receipt eligibility states

Do not use a loose boolean only.

Design explicit states such as:

```text
ACCEPTED

REJECTED

QUARANTINED

LEGACY_UNVERIFIED
```

or equivalent.

Only:

```text
ACCEPTED
```

may enter the canonical automated persistence lifecycle.

Historical rows without a receipt must NOT be retroactively marked accepted.

---

# 18. Receipt issuance boundary

Define the ONE code boundary authorized to issue
`CanonicalAcceptanceReceiptV1`.

Required preconditions:

```text
runtime/schema success

canonical semantic audit PASS

final composition PASS

core immutability PASS

required source/provenance identities present

not quarantined

valid ticker

valid assessment time/date.
```

Receipt issuance must fail closed.

No API caller may self-assert:

```text
canonical_semantic_status = PASS
```

and thereby become accepted.

---

# 19. Receipt trust model

Explicitly classify:

```text
trusted internal issuer

untrusted external request

manual user-authored assessment

legacy imported assessment.
```

The receipt must be issued by trusted internal code
from frozen/validated evidence,
not accepted from arbitrary request JSON.

Define verification rules.

---

# 20. Manual vs canonical-model trust domains

The existing:

```text
recordThesisAssessment
```

may serve a manual/tool-facing workflow.

M12BM must decide whether manual assessments remain supported.

If YES, define separate source domains:

```text
CANONICAL_MODEL_ACCEPTED

MANUAL_USER_AUTHORED

LEGACY_UNVERIFIED.
```

Required:

```text
manual record may be stored as manual history
if product requirements require it

but manual/unverified record must not impersonate
canonical model acceptance

and must not automatically drive
canonical warning / notification lifecycle
unless a separately explicit manual-authority contract exists.
```

Do not silently break the external action API.

Do not silently let it bypass canonical acceptance either.

---

# 21. Accepted assessment V2 — required design

Design a typed, lossless persistence contract.

Suggested conceptual entity:

```text
AcceptedAssessmentV2
```

This may be:

```text
a new table

an extension of ThesisAssessment

or ThesisAssessment + sidecar tables.
```

M12BM must compare options and choose one.

Do not force the name.

---

# 22. Accepted assessment V2 required properties

The chosen design must support:

```text
immutable accepted history

canonical acceptance receipt linkage

lossless typed decision fields

lossless stance fields

lossless provenance

safe same-date multi-generation history

stale-safe current-state derivation

backward-compatible read strategy.
```

Current `(ticker, assessment_date)` mutable upsert
cannot remain the only canonical identity.

---

# 23. Preserve canonical typed decision fields

At minimum decide explicit storage for:

```text
overall_direction

directional_balance if production needs it

directional_lean / hold-band state if production needs it

directional_confidence as enum

business_thesis_change canonical enum

new_buyer_stance canonical enum

holder_stance canonical enum.
```

Do not reduce all structured decisions to free text.

---

# 24. Business Delta storage contract

Prefer storing the canonical enum directly:

```text
STRENGTHENED

UNCHANGED

WEAKENED

UNRESOLVED
```

If existing production `AssessmentStatus`
must remain for backward compatibility:

Design:

```text
canonical_business_delta
+
explicit versioned legacy_projection
```

or equivalent.

Never silently map:

```text
UNRESOLVED → NO_MATERIAL_CHANGE.
```

If the legacy enum cannot represent a canonical value:

```text
projection must be nullable / explicit unsupported
or schema must be extended.
```

No guessing.

---

# 25. New-buyer structured persistence

Persist at least the canonical meaning of:

```text
new_buyer_stance

new_buyer_summary if accepted output owns one

confirmation condition

evidence refs / identity required for auditability.
```

Do not keep only one lossy free-text `new_buyer_view`
as the authoritative value.

A legacy presentation string may be derived downstream
from stored canonical fields.

---

# 26. Holder structured persistence

Persist at least:

```text
holder_stance

holder summary

business confirmation condition

business invalidation condition

bound evidence refs / audit identities.
```

Do not keep only lossy free text as authoritative state.

No downstream:

```text
SELL → REDUCE
```

or:

```text
UNCHANGED → HOLDABLE
```

mapping.

---

# 27. Market expectation structured persistence

Design lossless storage for applicable accepted fields:

```text
expectation level

assessment/context summary

evidence basis / refs

independence/material-anchor metadata if required for auditability.
```

Do not mix market expectation into Business Delta.

---

# 28. Unknowns structured persistence

Current `list[str]` is lossy.

Where the accepted output owns structured unknowns,
design storage for:

```text
text

evidence refs

treatment

negative basis / why unknown if applicable

semantic role if required.
```

If JSON is chosen:

```text
version the JSON contract.
```

Do not store unversioned arbitrary blobs.

---

# 29. Facts / implications / summary

M12BL found no authorized final projection for:

```text
confirmed_facts

inferred_implications

summary.
```

M12BM must decide one of:

```text
A. add an explicit accepted final projection upstream
   in a future model-facing task

B. omit these fields from canonical V2 persistence
   and preserve them only for legacy/manual paths

C. deterministically derive them from already-owned structured fields
   ONLY if derivation is semantic-free and lossless.
```

Do NOT invent these fields at persistence time.

If option A is required:

```text
mark it as a separate future model-facing scope
```

and do not smuggle it into M12BM.

---

# 30. Valuation / earnings impact fields

M12BL found current mappings are lossy.

M12BM must classify:

```text
valuation_context

earnings_estimate_impact
```

as one of:

```text
CANONICAL_TYPED_FIELD_REQUIRED

LEGACY_PRESENTATION_ONLY

NOT_OWNED_BY_CURRENT_ACCEPTED_OUTPUT.
```

Do not infer enums from free-text claims.

If canonical model output does not own the field,
do not make persistence invent it.

---

# 31. Confidence storage

Current target:

```text
float 0..1
```

but canonical output is:

```text
LOW / MEDIUM / HIGH.
```

Preferred design:

```text
store canonical enum losslessly.
```

If legacy float remains:

```text
define a versioned projection table
and clearly mark it as presentation/compatibility projection.
```

Do not make a hidden mapping.

---

# 32. Risk storage

Current risk target is unconstrained string.

M12BM must determine whether risk level is:

```text
an authoritative canonical enum

a structured risk-context claim

or legacy presentation only.
```

Do not synthesize a scalar risk level
if the accepted output does not own one.

---

# 33. Security / ADR / currency provenance

M12BL found security-basis provenance was lossy.

Design how proof-critical caveats remain auditable:

```text
security basis

ADR/ADS ratio basis if applicable

financial currency

price currency

per-share basis caveat

evidence refs.
```

Do not duplicate full semantic analysis if not needed.

The goal is preservation,
not a second valuation engine.

---

# 34. Immutable assessment history

Canonical accepted assessments should be append-only history.

Required design:

```text
one acceptance_id
→ one immutable accepted assessment record.
```

Replaying the same acceptance:

```text
no-op / existing row returned.
```

A different valid acceptance on the same date:

```text
must be representable as distinct history
```

if the workflow allows multiple generations.

Do not overwrite history by date.

---

# 35. Current monitoring state

Separate:

```text
immutable assessment history
```

from:

```text
current derived monitoring state.
```

Current state may contain:

```text
ticker

latest_acceptance_id

latest_ordering_key

latest assessment date

current warning pointer/state

current thesis monitoring metadata as allowed.
```

It must not be the historical record itself.

---

# 36. Stale-safe ordering key

M12BM must define one total ordering for accepted assessments.

Do NOT use only:

```text
assessment_date.
```

Candidate components may include:

```text
effective assessment timestamp

generation timestamp

accepted_at

run sequence

generation id timestamp

acceptance_id as deterministic tie-breaker.
```

Select one explicit contract.

Requirements:

```text
newer acceptance cannot be overwritten by older replay

same acceptance replay is idempotent

same date distinct generations are ordered deterministically

ordering is timezone-safe

ordering does not depend on DB insertion order.
```

---

# 37. Assessment date vs ordering timestamp

Keep separate concepts:

```text
assessment_date
```

for user/business date,

and:

```text
ordering/effective timestamp
```

for stale protection.

Do not overload assessment date as a concurrency version.

Korean date semantics may remain Asia/Seoul where applicable.

---

# 38. Optimistic concurrency / compare-and-swap

Current state update must be concurrency-safe.

Design one of:

```text
database row version

compare-and-swap on latest ordering key

conditional UPDATE WHERE current_version = expected_version

transactional SELECT FOR UPDATE where supported.
```

Do not rely only on Python/process locks.

SQLite/local test design must have a deterministic approximation.

---

# 39. Warning lifecycle contract

Warnings are downstream derived state.

Design warning identity around:

```text
ticker

warning type / signal identity

fundamental condition identity

possibly thesis version if required.
```

Warning lifecycle events must reference:

```text
acceptance_id.
```

Repeated application of the SAME acceptance:

```text
no state escalation

no duplicate event

no duplicate notification.
```

This fixes M12BL same-date replay escalation.

---

# 40. Warning transition identity

Design a deterministic event identity such as:

```text
warning_transition_id =
hash(
  warning_identity,
  from_state,
  to_state,
  triggering_acceptance_id,
  transition_reason_version
)
```

or equivalent.

Required:

```text
same transition replay
→ same event identity

different acceptance / valid new transition
→ distinguishable.
```

Do not let call count itself cause escalation.

---

# 41. Warning state machine

Document exact allowed transitions.

Use actual repository states.

Do not invent state names
without inspecting current warning implementation.

For each transition define:

```text
precondition

accepted evidence source

triggering acceptance

idempotency behavior

notification eligibility

stale behavior.
```

---

# 42. Same-date warning behavior

Explicitly resolve M12BL failure:

```text
same accepted assessment replay on same date
must NOT escalate warning state.
```

If a genuinely different accepted assessment
on the same date confirms persistence/severity:

the contract may allow escalation,
but it must require:

```text
different acceptance_id

newer ordering key

valid transition evidence.
```

Not merely another function call.

---

# 43. Notification outbox contract

Prefer transactional outbox semantics.

Design an outbox row generated inside
the same DB transaction as accepted-state / warning transition changes.

Outbox identity should include:

```text
event_id / transition_id

channel

payload version.
```

Unique constraint:

```text
(event_id, channel)
```

or equivalent.

Repeated transaction replay:

```text
does not duplicate outbox rows.
```

---

# 44. External send boundary

Actual external send occurs:

```text
after transaction commit

from outbox/delivery worker

with its own idempotency identity.
```

M12BM design must preserve:

```text
no external send inside the DB transaction

no send from an unaccepted raw model output

no send from stale replay.
```

Schedules remain paused.

---

# 45. Assessment-only events vs material transition notifications

Current daily notification may be transition-independent.

M12BM must explicitly separate:

```text
DAILY_SUMMARY_NOTIFICATION

MATERIAL_STATE_TRANSITION_NOTIFICATION
```

if both product behaviors are intended.

Each needs its own idempotency contract.

Do not accidentally make every accepted assessment
a material alert.

Do not accidentally remove intended daily summaries.

---

# 46. Transaction boundary design

Define the atomic unit for one accepted assessment application.

Preferred conceptual transaction:

```text
verify receipt

insert immutable accepted assessment if absent

conditionally advance current state if newer

apply warning transition if eligible

insert notification outbox event(s)

commit.
```

External send occurs later.

If current repository architecture cannot support
one transaction for all local DB state:

define an explicit saga/recovery contract.

Unspecified partial commits are not acceptable.

---

# 47. Failure semantics

For each failure point define outcome:

```text
accepted assessment insert fails

current state compare-and-swap fails

warning transition fails

outbox insert fails

post-commit send fails.
```

Classify:

```text
ROLLBACK

NO-OP_STALE

IDEMPOTENT_ALREADY_APPLIED

RETRY_SAFE

DEAD_LETTER / MANUAL_REVIEW
```

according to actual architecture.

No vague "retry later."

---

# 48. Retry safety

Retries must reuse:

```text
acceptance_id

warning_transition_id

outbox event_id.
```

Retries must not generate fresh identities.

Bound retries.

Semantic content must not mutate during retry.

---

# 49. Legacy rows

Existing `ThesisAssessment` rows without canonical receipts
must be classified explicitly.

Suggested:

```text
LEGACY_UNVERIFIED.
```

Required:

```text
remain readable

not retroactively treated as canonical accepted

cannot drive new automated warning transitions
without a new valid canonical acceptance

do not delete history.
```

Design backward-compatible read behavior.

---

# 50. Existing external/manual action compatibility

`recordThesisAssessment` is an existing action/API.

M12BM must decide:

```text
retain unchanged for manual history only

version it

add a new canonical persistence endpoint

or route canonical internal persistence through a non-public service.
```

The canonical receipt must NOT be user-forgeable.

If the public/manual endpoint remains:

```text
its source type and automation eligibility must be explicit.
```

---

# 51. API trust boundary

Define which interfaces may:

```text
create a manual assessment

submit an accepted canonical assessment

apply a warning transition

queue a material notification.
```

Strong default:

```text
external action API cannot mint canonical acceptance.
```

Canonical acceptance should be internal.

---

# 52. Schema architecture options

M12BM must compare at least:

## Option A — Extend `ThesisAssessment`

Add canonical typed/provenance fields directly.

## Option B — `ThesisAssessment` + acceptance/provenance sidecar

Keep legacy row shape but attach canonical receipt and typed payload.

## Option C — New immutable `AcceptedAssessmentV2` + derived current state

Keep legacy table for manual/backward compatibility.

Compare:

```text
migration risk

backward compatibility

losslessness

idempotency

same-date multi-generation support

query/read-path complexity

warning/outbox linkage

rollback complexity

future fresh-proof integration.
```

Choose one.

Do not simply choose the smallest migration.

---

# 53. Recommended architectural bias

Unless repository evidence strongly contradicts it,
prefer a design that separates:

```text
immutable accepted V2 history

from

legacy/manual assessment records

from

derived current monitoring state.
```

Reason:

```text
current mutable UNIQUE(ticker, assessment_date) row
cannot safely represent canonical immutable acceptance history.
```

This is a design bias,
not a forced solution.

The code audit must decide.

---

# 54. Migration design

Produce an implementation-ready migration plan.

Do NOT apply production migration.

Define:

```text
new/altered tables

columns

types

enum strategy

JSON schema/versioning where used

foreign keys

unique constraints

indexes

current-state pointer/version fields

warning transition event storage

outbox storage.
```

Include downgrade/rollback strategy
or explicitly justify forward-only migration.

---

# 55. Existing data migration

Design how existing rows are migrated.

Required:

```text
no fabricated canonical receipt

no fabricated packet hash

no fabricated semantic PASS

legacy row retains original content

legacy status clearly distinguishable.
```

If backfill is impossible:

```text
store as LEGACY_UNVERIFIED.
```

---

# 56. Business Delta legacy projection

If legacy read API expects old `AssessmentStatus`,
design explicit versioned projection.

For every canonical enum specify:

```text
STRENGTHENED

UNCHANGED

WEAKENED

UNRESOLVED.
```

If no lossless legacy value exists:

```text
projection = null / unsupported
```

or extend the enum.

Do NOT coerce.

---

# 57. Read-path compatibility

Design reads for:

```text
Current Thesis Review

Daily Monitoring

Assessment History

existing external API clients.
```

Specify:

```text
which table is authoritative for canonical V2

how legacy rows are displayed

how manual rows are distinguished

how latest current state is selected

how same-date multiple canonical assessments are ordered.
```

---

# 58. Monitoring state / thesis version separation

Assessment persistence must NOT automatically create
a new monitored-thesis version.

Preserve:

```text
assessment history

thesis/version management

warning lifecycle

monitoring registration
```

as separate lifecycle concepts.

Define exact allowed transitions.

---

# 59. Source snapshot identity

M12BM must define:

```text
source_evidence_snapshot_identity
```

for canonical receipt.

It may be:

```text
packet hash

manifest hash

evidence-view bundle hash

or another frozen deterministic identity.
```

Do not duplicate unnecessary fields
if one cryptographic identity already covers them,
but preserve auditability.

---

# 60. Core / stance hash contract

Define exactly what:

```text
core_hash

stance_hash
```

cover.

Use the same canonical serialization
that the proof pipeline used.

No persistence-specific reserialization
that changes content hash semantics.

If existing hashes are already canonical:

```text
reference them unchanged.
```

---

# 61. Receipt verification

Design a verifier that checks:

```text
receipt contract version supported

receipt content hash valid

ticker/date identity matches payload

candidate hash matches accepted payload

semantic status = PASS

finalization status = PASS

core immutability = PASS

receipt not quarantined/rejected

source snapshot identity present

issuer trusted.
```

The verifier does NOT re-run semantic validation.

---

# 62. Persistence eligibility decision

Design one function/service such as:

```text
evaluate_persistence_eligibility(...)
```

or equivalent.

Output must be deterministic:

```text
ELIGIBLE_CANONICAL

INELIGIBLE_MANUAL_ONLY

INELIGIBLE_LEGACY_UNVERIFIED

REJECTED_INVALID_RECEIPT

REJECTED_STALE

REJECTED_QUARANTINED
```

or equivalent.

Do not overload HTTP status or DB exception as business policy.

---

# 63. Historical fresh negative fixture contract

The old 16 canonical-failed fresh candidates
must not be able to produce:

```text
CanonicalAcceptanceReceiptV1(ACCEPTED).
```

Design the exact negative path.

Expected future local implementation fixture:

```text
receipt issuance fails

persistence eligibility fails

warning transition = none

outbox event = none.
```

---

# 64. 22 M12BJ positive fixture contract

For the frozen 22 accepted monitored outputs,
design expected future implementation behavior:

```text
valid canonical receipt can be issued from frozen accepted artifacts

22 / 22 pass receipt verification

22 immutable accepted rows inserted locally

22 / 22 read back losslessly

duplicate replay creates 0 new accepted rows

stale replay does not advance current state

warning / outbox behavior follows exact transition fixtures.
```

Do NOT execute this full implementation replay in M12BM.

It becomes M12BN implementation acceptance.

---

# 65. Warning fixture design

Specify future deterministic fixtures:

```text
same acceptance replay

newer same-state acceptance

newer confirming acceptance

newer recovery acceptance

stale worsening acceptance

stale recovery acceptance

concurrent duplicate acceptance.
```

Expected warning state and event counts for each.

---

# 66. Notification fixture design

Specify:

```text
same warning transition replay

same daily summary replay

new material transition

stale material transition

manual assessment

legacy unverified assessment

canonical invalid assessment.
```

For each define expected:

```text
outbox rows

send eligibility

dedupe identity.
```

---

# 67. Transaction fixture design

Specify failure injection points:

```text
after accepted-history insert

after current-state update

after warning transition

after outbox insert

after DB commit before send

during send.
```

For each define durable state after failure.

No ambiguity.

---

# 68. Concurrency fixture design

Future implementation must test:

```text
two concurrent identical acceptances

two concurrent different same-date acceptances

older and newer acceptance racing.
```

Define expected winners/history.

Current state must end at the highest ordering key.

Immutable history may contain both valid distinct acceptances.

---

# 69. Timezone contract

Keep:

```text
assessment_date
```

as business/user date.

Define:

```text
effective_at / accepted_at / generated_at
```

as offset-aware timestamp.

Use timezone-aware ordering.

Do not derive ordering solely from KST date.

Document scheduler KST behavior separately.

---

# 70. Ticker identity

Canonical accepted persistence identity must preserve:

```text
KR six-digit ticker strings

US uppercase ticker strings.
```

Do not silently zero-pad arbitrary numeric input.

Canonical pipeline should already own normalized ticker.

Receipt and payload tickers must match exactly.

---

# 71. No semantic changes

Expected:

```text
model prompt semantic change = 0

model schema semantic change = 0

canonical semantic service change = 0

decision-policy change = 0

final accepted model-output schema change = 0.
```

M12BM is persistence contract design only.

---

# 72. No production implementation in M12BM

Do not:

```text
change production DB models

create migration files intended for deployment

change runtime persistence behavior

change warning behavior

change notification behavior.
```

You MAY produce:

```text
schema diagrams

pseudo-DDL

migration specification

typed interface specification

state-machine specification

future fixture specification.
```

The next bounded task implements the chosen design locally.

---

# 73. No model/network calls

Required:

```text
model calls = 0

provider fetches = 0

external proof network calls = 0.
```

All evidence is local.

---

# 74. Required architecture artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bm-scope-freeze

04-m12bl-blocking-gap-freeze

05-current-production-persistence-schema-map

06-current-entrypoint-trust-boundary-map

07-canonical-acceptance-receipt-options

08-canonical-acceptance-receipt-decision

09-canonical-acceptance-receipt-v1-spec

10-receipt-issuance-boundary-contract

11-receipt-verification-contract

12-persistence-eligibility-contract-v2

13-manual-vs-canonical-vs-legacy-source-contract.
```

---

# 75. Required schema design artifacts

Produce:

```text
14-persistence-schema-options-comparison

15-persistence-schema-architecture-decision

16-accepted-assessment-v2-schema-spec

17-current-monitoring-state-v2-schema-spec

18-canonical-provenance-schema-spec

19-structured-stance-schema-spec

20-market-expectation-schema-spec

21-structured-unknown-schema-spec

22-security-basis-provenance-schema-spec

23-business-delta-canonical-storage-contract

24-legacy-assessment-projection-contract

25-confidence-risk-storage-contract.
```

---

# 76. Required lifecycle artifacts

Produce:

```text
26-immutable-history-contract

27-acceptance-id-idempotency-contract

28-stale-safe-ordering-contract

29-current-state-compare-and-swap-contract

30-warning-identity-contract

31-warning-state-machine-contract

32-warning-transition-idempotency-contract

33-notification-outbox-contract

34-daily-vs-material-notification-contract

35-transaction-boundary-v2-contract

36-partial-failure-recovery-contract

37-retry-safety-v2-contract

38-concurrency-contract.
```

---

# 77. Required migration/read compatibility artifacts

Produce:

```text
39-schema-migration-spec

40-existing-data-legacy-unverified-migration-spec

41-index-and-unique-constraint-spec

42-upgrade-order

43-rollback-or-forward-only-decision

44-read-path-v2-contract

45-current-review-read-compatibility

46-assessment-history-read-compatibility

47-external-action-api-compatibility-decision

48-manual-assessment-automation-eligibility-decision.
```

---

# 78. Required fixture specifications

Produce:

```text
49-m12bj-22-positive-receipt-fixture-spec

50-historical-fresh-negative-receipt-fixture-spec

51-missing-receipt-negative-fixture-spec

52-tampered-receipt-negative-fixture-spec

53-quarantined-receipt-negative-fixture-spec

54-duplicate-acceptance-fixture-spec

55-same-date-distinct-generation-fixture-spec

56-stale-replay-fixture-spec

57-warning-replay-fixture-spec

58-warning-new-confirmation-fixture-spec

59-warning-recovery-fixture-spec

60-notification-dedupe-fixture-spec

61-transaction-failure-injection-fixture-spec

62-concurrency-race-fixture-spec

63-timezone-boundary-fixture-spec

64-ticker-identity-fixture-spec.
```

---

# 79. Required implementation handoff artifacts

Produce:

```text
65-implementation-change-map

66-files-modules-expected-to-change

67-migration-implementation-plan

68-local-ephemeral-replay-plan

69-backward-compatibility-test-plan

70-production-firewall-test-plan

71-implementation-acceptance-criteria

72-next-bounded-scope-decision

73-master-workflow-update

74-program-completion.
```

---

# 80. Implementation change-map requirements

For every planned code change list:

```text
module/path

current responsibility

new responsibility

semantic behavior changed? yes/no

model-facing behavior changed? yes/no

database schema changed? yes/no

production side-effect path changed? yes/no

migration dependency

test coverage required.
```

Expected semantic/model-facing changes:

```text
NO.
```

---

# 81. Implementation acceptance criteria for next task

The next implementation task must not be authorized
unless M12BM design can specify how to prove all of:

```text
1. canonical receipt is unforgeable by external/manual request

2. missing/failed/quarantined receipt cannot enter canonical persistence

3. historical invalid fresh proof is rejected

4. 22 M12BJ accepted outputs can persist locally losslessly

5. accepted history is immutable

6. same acceptance replay is idempotent

7. same-date distinct accepted generations are representable

8. stale replay cannot move current state backward

9. concurrent races are deterministic

10. warning replay is idempotent

11. warning transition is acceptance-driven, not call-count-driven

12. outbox rows are transactionally deduped

13. external send is outside DB transaction

14. legacy/manual records remain distinguishable

15. existing reads remain backward compatible or migration is explicit

16. proof-critical provenance loss = 0.
```

---

# 82. Top-level design result

Choose exactly one:

```text
PERSISTENCE_V2_CONTRACT_DESIGN_COMPLETE
```

or:

```text
PERSISTENCE_CONTRACT_DESIGN_BLOCKED_BY_PRODUCT_DECISION.
```

Use the second only if a product behavior genuinely cannot be inferred,
for example:

```text
whether manual user-authored assessments are allowed
to trigger automated warnings/notifications.
```

Do not block on naming/style questions.

---

# 83. If product decision is required

Do not ask the user a broad technical question.

Produce a compact decision memo containing:

```text
decision required

Option A

Option B

risk of each

recommended default

which later implementation depends on it.
```

Stop before implementation.

---

# 84. Expected clean design outcome

Expected if repository contracts allow a deterministic design:

```text
top_level_design_result =
PERSISTENCE_V2_CONTRACT_DESIGN_COMPLETE

canonical_acceptance_receipt_contract =
DEFINED

persistence_eligibility_contract =
DEFINED

typed_lossless_v2_schema =
DEFINED

immutable_history_contract =
DEFINED

stale_safe_current_state_contract =
DEFINED

warning_idempotency_contract =
DEFINED

transactional_outbox_contract =
DEFINED

legacy_unverified_migration_contract =
DEFINED

model_facing_change_required =
false

semantic_service_change_required =
false

fresh_real_proof_readiness =
NOT_READY

final_main_merge_readiness =
NOT_READY

production_readiness =
NOT_READY

next_scope =
BOUNDED_PERSISTENCE_V2_IMPLEMENTATION_AND_LOCAL_REPLAY.
```

---

# 85. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch
final_local_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bl_top_level_result
m12bl_raw_model_persistence_bypass_count
m12bl_proof_critical_missing_provenance_count
m12bl_persistence_data_loss_count
m12bl_stale_guard_status
m12bl_warning_idempotency_status
m12bl_transaction_status

canonical_acceptance_receipt_contract_version
canonical_acceptance_receipt_field_count
canonical_acceptance_issuer_count
external_request_can_mint_receipt

persistence_source_domain_count
manual_assessment_supported
manual_assessment_automation_eligible
legacy_assessment_automation_eligible

selected_schema_architecture
accepted_assessment_v2_defined
current_state_v2_defined
canonical_provenance_storage_defined

canonical_business_delta_storage_status
new_buyer_structured_storage_status
holder_structured_storage_status
market_expectation_structured_storage_status
unknown_structured_storage_status
security_basis_provenance_storage_status
confidence_storage_status
risk_storage_status

acceptance_id_contract_defined
immutable_history_contract_defined
stale_safe_ordering_contract_defined
current_state_cas_contract_defined
warning_state_machine_contract_defined
warning_transition_idempotency_defined
notification_outbox_contract_defined
transaction_boundary_v2_defined
partial_failure_recovery_defined
retry_safety_defined
concurrency_contract_defined

legacy_unverified_migration_defined
schema_migration_required
schema_migration_spec_status
rollback_or_forward_only_decision

external_action_api_compatibility_status
read_path_compatibility_status

model_facing_change_required
semantic_service_change_required
decision_policy_change_required

model_calls
provider_source_fetches
external_proof_network_calls

production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

remote_push_count
raw_model_artifact_remote_push_count

main_branch_mutations
main_merges
deployments

scheduler_mutation_count
automatic_monitoring_resume

top_level_design_result

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Anything unresolved:

```text
NOT_DECIDED
```

with explicit reason.

---

# 86. Local-only / production firewall

M12BM is LOCAL-ONLY DESIGN.

Required:

```text
model calls = 0

provider source fetches = 0

external proof network calls = 0

production DB mutations = 0

monitoring registrations = 0

monitoring stops = 0

assessment persistence mutations = 0

warning mutations = 0

notification queue writes = 0

production sends = 0

remote pushes = 0

raw model artifact pushes = 0

main branch mutations = 0

main merges = 0

deployments = 0

scheduler mutations = 0

automatic monitoring resume = 0.
```

Schedules remain paused.

---

# 87. Artifact integrity

Freeze all local artifacts before final artifact index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Report final ZIP SHA-256.

---

# 88. Final task principle

The investment reasoning stack is already past:

```text
semantic convergence

full monitored proof

real-cohort policy validation.
```

M12BL proved the remaining blocker is production persistence architecture.

The current system:

```text
can store an assessment without canonical acceptance

cannot preserve the accepted two-stage output losslessly

can overwrite newer current state with stale replay

can escalate a warning by replaying the same assessment

and lacks one explicit atomic/recoverable lifecycle.
```

M12BM must solve this at the CONTRACT level.

The correct flow is:

```text
define a trusted canonical acceptance receipt

→ define a typed immutable AcceptedAssessment V2 representation

→ separate immutable history from current derived state

→ define a stale-safe total ordering and concurrency contract

→ define warning transition identity and idempotency

→ define a transactional notification outbox

→ define legacy/manual trust domains

→ define migration and backward-compatible reads

→ produce an implementation-ready bounded plan

→ then, in the NEXT task,
   implement locally and replay the frozen 22 outputs

→ only after that local persistence proof passes,
   authorize a separate NEW fresh unseen proof.
```

Do NOT:

```text
reopen model semantics

reopen decision policy

patch old free-text fields ad hoc

mark legacy rows canonically accepted

let the public API mint acceptance receipts

use mutable same-date upsert as canonical history

rely on process-local locks for correctness

run models

run fresh issuers

touch production DB

resume schedules

merge main

deploy.
```
