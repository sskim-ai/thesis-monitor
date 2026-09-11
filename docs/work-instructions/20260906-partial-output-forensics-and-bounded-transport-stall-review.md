# Thesis Monitor — Partial Output Forensics + Bounded Transport Stall Review

## 0. Task identity

Suggested work-instruction filename:

```text
20260906-partial-output-forensics-and-bounded-transport-stall-review.md
```

Suggested result bundle:

```text
thesis-monitor-20260906-partial-output-forensics-bounded-transport-stall-review-report.zip
```

This is a **bounded forensic / evidence-preservation / transport-stall review task**.

It follows the completed real-holdout runner↔adapter repair and the partially exposed FIRST attempt.

The current task is NOT:

- a runner↔adapter repair task;
- an investment architecture tuning task;
- a Directional Core / Price-Timing semantic change;
- a production transport redesign;
- a timeout-increase task;
- a same-cohort continuation task;
- a selective remaining-subject rerun;
- a new real-issuer holdout-selection task;
- a new real-issuer ownership-proof run;
- a monitoring-bootstrap task;
- a production-promotion task.

The bounded task scope is:

```text
recover/preserve prior partial real outputs if they still exist
→ validate recovered partial outputs offline with zero model recall
→ perform batch03 lifecycle/log forensic review
→ run one bounded fictional sequential transport probe
→ classify the next blocker
```

The main current blocker is no longer the runner↔adapter interface.

It is:

```text
DIRECTIONAL_CORE batch03
1800-second silent transport/model stall
after two successful shared-context batches
```

The current retired real cohort must not be reused as unseen evidence.

---

# 1. Authoritative source-of-truth model

Use concern-specific authority.

## 1.1 Latest measured experiment result

The authoritative latest result bundle is:

```text
thesis-monitor-20260906-real-holdout-runner-adapter-repair-ownership-proof-resume-report(2).zip
```

Externally verified ZIP SHA-256:

```text
5704dc77bd77458ae68550aa8262cc90525a562e739345a1dace39b7a194ef2b
```

At task start, independently recompute the SHA-256.

If it does not match:

```text
STOP
RESULT_BUNDLE_CHECKSUM_MISMATCH
```

The latest result bundle is authoritative for historical measured facts.

## 1.2 Current repository

Current repository HEAD/worktree is authoritative for the code/configuration that exists now.

Do not let the historical bundle overwrite current repository facts.

Do not let current code rewrite historical run facts.

## 1.3 Current task constraints

This work instruction is authoritative for:

- forensic scope;
- real-issuer model-call prohibition;
- retired-cohort rules;
- partial-output preservation requirements;
- offline validation requirements;
- fictional sequential transport probe;
- next-scope decision rules.

## 1.4 Investment / safety semantics

Use the current Investment Thesis Analysis & Monitoring Knowledge Guide and frozen repository contracts for:

- Directional Core ownership;
- Price-Timing ownership;
- renderer/action ownership;
- source sufficiency;
- numeric provenance;
- accounting attribution;
- ADR/security basis;
- official provisional earnings;
- price/supply separation.

Do not reinterpret these semantics during forensic review.

---

# 2. Latest confirmed historical facts

The latest result bundle establishes the following.

## 2.1 Runner↔adapter repair succeeded

Root cause:

```text
RUNNER_OWNED_CODEX_BIN_LEAKED_TO_CANONICAL_ADAPTER
```

Detailed classification:

```text
codex_bin =
RUNNER_OWNED_LEGACY_TRANSPORT_CONFIGURATION

defect_location =
REAL_HOLDOUT_RUNNER_ARGUMENT_BRIDGE

canonical adapter API widened = 0
```

The repair consumed `codex_bin` in the runner bridge instead of widening `ContinuationTransportAdapter.invoke()`.

Binding preflight:

```text
REAL_HOLDOUT_RUNNER_ADAPTER_BINDING_PREFLIGHT = PASS
model_invocation_count = 0
```

Repair/freeze result:

```text
implementation_success = 1
full_tests = PASS
ruff = PASS

authorized_harness_hash_drift = 1

directional_core_semantic_mutation = 0
price_timing_semantic_mutation = 0
composer_semantic_mutation = 0
renderer_semantic_mutation = 0

prompt_semantic_drift = 0
schema_semantic_drift = 0

source_drift = 0
source_sufficiency_policy_drift = 0

transport_topology_mutation = 0
model_semantic_input_drift = 0
batch_split_adopted = 0
```

Model/runtime remained:

```text
model = gpt-5.6-sol
reasoning_effort = xhigh
batch_semantics = MODEL_CONTEXT_COUPLED
real_run_batch_size = 4
model_timeout_seconds = 1800
model_timeout_owner_count = 1
```

Historical canaries remained reused rather than rerun:

```text
historical_canaries_reused = 7
historical_canaries_rerun = 0
```

This task must treat the runner↔adapter repair as **closed unless new direct evidence contradicts it**.

Do not reopen it merely because batch03 later timed out.

---

# 3. FIRST result — exact observed sequence

Source generation:

```text
20260906-direction-timing-holdout-20260906T093200Z-bd30668470f0
```

Resume generation:

```text
20260906-real-holdout-adapter-resume-20260906T133003Z-585c983a57d9
```

Frozen source lock:

```text
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d
```

FIRST status:

```text
FAILED
error_type = CodexTransportError
error = MODEL_TIMEOUT:attempts=1
transport_failure = 1

real_holdout_transport_retry_count = 0
same_generation_repair = 0
selective_rerun = 0
schema_failure = 0
execution_harness_interface_failure = 0
```

Observed Directional Core context sequence:

### core-batch-01

```text
status = PASS
subject_count = 4
input_bytes = 17630
output_bytes = 16612
stdout_bytes = 16613
elapsed_to_exit_seconds = 155.827806
elapsed_to_first_stderr_seconds = 1.579687
elapsed_to_first_stdout_seconds = 155.664766
orphan_model_process_count = 0
```

### core-batch-02

```text
status = PASS
subject_count = 4
input_bytes = 17967
output_bytes = 16361
stdout_bytes = 16362
elapsed_to_exit_seconds = 155.095142
elapsed_to_first_stderr_seconds = 0.282999
elapsed_to_first_stdout_seconds = 154.950691
orphan_model_process_count = 0
```

### core-batch-03

```text
status = TIMEOUT
subject_count = 4
input_bytes = 17896
output_bytes = 0
stdout_bytes = 0
configured_timeout_seconds = 1800
elapsed_to_exit_seconds = 1800.032760

elapsed_to_first_stderr_seconds ≈ 0.284216
elapsed_to_first_stdout_seconds = null

parse_error = OUTPUT_FILE_MISSING
exit_code = -15

termination_initiator =
PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG

termination_signal = 15

child_cleanup_status =
PROCESS_GROUP_TERMINATED

orphan_model_process_count = 0
timeout_owner_count = 1
```

The batch03 transport receipt records a very short startup stderr burst:

```text
first_stderr_byte_monotonic = 253169.324368083
last_stderr_byte_monotonic  = 253169.324493166
```

Observed stderr burst duration is approximately:

```text
0.000125 seconds
```

Observed silence from last stderr byte to process exit is approximately:

```text
1799.748419 seconds
```

The three invocations used the same recorded runtime state namespace hash:

```text
109349399ebbd66080e41cf4
```

Live workload audit for all three contexts:

```text
active_natural_job_count = 0
other_codex_exec_count = 0
live_workload_contention_risk = 0
natural_live_cancel_count = 0
scheduler_mutation = 0
```

Therefore do not classify this event as a recurrence of:

```text
multiple timeout owners
orphan-process leakage
live workload contention
runner-adapter interface mismatch
```

unless new evidence proves otherwise.

---

# 4. Current holdout state — retired cohort

Original ordered 16-subject cohort:

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

The first eight exposed subjects are:

```text
ORCL
UNH
KO
AVGO
095570
058860
246960
099520
```

The eight not yet returned as real model output are:

```text
403870
014790
079810
060980
061970
012030
225190
245620
```

Latest measured holdout state:

```text
real_holdout_subject_output_count = 8

holdout_output_exposure_state =
PARTIALLY_EXPOSED

holdout_semantic_revelation_state =
NOT_MEASURED

holdout_retirement_state =
RETIRED_PARTIAL_EXPOSURE

future_unseen_holdout_reuse_allowed = 0
same_cohort_architecture_tuning_rerun_allowed = 0
```

These states are correct and must remain preserved.

## 4.1 Entire 16-subject cohort is retired

Do not rerun the entire 16-subject FIRST.

Do not resume only the unexposed eight.

Do not call batch03 again.

Do not call batch04.

Do not selectively continue the remaining subjects.

The fact that eight subjects did not yet receive model output does not make them separately reusable as unseen proof subjects.

Selective continuation after a partial cohort failure would break the precommitted experiment.

Therefore:

```text
ALL_16_CURRENT_HOLDOUT_ISSUERS_EXCLUDED_FROM_FUTURE_UNSEEN_PROOF = 1
```

They may remain available only as:

```text
historical evidence
regression history
forensic reference
```

subject to the specific no-model-call rules in this task.

---

# 5. Real issuer model-call prohibition for this task

This task must produce:

```text
new_real_issuer_model_call_count = 0
```

This prohibition includes:

- the eight exposed issuers;
- the eight unexposed issuers from the retired cohort;
- the old consumed regression cohort;
- any newly selected real issuers.

Do not select a new real holdout in this task.

Do not call the model on a real company to diagnose transport.

Do not replay a real issuer prompt.

Do not use the remaining eight subjects as a diagnostic continuation.

The only new model calls authorized in this task are the explicitly defined **fictional sequential transport probe**.

---

# 6. Existing regression cohort remains consumed

Do not issue new model calls for:

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

Future unseen holdout selection must exclude both:

1. this consumed regression cohort; and
2. all 16 issuers from the partially exposed retired cohort.

No new holdout is selected in this task.

---

# 7. Newly identified audit gap — partial-output provenance

The result bundle reports:

```text
real_holdout_subject_output_count = 8
```

and lists:

```text
exposed_subjects = [
  ORCL,
  UNH,
  KO,
  AVGO,
  095570,
  058860,
  246960,
  099520
]
```

However, the result ZIP does **not** contain the exact batch01/batch02 Directional Core model output files.

It contains transport receipts and metadata proving that output was parsed, but not the actual model decision artifacts.

This creates:

```text
PARTIAL_OUTPUT_PROVENANCE_GAP = 1
```

The gap does not retroactively convert the runner repair into failure.

It does not change the retired-cohort state.

It does prevent independent offline revalidation of the actual eight outputs from the result ZIP alone.

The first priority of this task is to attempt recovery and preservation of those exact historical outputs **without any model recall**.

---

# 8. Task goals

This task has four bounded goals.

## Goal A — Recover and preserve historical partial output

Attempt to recover the exact batch01 and batch02 real-model outputs from the previous local generation artifacts.

No model recall.

No regeneration.

No reconstruction from metadata.

## Goal B — Offline validate the recovered eight outputs

If exact provenance-linked output can be recovered, run applicable Directional Core ownership / schema / safety validators offline.

No model call.

Do not claim Price-Timing or renderer gates were measured when Price-Timing never ran.

## Goal C — Perform batch03 lifecycle/log forensic review

Recover and analyze raw batch03 stderr/log/process lifecycle evidence if still present.

Do not assume a model compute stall, CLI stall, state-namespace problem, prompt pathology, or backend stall without evidence.

## Goal D — Run one bounded fictional sequential transport probe

Use only fictional subjects and valid production market enums to test:

```text
shared state namespace
US4 → KR4 → KR4
three sequential Directional Core-like invocations
```

No real issuers.

No real holdout prompts.

No timeout increase.

---

# 9. Repository provenance gate

Before creating or modifying forensic/probe code:

Record:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Latest result reported:

```text
branch =
codex/20260906-real-holdout-runner-adapter-repair-ownership-proof-resume

implementation_commit =
16681321683d4ef6bdbff4007770524b1b153136

final_head_sha =
16681321683d4ef6bdbff4007770524b1b153136

work_instruction_commit =
a539eaa
```

Do not assume current HEAD is still exactly that SHA.

Classify any later repository changes.

If current code has unexplained semantic changes affecting:

```text
investment architecture
prompt/schema
source/evidence semantics
model/context shape
ContinuationTransportAdapter semantics
process lifecycle topology
timeout ownership
```

then:

```text
STOP
UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT
```

Do not reset, merge, cherry-pick, or discard unrelated work.

---

# 10. Work-instruction commit first

Commit this work instruction before implementation of any forensic/probe helper.

Record:

```text
new_work_instruction_commit
```

This task may add:

- experiment-only forensic scripts;
- output-preservation helpers;
- offline validation adapters;
- fictional probe fixtures;
- report generation.

It must not change investment semantics or shared production transport semantics.

---

# 11. Allowed mutation surface

Allowed:

```text
experiment-only forensic tooling
experiment-only evidence recovery tooling
offline validator wiring
fictional sequential probe fixture
fictional probe runner
result/report serialization
artifact-preservation logic for this task
```

Strong preference:

```text
reuse existing validated transport adapter and validators
```

Do not modify the shared adapter just to add diagnostic behavior.

If additional observability is required, prefer:

```text
experiment-only wrapper
existing receipt fields
read-only lifecycle capture
```

If the needed diagnostic requires changing shared transport topology:

```text
STOP
BROADER_TRANSPORT_REVALIDATION_REQUIRED
```

---

# 12. Forbidden mutations

Do not change:

```text
Directional Core semantics
Price-Timing semantics
deterministic composer semantics
renderer/action ownership semantics

BUY/HOLD/SELL thresholds
BUY:SELL rules
HOLD lean rules
new-buyer/holder transition rules

DecisionEvidencePacket semantics
production market enum
prompt semantics
model output schema

source assembly
source sufficiency
fundamental enrichment
numeric provenance
valuation safety
ADR/security basis
official provisional earnings logic

ContinuationTransportAdapter canonical contract
instrumented Codex transport topology
process-group lifecycle
timeout ownership

model
reasoning effort
production scheduler
production DB
Telegram production send
monitoring registration
Night Futures
```

Do not increase the real/model transport timeout from:

```text
1800 seconds
```

Do not solve this task by changing it to:

```text
3600 seconds
```

A timeout increase is explicitly out of scope.

---

# 13. Phase A — Verify latest result bundle integrity

Recompute:

```text
SHA-256(
  thesis-monitor-20260906-real-holdout-runner-adapter-repair-ownership-proof-resume-report(2).zip
)
```

Expected:

```text
5704dc77bd77458ae68550aa8262cc90525a562e739345a1dace39b7a194ef2b
```

Verify the internal artifact index.

Expected historical index facts:

```text
artifact_count = 63
artifact_hash_mismatch_count = 0
artifact_size_mismatch_count = 0
```

Also explicitly confirm whether exact real-output files are absent from the bundle.

Required field:

```text
prior_bundle_exact_partial_output_files_present =
0 / 1
```

Expected from the known result:

```text
0
```

Do not treat transport metadata as a substitute for the actual output bytes.

---

# 14. Phase B — Historical output recovery search

Search read-only local artifacts for the prior generation:

```text
20260906-real-holdout-adapter-resume-20260906T133003Z-585c983a57d9
```

and the exact invocation IDs:

```text
...:run-first:DIRECTIONAL_CORE:01
...:run-first:DIRECTIONAL_CORE:02
...:run-first:DIRECTIONAL_CORE:03
```

The search may include:

```text
repository experiment output directories
generation-specific temp/work directories
runner output paths
captured stdout files
structured parsed output files
transport logs
stderr logs
receipt-linked artifact locations
```

Do not search unrelated user data.

Do not invoke the model.

Do not regenerate historical outputs.

## 14.1 Batch01 expected consistency signals

Receipt facts:

```text
batch_id = 01
prompt_sha256 =
73cc97228b7263ba207c333278798ea9d5cb281c9e6a9e039c615eecacba9f84

schema_sha256 =
fbb4d4e7642e9a2bed8a9d15ebd8ba4f5817d1a7eb44f2eac5942b4907875ad8

output_bytes = 16612
stdout_bytes = 16613
output_parsed = true
subject_count = 4
```

## 14.2 Batch02 expected consistency signals

Receipt facts:

```text
batch_id = 02
prompt_sha256 =
5bf8257acbc6197f0f3b904714852261cf7b88cfe53486043170ad4968d3dab1

schema_sha256 =
97ed401cc09f7173c3a8f87e780d36ae7cc2d71d94573dfef357283578c910cd

output_bytes = 16361
stdout_bytes = 16362
output_parsed = true
subject_count = 4
```

Byte-count differences between a parsed output file and captured stdout may include a trailing newline.

Use byte sizes only as consistency evidence, not as a substitute for provenance.

---

# 15. Provenance criteria for recovered output

Do not call an arbitrary matching file the historical output.

For each recovered batch require a provenance chain containing as much as available:

```text
generation_id
invocation_id
stage
batch_id

original local artifact location or safe identity
recovery method

file SHA-256
file byte size

receipt prompt hash
receipt schema hash

subject count
subject identity list

parse status
schema validation status

copied artifact SHA-256
copied artifact byte size
```

Preferred classification:

```text
EXACT_PROVENANCE_LINKED_OUTPUT_RECOVERED
```

Other allowed classifications:

```text
PROVENANCE_AMBIGUOUS
OUTPUT_NOT_FOUND
OUTPUT_FOUND_BUT_NOT_PROVENANCE_LINKED
SECRET_BEARING_OUTPUT_NOT_BUNDLED
```

Do not reconstruct a missing model output from:

```text
reports
subject metadata
expected decisions
transport receipts
```

If exact output cannot be recovered, report it honestly.

---

# 16. Preserve exact recovered output bytes

If a provenance-linked historical output file exists:

1. copy it read-only into the new result bundle;
2. preserve exact bytes;
3. compute SHA-256;
4. compute byte size;
5. do not prettify or normalize the raw artifact in place.

Recommended bundle paths:

```text
recovered-real-output/
  first-directional-core-batch-01.raw.json
  first-directional-core-batch-02.raw.json
```

If a normalized parsed copy is useful, store it separately:

```text
recovered-real-output/
  first-directional-core-batch-01.normalized.json
  first-directional-core-batch-02.normalized.json
```

Never replace the exact raw copy with the normalized copy.

## 16.1 Secret handling

Run the existing secret-exposure scan before bundling.

If exact raw output unexpectedly contains a secret:

- do not expose the secret in the result ZIP;
- record the original file hash and size locally in evidence;
- produce a redacted derivative;
- set:

```text
exact_output_bundle_preservation =
BLOCKED_BY_SECRET_POLICY
```

Do not silently alter exact historical bytes and call them raw.

---

# 17. Preserve subject-to-batch mapping

The prior ordered cohort implies the known first two batches are:

### Batch01 exposed subjects

```text
ORCL
UNH
KO
AVGO
```

### Batch02 exposed subjects

```text
095570
058860
246960
099520
```

Verify this mapping against recovered output before using it for semantic audit.

Do not assume the mapping solely from ordered metadata if the recovered file contradicts it.

If contradiction occurs:

```text
STOP
PARTIAL_OUTPUT_SUBJECT_MAPPING_CONFLICT
```

---

# 18. Phase C — Offline schema and ownership audit

This phase is allowed only for exact provenance-linked recovered output.

Model calls:

```text
0
```

Use the exact original output bytes plus the frozen validator semantics.

Do not modify validators to make historical output pass.

## 18.1 Schema validity

Revalidate each recovered batch against the exact schema used by that invocation if recoverable.

Verify schema hashes:

Batch01:

```text
fbb4d4e7642e9a2bed8a9d15ebd8ba4f5817d1a7eb44f2eac5942b4907875ad8
```

Batch02:

```text
97ed401cc09f7173c3a8f87e780d36ae7cc2d71d94573dfef357283578c910cd
```

If exact historical schema bytes are unavailable but a current canonical schema is byte-identical to the receipt hash, it may be used.

If no exact-hash schema can be obtained:

```text
offline_schema_revalidation = NOT_MEASURED
```

Do not replace the prior receipt fact:

```text
output_parsed = true
```

with a stronger unsupported claim.

## 18.2 Applicable Directional Core ownership gates

Audit, for the recovered eight subjects:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS
DIRECTIONAL_CORE_SUPPLY_REFS
SUPPLY_DIRECTIONAL_CORE_USAGE

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS

FINAL_DIRECTION_OWNER
```

Where an invariant is structurally evaluable from Directional Core output and frozen source metadata, evaluate it.

Where it requires a stage that never ran, leave it:

```text
NOT_MEASURED
```

## 18.3 Do not overclaim Price-Timing validation

FIRST never reached Price-Timing.

Therefore the following are not proven by recovered Directional Core output alone:

```text
TIMING_STAGE_DIRECTION_MUTATION
TIMING_STAGE_BALANCE_MUTATION
TIMING_STAGE_HOLD_LEAN_MUTATION
PRICE_TIMING_NEW_BUYER_UPGRADE
PRICE_ONLY_HOLDER_REDUCE
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS
```

Unless the canonical validator can establish a specific zero purely because Price-Timing invocation count was zero, report the semantic gate itself as:

```text
NOT_MEASURED
```

Do not reinterpret non-execution as evidence that the architecture would have passed.

## 18.4 Renderer/action ownership

If renderer output was not produced/preserved for the partial batch:

```text
PRIMARY_USER_ACTION_WORDING_OWNER = NOT_MEASURED
AI_IMPERATIVE_PRIMARY_ACTION = NOT_MEASURED
```

Do not invent a renderer result from Directional Core model text.

## 18.5 Hard safety

Run only hard-safety checks actually supported by recovered output and frozen evidence.

Preserve:

```text
no fabricated numeric provenance
no accounting attribution substitution
no ADR/share-basis mixing
no provisional-earnings fabrication
no unavailable evidence promoted to Fact
no price/supply promoted into fundamental investment logic
```

Unsupported checks remain:

```text
NOT_MEASURED
```

---

# 19. Partial semantic audit classification

Produce:

```text
partial_output_semantic_audit_status =
CLEAN_ON_RECOVERED_DIRECTIONAL_CORE /
SEMANTIC_DEFECT_CONFIRMED /
PARTIALLY_MEASURED /
NOT_MEASURED
```

## 19.1 If a semantic defect is confirmed

If exact recovered output proves a real hard ownership or hard-safety semantic violation:

```text
holdout_semantic_revelation_state =
REVEALED_FOR_ARCHITECTURE_TUNING

holdout_retirement_state =
RETIRED_FOR_ARCHITECTURE_REPAIR
```

Then:

```text
architecture repair needed = 1
```

Do not tune code in this task.

Continue only non-mutating forensic evidence collection if useful.

The fictional transport probe may still run only if it remains useful to independently classify the transport blocker and does not modify architecture.

Next scope must prioritize:

```text
GENERIC_ARCHITECTURE_REPAIR
THEN_NEW_ISSUER_HOLDOUT
```

## 19.2 If recovered partial Directional Core is clean

Do not upgrade overall ownership proof to PASS.

Use:

```text
partial_output_semantic_audit_status =
CLEAN_ON_RECOVERED_DIRECTIONAL_CORE

ownership_generalization_verdict =
NOT_MEASURED
```

The partial clean result is evidence, not full proof.

The cohort remains retired.

## 19.3 If output cannot be recovered

Use:

```text
partial_output_semantic_audit_status =
NOT_MEASURED

partial_output_provenance_gap =
UNRESOLVED
```

Do not infer semantic cleanliness from transport metadata.

---

# 20. Phase D — Historical batch03 raw-log recovery

Attempt to recover the exact batch03:

```text
stderr
transport log
CLI/runtime log
process lifecycle artifact
output-path metadata
```

linked to invocation:

```text
20260906-real-holdout-adapter-resume-20260906T133003Z-585c983a57d9:run-first:DIRECTIONAL_CORE:03
```

No model recall.

Preserve raw evidence if safe.

Recommended paths:

```text
recovered-transport-forensics/
  batch03.stderr.raw.log
  batch03.transport.raw.log
  batch03-lifecycle.json
```

If raw logs contain secrets:

- do not bundle secret-bearing originals;
- hash originals;
- create redacted derivatives;
- document redaction count and categories.

---

# 21. Batch03 forensic comparison matrix

Compare batch01, batch02 and batch03 on at least:

```text
CLI binary path
CLI binary SHA-256
CLI version

model
reasoning effort

state namespace hash

working directory identity
input bytes
prompt hash
schema hash

network readiness probe count
resolved address count
TLS trust source

stdin completion timing

first stderr timing
last stderr timing
stderr byte count

first stdout timing
last stdout timing
stdout byte count

output file existence
output parse status

process exit timing
exit code

termination initiator
termination signal

timeout owner
timeout owner count

child cleanup status
orphan process count
```

Known shared CLI facts:

```text
cli_version =
codex-cli 0.148.0-alpha.15

cli_binary_sha256 =
7645c3caf5607e4528eb3a15b12496c284c2a918939aed34e863c760c1b421e7
```

Do not expose private tokens or secrets.

---

# 22. Batch03 forensic questions

Answer from evidence, not guesswork.

At minimum:

1. Did batch03 stdin complete normally?
2. Was the child process successfully spawned?
3. Did it emit only a startup stderr burst?
4. Was there any stdout at all?
5. Was an output file ever created?
6. Was the same runtime state namespace used as batches01/02?
7. Was the CLI binary/version identical?
8. Were network readiness checks materially different?
9. Was there concurrent Codex/live workload?
10. Did the watchdog behave as designed?
11. Did process-group cleanup succeed?
12. Is there evidence that the request reached the remote model backend?
13. Is there evidence of a local CLI event-loop/runtime hang?
14. Is there evidence of a model-compute/backend stall?
15. Is there evidence of a state-namespace sequential-invocation correlation?
16. Is there evidence of a prompt/context-specific pathological latency?
17. Can any of those be confirmed, or are they only hypotheses?

Important historical constraint:

```text
request_accepted_observability = UNAVAILABLE
```

in the transport receipts.

Do not claim the backend accepted the request unless new raw logs establish it.

---

# 23. Root-cause classification discipline

Allowed result classifications include:

```text
CONFIRMED_LOCAL_CLI_RUNTIME_STALL
CONFIRMED_STATE_NAMESPACE_SEQUENCE_FAILURE
CONFIRMED_PROMPT_CONTEXT_PATHOLOGY
CONFIRMED_BACKEND_OR_MODEL_STALL

STATE_NAMESPACE_CORRELATION_SUSPECTED
LOCAL_CLI_RUNTIME_STALL_SUSPECTED
MODEL_OR_BACKEND_STALL_SUSPECTED
PROMPT_CONTEXT_PATHOLOGY_POSSIBLE
TRANSIENT_STALL_NOT_REPRODUCED
ROOT_CAUSE_UNRESOLVED
```

Use `CONFIRMED_*` only with direct evidence.

The following known pattern is not enough by itself to select one root cause:

```text
batch01 PASS ~156 sec
batch02 PASS ~155 sec
batch03 startup stderr only
batch03 stdout 0
batch03 1800-sec timeout
```

Do not collapse multiple live hypotheses into one unsupported diagnosis.

---

# 24. Supplementary historical implementation-freeze audit

The prior result reported:

```text
implementation_commit =
16681321683d4ef6bdbff4007770524b1b153136

final_head_sha =
16681321683d4ef6bdbff4007770524b1b153136
```

and pre-FIRST freeze checks were reported PASS.

However, the previous bundle does not necessarily contain a fully explicit immutable timestamp proof that no implementation mutation occurred between the final implementation state and FIRST invocation.

Perform a bounded historical audit using existing local git/log evidence if available.

Compare:

```text
implementation commit identity
commit timestamps
FIRST start timestamp
worktree/report generation evidence
freeze hash evidence
```

FIRST batch01 started at:

```text
2026-09-06T13:30:21.890362+00:00
```

Classify:

```text
historical_pre_first_implementation_freeze_proof =
COMPLETE /
STRONG_BUT_TIMESTAMP_INCOMPLETE /
CONTRADICTED
```

Do not manufacture timestamp evidence.

If contradicted in a way that could alter model semantic inputs:

```text
STOP
EXPERIMENT_FREEZE_INTEGRITY_CONFLICT
```

Otherwise this audit is supplementary and does not by itself invalidate the known partial run.

---

# 25. Phase E — Fictional sequential transport probe

After static/forensic recovery, run one bounded synthetic/fictional sequential transport probe.

This is the only model-backed operation authorized in this task.

## 25.1 Real issuer prohibition

All probe subjects must be fictional.

Do not use:

```text
ORCL
UNH
KO
AVGO
any Korean listed issuer
any US listed issuer
any consumed regression issuer
```

Do not use recognizable real-company names, tickers, financials, or source events.

## 25.2 Valid routing enums

Fictional identity must remain separate from routing market.

Use only production-valid market values:

```text
us
kr
```

Do not reintroduce:

```text
market = synthetic
```

The previous synthetic fixture repair remains closed.

## 25.3 Probe sequence

Precommit one fictional sequence:

```text
probe-batch-01 = 4 fictional US subjects
probe-batch-02 = 4 fictional KR subjects
probe-batch-03 = 4 fictional KR subjects
```

Run them sequentially:

```text
01 → 02 → 03
```

under one newly created fictional runtime state namespace.

Important:

- same namespace across the three fictional probe invocations;
- do NOT reuse the historical real-holdout namespace;
- do NOT use the historical real-holdout generation ID;
- do NOT use historical real-issuer prompts.

## 25.4 Context shape

Use:

```text
batch_semantics = MODEL_CONTEXT_COUPLED
subject_count = 4 per invocation
model = gpt-5.6-sol
reasoning_effort = xhigh
```

Construct schema-valid fictional packets with similar architecture-scale payload size.

Target approximate input range:

```text
15 KB – 20 KB per shared context
```

Do not add meaningless giant padding solely to hit an exact byte count.

The goal is comparable architecture-scale context, not byte-perfect replay.

## 25.5 Transport topology

Use the already validated current transport topology unchanged:

```text
Popen new session
stdin writer
stdout reader
stderr reader
single monotonic watchdog
process-group cleanup
output parse
single receipt
```

Do not modify the canonical adapter.

Do not add a second timeout owner.

Do not split the four-subject context.

## 25.6 Timeout

Do not increase the timeout.

For direct comparability use:

```text
configured_timeout_seconds = 1800
```

with one authoritative watchdog.

If any fictional probe invocation times out:

```text
STOP PROBE
retry = 0
```

Do not rerun the same failed fictional batch in the same task.

---

# 26. Probe observability requirements

Unlike the prior partial result bundle, this task must preserve diagnostic artifacts for every fictional probe invocation.

For each probe batch preserve:

```text
exact model output if produced
exact stdout capture
stderr/log capture
transport receipt
input byte size
output byte size
prompt hash
schema hash
state namespace hash
CLI binary hash
CLI version
timing fields
exit code
termination initiator
cleanup status
orphan count
```

Secret scan all artifacts before bundling.

If secrets appear in raw stderr/log:

- hash the raw local artifact;
- bundle a redacted derivative;
- document redaction.

Do not omit successful probe output files from the final result ZIP.

This task must explicitly fix the **evidence-preservation process gap** for newly generated diagnostic output, even though it does not retroactively fix the prior bundle.

---

# 27. Probe outcome interpretation

## 27.1 All three fictional batches PASS

If:

```text
probe01 = PASS
probe02 = PASS
probe03 = PASS
```

then classify:

```text
sequential_same_namespace_stall_reproduced = 0
```

Appropriate interpretation:

```text
TRANSIENT_STALL_NOT_REPRODUCED
```

or:

```text
ROOT_CAUSE_UNRESOLVED_NONREPRODUCED
```

Do not claim the historical batch03 stall was impossible or fully solved.

Do not modify transport merely because the stall did not reproduce.

## 27.2 Probe reproduces a late sequential stall

If the fictional sequence reproduces a materially similar stall:

```text
sequential_same_namespace_stall_reproduced = 1
```

Preserve exact evidence.

Do not retry.

Do not repair shared transport in this task.

Classify whether evidence supports:

```text
state namespace correlation
CLI/runtime correlation
other transport lifecycle correlation
```

Next scope should be a dedicated transport/runtime diagnostic or repair task.

Do not select a new real holdout yet.

## 27.3 Probe stalls on the first or second invocation

This is not the same historical pattern.

Record exact batch position and evidence.

Do not force it into:

```text
batch03 sequential-state failure
```

Use:

```text
FICTIONAL_TRANSPORT_STALL_REPRODUCED_DIFFERENT_POSITION
```

or repository equivalent.

No retry.

---

# 28. No timeout tuning from this task

The historical observation:

```text
two batches ≈ 155 sec
third batch = 1800 sec timeout
```

does not justify changing timeout to 3600 seconds.

This task must report:

```text
timeout_increase_this_task = 0
```

If later evidence supports a timeout policy review, propose it as a separate task.

Do not modify timeout while transport root cause remains unresolved.

---

# 29. No architecture repair in this task

If recovered partial output reveals:

```text
Directional Core technical/price ownership violation
supply ownership violation
BUY/SELL without material non-price anchor
source-sufficiency violation
hard-safety semantic defect
```

then:

```text
STOP semantic mutation
```

Do not patch the architecture against the exposed eight.

Preserve the evidence.

Recommended next lifecycle:

```text
generic architecture repair
→ freeze generically
→ select completely new issuer-level holdout
→ fresh FIRST/A/B/C proof
```

No current-cohort reuse.

---

# 30. No new real holdout in this task

Even if:

```text
partial recovered output is clean
AND
fictional sequential probe passes
```

do not select or invoke a new real holdout inside this same task.

End with a handoff.

Reason:

- forensic conclusions must be frozen before new real evidence is exposed;
- new holdout selection must have its own precommitted exclusion set and source lock;
- the old 16-subject cohort is already retired.

---

# 31. Next-scope decision matrix

## Case A — Partial semantic defect confirmed

If provenance-linked recovered output confirms an architecture/ownership/hard-safety semantic defect:

```text
readiness =
NOT_READY_SEMANTIC_REPAIR_REQUIRED

next_scope =
GENERIC_ARCHITECTURE_REPAIR_THEN_NEW_ISSUER_HOLDOUT
```

Transport forensic result should still be reported separately.

Do not let a clean fictional transport probe erase the semantic defect.

## Case B — Partial directional output clean + probe passes

If:

```text
partial_output_semantic_audit_status =
CLEAN_ON_RECOVERED_DIRECTIONAL_CORE

fictional sequential probe =
PASS / NOT_REPRODUCED
```

then preserve architecture unchanged.

Possible readiness:

```text
READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_AND_OWNERSHIP_PROOF
```

provided no other transport integrity blocker is found.

The next real holdout must:

- exclude all 16 retired partial cohort issuers;
- exclude all consumed regression issuers;
- use a new source lock;
- include precommitted exact raw-output preservation;
- apply per-run semantic gates after FIRST/A/B/C.

## Case C — Partial outputs unrecoverable + probe passes

If:

```text
partial_output_provenance_gap = UNRESOLVED
fictional sequential probe = PASS
```

do not falsely mark the old partial outputs clean.

Use:

```text
partial_output_semantic_audit_status = NOT_MEASURED
ownership_generalization_verdict = NOT_MEASURED
```

The next-scope recommendation may still be a new issuer holdout only if transport review finds no remaining blocker, but it must explicitly carry forward:

```text
historical partial-output provenance gap
```

and must precommit exact raw-output preservation before any new real call.

## Case D — Fictional sequential stall reproduced

If the fictional sequential probe reproduces a transport stall:

```text
readiness =
NOT_READY_TRANSPORT_BLOCKED

next_scope =
BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR
```

Do not select a new real holdout.

## Case E — Strong evidence of historical CLI/runtime/state defect without probe reproduction

If static forensic evidence itself confirms a transport/runtime defect:

```text
next_scope =
appropriate bounded transport/runtime repair
```

Do not skip directly to new issuer proof merely because one fictional probe happened to pass.

---

# 32. Per-context evidence preservation policy — new required rule

Create a reusable experiment-harness rule for future ownership-proof tasks:

After every successful real or fictional model context:

```text
persist exact raw model output immediately
persist transport receipt immediately
persist stdout/stderr evidence immediately or safe redacted derivative
hash each artifact immediately
associate generation/invocation/stage/batch/subjects immediately
```

Do not wait for the entire FIRST run to succeed before preserving earlier successful contexts.

This is an **experiment evidence-preservation requirement**, not an investment semantic change.

It exists specifically to prevent another case where:

```text
subject_output_count > 0
but exact successful model outputs are absent from the result bundle
```

If implementing this rule requires shared production transport changes:

```text
STOP
```

Keep it experiment-only and request a separate broader change if needed.

---

# 33. Optional offline early semantic gate for future runs

This task may specify, document, or implement an experiment-only orchestration hook that allows:

```text
successful context output
→ immediate exact preservation
→ offline context-applicable semantic validation
```

before the next expensive context is launched.

However:

- do not change Directional Core semantics;
- do not weaken validators;
- do not apply full Price-Timing gates before Price-Timing exists;
- do not call this a complete per-run gate when the full stage/run is incomplete.

Use a distinct status such as:

```text
PER_CONTEXT_PARTIAL_SEMANTIC_AUDIT
```

This hook is allowed only if it is experiment-only and semantic-neutral.

If it requires broad runtime redesign:

```text
document recommendation only
```

Do not widen scope.

---

# 34. Historical partial-output state remains retired regardless of recovery

Recovering the missing eight outputs does not make the old cohort reusable.

Even if all recovered outputs are clean:

```text
holdout_output_exposure_state =
PARTIALLY_EXPOSED

holdout_retirement_state =
RETIRED_PARTIAL_EXPOSURE

future_unseen_holdout_reuse_allowed =
0

same_cohort_architecture_tuning_rerun_allowed =
0
```

If a semantic defect is found, retirement may strengthen to:

```text
RETIRED_FOR_ARCHITECTURE_REPAIR
```

It must never revert to:

```text
ACTIVE_UNEXPOSED
```

---

# 35. Required machine-readable artifacts

Produce Markdown plus JSON evidence for at least:

```text
01-repository-provenance
02-latest-result-bundle-integrity
03-prior-run-fact-reconstruction
04-partial-output-provenance-gap
05-partial-output-recovery-search
06-recovered-batch01-provenance
07-recovered-batch02-provenance
08-recovered-output-artifact-manifest
09-offline-schema-validation
10-offline-directional-ownership-validation
11-offline-partial-hard-safety-validation
12-partial-semantic-audit-summary
13-batch03-log-recovery
14-batch03-lifecycle-forensics
15-batch01-02-03-comparison
16-transport-root-cause-classification
17-historical-pre-first-freeze-audit
18-fictional-probe-precommit
19-fictional-probe-batch01
20-fictional-probe-batch02
21-fictional-probe-batch03
22-fictional-probe-sequence-summary
23-retired-cohort-proof
24-real-issuer-no-model-call-proof
25-evidence-preservation-policy
26-production-no-change
27-night-futures-no-change
28-next-scope-decision
29-program-completion
```

If recovered exact outputs exist, include them under:

```text
recovered-real-output/
```

If raw batch03 logs exist, include safe raw/redacted evidence under:

```text
recovered-transport-forensics/
```

If fictional probe outputs/logs exist, include them under:

```text
fictional-sequential-probe/
```

No secret-bearing raw command material may be exposed.

---

# 36. Required partial-output provenance fields

For batch01 and batch02 independently report:

```text
generation_id
invocation_id
stage
batch_id

recovery_status
original_artifact_identity
copied_artifact_path

raw_output_sha256
raw_output_bytes

receipt_output_bytes
receipt_stdout_bytes

prompt_sha256
schema_sha256

subject_count
subjects

schema_revalidation_status
offline_validator_status

secret_exposure_count
```

If not recovered:

```text
raw_output_sha256 = NOT_AVAILABLE
raw_output_bytes = NOT_AVAILABLE
schema_revalidation_status = NOT_MEASURED
offline_validator_status = NOT_MEASURED
```

Do not fill missing hashes with hashes of reports or normalized reconstructions.

---

# 37. Required batch03 forensic fields

Report:

```text
generation_id
invocation_id

input_bytes
prompt_sha256
schema_sha256

state_namespace_hash
working_directory_identity

cli_version
cli_binary_sha256

stdin_complete

first_stderr_seconds
last_stderr_seconds
stderr_bytes
stderr_burst_duration_seconds
silent_interval_before_exit_seconds

first_stdout_seconds
stdout_bytes

output_file_created
output_parsed
parse_error

elapsed_to_exit_seconds
exit_code

termination_initiator
termination_signal

timeout_owner
timeout_owner_count

child_cleanup_status
orphan_model_process_count

network_probe_attempts
network_resolved_address_count
request_accepted_observability

raw_stderr_recovery_status
raw_transport_log_recovery_status

root_cause_classification
root_cause_confidence
confirmed_facts
inferred_hypotheses
unknowns
```

Do not express confidence as a probability unless the system already defines that semantics.

---

# 38. Required fictional probe fields

For each fictional probe invocation report:

```text
probe_generation_id
invocation_id
stage
probe_batch_id

fictional_subject_count
fictional_subject_ids
market_mix

real_issuer_identity_count

state_namespace_hash
same_namespace_sequence_position

model
reasoning_effort
configured_timeout_seconds
timeout_owner_count

input_bytes
prompt_sha256
schema_sha256

first_stderr_seconds
last_stderr_seconds
stderr_bytes

first_stdout_seconds
stdout_bytes
output_bytes

elapsed_to_exit_seconds
exit_code
status

termination_initiator
child_cleanup_status
orphan_model_process_count

raw_output_artifact_path
transport_receipt_path
log_artifact_path

secret_exposure_count
```

Required:

```text
real_issuer_identity_count = 0
```

for every probe batch.

---

# 39. Program-completion object

The final machine-readable completion object must include at least:

```text
base_sha
work_instruction_commit
implementation_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_bundle_integrity

runner_adapter_repair_status

new_real_issuer_model_call_count
fictional_probe_model_call_count

retired_holdout_cohort
exposed_subjects
unexposed_but_retired_subjects

holdout_output_exposure_state
holdout_semantic_revelation_state
holdout_retirement_state
future_unseen_holdout_reuse_allowed
same_cohort_architecture_tuning_rerun_allowed

prior_bundle_exact_partial_output_files_present
partial_output_provenance_gap

batch01_recovery_status
batch02_recovery_status
recovered_real_subject_output_count

partial_output_semantic_audit_status

directional_core_price_technical_refs
directional_core_supply_refs
supply_directional_core_usage
buy_without_nonprice_material_anchor
sell_without_nonprice_material_anchor
directional_model_calls_on_source_insufficient
price_only_directional_model_calls
final_direction_owner

timing_stage_direction_mutation
timing_stage_balance_mutation
timing_stage_hold_lean_mutation
price_timing_new_buyer_upgrade
price_only_holder_reduce
price_only_directional_ownership_violations

primary_user_action_wording_owner
ai_imperative_primary_action

known_hard_safety_regression

batch03_root_cause_classification
batch03_raw_stderr_recovery_status
batch03_raw_transport_log_recovery_status

historical_pre_first_implementation_freeze_proof

fictional_probe_status
fictional_probe_sequence_completed
fictional_probe_timeout_count
sequential_same_namespace_stall_reproduced

timeout_increase_this_task
transport_topology_mutation
model_semantic_input_drift
architecture_semantic_drift

main_merge
production_db_mutation
production_scheduler_change
production_telegram_send
monitoring_registration_calls
live_structured_autonomy_activation
live_v2_change
night_futures_code_mutation

readiness
stop_reason
next_scope
```

Anything not actually measured must remain:

```text
NOT_MEASURED
```

Do not convert lack of recovered artifacts into PASS.

---

# 40. Production no-change proof

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
```

This task is forensic and diagnostic only.

---

# 41. Hard-stop rules

Stop implementation/execution if:

```text
latest result bundle checksum mismatch
unexplained semantic repository drift
shared adapter/transport topology must change
model/context semantics must change
timeout increase appears required for the probe
real issuer model call becomes necessary
new real holdout selection becomes necessary
```

During the fictional probe:

```text
first probe timeout/failure
→ preserve evidence
→ no retry
→ stop remaining probe invocations if continuing would no longer answer the precommitted diagnostic question safely
```

If the intended sequential position itself is required to test batch03 behavior, a failure before that position ends the probe and must not be worked around.

---

# 42. Artifact integrity

Create a final artifact index containing:

```text
relative path
SHA-256
byte size
artifact class
historical vs newly generated
secret-scan status
```

Verify all bundle files.

Report:

```text
artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
```

Expected mismatch counts:

```text
0
0
```

Also report final ZIP SHA-256.

Recovered historical exact outputs must be distinguishable from newly generated fictional probe outputs.

---

# 43. Task success criteria

This task is successful as a forensic review if it does all possible bounded work without violating experiment integrity.

Minimum required success:

```text
latest result bundle integrity confirmed

current 16-subject cohort retirement preserved

new_real_issuer_model_call_count = 0

partial-output recovery attempted with explicit provenance result

batch03 lifecycle forensic completed

timeout not increased

fictional sequential probe executed according to precommit
or stopped cleanly at its first precommitted failure

all new diagnostic outputs/logs preserved with hashes

production no-change proven

next blocker classified without overclaiming
```

Exact historical output recovery is desired but cannot be guaranteed.

Therefore:

```text
OUTPUT_NOT_FOUND
```

is a valid forensic result if the search was thorough and provenance-safe.

Do not fabricate recovery success.

---

# 44. Architecture decision after partial audit

If the eight recovered Directional Core outputs reveal a hard semantic defect:

```text
do not repair here
do not run new real issuers here
```

Next scope:

```text
GENERIC_ARCHITECTURE_REPAIR
```

followed later by:

```text
NEW_ISSUER_HOLDOUT_SELECTION_AND_OWNERSHIP_PROOF
```

If recovered partial Directional Core is clean:

```text
architecture remains frozen
```

unless independent evidence says otherwise.

---

# 45. Transport decision after forensic probe

If the fictional same-namespace sequence reproduces a stall:

```text
NOT_READY_TRANSPORT_BLOCKED
```

and next scope is a bounded transport/runtime diagnostic repair.

If the probe passes and no confirmed transport defect remains:

```text
historical batch03 stall =
not reproduced under bounded fictional probe
```

Do not call it "fixed" unless a specific root cause was confirmed and repaired.

The appropriate next step may then be:

```text
NEW_ISSUER_HOLDOUT_SELECTION_AND_OWNERSHIP_PROOF
```

with enhanced mandatory per-context evidence preservation.

---

# 46. Requirements for the future new issuer holdout

This task does not select the new holdout, but its handoff must precommit these constraints.

The future unseen issuer cohort must exclude:

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

It must use:

```text
new issuer set
new source generation
new source lock
same frozen investment architecture unless generic repair was separately authorized
same per-run FIRST/A/B/C gates
```

It must preserve exact model outputs **per successful context immediately**, not only after full FIRST success.

---

# 47. Final task principle

The runner↔adapter defect is closed.

The old 16-subject holdout is retired.

The immediate value is in preserving and auditing evidence already paid for before exposing any new real issuers.

Therefore the correct sequence is:

```text
recover
→ preserve
→ validate offline
→ investigate the 1800-second stall
→ probe transport only with fictional subjects
→ freeze the forensic conclusion
→ choose the next task
```

Not:

```text
increase timeout
→ rerun old cohort
```

Not:

```text
continue only the unexposed eight
```

Not:

```text
immediately select new real issuers before understanding/preserving the partial evidence
```

And not:

```text
tune architecture against partially exposed real output
```

Preserve experiment integrity first.
