# Thesis Monitor — Pre-Spawn Live-Workload Guard Compatibility & Holdout Proof Resume

## 0. Task identity

Suggested work-instruction filename:

```text
20260907-prespawn-live-workload-guard-compatibility-and-holdout-proof-resume.md
```

Suggested result bundle:

```text
thesis-monitor-20260907-prespawn-live-workload-guard-compatibility-holdout-proof-resume-report.zip
```

This is a **bounded pre-spawn coexistence-guard compatibility repair + frozen unseen-holdout proof resume task**.

The current blocker is NOT:

- source sufficiency;
- US/KR cohort selection;
- Directional Core;
- Price-Timing;
- renderer ownership;
- model timeout;
- ContinuationTransportAdapter;
- model transport process cleanup.

The confirmed blocker is:

```text
LiveWorkloadGuard
→ pre-spawn process census using `ps`
→ sandbox PermissionError
→ model process never spawned
→ no transport receipt exists
→ context-preservation layer masks original exception as transport_receipt_missing
```

The repair must address only:

1. sandbox-compatible live-workload observation;
2. correct pre-spawn exception provenance;
3. correct receipt lifecycle semantics when spawn never occurred.

Only after model-free guard preflight and freeze/reuse gates PASS may the same still-unexposed holdout resume.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260907-us-price-context-gate-supported-universe-remediation-holdout-proof-resume-report(1).zip
```

Verified local ZIP SHA-256:

```text
fd519905d0201d5742d1c1b90c9b3e15b681020d05ad23a4031734a98eb73c68
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

The latest bundle contains:

```text
artifact_count = 200
artifact_hash_mismatch_count = 0
artifact_size_mismatch_count = 0
artifact_secret_scan_failure_count = 0
```

Latest repository/result provenance:

```text
base_sha =
58f7505ea417dd7d7b7a8378655af850e0c13f9f

work_instruction_commit =
56445bb8d3212320eb4d34defdfaae65dcea986f

implementation_commit =
5514d366441a734c562aa0b5e9cf5b47fabda11d

final_head_sha =
30d42e75c850ed20e63c632db78b517307efbe80

branch =
codex/20260907-us-price-context-gate-supported-universe-remediation-holdout-proof-resume
```

Do not assume current HEAD remains identical.

---

# 2. Source/readiness work is now complete for this holdout

The previous task established:

```text
US_SOURCE_TARGET_STATUS = PASS
KR historical target status = PASS

fresh combined source generation =
20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a

fresh combined source lock =
d4bd0b51d9cc543ebe03088047cce375db41d3d9a9f21c07d4fd5646bdf9b1ef

source identity = PASS
source sufficiency = PASS
holdout unseen gate = PASS
```

Final ordered cohort:

```text
NVDA
JPM
WMT
BRK-B
142210
060900
002680
035420
216050
100700
001530
487580
038870
342870
060230
415380
```

Market mix:

```text
US = 4
KR = 12
```

Frozen context grouping:

```text
[
  [NVDA, JPM, WMT, BRK-B],
  [142210, 060900, 002680, 035420],
  [216050, 100700, 001530, 487580],
  [038870, 342870, 060230, 415380]
]
```

Do not repeat US/KR source-remediation work in this task.

---

# 3. Price-context gate remediation is also closed

The latest result established:

```text
price_context_gate_classification =
IMPLEMENTATION_OVERCOUPLING

price_context_gate_repair_applied = 1
source_sufficiency_policy_changed = 0
```

Canonical contract now explicitly distinguishes:

```text
Directional Core fundamental source sufficiency
from
Price-Timing price/technical readiness
```

The result confirmed:

```text
DecisionEvidencePacket does not require current price
Directional Core does not require safe technical context
price/technical inputs are conditional

safe absent price
→ explicit UNAVAILABLE_SAFE timing path

future/malformed price
→ still blocked
```

No price is fabricated.

No technical claim is permitted when technical context is unavailable.

WMT and BRK-B may therefore be Directional-ready with:

```text
price_timing_input_readiness = UNAVAILABLE_SAFE
```

Do not reopen this contract in the current task.

---

# 4. Exact current failure

The confirmed forensic result is:

```text
root_cause =
LIVE_WORKLOAD_GUARD_PS_PERMISSION_DENIED

root_exception =
PermissionError: [Errno 1] Operation not permitted: 'ps'

failed_operation =
LiveWorkloadGuard._active_natural_job_count /
LiveWorkloadGuard._running_model_process_count

failure_stage =
PRE_SPAWN

model_invocation_count = 0
real_holdout_subject_output_count = 0
transport_receipt_created = 0

retry_count = 0
mid_run_hotfix_count = 0

exception_masked_by_context_preservation = true
```

The surface error was incorrectly reported as:

```text
ValueError:
transport_receipt_missing:
20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a:first:DIRECTIONAL_CORE:01
```

The model never started.

Therefore:

```text
transport_receipt_missing
```

was a downstream symptom, not the root cause.

---

# 5. Current holdout integrity

Because no real model process was spawned:

```text
real_holdout_model_invocation_count = 0
real_holdout_subject_output_count = 0

holdout_output_exposure_state =
UNEXPOSED

holdout_semantic_revelation_state =
NOT_MEASURED

holdout_retirement_state =
ACTIVE_UNEXPOSED

future_unseen_holdout_reuse_allowed =
1
```

This holdout remains reusable if and only if the current task proves that:

```text
source lock unchanged
ordered cohort unchanged
packet hashes unchanged
prompt/schema semantic inputs unchanged
model/effort unchanged
context grouping unchanged
investment architecture unchanged
only bounded pre-spawn guard / error-provenance implementation changed
```

Do not select a new issuer cohort.

---

# 6. Goal

Perform:

```text
root-cause code-path audit
→ sandbox-compatible coexistence-observation repair
→ pre-spawn exception-provenance repair
→ receipt-lifecycle repair
→ model-free exact-path preflight
→ semantic/freeze/reuse verification
→ same unseen holdout FIRST
→ per-context preservation + early semantic gates
→ FIRST run gates
→ A/B/C if clean
```

Do not tune the investment model.

---

# 7. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Compare current state with the latest known result.

If unexplained semantic drift affects:

```text
Directional Core
Price-Timing
renderer/action ownership
source/evidence inputs
DecisionEvidencePacket
prompt/schema
model/context grouping
ContinuationTransportAdapter canonical semantics
timeout ownership
```

then:

```text
STOP
UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT
```

Do not reset, merge, cherry-pick, or silently discard unrelated work.

---

# 8. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then modify the bounded guard/error-handling surface.

---

# 9. Allowed mutation surface

Allowed:

```text
LiveWorkloadGuard observation implementation
experiment-only GuardedTransportAdapter coexistence wrapper
pre-spawn guard result/receipt state model
context-preservation exception propagation
model-free guard preflight
tests/fixtures for these paths
result/report serialization
```

Allowed hash drift should be explicitly classified as:

```text
AUTHORIZED_GUARD_COMPATIBILITY_HASH_DRIFT
```

The task may change a guard/wrapper file hash without treating that alone as investment or canonical transport semantic drift.

---

# 10. Forbidden mutation surface

Do not change:

```text
Directional Core semantics
Price-Timing semantics
composer semantics
renderer ownership

source sufficiency
price-context gate contract
DecisionEvidencePacket meaning

prompt semantics
schema semantics

model = gpt-5.6-sol
reasoning effort = xhigh

batch semantics = MODEL_CONTEXT_COUPLED
context size = 4

timeout = 1800 seconds
timeout owner count = 1

ContinuationTransportAdapter canonical API
instrumented Codex subprocess lifecycle
stdin/stdout/stderr topology
process-group cleanup semantics

production scheduler
production DB
production Telegram
monitoring registration
live V2/Structured Autonomy
Night Futures
```

Do not add automatic retry.

Do not split batches.

---

# 11. Phase A — Exact guard code-path audit

Before changing code, document:

```text
where LiveWorkloadGuard is constructed
where PRE_SPAWN coexistence checks run

exact command used for process observation
exact call path to `ps`

which decisions depend on:
- active natural job count
- running model process count

whether protected time-window checks are independent
whether scheduler/job registry signals already exist
whether a lock/process registry already exists

when transport spawn is considered to have begun
when a transport receipt becomes expected

where context-preservation catches/replaces exceptions
```

Required root-cause result:

```text
PRESPAWN_GUARD_ROOT_CAUSE_CONFIRMED
```

or:

```text
PRESPAWN_GUARD_ROOT_CAUSE_NOT_CONFIRMED
```

If not confirmed:

```text
STOP
```

No speculative repair.

---

# 12. Sandbox-compatible workload observation rule

The repair must preserve the semantic purpose of the guard.

The prohibited shortcut is:

```text
ps unavailable
→ assume active_natural_job_count = 0
→ assume running_model_process_count = 0
→ spawn model
```

This is NOT allowed.

Likewise, do not simply catch:

```text
PermissionError
```

and continue fail-open.

## 12.1 Preferred observation source

First inspect whether the repository/environment already provides a sandbox-compatible authoritative or bounded signal such as:

```text
scheduler/job registry
natural-run state store
shared execution lock
experiment/model invocation registry
provider/runtime status registry
other existing supported process/job census abstraction
```

Use an existing signal only if it is semantically sufficient for the guard decision.

Do not invent an unrelated health signal and call it workload observation.

## 12.2 If an equivalent supported observation exists

Use it generically.

Record:

```text
workload_observation_backend
observation_capabilities
natural_job_observable
model_process_or_execution_observable
```

The repair must not be dependent on a single ticker/run.

## 12.3 If no safe equivalent observation exists

Fail closed before spawn:

```text
LIVE_WORKLOAD_OBSERVATION_UNAVAILABLE
```

Required:

```text
model_invocation_count = 0
```

Do not surface this as `transport_receipt_missing`.

If no safe observation backend exists, the task stops before real model execution and the next scope becomes:

```text
LIVE_WORKLOAD_OBSERVABILITY_COMPATIBILITY
```

---

# 13. Protected natural-live windows remain authoritative

The existing protected-window behavior must remain intact.

The prior run recorded:

```text
provider_and_model_calls_deferred_for_us_natural_window

protected_window_kst =
2026-09-07T08:05:00+09:00 /
2026-09-07T08:40:00+09:00
```

Do not weaken or remove protected time-window deferral merely to avoid process observation.

If a protected window is active:

```text
do not spawn shadow holdout model work
```

No scheduler mutation.

No natural-live cancellation.

---

# 14. Exception provenance repair

The original failure must remain the primary failure.

Required behavior:

```text
PRE_SPAWN guard exception
→ preserve exact root exception classification
→ record failure stage = PRE_SPAWN
→ record spawn_started = 0
→ record transport_receipt_expected = 0
→ do not replace with transport_receipt_missing
```

For this class of failure:

```text
transport_receipt_created = 0
```

is valid and expected.

The result should distinguish:

```text
PRE_SPAWN_GUARD_FAILURE
POST_SPAWN_TRANSPORT_FAILURE
POST_SPAWN_RECEIPT_MISSING
```

Do not use one generic missing-receipt error for all three.

---

# 15. Receipt lifecycle contract

Define and test:

```text
transport_receipt_expected
```

based on actual lifecycle state.

Minimum rules:

### Before subprocess spawn

```text
spawn_started = 0
transport_receipt_expected = 0
missing receipt is not an error by itself
```

### Spawn successfully initiated

```text
spawn_started = 1
transport_receipt_expected = 1
```

If execution then returns without the required receipt:

```text
POST_SPAWN_RECEIPT_MISSING
```

may be valid.

Do not fabricate a receipt for a pre-spawn failure.

---

# 16. Context-preservation behavior

Evidence-preservation code must not mask the causal exception.

On pre-spawn failure, preserve whatever already exists:

```text
prompt
schema
context manifest
pre-spawn guard evidence
root exception
```

but do not require:

```text
model output
stdout
stderr from model subprocess
transport receipt
```

because no subprocess existed.

Required:

```text
context_preservation_secondary_failure_count = 0
root_exception_masked = 0
```

---

# 17. Model-free exact-path guard preflight

Before any real model call, run a preflight through the **same guard/orchestration path used by FIRST**, stopping immediately before model spawn.

The preflight must test:

```text
protected-window decision
workload observation
coexistence decision
exception provenance
receipt-expected state
context-preservation behavior
```

It must invoke:

```text
real model calls = 0
```

Required successful classification:

```text
PRESPAWN_GUARD_PREFLIGHT = PASS
SAFE_TO_SPAWN = 1
```

If observation is unavailable:

```text
PRESPAWN_GUARD_PREFLIGHT = FAIL
SAFE_TO_SPAWN = 0
```

No model call.

---

# 18. Regression tests

Add tests for at least:

```text
ps PermissionError is not masked

pre-spawn failure:
  spawn_started = 0
  receipt_expected = 0

post-spawn missing receipt remains detectable

safe observation backend returns zero contention

safe observation backend returns natural-workload contention

safe observation backend returns model-execution contention

protected time-window blocks spawn

context preservation does not replace root exception

no fail-open on observation unavailable
```

Prefer fictional/minimal fixtures.

No production secrets.

---

# 19. Authorized guard drift vs canonical transport drift

After implementation report:

```text
authorized_guard_compatibility_hash_drift

ContinuationTransportAdapter_semantic_mutation = 0
instrumented_codex_lifecycle_mutation = 0
timeout_owner_mutation = 0
model_context_shape_mutation = 0

transport_process_topology_mutation = 0
model_semantic_input_drift = 0

architecture_semantic_drift = 0
prompt_semantic_drift = 0
schema_semantic_drift = 0
source_drift = 0
```

A changed `GuardedTransportAdapter` or experiment guard hash can be authorized if the underlying subprocess/model transport topology is unchanged.

If canonical adapter/process topology must change:

```text
STOP
BROADER_TRANSPORT_REVALIDATION_REQUIRED
```

---

# 20. Holdout reuse gate

The existing cohort may be reused only if all are proven:

```text
prior real model invocation count = 0
prior subject output count = 0

holdout state = UNEXPOSED
retirement state = ACTIVE_UNEXPOSED

ordered cohort unchanged

source generation unchanged =
20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a

source lock unchanged =
d4bd0b51d9cc543ebe03088047cce375db41d3d9a9f21c07d4fd5646bdf9b1ef

per-issuer packet hashes unchanged
prompt/schema semantic inputs unchanged

model/effort unchanged
context grouping unchanged
investment architecture unchanged

only bounded guard/error-provenance implementation changed
```

Required:

```text
current_holdout_reuse_allowed = 1
```

If any model semantic input changed:

```text
STOP
```

Do not silently rebuild source packets in this task.

---

# 21. Resume generation

Do not reuse the failed runtime generation ID as if nothing happened.

Create a new resume/runtime generation ID.

Reference the same frozen:

```text
cohort
source generation
source lock
packet hashes
prompt/schema semantic inputs
context groups
```

The new runtime precommit may contain the new authorized guard implementation identity.

---

# 22. Live-workload coexistence gate before each heavy context

Before each real model context:

```text
run protected-window check
run sandbox-compatible workload observation
```

Required states:

```text
natural_live_cancel_count = 0
scheduler_mutation = 0
```

If contention exists:

```text
do not spawn shadow context
```

Use the existing safe pause/defer policy.

Do not preempt production monitoring.

---

# 23. FIRST execution

Only after:

```text
PRESPAWN_GUARD_PREFLIGHT = PASS
SAFE_TO_SPAWN = 1
holdout reuse gate = PASS
freeze gate = PASS
```

execute:

```text
FIRST
```

once as one complete cohort-level attempt.

No automatic retry.

No selective continuation after failure.

No timeout increase.

No batch split.

---

# 24. Per-context exact evidence preservation

After every successful context, before the next context:

```text
persist exact raw output
persist stdout
persist stderr/log or safe redacted derivative
persist transport receipt
persist prompt
persist schema
persist context/subject manifest

hash every artifact
secret scan
reopen verification
```

Required:

```text
CONTEXT_EVIDENCE_PRESERVATION = PASS
```

Failure:

```text
STOP
```

---

# 25. Per-context Directional Core semantic gate

After every successful Directional Core context:

```text
schema validity

DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
```

If a hard semantic defect appears:

```text
STOP
```

Retire exposed cohort for architecture repair.

No hotfix.

---

# 26. Transport failure after spawn

After actual model spawn:

No retry.

If a real context times out or transport fails:

```text
preserve exact diagnostics
STOP
```

If partial real output already exists:

```text
holdout_output_exposure_state =
PARTIALLY_EXPOSED

holdout_retirement_state =
RETIRED_PARTIAL_EXPOSURE

future_unseen_holdout_reuse_allowed = 0
```

If another materially similar 1,800-second silent stall appears:

```text
HISTORICAL_STALL_PATTERN_RECURRED = 1
```

Do not call it transient again.

Next scope:

```text
BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR
```

---

# 27. FIRST run-level gates

After complete FIRST and before A:

Required:

```text
first_ownership_gate_status = PASS
first_renderer_gate_status = PASS
first_hard_safety_gate_status = PASS
```

Hard invariants include:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0

PRICE_TIMING_NEW_BUYER_UPGRADE = 0
PRICE_ONLY_HOLDER_REDUCE = 0
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE

PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0

KNOWN_HARD_SAFETY_REGRESSION = 0
```

Only then run A.

---

# 28. A / B / C

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

At first hard execution/semantic/renderer/safety failure:

```text
STOP
```

No later run.

Per-context guard, preservation and early semantic audits remain active.

---

# 29. Stability/generalization

Use only valid completed runs that passed their own gates.

Directional Core:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Price-Timing:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

If insufficient valid repeated runs:

```text
NOT_MEASURED
```

Do not infer.

---

# 30. Production no-change

Required:

```text
main_merge = 0
production_db_mutation = 0
production_scheduler_change = 0
production_telegram_send = 0
monitoring_registration_calls = 0
live_structured_autonomy_activation = 0
live_v2_change = 0
night_futures_code_mutation = 0
night_futures_decision_packet_injection = 0
```

This task must not alter existing US/KR production monitoring behavior.

---

# 31. Monitoring Bootstrap remains out of scope

Only after complete FIRST/A/B/C ownership proof success may:

```text
next_scope =
Monitoring Bootstrap Integration Review
```

Do not implement bootstrap here.

---

# 32. Required guard-repair artifacts

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-current-unexposed-holdout-state

04-prespawn-guard-code-path-audit
05-workload-observation-capability-audit
06-workload-observation-backend-decision
07-prespawn-root-cause-proof

08-exception-provenance-contract
09-receipt-lifecycle-contract
10-context-preservation-error-propagation

11-guard-compatibility-remediation-diff
12-guard-regression-tests
13-model-free-prespawn-guard-preflight

14-authorized-guard-hash-drift-audit
15-canonical-transport-freeze
16-model-semantic-input-freeze
17-source-lock-reuse-proof
18-holdout-reuse-gate
19-resume-runtime-precommit
20-live-workload-coexistence-audit
```

---

# 33. Required execution artifacts if resume is permitted

If guard preflight/reuse gates PASS, additionally produce:

```text
21-first-execution-summary
22-first-context-artifact-manifest
23-first-context-partial-semantic-audits
24-first-ownership-gate
25-first-renderer-gate
26-first-hard-safety-gate

27-run-a-execution-summary
28-run-a-context-artifact-manifest
29-run-a-context-partial-semantic-audits
30-run-a-ownership-gate
31-run-a-renderer-gate
32-run-a-hard-safety-gate

33-run-b-execution-summary
34-run-b-context-artifact-manifest
35-run-b-context-partial-semantic-audits
36-run-b-ownership-gate
37-run-b-renderer-gate
38-run-b-hard-safety-gate

39-run-c-execution-summary
40-run-c-context-artifact-manifest
41-run-c-context-partial-semantic-audits
42-run-c-ownership-gate
43-run-c-renderer-gate
44-run-c-hard-safety-gate

45-holdout-exposure-retirement-state
46-core-stability
47-timing-stability
48-ownership-generalization
49-renderer-ownership-proof
50-hard-safety-regression
51-production-no-change
52-night-futures-no-change
53-monitoring-bootstrap-next-handoff
54-program-completion
```

If the guard remains unavailable:

```text
execution artifacts = NOT_RUN
```

Do not fabricate them.

---

# 34. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

prespawn_guard_root_cause
original_root_exception
root_exception_masked_before_repair

workload_observation_backend
workload_observation_capabilities
ps_dependency_after_repair

observation_unavailable_fail_open_count
observation_unavailable_fail_closed_count

protected_window_semantics_changed

spawn_started_on_guard_failure
transport_receipt_expected_on_guard_failure
transport_receipt_created_on_guard_failure

root_exception_masked_after_repair
context_preservation_secondary_failure_count

prespawn_guard_preflight_status
safe_to_spawn

authorized_guard_compatibility_hash_drift

continuation_adapter_semantic_mutation
instrumented_codex_lifecycle_mutation
transport_process_topology_mutation
timeout_owner_mutation

architecture_semantic_drift
prompt_semantic_drift
schema_semantic_drift
model_semantic_input_drift
source_drift

current_holdout_reuse_allowed

source_generation_id
source_lock
ordered_cohort

model
reasoning_effort
model_timeout_seconds
model_timeout_owner_count
batch_semantics
shared_context_subject_count

real_holdout_model_invocation_count
real_holdout_subject_output_count
transport_retry_count
transport_timeout_count

holdout_output_exposure_state
holdout_semantic_revelation_state
holdout_retirement_state
future_unseen_holdout_reuse_allowed

run_results.first
run_results.a
run_results.b
run_results.c

first_ownership_gate_status
first_renderer_gate_status
first_hard_safety_gate_status

run_a_ownership_gate_status
run_a_renderer_gate_status
run_a_hard_safety_gate_status

run_b_ownership_gate_status
run_b_renderer_gate_status
run_b_hard_safety_gate_status

run_c_ownership_gate_status
run_c_renderer_gate_status
run_c_hard_safety_gate_status

historical_stall_pattern_recurred
ownership_generalization_verdict
ownership_proof_completion_state

main_merge
production_db_mutation
production_scheduler_change
production_telegram_send
monitoring_registration_calls
live_structured_autonomy_activation
live_v2_change
night_futures_code_mutation

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

readiness
stop_reason
next_scope
```

Anything not measured:

```text
NOT_MEASURED
```

---

# 35. Decision matrix

## A. Safe sandbox-compatible observation backend exists

If:

```text
PRESPAWN_GUARD_PREFLIGHT = PASS
SAFE_TO_SPAWN = 1
holdout reuse = PASS
```

resume the same unseen frozen holdout.

## B. Observation remains unavailable

Use:

```text
STOP
LIVE_WORKLOAD_OBSERVATION_UNAVAILABLE
```

Do not spawn the model.

Do not report `transport_receipt_missing`.

Holdout remains:

```text
UNEXPOSED
ACTIVE_UNEXPOSED
```

Next scope:

```text
LIVE_WORKLOAD_OBSERVABILITY_COMPATIBILITY
```

## C. Guard repair requires canonical model transport change

Stop:

```text
BROADER_TRANSPORT_REVALIDATION_REQUIRED
```

Do not resume holdout.

## D. Model starts, then transport fails

Use actual post-spawn transport classification.

Do not conflate it with the repaired pre-spawn guard issue.

## E. Full FIRST/A/B/C proof succeeds

Only then:

```text
readiness =
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW

next_scope =
Monitoring Bootstrap Integration Review
```

---

# 36. Artifact integrity

Final artifact index must include:

```text
relative path
SHA-256
byte size
artifact class
run/stage/context
secret-scan status
```

Required:

```text
artifact_hash_mismatch_count = 0
artifact_size_mismatch_count = 0
artifact_secret_scan_failure_count = 0
```

Report final ZIP SHA-256.

---

# 37. Final task principle

The current holdout itself is ready and still unseen.

The failure occurred before model spawn.

Therefore do not throw away the cohort or rebuild its evidence.

The smallest valid next repair is:

```text
make the pre-spawn live-workload guard observable in the sandbox
without weakening coexistence safety
+
preserve the real root exception when pre-spawn fails
```

Not:

```text
catch PermissionError and assume no contention
```

Not:

```text
remove the live-workload guard
```

Not:

```text
treat missing receipt as root cause before spawn
```

And not:

```text
select a new holdout
```

Preserve safety.

Preserve the unseen cohort.

Fix only the pre-spawn control plane.

Then measure the frozen architecture.
