# Thesis Monitor — Bounded Directional Financial Context Validator Repair & Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-bounded-directional-financial-context-validator-repair-and-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-bounded-directional-financial-context-validator-repair-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12R — Bounded Directional Financial Context Repair
        QTD/YTD Semantic Validator + Full Fictional Canary
```

This task begins only after M12 stopped with:

```text
status = M12_MODEL_CANARY_FAIL
stop_reason = QTD_YTD_VALIDATOR_FALSE_REJECT_KOREAN_CUMULATIVE_WORDING
next_scope = BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

M12 deterministic implementation is preserved.

M12R must repair only the validator defect proven by the M12 artifact set,
then rerun the entire 8-subject fictional canary from a new generation.

M12R must NOT:

```text
change Directional financial-context selection
change Directional prompt
change BUY/SELL thresholds
change 0.5 balance increments
change HOLD lean
change calibration tie-break
change source mappings
change source sufficiency
change Price-Timing
change renderer substantive ownership
run a fresh real issuer proof
merge/deploy production
resume monitoring schedules
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260909-directional-financial-context-consumption-specificity-implementation-report.zip
```

Verified SHA-256:

```text
0df2b7117ac262cc45792fe10a1b92f33bd1853d1d0545318e953f4d5a791471
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M12 state:

```text
M1–M11 = COMPLETE

M12 =
DETERMINISTIC_COMPLETE_CANARY_BLOCKED

deterministic implementation =
PASS

fictional canary =
FAIL_VALIDATOR_FALSE_REJECT

fresh real proof readiness =
NOT_READY

production readiness =
NOT_READY
```

Reported M12 provenance:

```text
base_sha =
58ae6feb3654d3c11f9ca98a6483c748163c5886

work_instruction_commit =
942f794cfff67f7ec881911a07804f96998c5158

implementation_commit =
72c28172949939b268806f5cb347ae4761a0d7f0

branch =
codex/20260909-directional-financial-context-consumption-specificity-implementation
```

M12 completion artifact used the established pre-report-commit convention:

```text
report_commit = NOT_MEASURED
final_head_sha = NOT_MEASURED
```

At task start, use actual repository HEAD as authority and record actual M12 final/report state.

M12 artifact integrity independently verified:

```text
indexed payload count = 95
hash mismatch count = 0
size mismatch count = 0
```

---

# 2. Proven M12 failure — do not reinterpret

M12 attempted only:

```text
run-1 / context-01
```

covering:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-03
FIC-FIN-04
```

Transport succeeded.

All 4 model rows were schema-valid.

Actual financial hard-semantic violation count:

```text
0
```

The stop was caused by:

```text
FIC-FIN-03
reported_error = qtd_ytd_conflict_not_explicit
root_cause = VALIDATOR
validator_false_reject_count = 1
```

The output actually said, among other equivalent statements:

```text
"최근 분기 영업실적이 흑자로 돌아섰다."

"연초 이후 누적 영업실적은 손실이다."

"분기 영업흑자와 누적 영업손실의 기간별 충돌이 판단을 지배한다."

"최근 분기는 흑자지만 연초 이후 누적 기준은 손실..."
```

The output cited both:

```text
QTD evidence ref
YTD evidence ref
```

M12's frozen validator recognized:

```text
ytd
누계
```

but did not recognize the valid Korean cumulative wording:

```text
누적
```

Therefore the authoritative root cause is:

```text
QTD_YTD_VALIDATOR_KOREAN_CUMULATIVE_WORDING_FALSE_REJECT
```

Do not change the prompt to work around this validator bug.

Do not rewrite the fictional case.

Do not modify the old raw output.

---

# 3. Preserve M12 implementation

M12 deterministic layer passed:

```text
financial_context_builder_status = PASS
financial_context_builder_idempotency = PASS

selected item cap = 8
max actual selected items in 8 fixtures = 3

price refs in financial context = 0
technical refs = 0
supply refs = 0
selection direction bias = 0

FCF label violations = 0
year-end-as-YoY violations = 0
partial-debt-total violations = 0
normalized-earnings violations = 0
financial-sector generic financial-context leak = 0
fixed financial score rules = 0

source sufficiency changes = 0
Daily Delta changes = 0
warning semantic changes = 0
```

M12 changed Directional prompt intentionally.

M12R must preserve the M12 Directional prompt byte-for-byte.

Required:

```text
directional_prompt_change_count = 0
```

relative to M12 final implementation.

Also preserve:

```text
Price-Timing prompt
financial-context selector
financial-context item cap
source mappings
financial-context schema
renderer
```

unless a direct compatibility import is necessary and semantic-neutral.

---

# 4. User-approved operating constraints

## 4.1 Provider policy

No provider calls.

Required:

```text
provider_source_fetches = 0
```

## 4.2 Existing monitoring remains paused

Observe the same approved 8 schedule paths at start/end.

Do not resume them.

If one exact approved path unexpectedly becomes active:

```text
pause only that exact path
record mutation
```

## 4.3 Production side effects remain zero

Required:

```text
production DB mutations = 0
monitoring registrations = 0
assessment persistence = 0
warning mutations = 0
notification queue writes = 0
production sends = 0

main merge = 0
deployments = 0
automatic monitoring resume = 0
```

---

# 5. Work-instruction commit first

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Then commit this work instruction.

Record:

```text
new_work_instruction_commit
```

Only then repair the validator.

---

# 6. Validator repair scope

Repair only the generic validator responsible for determining whether a QTD/YTD conflict is explicitly distinguished.

The repaired validator must be:

```text
multilingual enough for the supported Korean/English Directional output

period-aware

evidence-ref aware where feasible

bounded to explicit period semantics

not a loose substring pass
```

Do not create a natural-language parser for all finance prose.

---

# 7. Preferred validator architecture

The validator should use BOTH:

```text
structured supplied evidence period types
and
bounded explicit output period-language markers
```

rather than relying on one hard-coded English/Korean word.

For a required QTD/YTD conflict explanation:

## Evidence condition

The relevant output claim / dominant reasoning must cite or be traceable to:

```text
at least one supplied QTD evidence ref
and
at least one supplied YTD evidence ref
```

or the equivalent existing validator-level structured linkage.

## Language condition

The text must explicitly distinguish both period meanings.

Accepted QTD marker family may include bounded terms equivalent to:

```text
QTD
quarter
quarterly
current quarter
latest quarter
this quarter

분기
최근 분기
해당 분기
이번 분기
분기 기준
분기 실적
```

Accepted YTD/cumulative marker family may include bounded terms equivalent to:

```text
YTD
year-to-date
cumulative
cumulative YTD
since the start of the year

누계
누적
누적 기준
연초 이후
연초부터
연초 이후 누적
연초부터 누적
```

Exact implementation may normalize case/spacing/punctuation.

Do not accept vague text such as:

```text
최근 실적
전체 실적
현재까지
그동안
```

without an explicit cumulative/YTD meaning.

---

# 8. Avoid false accepts

The repair must not simply add:

```text
if "누적" in text: PASS
```

to the old validator.

Required fail cases include:

```text
"누적적으로 좋아졌다"
```

when no YTD/cumulative financial period is actually expressed.

Also reject:

```text
QTD evidence cited but no YTD evidence

YTD evidence cited but no QTD evidence

both refs cited but text collapses them into one undifferentiated "최근 실적"

"분기" appears only in an unrelated checkpoint while the conflict claim remains vague

"누적" appears only inside unrelated text with no YTD conflict statement
```

The validator must remain claim/evidence specific enough to prevent false passes.

---

# 9. Historical raw-output regression

Before any new model call, apply the repaired validator offline to the preserved M12 raw output:

```text
experiment/model-calls/run-1/context-01/output.raw.json
```

Expected:

```text
FIC-FIN-03 prior false reject
→ PASS under repaired validator

FIC-FIN-01
FIC-FIN-02
FIC-FIN-04
→ remain PASS

new hard-financial semantic violation = 0
```

This is a regression proof only.

It does NOT convert the old M12 canary into a successful 6-call canary.

Do not count old output toward M12R repetition/stability.

---

# 10. Dedicated validator unit fixtures

Add positive fixtures for explicit QTD/YTD distinction.

At minimum:

```text
"최근 분기는 흑자지만 연초 이후 누적 기준은 적자다."

"분기 영업흑자와 누계 영업손실이 공존한다."

"QTD profit is positive while YTD operating income remains negative."

"이번 분기는 개선됐지만 연초부터 누적 실적은 아직 손실이다."
```

with correct structured QTD/YTD evidence refs.

Add negative fixtures for:

```text
"최근 실적은 엇갈린다."

"분기 실적이 좋고 누적적으로도 중요하다."

QTD marker only

YTD marker only

both marker words but only one period evidence ref

both evidence refs but no explicit period contrast

unrelated "누적" occurrence
```

Fail closed.

---

# 11. No prompt/context changes

Freeze the following hashes before repair and verify after repair:

```text
Directional prompt
Price-Timing prompt

financial-context selector implementation / contract
fictional case packets
fictional source lock
frozen context prompt inputs
model output schema
```

The only semantic implementation change should be the validator.

Required:

```text
directional_prompt_change_count = 0
price_timing_prompt_change_count = 0
financial_context_selection_change_count = 0
fictional_case_change_count = 0
schema_change_count = 0
```

If a frozen input changes unexpectedly:

```text
STOP
M12R_SCOPE_DRIFT
```

---

# 12. Directional calibration remains frozen

Required unchanged:

```text
BUY >= 6.0
SELL >= 6.0
otherwise HOLD

0.5 increments

HOLD 5.5:4.5 BUY_LEAN
HOLD 5.0:5.0 NEUTRAL
HOLD 4.5:5.5 SELL_LEAN

less-directional adjacent-bucket tie-break toward 5.0
```

Required:

```text
directional_threshold_changed = false
directional_increment_changed = false
hold_lean_contract_changed = false
calibration_tiebreak_changed = false
```

No score averaging / voting.

---

# 13. Phase A deterministic gating

Before model calls:

```text
historical false-reject regression PASS

new QTD/YTD positive unit fixtures PASS

new QTD/YTD negative unit fixtures PASS

focused pytest PASS

full repository pytest PASS

ruff PASS

git diff --check PASS

prompt/context/schema freeze audit PASS

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer ownership unchanged

production side-effect firewall PASS
```

If any fails:

```text
STOP
NO_MODEL_CALLS
```

---

# 14. Full fictional canary — new generation required

After Phase A passes, create a NEW canary generation ID.

Use the same frozen 8 fictional cases:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-03
FIC-FIN-04
FIC-FIN-05
FIC-FIN-06
FIC-FIN-07
FIC-FIN-08
```

Use the same frozen financial case semantics.

Do not alter case values to make the model pass.

Do not merge old M12 output into the new generation.

---

# 15. Full canary topology

Run:

```text
8 subjects
2 shared contexts
4 subjects per context
3 repetitions
```

Total:

```text
6 fictional model calls
24 subject outputs
```

Execution order may be:

```text
run-1 context-01
run-1 context-02
run-2 context-01
run-2 context-02
run-3 context-01
run-3 context-02
```

or the existing canonical equivalent.

All 6 calls belong to the new M12R generation.

---

# 16. Frozen runtime

Use exactly the M12 frozen runtime:

```text
model = gpt-5.6-sol
reasoning = xhigh
runtime mode = MODEL_CONTEXT_COUPLED
subjects per context = 4
timeout = 1800 seconds
single authoritative watchdog = true
wrapper auto-retry = 0
batch split = 0
```

Each context invocation must have:

```text
unique invocation ID
unique runtime namespace
unique working directory
unique session identity
```

No namespace reuse.

---

# 17. Whole-canary stop rules

If a hard semantic failure occurs during the new generation:

```text
stop the canary
preserve all emitted outputs
do not selectively continue later contexts
```

If transport fails:

```text
follow no-wrapper-retry / single-watchdog policy
```

Do not selectively rerun one failed context inside the same generation to manufacture a complete sample.

Any new full canary after a semantic/runtime repair must use a new generation.

---

# 18. Canary hard semantic gates

Across all completed outputs require zero:

```text
invalid financial evidence refs

price / technical / supply references in Directional financial reasoning

partial PPE cash-conversion proxy called FCF

prior-year-end comparison called YoY

partial debt called total debt

total liabilities called debt

normalized / adjusted earnings invented

normalized EPS invented

financial-sector generic industrial financial reasoning

missing optional financial context treated as negative evidence

fixed financial scorecard behavior

AI imperative primary action wording

QTD/YTD conflict false rejects

QTD/YTD conflict false accepts
```

---

# 19. Case-specific semantic expectations

Preserve M12 fictional case contracts.

## FIC-FIN-01

Strong-quality case.

Expected:

```text
specific positive financial anchor(s)
no FCF invention
```

## FIC-FIN-02

Profit/cash divergence.

Expected:

```text
cash conversion limits conviction
not automatically SELL solely from one weak OCF period
```

## FIC-FIN-03

QTD/YTD conflict.

Expected:

```text
explicit distinction between latest-quarter improvement
and cumulative/YTD weakness
```

This is the validator-repair focal case.

## FIC-FIN-04

Non-operating net-income boost.

Expected:

```text
net-income improvement not equated with operating improvement
no normalized earnings
```

## FIC-FIN-05

Leverage/liquidity pressure.

Expected:

```text
financial resilience as limiting anchor
no total-liabilities-as-debt inference
```

## FIC-FIN-06

Inventory/receivables build.

Expected:

```text
prior-year-end not called YoY
working-capital checkpoint
not automatic deterioration
```

## FIC-FIN-07

Missing optional context.

Expected:

```text
missing context does not mechanically create a more bearish direction
```

## FIC-FIN-08

Financial-sector exclusion.

Expected:

```text
no generic industrial net debt
no generic operating working-capital interpretation
no interest income classified as generic non-operating
```

---

# 20. Formal fictional stability

If all 6 calls complete and pass hard semantic validation,
run the existing formal stability classifier over all 8 fictional subjects / 3 repetitions.

Report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Required hard gate:

```text
opposite_direction_reversal_count = 0
```

Do not majority-vote.

Do not average balances.

If a subject is threshold-adjacent,
use the existing frozen stability classifier.

---

# 21. Validator-specific stability audit

Because M12R changes only the validator,
also report:

```text
validator_pass_count by repetition
validator_false_reject_count
validator_false_accept_count
```

Expected:

```text
false reject = 0
false accept = 0
```

for the full 24-output canary.

---

# 22. Message specificity advisory

Run the same M12 advisory over all 24 outputs if full canary completes.

Measure:

```text
material financial anchor presence

period specificity

case-specific checkpoints

generic substantive repetition

renderer-introduced repetition
```

This remains advisory unless it exposes a hard semantic violation.

Do not rewrite model reasoning inside M12R merely to reduce repetition.

---

# 23. No fresh real issuer proof in M12R

Required:

```text
real model calls = 0
real issuer model exposures = 0
```

Do not use:

```text
historical exposed real cohort
new unseen real cohort
```

The next real proof is authorized only after the repaired full fictional canary passes.

---

# 24. Source sufficiency / lifecycle / warnings unchanged

Required all zero:

```text
source_sufficiency_semantic_change_count

daily_delta_semantic_change_count

warning_semantic_change_count

monitoring lifecycle semantic change count
```

M12R is only a Directional semantic-validator repair.

---

# 25. Required artifacts — provenance / root cause

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m12r-scope-freeze

04-m12-failure-reproduction
05-qtd-ytd-validator-root-cause
06-qtd-ytd-validator-before-after
07-validator-responsibility-contract
```

---

# 26. Required artifacts — deterministic repair proof

Produce:

```text
08-historical-raw-output-regression
09-qtd-ytd-positive-fixture-manifest
10-qtd-ytd-negative-fixture-manifest
11-validator-false-accept-control
12-validator-false-reject-control

13-directional-prompt-freeze-proof
14-price-timing-prompt-freeze-proof
15-financial-context-selection-freeze-proof
16-fictional-case-freeze-proof
17-schema-freeze-proof

18-source-sufficiency-no-change-proof
19-daily-delta-no-change-proof
20-renderer-ownership-no-change-proof
```

---

# 27. Required artifacts — validation

Produce:

```text
21-focused-test-results
22-full-test-results
23-ruff-and-diff-results
24-phase-a-gate
```

---

# 28. Required artifacts — new full fictional canary

If Phase A passes, produce for the new generation:

```text
25-fictional-canary-generation-manifest
26-fictional-canary-source-lock

27-run-1-context-01
28-run-1-context-02

29-run-2-context-01
30-run-2-context-02

31-run-3-context-01
32-run-3-context-02

33-full-fictional-canary-semantic-audit
34-full-fictional-canary-validator-audit
35-full-fictional-canary-stability
36-full-fictional-canary-message-specificity-advisory
37-runtime-observations
```

Preserve:

```text
prompt
schema
raw output
receipt
transport log
run document
```

for every attempted call.

---

# 29. Required completion artifacts

Produce:

```text
38-fresh-real-proof-readiness-decision
39-production-no-change
40-schedule-pause-observation
41-master-workflow-update
42-program-completion
```

---

# 30. M12R acceptance criteria — repair

Repair layer passes only if:

```text
M12 FIC-FIN-03 raw output now passes correctly

valid Korean "누적" / "연초 이후 누적" wording is recognized

valid "누계" wording remains recognized

English YTD/cumulative wording remains recognized

vague/unrelated cumulative wording remains rejected

QTD/YTD structured evidence linkage remains required

Directional prompt unchanged from M12

financial-context selection unchanged from M12

threshold/calibration unchanged

focused/full tests PASS
ruff PASS
git diff --check PASS
```

---

# 31. M12R acceptance criteria — full fictional canary

Canary passes only if:

```text
6 / 6 model contexts complete successfully

24 / 24 subject outputs schema-valid

invalid financial reference count = 0

hard financial semantic violation count = 0

QTD/YTD validator false reject count = 0

QTD/YTD validator false accept count = 0

price/technical/supply Directional violation count = 0

AI imperative primary action count = 0

opposite-direction reversal count = 0

wrapper retry count = 0

unexpected timeout/capacity/orphan count = 0
```

Stability must be fully measured.

Do not leave:

```text
NOT_MEASURED
```

if all 6 contexts complete.

---

# 32. Next-scope decision

## A. Full repaired fictional canary PASS

Set:

```text
fresh_real_proof_readiness = READY
```

Recommended:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF
```

Do NOT start that proof inside M12R.

## B. Validator still false-rejects / false-accepts

Set:

```text
fresh_real_proof_readiness = NOT_READY
next_scope = BOUNDED_QTD_YTD_VALIDATOR_REPAIR
```

No real proof.

## C. Validator fixed but a different financial semantic failure appears

Set:

```text
next_scope =
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

Classify the new failure precisely.

Do not broaden the repair.

## D. Runtime failure blocks the full canary

Do not treat it as a semantic failure automatically.

Classify:

```text
transport
timeout
capacity
runtime isolation
```

and use a separate bounded runtime repair if required.

---

# 33. Production readiness

Even if M12R fully passes:

```text
production_readiness = NOT_READY
```

A fresh real generalization proof and later production integration review are still required.

Existing schedules remain paused.

---

# 34. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
report_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

m1_status
m2_status
m3_status
m4_status
m5_status
m6_status
m7_status
m8_status
m9_status
m10_status
m11_status
m12_status
m12r_status

m12_root_cause
validator_repair_status

historical_fic_fin_03_regression_status

qtd_ytd_positive_fixture_count
qtd_ytd_positive_fixture_pass_count
qtd_ytd_negative_fixture_count
qtd_ytd_negative_fixture_rejected_count

validator_false_reject_count
validator_false_accept_count

directional_prompt_change_count
price_timing_prompt_change_count
financial_context_selection_change_count
fictional_case_change_count
schema_change_count

directional_threshold_changed
directional_increment_changed
hold_lean_contract_changed
calibration_tiebreak_changed

source_sufficiency_semantic_change_count
daily_delta_semantic_change_count
warning_semantic_change_count

fictional_generation_id
fictional_subject_count
fictional_context_count
fictional_repetition_count

model_calls_real
model_calls_fictional
model_calls_judge

model_context_success_count
model_context_failure_count
wrapper_retry_count
timeout_count
capacity_failure_count
orphan_process_count

fictional_output_row_count
fictional_schema_pass_count

invalid_financial_reference_count
hard_financial_semantic_violation_count

fictional_stable_count
fictional_boundary_uncertainty_count
fictional_unstable_count
opposite_direction_reversal_count

message_specificity_advisory_status

real_issuer_model_exposure_count

provider_source_fetches

production_db_mutations
monitoring_registrations
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

main_merges
deployments
live_v2_changes
night_futures_changes

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

fresh_real_proof_readiness
production_readiness
status
stop_reason
next_scope
```

Anything not actually measured:

```text
NOT_MEASURED
```

---

# 35. Artifact integrity

Freeze:

```text
program completion
master workflow update
all deterministic reports
all attempted model call artifacts
```

before final artifact-index creation.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 36. Final task principle

M12's model did not fail the QTD/YTD reasoning test.

The validator failed to recognize a valid Korean cumulative-period expression.

The correct repair is:

```text
fix the generic period-language validator
→ prove the old valid output now passes
→ prove vague wording still fails
→ keep prompt/context/calibration frozen
→ rerun all 8 fictional cases from a new generation
→ measure full 3-repeat stability
```

Not:

```text
rewrite the prompt to say "누계"
```

Not:

```text
special-case FIC-FIN-03
```

Not:

```text
hotfix the old result and continue from context-02
```

Not:

```text
count the old partial run as part of the new 3-repeat sample
```

Not:

```text
change BUY/SELL thresholds
```

Not:

```text
run a fresh real cohort before the full repaired canary passes
```

And not:

```text
resume production monitoring
```

Repair the validator narrowly, then rerun the complete fictional proof cleanly.
