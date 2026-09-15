# Thesis Monitor — Runtime Namespace Isolation Repair & Fresh Holdout Ownership Proof

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-runtime-namespace-isolation-repair-and-fresh-holdout-proof.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-runtime-namespace-isolation-repair-fresh-holdout-proof-report.zip
```

This is a **bounded model-context runtime-namespace isolation repair + fresh unseen holdout ownership-proof task**.

The current blocker is NOT:

- source configuration;
- US/KR source coverage;
- prompt/schema identity;
- model output schema;
- Directional Core ownership semantics;
- Price-Timing ownership semantics;
- renderer ownership;
- timeout/capacity;
- WebSocket disconnect.

The latest task stopped because the actual execution violated its own frozen isolation contract:

```text
precommit:
one isolated signed-in Codex CLI subprocess,
temporary working directory and runtime-state namespace
per model context

actual:
FIRST:DIRECTIONAL_CORE:01 namespace =
8b84826c3fc02f4ee5d968ba

FIRST:DIRECTIONAL_CORE:02 namespace =
8b84826c3fc02f4ee5d968ba
```

Batch 02 therefore correctly failed the runtime isolation gate, even though:

```text
transport = PASS
exit_code = 0
schema = valid
prompt/schema/receipt identity = PASS
session_id itself was unique
```

The current task must repair **runtime-state namespace allocation/isolation**, not investment semantics.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-existing-source-env-binding-fresh-holdout-proof-resume-report.zip
```

Verified SHA-256:

```text
1863c83cc54b3c07a4a74f89ba0d46634836334df7bed3d46cc819132f025474
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest bundle artifact integrity independently verified:

```text
zip_member_count = 1072
indexed_payload_count = 1071
missing indexed files = 0
hash mismatch = 0
size mismatch = 0
```

The index intentionally excludes only:

```text
artifact-index.json
```

---

# 2. What the latest task successfully fixed

The existing protected source configuration binding is now working.

Latest measured state:

```text
protected_source_config_located = true
protected_source_config_bound = true

OPENDART_API_KEY present = true
SEC_USER_AGENT present = true
secret_values_emitted = 0

source_configuration_preflight_status = PASS
US_SOURCE_CONFIG_SMOKE = PASS
KR_SOURCE_CONFIG_SMOKE = PASS

US source target = PASS
KR source target = PASS
```

Fresh source generation created:

```text
20260907-fresh-issuer-source-20260907T152751Z-3f4af1225c1c
```

Fresh source lock:

```text
74dbadf1f826891e45ee86d47d8071d5a6deb512f1f06e89b397011ac478af92
```

Do not reopen the environment-binding task unless current repository evidence directly contradicts it.

---

# 3. Exact latest execution result

The latest fresh holdout cohort was:

```text
ACHR
BNED
CROX
AWX
095720
000250
389030
009310
042700
002690
103590
025750
084680
377330
024840
360070
```

Market mix:

```text
US = 4
KR = 12
```

FIRST attempted two Directional Core contexts.

## 3.1 Batch 01

```text
subjects =
ACHR / BNED / CROX / AWX

transport = PASS
exit_code = 0
schema validation = PASS
receipt identity = PASS
partial semantic audit = PASS

runtime_state_namespace_hash =
8b84826c3fc02f4ee5d968ba

runtime_state_namespace_unique = true
session_id =
01a07ccf-7b4e-79d1-9d64-23622c7d62e7

session_identity_unique = true
```

## 3.2 Batch 02

```text
subjects =
095720 / 000250 / 389030 / 009310

transport = PASS
exit_code = 0
schema = valid
receipt identity = PASS

runtime_state_namespace_hash =
8b84826c3fc02f4ee5d968ba

runtime_state_namespace_unique = false

session_id =
01a07cd3-e2d4-77c3-9157-809b8bcff297

session_identity_unique = true

passive classification =
IDENTITY_INVALID_RESULT
```

The raw batch02 output itself validates against its exact bundled schema with:

```text
schema_errors = 0
candidate_count = 4
packet_id matches runtime generation
ticker order matches expected batch
```

Therefore the model output was not rejected because of investment-content schema failure.

The gate failed because runtime-state namespace reuse violated the frozen per-context isolation policy.

---

# 4. Correct failure classification

The latest completion currently reports:

```text
semantic_revelation_state =
REVEALED_FOR_ARCHITECTURE_TUNING

retirement_state =
RETIRED_FOR_ARCHITECTURE_REPAIR

next_scope =
GENERIC_OWNERSHIP_ARCHITECTURE_REPAIR
```

This task must independently audit that classification.

Based on the preserved evidence, the expected correct classification is:

```text
execution failure class =
RUNTIME_NAMESPACE_ISOLATION_CONTRACT_VIOLATION

investment ownership semantic defect =
NOT_MEASURED

semantic_revelation_state =
NOT_MEASURED_RUNTIME_ISOLATION_FAILURE

retirement_state =
RETIRED_PARTIAL_EXPOSURE

future_unseen_reuse_allowed =
0
```

Do not modify historical artifacts in place.

Produce a new correction/audit artifact explaining the distinction.

If current code inspection proves that namespace reuse was intentionally allowed by a newer authoritative runtime contract that superseded the frozen precommit:

```text
STOP
CONTRACT_CONFLICT_REQUIRES_REVIEW
```

Do not silently reinterpret history.

---

# 5. Existing cohort is consumed for unseen-proof purposes

The latest cohort produced usable real model output for eight issuers.

Therefore:

```text
holdout_output_exposure_state =
PARTIALLY_EXPOSED

future_unseen_reuse_allowed =
0
```

The entire 16-issuer cohort must be added to the future unseen exclusion registry.

Do not:

```text
rerun FIRST on the same 16
continue only the remaining eight
rerun batch02 after the repair
continue from batch03
```

The preserved outputs may be used for offline forensic/audit only.

---

# 6. Goal

The task must perform:

```text
1. audit runtime namespace construction
2. confirm why different contexts received the same namespace
3. repair namespace allocation generically
4. prove per-context namespace isolation model-free
5. prove no transport/model/prompt/schema semantic drift
6. retire the partially exposed cohort correctly
7. build a completely fresh unseen US4 + KR12 cohort
8. create a fresh source generation/source lock
9. execute FIRST → A → B → C
10. stop at the first hard failure
11. preserve every successful context immediately
```

Do not create another preparation-only task after the namespace repair if the model-free proof passes.

Proceed to the fresh real proof in the same task.

---

# 7. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Latest result reported:

```text
base_sha =
be78b8e0a40b2e63d3522487a1482b47b6efe271

work_instruction_commit =
12c482b7971dac2532d93912b6c51ed323df88ea

implementation_commit =
0ef6c9ea9a82d1a761701b5ee91cc81a15530bd4
```

The latest result contains more than one reported final-head value in different generated summaries.

Do not guess which one is current.

Use the actual repository state and explicitly report:

```text
current_head
current_tree
worktree status
historical final-head discrepancy
```

If unexplained semantic changes affect investment/source/model semantics:

```text
STOP
UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT
```

---

# 8. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then modify the bounded runtime namespace allocation / gate surface.

---

# 9. Allowed mutation surface

Allowed:

```text
model-context runtime-state namespace allocation
temporary working-directory allocation
context-isolation identity generation
runtime isolation validator
runtime lifecycle classification
tests for the above
reporting of runtime isolation state
historical failure reclassification report
experiment-only proof orchestration
```

Strong preference:

```text
one unique runtime state root per model context
derived deterministically or securely from invocation identity
```

The repair must remain generic.

No ticker/run-specific exception.

---

# 10. Forbidden mutation surface

Do not change:

```text
Directional Core semantics
Price-Timing semantics
composer semantics
renderer/action ownership

source-sufficiency semantics
price-context contract

DecisionEvidencePacket meaning

prompt semantics
schema semantics

model = gpt-5.6-sol
reasoning effort = xhigh

MODEL_CONTEXT_COUPLED grouping
subjects per context = 4

timeout = 1800 seconds
timeout owner count = 1

ContinuationTransportAdapter canonical request semantics
stdin/stdout/stderr collection topology
process-group cleanup semantics
```

Do not:

```text
change model
increase timeout
add wrapper retry
split four-subject contexts
add paid data provider
auto-resume scheduled monitoring
```

---

# 11. Runtime namespace root-cause audit

Before patching, identify:

```text
where runtime_state_namespace_hash is generated
where runtime state directory/path is allocated
where working directory is allocated
what values are included in namespace derivation

whether generation_id only is used
whether invocation_id is omitted
whether batch/run/stage are omitted

whether a cached/shared path is reused
whether temp directory lifecycle is scoped per generation instead of per context
```

Compare:

```text
FIRST:DIRECTIONAL_CORE:01
FIRST:DIRECTIONAL_CORE:02
```

Required root-cause result:

```text
RUNTIME_NAMESPACE_ISOLATION_ROOT_CAUSE_CONFIRMED
```

or:

```text
RUNTIME_NAMESPACE_ISOLATION_ROOT_CAUSE_NOT_CONFIRMED
```

If not confirmed:

```text
STOP
```

No speculative patch.

---

# 12. Correct namespace contract

The frozen contract is:

```text
one isolated signed-in Codex CLI subprocess
+
one temporary working directory
+
one runtime-state namespace
per model context
```

Therefore, for any two different invocation IDs:

```text
runtime_state_namespace_hash(A)
!=
runtime_state_namespace_hash(B)
```

Required across:

```text
different batch
different stage
different run
fresh vs resumed execution
```

A namespace may not be reused merely because:

```text
generation_id is the same
source lock is the same
same 16 issuers are reused across FIRST/A/B/C
```

The model context is the isolation unit.

---

# 13. Session identity and namespace identity are separate

Do not conflate:

```text
Codex session_id
runtime-state namespace
working directory
invocation_id
generation_id
```

Each has a different role.

A unique session ID does not make namespace reuse valid.

A shared generation ID does not authorize namespace reuse.

The lifecycle output should report independently:

```text
session_identity_unique
runtime_state_namespace_unique
working_directory_unique
```

Do not collapse them into a misleading single field such as:

```text
session_identity_valid
```

unless that field's exact composite semantics are documented.

Prefer explicit:

```text
execution_isolation_valid
```

with component checks.

---

# 14. Model-free isolation regression

Before any real model call, test the actual execution-path allocation for the full proof shape.

Generate model-free contexts for:

```text
FIRST Directional Core batch 01-04
FIRST Price-Timing batch 01-04

A Directional Core batch 01-04
A Price-Timing batch 01-04

B Directional Core batch 01-04
B Price-Timing batch 01-04

C Directional Core batch 01-04
C Price-Timing batch 01-04
```

Total:

```text
32 planned model contexts
```

Required:

```text
32 invocation IDs
32 unique runtime-state namespace hashes
32 unique temporary context working directories
```

If session IDs cannot exist without model spawn:

```text
session uniqueness = NOT_MEASURED_PRESPAWN
```

Do not fabricate them.

Also test resumed-generation path if the production experiment code supports resume.

No model call in this phase.

Required:

```text
FULL_PATH_NAMESPACE_ISOLATION_PREFLIGHT = PASS
```

---

# 15. Negative regression tests

Add tests proving:

```text
same generation + different batch
→ different namespace

same generation + different stage
→ different namespace

same generation + different run
→ different namespace

different invocation IDs
→ different context work dirs

reused namespace
→ gate FAIL before next context
```

Also prove namespace uniqueness does not mutate:

```text
prompt bytes
schema bytes
packet bytes
model
effort
timeout
```

---

# 16. Historical batch02 offline audit

Do not call the model.

Use the exact preserved batch02 raw output and exact bundled schema.

Verify:

```text
schema validation
packet_id
subject order
receipt identity
prompt/schema hash
```

Run the applicable Directional Core ownership audit offline if the canonical validator can do so without altering historical artifacts.

Report:

```text
historical_batch02_output_schema_status
historical_batch02_identity_status
historical_batch02_directional_semantic_audit_status
```

Even if it passes:

```text
do not count it as valid unseen proof
```

because the execution isolation contract was violated.

This audit exists only to distinguish:

```text
investment semantic defect
from
runtime isolation defect
```

---

# 17. Corrected historical state artifact

Produce a machine-readable reclassification artifact containing:

```text
historical_latest_status
historical_latest_stop_reason

confirmed_runtime_isolation_violation

usable_real_output_count = 8
exposure_state = PARTIALLY_EXPOSED

semantic_defect_confirmed =
0 / 1 / NOT_MEASURED

semantic_revelation_state

retirement_state

future_unseen_reuse_allowed = 0

correct_next_scope
```

Expected, if no semantic defect is confirmed offline:

```text
semantic_revelation_state =
NOT_MEASURED_RUNTIME_ISOLATION_FAILURE

retirement_state =
RETIRED_PARTIAL_EXPOSURE

correct_next_scope =
RUNTIME_NAMESPACE_ISOLATION_REPAIR_THEN_FRESH_HOLDOUT_PROOF
```

---

# 18. Extend prior-real-issuer exclusion registry

Add all 16 issuers from the latest partially exposed cohort:

```text
ACHR
BNED
CROX
AWX
095720
000250
389030
009310
042700
002690
103590
025750
084680
377330
024840
360070
```

to the future unseen exclusion registry.

Do not remove older exclusions.

Record:

```text
previous_exclusion_registry_hash
new_exclusion_registry_hash
newly_retired_issuer_count = 16
```

---

# 19. Existing source configuration remains bound

Before fresh candidate preparation, perform only a lightweight secret-safe preflight:

```text
OPENDART_API_KEY present
SEC_USER_AGENT present
canonical loader identity unchanged
secret values emitted = 0
```

Do not repeat the previous environment-debug project.

If configuration is unexpectedly absent again:

```text
STOP before candidate loop
```

No dozens of failed source requests.

---

# 20. Existing monitoring schedules remain paused

The user explicitly requested the existing US/KR scheduled monitoring remain paused.

Observe the approved monitoring schedule paths before proof execution.

If already paused:

```text
scheduler mutation = 0
```

If one approved path unexpectedly resumed:

```text
pause only that approved path
record actual mutation count
```

Do not alter unrelated schedules.

Do not automatically resume monitoring after success.

---

# 21. Fresh unseen cohort selection

After namespace isolation preflight PASS:

Create a completely fresh unseen cohort:

```text
US = 4
KR = 12
```

using:

```text
existing free-data routes
current canonical security/issuer universe
updated prior-real-issuer exclusion registry
deterministic outcome-independent selection
precommitted reserve order
```

Do not reuse any issuer with prior real-model exposure.

Do not use the latest 16 as reserves.

If one market cannot meet its source target:

```text
finish the other market's bounded diagnostic
STOP pre-model
```

Do not lower source standards.

---

# 22. Fresh source generation and lock

After both markets pass:

Create:

```text
new source generation
new ordered issuer manifest
per-issuer packet hashes
source identity audit
source sufficiency audit
new aggregate source lock
```

Do not reuse:

```text
74dbadf1f826891e45ee86d47d8071d5a6deb512f1f06e89b397011ac478af92
```

That source lock belongs to the partially exposed retired cohort.

---

# 23. Fresh proof precommit

Before first real model call, freeze:

```text
ordered 16 issuers
context grouping

source generation
source lock
packet hashes

prompt/schema semantic identities

model
reasoning effort
timeout
timeout owner

namespace isolation implementation identity
namespace policy

schedule pause observation

hard gates
artifact preservation rules
failure rules
```

Required namespace policy:

```text
PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE
```

No cohort/source mutation after precommit.

---

# 24. FIRST/A/B/C execution

Run:

```text
FIRST
→ gates
→ A
→ gates
→ B
→ gates
→ C
→ gates
```

At the first execution/semantic/renderer/hard-safety failure:

```text
STOP
```

No later run.

No automatic retry.

No selective continuation.

No same-cohort hotfix.

---

# 25. Runtime isolation assertion before every model spawn

Immediately before each model spawn:

```text
assert invocation_id not previously used
assert runtime namespace hash not previously used
assert context working directory not previously used
```

If any collision occurs:

```text
STOP BEFORE SPAWN
RUNTIME_NAMESPACE_COLLISION
```

Do not expose the next real context.

Preserve collision evidence.

---

# 26. Per-context evidence preservation

After each successful real context:

```text
raw output
stdout
stderr/log
transport receipt
prompt
schema
context manifest
runtime namespace identity
working-directory identity
session identity if observable
```

Hash and secret-scan immediately.

Do not wait for full FIRST.

---

# 27. Directional Core early semantic gate

After each successful Directional Core context:

```text
schema valid

DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
```

If hard semantic defect confirmed:

```text
STOP
RETIRED_FOR_ARCHITECTURE_REPAIR
```

Do not tune against that cohort.

---

# 28. Run-level hard gates

For each complete run:

```text
ownership = PASS
renderer = PASS
hard safety = PASS
```

before next run.

Keep message-quality advisory separate.

Do not hide advisory FAIL.

Do not turn it into a hard gate unless the frozen acceptance contract says so.

---

# 29. Runtime failure rules

## Explicit capacity

```text
STOP
no model substitution
no wrapper retry
```

## WebSocket disconnect

Preserve exact lifecycle.

If recovered:

```text
record observed recovery
```

If watchdog timeout follows:

```text
STOP
```

## Silent timeout

```text
STOP
no timeout increase
```

## Namespace collision

```text
STOP before spawn
```

No automatic cohort replacement within the same run after real exposure.

---

# 30. Stability/generalization

Use only completed runs that passed all required run-level hard gates.

Report separately:

```text
Directional Core stability
Price-Timing stability
ownership generalization
renderer ownership
hard safety
message quality advisory
runtime reliability observations
```

Do not merge these into one binary score.

Do not hide 0.5-point boundary crossings.

---

# 31. Production no-change

Other than maintaining the already-approved pause:

```text
production DB mutation = 0
production send = 0
monitoring registration change = 0
live V2 activation/change = 0
Night Futures change = 0
automatic monitoring resume = 0
```

---

# 32. Monitoring Bootstrap remains out of scope

Only after full proof success:

```text
next_scope =
Monitoring Bootstrap Integration Review
```

Do not start it here.

Monitoring remains paused until separately authorized.

---

# 33. Required artifacts — isolation repair

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-latest-runtime-isolation-failure-reconstruction
04-runtime-namespace-root-cause
05-runtime-namespace-contract
06-runtime-namespace-repair-diff
07-runtime-namespace-regression-tests
08-full-path-32-context-namespace-preflight
09-historical-batch02-offline-audit
10-historical-failure-reclassification
11-updated-real-issuer-exclusion-registry
12-source-config-presence-preflight
13-schedule-pause-observation
```

---

# 34. Required artifacts — fresh proof preparation

If isolation preflight passes:

```text
14-fresh-selection-policy
15-us-candidate-source-readiness
16-kr-candidate-source-readiness
17-dual-market-source-decision
18-fresh-holdout-selection
19-fresh-source-generation
20-source-identity-audit
21-source-sufficiency-audit
22-fresh-source-lock
23-fresh-proof-precommit
24-investment-semantic-freeze
25-transport-and-isolation-freeze
```

---

# 35. Required execution artifacts

For FIRST/A/B/C, preserve:

```text
execution summary
context artifact manifest
namespace/session/working-dir identity manifest
per-context partial semantic audits
ownership gate
renderer gate
hard-safety gate
message-quality advisory
```

If execution stops:

```text
later runs = NOT_RUN
unmeasured gates = NOT_MEASURED
```

Do not encode unmeasured results as zero-valued PASS-like fields.

---

# 36. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

historical_runtime_namespace_policy
historical_distinct_context_count
historical_distinct_namespace_count

runtime_namespace_root_cause
runtime_namespace_repair_applied
ticker_specific_runtime_exception_count

namespace_preflight_planned_context_count
namespace_preflight_unique_invocation_count
namespace_preflight_unique_namespace_count
namespace_preflight_unique_workdir_count
namespace_preflight_status

historical_batch02_schema_status
historical_batch02_identity_status
historical_batch02_offline_semantic_status

historical_failure_reclassification
historical_exposure_state
historical_semantic_revelation_state
historical_retirement_state

previous_exclusion_registry_count
new_exclusion_registry_count
newly_retired_issuer_count

source_config_present
secret_values_emitted

fresh_us_target_status
fresh_kr_target_status

fresh_cohort
fresh_source_generation
fresh_source_lock

model
reasoning_effort
batch_semantics
subjects_per_context
timeout
timeout_owner_count

planned_real_contexts
attempted_real_contexts
successful_real_contexts
failed_real_contexts

distinct_real_invocation_count
distinct_real_namespace_count
distinct_real_workdir_count
distinct_real_session_count

namespace_collision_count

raw_output_document_count
unique_issuer_output_count

wrapper_retry_count
cli_retry_signal_count
disconnect_count
capacity_failure_count
timeout_count
orphan_count

run_results.first
run_results.a
run_results.b
run_results.c

first_ownership_gate
first_renderer_gate
first_hard_safety_gate
first_message_quality

run_a_ownership_gate
run_a_renderer_gate
run_a_hard_safety_gate
run_a_message_quality

run_b_ownership_gate
run_b_renderer_gate
run_b_hard_safety_gate
run_b_message_quality

run_c_ownership_gate
run_c_renderer_gate
run_c_hard_safety_gate
run_c_message_quality

core_stability
timing_stability
ownership_generalization
runtime_reliability_observation

exposure_state
semantic_revelation_state
retirement_state
future_unseen_reuse_allowed

observed_paused_schedule_count
approved_pause_scheduler_mutation_count
automatic_monitoring_resume

production_db_mutation
production_send
monitoring_registration_change
live_v2_change
night_futures_change

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

status
readiness
stop_reason
next_scope
```

Anything not measured:

```text
NOT_MEASURED
```

---

# 37. Artifact integrity

Create artifact index only after final completion artifacts are frozen.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

---

# 38. Decision matrix

## A. Runtime namespace root cause not confirmed

Stop.

No new real model calls.

## B. Root cause confirmed but full-path 32-context isolation preflight fails

Stop.

No new real model calls.

## C. Isolation passes but source targets fail

Finish both market diagnostics.

Stop pre-model.

## D. Fresh real proof hits runtime namespace collision

Stop before spawn.

No exposure from the colliding context.

## E. Fresh real proof hits semantic defect

Stop after preserving output.

Retire for architecture repair.

## F. Fresh real proof hits transport/capacity/timeout failure

Stop after preserving evidence.

Do not auto-retry or switch model.

## G. FIRST/A/B/C all complete with required hard gates and formal stability/generalization

Then:

```text
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW
```

Monitoring remains paused until separately authorized.

---

# 39. Final task principle

The latest task finally reached real model execution.

The model returned two valid Directional Core documents.

The source and secret binding worked.

The failure occurred because the executor reused a runtime-state namespace even though the frozen precommit required one namespace per model context.

Therefore the correct next move is:

```text
repair model-context isolation
→ prove 32-context uniqueness without model calls
→ retire the exposed cohort
→ select a fresh unseen cohort
→ execute the real proof
```

Not:

```text
change investment logic
```

Not:

```text
lower ownership gates
```

Not:

```text
continue the exposed cohort
```

Not:

```text
change model or timeout
```

And not:

```text
create another preparation-only project after the isolation preflight passes
```

Once the namespace repair is proven, proceed directly to the fresh real ownership proof in the same task.
