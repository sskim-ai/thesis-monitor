# Thesis Monitor — M12CE New Full22 Reproof Under Frozen Deterministic Maturity `as_of` Contract

## 0. Task identity

Suggested work-instruction filename:

`20260916-m12ce-new-full22-reproof-under-frozen-deterministic-asof-contract.md`

Suggested result bundle:

`thesis-monitor-20260916-m12ce-new-full22-reproof-under-frozen-deterministic-asof-contract-report.zip`

This is a **proof-only, no-repair, wholly new US14/KR8 Full22 model reproof** under the already implemented and offline-proven M12CD deterministic maturity-`as_of` contract.

It is NOT:

- a new architecture task;
- a maturity-`as_of` policy redesign;
- a prompt/schema repair task;
- a validator weakening task;
- a ticker/date exception task;
- a Fundamental Core redesign;
- a three-axis/preconfirmation/polarity redesign;
- a Treasury or Kiwoom implementation task;
- a production promotion/deployment task;
- a retry/repair/judge/fallback task.

The objective is singular:

> Exercise the frozen M12CD model-facing contract in a completely new Full22 generation from call 1, and prove that the model can produce all US14/KR8 outputs without model-authored maturity dates while the deterministic runtime materializer derives valid ticker-local same-row provenance dates and all previously frozen semantic contracts remain intact.

If the first new hard failure occurs, stop that generation immediately and return to Chat for architecture/scope review. Do not patch the generation.

---

## 1. Authoritative source-of-truth order

Use this precedence:

1. latest M12CD result ZIP supplied for this task;
2. current repository state at the M12CD final-local commit;
3. M12CC result;
4. M12CB result;
5. M12CA result;
6. older handoff/state files only for background.

Authoritative M12CD result bundle SHA-256:

`89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff`

The M12CD result bundle was independently checked as:

- manifest artifacts: `89/89`;
- missing artifacts: `0`;
- SHA mismatches: `0`;
- size mismatches: `0`;
- unexpected payload artifacts: `0`.

M12CD top-level result:

`MATURITY_AS_OF_DETERMINISTIC_OWNERSHIP_MIGRATION_OFFLINE_PASS`

M12CD message/model readiness:

`NOT_REPROVEN_MODEL_CALL_REQUIRED`

M12CD next scope:

`M12CE_NEW_FULL22_REPROOF_UNDER_FROZEN_DETERMINISTIC_AS_OF_CONTRACT`

Do not reopen M12CD scalar-policy design unless fresh proof evidence demonstrates an actual contradiction.

---

## 2. Repository provenance — exact meanings

The following meanings are authoritative and MUST remain distinct:

```text
origin_main_observed = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479
m12cc_final_local_sha = b26022916f0bd2dea58dde71a9fddb41a844a9d4
m12cd_work_instruction_sha = dbe40f4c9b5564660dab509d6534c8f9acbeb1b2
m12cd_runtime_implementation_sha = 9a9bda729afcb0777d7228ee7151d31f0b2f84f8
m12cd_final_local_sha = 6f87e8723cae359054335ee8fa92f5efca40047b
```

The Git history is:

```text
6f87e87 docs: close M12CD deterministic as-of migration
9a9bda7 feat: make maturity as-of runtime owned
dbe40f4 docs: freeze M12CD work instruction
b260229 docs: close M12CC ownership design audit
```

### 2.1 Known M12CD reporting-label inconsistency

Some M12CD artifacts (`01-repository-provenance.json` and `59-program-completion.json`) label `6f87e872...` as `implementation_sha`. That is a reporting/provenance-label inconsistency.

The authoritative distinction is:

- runtime implementation commit = `9a9bda729afcb0777d7228ee7151d31f0b2f84f8`;
- final local documentation-close commit = `6f87e8723cae359054335ee8fa92f5efca40047b`.

This is supported by Git log, M12CD result report, readiness JSON, repository-state JSON, and project-state JSON.

Do NOT rewrite the immutable M12CD result ZIP. Record this correction in M12CE provenance artifacts and use the corrected meanings going forward.

### 2.2 M12CE starting point

Create the M12CE working branch from exact:

`6f87e8723cae359054335ee8fa92f5efca40047b`

Suggested branch:

`codex/20260916-m12ce-deterministic-asof-full22-reproof`

The worktree must be clean before the M12CE work-instruction commit.

Commit the M12CE work instruction before any proof execution.

No runtime/source implementation change is authorized in M12CE.

---

## 3. Frozen M12CD contract

The following is already decided and is not under redesign in this task.

### 3.1 Ownership

`driver_maturity.as_of` is:

`DETERMINISTIC_PROVENANCE_FIELD`

It is not a meaningful model-selected investment judgment.

### 3.2 Model-facing contract

```text
model_output_contract = v2-accepted-stage2-model-output-v2
```

The model-facing Stage-2 schema does **not** expose or require `driver_maturity[].as_of`.

The model must not emit, infer, choose, copy, or guess `driver_maturity.as_of`.

### 3.3 Normalization/materialization contract

```text
normalization_contract = stage2-maturity-as-of-deterministic-v1
semantic = LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE
aggregation = MAX_CONCRETE_OWNED_DATES
owner = materialize_accepted_v2_stage2_output
```

Derivation uses only:

- refs actually cited in the same `driver_maturity` row;
- refs visible to the same ticker;
- canonical concrete dates resolved from those refs.

It excludes:

- assessment-date fallback;
- system/current date;
- batch-global maximum date;
- ticker-global uncited date;
- other-ticker refs;
- unresolved symbolic tokens from scalar derivation.

If no concrete same-row owned date exists, fail closed.

If the derived date is after the assessment date, fail closed.

The existing hard same-row ownership validator remains active after materialization.

### 3.4 Internal contract

The internal typed candidate contract remains:

`v2-accepted-production-output-v1`

The internal `DriverEvidenceMaturity.as_of` field remains required after deterministic materialization for compatibility.

### 3.5 Historical compatibility facts

M12CD audited 62 historical maturity rows:

```text
single concrete date rows = 37
multi concrete date rows = 25
symbolic-only rows = 0
symbolic + concrete rows = 2
old as_of == derived MAX = 60/62
old as_of != derived MAX = 2/62
```

Policy classification:

`MAX_IS_NEW_DETERMINISTIC_CONTRACT_BUT_COMPATIBLE`

Chosen scalar semantics:

`LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`

Primary-evidence-date semantics found:

`false`

Hash impact:

`HASH_CHANGE_EXPECTED_BUT_SEMANTICALLY_NEUTRAL`

Historical old-vs-derived audit:

```text
accepted-plan semantic changes = 0
renderer changes = 0
continuity churn events = 0
candidate hash changes = 2
accepted-plan hash changes = 2
Fundamental Core SHA changes = 0
```

Do not redesign these conclusions during M12CE.

---

## 4. Immutable historical 010120 control

The historical M12CB/M12CC `010120` raw output remains an immutable negative fixture:

```text
historical model-authored as_of = 2026-09-15
same-row cited ref owned date = 2026-08-12
classification = CONCRETE_BUT_UNOWNED_DATE
```

The old raw output must remain invalid.

The M12CD ephemeral new-contract replay derived `2026-08-12` only because that historical row cited that exact concrete owner.

### Critical M12CE rule

Do **not** hard-code or require `010120 = 2026-08-12` in the new generation.

For the new M12CE model output, whatever ticker-local exact refs the model validly cites in the row determine the deterministic provenance date under the frozen generic rule.

No ticker/date exception is allowed.

---

## 5. Proof-only code freeze

M12CE is not authorized to change runtime behavior.

Before the first model call:

1. compare runtime/source files against M12CD final-local `6f87e872...`;
2. prove that only the M12CE work-instruction/documentation/proof-harness artifacts differ;
3. prove the M12CD runtime implementation remains exactly the implementation introduced at `9a9bda729...`;
4. record a runtime-source tree hash or exact changed-file audit sufficient to prove no model/runtime contract drift.

If a runtime/source change is required to make the new proof pass:

- STOP;
- make zero model retries;
- classify the failure;
- propose a separately authorized bounded task in Chat.

Do not silently turn M12CE into M12CF-style repair work.

---

## 6. Mandatory pre-model preflight

No external model call may begin until all preflight gates pass.

### 6.1 M12CD bundle integrity

Verify:

- M12CD ZIP SHA-256 exact match;
- manifest completeness;
- artifact hashes/sizes;
- repository provenance;
- corrected implementation/final-local distinction from Section 2.

### 6.2 Repository cleanliness

Require:

- exact M12CD final-local base;
- clean worktree before work-instruction commit;
- no unmerged conflicts;
- no source/runtime drift after work-instruction commit.

### 6.3 Frozen contract assertions

Prove locally:

- Stage-2 model output contract is `v2-accepted-stage2-model-output-v2`;
- normalization contract is `stage2-maturity-as-of-deterministic-v1`;
- model-facing `DriverEvidenceMaturity` schema contains no `as_of` property;
- `as_of` is not in the model-facing required list;
- `additionalProperties=false` strictness is preserved;
- prompt says runtime owns/materializes the field and the model must not emit/infer it;
- raw model-emitted `as_of` is rejected;
- no-concrete-owner rows fail closed;
- cross-ticker/unknown refs fail closed;
- future derived dates fail closed;
- post-materialization date tampering still fails the hard validator.

### 6.4 M12CD contract hash reference

Record and compare against the M12CD contract reference:

```text
model_contract_hash_after = c2486e65c105a0c143308eb18da426cac7e45e8426dca567713c2293f5675a93
```

If the proof input/context intentionally changes byte-level batch prompts, do not falsely require each old batch prompt hash to remain identical. Instead:

- prove contract structure is unchanged;
- separately record fresh prompt/schema hashes for every M12CE batch;
- explain any byte-level difference by input/context only.

Any unexplained contract-level schema/prompt change is a hard stop before model calls.

### 6.5 Local regression preflight

At minimum run the focused M12CD ownership/materializer regressions and all proof-critical frozen-contract tests.

No known failing proof-critical test may be waived.

---

## 7. Full22 subject and call plan

The proof population is unchanged:

- US: 14 subjects;
- KR: 8 subjects;
- total: 22 subjects.

Use a **wholly new generation id**. Do not continue, clone, stitch, or resume any M12CA/M12CB generation.

Expected no-repair model-call topology is 16 calls:

```text
calls 01-05: US Fundamental Core batches 1-5
calls 06-10: US Stage-2 batches 1-5
calls 11-13: KR Fundamental Core batches 1-3
calls 14-16: KR Stage-2 batches 1-3
```

Batch subject sets must come from the existing canonical runner/configuration. Do not manually repartition to make a failure disappear.

Expected current historical batching reference:

US Stage-2:

```text
batch 1: CORZ / CPNG / CRCL
batch 2: GOOGL / HUT / IBM
batch 3: MU / RXRX / SKHY
batch 4: SNDK / TSLA / TSM
batch 5: WRD / WULF
```

KR observed reference:

```text
batch 1: 000660 / 003690 / 005490
batch 2: 005930 / 010120 / 012450
batch 3: remaining canonical KR subjects
```

Do not invent the KR batch-3 names if the canonical runner already owns that set. Resolve them from the current canonical Full22 configuration.

---

## 8. Formal no-repair proof policy

M12CE must use the same strict no-repair philosophy as prior Full22 proof generations.

The following counts must remain zero:

```text
retry = 0
wrapper_retry = 0
fallback = 0
judge = 0
repair = 0
schema_repair = 0
candidate_repair = 0
selective_rerun = 0
per_ticker_retry = 0
hotfix = 0
output_stitch = 0
prior_output_reuse = 0
```

The production runtime may contain dormant repair capabilities. They are not authorized in this formal proof.

Use a no-repair proof harness/configuration that stops before any such path executes.

A failed raw output remains failed.

---

## 9. Per-call Fundamental Core acceptance

For each Fundamental Core batch require existing canonical gates, including:

- exact requested subject cardinality;
- exact ticker set;
- no missing ticker;
- no extra ticker;
- no duplicate ticker;
- frozen identity fields correct;
- exact source/evidence ownership;
- no batch identity drift.

Full22 Fundamental Core acceptance must reach:

`22/22`

Any Fundamental Core hard failure stops the generation immediately.

Do not reopen Fundamental Core architecture in this proof task.

---

## 10. Per-call Stage-2 raw contract acceptance

Before deterministic materialization, inspect the immutable raw model output.

Require:

```text
contract = v2-accepted-stage2-model-output-v2
```

For every raw `driver_maturity` row:

- `as_of` property count must be zero;
- exact evidence refs must be model-visible and ticker-local;
- maturity atomic claim refs must be canonical;
- supporting/contradicting claim sets must satisfy existing polarity/identity rules;
- no new hidden date field or prose surrogate may be used to reintroduce model date selection.

If any raw model output contains `driver_maturity.as_of`, classify and stop as a new contract violation. Do not strip it and continue inside the proof harness.

The production materializer itself also rejects model-authored `as_of`; preserve that defense.

---

## 11. Deterministic `as_of` materialization proof

For every Stage-2 candidate and every maturity row, record a row-level proof matrix containing at least:

```text
market
ticker
batch
row_index
stable row identifier / driver hash
driver text hash (or stable equivalent)
supporting_evidence_refs
contradicting_evidence_refs
all same-row cited refs
resolved_as_of_date per cited ref
symbolic/unresolved refs
distinct concrete owned dates
derived as_of
assessment_date
same-row ownership valid
future-date valid
hard-validator result
```

Frozen derivation rule:

```text
concrete_owned_dates = concrete resolved dates of ticker-local refs cited in this same row
if empty -> FAIL CLOSED
derived_as_of = MAX(concrete_owned_dates)
if derived_as_of > assessment_date -> FAIL CLOSED
inject into internal representation
run existing typed/hard validators
```

Acceptance requires:

- model-authored `as_of` count = `0`;
- no-concrete-owner failure count = `0` for an overall Full22 PASS;
- cross-ticker/unknown-ref failure count = `0`;
- future-derived-date failure count = `0`;
- unowned-derived-date failure count = `0`;
- post-materialization hard-validator failure count = `0`.

Symbolic + concrete rows are allowed only under the frozen Option-A semantics: unresolved symbolic refs do not participate in scalar derivation; the latest known concrete same-row provenance date is used.

Symbolic-only rows must fail closed.

---

## 12. Stage-2 semantic acceptance

After materialization and typed construction, preserve every previously accepted hard semantic contract.

Require existing validation for, at minimum:

- frozen-core ownership/identity;
- Stage-2-owned claim-language scope;
- standalone numeric validator strictness;
- exact-ref fidelity;
- typed string/date primitive contract;
- maturity polarity atomic-claim contract;
- same-claim polarity overlap prohibition;
- parent evidence ownership;
- preconfirmation BUY contract;
- BUY/new-buyer/holder/timing three-axis independence;
- post-confirmation HOLD maturity;
- expectation/valuation ownership separation;
- BusinessDelta ownership;
- Persistence V2 identity/continuity rules.

Full22 Stage-2 semantic acceptance must reach:

`22/22`

No partial-batch acceptance or selective salvage is allowed.

---

## 13. Required targeted regressions inside the new generation

### 13.1 GOOGL preconfirmation contract

Do not force exact prose or price timing, but the previously solved contract must not regress.

Specifically, if the fresh analytical state remains the same semantic shape, verify the system can still represent independently:

- overall BUY;
- pre-confirmation state;
- new-buyer WAIT;
- holder HOLDABLE;
- timing UNFAVORABLE;

without mechanical new-buyer mapping or price-confirmation contamination.

Do not hard-code GOOGL to BUY if fresh evidence/valid model reasoning legitimately changes the analytical decision. The regression target is the contract independence, not a forced investment answer.

### 13.2 SNDK / TSLA / TSM frozen-core numeric scope

Verify:

- frozen Fundamental Core numeric prose is not falsely revalidated as Stage-2-owned prose;
- Stage-2-owned exact numeric violations still fail;
- frozen-core mutation still fails;
- false-positive count remains zero.

### 13.3 010120 maturity date

Do not assert a ticker-specific date.

Verify only the generic frozen contract:

- raw model output contains no `as_of`;
- same-row refs are canonical and ticker-local;
- deterministic materializer derives from those exact refs;
- hard same-row ownership validation passes.

The immutable historical bad output remains separately invalid.

---

## 14. Fresh generation immutability and stop-on-first-failure

Every raw prompt, schema, output, normalized/materialized output, validation result, and call ledger entry must be content-addressed or otherwise immutable in the proof bundle.

If any new hard failure occurs:

1. stop the entire generation at that call;
2. do not modify the failed raw output;
3. do not retry the call;
4. do not rerun the ticker/batch;
5. do not continue later calls;
6. do not patch runtime/prompt/schema in the same M12CE task;
7. classify the failure precisely;
8. return the result to Chat for next bounded-scope design.

A new failure is evidence, not permission to repair inside the proof generation.

---

## 15. Full22 success criteria

A clean M12CE Full22 proof requires all of the following:

```text
planned model calls = 16
started model calls = 16
completed model calls = 16
usable raw outputs = 16
Fundamental Core accepted subjects = 22/22
Stage-2 raw contract accepted subjects = 22/22
Stage-2 deterministic materialization accepted subjects = 22/22
Stage-2 semantic accepted subjects = 22/22
final US composition = 14/14
final KR composition = 8/8
final total composition = 22/22
```

And:

```text
raw model-authored maturity as_of count = 0
maturity materialization failure count = 0
same-row ownership failure count = 0
future derived date count = 0
cross-ticker date/ref count = 0
unknown ref count = 0
maturity atomic identity failure count = 0
frozen-core revalidation false-positive count = 0
preconfirmation contract failure count = 0
three-axis violation count = 0
```

And all no-repair counters from Section 8 must be zero.

---

## 16. Post-generation local validation

After a clean generation, run:

- focused M12CD materializer/contract tests;
- all frozen Stage-2 regression tests;
- full local pytest suite;
- Ruff;
- `git diff --check`;
- Treasury focused regression;
- Kiwoom local focused regression.

Because M12CE is proof-only, unexpected runtime source diffs are a failure.

Record warnings/skips separately; do not silently convert them into PASS if proof-critical.

---

## 17. Frozen successful contracts — do not reopen

The following are frozen unless the new immutable Full22 output produces direct contradictory evidence:

- M12CB frozen-core numeric claim-language scope repair;
- standalone numeric validator strictness;
- preconfirmation BUY contract;
- BUY / WAIT / HOLDABLE three-axis independence;
- maturity polarity atomic-claim contract;
- Fundamental Core batch identity;
- exact-ref fidelity;
- Stage-2 typed string/date primitive contract;
- frozen-core ownership;
- post-confirmation HOLD maturity;
- expectation/valuation separation;
- BusinessDelta ownership;
- Persistence V2;
- M12CD deterministic maturity-`as_of` ownership;
- M12CD scalar semantics and MAX concrete same-row aggregation.

M12CE is validation of these contracts, not a redesign opportunity.

---

## 18. Market-context freeze

### 18.1 Treasury

Keep frozen:

```text
provider = FRED
nominal = DGS3 / DGS5 / DGS10 / DGS30
real = DFII10
breakeven = T10YIE
historical final renderer commit = 4407cd11a78579e11681b503b2d4e72ee3c3d60f
```

Preserve:

- daily semantics;
- per-series as-of;
- basis-point change semantics.

No Treasury source/renderer redesign in M12CE.

### 18.2 Kiwoom

Keep frozen:

```text
historical commit = 28f4f70700046f98d5d899ee491d3e5f45922e9a
KOSPI200 2026-09-01/02/03 replay = PASS
local LeadingMarket adapter = PASS
KOSDAQ150 historical actual fixture = NOT YET VERIFIED
live gateway authorized capability = READ_ONLY only
```

Required eventual live config names remain:

```text
KIWOOM_GATEWAY_URL
KIWOOM_GATEWAY_API_KEY
KIWOOM_GATEWAY_TIMEOUT_SECONDS
```

During M12CE:

- do not configure a new gateway;
- do not create a new connector;
- do not place/order/modify/cancel anything;
- expected live read/order/modify/cancel counts remain `0/0/0/0` unless Chat separately authorizes a later gateway task.

If gateway remains unavailable, report that state only.

---

## 19. Production and deployment freeze

Even if M12CE is 22/22 PASS:

```text
main merge = 0
deploy = 0
scheduler resume = 0
production send = 0
production DB mutation = 0
production warning/notification mutation = 0
Telegram real send = 0
Production Assist enablement = 0
remote push = 0 unless separately authorized
```

M12CE PASS means **model/message contract formally reproven under the frozen local implementation**, not deploy approval.

---

## 20. Provenance reporting requirements

M12CE result artifacts must never repeat the M12CD implementation/final-local ambiguity.

Use explicit fields:

```text
origin_main_observed
m12cc_final_local_sha
m12cd_work_instruction_sha
m12cd_runtime_implementation_sha
m12cd_final_local_sha
m12ce_work_instruction_sha
m12ce_proof_runtime_base_sha
m12ce_final_local_sha
```

For M12CE itself, do not invent an `implementation_sha` if no runtime implementation changed.

If a generic legacy field is unavoidable, document its exact meaning alongside it.

---

## 21. Required result artifacts

The result ZIP must include, at minimum:

1. `artifact-manifest.json`
2. M12CD source ZIP integrity verification
3. repository provenance with corrected M12CD implementation/final-local distinction
4. runtime/source freeze audit
5. M12CE work-instruction commit record
6. pre-model contract assertions
7. pre-model focused regression result
8. model contract/version/hash manifest
9. generation manifest and generation id
10. exact 16-call ledger
11. per-call prompt/schema hashes
12. immutable raw output hashes
13. Fundamental Core batch identity matrix
14. Stage-2 raw-contract matrix
15. raw model-authored-`as_of` audit
16. deterministic maturity materialization row matrix
17. per-row ref/date ownership matrix
18. symbolic/concrete row classification
19. Stage-2 semantic acceptance matrix
20. final US14/KR8 composition matrix
21. GOOGL preconfirmation/three-axis regression artifact
22. SNDK/TSLA/TSM frozen-core numeric-scope regression artifact
23. 010120 fresh-generation generic deterministic-date audit
24. immutable historical 010120 negative-fixture check
25. maturity polarity / atomic identity regression
26. exact-ref / typed-contract regression
27. Persistence V2 regression
28. full local test result
29. Ruff / diff-check result
30. Treasury regression
31. Kiwoom local regression/config status
32. message/model contract readiness
33. deployment readiness
34. next-scope decision
35. program-completion JSON
36. bundle safety artifact
37. repository state / Git log / final local diff as applicable

If the generation stops early, still produce every applicable artifact and explicitly mark later calls/batches as `NOT_RUN_AFTER_FIRST_HARD_FAILURE`.

---

## 22. Program-completion minimum fields

At minimum include:

```text
contract
top_level_result
source_of_truth_priority
m12cd_result_zip_sha256
m12cd_result_integrity
origin_main_observed
m12cc_final_local_sha
m12cd_work_instruction_sha
m12cd_runtime_implementation_sha
m12cd_final_local_sha
m12ce_work_instruction_sha
m12ce_proof_runtime_base_sha
m12ce_final_local_sha
m12cd_provenance_label_inconsistency_recorded
runtime_source_change_count
generation_id
new_generation_required
prior_output_reuse_count
output_stitch_count
planned_model_call_count
model_calls_started
model_calls_completed
model_calls_with_usable_output
retry_call_count
wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
schema_repair_call_count
candidate_repair_call_count
selective_rerun_count
per_ticker_retry_count
hotfix_count
fundamental_core_accepted_count
stage2_raw_contract_accepted_count
stage2_materialized_candidate_count
stage2_semantic_accepted_count
us_final_composition_count
kr_final_composition_count
full22_final_composition_count
model_output_contract
normalization_contract
maturity_as_of_semantics
maturity_as_of_aggregation
raw_model_authored_asof_count
materialized_maturity_row_count
symbolic_only_row_count
symbolic_plus_concrete_row_count
multi_concrete_date_row_count
maturity_no_concrete_owner_failure_count
maturity_future_derived_date_failure_count
maturity_cross_ticker_ref_failure_count
maturity_unknown_ref_failure_count
maturity_same_row_ownership_failure_count
maturity_atomic_identity_failure_count
frozen_core_revalidation_false_positive_count
stage2_owned_exact_numeric_violation_count
preconfirmation_contract_failure_count
preconfirmation_three_axis_violation_count
googl_contract_regression_status
sndk_tsla_tsm_regression_status
historical_010120_original_status
fresh_010120_deterministic_materialization_status
fundamental_core_sha256_changed
accepted_plan_semantic_change_count
renderer_change_count
continuity_churn_event_count
focused_test_result
full_test_result
ruff_result
git_diff_check
treasury_local_regression_status
kiwoom_adapter_status
kiwoom_gateway_configured
kiwoom_authorized_capability
live_read_order_modify_cancel_counts
production_db_mutations
production_sends
scheduler_mutation_count
scheduler_resume_count
main_merges
deployments
remote_push_count
message_model_contract_readiness
deployment_readiness
next_scope
```

---

## 23. Final result classification

### PASS branch

If all 22 subjects and all 16 no-repair calls pass:

```text
M12CE_RESULT = DETERMINISTIC_AS_OF_CONTRACT_FULL22_REPROOF_PASS
MESSAGE_MODEL_CONTRACT_READINESS = FULL22_REPROVEN_LOCAL_ONLY
DEPLOYMENT_READINESS = NO_BY_PHASE_BOUNDARY
```

Recommended next bounded scope after Chat review:

`KIWOOM_READ_ONLY_GATEWAY_CONFIGURATION_AND_VERIFICATION`

Do not automatically start that next scope inside M12CE.

### FAIL branch

On the first new hard failure:

```text
M12CE_RESULT = FULL22_REPROOF_BLOCKED_BY_NEW_HARD_FAILURE
MESSAGE_MODEL_CONTRACT_READINESS = NOT_READY
DEPLOYMENT_READINESS = NO
```

Record:

- exact ordinal;
- market/batch/ticker(s);
- raw immutable output hash;
- failing contract/error taxonomy;
- whether failure occurred before or after deterministic materialization;
- all counters through the stop point;
- all later calls as NOT_RUN.

Do not repair in M12CE.

---

## 24. Post-M12CE sequence — frozen

Even after a clean M12CE Full22 PASS, the intended sequence remains:

```text
M12CE Full22 PASS
→ return result to Chat for whole-system review
→ Kiwoom read-only gateway configuration / verification
→ return result to Chat
→ current US/KR market + monitored-stock message smoke
→ inspect only the collected facts and make an independent human judgment
→ compare human judgment against AI output
→ decide separately whether deploy / automation is authorized
```

No step in M12CE authorizes skipping this sequence.

---

## 25. Final instruction to execution session

Treat M12CD as the frozen deterministic implementation and M12CE as its formal no-repair model proof.

Do not “help” the proof by changing the contract after seeing an output.

Do not resume an old generation.

Do not reuse old outputs.

Do not strip a forbidden field and continue.

Do not invoke repairs.

Do not selectively salvage a good ticker from a failed batch.

Start a wholly new generation at call 1, preserve every raw result, stop on the first hard failure, and return the evidence to Chat.

If and only if all 16 calls and all 22 subjects pass under the frozen deterministic maturity-`as_of` contract, declare local model/message contract reproof complete — **not deployment-ready**.
