# Thesis Monitor — Persistence V2 Implementation + Local Ephemeral Replay

## 0. Task identity

Suggested work-instruction filename:

```text
20260914-persistence-v2-implementation-local-ephemeral-replay.md
```

Suggested result bundle:

```text
thesis-monitor-20260914-persistence-v2-implementation-local-ephemeral-replay-report.zip
```

Master-workflow phase:

```text
M12BN — Persistence V2 Local Implementation Proof
         A. Freeze M12BM contract design exactly
         B. Implement CanonicalAcceptanceReceiptV1 locally
         C. Implement immutable AcceptedAssessmentV2 and current-state V2 tables
         D. Implement canonical persistence eligibility and trusted issuance boundary
         E. Implement acceptance-driven warning V2 lifecycle
         F. Implement transactional notification outbox V2
         G. Implement legacy/manual source classification and backward-compatible reads
         H. Implement idempotent forward-only V2 local migration
         I. Replay the frozen 22 M12BJ positive outputs
         J. Reject the historical 16 canonical-failed fresh outputs
         K. Execute tamper / missing-receipt / quarantine / duplicate / stale / race /
            warning / outbox / failure-injection / timezone / ticker fixtures
         L. Prove zero semantic drift and zero production side effects
         M. If all executable local proof gates pass, authorize only a separately instructed
            NEW fresh unseen proof
```

This task IMPLEMENTS the M12BM design.

It is NOT a redesign task unless the selected M12BM contract is mechanically impossible to
implement without violating one of its frozen requirements.

Do NOT reopen:

```text
semantic services

FCF / net-debt / working-capital / financial-sector semantics

ConfiguredSignalEvidenceView

BusinessDeltaEvidenceView

MarketExpectationEvidenceView

decision boundary policy

holder policy

new-buyer policy

same-direction calibration policy.
```

Do NOT change:

```text
model prompts

model schemas

canonical final output semantics

direction thresholds

holder definitions

Business Delta definitions.
```

No model calls.
No provider calls.
No production database.
No external sends.
No scheduler mutation.
No remote push.
No main merge.
No deployment.
No fresh unseen proof in M12BN.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design-report.zip
```

Verified SHA-256:

```text
4c37dc1ea733cda1bea508abfc1eefa8d0ac576e49d7bea6e11e26d68c736947
```

Recompute independently at task start.

Sidecar must match exactly.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent archive verification from the submitted result:

```text
indexed payloads = 91

ZIP entries =
91 indexed payloads
+ artifact-index.json
= 92

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0.
```

Recompute independently.

---

# 2. M12BM authoritative result

Freeze:

```text
status =
COMPLETE_DESIGN_ONLY

top_level_design_result =
PERSISTENCE_V2_CONTRACT_DESIGN_COMPLETE

next_scope =
BOUNDED_PERSISTENCE_V2_IMPLEMENTATION_AND_LOCAL_REPLAY
```

M12BM repository reference:

```text
integration branch =
codex/20260914-canonical-acceptance-persistence-design-m12bm

base integration head =
1f1155711f9cda1d98ea4d51f30eb43967f1f25d

final local head =
5e80c0122ca4c49cdd1ecc8cdf1eae5ad8ad5d94
```

M12BM validation:

```text
focused = PASS
12 passed

full local = PASS
3955 passed

ruff = PASS

git diff --check = PASS.
```

Start from the exact intended integrated local head according to repository workflow.
Do not silently omit M12BM design artifacts.

---

# 3. M12BM architecture — freeze

Selected architecture:

```text
OPTION_C_NEW_IMMUTABLE_ACCEPTED_V2_AND_DERIVED_CURRENT_STATE
```

Reason:

```text
legacy UNIQUE(ticker, assessment_date) mutable rows cannot express
immutable same-date multi-generation canonical history.
```

New V2 tables:

```text
canonical_acceptance_receipt_v1

accepted_assessment_v2

monitoring_current_state_v2

assessment_source_registry_v2

warning_state_v2

warning_transition_v2

notification_outbox_v2.
```

Existing legacy `ThesisAssessment` remains.

Do NOT destructively rewrite legacy storage.

---

# 4. Source trust domains — freeze

Exactly three domains:

```text
CANONICAL_MODEL_ACCEPTED

MANUAL_USER_AUTHORED

LEGACY_UNVERIFIED.
```

Automation eligibility:

```text
CANONICAL_MODEL_ACCEPTED = true

MANUAL_USER_AUTHORED = false

LEGACY_UNVERIFIED = false.
```

Manual assessment support remains:

```text
true.
```

The existing public/action path:

```text
recordThesisAssessment
```

remains a manual-history path.

It must NOT:

```text
mint a canonical receipt

self-assert canonical PASS

drive warning V2 automation

drive material notification V2 automation.
```

Reserved canonical fields supplied through the public/manual request must fail closed
or be explicitly rejected according to the M12BM compatibility contract.

No silent promotion.

---

# 5. Canonical acceptance receipt contract — freeze

Contract version:

```text
canonical-acceptance-receipt-v1
```

Field count:

```text
25.
```

Trusted issuer count:

```text
1.
```

Trusted issuer:

```text
canonical_two_stage_finalizer_v1
```

External/manual request can mint receipt:

```text
false.
```

Canonical serialization:

```text
canonical-json-utf8-sorted-compact-v1.
```

Acceptance identity:

```text
canonical-acceptance-id-v1.
```

Receipt hash:

```text
canonical-acceptance-receipt-hash-v1.
```

---

# 6. Canonical receipt exact fields

Implement the exact M12BM receipt envelope:

```text
1. receipt_contract_version
2. acceptance_id
3. receipt_hash
4. receipt_status
5. trusted_issuer_id
6. generation_id
7. generation_generated_at
8. ticker
9. thesis_version
10. assessment_date
11. effective_at
12. accepted_at
13. source_packet_id
14. packet_hash
15. source_evidence_snapshot_identity
16. accepted_payload_contract_version
17. canonical_serialization_contract
18. final_composed_candidate_hash
19. canonical_semantic_audit_contract
20. canonical_semantic_audit_status
21. finalization_status
22. core_immutability_status
23. core_hash
24. stance_hash
25. quarantine_reason_codes.
```

No additional user-controlled field may alter canonical identity.

No field may be silently dropped during verify/persist.

---

# 7. Receipt states

Supported receipt states:

```text
ACCEPTED

REJECTED

QUARANTINED.
```

Only:

```text
ACCEPTED
```

with all required PASS/provenance conditions may enter canonical V2 persistence.

Legacy rows do not have a receipt.

They are:

```text
LEGACY_UNVERIFIED.
```

Do not fabricate historical receipts.

---

# 8. Acceptance ID

Implement:

```text
acceptance_id =
"ca1_" +
sha256(
  canonical JSON of proof-critical receipt material
  excluding:
    acceptance_id
    receipt_hash
    accepted_at
)
```

Required properties:

```text
same accepted semantic/result identity
→ same acceptance_id

different final candidate
→ different acceptance_id

different generation
→ different acceptance_id

different ticker
→ different acceptance_id

tampering
→ detected.
```

Do not use random UUID as the canonical idempotency identity.

A DB surrogate key is optional but cannot replace `acceptance_id`.

---

# 9. Receipt hash

Receipt hash covers the complete receipt envelope
except the hash field itself, according to M12BM.

It includes:

```text
accepted_at.
```

Therefore implement explicit repeat-issuance behavior:

```text
same acceptance_id already exists
→ return / verify the exact existing immutable receipt
→ do NOT mint a second receipt with a fresh accepted_at
→ do NOT change receipt_hash
→ do NOT update accepted_at.
```

This requirement is mandatory.

Add a deterministic fixture:

```text
issue same TrustedFinalizationResult twice
```

Expected:

```text
same acceptance_id
same accepted_at
same receipt_hash
receipt row delta on second issue = 0.
```

This closes any ambiguity created by `accepted_at` not being part of acceptance_id.

---

# 10. Trusted receipt issuance boundary

Implement an internal typed issuance API.

Input:

```text
TrustedFinalizationResult
```

or repository-equivalent frozen internal type.

Arbitrary:

```text
dict
Mapping
public API body
manual assessment payload
```

must NOT be sufficient to mint an ACCEPTED receipt.

Receipt issuance preconditions:

```text
runtime/schema success

canonical semantic audit PASS

final composition PASS

core immutability PASS

source packet/evidence identities present

not quarantined

canonical ticker

positive thesis_version

valid business assessment_date

offset-aware generation/effective timestamps

supported final payload contract.
```

Fail closed.

Do not allow:

```text
canonical_semantic_audit_status="PASS"
```

in user JSON to establish trust.

---

# 11. Receipt verifier

Implement a pure verifier.

Required checks:

```text
supported receipt version

exact receipt envelope

supported canonical serialization version

acceptance_id recomputation

receipt_hash recomputation

trusted issuer

ticker / thesis version / date identity

offset-aware timestamp validity

packet/source snapshot binding

final payload hash equality

canonical semantic status = PASS

finalization status = PASS

core immutability = PASS

receipt_status = ACCEPTED

quarantine_reason_codes empty.
```

Verifier does NOT:

```text
rerun semantic classification

parse model rationale semantically

repair output

infer missing values.
```

---

# 12. AcceptedAssessmentV2

Implement:

```text
accepted-assessment-v2.
```

Table:

```text
accepted_assessment_v2.
```

Primary key:

```text
acceptance_id.
```

Mutability:

```text
APPEND_ONLY.
```

One accepted identity maps to one immutable accepted row.

No application-level UPDATE/DELETE path for canonical accepted history.

---

# 13. Accepted payload authority

Authoritative payload:

```text
canonical_payload_json.
```

Store:

```text
canonical_payload_contract_version

canonical_payload_sha256.
```

Required:

```text
canonical_payload_sha256
==
receipt.final_composed_candidate_hash.
```

Any structured/extracted columns must exactly match
the hash-bound canonical payload.

Add:

```text
extract_consistency_gate.
```

Mismatch:

```text
REJECT_BEFORE_TRANSACTION.
```

Never “repair” extracts to fit the row.

---

# 14. AcceptedAssessmentV2 typed decision fields

Implement the M12BM storage design, including:

```text
overall_direction

directional_balance_buy

directional_balance_sell

hold_lean

directional_confidence

canonical_business_delta.
```

Canonical Business Delta is stored directly:

```text
STRENGTHENED

UNCHANGED

WEAKENED

UNRESOLVED.
```

No legacy coercion.

Specifically forbidden:

```text
UNRESOLVED → NO_MATERIAL_CHANGE.
```

---

# 15. Structured context storage

Implement versioned exact representations for accepted owned fields such as:

```text
business_thesis_context_json

earnings_estimate_context_json

market_expectation_context_json

valuation_context_json

risk_context_json

sector_interpretation_json

buy_drivers_json

sell_drivers_json

dominant_evidence_json

uncertainty_limit_json

core_judgment_json

structured_unknowns_json

material_anchor_refs_json

new_buyer_json

holder_json

reevaluation_up_json

reevaluation_down_json.
```

These are exact accepted payload extracts.

Do not invent:

```text
confirmed_facts

inferred_implications

summary
```

if the current accepted payload does not own them.

No persistence-time summarization.

---

# 16. New-buyer structured storage

Persist canonical new-buyer structure losslessly.

At minimum preserve:

```text
stance

summary if owned

confirmation condition

bound evidence refs / provenance.
```

Do not make free-text `new_buyer_view`
the authoritative representation.

Do not derive stance from primary direction.

---

# 17. Holder structured storage

Persist canonical holder structure losslessly.

At minimum preserve:

```text
holder stance

holder summary

business confirmation condition

business invalidation condition

bound evidence refs / provenance.
```

No:

```text
SELL → REDUCE

UNCHANGED → HOLDABLE
```

downstream mapping.

---

# 18. Market expectation storage

Persist exact accepted market-expectation structure.

Do not convert:

```text
market expectation
```

into:

```text
Business Delta

warning state

holder stance.
```

No persistence-side semantic interpretation.

---

# 19. Unknowns

Use the M12BM versioned structured-unknown representation.

Do not reduce structured unknowns to a bare list of strings
for the canonical V2 authority.

Legacy/manual read projection may remain lossy only where the API contract explicitly permits it.

Canonical V2 must remain lossless.

---

# 20. Confidence and risk

Canonical confidence:

```text
LOW / MEDIUM / HIGH.
```

Store the enum.

Do NOT introduce a hidden float mapping.

Risk:

```text
structured accepted claim/context
```

according to M12BM.

Do not synthesize a scalar risk level
unless the accepted payload explicitly owns one.

---

# 21. Security / share-basis provenance

Implement receipt-bound preservation of applicable:

```text
security basis

ADR/ADS basis

price currency

financial currency

per-share basis caveat

supporting evidence refs.
```

Store:

```text
security_basis_provenance_json

security_basis_provenance_sha256.
```

Projection must be receipt/payload-bound.

No second valuation engine.

---

# 22. Current state V2

Implement:

```text
monitoring_current_state_v2.
```

One row per ticker.

Required fields from M12BM:

```text
ticker

latest_acceptance_id

latest_effective_at_utc

latest_generation_generated_at_utc

latest_generation_id

latest_ordering_acceptance_id

latest_assessment_date

latest_thesis_version

row_version

updated_at_utc.
```

This row is DERIVED current state.

It is not immutable history.

---

# 23. Stale-safe total order

Implement:

```text
accepted-assessment-total-order-v1
```

ordered by:

```text
1. effective_at_utc
2. generation_generated_at_utc
3. generation_id
4. acceptance_id.
```

Do NOT include:

```text
assessment_date

accepted_at

DB insert order.
```

All timestamps must be offset-aware at input and normalized to UTC.

---

# 24. Ordering behavior

Exact behavior:

```text
same acceptance
→ IDEMPOTENT_ALREADY_APPLIED

higher ordering tuple
→ eligible for current-state advancement

lower ordering tuple
→ immutable history may be retained if valid and absent
→ current state unchanged
→ warning state unchanged
→ outbox unchanged.
```

A stale valid result is not deleted from history.

It simply cannot move the system backward.

---

# 25. Current-state CAS

Use DB-level correctness.

Local SQLite proof:

```text
BEGIN IMMEDIATE
```

or repository-equivalent deterministic mechanism.

Algorithm:

```text
insert immutable history idempotently

read current tuple + row_version

conditional UPDATE using row_version and expected old tuple

on conflict:
  reread

  if candidate is now stale:
    NO_OP_STALE

  else:
    bounded retry
```

Do not rely on process-local locks.

Retries must preserve identity.

---

# 26. Concurrent first insert

Explicitly handle:

```text
current-state row absent
```

under concurrent writers.

Use:

```text
unique PK(ticker)

insert-on-conflict / retry / reread
```

or equivalent.

Acceptance:

```text
current row ends at greatest total-order tuple.
```

No duplicate current-state row.

---

# 27. Warning V2 identity

Implement:

```text
warning_state_v2

warning_transition_v2.
```

Warning identity is condition-based, not call-count-based.

Use exact M12BM identity inputs including:

```text
ticker

thesis_version

warning_type

condition_contract_version

condition_identity.
```

Do not key warning identity by assessment date alone.

---

# 28. Warning observation input

Implement trusted warning observation structure:

```text
canonical-warning-observation-v1
```

Fields:

```text
warning_type

condition_contract_version

condition_identity

observation

transition_reason_code

transition_reason_version

evidence_refs.
```

Observations:

```text
CONFIRMED

WORSENED

RECOVERED

UNRESOLVED.
```

Evidence refs must be a subset of receipt-bound accepted/source evidence.

No raw-text configured-signal reinterpretation inside warning persistence.

---

# 29. Warning state machine

Implement the M12BM state machine exactly.

States:

```text
absent

open

escalated

resolved.
```

Key rules:

```text
absent + CONFIRMED/WORSENED → open

open + CONFIRMED → open, no transition event

open + WORSENED → escalated

open + RECOVERED → resolved

escalated + CONFIRMED/WORSENED → escalated, no new transition event

escalated + RECOVERED → resolved

resolved + CONFIRMED/WORSENED → new open episode

UNRESOLVED does not itself change state.
```

No call-count escalation.

---

# 30. Warning episode

`episode` increments only on recurrence after resolution.

Same warning episode remains stable through:

```text
open → escalated → resolved.
```

Resolved recurrence:

```text
resolved → open
```

creates the next episode.

Define/test exact increment behavior.

---

# 31. Warning transition idempotency

Transition identity:

```text
sha256(
  warning_identity,
  episode,
  from_state,
  to_state,
  triggering_acceptance_id,
  transition_reason_version
)
```

or the exact M12BM canonical serialization equivalent.

Same acceptance replay:

```text
warning transition delta = 0.
```

Same-date repeated CONFIRMED:

```text
must NOT escalate.
```

Escalation requires a NEWER:

```text
WORSENED
```

accepted observation.

---

# 32. Warning stale guard

Warning state tracks:

```text
latest_observation_acceptance_id

latest_ordering_key_json.
```

If incoming acceptance ordering is lower:

```text
warning state = no-op

transition rows = 0

outbox rows = 0.
```

No stale recovery.
No stale escalation.

---

# 33. Notification outbox V2

Implement:

```text
notification_outbox_v2.
```

Required fields from M12BM include:

```text
outbox_event_id

event_kind

source_event_id

acceptance_id

channel

payload_contract_version

payload_json

payload_sha256

status

attempt_count

next_attempt_at_utc

last_error_code

sent_at_utc

created_at_utc.
```

Semantic payload fields are immutable after insertion.

Operational delivery fields may change.

---

# 34. Notification event kinds

Separate:

```text
DAILY_SUMMARY_NOTIFICATION

MATERIAL_STATE_TRANSITION_NOTIFICATION.
```

A daily summary is not automatically a material alert.

A material state notification requires a valid warning transition.

Do not send/queue material alerts merely because an assessment exists.

---

# 35. Outbox dedupe identity

Unique:

```text
(source_event_id, channel, payload_contract_version)
```

or exact design-equivalent constraint.

Material source event:

```text
warning_transition_id.
```

Daily summary source identity:

```text
schedule-run/ticker/acceptance slot identity
```

according to the M12BM contract.

Replay:

```text
outbox delta = 0.
```

---

# 36. External send

External delivery is POST-COMMIT only.

Never call sender inside the accepted-assessment DB transaction.

In M12BN:

```text
real external sender = disabled

fake/stub sender only

production_sends = 0.
```

If implementing an outbox worker,
test only against fake local sender.

Do not configure real channel credentials.

---

# 37. One accepted-assessment transaction

Implement:

```text
accepted-assessment-application-transaction-v2.
```

Pretransaction:

```text
verify trusted capability / receipt

verify payload hash and extract equality

verify warning observation refs if supplied.
```

Atomic DB transaction:

```text
1. insert receipt if absent

2. insert immutable accepted assessment if absent

3. conditionally advance current state if newer

4. apply only eligible/newer warning transitions

5. insert deduped outbox rows

6. commit once.
```

External send is not part of this transaction.

---

# 38. Transaction duplicate behavior

For exact already-applied acceptance:

```text
result =
IDEMPOTENT_ALREADY_APPLIED.
```

No mutation to:

```text
accepted_at

receipt hash

history

current row_version

warning state

warning transitions

outbox.
```

This must be asserted.

---

# 39. Partial failure

Implement failure injection tests at:

```text
receipt/payload verification

accepted-history insert

current-state CAS

warning transition

outbox insert

after commit / before send

during fake send.
```

Required semantics:

```text
verification fail
→ no durable state

history insert fail
→ rollback unless identical already exists

warning transition fail
→ rollback assessment lifecycle transaction

outbox insert fail
→ rollback assessment lifecycle transaction

after commit before send
→ DB state complete, pending outbox remains

send fail
→ accepted state unchanged, retry/dead-letter operational fields only.
```

No undefined partial commit.

---

# 40. Retry safety

Retry identities remain:

```text
acceptance_id

warning_transition_id

outbox_event_id.
```

Do not mint new identities on retry.

Semantic payload cannot change.

Bound retry count.

Terminal:

```text
dead_letter / manual review
```

or repository-equivalent.

No infinite loop.

---

# 41. Manual / legacy source registry

Implement:

```text
assessment_source_registry_v2.
```

Existing pre-V2 rows:

```text
LEGACY_UNVERIFIED

automation_eligible = false.
```

Future `recordThesisAssessment` rows:

```text
MANUAL_USER_AUTHORED

automation_eligible = false.
```

Insert the manual source registry row in the same transaction
as the legacy/manual assessment write.

---

# 42. Manual action reserved fields

The public/manual action must not accept or trust reserved fields such as:

```text
acceptance_id

receipt_hash

receipt_status

canonical_semantic_audit_status

generation_id

packet_hash

final_composed_candidate_hash

core_hash

stance_hash

source_domain=CANONICAL_MODEL_ACCEPTED.
```

Exact reserved set should follow implemented schemas.

Unknown reserved canonical fields:

```text
fail closed.
```

Do not silently ignore a spoofed acceptance claim.

---

# 43. Legacy history

Do not modify old `ThesisAssessment` rows.

Do not backfill:

```text
canonical receipt

packet hash

semantic PASS

finalization PASS

core hash

stance hash.
```

Only source classification metadata may be added.

All existing content remains readable.

---

# 44. Read-path V2

Implement internal dual-read behavior.

Current selection:

```text
verified V2 current-state pointer if valid.
```

If V2 absent:

```text
legacy/manual read allowed with explicit internal source-domain discrimination.
```

If V2 current pointer exists but is corrupt:

```text
fail closed / explicit unavailable integrity failure.
```

Do NOT silently fall back to a legacy/manual row
and pretend it is the canonical current state.

---

# 45. History reads

Internal V2 history returns discriminated sources:

```text
CANONICAL_MODEL_ACCEPTED

MANUAL_USER_AUTHORED

LEGACY_UNVERIFIED.
```

Same-date canonical generations remain distinct and total-order sorted.

Existing external/manual history behavior should remain compatible
unless explicitly versioned.

No hidden `UNRESOLVED` projection.

---

# 46. Business Delta legacy projection

If a legacy API cannot represent:

```text
UNRESOLVED
```

do NOT coerce it.

Use:

```text
null

unsupported marker

versioned new field
```

according to the M12BM design.

Exact behavior must be tested.

No `NO_MATERIAL_CHANGE` fallback.

---

# 47. Database migration implementation

Implement a LOCAL / DISABLED production migration path.

Create the seven V2 tables and required indexes/constraints.

Migration strategy:

```text
FORWARD_ONLY_DATA_PRESERVING.
```

Legacy table alterations:

```text
none.
```

Legacy row deletion:

```text
0.
```

Existing canonical receipts fabricated:

```text
0.
```

Existing semantic PASS fabricated:

```text
0.
```

---

# 48. Migration production gate

The V2 migration/runtime writer must remain default-disabled
for normal production startup.

Do NOT allow merely importing:

```text
app/models/accepted_assessment.py
```

to cause an unauthorized production migration.

Any startup migration hook must require an explicit disabled-by-default gate.

In M12BN:

```text
gate enabled only against temporary/local SQLite
under test or explicit local migration command.
```

No production DB URL.

---

# 49. Migration idempotency

Against ephemeral copied/local SQLite:

```text
first migration
→ seven tables created

legacy registry rows backfilled

second migration
→ schema delta = 0

legacy registry delta = 0.
```

Inspect:

```text
foreign keys

indexes

unique constraints

CHECK constraints where applicable.
```

No best-effort “table exists” only proof.

---

# 50. Migration rollback

M12BM selected:

```text
FORWARD_ONLY_DATA_PRESERVING.
```

Operational rollback:

```text
disable V2 writes/read preference

retain V2 tables/data.
```

Do not implement destructive down migration.

Test that disabling V2 preference
restores legacy/manual path without deleting canonical local V2 data.

---

# 51. M12BJ frozen positive cohort

Frozen accepted generation:

```text
20260911-m12ai-shadow-20260914T024739Z-1fe808eba817
```

Positive fixture count:

```text
22.
```

Do NOT call model again.

Locate the exact frozen final composed payload for each ticker
through the M12BJ manifests.

Hash-verify before use.

At minimum verify against the M12BM frozen identities for:

```text
ticker

assessment_date

generation_id

packet_id

packet_sha256

final_composed_candidate_sha256

canonical semantic contract/status

final composition status

core immutability status

core_sha256

stance_sha256.
```

If raw accepted payload required for lossless replay is unavailable:

```text
STOP
FROZEN_M12BJ_ACCEPTED_PAYLOAD_UNAVAILABLE
```

Do not reconstruct a payload from summary fields.

---

# 52. No fabricated receipt inputs

For M12BJ positive receipt issuance,
derive every required receipt field from verified frozen artifacts.

Do NOT fabricate:

```text
thesis_version

effective_at

generation_generated_at

source snapshot identity

payload contract version.
```

If a required field cannot be proven from frozen artifacts/design:

```text
STOP
CANONICAL_RECEIPT_FIXTURE_PROVENANCE_INCOMPLETE.
```

The purpose is executable proof, not fixture convenience.

---

# 53. Positive 22 receipt issuance

Expected:

```text
22 / 22
valid TrustedFinalizationResult inputs

22 / 22
ACCEPTED receipts

22 / 22
receipt verifier PASS

22 / 22
canonical accepted rows inserted locally.
```

No production write.

---

# 54. Positive 22 readback fidelity

For every ticker compare persisted canonical V2 readback
against the exact hash-bound accepted payload.

Required:

```text
canonical payload hash match

overall direction exact

balance exact

confidence exact

Business Delta exact

new-buyer exact

holder exact

market expectation exact

structured unknowns exact

material refs exact

reevaluation fields exact

security basis provenance exact where applicable.
```

Proof-critical lossy count:

```text
0.
```

---

# 55. Positive 22 provenance fidelity

Required per ticker:

```text
receipt acceptance_id valid

receipt hash valid

generation identity exact

packet identity exact

payload hash exact

semantic contract/status exact

finalization exact

core immutability exact

core hash exact

stance hash exact

source snapshot identity exact.
```

Provenance mismatch:

```text
0.
```

---

# 56. Historical fresh negative cohort

Historical generation:

```text
20260907-new-issuer-proof-20260907T055608Z-0446826566f6
```

Fixture count:

```text
16.
```

Frozen canonical failure:

```text
BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY
```

Do not mutate candidates.

Do not weaken Business Delta semantics.

Expected:

```text
ACCEPTED receipt count = 0

accepted_assessment_v2 rows = 0

current-state advances = 0

warning transitions = 0

outbox rows = 0.
```

A REJECTED diagnostic envelope may be constructed locally if the design owns one,
but it must not be persistence-eligible.

---

# 57. Missing receipt fixture

Structurally valid accepted-payload-like object
without receipt.

Expected:

```text
REJECTED_INVALID_RECEIPT
or exact contract-equivalent

accepted rows = 0.
```

Persistence must not rerun semantics
to “help” it become eligible.

---

# 58. Tampered receipt fixtures

At minimum tamper one at a time:

```text
ticker

packet_hash

final_composed_candidate_hash

canonical semantic status

core_hash

stance_hash

receipt_hash.
```

Expected:

```text
verification FAIL

accepted rows = 0

warning/outbox = 0.
```

---

# 59. Quarantine fixture

Receipt/candidate marked:

```text
QUARANTINED
```

or non-empty quarantine reason.

Expected:

```text
not canonical persistence eligible.
```

No automation.

---

# 60. External/manual receipt spoof fixture

Call the existing public/manual assessment path with reserved fields
attempting to claim canonical acceptance.

Expected:

```text
request rejected
or reserved canonical fields explicitly rejected

canonical receipt rows = 0

canonical accepted rows = 0

warning V2 = 0

outbox V2 = 0.
```

Ordinary manual request remains compatible.

---

# 61. Duplicate receipt issuance fixture

Issue the exact same frozen TrustedFinalizationResult twice.

Required:

```text
acceptance_id same

accepted_at same

receipt_hash same

receipt rows = 1

accepted rows = 1

current row_version delta on replay = 0

warning transition delta = 0

outbox delta = 0.
```

---

# 62. Same-date distinct generation fixture

Use two distinct valid accepted identities:

```text
same ticker

same assessment_date

different generation / final identity.
```

Required:

```text
history rows = 2

no overwrite

current winner =
greatest accepted-assessment-total-order-v1 tuple.
```

This directly proves the old `(ticker,date)` limitation is removed.

---

# 63. Stale replay fixture

Persist newer valid acceptance first.

Then submit older valid acceptance.

Expected:

```text
older valid history may be inserted if absent

current state unchanged

warning state unchanged

warning transition delta = 0

outbox delta = 0

result =
REJECTED_STALE
or exact contract-equivalent for derived effects.
```

No stale overwrite.

---

# 64. Warning replay fixture

Apply an acceptance that opens a warning.

Replay same acceptance.

Expected:

```text
warning state unchanged

episode unchanged

transition rows delta = 0

outbox delta = 0.
```

No same-date escalation.

---

# 65. Warning new-confirmation fixture

From:

```text
open
```

apply a NEWER acceptance with:

```text
CONFIRMED
```

but not `WORSENED`.

Expected:

```text
open remains open

no transition event

no material-transition outbox.
```

This prevents call-count escalation.

---

# 66. Warning worsening fixture

From:

```text
open
```

apply a NEWER acceptance with:

```text
WORSENED.
```

Expected:

```text
state → escalated

one transition

one eligible material event per configured channel.
```

Replay:

```text
0 additional transitions

0 additional outbox rows.
```

---

# 67. Warning recovery fixture

From:

```text
open / escalated
```

NEWER:

```text
RECOVERED
```

Expected:

```text
resolved

one transition

material notification eligibility according to frozen contract.
```

Resolved + newer recurrence:

```text
episode increments

new open event.
```

---

# 68. Stale warning fixtures

Test both stale worsening and stale recovery.

Expected:

```text
state unchanged

episode unchanged

transition rows = 0

outbox rows = 0.
```

---

# 69. Notification daily summary fixture

Daily summary uses a distinct source identity.

Required:

```text
same schedule slot/ticker/acceptance/channel/payload version replay
→ one outbox row.
```

A daily summary does NOT require a material warning transition.

It must still require a valid accepted canonical assessment
if the V2 automation contract says so.

Manual/legacy rows are not eligible.

---

# 70. Notification material fixture

Requires a valid warning transition.

Same warning transition replay:

```text
one outbox row per channel/payload version.
```

No duplicate.

No transition:

```text
no material outbox.
```

---

# 71. Outbox post-commit send fixture

Use fake sender.

Prove:

```text
DB transaction commits accepted/warning/outbox state first

sender is called only after commit by worker

sender failure does not roll back accepted semantic state

payload semantic fields do not mutate on retry.
```

Production sender call count:

```text
0.
```

---

# 72. Outbox retry fixture

Same outbox event:

```text
attempt_count increments operationally

semantic payload hash unchanged

outbox_event_id unchanged.
```

Bound retries.

Terminal path:

```text
dead_letter
```

or contract-equivalent.

No new semantic event id.

---

# 73. Failure injection — history insert

Inject failure.

Expected:

```text
transaction rollback

no current advance

no warning transition

no outbox.
```

Unless exact immutable row already exists,
in which case classify:

```text
IDEMPOTENT_ALREADY_APPLIED.
```

---

# 74. Failure injection — current CAS

Simulate conflict.

Expected:

```text
reread current tuple

if stale:
NO_OP_STALE

if still newer:
bounded retry with same acceptance_id.
```

No duplicate history.

No duplicate warning/outbox.

---

# 75. Failure injection — warning transition

Expected:

```text
whole accepted-assessment application transaction rolls back
for the new application

no partial current-state advancement
without its warning/outbox consequences.
```

Existing earlier durable rows remain unchanged.

---

# 76. Failure injection — outbox insert

Expected:

```text
application transaction rollback

no partial warning/current advance.
```

No silent loss of notification event.

---

# 77. Failure injection — after commit

Simulate crash:

```text
after DB commit
before fake send.
```

Expected:

```text
accepted history durable

current state durable

warning transition durable

outbox pending durable

safe replay / worker resume.
```

No second semantic event.

---

# 78. Concurrency fixture — identical

Two concurrent local attempts:

```text
same acceptance.
```

Expected:

```text
receipt rows = 1

accepted rows = 1

current = that acceptance

warning/outbox duplicates = 0.
```

Use separate DB sessions/connections.

Do not simulate concurrency with sequential function calls only.

---

# 79. Concurrency fixture — distinct same date

Two valid acceptances:

```text
same ticker/date
different ordering tuple.
```

Run concurrently.

Expected:

```text
history = 2

current = greatest tuple

loser derived effects = 0

winner derived effects exactly once.
```

---

# 80. Concurrency fixture — older/newer race

Commit order must not determine current state.

Test:

```text
older commits last

newer commits first
```

and reverse if feasible.

Expected:

```text
current = newer by total-order contract.
```

---

# 81. Timezone fixture

Reject naive timestamps.

Normalize aware timestamps to UTC.

Prove:

```text
assessment_date
is business/user date

not ordering timestamp.
```

Include KST midnight boundary.

No UTC-date overwrite of KST business date.

---

# 82. Ticker identity fixture

Required:

```text
"000660" → PASS

"660" → REJECT

660 → REJECT

"IBM" → PASS

"ibm" → REJECT.
```

Normalization belongs upstream of receipt issuance.

Receipt verifier does not zero-pad or uppercase.

---

# 83. Migration empty-DB fixture

New temporary SQLite.

Run migration.

Verify all seven tables/constraints/indexes.

No legacy rows.

Second run:

```text
zero schema delta.
```

---

# 84. Migration existing-DB fixture

Create/copy a representative local legacy schema with rows.

Run migration.

Expected:

```text
legacy rows unchanged

one source-registry row per legacy assessment

source_domain =
LEGACY_UNVERIFIED

automation_eligible =
false.
```

Second run:

```text
zero backfill delta.
```

No fabricated canonical fields.

---

# 85. Future manual row fixture

Use ordinary `recordThesisAssessment` local path.

Expected:

```text
legacy/manual assessment stored

source registry row stored in same transaction

source_domain =
MANUAL_USER_AUTHORED

automation_eligible =
false

canonical receipt rows delta = 0

accepted V2 rows delta = 0

warning V2 delta = 0

outbox V2 delta = 0.
```

Existing API request/response compatibility remains.

---

# 86. Read compatibility fixture

Verify:

```text
V2 current exists and valid
→ typed canonical current returned internally

V2 absent
→ legacy/manual read available

V2 pointer corrupt
→ explicit integrity/unavailable result

NOT
silent legacy fallback.
```

---

# 87. History compatibility fixture

Verify:

```text
legacy rows remain visible

manual rows remain visible

canonical V2 rows visible with source domain

same-date V2 generations all visible

canonical V2 sorted by total ordering.
```

Unsupported legacy projection:

```text
explicit null/unsupported.
```

---

# 88. No post-acceptance semantic re-derivation

Search all newly changed persistence/warning/outbox/read code.

Forbidden independent semantics:

```text
FCF logic

net-debt logic

WC direction logic

Business Delta inference

market-expectation inference

HOLDABLE/REVIEW/REDUCE inference

BUY/HOLD/SELL inference

configured-signal fulfillment inference.
```

Allowed:

```text
typed mapping

receipt verification

identity / ordering

state transition using trusted observation enum

presentation projection.
```

Required:

```text
post_acceptance_semantic_rederivation_count = 0.
```

---

# 89. Model-facing freeze

Verify unchanged semantic hashes / source identity for:

```text
model prompts

model schemas

directional-core-semantic-audit-v1

ConfiguredSignalEvidenceView

BusinessDeltaEvidenceView

MarketExpectationEvidenceView

WorkingCapitalCheckpointBindingView

decision policy

final accepted model-output schema.
```

Expected:

```text
model_prompt_semantic_change_count = 0

model_schema_semantic_change_count = 0

canonical_semantic_service_change_count = 0

decision_policy_change_count = 0

final_model_output_schema_change_count = 0.
```

Persistence schema changes are allowed.

---

# 90. No new semantic acceptance for historical fresh proof

M12BN must not “upgrade” the old 16 fresh outputs.

Required:

```text
historical_fresh_canonical_pass_count remains 0

historical_fresh_accepted_receipt_count = 0

historical_fresh_v2_persistence_count = 0.
```

No reclassification.

---

# 91. V2 runtime cutover remains disabled

M12BN implements and tests locally.

Do NOT enable:

```text
production V2 writer

production V2 current-read preference

production warning V2

production notification outbox delivery.
```

Feature/runtime gates remain disabled by default.

The existing production path must not start using V2 merely because the code is present.

---

# 92. Production firewall

Required:

```text
production_db_mutations = 0

monitoring_registrations = 0

monitoring_stops = 0

assessment_production_writes = 0

warning_production_mutations = 0

notification_production_queue_writes = 0

production_sends = 0

provider_source_fetches = 0

model_calls = 0

external_proof_network_calls = 0

remote_push_count = 0

raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0

main_merges = 0

deployments = 0

scheduler_mutation_count = 0

automatic_monitoring_resume = 0.
```

Monitoring schedules remain paused.

All DB proof uses temporary/local SQLite.

---

# 93. Expected implementation modules

M12BM proposed these bounded implementation paths:

```text
app/models/accepted_assessment.py

app/models/__init__.py

app/schemas/accepted_assessment_v2.py

app/services/canonical_acceptance_receipt_service.py

app/services/accepted_assessment_persistence_service.py

app/services/accepted_assessment_read_service.py

app/services/warning_lifecycle_v2_service.py

app/services/notification_outbox_service.py

app/services/monitoring_service.py

app/database.py

app/jobs/migrate_accepted_assessment_v2.py

tests/fixtures/persistence_v2/.
```

Use actual repository conventions.

Additional tests/migration helpers are allowed if narrowly required.

If implementation requires broad unrelated runtime changes:

```text
STOP
PERSISTENCE_V2_IMPLEMENTATION_SCOPE_EXPANSION.
```

---

# 94. No production migration framework invention

If the repository already has a migration mechanism:

```text
use it.
```

If it does not:

```text
implement the bounded idempotent local/new-table migration mechanism
specified by M12BM.
```

Do not introduce a large external migration framework
solely for M12BN unless repository architecture requires it.

No production migration execution.

---

# 95. Full local test gate

Run:

```text
focused new V2 tests

existing persistence/monitoring tests

semantic convergence regression tests

full local test suite

Ruff

git diff --check.
```

Required:

```text
PASS.
```

No disabling existing tests to get green.

No changing frozen expected semantic outputs.

---

# 96. Performance / scope sanity

This is not a performance-optimization task.

Still verify:

```text
no obvious N+1 on V2 current/history reads

indexes support ordering and outbox scan

receipt verification is deterministic

large canonical JSON is not repeatedly semantically parsed.
```

Do not over-optimize.

---

# 97. Top-level implementation outcome

Choose exactly one:

```text
PERSISTENCE_V2_LOCAL_IMPLEMENTATION_PROOF_PASS

BOUNDED_PERSISTENCE_V2_IMPLEMENTATION_REPAIR_REQUIRED

PERSISTENCE_V2_DESIGN_CONTRACT_INVALIDATED.
```

Use:

```text
PERSISTENCE_V2_DESIGN_CONTRACT_INVALIDATED
```

only if executable proof reveals a contradiction in M12BM design
that cannot be fixed without redesign.

Do NOT use it for ordinary coding bugs.

---

# 98. PASS criteria

`PERSISTENCE_V2_LOCAL_IMPLEMENTATION_PROOF_PASS`
requires at least:

```text
1. seven V2 tables created locally with intended constraints

2. migration idempotent

3. legacy rows classified LEGACY_UNVERIFIED without mutation

4. manual rows classified MANUAL_USER_AUTHORED

5. external/manual caller cannot mint receipt

6. receipt issue/verify deterministic and tamper-safe

7. repeat issuance returns exact existing receipt identity/time/hash

8. 22 / 22 M12BJ accepted outputs produce valid ACCEPTED receipts

9. 22 / 22 persist to immutable V2 locally

10. 22 / 22 read back losslessly

11. provenance mismatch = 0

12. historical fresh 16 / 16 cannot persist canonically

13. missing/tampered/quarantined receipt rejected

14. accepted history immutable

15. same acceptance replay idempotent

16. same-date distinct generations retained

17. stale replay cannot move current state backward

18. DB race ends at maximum ordering tuple

19. warning same-acceptance replay idempotent

20. CONFIRMED alone does not call-count escalate

21. WORSENED/RECOVERED state transitions correct

22. warning stale observations no-op

23. outbox dedupe correct

24. external send outside transaction

25. failure-injection leaves only defined durable states

26. manual/legacy rows remain automation-ineligible

27. read compatibility passes

28. post-acceptance semantic re-derivation = 0

29. proof-critical persistence data loss = 0

30. all production side effects = 0

31. model/provider/network proof calls = 0

32. V2 production gates remain disabled

33. full tests/Ruff/diff pass.
```

---

# 99. Fresh proof readiness after PASS

If and only if M12BN PASS:

```text
fresh_real_proof_readiness =
READY_FOR_SEPARATELY_AUTHORIZED_PROOF.
```

This does NOT authorize running it inside M12BN.

Required next scope:

```text
NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE.
```

Still:

```text
final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY.
```

The next fresh proof must be separately instructed.

---

# 100. If bounded implementation repair is required

If local executable proof exposes an implementation bug:

```text
next_scope =
BOUNDED_PERSISTENCE_V2_IMPLEMENTATION_REPAIR_AND_LOCAL_REPLAY.
```

The report must identify:

```text
exact failing contract

exact module

exact fixture

whether design remains valid

minimal repair.
```

Do not reopen semantic/model policy.

---

# 101. If design is invalidated

Only if M12BM itself is internally impossible,
for example:

```text
acceptance identity cannot be deterministic with required provenance

transaction contract cannot represent required atomicity in supported DB architecture

read compatibility cannot be met without corrupting source trust domains.
```

Then:

```text
next_scope =
PERSISTENCE_V2_CONTRACT_DESIGN_AMENDMENT.
```

Provide one precise contradiction.

Do not silently redesign while implementing.

---

# 102. Required provenance artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bn-scope-freeze

04-m12bm-design-contract-freeze

05-production-firewall-precheck

06-model-semantic-policy-no-change-freeze

07-v2-feature-gate-freeze.
```

---

# 103. Required implementation artifacts

Produce:

```text
08-v2-model-implementation

09-v2-schema-implementation

10-canonical-receipt-service-implementation

11-persistence-eligibility-implementation

12-accepted-assessment-persistence-implementation

13-current-state-cas-implementation

14-warning-lifecycle-v2-implementation

15-notification-outbox-v2-implementation

16-manual-source-registry-integration

17-v2-read-service-implementation

18-local-migration-implementation

19-implementation-change-map-final.
```

---

# 104. Required migration proof artifacts

Produce:

```text
20-empty-db-migration-replay

21-existing-db-migration-replay

22-migration-second-run-idempotency

23-legacy-registry-backfill-proof

24-v2-schema-introspection

25-v2-index-constraint-introspection

26-operational-rollback-disable-proof.
```

---

# 105. Required receipt proof artifacts

Produce:

```text
27-receipt-contract-unit-tests

28-trusted-issuer-boundary-proof

29-external-manual-spoof-rejection

30-receipt-tamper-matrix

31-repeat-issuance-idempotency-proof

32-payload-extract-consistency-proof

33-m12bj-22-receipt-issuance-proof

34-historical-fresh-16-receipt-rejection-proof.
```

---

# 106. Required positive replay artifacts

Produce:

```text
35-m12bj-frozen-input-identity-manifest

36-m12bj-22-local-persistence-replay

37-m12bj-22-readback-fidelity

38-m12bj-22-provenance-fidelity

39-m12bj-22-current-state-result

40-m12bj-22-data-loss-audit.
```

---

# 107. Required negative fixtures

Produce:

```text
41-missing-receipt-rejection

42-failed-receipt-rejection

43-quarantined-receipt-rejection

44-tampered-receipt-rejection

45-final-composition-failure-rejection

46-core-immutability-failure-rejection

47-malformed-canonical-enum-rejection

48-ticker-identity-rejection

49-naive-timestamp-rejection.
```

---

# 108. Required ordering/idempotency artifacts

Produce:

```text
50-duplicate-acceptance-replay

51-same-date-distinct-generation-replay

52-stale-replay

53-current-state-cas-conflict-replay

54-concurrent-identical-acceptance-race

55-concurrent-same-date-distinct-race

56-concurrent-older-newer-race

57-total-ordering-invariant-audit.
```

---

# 109. Required warning artifacts

Produce:

```text
58-warning-open-replay

59-warning-confirmed-no-escalation

60-warning-worsened-escalation

61-warning-recovery

62-warning-resolved-recurrence

63-warning-stale-worsened-noop

64-warning-stale-recovery-noop

65-warning-transition-idempotency-audit.
```

---

# 110. Required outbox artifacts

Produce:

```text
66-daily-summary-outbox-dedupe

67-material-transition-outbox-dedupe

68-no-transition-no-material-outbox

69-outbox-postcommit-send-boundary

70-outbox-retry-identity

71-outbox-dead-letter-fixture.
```

---

# 111. Required transaction/failure artifacts

Produce:

```text
72-failure-injection-history-insert

73-failure-injection-current-cas

74-failure-injection-warning-transition

75-failure-injection-outbox-insert

76-failure-after-commit-before-send

77-failure-during-fake-send

78-partial-state-invariant-audit.
```

---

# 112. Required compatibility artifacts

Produce:

```text
79-manual-action-backward-compatibility

80-future-manual-source-classification

81-legacy-source-classification

82-current-read-v2-preference

83-corrupt-v2-pointer-fail-closed

84-history-dual-read-compatibility

85-business-delta-legacy-projection-audit

86-timezone-boundary-fixture

87-ticker-identity-fixture

88-security-basis-provenance-fidelity.
```

---

# 113. Required no-semantic-drift artifacts

Produce:

```text
89-post-acceptance-semantic-rederivation-scan

90-model-prompt-hash-freeze

91-model-schema-hash-freeze

92-canonical-semantic-service-freeze

93-decision-policy-freeze

94-final-model-output-schema-freeze.
```

---

# 114. Required test / firewall artifacts

Produce:

```text
95-focused-v2-test-results

96-existing-persistence-regression-tests

97-full-local-test-results

98-ruff-results

99-git-diff-check

100-production-db-zero-mutation-proof

101-production-send-zero-proof

102-scheduler-pause-preservation

103-remote-push-zero-proof

104-main-merge-zero-proof

105-deployment-zero-proof

106-secret-scan.
```

---

# 115. Required decisions

Produce:

```text
107-persistence-v2-local-proof-decision

108-fresh-real-proof-readiness-decision

109-main-merge-readiness-decision

110-production-readiness-decision

111-next-scope-decision

112-master-workflow-update

113-program-completion.
```

---

# 116. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch
final_local_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bm_top_level_design_result
m12bm_receipt_contract_version
m12bm_selected_schema_architecture

v2_table_count
v2_tables
migration_status
migration_second_run_schema_delta
migration_second_run_legacy_registry_delta
legacy_rows_modified_count
legacy_rows_deleted_count
fabricated_legacy_receipt_count
fabricated_legacy_semantic_pass_count

receipt_contract_version
receipt_field_count
trusted_issuer_count
external_request_can_mint_receipt

receipt_repeat_issue_same_acceptance_id
receipt_repeat_issue_same_accepted_at
receipt_repeat_issue_same_receipt_hash

receipt_tamper_failure_count
receipt_spoof_accept_count

accepted_assessment_v2_status
current_state_v2_status
source_registry_v2_status
warning_state_v2_status
warning_transition_v2_status
notification_outbox_v2_status

m12bj_fixture_count
m12bj_verified_payload_count
m12bj_accepted_receipt_count
m12bj_persisted_v2_count
m12bj_readback_lossy_count
m12bj_provenance_mismatch_count
m12bj_extract_consistency_failure_count

historical_fresh_fixture_count
historical_fresh_accepted_receipt_count
historical_fresh_persisted_v2_count
historical_fresh_warning_transition_count
historical_fresh_outbox_count

missing_receipt_rejection_status
failed_receipt_rejection_status
quarantined_receipt_rejection_status
tampered_receipt_rejection_status
finalization_failure_rejection_status
core_immutability_failure_rejection_status

manual_action_compatibility_status
manual_source_classification_status
manual_automation_eligible
legacy_source_classification_status
legacy_automation_eligible

duplicate_acceptance_status
duplicate_history_delta
duplicate_current_row_version_delta
duplicate_warning_transition_delta
duplicate_outbox_delta

same_date_distinct_generation_status
same_date_distinct_generation_history_count

stale_replay_status
stale_current_delta
stale_warning_transition_delta
stale_outbox_delta

concurrent_identical_status
concurrent_identical_history_count
concurrent_same_date_distinct_status
concurrent_older_newer_status
current_state_max_ordering_invariant

warning_replay_status
warning_confirmed_no_escalation_status
warning_worsened_status
warning_recovery_status
warning_recurrence_status
warning_stale_worsened_status
warning_stale_recovery_status

daily_outbox_dedupe_status
material_outbox_dedupe_status
external_send_postcommit_status
outbox_retry_identity_status

history_insert_failure_status
current_cas_failure_status
warning_transition_failure_status
outbox_insert_failure_status
after_commit_failure_status
fake_send_failure_status

timezone_fixture_status
ticker_identity_fixture_status
security_basis_provenance_status

post_acceptance_semantic_rederivation_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
canonical_semantic_service_change_count
decision_policy_change_count
final_model_output_schema_change_count

proof_critical_persistence_data_loss_count

v2_production_writer_enabled
v2_production_read_preference_enabled
v2_production_warning_enabled
v2_production_outbox_delivery_enabled

model_calls
provider_source_fetches
external_proof_network_calls

production_db_mutations
monitoring_registrations
monitoring_stops
assessment_production_writes
warning_production_mutations
notification_production_queue_writes
production_sends

remote_push_count
raw_model_artifact_remote_push_count
main_branch_mutations
main_merges
deployments

scheduler_mutation_count
automatic_monitoring_resume
observed_paused_schedule_count

top_level_implementation_result

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Anything genuinely unavailable:

```text
NOT_MEASURED
```

with reason.

Do not substitute zero for unknown.

---

# 117. Expected clean result

If all local executable proof passes:

```text
top_level_implementation_result =
PERSISTENCE_V2_LOCAL_IMPLEMENTATION_PROOF_PASS

v2_table_count = 7

migration_second_run_schema_delta = 0

migration_second_run_legacy_registry_delta = 0

external_request_can_mint_receipt = false

m12bj_fixture_count = 22

m12bj_accepted_receipt_count = 22

m12bj_persisted_v2_count = 22

m12bj_readback_lossy_count = 0

m12bj_provenance_mismatch_count = 0

historical_fresh_fixture_count = 16

historical_fresh_accepted_receipt_count = 0

historical_fresh_persisted_v2_count = 0

duplicate_history_delta = 0

duplicate_warning_transition_delta = 0

duplicate_outbox_delta = 0

proof_critical_persistence_data_loss_count = 0

post_acceptance_semantic_rederivation_count = 0

v2_production_writer_enabled = false

v2_production_read_preference_enabled = false

v2_production_warning_enabled = false

v2_production_outbox_delivery_enabled = false

model_calls = 0

provider_source_fetches = 0

production_db_mutations = 0

production_sends = 0

scheduler_mutation_count = 0

fresh_real_proof_readiness =
READY_FOR_SEPARATELY_AUTHORIZED_PROOF

final_main_merge_readiness =
NOT_READY

production_readiness =
NOT_READY

next_scope =
NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE.
```

Do NOT force these values if executable evidence disagrees.

---

# 118. Failure handling

## A. Design-field mismatch

If implementation discovers the M12BM report artifacts disagree with each other:

```text
STOP
PERSISTENCE_V2_DESIGN_ARTIFACT_CONFLICT.
```

Do not choose whichever is convenient.

## B. Receipt idempotency ambiguity

If same acceptance can mint a second differing immutable receipt:

```text
STOP
CANONICAL_RECEIPT_REPEAT_ISSUANCE_CONTRACT_FAILURE.
```

Do not weaken receipt hashing.

## C. Positive frozen payload unavailable

```text
STOP
FROZEN_M12BJ_ACCEPTED_PAYLOAD_UNAVAILABLE.
```

No reconstruction.

## D. Historical invalid fresh candidate persists

```text
STOP
QUARANTINED_FRESH_CANONICAL_PERSISTENCE_BYPASS.
```

## E. V2 readback loses canonical fields

```text
STOP
PERSISTENCE_V2_LOSSY_CANONICAL_READBACK.
```

## F. Same-date generation overwrite

```text
STOP
PERSISTENCE_V2_IMMUTABLE_HISTORY_FAILURE.
```

## G. Stale replay advances current/warning/outbox

```text
STOP
PERSISTENCE_V2_STALE_GUARD_FAILURE.
```

## H. Warning replay escalates

```text
STOP
WARNING_V2_IDEMPOTENCY_FAILURE.
```

## I. Outbox duplicates

```text
STOP
OUTBOX_V2_DEDUPE_FAILURE.
```

## J. Transaction leaves undefined partial state

```text
STOP
PERSISTENCE_V2_TRANSACTION_ATOMICITY_FAILURE.
```

## K. Race winner depends on commit order

```text
STOP
PERSISTENCE_V2_CONCURRENCY_ORDERING_FAILURE.
```

## L. Production side effect occurs

```text
STOP
PRODUCTION_FIREWALL_VIOLATION.
```

## M. All local implementation proof passes

Proceed only to:

```text
NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE
```

as a separately instructed task.

---

# 119. Local-only / production firewall

M12BN is LOCAL-ONLY.

Required:

```text
temporary/local SQLite only

fake sender only

no production credentials

no production migration

no production write

no real notification queue

no real notification delivery

no scheduler mutation

no model/provider call

no remote push

no main merge

no deployment.
```

Never package secrets.

Artifact secret scan required.

---

# 120. Final task principle

M12BM completed the persistence contract design.

M12BN must now prove the design in executable local code.

The required causal chain is:

```text
verified canonical finalization
→ trusted deterministic receipt
→ immutable typed AcceptedAssessmentV2
→ stale-safe current-state CAS
→ acceptance-driven idempotent warning transition
→ transactional deduped outbox
→ post-commit fake delivery
```

while preserving:

```text
legacy/manual readability

manual/legacy automation ineligibility

zero semantic re-derivation

zero production side effects.
```

The proof must use:

```text
22 real frozen M12BJ canonical positives

16 historical fresh canonical negatives

receipt tamper/spoof negatives

duplicate/stale/race/failure fixtures.
```

Do NOT:

```text
reopen semantic rules

reopen policy

reconstruct missing frozen payloads

fabricate provenance

upgrade legacy rows to canonical accepted

allow manual API to mint receipts

use assessment_date as stale ordering

use call count to escalate warnings

send externally

enable production V2

run a fresh proof

merge main

deploy.
```

Only after M12BN executable local proof is clean
may the workflow authorize a separate NEW fresh unseen proof.
