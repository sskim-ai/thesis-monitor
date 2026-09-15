# Thesis Monitor — Dual-Market Source Coverage + New Issuer Holdout Ownership Proof

## 0. Task identity

Suggested work-instruction filename:

```text
20260907-dual-market-source-coverage-and-new-issuer-holdout-ownership-proof.md
```

Suggested result bundle:

```text
thesis-monitor-20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof-report.zip
```

This task supersedes the immediately preceding new-issuer holdout instruction in one important way:

> **A source-sufficiency shortfall in one market must NOT terminate source-coverage diagnostics for the other market.**

The task must independently inspect and complete bounded source-coverage evaluation for both:

```text
US target = 4 issuers
KR target = 12 issuers
```

before deciding whether a new 16-issuer holdout can be frozen.

The task remains fail-closed for model execution:

```text
US source target satisfied
AND
KR source target satisfied
AND
all freeze gates satisfied
→ only then may real holdout model execution begin
```

If either market remains insufficient after its bounded precommitted candidate/reserve evaluation, do not create a final holdout source lock and do not invoke the real model.

But do **not** stop the task at the first market failure.

Complete the other market's diagnostic first.

---

# 1. Primary purpose

This task has two sequential purposes.

## Purpose A — Dual-market source coverage diagnosis

Evaluate US and KR source coverage independently and completely.

For each market determine:

```text
how many candidates were attempted
how many passed identity validation
how many passed source sufficiency
which exact source domains/components failed
whether failures are true source absence
or assembler/normalization/coverage gaps
whether precommitted reserves can fill the target
```

The output must make it possible to answer:

```text
US: where exactly does source coverage fail?
KR: where exactly does source coverage fail?
Are the failure modes shared or market-specific?
```

## Purpose B — New unseen holdout ownership proof

Proceed to new source lock and FIRST/A/B/C only if both markets independently satisfy their targets after the bounded candidate/reserve process.

---

# 2. Historical authority

Use the latest forensic result as historical source of truth:

```text
thesis-monitor-20260906-partial-output-forensics-bounded-transport-stall-review-report(1).zip
```

Verified SHA-256:

```text
c88368357cd4fbde183d90620194307f9e5498cfd75d2dcafad6b8d04ffbc3b4
```

Recompute at task start.

The latest forensic result established:

```text
runner_adapter_repair_status = CLOSED

partial_output_provenance_gap =
RESOLVED_BY_LOCAL_EXACT_RECOVERY

partial_output_semantic_audit_status =
CLEAN_ON_RECOVERED_DIRECTIONAL_CORE

fictional_probe_status = PASS
fictional_probe_sequence_completed = 1
fictional_probe_timeout_count = 0
sequential_same_namespace_stall_reproduced = 0

historical batch03 root cause =
ROOT_CAUSE_UNRESOLVED

forensic transport classification =
TRANSIENT_STALL_NOT_REPRODUCED

new_real_issuer_model_call_count = 0

readiness =
READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_AND_OWNERSHIP_PROOF
```

Do not reopen already closed runner↔adapter repair unless new direct evidence requires it.

---

# 3. Permanently excluded real issuers

The following 16 issuers from the partially exposed retired cohort must never be reused as unseen proof:

```text
ORCL
UNH
KO
AVGO
095570
058860
246960
099520
403870
014790
079810
060980
061970
012030
225190
245620
```

The consumed regression cohort is also excluded:

```text
PLTR
V
MA
AMZN
XOM
DIS
NKE
MCD
033920
104480
071320
096240
032860
060570
016600
462520
```

Before new selection, also build the repository-local prior-real-issuer exposure registry and exclude any additional real issuer with proven prior model exposure.

---

# 4. Repository provenance gate

Before changing experiment-only tooling:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Classify any changes after the latest known forensic implementation state.

If unexplained semantic drift affects:

```text
Directional Core
Price-Timing
renderer/action ownership
prompt/schema
source/evidence semantics
source sufficiency
model/context shape
ContinuationTransportAdapter
process lifecycle topology
timeout ownership
```

then:

```text
STOP
UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT
```

This hard stop occurs before any new real model call.

Do not reset, merge, cherry-pick, or silently discard unrelated work.

---

# 5. Work-instruction commit first

Commit this work instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Allowed implementation remains experiment-only:

```text
dual-market candidate selection tooling
dual-market source-coverage diagnostics
historical exposure registry
source-lock/report tooling
per-context evidence preservation
per-context partial semantic audit orchestration
ownership-proof runner/report serialization
```

Do not mutate production investment semantics.

---

# 6. Model/runtime freeze

If and only if both market source targets later pass, the real proof remains frozen to:

```text
model = gpt-5.6-sol
reasoning_effort = xhigh

batch_semantics =
MODEL_CONTEXT_COUPLED

shared-context subject count =
4

model timeout =
1800 seconds

model_timeout_owner_count =
1
```

Do not:

```text
increase timeout
add another timeout owner
split a four-subject shared context
change model
change reasoning effort
add automatic retry
```

---

# 7. Build prior-real-issuer exposure registry

Before selecting any new issuer:

Create:

```text
prior-real-issuer-exposure-registry.json
```

At minimum include:

```text
issuer
market
ticker
generation_id
invocation_id
experiment_class
model_call_started
usable_output_exists
exposure_class
source_artifact
```

Then define:

```text
NEW_HOLDOUT_EXCLUSION_SET =
retired partial cohort
+ consumed regression cohort
+ any additional proven historical real-model exposure
```

No model call is allowed in this phase.

---

# 8. Precommit dual-market source-coverage policy

Before evaluating candidate source sufficiency, create and hash:

```text
dual-market-source-coverage-policy.json
```

It must define independently for US and KR:

```text
target issuer count
candidate universe
initial candidate count
reserve count
deterministic candidate ordering
objective eligibility rules
source-sufficiency rules
replacement rules
bounded evaluation limit
stop condition
```

The policy must also define the key behavior:

```text
MARKET_FAILURE_DOES_NOT_ABORT_OTHER_MARKET_DIAGNOSTIC = 1
```

This is a diagnostic orchestration rule only.

It does not weaken final holdout requirements.

---

# 9. Target holdout shape

Target remains:

```text
total issuer count = 16
US issuer count = 4
KR issuer count = 12
```

Expected Directional Core grouping:

```text
US4
KR4
KR4
KR4
```

unless the frozen canonical runner specifies another existing grouping rule.

Do not mix markets merely to work around source or transport problems.

---

# 10. Candidate and reserve evaluation policy

For each market separately:

1. evaluate deterministic primary candidates;
2. if an objective pre-model failure occurs, evaluate the next precommitted reserve;
3. continue until either:
   - target count is reached; or
   - bounded candidate/reserve pool is exhausted.

Objective replacement reasons include only:

```text
identity validation failure
unsupported market
duplicate issuer
source insufficiency
hard source validation failure
missing required evidence packet
```

Replacement is forbidden for:

```text
valuation appearance
price trend
expected BUY/HOLD/SELL
desired sector result
expected ownership result
transport result
```

No model call during source-coverage evaluation.

---

# 11. Critical orchestration change — do not stop after US failure

If US evaluation ends with:

```text
source_sufficient_us_count < 4
```

record:

```text
US_SOURCE_TARGET_STATUS = FAIL
```

but **continue immediately to KR evaluation**.

Do not exit the task.

Do not create a final holdout.

Do not call the model.

Complete KR identity/source-sufficiency evaluation under its own precommitted candidate/reserve policy.

Likewise, if KR evaluation fails first for any implementation reason after US succeeds, still finish any remaining bounded KR diagnostic necessary to identify the failure class before final task stop, provided no semantic repository drift or safety violation requires immediate global stop.

The desired diagnostic outcome is always:

```text
complete US coverage report
+
complete KR coverage report
```

before declaring:

```text
SOURCE_COVERAGE_BLOCKED
```

---

# 12. Market-specific source coverage reports

Produce:

```text
us-source-coverage-audit.json
kr-source-coverage-audit.json
```

For each candidate report at minimum:

```text
ticker
canonical issuer identity
market

candidate_rank
primary_or_reserve

identity_validation_status

source_pipeline_attempted
source_pipeline_status

official_profile_status
filing_or_official_financial_status
earnings_context_status
valuation_input_status
price_context_status
other_required_domain_status

source_sufficiency_status

failure_domains
failure_reason_codes

data_received_but_not_assembled
assembler_or_normalization_gap_suspected

true_source_absence_suspected

packet_created
packet_hash

eligible_for_final_holdout
```

Do not manufacture source-domain detail unsupported by actual pipeline evidence.

If a domain is not part of the canonical source-sufficiency contract, do not invent it as required.

---

# 13. Failure taxonomy

Every source-insufficient issuer must receive the most specific supported reason.

Recommended categories include:

```text
IDENTITY_VALIDATION_FAILURE

OFFICIAL_SOURCE_UNAVAILABLE
OFFICIAL_FINANCIAL_SOURCE_UNAVAILABLE
EARNINGS_CONTEXT_INSUFFICIENT
VALUATION_INPUT_INSUFFICIENT
REQUIRED_FUNDAMENTAL_DOMAIN_INSUFFICIENT

SOURCE_FETCH_SUCCEEDED_PACKET_ASSEMBLY_FAILED
NORMALIZATION_OR_MAPPING_GAP
SOURCE_SUFFICIENCY_RULE_REJECTED

VALIDATION_FAILURE
UNKNOWN_SOURCE_COVERAGE_FAILURE
```

Multiple reason codes are allowed if supported.

Do not use:

```text
SOURCE_INSUFFICIENT
```

as the only explanation when more precise evidence exists.

---

# 14. True source absence vs pipeline coverage gap

For each failed candidate, explicitly distinguish where possible:

```text
SOURCE_ABSENCE
```

versus:

```text
PIPELINE_COVERAGE_GAP
```

A `PIPELINE_COVERAGE_GAP` may include evidence such as:

```text
official source request succeeded
required data exists in retrieved source
but canonical packet omitted or failed to normalize/map it
```

A `SOURCE_ABSENCE` requires evidence that the required canonical source/evidence was not actually available from supported providers during the bounded evaluation.

If evidence is insufficient:

```text
UNKNOWN
```

Do not guess.

---

# 15. Cross-market diagnostic comparison

After both market diagnostics complete, produce:

```text
dual-market-source-coverage-summary.json
```

Include:

```text
us_target
us_attempted
us_source_sufficient
us_source_insufficient

kr_target
kr_attempted
kr_source_sufficient
kr_source_insufficient

shared_failure_reason_codes
us_only_failure_reason_codes
kr_only_failure_reason_codes

pipeline_coverage_gap_count_us
pipeline_coverage_gap_count_kr

source_absence_count_us
source_absence_count_kr

unknown_failure_count_us
unknown_failure_count_kr
```

Also classify:

```text
DUAL_MARKET_SOURCE_STATUS =
BOTH_PASS /
US_FAIL_KR_PASS /
US_PASS_KR_FAIL /
BOTH_FAIL
```

This classification must be available even when no final holdout is created.

---

# 16. Source-coverage remediation decision

After both markets are audited:

## Case A — both markets pass

```text
US source-sufficient >= 4
KR source-sufficient >= 12
```

Then proceed to final new holdout freeze and ownership proof.

## Case B — US fails, KR passes

Stop before model execution.

Use:

```text
readiness =
NOT_READY_US_SOURCE_COVERAGE_BLOCKED
```

Next scope should repair only the proven US source-coverage blocker(s), while preserving evidence that KR coverage is currently adequate.

Do not rerun KR source diagnostics unnecessarily after a US-only remediation unless KR source inputs materially changed.

## Case C — US passes, KR fails

Stop before model execution.

Use:

```text
readiness =
NOT_READY_KR_SOURCE_COVERAGE_BLOCKED
```

Next scope focuses on KR source coverage.

## Case D — both fail

Stop before model execution.

Use:

```text
readiness =
NOT_READY_DUAL_MARKET_SOURCE_COVERAGE_BLOCKED
```

Next scope should prioritize common pipeline gaps first, then market-specific gaps.

---

# 17. No model call until both targets pass

Required invariant:

```text
REAL_HOLDOUT_MODEL_CALLS_WHILE_US_OR_KR_SOURCE_TARGET_FAILS = 0
```

Also:

```text
DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
```

Do not partially run a US-only or KR-only real holdout proof.

The target experiment is one precommitted 16-issuer cohort.

---

# 18. Final cohort freeze — only after dual pass

If and only if:

```text
US_SOURCE_TARGET_STATUS = PASS
KR_SOURCE_TARGET_STATUS = PASS
```

construct the final 16-issuer cohort.

Produce:

```text
new-holdout-selection-result.json
```

with exactly:

```text
4 US issuers
12 KR issuers
```

all absent from the exposure registry.

Then build:

```text
new source generation
per-issuer packet hashes
source identity audit
source sufficiency audit
new aggregate source lock
```

The final source lock must be newly created.

Do not reuse:

```text
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d
```

---

# 19. Final holdout precommit

Before the first real model call produce:

```text
new-holdout-precommit.json
```

Include:

```text
ordered issuer list
canonical issuer identities
market

context grouping

exposure-registry hash
dual-market coverage-policy hash
US coverage-audit hash
KR coverage-audit hash
selection-result hash

source generation ID
source lock
per-issuer packet hashes

prompt/schema identities

model
reasoning effort
timeout
timeout owner count
batch semantics
context size
transport topology identity

per-context evidence-preservation policy
per-context partial semantic-audit policy

FIRST/A/B/C hard-stop rules
```

After this point:

```text
cohort mutation = 0
source mutation = 0
context grouping mutation = 0
```

---

# 20. Per-context evidence preservation

After every successful model context, before launching the next context:

```text
persist exact raw model output
persist stdout
persist stderr/log or safe redacted derivative
persist transport receipt
persist exact prompt
persist exact schema

persist generation/run/stage/batch/subject mapping

compute SHA-256
compute byte size
run secret scan
verify artifact can be reopened
```

Required:

```text
CONTEXT_EVIDENCE_PRESERVATION = PASS
```

If preservation fails:

```text
STOP
```

A successful context still counts as holdout exposure.

Do not continue merely because the model output existed in memory.

---

# 21. Per-context Directional Core early semantic audit

After every successful Directional Core shared context:

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

Required status:

```text
PER_CONTEXT_PARTIAL_SEMANTIC_AUDIT =
PASS / FAIL / NOT_MEASURED
```

If a hard semantic violation is confirmed:

```text
STOP
```

Do not expose later contexts.

Set the cohort to:

```text
REVEALED_FOR_ARCHITECTURE_TUNING
RETIRED_FOR_ARCHITECTURE_REPAIR
```

No same-cohort hotfix.

---

# 22. Transport failure handling

No automatic retry.

No selective continuation.

No batch split.

No timeout increase.

No same-task real-model repair.

If no usable output exists before failure:

```text
holdout_output_exposure_state = UNEXPOSED
```

If partial usable output exists:

```text
holdout_output_exposure_state = PARTIALLY_EXPOSED
holdout_retirement_state = RETIRED_PARTIAL_EXPOSURE
future_unseen_holdout_reuse_allowed = 0
```

Do not rerun the whole cohort.

Do not continue remaining issuers.

---

# 23. Historical stall recurrence

If another materially similar silent 1,800-second stall occurs:

```text
HISTORICAL_STALL_PATTERN_RECURRED = 1
```

Preserve exact diagnostics.

Retry:

```text
0
```

Next scope:

```text
BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR
```

Do not classify it as transient merely because the earlier fictional probe passed.

---

# 24. FIRST execution

Only after both-market source PASS and final freeze.

Execute:

```text
FIRST
```

as one complete cohort-level attempt.

This may require multiple model invocations.

Report separately:

```text
first_complete_run_attempt_count

real_holdout_model_invocation_count
real_holdout_directional_context_count
real_holdout_price_timing_context_count
real_holdout_renderer_context_count
real_holdout_subject_output_count
```

---

# 25. FIRST hard gates

Before A, all applicable FIRST gates must PASS:

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

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE

PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0

KNOWN_HARD_SAFETY_REGRESSION = 0
```

Required:

```text
first_ownership_gate_status = PASS
first_renderer_gate_status = PASS
first_hard_safety_gate_status = PASS
```

Otherwise:

```text
STOP
```

No A.

---

# 26. A / B / C

After clean FIRST:

```text
A
→ A ownership/renderer/hard-safety gates
→ B only if PASS

B
→ B ownership/renderer/hard-safety gates
→ C only if PASS

C
→ C ownership/renderer/hard-safety gates
```

No later run begins after an earlier hard-gate failure.

Per-context evidence preservation and early semantic audits remain active in A/B/C.

---

# 27. Stability/generalization

Use only valid completed runs that passed their own hard gates.

If sufficient valid repeated runs exist:

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

Do not redefine thresholds after seeing outputs.

If evidence is insufficient:

```text
NOT_MEASURED
```

---

# 28. Production no-change

Required:

```text
main_merge = 0
production_db_mutation = 0
production_telegram_send = 0
production_scheduler_change = 0
monitoring_registration_calls = 0
live_structured_autonomy_activation = 0
live_v2_change = 0
night_futures_code_mutation = 0
night_futures_decision_packet_injection = 0
```

This task must not alter tomorrow's existing US/KR production monitoring behavior.

---

# 29. Monitoring Bootstrap remains out of scope

Do not begin Monitoring Bootstrap in this task.

Only after full ownership proof success may:

```text
next_scope =
Monitoring Bootstrap Integration Review
```

The desired later lifecycle remains:

```text
Initial Analysis
→ explicit monitoring request
→ stored investment-logic baseline
→ bootstrap fundamental enrichment
→ source-sufficiency check
→ monitoring-ready baseline
→ Daily Delta
```

---

# 30. Required dual-market diagnostic artifacts

Produce at least:

```text
01-repository-provenance
02-latest-forensic-result-integrity
03-prior-real-issuer-exposure-registry
04-new-holdout-exclusion-set

05-dual-market-source-coverage-policy

06-us-candidate-manifest
07-us-source-coverage-audit
08-us-source-failure-detail

09-kr-candidate-manifest
10-kr-source-coverage-audit
11-kr-source-failure-detail

12-dual-market-source-coverage-summary
13-cross-market-failure-comparison
14-source-coverage-remediation-decision
```

These artifacts must be produced even when US fails before KR begins in the old orchestration.

The new orchestration explicitly requires KR diagnostic completion.

---

# 31. Required execution artifacts if both markets pass

If both markets pass, additionally produce:

```text
15-new-holdout-selection-result
16-new-source-generation
17-source-sufficiency-audit
18-source-identity-audit
19-new-source-lock
20-new-holdout-precommit

21-architecture-semantic-freeze
22-prompt-schema-freeze
23-model-context-freeze
24-transport-topology-freeze
25-holdout-unseen-reuse-gate
26-live-workload-coexistence-audit

27-first-execution-summary
28-first-context-artifact-manifest
29-first-context-partial-semantic-audits
30-first-run-ownership-gate
31-first-run-renderer-gate
32-first-run-hard-safety-gate

33-run-a-execution-summary
34-run-a-context-artifact-manifest
35-run-a-context-partial-semantic-audits
36-run-a-ownership-gate
37-run-a-renderer-gate
38-run-a-hard-safety-gate

39-run-b-execution-summary
40-run-b-context-artifact-manifest
41-run-b-context-partial-semantic-audits
42-run-b-ownership-gate
43-run-b-renderer-gate
44-run-b-hard-safety-gate

45-run-c-execution-summary
46-run-c-context-artifact-manifest
47-run-c-context-partial-semantic-audits
48-run-c-ownership-gate
49-run-c-renderer-gate
50-run-c-hard-safety-gate

51-holdout-exposure-retirement-state
52-core-stability
53-timing-stability
54-ownership-generalization
55-renderer-ownership-proof
56-hard-safety-regression
57-production-no-change
58-night-futures-no-change
59-monitoring-bootstrap-next-handoff
60-program-completion
```

If source coverage blocks before model execution, later artifacts should be explicit:

```text
NOT_RUN
```

not fabricated.

---

# 32. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
final_head_sha
branch

prior_real_issuer_exposure_registry_count
new_holdout_exclusion_count

dual_market_source_policy_hash

us_target_count
us_candidate_attempt_count
us_source_sufficient_count
us_source_insufficient_count
us_pipeline_coverage_gap_count
us_source_absence_count
us_unknown_failure_count
us_source_target_status

kr_target_count
kr_candidate_attempt_count
kr_source_sufficient_count
kr_source_insufficient_count
kr_pipeline_coverage_gap_count
kr_source_absence_count
kr_unknown_failure_count
kr_source_target_status

dual_market_source_status

real_holdout_model_calls_while_source_target_failed

new_holdout_cohort
new_source_generation_id
new_source_lock

model
reasoning_effort
model_timeout_seconds
model_timeout_owner_count
batch_semantics
shared_context_subject_count

architecture_semantic_drift
prompt_semantic_drift
schema_semantic_drift
model_semantic_input_drift
transport_topology_mutation
timeout_increase_this_task

holdout_output_exposure_state
holdout_semantic_revelation_state
holdout_retirement_state
future_unseen_holdout_reuse_allowed

first_complete_run_attempt_count
real_holdout_model_invocation_count
real_holdout_subject_output_count

context_evidence_preservation_failure_count
per_context_semantic_failure_count
transport_timeout_count
transport_retry_count
historical_stall_pattern_recurred

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

readiness
stop_reason
next_scope
```

Anything not actually measured remains:

```text
NOT_MEASURED
```

---

# 33. Artifact integrity

Final artifact index must contain:

```text
relative path
SHA-256
byte size
artifact class
market
candidate/run/stage/context
secret-scan status
```

Required:

```text
artifact_hash_mismatch_count = 0
artifact_size_mismatch_count = 0
```

Report final result ZIP SHA-256.

---

# 34. Key task-success conditions

At the source-diagnostic level, this task is successful if:

```text
US source coverage fully diagnosed
AND
KR source coverage fully diagnosed
```

even if one or both targets fail.

Do not treat:

```text
US target failure
```

as a reason not to learn the KR failure/success pattern.

At the ownership-proof level, model execution is allowed only if:

```text
US target PASS
AND
KR target PASS
AND
final source lock/freeze PASS
```

---

# 35. Final decision principle

The correct source-coverage workflow is now:

```text
diagnose US fully
→ regardless of US target result, diagnose KR fully
→ compare both markets
→ decide remediation
```

Not:

```text
US fails
→ terminate task
→ KR remains unknown
```

But experiment safety remains:

```text
either market fails
→ no final 16-issuer holdout
→ no source lock for proof
→ no real model call
```

This allows the next remediation task to address the real bottleneck(s) in one pass rather than discovering US and KR problems sequentially over multiple days.

Measure both markets first.

Then fix only what the evidence supports.
