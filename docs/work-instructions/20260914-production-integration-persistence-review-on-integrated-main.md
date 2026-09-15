# Thesis Monitor — Production Integration / Persistence Review on Integrated Main

## 0. Task identity

Suggested work-instruction filename:

```text
20260914-production-integration-persistence-review-on-integrated-main.md
```

Suggested result bundle:

```text
thesis-monitor-20260914-production-integration-persistence-review-on-integrated-main-report.zip
```

Master-workflow phase:

```text
M12BL — Production Integration / Persistence Review
         A. Freeze M12BI semantic single-source convergence
         B. Freeze M12BJ complete monitored compatibility shadow
         C. Freeze M12BK-R2 real-cohort policy validation
         D. Keep historical fresh proof quarantined
         E. Map the production assessment / warning / notification / monitoring persistence paths
         F. Verify composed two-stage decisions map losslessly into persistence contracts
         G. Verify canonical semantic provenance is required before persistence eligibility
         H. Verify idempotency, duplicate suppression, transaction/rollback, and partial-failure behavior
         I. Verify warning lifecycle and notification eligibility without sending anything
         J. Replay the frozen 22 monitored outputs through a LOCAL / EPHEMERAL persistence harness only
         K. Run negative fixtures for invalid / stale / duplicate / provenance-missing inputs
         L. Decide whether production integration is structurally ready for a NEW fresh unseen proof
```

This is an OFFLINE / LOCAL-ONLY integration review.

Do NOT:

```text
run model calls
call providers
persist to production DB
mutate real watchlists
open/close real warnings
enqueue real notifications
send anything
resume schedules
merge main
deploy
push raw model artifacts.
```

This task must NOT reopen:

```text
FCF semantics
net-debt semantics
working-capital semantics
financial-sector semantics
configured-signal semantics
BusinessDeltaEvidenceView semantics
MarketExpectationEvidenceView semantics
primary-boundary policy
holder-boundary policy
new-buyer policy
same-direction calibration policy.
```

Those are frozen inputs.

The purpose is only:

```text
Can a canonically validated decision
flow through production persistence / warning / notification plumbing
without semantic loss, duplication, stale overwrite, or side effects?
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260914-real-cohort-policy-validation-against-frozen-boundary-contracts-report.zip
```

Verified SHA-256:

```text
0f845b5c0cf2d6fdef74228bebacdc08bf46543bd8bc0299bcfba6a1ee0c050e
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent archive verification:

```text
artifact_count = 45

ZIP entries =
45 indexed payloads
+ artifact-index.json
= 46

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Recompute independently.

---

# 2. M12BK-R2 completion — authoritative

Freeze:

```text
status = COMPLETE

top_level_policy_validation_result =
REAL_COHORT_VALIDATES_FROZEN_POLICY_CONTRACTS

policy_exception_count = 0

primary boundary =
5 / 5 tolerated

holder boundary =
3 / 3 tolerated

coupled entry boundary =
1 / 1 tolerated

same-direction calibration =
5 / 5 tolerated

Business Delta policy change required =
false

model-facing policy change required =
false

semantic-service change required =
false.
```

Next scope:

```text
PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_ON_INTEGRATED_MAIN.
```

---

# 3. Semantic convergence — frozen

M12BI proved:

```text
SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED

proof-critical bypass = 0

proof-critical duplicate semantic engines = 0

cross-path golden corpus divergence = 0.
```

Canonical orchestrator:

```text
directional-core-semantic-audit-v1
```

M12BL must consume this result.

Do not create a second persistence-specific semantic engine.

Persistence is downstream of canonical semantic acceptance.

---

# 4. Monitored compatibility proof — frozen

M12BJ full monitored shadow:

```text
generation =
20260911-m12ai-shadow-20260914T024739Z-1fe808eba817

active names = 22

contexts = 6

model calls = 18 / 18

final compositions = 22

aggregate finalization = PASS

hard semantic failure = 0

architecture regression = 0

canonical bypass = 0

legacy duplicate hard-decision participation = 0.
```

Use these frozen 22 outputs as LOCAL persistence fixtures.

Do not call the model again.

---

# 5. Historical fresh proof — quarantine remains hard

Historical fresh generation:

```text
20260907-new-issuer-proof-20260907T055608Z-0446826566f6
```

M12BI canonical re-audit:

```text
candidate count = 16

previously accepted = 16

canonical PASS = 0

canonical FAIL = 16

failure family =
BusinessDelta canonical contract.
```

Required:

```text
historical_fresh_readiness_evidence_used = false

historical_fresh_persistence_eligible = false.
```

M12BL must prove these invalid historical outputs
cannot accidentally pass a persistence-eligibility gate.

Do not rewrite them.

---

# 6. Primary M12BL question

Answer with code and deterministic replay evidence:

> Does the production integration path persist only canonically accepted decisions, preserve all decision semantics and provenance losslessly, behave idempotently, and keep warning/notification/scheduler side effects fail-closed?

This is the only top-level question.

---

# 7. Map the actual production integration call graph

Do NOT assume filenames.

Locate the actual current paths for:

```text
assessment persistence

monitoring state persistence

warning creation/update/close

notification queue writes

production send

scheduler-driven monitoring execution

manual/read-only review paths.
```

For each record:

```text
entrypoint

service/module

repository/model

transaction boundary

idempotency key

dedupe rule

provenance fields

side effects

caller(s).
```

Produce an actual call graph.

---

# 8. Persistence eligibility gate

Identify where a completed analysis becomes eligible for persistence.

Desired contract:

```text
PERSISTENCE_ELIGIBLE
only if:

1. model/runtime/schema success

2. canonical semantic audit PASS

3. final composition PASS

4. core immutability PASS

5. required provenance identities present

6. target ticker / assessment date valid

7. no stale-generation conflict

8. no quarantined-proof marker.
```

If no explicit eligibility gate exists:

```text
report the exact bypass path.
```

Do NOT implement a broad redesign in the audit phase
unless the repair is tiny, non-model-facing, and entirely deterministic.

Default:
audit first, decide repair scope at completion.

---

# 9. Canonical semantic receipt / provenance

Determine what production persistence currently records
or can deterministically verify for:

```text
generation id

ticker

assessment date

packet hash

final composed candidate hash

canonical semantic audit contract/version

canonical semantic audit status

model identity / effort if stored

source/evidence snapshot identity where available

finalization status

core hash / stance hash where applicable.
```

Do not invent schema fields.

Classify each desired identity:

```text
PERSISTED

DERIVABLE_AND_VERIFIABLE

MISSING_BUT_NONCRITICAL

MISSING_AND_PROOF_CRITICAL.
```

---

# 10. No persistence from raw model output alone

Required architecture:

```text
raw monolithic / Stage-1 / Stage-2 model output
must not directly persist an assessment.
```

Persistence must consume:

```text
final composed / accepted output
```

with canonical acceptance.

If any raw-path persistence bypass exists:

```text
STOP
RAW_MODEL_OUTPUT_PERSISTENCE_BYPASS.
```

---

# 11. Assessment field mapping audit

Map accepted final output into the actual persisted assessment schema.

At minimum inspect mappings for concepts equivalent to:

```text
business thesis change

valuation context

earnings estimate impact

market expectation assessment

confirmed facts

inferred implications

unknowns

summary

new-buyer view

holder view

price view

risk level

confidence

assessment date

ticker.
```

Use actual schema names.

For every field classify:

```text
EXACT

LOSSLESS_NORMALIZATION

INTENTIONAL_NOT_PERSISTED

LOSSY

INVALID_ENUM_MAPPING

MISSING.
```

No silent coercion.

---

# 12. Business-delta persistence mapping

Canonical model-facing / analysis enums may not exactly match persistence enums.

Audit the actual mapping.

Required principles:

```text
UNCHANGED / no-material-change semantics must map correctly

STRENGTHENED must not map to MIXED

WEAKENED must not map to INVALIDATED

UNRESOLVED must not be silently persisted as NO_MATERIAL_CHANGE
unless the production contract explicitly defines that mapping

invalidation candidate / invalidated / needs-review distinctions
must remain explicit if applicable.
```

If canonical output vocabulary differs from persistence vocabulary:

```text
require an explicit versioned mapping table.
```

No string guessing.

---

# 13. Market-expectation persistence mapping

Verify:

```text
expectation level

assessment/summary

evidence basis
```

do not become:

```text
business thesis delta

warning status

holder stance
```

through persistence-side convenience logic.

Market expectation remains its own dimension.

---

# 14. New-buyer / holder persistence separation

Verify separate persistence for:

```text
new-buyer view

holder view.
```

Do not allow:

```text
BUY → ATTRACTIVE

SELL → REDUCE

UNCHANGED → HOLDABLE

HOLD → WAIT
```

to be generated downstream as mechanical mappings.

Persist the validated stance output,
or an explicitly documented presentation transform only.

---

# 15. Price / supply separation

Verify production persistence does not convert:

```text
price move

technical signal

foreign/institutional/personal flow

positioning signal
```

into:

```text
business thesis change

holder REDUCE

fundamental warning
```

unless a separately authorized contract exists.

Preserve the established fundamental-vs-timing separation.

---

# 16. Warning lifecycle call graph

Map:

```text
warning create

warning update

warning acknowledge if applicable

warning resolve/close

warning supersede

warning dedupe.
```

For each identify:

```text
trigger source

required confirmed evidence

configured signal identity

assessment identity

ticker

warning type

status transition rules

transaction boundary.
```

Do not execute against production.

---

# 17. Configured signal vs fulfilled warning

Verify:

```text
configured strengthen/weaken/invalidation signal
alone
!=
current fulfilled warning.
```

Warning creation must require the existing fulfillment contract,
not merely existence of a configured signal.

No persistence-side re-derivation from raw text.

Use canonical configured-signal evidence outputs or equivalent authoritative state.

---

# 18. Warning lifecycle idempotency

Replay the SAME accepted assessment twice in the ephemeral harness.

Expected:

```text
no duplicate open warning

no duplicate assessment if contract says one per unique identity

no duplicate notification eligibility row

stable warning id / dedupe identity where applicable.
```

If the contract intentionally stores assessment history per run,
the second insert must still be distinguishable by an explicit run identity,
not accidental duplication.

Document actual intended behavior.

---

# 19. Warning resolution / stale overwrite

Test deterministic fixtures:

```text
A. old warning open
   + newer confirmed recovery
   → expected lifecycle transition

B. newer warning state exists
   + stale assessment replay
   → stale assessment must not overwrite newer state

C. same timestamp / same generation replay
   → idempotent

D. same ticker / different generation / same semantic result
   → behavior follows explicit dedupe/version policy.
```

No production mutation.

---

# 20. Notification queue eligibility

Map the actual queue-write path.

Verify notification eligibility requires:

```text
a valid persisted state transition

not merely a model output

not merely a configured signal

not merely a repeated identical assessment.
```

Test:

```text
new material transition

duplicate same transition

no-material-change assessment

stale replay

invalid canonical candidate.
```

Expected duplicate sends/queue writes:

```text
0.
```

---

# 21. Production send firewall

M12BL must prove:

```text
notification send function is not invoked

external messaging provider is not invoked

email/push/webhook is not invoked.
```

Use mocks/spies/local harness.

Required:

```text
production_sends = 0.
```

---

# 22. Scheduler firewall

Audit scheduled monitoring entrypoints.

Required:

```text
scheduler mutation count = 0

automatic monitoring resume = 0

observed paused schedules remain paused.
```

If a local test harness simulates a scheduled call:

```text
it must not touch the real scheduler or schedule registry.
```

Do not alter cadence.

---

# 23. Transaction boundary

For the real persistence unit,
identify whether the following are atomic or intentionally separate:

```text
assessment row

warning transition

notification queue row

monitoring metadata update.
```

Construct a failure injection test.

Example:

```text
assessment insert succeeds
warning update throws
```

Expected behavior must be explicit:

```text
ROLLBACK_ALL

or

COMMIT_ASSESSMENT_AND_RETRY_DERIVED_SIDE_EFFECT
```

according to actual intended design.

Unspecified partial commit:

```text
FAIL.
```

---

# 24. Retry safety

If persistence/queue code has retries:

Verify:

```text
same idempotency identity is reused

retry cannot duplicate assessment/warning/notification

retry does not mutate semantic content

retry count bounded.
```

Do not add network retries.

This concerns persistence transaction retries only.

---

# 25. Concurrency / duplicate-run safety

Use a local deterministic concurrency fixture where feasible:

```text
same ticker
same assessment identity
two concurrent persistence attempts.
```

Required:

```text
database uniqueness or application idempotency prevents duplicate state.
```

If the repository cannot safely test true concurrency,
at least inspect uniqueness constraints and simulate duplicate insert conflict.

---

# 26. Stale generation guard

A persistence candidate should identify its generation / assessment time.

Test:

```text
new generation persisted first

older generation submitted afterward.
```

Expected:

```text
older generation cannot overwrite current warning/monitor state
unless explicitly stored as immutable historical assessment only.
```

History may be append-only.

Current state must remain monotonic by the intended ordering key.

---

# 27. Assessment date semantics

Audit timezone/date derivation.

User timezone:

```text
Asia/Seoul.
```

Do NOT assume UTC date equals Korean assessment date.

Identify actual production contract:

```text
assessment_date source

scheduler date source

market-local date rules if any

timezone conversion.
```

Do not change it unless a deterministic defect exists.

Test at least one date-boundary fixture.

---

# 28. Ticker normalization

Verify persistence identities for:

```text
Korean 6-digit codes

US ticker symbols.
```

No silent leading-zero loss.

Examples:

```text
000660

005930

CRCL

IBM.
```

Use actual normalization service.

Test duplicate aliases if the repository supports them.

---

# 29. Security / share-basis provenance

Persistence must not erase a material security-basis warning
if an assessment required ADR/ADS/share-basis qualification.

Audit whether:

```text
security basis caveat

currency caveat

per-share basis caveat
```

is preserved in the persisted summary/unknowns/evidence provenance
where the final accepted output contains it.

Do not invent fields.

---

# 30. Confidence persistence

Verify confidence mapping is explicit.

No arbitrary numeric conversion unless contract says so.

If production stores numeric confidence:

```text
document exact mapping

LOW / MEDIUM / HIGH
→ numeric values
```

and confirm it is versioned/stable.

If it stores enum/string:

```text
preserve exact accepted level.
```

---

# 31. Risk level persistence

Separate:

```text
holder stance

overall direction

risk level

warning status.
```

A high risk level must not mechanically create:

```text
SELL

REDUCE

warning
```

unless the contract explicitly requires it.

Audit actual mapping only.

---

# 32. Local ephemeral persistence harness

Preferred:

```text
temporary local database

transaction rollback fixture

repository/service layer identical to production code

all external sends mocked

all scheduler calls mocked

all provider/model calls blocked.
```

Forbidden:

```text
production connection string

production credentials

production database endpoint

real notification queue

real scheduler.
```

If no local DB backend exists,
use the repository's existing test database mechanism.

Do not substitute an unrelated fake data model
that bypasses real repositories.

---

# 33. Frozen 22-output replay

Replay all accepted M12BJ final composed outputs
through the local persistence eligibility/mapping layer.

Required:

```text
22 / 22 persistence-eligibility decisions are deterministic

0 semantic reclassification

0 field mapping enum errors

0 provenance mismatch

0 production side effect.
```

This does NOT mean 22 production writes.

Use local/ephemeral records only.

---

# 34. Replay fidelity audit

After local persistence,
read each record back and compare to the accepted source.

Report per ticker:

```text
business delta fidelity

valuation context fidelity

market expectation fidelity

new-buyer fidelity

holder fidelity

summary fidelity

unknowns fidelity

confidence fidelity

risk-level fidelity

provenance fidelity.
```

Classify:

```text
LOSSLESS

LOSSLESS_NORMALIZATION

INTENTIONAL_PRESENTATION_ONLY_DIFFERENCE

LOSSY.
```

Required proof-critical lossy count:

```text
0.
```

---

# 35. Negative fixture — historical invalid fresh proof

Select at least one of the quarantined 16 fresh candidates.

Attempt local persistence eligibility.

Expected:

```text
REJECTED_BEFORE_PERSISTENCE

reason =
canonical semantic acceptance missing/failed.
```

No warning.

No notification.

No current-state mutation.

This proves quarantine is enforceable in the integration layer.

---

# 36. Negative fixture — missing semantic receipt

Construct a structurally valid candidate
with no canonical semantic acceptance provenance.

Expected:

```text
REJECT
CANONICAL_SEMANTIC_ACCEPTANCE_REQUIRED.
```

Do not silently re-run semantics inside persistence.

Persistence should verify an authoritative receipt/state,
not become another semantic engine.

---

# 37. Negative fixture — failed final composition

Candidate:

```text
canonical semantic PASS
but final composition status FAIL.
```

Expected:

```text
not persistence eligible.
```

No partial assessment.

---

# 38. Negative fixture — core mutation

Candidate with stance-stage mutation of frozen core.

Expected:

```text
not persistence eligible.
```

No persistence.

---

# 39. Negative fixture — duplicate accepted assessment

Persist same accepted local fixture twice.

Required output:

```text
explicit idempotency behavior

duplicate assessment count according to contract

duplicate warning count = 0

duplicate queue count = 0.
```

No accidental duplicates.

---

# 40. Negative fixture — stale accepted assessment

Older valid assessment submitted after newer valid assessment.

Expected:

```text
historical append policy may retain it if intended

current state must not be downgraded by stale replay

warning lifecycle must not regress

notification must not re-fire.
```

---

# 41. Negative fixture — malformed enum mapping

Inject an unknown business-delta/stance enum
at the persistence boundary.

Expected:

```text
FAIL_CLOSED

no string passthrough

no default enum

no NO_MATERIAL_CHANGE fallback.
```

---

# 42. Negative fixture — ticker normalization

Test:

```text
"000660"

660

"005930"

5930.
```

Numeric forms must not silently collapse identifiers
if the production contract requires six-digit strings.

Expected behavior must be explicit.

---

# 43. Negative fixture — date boundary

Use a UTC timestamp near Korean midnight.

Verify the intended assessment date.

Example fixture:

```text
UTC 2026-09-13 15:30
=
Asia/Seoul 2026-09-14 00:30.
```

Do not hard-code the example if the actual contract uses a different clock source;
use it only to test the established timezone policy.

---

# 44. Warning/source evidence persistence

If warnings persist evidence refs or source identities:

Verify:

```text
only eligible current/confirmed refs are written

configured-only refs are not mislabeled fulfilled

market expectation refs are not mislabeled business-change refs

price/supply refs are not mislabeled fundamental warning refs.
```

If warnings do not persist evidence refs:

```text
document how auditability is preserved.
```

---

# 45. No post-persistence semantic derivation

Search downstream persistence / warning / notification code
for independent semantic logic.

At minimum scan for duplicated logic around:

```text
FCF

net debt

working capital

strengthened/weakened

market expectation

HOLDABLE/REVIEW/REDUCE

BUY/HOLD/SELL

configured signal fulfillment.
```

Classify hits:

```text
presentation-only

mapping-only

canonical receipt check

legacy semantic re-derivation.
```

Required:

```text
proof-critical downstream semantic re-derivation count = 0.
```

If found:

```text
STOP
POST_ACCEPTANCE_SEMANTIC_REDERIVATION_FOUND.
```

Do not patch phrase by phrase.

---

# 46. Assessment history semantics

Verify the persistence model distinguishes:

```text
immutable assessment history
```

from:

```text
current monitoring state.
```

An older historical record may remain queryable
without overwriting current state.

Document actual current architecture.

---

# 47. Warning lifecycle vs assessment history

Verify a new assessment does not automatically:

```text
close all warnings

open a warning

replace current thesis version
```

unless the specific lifecycle contract says so.

Assessment history is not itself warning state.

---

# 48. Monitoring thesis/version persistence boundary

If production persists monitored-thesis versions:

Audit:

```text
read-only assessment request
does not create a new thesis version

daily assessment
does not mutate core thesis fields unless explicitly authorized

new thesis version creation requires the intended management action.
```

Do not call monitoring registration/version mutation endpoints.

---

# 49. Historical fresh quarantine in persistence queries

If the historical invalid fresh proof is present only as local proof artifacts,
no action is needed.

If any integration test fixture or local persistence snapshot includes it:

```text
mark it non-readiness / non-production-eligible.
```

Do not delete history.

No production cleanup in this task.

---

# 50. Read path compatibility

After local persistence,
exercise the actual read path used by current review / daily monitoring.

Verify it reconstructs:

```text
business delta

market expectation

new-buyer view

holder view

facts / interpretations / unknowns

risk/confidence
```

without semantic drift.

No model call.

---

# 51. API/schema backward compatibility

If persistence or read APIs are versioned:

Audit whether the converged output shape
is compatible with the currently supported schema.

Classify any mismatch:

```text
BACKWARD_COMPATIBLE

MIGRATION_REQUIRED

BLOCKING_SCHEMA_MISMATCH.
```

Do not run a production migration.

---

# 52. Database migration review

If a migration is required to preserve proof-critical provenance or enum fidelity:

M12BL must only:

```text
design/review the migration

run it against ephemeral/local DB

prove upgrade + rollback
```

No production migration.

If no migration is required:

```text
state NO_SCHEMA_MIGRATION_REQUIRED.
```

---

# 53. Local migration rollback

If migration exists:

Test:

```text
upgrade local DB

read/write deterministic fixtures

downgrade/rollback if repository supports it

or prove forward-only migration contract.
```

No production endpoint.

---

# 54. Data-loss decision

Define proof-critical data loss as loss of:

```text
business thesis change meaning

new-buyer stance meaning

holder stance meaning

current vs prospective status where persisted

market expectation level/context

confidence/risk level if contract requires them

assessment identity/date/ticker

canonical acceptance provenance required for auditability.
```

Required:

```text
proof_critical_persistence_data_loss_count = 0.
```

---

# 55. Existing monitoring cohort safety

M12BL must not alter the 22 monitored names.

Required:

```text
monitoring_registrations = 0

monitoring_stops = 0

thesis version mutations = 0

assessment production writes = 0.
```

All replay is local/ephemeral.

---

# 56. Production credentials / secrets

Do not print or package:

```text
DB URLs

tokens

API keys

notification secrets

scheduler secrets.
```

Artifact secret scan required.

If environment variables exist:

```text
record only variable names / presence,
never values.
```

---

# 57. Readiness outcome taxonomy

Choose exactly one top-level outcome:

```text
PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_PASS

BOUNDED_PRODUCTION_INTEGRATION_REPAIR_REQUIRED

BLOCKING_PRODUCTION_PERSISTENCE_CONTRACT_GAP.
```

Use:

```text
BOUNDED_PRODUCTION_INTEGRATION_REPAIR_REQUIRED
```

for deterministic local integration defects
with a clear bounded repair.

Use:

```text
BLOCKING_PRODUCTION_PERSISTENCE_CONTRACT_GAP
```

when the required production contract is ambiguous
or would need broader schema/lifecycle redesign.

---

# 58. PASS criteria

`PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_PASS`
requires all:

```text
1. canonical acceptance is required before persistence

2. raw model output cannot bypass accepted final composition

3. 22 / 22 frozen monitored outputs map losslessly

4. Business Delta enum mapping is explicit/lossless

5. new-buyer / holder remain independent fields

6. no persistence-side semantic re-derivation

7. assessment identity is deterministic

8. duplicate replay is idempotent

9. stale replay cannot overwrite newer current state

10. transaction/partial-failure behavior is explicit and tested

11. warning lifecycle is idempotent

12. notification eligibility is transition-based and deduped

13. production send count = 0

14. scheduler mutation/resume = 0

15. invalid historical fresh output is rejected before persistence

16. missing semantic receipt is rejected

17. malformed enum fails closed

18. ticker/date normalization is explicit

19. proof-critical persisted data loss = 0

20. production DB mutation = 0.
```

---

# 59. Next scope if PASS

If PASS:

```text
next_scope =
NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE
```

But:

```text
fresh_real_proof_readiness =
READY_FOR_SEPARATELY_AUTHORIZED_PROOF
```

not:

```text
RUN_NOW.
```

Also:

```text
final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY.
```

The next task must explicitly authorize and define the fresh unseen cohort/proof.

---

# 60. Next scope if bounded repair required

If a deterministic integration defect is found:

```text
next_scope =
BOUNDED_PRODUCTION_INTEGRATION_PERSISTENCE_REPAIR_AND_LOCAL_REPLAY.
```

The repair scope must identify ONE common root cause if possible.

Do not reopen model semantics.

After repair:

```text
repeat local persistence replay
before fresh unseen proof.
```

---

# 61. Model-facing freeze

Expected in M12BL:

```text
model prompt change = 0

model schema change = 0

canonical semantic service change = 0

decision-policy change = 0

final user schema change = 0.
```

A persistence schema migration may be reviewed separately
without altering model-facing contracts.

---

# 62. No model / provider / web calls

Required:

```text
model calls = 0

provider source fetches = 0

external network calls for proof = 0.
```

All inputs are frozen local artifacts and local code.

---

# 63. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bl-scope-freeze

04-semantic-policy-proof-freeze

05-historical-fresh-quarantine-freeze

06-production-integration-entrypoint-map

07-assessment-persistence-call-graph

08-warning-lifecycle-call-graph

09-notification-queue-call-graph

10-scheduler-call-graph

11-persistence-eligibility-contract

12-canonical-acceptance-provenance-contract

13-assessment-field-mapping-matrix

14-business-delta-persistence-mapping

15-newbuyer-holder-persistence-separation

16-market-expectation-persistence-separation.
```

---

# 64. Required persistence safety artifacts

Produce:

```text
17-assessment-idempotency-contract

18-warning-idempotency-contract

19-notification-dedupe-contract

20-stale-generation-guard-contract

21-transaction-boundary-contract

22-partial-failure-behavior

23-retry-safety-audit

24-concurrency-duplicate-safety-audit

25-assessment-date-timezone-contract

26-ticker-normalization-contract

27-confidence-risk-mapping-contract

28-security-basis-provenance-audit

29-post-acceptance-semantic-rederivation-scan.
```

---

# 65. Required local replay artifacts

Produce:

```text
30-ephemeral-persistence-harness-contract

31-m12bj-22-output-persistence-eligibility-replay

32-m12bj-22-output-write-readback-fidelity

33-m12bj-22-output-provenance-fidelity

34-invalid-historical-fresh-rejection-fixture

35-missing-semantic-receipt-rejection-fixture

36-final-composition-failure-rejection-fixture

37-core-mutation-rejection-fixture

38-duplicate-assessment-replay-fixture

39-stale-assessment-replay-fixture

40-malformed-enum-rejection-fixture

41-ticker-normalization-fixture

42-assessment-date-boundary-fixture

43-warning-lifecycle-replay

44-notification-eligibility-replay

45-partial-failure-injection-replay

46-current-review-read-path-replay.
```

---

# 66. Required schema / migration artifacts

Produce:

```text
47-persistence-schema-compatibility-decision

48-proof-critical-provenance-field-coverage

49-schema-migration-requirement-decision

50-local-migration-upgrade-replay
```

Artifact 50 may be:

```text
NOT_APPLICABLE
```

if no migration is required.

If a migration exists also produce:

```text
51-local-migration-rollback-or-forward-only-proof.
```

---

# 67. Required production firewall artifacts

Produce:

```text
52-production-db-no-mutation-proof

53-monitoring-no-registration-stop-proof

54-warning-no-production-mutation-proof

55-notification-no-production-queue-write-proof

56-production-send-zero-proof

57-scheduler-pause-preservation

58-remote-push-prohibition-audit

59-main-merge-zero-proof

60-deployment-zero-proof

61-secret-scan.
```

---

# 68. Required decisions

Produce:

```text
62-production-integration-persistence-decision

63-fresh-proof-readiness-decision

64-main-merge-readiness-decision

65-production-readiness-decision

66-next-scope-decision

67-master-workflow-update

68-program-completion.
```

---

# 69. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch
final_local_head_sha

latest_result_zip_sha256
latest_result_integrity

semantic_single_source_status
real_cohort_policy_validation_status

historical_fresh_candidate_count
historical_fresh_canonical_fail_count
historical_fresh_persistence_eligible

production_assessment_entrypoint_count
production_warning_entrypoint_count
production_notification_entrypoint_count
production_scheduler_entrypoint_count

persistence_eligibility_gate_status
raw_model_persistence_bypass_count
canonical_acceptance_required

assessment_field_mapping_lossy_count
assessment_invalid_enum_mapping_count

business_delta_mapping_status
new_buyer_holder_separation_status
market_expectation_separation_status
price_supply_fundamental_separation_status

assessment_idempotency_status
warning_idempotency_status
notification_dedupe_status
stale_generation_guard_status
transaction_boundary_status
partial_failure_behavior_status
retry_safety_status
concurrency_duplicate_safety_status

assessment_date_timezone_status
ticker_normalization_status
security_basis_provenance_status
confidence_mapping_status
risk_level_mapping_status

post_acceptance_semantic_rederivation_count

m12bj_fixture_count
m12bj_persistence_eligible_count
m12bj_write_readback_lossy_count
m12bj_provenance_mismatch_count

historical_fresh_rejection_fixture_status
missing_semantic_receipt_fixture_status
final_composition_failure_fixture_status
core_mutation_fixture_status
duplicate_replay_fixture_status
stale_replay_fixture_status
malformed_enum_fixture_status
ticker_normalization_fixture_status
date_boundary_fixture_status
warning_lifecycle_fixture_status
notification_eligibility_fixture_status
partial_failure_fixture_status
current_review_readback_fixture_status

schema_compatibility_status
schema_migration_required
proof_critical_persistence_data_loss_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
canonical_semantic_service_change_count
decision_policy_change_count
final_user_schema_change_count

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
observed_paused_schedule_count

top_level_integration_result

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

Anything unmeasured:

```text
NOT_MEASURED.
```

---

# 70. Expected clean outcome

If production integration is structurally clean:

```text
top_level_integration_result =
PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_PASS

raw_model_persistence_bypass_count = 0

canonical_acceptance_required = true

m12bj_fixture_count = 22

m12bj_persistence_eligible_count = 22

m12bj_write_readback_lossy_count = 0

m12bj_provenance_mismatch_count = 0

historical_fresh_persistence_eligible = false

proof_critical_persistence_data_loss_count = 0

post_acceptance_semantic_rederivation_count = 0

production_db_mutations = 0

warning_mutations = 0

notification_queue_writes = 0

production_sends = 0

scheduler_mutation_count = 0

automatic_monitoring_resume = 0

fresh_real_proof_readiness =
READY_FOR_SEPARATELY_AUTHORIZED_PROOF

final_main_merge_readiness =
NOT_READY

production_readiness =
NOT_READY

next_scope =
NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE.
```

Do NOT force this expected result.

---

# 71. Failure handling

## A. Raw model output can persist directly

```text
STOP
RAW_MODEL_OUTPUT_PERSISTENCE_BYPASS.
```

Next:

```text
BOUNDED_PRODUCTION_INTEGRATION_PERSISTENCE_REPAIR_AND_LOCAL_REPLAY.
```

## B. Canonical acceptance receipt/provenance is not enforceable

If persistence cannot distinguish:

```text
canonically accepted
vs
unvalidated candidate
```

then:

```text
BLOCKING_PRODUCTION_PERSISTENCE_CONTRACT_GAP.
```

Do not run fresh proof.

## C. Historical invalid fresh candidate remains persistence eligible

```text
STOP
QUARANTINED_FRESH_PROOF_PERSISTENCE_BYPASS.
```

## D. Enum mapping is lossy

```text
STOP
PERSISTENCE_ENUM_MAPPING_LOSS.
```

No model change.

## E. Duplicate replay creates duplicate warning/notification

```text
STOP
PERSISTENCE_IDEMPOTENCY_FAILURE.
```

## F. Stale replay overwrites newer current state

```text
STOP
STALE_ASSESSMENT_OVERWRITE_FAILURE.
```

## G. Partial failure leaves undefined inconsistent state

```text
STOP
PERSISTENCE_TRANSACTION_CONTRACT_GAP.
```

## H. Production side effect occurs

```text
STOP
PRODUCTION_FIREWALL_VIOLATION.
```

## I. All integration contracts pass

Proceed only to:

```text
NEW_FRESH_UNSEEN_PROOF_ON_CANONICAL_INTEGRATED_PIPELINE
```

as a separately authorized task.

---

# 72. Local-only / production firewall

M12BL is LOCAL-ONLY.

Required:

```text
production DB mutations = 0

monitoring registrations = 0

monitoring stops = 0

assessment production writes = 0

warning production mutations = 0

notification production queue writes = 0

production sends = 0

provider source fetches = 0

model calls = 0

remote pushes = 0

raw model artifact pushes = 0

main branch mutations = 0

main merges = 0

deployments = 0

scheduler mutations = 0

automatic monitoring resume = 0.
```

Monitoring schedules remain paused.

---

# 73. Artifact integrity

Freeze all local artifacts before final artifact index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Report final ZIP SHA-256.

Do not push raw artifacts remotely.

---

# 74. Final task principle

The system has already completed:

```text
semantic convergence

full monitored compatibility proof

real-cohort policy validation.
```

M12BL must not repeat those tasks.

The remaining question is operational correctness:

```text
Can an already-valid decision be persisted,
read back,
deduped,
versioned,
and translated into warning/notification state
without losing semantics or causing side effects?
```

The correct flow is:

```text
map the real production persistence call graph

→ require canonical acceptance before persistence

→ verify field/enum/provenance fidelity

→ verify idempotency + stale protection + transaction behavior

→ replay the 22 frozen monitored outputs locally

→ prove invalid historical fresh outputs are rejected

→ prove warning/notification paths are fail-closed and deduped

→ preserve paused schedules and zero production side effects

→ if clean:
   authorize only a SEPARATE fresh unseen proof task

→ if not clean:
   define the smallest bounded persistence/integration repair.
```

Do NOT:

```text
reopen semantic contracts

reopen policy contracts

rerun the monitored shadow

run fresh issuers

call models

call providers

persist production assessments

mutate warnings

queue notifications

send messages

resume schedules

merge main

deploy.
```
