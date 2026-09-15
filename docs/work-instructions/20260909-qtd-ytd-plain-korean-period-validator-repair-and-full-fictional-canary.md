# Thesis Monitor — QTD/YTD Plain-Korean Period Validator Repair & Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-qtd-ytd-plain-korean-period-validator-repair-and-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-qtd-ytd-plain-korean-period-validator-repair-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12D — Bounded Directional Financial Context Repair
        QTD/YTD Plain-Korean Period Claim Validator
        + Full Fictional Canary
```

This task begins only after M12C stopped with:

```text
status = M12C_CANARY_FAIL
stop_reason = M12C_NEW_BOUNDED_SEMANTIC_BLOCKER
next_scope = BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

M12C successfully repaired the working-capital grounding validator.

The remaining blocker is run-3 FIC-FIN-03:

```text
qtd_ytd_conflict_not_explicit
```

The preserved raw output, however, explicitly distinguishes:

```text
분기 영업흑자
누적 영업손실
```

and cites the supplied QTD/YTD evidence together in multiple material fields.

Therefore M12D must first freeze the exact root cause.
If the preserved output is confirmed to satisfy the existing semantic contract,
repair the QTD/YTD validator narrowly and rerun the entire 8-subject fictional canary
from a new generation.

M12D must NOT:

```text
change the fictional cases
change first-class typed evidence architecture
change financial-context selection
change Directional prompt
change BUY/SELL thresholds
change 0.5 balance increments
change HOLD lean
change calibration tie-break
change source mappings
change source sufficiency
change Price-Timing
change renderer ownership
weaken working-capital grounding
run a fresh real issuer proof
merge/deploy production
resume monitoring schedules
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260909-materiality-scoped-working-capital-grounding-validator-repair-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
2ce3b4e501743fb9e640b62807a96658e54b1f682298a486ea0d0c3dc32dd92e
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest artifact integrity was independently verified:

```text
payload files = 121
artifact index mismatches = 0
size mismatches = 0
```

Latest M12C result:

```text
working_capital_grounding_root_cause =
SELECTION_TRIGGERED_OVERREACH

working_capital_grounding_repair_status =
PASS

M12C =
BLOCKED

fresh_real_proof_readiness =
NOT_READY

production_readiness =
NOT_READY
```

Reported repository provenance:

```text
base_sha =
0615ea399f295476c2bf47d66ac441eef04ec0d8

work_instruction_commit =
6a75e839fd05d7d8b095ae5d23180f621b7abb3a

implementation_commit =
4f367e27588b030508ae4c9d4ad0181caf64d0de

final/report =
f1f2d71ef3d93ad344c9abcd0d557477cfaa0b95

branch =
codex/20260909-materiality-scoped-working-capital-grounding-validator-repair-full-fictional-canary
```

At task start use actual repository HEAD as authority.

---

# 2. M12C completed work is frozen

M12C correctly repaired the WC grounding contract from:

```text
selection-triggered checkpoint requirement
```

to:

```text
material-claim / explicit-metric-use triggering
```

Frozen forensic root cause:

```text
SELECTION_TRIGGERED_OVERREACH
```

Required preserved regressions:

```text
FIC-FIN-02 run-1 = PASS
FIC-FIN-02 run-2 = PASS after WC repair

old FIC-FIN-06 narrative-only = FAIL
corrected FIC-FIN-06 = PASS

production fictional branches = 0
```

M12C deterministic validation:

```text
focused pytest = 609 passed

full pytest = 3071 passed

ruff = PASS

git diff --check = PASS
```

Do not modify this WC validator in M12D.

Required:

```text
working_capital_validator_semantic_change_count = 0
```

---

# 3. M12C canary completed sample

Generation:

```text
20260909-m12c-fictional-20260909T101525Z-4f367e27588b
```

Completed:

```text
run-1 context-01
run-1 context-02

run-2 context-01
run-2 context-02

run-3 context-01
```

Stopped before:

```text
run-3 context-02
```

Counts:

```text
fictional model calls = 5 / 6

subject outputs = 20 / 24

schema pass = 20 / 20

model context transport success = 5 / 5

timeout = 0
capacity failure = 0
orphan process = 0
wrapper retry = 0
```

Formal stability:

```text
NOT_MEASURED
```

because the full 6-call sample did not complete.

---

# 4. M12C grounding architecture result is good and frozen

Across the completed 20 outputs:

```text
selected typed financial refs = 41

first-class typed financial refs = 41

used typed financial refs = 40

material financial anchor grounding failures = 0

working-capital grounding failures = 0

narrative substitution failures = 0

irrelevant financial ref grounding failures = 0
```

Therefore M12D must NOT reopen:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION
```

The remaining blocker is not the first-class evidence architecture.

---

# 5. Authoritative failing row

Failing row:

```text
run = 3
context = 1
ticker = FIC-FIN-03
case = QTD/YTD operating conflict
```

Validator:

```text
qtd_evidence_ref_count = 1
ytd_evidence_ref_count = 1

required = true

errors =
qtd_ytd_conflict_not_explicit

explicit_claim_count = 0
linked_claim_count = 7
```

Supplied aliases:

```text
E01 =
canonical:fictional:FIC-FIN-03:operating-profit-qtd
metric = operating_income
period = QTD

E08 =
canonical:fictional:FIC-FIN-03:operating-profit-ytd
metric = operating_income
period = YTD
```

Do not change these aliases or case facts.

---

# 6. Preserved run-3 output — independent semantic evidence

The raw FIC-FIN-03 output includes:

## core_investment_judgment

```text
"분기 영업흑자와 누적 영업손실이 상충해
어느 방향의 충분성도 확보되지 않았다."

refs:
E01
E08
```

## dominant_evidence

```text
"서로 다른 기간의 영업흑자와 영업손실이 동시에 존재한다."

refs:
E01
E08
```

## earnings_estimate_context

```text
"분기 영업흑자와 누적 영업손실을
기간별로 구분해 함께 반영한다."

refs:
E01
E08
```

## business_reevaluation_up

```text
"분기 영업흑자가 다음 보고기간에도 지속되고
누적 영업손실이 해소되는 경우다."

refs include:
E01
E08
```

## business_reevaluation_down

```text
"최근 분기 반등이 이어지지 않고
누적 영업손실이 남는 경우다."

refs include:
E08
```

The candidate also says:

```text
"분기와 누적 결과를 섞지 않는다."
```

This is substantively an explicit QTD/YTD distinction.

M12D must not classify the preserved row as a model semantic failure
unless the current frozen semantic contract explicitly requires something more
than the above.

---

# 7. Key comparison — run-1 / run-2 / run-3

FIC-FIN-03 run-1 PASS used wording such as:

```text
"최근 분기 영업흑자와 누적 영업손실..."
```

FIC-FIN-03 run-2 PASS used wording such as:

```text
"최근 분기 흑자와 연초 이후 누적 적자..."
```

FIC-FIN-03 run-3 FAIL used wording such as:

```text
"분기 영업흑자와 누적 영업손실..."
```

The meaningful difference may be:

```text
최근 분기
vs
plain 분기
```

while the YTD marker remains explicit:

```text
누적
```

This suggests a possible validator claim-language coverage defect.

Do not assume this exact code defect.
Freeze it through source inspection and replay first.

---

# 8. Forensic phase — before implementation

Before code changes:

1. Load the exact M12C run-1, run-2, run-3 FIC-FIN-03 outputs.
2. Apply the current validator to all three.
3. Trace:
   - candidate claim paths inspected
   - QTD lexical markers detected
   - YTD lexical markers detected
   - QTD evidence refs
   - YTD evidence refs
   - same-metric linkage
   - explicit-claim decision
4. Inspect the current implementation of:
   ```text
   validate_qtd_ytd_conflict_semantics
   ```
5. Freeze one root-cause classification:

```text
PLAIN_KOREAN_QTD_MARKER_FALSE_REJECT

CLAIM_EXTRACTION_PATH_DEFECT

EVIDENCE_LINKAGE_DEFECT

GENUINE_MODEL_SEMANTIC_FAILURE

OTHER_BOUNDED_VALIDATOR_DEFECT
```

No implementation before this root-cause artifact is frozen.

---

# 9. Branch A — if false reject is confirmed

If classification is any bounded validator false-reject class:

```text
PLAIN_KOREAN_QTD_MARKER_FALSE_REJECT

CLAIM_EXTRACTION_PATH_DEFECT

EVIDENCE_LINKAGE_DEFECT

OTHER_BOUNDED_VALIDATOR_DEFECT
```

repair only the generic QTD/YTD validator.

Do not modify the Directional prompt.

Do not modify the fictional case.

Do not relax the requirement for explicit period distinction.

---

# 10. Branch B — if genuine model failure is proven

If classification is:

```text
GENUINE_MODEL_SEMANTIC_FAILURE
```

then:

```text
STOP
NO_MODEL_CALLS
```

Do not weaken the validator.

Set:

```text
next_scope =
BOUNDED_DIRECTIONAL_QTD_YTD_EXPLICITNESS_REPAIR
```

or a more precise prompt/output-structure scope supported by the forensic evidence.

M12D then ends as a root-cause review.

---

# 11. Target semantic contract

The generic validator should accept a claim only when all required conditions hold.

For a same-metric QTD/YTD conflict:

```text
1. supplied QTD evidence exists

2. supplied YTD evidence exists

3. the claim is linked to the relevant QTD/YTD evidence
   through evidence refs / structured claim linkage

4. the claim text explicitly distinguishes:
   quarter-period meaning
   AND
   cumulative/YTD meaning
```

Do not accept period words with no relevant evidence linkage.

---

# 12. QTD Korean marker family

If Branch A confirms a lexical coverage defect,
support bounded Korean QTD expressions including semantically explicit forms such as:

```text
분기

분기 기준

분기 실적

분기 영업흑자

분기 영업손실

최근 분기

이번 분기

해당 분기

직전 분기
```

The validator must not pass merely because the character sequence:

```text
분기
```

appears anywhere.

Plain `분기` is valid only in a claim that:

```text
is linked to a supplied QTD ref

and expresses the relevant financial metric/period contrast.
```

---

# 13. YTD / cumulative Korean marker family

Preserve M12R support for semantically explicit cumulative expressions:

```text
YTD

year-to-date

cumulative

누계

누적

누적 기준

연초 이후

연초부터

연초 이후 누적

연초부터 누적
```

Do not regress valid M12R fixtures.

---

# 14. Plain-분기 false-accept protection

Required negative controls include:

```text
"분기점이 중요하다."

"사업의 분기별 구조를 본다."
when no QTD financial evidence is linked

"분기" appears only in an unrelated sector sentence

plain 분기 appears with only YTD ref

plain 분기 appears with QTD ref
but no explicit YTD/cumulative period statement

QTD/YTD refs exist
but text says only "서로 다른 실적이 있다."
```

No loose substring pass.

---

# 15. Explicit period contrast may be concise

The semantic contract must allow concise but explicit forms such as:

```text
"분기 흑자와 누적 적자가 공존한다."

"분기 영업흑자와 누적 영업손실이 상충한다."

"분기 기준은 흑자지만 연초 이후 누적 기준은 적자다."
```

when the relevant same-metric QTD/YTD refs are linked.

Do not require the word:

```text
최근
```

if QTD evidence linkage already establishes the quarter period.

Do not require the literal token:

```text
YTD
```

when a valid Korean cumulative expression is present.

---

# 16. Claim-path coverage

The validator must inspect all existing material Directional claim paths
that the frozen contract intends to count.

At minimum audit:

```text
core_investment_judgment

dominant_evidence

earnings_estimate_context

business_thesis_context

buy_drivers

sell_drivers

business_reevaluation_up

business_reevaluation_down

fundamental_new_buyer

fundamental_holder

sector_interpretation
```

Do not add arbitrary fields without checking the current contract.

If run-3 failed because explicit text existed only on a path the validator skipped,
repair the generic path coverage.

Do not special-case FIC-FIN-03.

---

# 17. Evidence-linkage rule

For a QTD/YTD conflict claim to count,
the validator should prefer:

```text
same claim carries both relevant QTD and YTD refs
```

or an existing structured linkage that proves both periods.

A candidate can also have explicit period distinction in multiple linked fields
if the current frozen design intentionally aggregates claim coverage.

Do not infer linkage from nearby text without evidence refs.

Do not use ticker/case IDs.

---

# 18. Historical regression matrix

Before any new model calls, repaired validator must classify:

```text
M12R historical valid FIC-FIN-03 output = PASS

M12C run-1 FIC-FIN-03 = PASS

M12C run-2 FIC-FIN-03 = PASS

M12C run-3 FIC-FIN-03 = PASS
```

only if Branch A false reject is confirmed.

Also preserve all previous QTD/YTD negative fixtures as rejected.

---

# 19. New positive fixtures

At minimum:

```text
"분기 영업흑자와 누적 영업손실이 상충한다."
+ same-metric QTD/YTD refs
→ PASS

"분기 흑자와 연초 이후 누적 적자가 공존한다."
+ QTD/YTD refs
→ PASS

"분기 기준은 흑자지만 누계 기준은 적자다."
+ QTD/YTD refs
→ PASS

"이번 분기는 흑자지만 YTD는 손실이다."
+ QTD/YTD refs
→ PASS
```

---

# 20. New negative fixtures

At minimum:

```text
plain "분기" unrelated to a financial period

QTD word without QTD evidence ref

YTD/cumulative word without YTD evidence ref

QTD + YTD refs but only one period explicitly described

different metrics:
QTD operating income
vs
YTD revenue
→ not a same-metric conflict

same refs but vague:
"실적이 엇갈린다."
→ reject

"분기 영업흑자"
with no cumulative/YTD explicit statement
→ reject
```

---

# 21. Preserve working-capital validator repair

M12C WC repair must remain byte/semantic frozen.

Required:

```text
working_capital_validator_semantic_change_count = 0
```

Regression:

```text
FIC-FIN-02 M12B run-2 = PASS

old FIC-FIN-06 narrative-only = FAIL

corrected FIC-FIN-06 = PASS

M12B/M12C FIC-FIN-06 passing output = PASS
```

M12D must not reintroduce selection-triggered WC overreach.

---

# 22. Preserve first-class typed evidence architecture

Required unchanged:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

selected-only projection

alias reuse

neutral statements

financial_decision_context detail block
```

Required:

```text
first_class_projection_change_count = 0
financial_context_selection_change_count = 0
```

---

# 23. Prompt / schema / calibration freeze

Required:

```text
directional_prompt_change_count = 0

price_timing_prompt_change_count = 0

output_schema_change_count = 0

fictional_case_change_count = 0

directional_threshold_changed = false

directional_increment_changed = false

hold_lean_contract_changed = false

calibration_tiebreak_changed = false
```

No fixed scorecard.

No voting.

No averaging.

---

# 24. Other financial validators remain frozen

Do not change:

```text
FCF label validator

prior-year-end vs YoY validator

debt completeness validator

normalized earnings validator

financial-sector routing validator

evidence-ref validator
```

Required:

```text
non_qtd_ytd_financial_validator_change_count = 0
```

---

# 25. Source sufficiency / lifecycle / warnings unchanged

Required:

```text
source_sufficiency_semantic_change_count = 0

daily_delta_semantic_change_count = 0

monitoring_lifecycle_semantic_change_count = 0

warning_semantic_change_count = 0
```

No provider/source changes.

---

# 26. Phase A deterministic gate

Only if Branch A executes, before model calls require:

```text
M12C run-3 FIC-FIN-03 = PASS for the correct period/evidence reason

M12C run-1/run-2 FIC-FIN-03 remain PASS

M12R historical FIC-FIN-03 remains PASS

all QTD/YTD positive fixtures PASS

all QTD/YTD negative fixtures rejected

false accept count = 0

false reject count = 0

WC grounding regressions PASS

first-class architecture freeze PASS

Directional prompt unchanged

output schema unchanged

threshold/calibration unchanged

source sufficiency unchanged

Daily Delta unchanged

focused pytest PASS

full pytest PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

If any fail:

```text
STOP
NO_MODEL_CALLS
```

---

# 27. New full fictional canary generation

Only after Branch A + Phase A PASS.

Create a NEW generation.

Use the exact same frozen 8 cases:

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

Do not alter values/evidence/narrative duplicates.

Do not continue run-3/context-02 from the M12C generation.

Start again at:

```text
run-1/context-01
```

---

# 28. Canary topology

Run:

```text
8 subjects
2 contexts
4 subjects/context
3 repetitions
```

Total:

```text
6 fictional model calls
24 subject outputs
```

No real issuer calls.

No judge calls.

---

# 29. Frozen runtime

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

# 30. Whole-generation stop rule

On any hard semantic failure:

```text
stop immediately
preserve outputs
do not continue later contexts
```

On runtime failure:

```text
classify separately
no wrapper retry
```

Any later rerun after a repair must use another new generation.

---

# 31. Canary hard gates

Across all completed outputs require zero:

```text
invalid financial evidence refs

true material financial anchor grounding failures

true working-capital grounding failures

narrative substitution failures

irrelevant financial ref grounding failures

price/technical/supply Directional refs

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

financial-sector generic misuse

missing optional context treated as bearish

fixed financial scoring

QTD/YTD false rejects

QTD/YTD false accepts

QTD/YTD true semantic violations

AI imperative primary action
```

---

# 32. FIC-FIN-03 hard case expectation

For each repetition of FIC-FIN-03:

Required:

```text
same-metric QTD operating-income evidence exists

same-metric YTD operating-income evidence exists

candidate explicitly distinguishes quarter-period result
from cumulative/YTD result

relevant QTD/YTD refs are cited

no quarter/YTD period collapse
```

Accepted semantic examples include:

```text
"분기 흑자와 누적 적자가 공존한다."

"최근 분기는 흑자지만 연초 이후 누적 기준은 적자다."

"분기 기준은 개선됐지만 누계 기준은 손실이다."
```

Do not require one exact phrase.

---

# 33. Preserve FIC-FIN-02 / FIC-FIN-06 contracts

## FIC-FIN-02

Hard focal domain:

```text
CASH_CONVERSION
```

Inventory can remain secondary/context-only unless made material.

## FIC-FIN-06

Hard focal domain:

```text
WORKING_CAPITAL
```

Material WC claim must be grounded to typed inventory/receivable refs.

M12C repaired this distinction.

Do not regress it.

---

# 34. Formal stability

If all 6 contexts complete and hard semantics pass,
run the existing formal stability classifier.

Report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

No majority vote.

No balance averaging.

Required:

```text
opposite_direction_reversal_count = 0
```

The partial M12C generation is not part of the new formal sample.

---

# 35. Stability interpretation

If hard semantics pass but formal instability remains:

Separate:

```text
threshold-adjacent boundary uncertainty

vs

material financial evidence interpretation variability
```

Do not change calibration in M12D.

Any calibration review must be separately authorized.

---

# 36. Message specificity advisory

If full canary completes,
run the existing advisory for 24 outputs.

Measure:

```text
typed financial anchor specificity

period specificity

case-specific checkpoints

generic substantive repetition

renderer-introduced repetition
```

Advisory does not override hard semantics.

---

# 37. No real issuer exposure

Required:

```text
model_calls_real = 0

real_issuer_model_exposure_count = 0
```

Fresh real proof is still a later task.

---

# 38. Production side-effect firewall

Required:

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

automatic_monitoring_resume = 0
```

Approved monitoring schedules remain paused.

---

# 39. Required artifacts — forensic phase

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12d-scope-freeze

04-fic-fin-03-run1-run2-run3-comparison

05-run3-qtd-ytd-claim-path-trace

06-run3-qtd-ytd-evidence-linkage-trace

07-qtd-ytd-validator-source-audit

08-qtd-ytd-root-cause
```

Freeze Branch A/B before implementation.

---

# 40. Required Branch A repair artifacts

If Branch A executes:

```text
09-qtd-ytd-validator-before-after

10-korean-qtd-marker-contract

11-korean-ytd-marker-regression

12-claim-path-coverage-contract

13-evidence-linkage-contract

14-run3-fic-fin-03-regression

15-qtd-ytd-positive-fixtures

16-qtd-ytd-negative-fixtures

17-false-accept-control

18-false-reject-control
```

---

# 41. Required freeze/no-change artifacts

Produce:

```text
19-working-capital-validator-freeze-proof

20-first-class-projection-freeze-proof

21-directional-prompt-freeze-proof

22-output-schema-freeze-proof

23-other-financial-validator-freeze-proof

24-price-timing-no-change-proof

25-source-sufficiency-no-change-proof

26-daily-delta-no-change-proof

27-renderer-ownership-no-change-proof
```

---

# 42. Required deterministic validation artifacts

Produce:

```text
28-focused-test-results

29-full-test-results

30-ruff-and-diff-results

31-model-call-gate
```

If Branch B:

```text
31-model-call-gate =
NO_MODEL_CALLS
```

---

# 43. Required full-canary artifacts

Only if Branch A + gate PASS:

```text
32-fictional-canary-generation-manifest

33-fictional-canary-source-lock

34-run-1-context-01

35-run-1-context-02

36-run-2-context-01

37-run-2-context-02

38-run-3-context-01

39-run-3-context-02

40-full-fictional-semantic-audit

41-full-fictional-grounding-audit

42-full-fictional-qtd-ytd-validator-audit

43-full-fictional-stability

44-full-fictional-message-specificity-advisory

45-runtime-observations
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

for every attempted model call.

---

# 44. Required completion artifacts

Produce:

```text
46-fresh-real-proof-readiness-decision

47-production-no-change

48-schedule-pause-observation

49-master-workflow-update

50-program-completion
```

---

# 45. Branch A acceptance criteria

QTD/YTD repair is accepted only if:

```text
preserved M12C run-3 FIC-FIN-03 now PASSes

plain Korean "분기" is accepted only in claim/evidence-specific QTD context

valid 누적/누계/연초 이후 cumulative wording remains accepted

unrelated/vague "분기" wording remains rejected

same-metric QTD/YTD evidence linkage remains required

run-1/run-2/historical FIC-FIN-03 remain PASS

WC validator remains unchanged

first-class architecture remains unchanged

Directional prompt unchanged

output schema unchanged

threshold/calibration unchanged

focused/full tests PASS

ruff PASS

git diff --check PASS
```

---

# 46. Full-canary acceptance criteria

If Branch A proceeds:

```text
6 / 6 model contexts complete

24 / 24 rows schema PASS

hard financial semantic violation count = 0

QTD/YTD false reject count = 0

QTD/YTD false accept count = 0

QTD/YTD true semantic violation count = 0

working-capital grounding failure count = 0

material financial anchor grounding failure count = 0

narrative substitution failure count = 0

price/technical/supply violations = 0

AI imperative primary action = 0

opposite-direction reversal count = 0

wrapper retry = 0

unexpected timeout/capacity/orphan = 0
```

Formal stability must be measured.

---

# 47. Failure handling

## If forensic confirms genuine model semantic failure

Do not repair validator.

Set:

```text
status =
M12D_REVIEW_COMPLETE_MODEL_EXPLICITNESS_REQUIRED

fresh_real_proof_readiness =
NOT_READY

next_scope =
BOUNDED_DIRECTIONAL_QTD_YTD_EXPLICITNESS_REPAIR
```

No model calls.

## If repaired validator still false-rejects

Use:

```text
BOUNDED_QTD_YTD_VALIDATOR_REPAIR
```

No real proof.

## If a different semantic blocker appears

Use:

```text
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

with exact contract.

## If hard semantics pass but stability fails

Create a separate stability root-cause review.

Do not modify thresholds automatically.

## If runtime fails

Classify runtime separately.

---

# 48. Next-scope decision

## A. Full canary PASS

```text
fresh_real_proof_readiness = READY

next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF
```

Do not start that real proof inside M12D.

## B. Validator repair insufficient

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_QTD_YTD_VALIDATOR_REPAIR
```

## C. Genuine model period-explicitness failure

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_DIRECTIONAL_QTD_YTD_EXPLICITNESS_REPAIR
```

## D. New bounded semantic failure

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

---

# 49. Production readiness

Even if M12D full canary passes:

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

# 50. Program-completion fields

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

m12c_status
m12d_status

qtd_ytd_root_cause
qtd_ytd_repair_status

fic_fin_03_run1_regression_status
fic_fin_03_run2_regression_status
fic_fin_03_run3_regression_status
historical_fic_fin_03_regression_status

qtd_ytd_positive_fixture_count
qtd_ytd_positive_fixture_pass_count
qtd_ytd_negative_fixture_count
qtd_ytd_negative_fixture_rejected_count

validator_false_reject_count
validator_false_accept_count
qtd_ytd_true_semantic_violation_count

working_capital_validator_semantic_change_count
first_class_projection_change_count
financial_context_selection_change_count

directional_prompt_change_count
price_timing_prompt_change_count
output_schema_change_count

non_qtd_ytd_financial_validator_change_count

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

material_financial_anchor_grounding_failure_count
working_capital_grounding_failure_count
narrative_substitution_failure_count

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

Anything unmeasured:

```text
NOT_MEASURED
```

---

# 51. Artifact integrity

Freeze all reports/master workflow/model-call artifacts before final index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 52. Final task principle

M12C fixed the working-capital validator correctly.

The remaining failing row is different:

```text
the model explicitly says
"분기 영업흑자와 누적 영업손실"

and links the QTD/YTD evidence,

but the validator still reports
qtd_ytd_conflict_not_explicit.
```

The correct next move is:

```text
forensically compare run-1/run-2/run-3

→ determine why plain Korean "분기" was not recognized

→ repair only the generic claim/evidence-aware period validator
   if false reject is confirmed

→ preserve WC / first-class / prompt / calibration contracts

→ rerun all 8 cases from a fresh generation

→ measure full formal stability
```

Not:

```text
add another prompt instruction before proving a model failure
```

Not:

```text
special-case FIC-FIN-03
```

Not:

```text
accept any occurrence of "분기"
```

Not:

```text
weaken QTD/YTD evidence linkage
```

Not:

```text
change thresholds/calibration
```

Not:

```text
continue only run-3/context-02
```

Not:

```text
start the real cohort before the full fictional canary passes
```

And not:

```text
resume production monitoring
```

Fix the period validator only if the preserved output already satisfies the semantic contract.
