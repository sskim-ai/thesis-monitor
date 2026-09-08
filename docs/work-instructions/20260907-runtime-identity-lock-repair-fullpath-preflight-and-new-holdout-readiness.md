# Thesis Monitor — Runtime Identity Lock Repair, Whole-Path Preflight & New Holdout Readiness

**Task date:** 2026-09-07  
**Scope:** bounded experiment identity-binding repair; model-free whole-path validation; dual-market unseen-universe feasibility; conditional new-issuer ownership proof.  
**Production:** no change.

Suggested result bundle:

```text
thesis-monitor-20260907-runtime-identity-lock-repair-fullpath-preflight-new-holdout-report.zip
```

## 0. Immediate decision

The pre-spawn guard repair succeeded in the latest reported execution. The first real US context then returned four outputs successfully, but runtime identity validation rejected them because the prompt and validator expected a new runtime ID while the supplied JSON Schema still required the old source-generation ID.

This is an experiment identity-binding failure, not evidence of a model timeout or an investment-architecture defect.

Do not fix one constant and immediately spend another unseen real cohort. The next sequence is:

```text
preserve historical evidence and retire the complete exposed cohort
→ prove identity-binding root cause across ALL paths
→ repair identity binding generically
→ run whole-path model-free FIRST/A/B/C rehearsal
→ audit untouched US AND KR universe feasibility
→ only if both targets and every preflight pass:
   select a genuinely new cohort
   freeze new source and runtime identities
   execute gated FIRST/A/B/C
```

The known small US universe may prevent new-cohort construction after the latest four US exposures. This is a conditional proof task, not a promise that new real-model execution will occur.

No production activation, legacy monitoring message change, or Monitoring Bootstrap work is authorized.

---

## 1. Sources of truth and review boundaries

### 1.1 Latest measured result

```text
thesis-monitor-20260907-prespawn-live-workload-guard-compatibility-holdout-proof-resume-report.zip

SHA-256:
083599be551a40ab62941a26168482ebd18de6856b6090eecb979767d5bdbfb6
```

Recompute before use. Stop on mismatch.

Load, at minimum:

```text
reports/proofs/54-program-completion.json
reports/runtime-identity-failure-forensic.json
reports/proofs/13-model-free-prespawn-guard-preflight.json
reports/proofs/16-model-semantic-input-freeze.json
reports/proofs/19-resume-runtime-precommit.json
reports/proofs/21-first-execution-summary.json
reports/proofs/45-holdout-exposure-retirement-state.json
experiment/program-state.json
experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-01/*
experiment/schemas/*
experiment/frozen-source-precommit.json
experiment/source-lock.json
```

Historical experiment facts are governed by these files, not older summaries.

### 1.2 Current code

Current repository HEAD/worktree governs actual implementation. The uploaded ZIP is evidence, not a complete source-code checkout.

Inspect current code before claiming the exact fix. Record differences from the reported baseline. Do not silently substitute historical report assertions for current code inspection.

### 1.3 Predecessor source/universe evidence

Use the predecessor only where the latest result has not superseded it:

```text
thesis-monitor-20260907-us-price-context-gate-supported-universe-remediation-holdout-proof-resume-report(1).zip

SHA-256:
fd519905d0201d5742d1c1b90c9b3e15b681020d05ad23a4031734a98eb73c68
```

Relevant files:

```text
reports/proofs/05-price-context-gate-classification.json
reports/proofs/15-us-supported-universe-root-cause.json
reports/proofs/69-program-completion.json
```

Do not treat its former unseen-cohort permission as current.

### 1.4 Normative semantics

Use the Investment Thesis Analysis & Monitoring Knowledge Guide and frozen repository investment/safety contracts. Older START_HERE and FULL SYSTEM PROMPT provide background only where they do not conflict with newer results or this instruction.

This instruction authorizes bounded execution-identity changes, not business schema/decision-policy changes.

---

## 2. Established result baseline

### 2.1 Successful repair and execution

The latest result reports:

```text
guard preflight = PASS
workload observation =
LAUNCHCTL_JOB_STATE_PLUS_LSOF_CODEX_RUNTIME_STATE
ps dependency after repair = false
fail-open added = 0
root exception masked after repair = 0
pre-spawn receipt incorrectly expected = 0

full tests = PASS
Ruff = PASS
diff check = PASS

model = gpt-5.6-sol
reasoning_effort = xhigh
batch_semantics = MODEL_CONTEXT_COUPLED
shared_context_subject_count = 4
timeout_seconds = 1800
timeout_owner_count = 1
```

First real context:

```text
stage = DIRECTIONAL_CORE
batch = 01
subjects = NVDA, JPM, WMT, BRK-B

model invocations = 1
raw subject outputs = 4
transport status = PASS
elapsed_to_exit_seconds = 127.288596
output bytes = 15654
stdout bytes = 15655
exit code = 0
retry count = 0
timeout count = 0
orphan model processes = 0

raw output SHA-256 =
53f66341319d9e4577cc98b88135f80188ca0add2bca38b32b34fe0cd9859cfb
```

Exact raw output, prompt, schema, stdout/stderr and receipt are present in the latest ZIP. Do not recreate the previous missing-output provenance gap.

### 2.2 Identity failure

```text
source_generation_id =
20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a

expected runtime_generation_id =
20260907-prespawn-guard-resume-20260907T012700Z-1f19aa40aef6

prompt IDENTITY.packet_id = runtime_generation_id
runtime validator expects = runtime_generation_id
receipt generation_id = runtime_generation_id

supplied schema properties.packet_id.const = source_generation_id
actual model output packet_id = source_generation_id

failure_class =
RUNTIME_GENERATION_SCHEMA_CONST_MISMATCH

FIRST =
FAILED_IDENTITY_GATE_0/16
A/B/C =
NOT_RUN
```

The prompt told the model to match the new identity; the constrained output schema required the old identity. Do not describe this as the model inventing an ID or ignoring a consistent contract.

Independent inspection of the uploaded bytes found:

```text
core-batch-01..04 schema packet_id.const = source_generation_id
timing-batch-01..04 schema packet_id.const = source_generation_id

affected bundled stage/batch schemas = 8
```

Batch01 raw output validates against the exact supplied (old-ID) JSON Schema. This does NOT make it valid against the expected runtime identity or establish ownership safety.

### 2.3 Measurement status

The per-context audit stopped at identity checking with no candidate semantic rows accepted:

```text
model_candidate_semantics_reviewed = 0
model_semantic_candidate_audit = NOT_MEASURED_IDENTITY_GATE
FIRST ownership / renderer / hard-safety gates = NOT_MEASURED
ownership_generalization_verdict = NOT_ESTABLISHED
```

Several aggregate violation counters in the report are zero. They are not proof of clean investment semantics when the audit never reached those checks.

Do not convert the existing four outputs into a valid FIRST by rewriting packet_id.

---

## 3. Historical artifact integrity

The latest ZIP has 182 entries. Its internal index covers 177 entries; verification of those indexed entries found no SHA-256 or size mismatch.

The five entries outside that internal index are:

```text
reports/README.md
reports/54-program-completion.md
reports/proofs/54-program-completion.json
reports/artifact-index.json
reports/artifact-index.md
```

Record this scope precisely. Do not claim that the internal index independently authenticated all 182 entries. The outer ZIP checksum covers the complete delivered archive.

The latest bundle reports secret scans PASS; this does not remove the obligation to scan newly produced artifacts.

---

## 4. Latest cohort is now retired in full

The earlier permission to reuse this cohort was valid BEFORE the latest model call. It is no longer an authorization to replay it.

Retire all 16:

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

State:

```text
holdout_output_exposure_state = PARTIALLY_EXPOSED
holdout_semantic_revelation_state = NOT_MEASURED_IDENTITY_GATE
holdout_retirement_state = RETIRED_PARTIAL_EXPOSURE
future_unseen_holdout_reuse_allowed = 0
```

The first four produced investment outputs. The remaining KR12 did not run, but are still retired with the precommitted cohort under the existing experiment policy.

Forbidden:

```text
repair identity and rerun these US4
continue only the old KR12
reuse the old source lock as a new proof
relabel historical output with the corrected runtime ID
claim corrected copies as accepted model output
```

Keep original artifacts immutable and available as forensic/regression history. Do not re-call the model on any issuer in a retired cohort during this task.

### Other mandatory exclusions

Previous retired partial cohort:

```text
ORCL, UNH, KO, AVGO,
095570, 058860, 246960, 099520,
403870, 014790, 079810, 060980,
061970, 012030, 225190, 245620
```

Previous consumed regression cohort:

```text
PLTR, V, MA, AMZN, XOM, DIS, NKE, MCD,
033920, 104480, 071320, 096240,
032860, 060570, 016600, 462520
```

These three lists are minimum exclusions, not the complete current registry. Union them with all additional recorded exposures and cohort-retirement exclusions.

Deduplicate and exclude at issuer level, including alternate listings, share classes and ADR/ordinary aliases. Do not reintroduce BRK-B via BRK-A or another alias.

Record actual-output exposure separately from cohort-policy retirement. Do not falsely report that the uncalled KR12 produced model output.

---

## 5. Repository provenance and commit order

Latest reported repository facts:

```text
base_sha =
eced7b9149e7d9ab7cbc5e3e3e6fab3fef1500d6

work_instruction_commit =
78d05fea9690753095e42e403f3677b6901627bb

implementation_commit =
e78926cf246d6336889eab5373ae7423383bbf14

final_head_sha =
0f3b8dbdead385b1a3706560096f4805ca9d2d2f

branch =
codex/20260907-prespawn-live-workload-guard-compatibility-holdout-proof-resume
```

Capture actual:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Audit later changes. Stop on unexplained investment, source-policy, identity-contract or transport drift. Do not reset, discard, merge or cherry-pick unrelated work.

Required order:

```text
commit this work instruction
→ root-cause audit and bounded repair
→ focused/full tests + lint + whole-path model-free rehearsal
→ commit implementation
→ record implementation freeze and UTC timestamps
→ new candidate/source precommit, if feasible
→ final concrete runtime binding lock
→ first real spawn, only if permitted
```

Record implementation/freeze commits and final runtime precommit timestamps before any real spawn. Do not use a later final commit as the only proof of pre-run freeze.

If a mandatory preflight fails, do not invoke a real model. A failing negative regression deliberately rejecting bad identity is an expected test, not permission to bypass the real gate.

---

## 6. Allowed scope

Allowed, subject to actual code inspection:

```text
experiment-only runtime identity binding/construction
experiment-only prompt IDENTITY serialization
experiment-only schema instantiation of existing identity constants
experiment-only validator expected-identity wiring
experiment context/receipt/manifest identity propagation
identity-readiness checks before spawn
model-free orchestration rehearsal and regression fixtures
measurement-aware summary/counter serialization
issuer exposure/retirement registry maintenance
outcome-independent dual-market universe/selection diagnostics
new source generation using unchanged supported pipeline
conditional new-cohort FIRST/A/B/C execution
```

Use one generic repair; no ticker/batch-specific exception.

A schema's execution-specific ID value is not required to remain byte-identical to a source-era instantiated schema. Binding the same existing field to the correct runtime value is explicitly authorized, with precise change evidence.

Do not change the public DecisionEvidencePacket meaning, add a second accepted identity, relax schemas, or change investment thresholds to achieve this repair.

---

## 7. Forbidden scope

No change to:

```text
Directional Core decision semantics
Price-Timing semantics
deterministic composer semantics
renderer/action ownership
BUY/HOLD/SELL thresholds, balance, HOLD lean
new-buyer / holder transition rules
business invalidation meaning

source-sufficiency policy and required evidence families
official data attribution or freshness/safety validators
price-context UNAVAILABLE_SAFE contract
production market enum (kr | us)
source packet identity semantics

model = gpt-5.6-sol
reasoning effort = xhigh
shared-context grouping = MODEL_CONTEXT_COUPLED
context subject count = 4
timeout = 1800 seconds
timeout owner count = 1

canonical ContinuationTransportAdapter API
subprocess lifecycle and process-group cleanup
validated workload guard observation / fail-closed semantics
production scheduler, DB, Telegram, registrations
live V2 / Structured Autonomy activation
Night Futures
```

Do not add retries, split batches, remove an identity const, allow both old/new IDs, catch identity mismatches as warnings, or change old raw output.

No broad supported-universe/provider/source expansion is authorized here. Diagnose infeasibility and propose a separate bounded coverage task if necessary.

---

## 8. Phase A — Reproduce the binding failure without model calls

Inspect the actual code path from source freeze to resumed FIRST:

```text
source precommit
→ runtime generation creation
→ prompt construction/substitution
→ schema file choice
→ adapter arguments / actual schema path
→ validator expected packet_id
→ receipt / context manifest
```

Identify the functions/files responsible for each field.

Prove the current mismatch using the archived prompt/schema and expected identity, without any external model invocation. Restrict the historical regression to identity/provenance data; do not tune against the historical investment answers.

Required findings:

```text
root cause confirmed or not confirmed
prompt identity producer
schema identity producer
validator identity producer
adapter schema-path producer
normalization/freeze check that missed the mismatch
all affected stages/batches/runs
```

Audit BOTH Directional Core and Price-Timing. The eight retained source-era constants demonstrate that fixing only core batch01 is insufficient.

If actual code cannot support the stated root cause or required repair scope, stop rather than guess.

---

## 9. Phase B — Separate evidence identity from execution identity

Create or reuse a single immutable experiment binding object with explicit roles. Equivalent existing names are acceptable if mapped.

### Evidence identity: immutable source lineage

```text
source_generation_id
source_lock
per-issuer packet identity and hashes
issuer/evidence alias ownership
```

### Execution identity: current attempt and context lineage

```text
runtime_generation_id
run_id (FIRST / A / B / C)
stage
batch_id
invocation_id
ordered subject identities
output contract
```

For the current aggregate model-output contract, preserve the existing runtime-validator intent:

```text
model output packet_id = runtime_generation_id
```

Do not rename or rewrite source-level per-issuer packet IDs to achieve it.

The same binding must drive:

```text
prompt IDENTITY.packet_id
schema properties.packet_id.const
validator expected output packet_id
adapter invocation identity
receipt generation/invocation context
context manifest and artifact paths
```

Run/stage/batch and ordered-subject consistency must also be checked at their existing contract locations. Where not present in the model payload, prove them through the bound invocation/receipt/manifest rather than silently adding public model-schema fields.

Do not require all identity fields to have the same string. They have different roles; require the correct relationships.

---

## 10. Runtime-bound schema/prompt copies and hash discipline

Treat source-era schemas/prompts as immutable historical artifacts/templates, not ready-to-use resumed requests.

Build concrete runtime prompt and schema copies through the same binding object.

Allowed mutation examples:

```text
schema JSON Pointer /properties/packet_id/const
prompt's dedicated IDENTITY.packet_id value
experiment-side expected runtime identity and context metadata
```

Report the precise JSON paths/structured prompt fields actually modified. Do not globally replace source IDs throughout evidence, citations or arbitrary text.

Maintain both:

```text
raw_runtime_prompt_sha256
raw_runtime_schema_sha256

identity-normalized_prompt_semantic_hash
identity-normalized_schema_semantic_hash

identity_binding_lock_hash
```

Normalization may remove ONLY audited execution-binding fields. It must not ignore issuer lists, aliases, evidence values, thresholds, required properties, enums, security basis or other semantic content.

Required distinction:

```text
authorized_runtime_identity_binding_change = 1, if changed
investment_schema_semantic_change = 0
decision_prompt_semantic_change = 0
historical_source_artifact_mutation = 0
```

An identity-normalized hash PASS is necessary where used, but not sufficient. Explicit equality checks between actual prompt, actual schema and validator are mandatory.

For a new cohort, evidence/source hashes legitimately differ from the retired cohort. Report a new source generation, not "historical source unchanged." Within its locked FIRST/A/B/C proof, source drift must be zero.

---

## 11. Pre-spawn actual-request identity gate

Immediately before the terminal model-spawn boundary, inspect the actual serialized request and actual schema file that the adapter will receive, not a separate preview object.

Required checks:

```text
prompt IDENTITY.packet_id == bound runtime_generation_id
actual schema packet_id.const == bound runtime_generation_id
validator expected packet_id == bound runtime_generation_id

output contract consistent with stage
ordered tickers and schema subject constraints consistent
aliases remain issuer-fenced
source lock and packet hashes match precommit
run/stage/batch/invocation context matches manifest
actual prompt/schema hashes match runtime binding lock
```

If the adapter consumes a path, reopen the file at that path and verify it. Passing checks on an in-memory schema while sending a stale file is not sufficient.

Required error:

```text
PRESPAWN_RUNTIME_IDENTITY_BINDING_MISMATCH
```

or canonical equivalent.

On that failure:

```text
spawn_started = 0
transport_receipt_expected = 0
real_model_invocations = 0
```

Preserve prompt/schema/context and primary mismatch evidence. Do not mask it with missing-receipt or output-preservation errors.

Do not add another model watchdog.

---

## 12. Whole-path model-free FIRST/A/B/C rehearsal

This gate must exercise the actual proof orchestration, not only helper unit tests.

Use fictional schema-valid US4/KR12 fixtures and a controlled model substitute at the terminal invocation boundary. Preserve real request construction, schema binding, guard-decision interfaces, parsing, identity validation, per-context persistence, composer/renderer routing and run advancement.

Do not use a second simplified runner that avoids the repaired path.

Required coverage:

```text
new source generation != new runtime generation
fresh execution
resumed execution with a different runtime generation
FIRST, A, B, C
all four core batches
all timing batches according to frozen runner
renderer/composer boundary
available price path
UNAVAILABLE_SAFE price path
explicit pre-spawn failure path
post-spawn receipt failure path in simulated lifecycle
```

Dynamic Price-Timing prompts may depend on core output. Use fictional upstream core fixtures to exercise that construction. Later, on real execution, the actual dynamically constructed timing request must pass the same pre-spawn gate.

Do not claim future dynamic prompt bytes were already frozen before their upstream inputs existed. Precommit the template/builder, binding rules and schema, then lock the concrete derived request before its actual spawn.

Model-free artifacts must be clearly separated:

```text
artifact_mode = MODEL_FREE_SIMULATION
real_model_call_count = 0
simulated_invocation_count = measured separately
```

Simulated receipts/output are test fixtures, not proof of real transport or real investment safety. Never include them in real holdout counts.

No new seven-canary rerun or model-backed fictional probe is required here if canonical transport is unchanged. The latest real transport succeeded; this defect can be demonstrated and tested without a live model.

---

## 13. Negative and regression tests

Include at least:

```text
old source ID remains in schema while prompt uses runtime ID → blocked pre-spawn
schema uses runtime ID while prompt uses source ID → blocked pre-spawn
validator expected ID differs → blocked pre-spawn
in-memory schema correct but adapter path points to old file → blocked
core schemas corrected but timing schemas stale → blocked
FIRST path correct but A/B/C/resume path stale → blocked
wrong output contract/stage → blocked
wrong subject order/set or foreign issuer alias → rejected under frozen contracts
cross-context or cross-run receipt/manifest swap → rejected
unexpected model-output ID → rejected without rewriting output
missing/corrupt binding lock or schema file → blocked
normalization hides a non-ID semantic change → rejected
source/evidence IDs accidentally overwritten → rejected
guard observation unavailable → fail-closed, no model call
pre-spawn identity failure → no expected transport receipt and no root-error masking
successful output preservation fails → no later context launch
positive runtime != source case → all paths consistent
```

Cross-run provenance tests must use actual receipt/manifest/invocation lineage. Do not claim the unchanged aggregate payload alone can detect cross-run provenance when its schema has no run field.

Run focused tests, full suite, Ruff and repository diff checks. Preserve test commands/results. Do not fabricate test counts or execute live providers/models as an accidental side effect of the model-free suite.

If whole-path compatibility cannot be proven within experiment scope, stop before new real exposure.

---

## 14. Reporting: separate counters from measured semantic verdicts

Correct generic reporting so it distinguishes:

```text
request attempts
successful process spawns / real invocations
transport-completed contexts
identity-valid contexts
raw subject outputs
identity-accepted subject outputs
semantically audited subject outputs
violations observed among audited outputs
```

Historical latest case, reconstructed from the bundle:

```text
real model invocations = 1
transport-completed core contexts = 1
identity-valid contexts = 0
raw subject outputs = 4
identity-accepted subject outputs = 0
investment candidate semantics audited = 0
```

Do not present accepted-context counts as though no transport call occurred. Document any legacy counter-name mapping rather than rewriting historical records.

Each hard-gate record must have:

```text
status
applicability
audited_context_count
audited_subject_count
observed_violation_count, only where actually measured
reason_not_measured, when applicable
```

If identity prevents semantic evaluation:

```text
status = NOT_MEASURED_IDENTITY_GATE
```

Zero-initialized counters must not turn this into PASS.

Preserve known raw counts; do not replace real numeric facts with NOT_MEASURED merely because a later gate failed.

Separate a pre-run `reuse_allowed` decision from final `future_unseen_reuse_allowed`. The former must never overwrite the latter after exposure.

---

## 15. Mandatory dual-market unseen-universe feasibility audit

Perform this before any new real model call. It may run alongside bounded offline repair work, but cannot authorize model execution until repair/preflight are frozen.

The predecessor reported:

```text
canonical_us_universe_pre_filter_count = 33
canonical_us_universe_post_exposure_count = 5
unexposed supported US candidates = NVDA, JPM, WMT, BRK-B, MSFT
supported_universe_expansion_applied = 0
expanded_us_reserve_count = 0
```

The latest run exposed the first four.

Therefore, IF that security master and other exclusions are unchanged, the remaining supported unseen US pool is at most MSFT alone. This is a conditional inference to verify, not a newly measured current-universe count.

Audit the actual current canonical universe and exposure/retirement registry.

For BOTH US and KR record:

```text
raw supported-security count
canonical issuer count
share-class/alias dedup exclusions
actual-output exposure exclusions
whole-cohort retirement exclusions
other existing canonical exclusions
remaining unseen supported issuer count
required target
target feasibility
```

Do not stop the KR audit because US fails. Retired KR12 cannot be reused simply because no output was produced for them.

Do not invent securities, loosen listing/security validation, shrink the exclusion registry or change the target to fit availability.

### Feasibility failure

If either current universe cannot supply US4/KR12:

```text
new_holdout_cohort = NOT_CREATED
new_source_lock = NOT_CREATED
FIRST/A/B/C = NOT_RUN
new_real_model_call_count = 0
```

Complete both market reports, finish the bounded identity repair evidence, then stop.

Possible next scope:

```text
BOUNDED_SUPPORTED_UNIVERSE_EXPANSION_BEFORE_NEW_HOLDOUT
```

Use market-specific or dual-market wording based on measured counts.

A successful identity repair remains successful even when the separate unseen-universe gate fails.

No broad universe/source-provider expansion is authorized inside this repair task.

---

## 16. Conditional new-cohort selection and source coverage

Only if both unseen-universe targets are feasible:

1. Precommit deterministic selection rule, seed, primary order and bounded reserve order before source-result inspection.
2. Select 4 US and 12 KR canonical issuers, all outside the expanded exclusion set.
3. Use unchanged read-only source assembly and sufficiency/identity validation.
4. Replace pre-model objective failures only in the precommitted reserve order.
5. Complete bounded source diagnostics for BOTH markets even if the first market fails.
6. Freeze a new source generation and combined source lock only after both targets pass.

Permitted replacement reasons are identity/source/validation failures, not price trend, desired model direction, valuation appearance or preferred sector outcome.

Do not use any old retired issuer as a convenient diagnostic real-model call.

Maintain bounded provider/request budgets. A small exhausted universe is not justification for repeatedly retrying the same provider requests.

### Existing price/readiness contract remains

```text
Directional Core fundamental sufficiency
is separate from
Price-Timing price/technical readiness.
```

Safe absence of price uses the established `UNAVAILABLE_SAFE` path. It does not permit fabricated timing claims or imply that invalid/future price data is acceptable.

Do not reopen closed bank/insurer mapping or price-overcoupling repairs without direct new evidence. A broader repair requirement is a separate task, not permission to change rules during this one.

---

## 17. New source/runtime lock and freeze

The retired source generation and lock remain historical only:

```text
source generation:
20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a

source lock:
d4bd0b51d9cc543ebe03088047cce375db41d3d9a9f21c07d4fd5646bdf9b1ef
```

A genuinely new cohort requires a new source generation and lock.

Create a distinct runtime generation and a precommitted binding matrix for all FIRST/A/B/C contexts.

Runtime precommit must include:

```text
implementation/freeze commit
selection policy and exclusion registry hashes
new ordered cohort and issuer identities
new source generation and source lock
per-issuer packet hashes
runtime generation
run/stage/batch/invocation identity rules
concrete core prompt/schema hashes
timing template/schema/binding identities
model / effort / grouping / timeout
per-context evidence and semantic-gate policies
```

Before the first real call, verify the whole concrete core matrix and all timing schema bindings. Check dynamically assembled requests again at their actual pre-spawn boundary.

Across FIRST/A/B/C preserve source, architecture, grouping, model, effort and timeout. Keep run/invocation identities distinct under the predeclared convention; bind any permitted execution-ID differences precisely.

No implementation edits after real output begins. Report code freeze before FIRST and verify no unauthorized changes before later runs.

---

## 18. Preserve live monitoring and transport

Retain the repaired workload guard:

```text
LaunchAgent / launchctl state observation
lsof runtime-state observation
protected natural-run windows
fail-closed on unobservable workload
```

Inspect the existing canonical schedule policy at execution time. Do not hardcode yesterday's protected window as a future guarantee.

Before each heavy real context:

```text
check protected window
check workload observability and contention
check request identity binding
```

Production monitoring has priority. Do not cancel natural jobs, modify schedules, or assume that unavailable observation means zero contention.

A safe deferral before a new context is not a retry of an attempted model call. Follow the existing defer policy without starting a second competing watchdog.

Retain:

```text
gpt-5.6-sol / xhigh
MODEL_CONTEXT_COUPLED / 4 subjects
1800 seconds / one timeout owner
no automatic real-model retry
no batch splitting
no transport topology change
```

If another real silent stall occurs, preserve evidence and stop; the prior historical stall remains causally unresolved, not permanently fixed.

---

## 19. Conditional FIRST/A/B/C execution

Only execute real models after all earlier gates pass.

For every successful context, before the next:

```text
persist exact output bytes
persist exact prompt/schema used
persist stdout/stderr/log or safe redacted derivative
persist receipt and identity binding lock
persist subject/source/run/stage/batch mapping
hash and reopen-verify artifacts
run applicable offline context gates
```

If secret policy blocks exact raw bundling, keep original hash/provenance and clearly label redacted derivatives; do not silently edit a raw artifact. Stop if required safe evidence preservation cannot be satisfied.

Context order:

```text
preserve
→ schema and identity validation
→ applicable ownership/safety validation
→ next context only if required gates PASS
```

Before timing exists, timing-only gates remain NOT_MEASURED. Apply context-level timing checks once timing output exists, using frozen canonical validators.

Run sequence:

```text
FIRST → complete run ownership / renderer / hard-safety gates
A     → complete run ownership / renderer / hard-safety gates
B     → complete run ownership / renderer / hard-safety gates
C     → complete run ownership / renderer / hard-safety gates
```

No next run before all required previous-run gates PASS.

At the first unexpected real execution, identity, schema, preservation or hard semantic failure:

```text
STOP
no retry
no selective continuation
no same-task hotfix
no same-cohort tuning
```

Persist failed-context evidence even if output is invalid or partial. Do not preserve only successful outputs.

---

## 20. Frozen investment and renderer hard gates

Use the actual canonical validators and name mappings; do not invent looser gates.

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

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

Price-Timing may make entry views more conservative, not upgrade them. It may create price REVIEW pressure, not price-only REDUCE or business invalidation.

Preserve numeric provenance, accounting attribution, ADR/share basis, official provisional-earnings safety, issuer alias fencing, future-data rejection and Unknown handling.

No fabricated EPS/BVPS/FCF, unsupported technical indicator, target or stop. No one-quarter EPS annualization or reverse engineering of denominators from multiples.

Do not treat identity-gated, unexecuted or nonapplicable checks as measured zeros. Do not make an invented BUY/SELL distribution a success condition.

---

## 21. Exposure, retirement and proof state

Track separately:

```text
output exposure
semantic defect observation
retirement from unseen use
execution/proof completion
```

No cohort created:

```text
cohort_state = NOT_CREATED
proof_status = NOT_RUN
```

Created, no raw investment output:

```text
output exposure = UNEXPOSED
retirement = ACTIVE_UNEXPOSED
reuse requires a separately validated future decision after any failure
```

Any raw investment output before full FIRST completion, including identity-invalid output that contains actual investment decisions:

```text
output exposure = PARTIALLY_EXPOSED
future unseen reuse = 0
```

If stopped for nonsemantic identity/transport/preservation failure:

```text
retirement = RETIRED_PARTIAL_EXPOSURE
semantic verdict = NOT_MEASURED or explicit identity-limited status
```

A complete FIRST makes exposure FULLY_EXPOSED. The precommitted A/B/C repeats may continue only through their gates; they do not make the cohort unseen again.

An identity failure alone is not an investment-architecture defect. A confirmed investment/renderer/hard-safety semantic defect requires:

```text
REVEALED_FOR_ARCHITECTURE_TUNING
RETIRED_FOR_ARCHITECTURE_REPAIR
```

Preserve monotonic exposure across runs. If A fails after a complete FIRST, do not downgrade FULLY_EXPOSED to PARTIALLY_EXPOSED.

Retire the entire final cohort after partial proof failure, including uncalled members. Keep the exposure and cohort-policy reasons separate in the registry.

---

## 22. Stability and readiness decisions

Aggregate only valid completed runs that passed their own required gates.

Use frozen stability categories and thresholds. Do not declare generalization merely because a stability report was generated; apply the existing acceptance criteria.

If repeated-run evidence is insufficient:

```text
stability = NOT_MEASURED
ownership generalization = NOT_ESTABLISHED
```

Possible next scopes:

| Measured outcome | Next scope |
| --- | --- |
| Identity binding repair/preflight fails | BOUNDED_RUNTIME_IDENTITY_LOCK_REPAIR |
| Repair passes, US/KR unseen universe insufficient | BOUNDED_SUPPORTED_UNIVERSE_EXPANSION_BEFORE_NEW_HOLDOUT |
| Universe feasible, source target insufficient | Market-specific or dual-market bounded source coverage |
| Pre-spawn workload observation unavailable | Bounded guard/observability review |
| Real transport failure or historical stall recurrence | BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR |
| Real identity failure recurs | Bounded identity-control review; retire exposed cohort |
| Confirmed investment/renderer/hard-safety defect | Generic semantic repair, then a new issuer cohort |
| Frozen stability/generalization gate fails | Review that failure; no tuning on current cohort |
| FIRST/A/B/C and all canonical proof gates PASS | Monitoring Bootstrap Integration Review |

Monitoring Bootstrap and production rollout are not authorized in this task, even on success.

---

## 23. Required artifacts

Produce Markdown summaries plus machine-readable evidence. Preserve exact historical files; label newly derived diagnostics separately.

Minimum unconditional artifacts:

```text
01-repository-provenance
02-latest-result-integrity
03-historical-identity-mismatch-reproduction
04-historical-cohort-retirement-and-exposure-registry
05-identity-producer-consumer-dataflow
06-source-vs-runtime-identity-contract
07-all-stage-batch-run-binding-matrix
08-runtime-binding-allowlist-and-diff
09-actual-adapter-request-preflight
10-negative-regression-results
11-whole-path-model-free-rehearsal
12-test-lint-and-implementation-freeze
13-measurement-aware-counter-contract
14-us-unseen-universe-audit
15-kr-unseen-universe-audit
16-dual-market-feasibility-decision
17-production-no-change
18-program-completion
```

Conditional artifacts if a new cohort is feasible:

```text
new-selection-policy-and-reserve-order
new-us-source-audit
new-kr-source-audit
new-cohort-source-precommit
new-runtime-binding-lock
live-workload-coexistence-audit
```

Conditional execution artifacts for EACH FIRST/A/B/C:

```text
run-execution-summary
all-context-artifact-manifest
all-context-identity-and-semantic-gates
run-ownership-gate
run-renderer-gate
run-hard-safety-gate
```

Final conditional proof artifacts:

```text
holdout-exposure-and-retirement
core-stability
timing-stability
ownership-generalization
next-scope-handoff
```

Later runs are NOT_RUN when stopped; missing measurements are NOT_MEASURED. Do not fabricate placeholder PASS artifacts.

---

## 24. Program-completion and counter fields

At minimum include:

```text
base_sha
work_instruction_commit
implementation_commit
implementation_freeze_commit
final_head_sha
branch
implementation_freeze_utc
runtime_precommit_utc
first_real_spawn_utc

latest_result_zip_sha256
input_zip_entry_count
input_index_verified_count
input_unindexed_entries
input_hash_mismatch_count
input_size_mismatch_count

root_cause
root_cause_confirmed
identity_repair_status
authorized_runtime_identity_binding_change
historical_source_artifact_mutation

identity_binding_single_source
actual_request_identity_preflight
all_core_schema_binding_status
all_timing_schema_binding_status
all_run_binding_status
whole_path_model_free_rehearsal_status
model_free_real_model_call_count

full_tests
ruff
diff_check

investment_architecture_semantic_drift
investment_schema_semantic_drift
decision_prompt_semantic_drift
source_sufficiency_policy_drift
canonical_transport_mutation
guard_semantics_mutation
timeout_increase
unexpected_semantic_normalization_exclusions

prior_actual_output_exposure_registry_count
whole_cohort_retirement_exclusion_count
issuer_deduplicated_exclusion_count

us_supported_unseen_count
kr_supported_unseen_count
us_universe_target_status
kr_universe_target_status
both_market_audits_completed
new_universe_expansion_applied

new_cohort_state
new_ordered_cohort
new_source_generation_id
new_source_lock
new_runtime_generation_id
new_runtime_binding_lock_hash

new_real_model_invocation_count
transport_completed_context_count
identity_valid_context_count
raw_subject_output_count
identity_accepted_subject_output_count
semantically_audited_subject_output_count
simulated_invocation_count

identity_failure_count
evidence_preservation_failure_count
transport_timeout_count
transport_retry_count
historical_stall_pattern_recurred

run_results.FIRST
run_results.A
run_results.B
run_results.C
per_run_identity_gate_status
per_run_ownership_gate_status
per_run_renderer_gate_status
per_run_hard_safety_gate_status

hard_gate_measurement_records
core_stability_counts
timing_stability_counts
ownership_generalization_verdict
ownership_proof_completion_state

holdout_output_exposure_state
holdout_semantic_revelation_state
holdout_retirement_state
future_unseen_holdout_reuse_allowed

main_merge
production_db_mutation
production_scheduler_change
production_telegram_send
monitoring_registration_calls
live_structured_autonomy_activation
live_v2_change
night_futures_code_mutation

artifact_count
indexed_artifact_count
unindexed_entries_and_reasons
artifact_hash_mismatch_count
artifact_size_mismatch_count
secret_scan_status

repair_readiness
proof_readiness
stop_reason
next_scope
```

Use repository canonical names with an explicit mapping where necessary. No new enum should silently break an existing reader.

---

## 25. Output integrity and production no-change

Preserve real/simulated/historical artifacts in separate directories.

Each indexed artifact needs:

```text
relative path
SHA-256
byte size
artifact class
historical / newly generated / simulation
run / stage / batch, where applicable
secret-scan status
```

Finalize completion reports BEFORE calculating their index entries. The index need not hash itself; explicitly list intentional exclusions. Avoid publishing a final completion report that was silently changed after indexing.

Verify ZIP CRC, every indexed hash/size and final ZIP SHA-256. Report actual counts rather than equating ZIP entry count with index coverage.

Required production invariants:

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
natural_live_cancel_count = 0
```

The existing US/KR scheduled monitoring and its messages stay unchanged. This evidence does not itself prove future delivery success; do not report a production health check that was not performed.

---

## 26. Final task principle

The model returned the ID that the supplied schema required. The system supplied conflicting execution identities.

The repair must therefore align the entire request/validation chain before another real issuer is exposed:

```text
one binding
→ actual prompt
→ actual schema
→ validator expectation
→ receipt/manifest lineage
```

Correcting only one file or normalizing hashes is not enough.

The previous cohort is retired. A new cohort is possible only if current untouched supported issuer counts and source coverage actually permit it.

Do not trade away identity fencing, evidence safety, cohort retirement or production isolation to make the experiment proceed.

Repair and rehearse the complete path first.
Measure both markets' remaining unseen capacity.
Only then spend genuinely new real-model evidence.
