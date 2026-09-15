# Thesis Monitor — Post-Confirmation HOLD Maturity Contract Repair + New Full 22-Subject Reproof

## 0. Task identity

Suggested work-instruction filename:

```text
20260915-postconfirmation-hold-maturity-contract-repair-full-22-reproof.md
```

Suggested result bundle:

```text
thesis-monitor-20260915-postconfirmation-hold-maturity-contract-repair-full-22-reproof-report.zip
```

Master-workflow phase:

```text
M12BT — Stage-2 Contract Repair
         A. Freeze all successful M12BS local changes
         B. Freeze the already-correct semantic validator invariant
         C. Make the Stage-2 prompt/schema express that invariant explicitly
         D. Add deterministic positive/negative fixtures
         E. Run full local regression
         F. Run a NEW full US14 + KR8 monitored reproof from scratch
         G. No repair/rerun/judge/fallback inside the proof
         H. If clean, hand off to leading-futures source integration
         I. Do NOT deploy yet because leading-futures coverage remains blocked
```

This is a BOUNDED model-contract repair.

Do NOT reopen:

```text
three-axis UX

GOOGL core/timing separation

expectation/valuation ownership

BusinessDeltaEvidenceView

holder definitions

new-buyer definitions

financial semantics

Persistence V2

KR-financial cold-start repair

leading-market source decision.
```

The exact new blocker is:

```text
post_confirmation_hold = true

with

overall_maturity = MIXED.
```

The current semantic validator correctly rejects that combination.

The repair must make the model-facing contract agree with the validator.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260915-three-axis-decision-core-timing-separation-leading-futures-message-repair-report(1).zip
```

Verified SHA-256:

```text
9d4bb43db61b98ce743608f6eba60953d6ef1020192a8d4d21c76b5156c2d411
```

Recompute independently.

Sidecar must match exactly.

Independent archive verification:

```text
indexed payloads = 60

ZIP payload entries =
60

hash mismatch = 0

size mismatch = 0

missing = 0

extra = 0.
```

Artifact secret scan in the submitted report:

```text
0 failures.
```

Recompute before work.

---

# 2. M12BS successful changes — freeze

M12BS locally completed:

```text
three-axis decision UX

REVIEW safe user copy

fundamental-core / price-timing ownership split

expectation/valuation overlap classifier

leading-market snapshot contract scaffolding

US market as-of heading repair

CPNG terminal phrase repair

047810 internal-label repair.
```

Deterministic results:

```text
focused tests = PASS

full local =
3974 passed, 63 skipped

Ruff = PASS

git diff --check = PASS

price_timing_in_core_anchor_count = 0

price_timing_in_holder_anchor_count = 0

mechanical_stance_mapping_count = 0

expectation_valuation_duplicate_anchor_count = 0.
```

Do not modify these contracts in M12BT
unless required solely to keep existing tests compiling.

---

# 3. M12BS model permission — freeze as resolved

The prior external-model permission blocker is resolved.

M12BS actually ran:

```text
model =
gpt-5.6-sol

reasoning effort =
xhigh

model calls =
6

fallback =
0

judge =
0

repair =
0

selective rerun =
0.
```

Therefore M12BT must NOT classify the current issue as a permission problem.

No new user authorization is needed for the bounded frozen reproof in this instruction.

---

# 4. M12BS reproof state

Frozen monitored cohort:

```text
US = 14

KR = 8

total = 22.
```

Source-packet identities:

```text
US packet SHA =
2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228

KR packet SHA =
819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597.
```

M12BS core result before the blocker:

```text
US fundamental core =
14 / 14 PASS.
```

Then the first Stage-2 / price-timing batch failed on:

```text
ticker =
CORZ

decision =
HOLD

overall_maturity =
MIXED

post_confirmation_hold =
true.
```

Required invariant:

```text
post_confirmation_hold = true
⇒
overall_maturity = CONFIRMED.
```

The semantic validator rejected the output correctly.

---

# 5. Root-cause classification

Freeze the root cause as:

```text
MODEL_FACING_STAGE2_CONTRACT_DOES_NOT_EXPLICITLY_ENFORCE
THE_EXISTING_POSTCONFIRMATION_HOLD_MATURITY_INVARIANT.
```

This is NOT:

```text
a semantic-validator bug

a CORZ-specific exception

a BusinessDelta failure

a holder-contract redefinition

a price/timing ownership regression

a transport failure.
```

Do not weaken the validator.

---

# 6. Contract semantics

`post_confirmation_hold` means:

```text
the current HOLD state is specifically a post-confirmation state,
not merely a mixed/uncertain pre-confirmation HOLD.
```

Therefore:

```text
true
```

is only valid when the confirmation/maturity contract says the relevant maturity is:

```text
CONFIRMED.
```

For:

```text
MIXED

UNCONFIRMED

INSUFFICIENT

or repository-equivalent non-confirmed maturity
```

the flag must be:

```text
false.
```

Do not infer a new enum if the schema does not have those exact values.

Use the actual current enum set.

---

# 7. Prompt repair

Update the Stage-2 / price-timing model prompt with an explicit rule equivalent to:

```text
Set post_confirmation_hold=true ONLY when overall_maturity=CONFIRMED.

If overall_maturity is MIXED or otherwise not CONFIRMED,
post_confirmation_hold MUST be false.

A HOLD decision by itself does not imply post_confirmation_hold=true.
```

Keep wording concise.

Do not add CORZ-specific examples.

Do not force HOLD/BUY/SELL.

Do not mechanically map maturity to decision.

---

# 8. Schema repair — preferred

If the current structured-output / JSON Schema stack supports conditional constraints,
encode the invariant structurally.

Preferred semantic equivalent:

```text
if post_confirmation_hold == true
then overall_maturity == CONFIRMED.
```

Possible implementation:

```text
if / then

oneOf

dependent schema

or another supported conditional form.
```

Use the schema mechanism actually supported by the model runtime.

Do not add an unsupported JSON Schema keyword that the runtime silently ignores.

---

# 9. Schema capability proof

Before using a conditional schema construct,
add a deterministic capability test proving the current runtime/schema validator supports it.

If the external model structured-output API does NOT support the required conditional:

```text
do not fake schema enforcement.
```

Then use:

```text
explicit prompt contract
+
existing hard semantic validator
```

and report:

```text
SCHEMA_CONDITIONAL_UNSUPPORTED_PROMPT_PLUS_HARD_VALIDATOR.
```

The semantic validator remains authoritative.

---

# 10. Do not overconstrain

The following combinations must remain potentially valid:

```text
decision = HOLD
overall_maturity = MIXED
post_confirmation_hold = false

decision = HOLD
overall_maturity = CONFIRMED
post_confirmation_hold = true

decision = HOLD
overall_maturity = CONFIRMED
post_confirmation_hold = false
```

if allowed by the existing product contract.

Do NOT introduce:

```text
HOLD → confirmed

confirmed → HOLD

MIXED → WAIT

BUY/SELL restrictions
```

unless already present in the frozen contract.

---

# 11. Deterministic fixtures

Add at minimum:

## PHM-P01

```text
overall_maturity = CONFIRMED
post_confirmation_hold = true
→ PASS.
```

## PHM-P02

```text
overall_maturity = MIXED
post_confirmation_hold = false
→ PASS.
```

## PHM-P03

```text
decision = HOLD
overall_maturity = MIXED
post_confirmation_hold = false
→ PASS.
```

## PHM-N01

```text
overall_maturity = MIXED
post_confirmation_hold = true
→ hard FAIL.
```

## PHM-N02

Any other non-CONFIRMED maturity with:

```text
post_confirmation_hold = true
→ hard FAIL.
```

Use actual enum values.

---

# 12. Exact CORZ frozen-output replay

Offline replay the exact M12BS CORZ rejected Stage-2 candidate.

Expected:

```text
existing candidate remains INVALID.
```

Do NOT edit the candidate.

Do NOT reinterpret it as valid.

The repair is to prevent NEW model output from repeating the invalid combination.

---

# 13. No candidate rewrite

Forbidden:

```text
post-process true → false

post-process MIXED → CONFIRMED

rewrite CORZ output

auto-repair model JSON

second judge pass.
```

The model must emit a contract-valid output itself.

---

# 14. Model-facing identity scope

Expected model-facing changes:

```text
Stage-2 prompt semantic hash =
changed

Stage-2 schema semantic hash =
changed only if supported conditional is added.
```

Expected unchanged:

```text
fundamental-core prompt

fundamental-core schema

canonical semantic services

three-axis renderer

expectation/valuation classifier

price/timing ownership contract

Persistence V2

decision policy

leading-market snapshot contract.
```

Report exact hashes.

---

# 15. No leading-futures work in M12BT

M12BS leading-market status remains:

```text
US futures =
BLOCKED_NO_SAFE_EXISTING_API_CONNECTOR

KR night futures =
BLOCKED_NO_AUTHENTICATED_NIGHT_SESSION_GATEWAY.
```

Do NOT implement a futures connector in this task.

Do NOT accept partial coverage silently.

After reproof passes,
the next bounded task will resolve:

```text
leading-futures source integration
or explicit partial-coverage product decision.
```

This isolation keeps model-contract proof causal.

---

# 16. Full local test gate

Before external model calls run:

```text
new invariant tests

existing Stage-2 schema tests

three-axis tests

GOOGL core/timing regressions

expectation/valuation overlap tests

BusinessDelta regressions

holder/new-buyer regressions

full local pytest

Ruff

git diff --check.
```

Required:

```text
PASS.
```

No external model call if full tests are red.

---

# 17. Frozen cohort identity

Use the exact M12BS frozen monitored input cohort.

Required:

```text
US source packet SHA exact match

KR source packet SHA exact match

ticker set exact match

duplicate ticker count = 0

missing ticker count = 0

extra ticker count = 0.
```

Do not refetch providers.

Do not rebuild packets with newer market data.

This is a contract reproof.

---

# 18. New reproof generation

Because the Stage-2 model-facing contract changes,
create a NEW proof generation.

Do NOT reuse M12BS model outputs.

Do NOT stitch:

```text
old fundamental core
+
new Stage-2 output.
```

Run the complete architecture from the beginning under one model-contract generation.

---

# 19. Full 22-subject reproof

Run:

```text
US 14

KR 8

total 22.
```

Use the currently frozen batching/topology of the Accepted V2 monitored architecture.

Do not hard-code the number of calls from the failed M12BS partial run;
derive the complete call plan from the current harness before call 1.

Freeze:

```text
planned call count

stage/batch/ticker assignments

prompt hashes

schema hashes.
```

---

# 20. Model configuration

Use:

```text
gpt-5.6-sol

reasoning effort =
xhigh.
```

No Astra.

No fallback.

No judge.

No model repair calls.

No selective rerun.

No per-candidate retry.

---

# 21. Reproof failure policy

The new reproof is a no-repair proof.

If any model output is:

```text
runtime-invalid

schema-invalid

semantic-invalid

core-mutating

ownership-invalid
```

record the first failure
and follow the existing proof stop policy.

Do not patch and continue in the same task.

Do not selectively rerun.

---

# 22. Reproof acceptance

Require:

```text
all 22 subjects represented

all planned required calls complete

fundamental core valid = 22

Stage-2 / price-timing valid = 22

final composition valid = 22

canonical hard semantic failure = 0

postconfirmation maturity conflict = 0

price/timing core mutation = 0

price/timing holder mutation = 0

mechanical stance mapping = 0

expectation/valuation duplicate anchor = 0

BusinessDelta hard failure = 0

core mutation = 0

fallback/judge/repair/selective rerun = 0.
```

No expected direction distribution.

---

# 23. Three-axis proof after reproof

After a clean 22-subject reproof,
render all 22 messages locally.

Verify:

```text
종합 방향 visible = 22

신규 관찰자 visible = 22

보유자 visible = 22

REVIEW copy safe where applicable

mechanical stance mapping = 0.
```

This is local renderer verification.

Do not deploy in M12BT.

---

# 24. GOOGL result

Report:

```text
overall direction

new-buyer stance

holder stance

market expectation

valuation

price/timing core-anchor count.
```

Required:

```text
price/timing core-anchor count = 0.
```

GOOGL direction is diagnostic.

Do not require BUY.

---

# 25. CORZ regression

Report CORZ in detail:

```text
fundamental decision

overall maturity

post_confirmation_hold

new-buyer stance

holder stance

price/timing context.
```

Required:

```text
if post_confirmation_hold = true
then maturity = CONFIRMED.
```

No invalid combination.

---

# 26. Deployment remains blocked by futures source

Even if the 22-subject reproof passes:

```text
DO NOT deploy M12BS changes in M12BT.
```

Reason:

the user requested all three improvements,
and leading futures remains unresolved.

Set:

```text
message_model_contract_readiness =
READY

deployment_readiness =
NOT_READY_LEADING_FUTURES_SOURCE_PENDING.
```

Next scope:

```text
LEADING_FUTURES_SAFE_SOURCE_INTEGRATION_AND_FINAL_MESSAGE_SMOKE.
```

---

# 27. Production firewall

Required:

```text
production DB mutations = 0

assessment production writes = 0

warning production mutations = 0

notification queue writes = 0

production sends = 0

scheduler mutations = 0

automatic monitoring resume = 0

V2 production gates remain OFF

main merge = 0

deployment = 0

remote raw model artifact push = 0.
```

Model calls for frozen reproof are allowed.

---

# 28. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bt-scope-freeze

04-m12bs-successful-change-freeze

05-corZ-failure-contract-freeze

06-postconfirmation-invariant-code-audit

07-stage2-prompt-gap-reproduction

08-stage2-schema-capability-audit

09-stage2-contract-repair-decision.
```

---

# 29. Required implementation artifacts

Produce:

```text
10-stage2-prompt-invariant-implementation

11-stage2-schema-invariant-implementation-or-unsupported-decision

12-postconfirmation-invariant-positive-fixtures

13-postconfirmation-invariant-negative-fixtures

14-exact-corz-invalid-output-offline-replay

15-no-candidate-rewrite-proof.
```

---

# 30. Required deterministic test artifacts

Produce:

```text
16-focused-contract-tests

17-three-axis-regression-tests

18-core-timing-regression-tests

19-expectation-valuation-regression-tests

20-business-delta-regression-tests

21-holder-newbuyer-regression-tests

22-full-local-test-result

23-ruff-diff-result

24-model-facing-hash-change-manifest.
```

---

# 31. Required full reproof artifacts

Produce:

```text
25-frozen-22-input-identity-manifest

26-new-full-reproof-generation-manifest

27-full-reproof-call-plan

28-fundamental-core-model-artifacts

29-stage2-model-artifacts

30-full-reproof-schema-audit

31-full-reproof-canonical-semantic-audit

32-postconfirmation-maturity-audit

33-price-timing-immutability-audit

34-expectation-valuation-anchor-audit

35-business-delta-audit

36-core-immutability-audit

37-final-composition-audit

38-per-ticker-result-matrix

39-corz-postrepair-dossier

40-googl-postrepair-dossier

41-three-axis-22-message-render-audit.
```

---

# 32. Required decisions

Produce:

```text
42-model-contract-repair-decision

43-full-22-reproof-decision

44-message-model-contract-readiness-decision

45-leading-futures-blocker-preservation

46-deployment-readiness-decision

47-next-scope-decision

48-program-completion.
```

---

# 33. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bs_failure_ticker
m12bs_failure_overall_maturity
m12bs_failure_post_confirmation_hold

postconfirmation_invariant_contract_version

stage2_prompt_semantic_change_count
stage2_schema_semantic_change_count
schema_conditional_supported

fundamental_core_prompt_change_count
fundamental_core_schema_change_count
canonical_semantic_service_change_count
three_axis_contract_change_count
expectation_valuation_contract_change_count
persistence_v2_contract_change_count
leading_market_contract_change_count

exact_corz_old_candidate_still_invalid

focused_test_result
full_test_result
ruff_result
git_diff_check

frozen_us_packet_sha
frozen_kr_packet_sha
frozen_ticker_count

new_reproof_generation_id
planned_model_call_count
model_calls_started
model_calls_completed
model_calls_with_usable_output

fundamental_core_valid_count
stage2_valid_count
final_composition_valid_count

postconfirmation_maturity_conflict_count
schema_invalid_count
canonical_semantic_failure_count
business_delta_hard_failure_count
price_timing_core_mutation_count
price_timing_holder_mutation_count
expectation_valuation_duplicate_anchor_count
core_mutation_count

wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
selective_rerun_count

three_axis_visible_count
three_axis_missing_count
review_copy_safe_count

corz_overall_direction
corz_overall_maturity
corz_post_confirmation_hold
corz_new_buyer
corz_holder

googl_overall_direction
googl_new_buyer
googl_holder
googl_price_timing_core_anchor_count
googl_expectation_valuation_overlap_class

us_futures_source_status
kr_night_futures_source_status

message_model_contract_readiness
deployment_readiness

production_db_mutations
assessment_production_writes
warning_production_mutations
notification_production_queue_writes
production_sends
scheduler_mutation_count
automatic_monitoring_resume

main_merges
deployments
remote_push_count
raw_model_artifact_remote_push_count

top_level_result

next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Unknowns:

```text
NOT_MEASURED
```

with reason.

---

# 34. Expected clean outcome

If the repair and full reproof pass:

```text
top_level_result =
POSTCONFIRMATION_HOLD_MATURITY_CONTRACT_REPAIR_PASS

postconfirmation_maturity_conflict_count = 0

fundamental_core_valid_count = 22

stage2_valid_count = 22

final_composition_valid_count = 22

canonical_semantic_failure_count = 0

price_timing_core_mutation_count = 0

price_timing_holder_mutation_count = 0

expectation_valuation_duplicate_anchor_count = 0

business_delta_hard_failure_count = 0

core_mutation_count = 0

three_axis_visible_count = 22

message_model_contract_readiness =
READY

deployment_readiness =
NOT_READY_LEADING_FUTURES_SOURCE_PENDING

next_scope =
LEADING_FUTURES_SAFE_SOURCE_INTEGRATION_AND_FINAL_MESSAGE_SMOKE.
```

Do NOT force the result.

---

# 35. Failure handling

## A. Schema conditional unsupported

Use:

```text
prompt + hard validator.
```

Do not block solely because JSON Schema cannot encode it.

Report accurately.

## B. CORZ or another subject repeats the same conflict

```text
STOP
POSTCONFIRMATION_MODEL_CONTRACT_COMPLIANCE_FAILURE.
```

No repair/rerun.

## C. New hard semantic failure appears

```text
STOP
FULL_REPROOF_NEW_HARD_FAILURE.
```

No patch in M12BT.

## D. Model transport fails

Follow current frozen reproof transport policy.

No selective retry.

## E. Reproof clean

Proceed only to the separate leading-futures source task.

Do not deploy yet.

---

# 36. Final task principle

M12BS successfully implemented the user's requested decision/message architecture,
but the required frozen monitored reproof exposed one bounded model-contract gap:

```text
the schema/prompt allowed a model to say:

overall_maturity = MIXED
and
post_confirmation_hold = true

even though the semantic validator correctly defines that flag
as valid only under CONFIRMED maturity.
```

The correct M12BT flow is:

```text
keep the validator

→ make the model-facing Stage-2 contract explicit

→ encode the invariant in schema if genuinely supported

→ preserve valid HOLD + MIXED + flag=false

→ never rewrite candidate outputs

→ run a completely NEW full US14 + KR8 proof

→ verify all 22 three-axis messages locally

→ if clean, declare the model/message contract ready

→ then separately solve the leading-futures data-source contract

→ only after both are clean, deploy and run the final live message smoke test.
```

Do NOT:

```text
special-case CORZ

force maturity=CONFIRMED for HOLD

turn MIXED into WAIT

relax the semantic validator

reuse the old partial reproof

selectively rerun one model output

implement futures in the same task

deploy before futures coverage is resolved.
```
