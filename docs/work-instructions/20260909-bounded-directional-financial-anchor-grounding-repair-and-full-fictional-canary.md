# Thesis Monitor — Bounded Directional Financial Anchor Grounding Repair & Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-bounded-directional-financial-anchor-grounding-repair-and-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-bounded-directional-financial-anchor-grounding-repair-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12G — Bounded Directional Financial Context Repair
        Financial Anchor Grounding + Full Fictional Canary
```

This task begins only after M12R ended with:

```text
status = M12R_CANARY_FAIL
stop_reason = M12R_FINANCIAL_SEMANTIC_OR_STABILITY_FAILURE
next_scope = BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

M12R successfully repaired the QTD/YTD validator.

The new blocking issue is different:

```text
FIC-FIN-06 used the working-capital concept in prose
but did not cite/use the selected typed financial evidence refs.
```

M12G must repair only this financial-evidence grounding/specificity behavior,
then rerun the entire 8-subject fictional canary from a new generation.

M12G must NOT:

```text
weaken the financial semantic validator
change financial-context selection
change fictional case values
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
thesis-monitor-20260909-bounded-directional-financial-context-validator-repair-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
0a55f4f04615602c2bac72e47c0489d30788437394135b772598e377c1289ab4
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M12R state:

```text
M1–M11 = COMPLETE

M12 =
DETERMINISTIC_COMPLETE_CANARY_BLOCKED

M12R =
BLOCKED

validator repair =
PASS

fresh real proof readiness =
NOT_READY

production readiness =
NOT_READY
```

Reported M12R provenance:

```text
base_sha =
d0e17f537d111203eafec057012182b983069831

work_instruction_commit =
d01c02f3338093bf5ee380f65b8b5907ff5bbf25

implementation_commit =
ffc3fd557f056feac693e596cb48214a5e41aea3

branch =
codex/20260909-bounded-directional-financial-context-validator-repair-full-fictional-canary
```

M12R used the established pre-report-commit artifact convention:

```text
report_commit = NOT_MEASURED
final_head_sha = NOT_MEASURED
```

At task start use actual repository HEAD as authority and record the actual M12R final/report state.

M12R artifact integrity independently verified:

```text
indexed payload count = 92
hash mismatch count = 0
size mismatch count = 0
```

---

# 2. M12R validator repair is frozen and preserved

M12R successfully repaired:

```text
QTD / YTD conflict validator
```

Historical FIC-FIN-03 regression:

```text
old valid output
→ PASS after repair
```

Validator fixtures:

```text
positive fixtures = 6 / 6 PASS
negative fixtures = 10 / 10 rejected

validator false rejects = 0
validator false accepts = 0
```

Do not modify the QTD/YTD validator in M12G unless a direct regression caused by unrelated import plumbing occurs.

Required:

```text
qtd_ytd_validator_semantic_change_count = 0
```

---

# 3. Authoritative new failure — FIC-FIN-06

M12R completed:

```text
run-1 context-01 = PASS
run-1 context-02 = model transport PASS, semantic audit FAIL
```

Total completed model calls:

```text
2
```

Total subject outputs:

```text
8
```

All 8 rows were schema-valid.

All generic financial hard-safety counters remained zero:

```text
invalid financial refs = 0
price/technical/supply Directional refs = 0
partial PPE called FCF = 0
prior-year-end called YoY = 0
partial debt called total debt = 0
normalized earnings claims = 0
financial-sector generic leak = 0
fixed financial score rules = 0
AI imperative primary action = 0
QTD/YTD conflict violation = 0
```

The actual hard failure was:

```text
ticker = FIC-FIN-06

errors:
- material_financial_anchor_not_used
- working_capital_checkpoint_not_used
```

Selected financial refs:

```text
canonical:fictional:FIC-FIN-06:inventory-current
canonical:fictional:FIC-FIN-06:trade-receivables-current
```

Selected aliases in the Directional context:

```text
E04 = inventory current
E03 = trade receivables current
```

Used financial refs in output:

```text
[]
```

---

# 4. Why FIC-FIN-06 is a real grounding failure, not a validator false reject

The model did discuss:

```text
재고와 매출채권 증가
수요의 질
현금 회수
운전자본 전환 품질
```

but cited only generic narrative aliases such as:

```text
structural-risk
remaining-unknown
operating-evidence
```

The packet contained duplicated high-level narrative:

```text
"Inventory and trade receivables have risen since year-end."
```

while the selected typed financial context contained the actual grounded facts:

```text
inventory current vs prior year-end

trade receivables current vs prior year-end
```

The M12 purpose was not merely for the model to repeat the topic.

It was to make the richer typed financial evidence part of the actual investment reasoning.

Therefore:

```text
financial concept mentioned
but selected financial refs unused
```

is a genuine grounding/specificity failure.

Do NOT weaken:

```text
material_financial_anchor_not_used
working_capital_checkpoint_not_used
```

just because narrative evidence expressed the same qualitative conclusion.

---

# 5. Preserve the original failed output

The original M12R FIC-FIN-06 output must remain unchanged.

Apply the current validator to it offline and preserve:

```text
status = FAIL
errors =
material_financial_anchor_not_used
working_capital_checkpoint_not_used
```

This proves the repair does not redefine the old failure as success.

Do not rewrite its evidence refs.

Do not patch historical raw output.

---

# 6. Repair scope — Directional financial-evidence grounding instruction

The primary repair should be a bounded Directional prompt clarification.

Required generic principle:

```text
When a selected financial_decision_context item materially supports
a financial claim, checkpoint, risk, dominant evidence, or reevaluation condition,
cite the corresponding typed financial evidence alias.

A generic narrative summary of the same financial fact may supplement
but must not substitute for the typed financial evidence ref.
```

This applies only when the selected typed financial fact is actually used.

Do not require the model to cite every selected financial item.

Do not force a financial item into the conclusion if it is immaterial.

---

# 7. Exact grounding rule

Add a concise Directional rule equivalent to:

```text
If you state or rely on a selected financial fact such as
cash conversion, complete debt/liquidity, inventory, trade receivables,
or financial/non-operating effects,
at least one relevant field carrying that claim must cite
the selected financial evidence alias.

If a typed financial ref exists for the material financial claim,
do not support the claim only with a narrative paraphrase alias.
```

Relevant fields may include:

```text
material_directional_anchor_basis
dominant_evidence
core_investment_judgment
risk_context
business_reevaluation_up/down
fundamental_new_buyer confirmation
fundamental_holder invalidation
buy_drivers / sell_drivers
```

Do not require the same ref in every field.

At least one substantively relevant claim must be grounded,
and case-specific validators may require a financial checkpoint ref
where the case contract makes that domain material.

---

# 8. No forced numeric prose

Preserve the existing M12 rule:

```text
Do not put exact numbers in prose.
```

The repair is evidence grounding, not numeric verbosity.

Acceptable:

```text
"재고와 매출채권이 연말 대비 증가해 현금 전환을 확인해야 한다."
refs = typed inventory / trade-receivables aliases
```

Not required:

```text
"재고가 180에서 300으로 증가했다."
```

The selected evidence ref carries the exact values/period lineage.

---

# 9. Narrative evidence remains allowed

Do not remove all narrative evidence.

Narrative evidence remains useful for:

```text
business thesis
structural risk interpretation
market expectation
Unknown
sector context
```

The prompt should allow:

```text
typed financial evidence
+
narrative interpretation evidence
```

to be cited together.

The repair must NOT require:

```text
financial ref only
```

The rule is:

```text
typed financial evidence cannot be replaced solely by a narrative summary
when the material claim is based on that financial fact.
```

---

# 10. Do not change financial-context selector

Freeze:

```text
financial-context selector
selected item cap = 8
sector routing
domain selection
ordering
```

For the frozen FIC-FIN-06 case, selected financial evidence must remain:

```text
inventory current
trade receivables current
```

Required:

```text
financial_context_selection_change_count = 0
```

If selector output changes unexpectedly:

```text
STOP
M12G_SCOPE_DRIFT
```

---

# 11. Do not change fictional case evidence

Freeze all 8 fictional cases:

```text
FIC-FIN-01 ... FIC-FIN-08
```

including:

```text
packet values
narrative evidence
financial-context values
sector framework
source refs
```

Do not remove the duplicate FIC-FIN-06 narrative statement to make the canary easier.

The real system can contain both narrative and typed representations.

The model must handle that situation correctly.

Required:

```text
fictional_case_change_count = 0
```

---

# 12. Prompt-change boundary

M12G is allowed to modify only the Directional financial-grounding wording required by this failure.

Do not modify:

```text
QTD/YTD instructions
cash-conversion semantics
debt completeness semantics
working-capital nonnegative semantics
non-operating semantics
financial-sector routing
missing-data semantics
balance calibration
ownership rules
```

Produce:

```text
Directional prompt before/after diff
```

and classify every changed line.

Expected:

```text
one bounded financial-evidence grounding clarification
```

No broad prompt rewrite.

---

# 13. Calibration remains frozen

Required unchanged:

```text
BUY >= 6.0
SELL >= 6.0
otherwise HOLD

0.5 increments

HOLD 5.5:4.5 BUY_LEAN
HOLD 5.0:5.0 NEUTRAL
HOLD 4.5:5.5 SELL_LEAN

adjacent-bucket tie-break toward 5.0
```

Required:

```text
directional_threshold_changed = false
directional_increment_changed = false
hold_lean_contract_changed = false
calibration_tiebreak_changed = false
```

No averaging.

No majority vote.

No fixed scorecard.

---

# 14. Validator remains strict

Preserve existing semantic validators:

```text
material financial anchor usage
working-capital checkpoint
FCF label
comparison label
debt completeness
normalized earnings
financial-sector routing
evidence ref validity
QTD/YTD
```

Do NOT relax them in M12G.

The validator may receive only a semantic-neutral bug fix if deterministic tests reveal a clearly unrelated defect.

Any such fix must be separately documented.

Default required:

```text
financial_semantic_validator_change_count = 0
qtd_ytd_validator_semantic_change_count = 0
```

---

# 15. Deterministic FIC-FIN-06 corrected-output fixture

Before model calls, create a test-only corrected FIC-FIN-06 output fixture.

It should preserve the M12R output's meaning and direction as much as possible,
but add proper typed financial grounding.

Example semantic pattern:

```text
risk / confirmation text:
"연말 이후 재고와 매출채권이 늘었지만,
잔액만으로 수요 악화나 회수 문제를 확정할 수 없다."

relevant evidence refs include:
inventory typed alias
trade-receivables typed alias
plus optional narrative/Unknown refs
```

Expected:

```text
material_financial_anchor_not_used = 0

working_capital_checkpoint_not_used = 0

year_end_as_yoy = 0

automatic deterioration claim = 0
```

This is a validator/prompt-contract test fixture.

It is NOT a replacement for the new model canary.

---

# 16. Negative grounding fixtures

Add deterministic negative fixtures.

At minimum:

## Case A — narrative-only substitution

Text correctly says:

```text
inventory / receivables increased since year-end
```

but cites only narrative structural-risk ref.

Expected:

```text
FAIL
material_financial_anchor_not_used
```

when typed financial evidence is selected and material.

## Case B — irrelevant financial ref

Working-capital claim cites a cash/net-debt financial ref.

Expected:

```text
FAIL
```

## Case C — typed ref cited only in unrelated field

Inventory ref appears only in an unrelated sector paragraph,
while the actual working-capital checkpoint claim is narrative-only.

Expected:

```text
FAIL
```

where the case contract requires checkpoint grounding.

## Case D — no selected financial evidence

No financial_context selected.

Narrative financial discussion supported only by valid non-financial evidence.

Expected:

```text
do not invent a typed-ref requirement
```

The rule applies only when relevant typed financial evidence is supplied/selected.

---

# 17. Positive grounding fixtures

At minimum:

```text
working-capital claim + typed inventory ref

working-capital claim + typed receivables ref

claim + both typed refs + narrative risk ref

cash-conversion claim + OCF typed ref

debt-resilience claim + complete debt/cash typed refs

non-operating claim + safe financial-effect typed ref
```

All should pass existing hard safety.

The model is not required to cite all selected refs,
only relevant material refs.

---

# 18. Historical M12R regression

Before any new model call:

## FIC-FIN-03

Must remain:

```text
PASS
```

under repaired QTD/YTD validator.

## FIC-FIN-06 old raw output

Must remain:

```text
FAIL
material_financial_anchor_not_used
working_capital_checkpoint_not_used
```

This proves M12G does not solve the problem by validator relaxation.

---

# 19. Prompt / selector / schema freeze audit

Before Phase B record hashes for:

```text
financial-context selector
fictional case packets
fictional aliases/source lock
Directional output schema
Price-Timing prompt/schema
```

Expected unchanged from M12R except:

```text
Directional prompt hash
```

which is allowed to change only for the bounded grounding clarification.

Required:

```text
price_timing_prompt_change_count = 0
financial_context_selection_change_count = 0
fictional_case_change_count = 0
schema_change_count = 0
```

---

# 20. Source sufficiency / lifecycle / warnings unchanged

Required:

```text
source_sufficiency_semantic_change_count = 0
daily_delta_semantic_change_count = 0
warning_semantic_change_count = 0
monitoring_lifecycle_semantic_change_count = 0
```

M12G changes only Directional grounding behavior.

No new source gate.

No production assessment/warning.

---

# 21. Price / technical / supply isolation unchanged

Required zero:

```text
directional_core_price_technical_refs
directional_core_supply_refs
financial_context_price_ref_count
financial_context_technical_ref_count
financial_context_supply_ref_count
```

No Price-Timing ownership changes.

---

# 22. Phase A deterministic gate

Before model calls require:

```text
old FIC-FIN-03 PASS

old FIC-FIN-06 remains FAIL for grounding

corrected FIC-FIN-06 fixture PASS

positive grounding fixtures PASS

negative grounding fixtures rejected

focused pytest PASS

full pytest PASS

ruff PASS

git diff --check PASS

prompt-diff scope audit PASS

selector/case/schema freeze PASS

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer ownership unchanged

production side-effect firewall PASS
```

If any fail:

```text
STOP
NO_MODEL_CALLS
```

---

# 23. New full fictional canary generation

If Phase A passes, create a NEW generation ID.

Use the same frozen 8 cases:

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

Do not reuse M12 or M12R raw outputs in the new stability sample.

Do not continue from run-1 context-02.

Start from run-1 context-01.

---

# 24. Full canary topology

Run:

```text
8 subjects
2 contexts
4 subjects per context
3 repetitions
```

Total intended:

```text
6 fictional model calls
24 subject outputs
```

Execution follows the canonical context-coupled runner.

---

# 25. Frozen runtime

Use:

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

Each context:

```text
unique invocation ID
unique runtime namespace
unique working directory
unique session identity
```

No reuse.

---

# 26. Whole-generation stop rule

If any hard semantic failure occurs:

```text
stop the new generation
preserve emitted outputs
do not selectively continue later contexts
```

If a transport/runtime failure occurs:

```text
classify separately
no wrapper retry
```

Any subsequent repaired full canary must use a new generation.

Do not stitch generations together.

---

# 27. Canary hard semantic gates

Across all completed outputs require zero:

```text
invalid financial evidence refs

material financial claim grounded only to duplicate narrative
when selected typed financial evidence is available

working-capital checkpoint ungrounded to selected typed financial evidence

price / technical / supply Directional refs

partial PPE proxy called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized / adjusted earnings invented

financial-sector generic industrial financial reasoning

missing optional financial context treated as negative evidence

fixed financial scorecard behavior

AI imperative primary action

QTD/YTD validator false reject

QTD/YTD validator false accept
```

---

# 28. Case-specific expectations

Preserve all prior M12/M12R case contracts.

## FIC-FIN-01 — strong quality

Expected:

```text
specific positive financial anchor
valid typed financial grounding
no FCF invention
```

## FIC-FIN-02 — profit/cash divergence

Expected:

```text
cash conversion limits conviction
typed cash-conversion evidence grounding
no automatic SELL solely from one weak OCF period
```

## FIC-FIN-03 — QTD/YTD conflict

Expected:

```text
explicit QTD vs cumulative/YTD distinction
both relevant evidence refs
```

## FIC-FIN-04 — non-operating boost

Expected:

```text
net-income improvement not equated with operating improvement
typed financial-effect grounding where used
no normalized earnings
```

## FIC-FIN-05 — leverage/liquidity

Expected:

```text
financial resilience limiting anchor
complete debt/cash grounding
```

## FIC-FIN-06 — working-capital build

Expected:

```text
working-capital confirmation point

not automatic deterioration

prior-year-end not called YoY

at least one material working-capital claim
grounded to selected typed inventory/receivables evidence

generic narrative summary may supplement,
not substitute
```

This is the focal case.

## FIC-FIN-07 — missing optional context

Expected:

```text
absence does not mechanically make direction more bearish
```

No forced typed ref when no relevant financial evidence is selected.

## FIC-FIN-08 — financial-sector exclusion

Expected:

```text
no industrial net debt
no generic working-capital interpretation
no interest-income-as-non-operating claim
```

---

# 29. Formal stability

If all 6 calls complete and pass hard semantics,
run the existing formal stability classifier over all 8 subjects × 3 repetitions.

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

Do not create a new classifier.

---

# 30. Financial grounding audit

Add an explicit canary audit:

For each subject/repetition report:

```text
selected financial refs

used financial refs

material financial anchor refs

financial checkpoint refs

narrative-only duplicate refs

grounding status
```

Summary counts:

```text
selected_financial_ref_count

used_financial_ref_count

material_financial_anchor_grounding_failure_count

working_capital_grounding_failure_count

narrative_substitution_failure_count
```

This must distinguish:

```text
financial item selected but legitimately immaterial/not used
```

from:

```text
financial item is the basis of the claim but typed ref is omitted
```

Do not force use of every selected item.

---

# 31. Message specificity advisory

If full canary completes, run the existing advisory.

Add:

```text
typed financial anchor specificity
```

as an advisory dimension.

Do not require exact numeric prose.

Measure whether outputs distinguish:

```text
cash conversion
debt/liquidity
working capital
non-operating effect
period conflict
```

where relevant.

Do not solve repetition with synonyms.

---

# 32. No real issuer model calls

Required:

```text
model_calls_real = 0
real_issuer_model_exposure_count = 0
```

Do not run a fresh real cohort in M12G.

Fresh real proof is authorized only after the full canary passes.

---

# 33. Production side-effect firewall

Required final:

```text
provider_source_fetches = 0

production_db_mutations = 0
monitoring_registrations = 0
assessment_persistence_mutations = 0
warning_mutations = 0
notification_queue_writes = 0
production_sends = 0

main_merges = 0
deployments = 0
live_v2_changes = 0
night_futures_changes = 0

automatic_monitoring_resume = 0
```

Expected model calls only:

```text
fictional = 6 if full canary completes
real = 0
judge = 0
```

---

# 34. Required artifacts — provenance / root cause

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m12g-scope-freeze

04-m12r-failure-reproduction
05-fic-fin-06-grounding-root-cause
06-financial-grounding-contract
07-prompt-before-after
08-validator-no-relaxation-proof
```

---

# 35. Required artifacts — deterministic repair proof

Produce:

```text
09-old-fic-fin-03-regression
10-old-fic-fin-06-remains-fail
11-corrected-fic-fin-06-fixture

12-positive-grounding-fixture-manifest
13-negative-grounding-fixture-manifest
14-narrative-substitution-negative-control
15-irrelevant-financial-ref-negative-control
16-no-selected-financial-context-control

17-financial-context-selection-freeze-proof
18-fictional-case-freeze-proof
19-schema-freeze-proof
20-price-timing-freeze-proof

21-source-sufficiency-no-change-proof
22-daily-delta-no-change-proof
23-renderer-ownership-no-change-proof
```

---

# 36. Required deterministic validation artifacts

Produce:

```text
24-focused-test-results
25-full-test-results
26-ruff-and-diff-results
27-phase-a-gate
```

---

# 37. Required new fictional-canary artifacts

If Phase A passes:

```text
28-fictional-canary-generation-manifest
29-fictional-canary-source-lock

30-run-1-context-01
31-run-1-context-02

32-run-2-context-01
33-run-2-context-02

34-run-3-context-01
35-run-3-context-02

36-full-fictional-canary-semantic-audit
37-full-fictional-canary-financial-grounding-audit
38-full-fictional-canary-validator-audit
39-full-fictional-canary-stability
40-full-fictional-canary-message-specificity-advisory
41-runtime-observations
```

Preserve raw:

```text
prompt
schema
output
receipt
transport log
run document
```

for every attempted call.

---

# 38. Required completion artifacts

Produce:

```text
42-fresh-real-proof-readiness-decision
43-production-no-change
44-schedule-pause-observation
45-master-workflow-update
46-program-completion
```

---

# 39. M12G deterministic acceptance criteria

Pass only if:

```text
old FIC-FIN-03 remains PASS

old FIC-FIN-06 remains FAIL
for missing typed financial grounding

corrected FIC-FIN-06 fixture PASS

narrative-only substitution rejected

irrelevant financial ref substitution rejected

case with no selected financial context does not get a fake grounding requirement

Directional prompt change is bounded to grounding clarification

financial-context selector unchanged

fictional cases unchanged

schema unchanged

QTD/YTD validator unchanged

financial semantic validators not relaxed

threshold/calibration unchanged

focused/full tests PASS
ruff PASS
git diff --check PASS
```

---

# 40. M12G full-canary acceptance criteria

Pass only if:

```text
6 / 6 model contexts complete successfully

24 / 24 subject outputs schema-valid

invalid financial reference count = 0

hard financial semantic violation count = 0

material financial anchor grounding failure count = 0

working-capital grounding failure count = 0

narrative substitution failure count = 0

QTD/YTD false reject count = 0
QTD/YTD false accept count = 0

price/technical/supply Directional violation count = 0

AI imperative primary action count = 0

opposite-direction reversal count = 0

wrapper retry count = 0

unexpected timeout/capacity/orphan count = 0
```

Formal stability must be measured if the full 6-call canary completes.

---

# 41. Failure handling

## If FIC-FIN-06 still omits typed financial grounding

Classify:

```text
PROMPT_GROUNDING_INSUFFICIENT
```

Do not weaken validator.

Possible next scope:

```text
FINANCIAL_CONTEXT_OUTPUT_GROUNDING_ARCHITECTURE_REVIEW
```

only if a prompt-only repair is demonstrably insufficient.

## If a different semantic failure appears

Classify the exact case and contract.

Recommended:

```text
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

Do not broaden scope automatically.

## If stability fails after hard semantics pass

Classify separately:

```text
financial evidence interpretation variability
vs
boundary calibration uncertainty
```

Do not change threshold without a separate root-cause review.

## If runtime fails

Classify transport/runtime separately.

Do not call it a semantic failure.

---

# 42. Next-scope decision

## A. Full canary PASS

Set:

```text
fresh_real_proof_readiness = READY
```

Recommended:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF
```

Do not start it inside M12G.

## B. Grounding remains the only blocker

```text
fresh_real_proof_readiness = NOT_READY
next_scope =
FINANCIAL_CONTEXT_OUTPUT_GROUNDING_ARCHITECTURE_REVIEW
```

## C. New semantic blocker

```text
fresh_real_proof_readiness = NOT_READY
next_scope =
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

## D. Runtime blocker

Use a bounded runtime repair scope.

---

# 43. Production readiness

Even if M12G passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real generalization proof
production integration review
explicit user authorization
```

Monitoring schedules remain paused.

---

# 44. Program-completion fields

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
m12g_status

m12r_grounding_root_cause
financial_grounding_repair_status

old_fic_fin_03_regression_status
old_fic_fin_06_regression_status
corrected_fic_fin_06_status

positive_grounding_fixture_count
positive_grounding_fixture_pass_count
negative_grounding_fixture_count
negative_grounding_fixture_rejected_count

financial_semantic_validator_change_count
qtd_ytd_validator_semantic_change_count

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

selected_financial_ref_count
used_financial_ref_count

material_financial_anchor_grounding_failure_count
working_capital_grounding_failure_count
narrative_substitution_failure_count

validator_false_reject_count
validator_false_accept_count

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

Anything not measured:

```text
NOT_MEASURED
```

---

# 45. Artifact integrity

Freeze:

```text
program completion
master workflow
all deterministic artifacts
all attempted model-call artifacts
```

before final artifact index.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

---

# 46. Final task principle

M12R fixed the validator.

The new problem is real but narrow:

```text
the model understood the working-capital concept
but bypassed the typed financial evidence
and grounded the conclusion only in a duplicate narrative summary.
```

The correct repair is:

```text
keep financial selector/cases/validator frozen
→ clarify that material financial claims must cite the typed financial evidence
→ prove old failure still fails
→ prove a properly grounded version passes
→ rerun all 8 cases from a new generation
→ measure full stability
```

Not:

```text
weaken the validator
```

Not:

```text
delete duplicate narrative evidence from the case
```

Not:

```text
force exact numbers into prose
```

Not:

```text
require every selected financial ref to be cited
```

Not:

```text
change thresholds/calibration
```

Not:

```text
continue from run-2 after the failed M12R generation
```

Not:

```text
run a fresh real cohort before the full repaired canary passes
```

And not:

```text
resume production monitoring
```

Make the model ground material financial reasoning in the actual typed financial evidence,
then rerun the fictional proof cleanly.
