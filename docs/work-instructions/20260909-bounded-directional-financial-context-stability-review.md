# Thesis Monitor — Bounded Directional Financial Context Stability Review

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-bounded-directional-financial-context-stability-review.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-bounded-directional-financial-context-stability-review-report.zip
```

Master-workflow phase:

```text
M12S — Bounded Directional Financial Context Stability Review
```

This task begins only after M12D completed the full fictional financial-context canary and stopped on formal stability:

```text
status = M12D_CANARY_FAIL
stop_reason = M12D_FINANCIAL_INTERPRETATION_STABILITY_FAILURE
next_scope = BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_STABILITY_REVIEW
```

M12D semantic correctness is preserved.

M12S is a **model-free stability root-cause review**.

It must determine whether the remaining repeated-run variance is caused by:

```text
true financial-evidence interpretation variance

adjacent Directional bucket calibration ambiguity

new-buyer stance calibration ambiguity

holder stance calibration ambiguity

anchor/presentation variance without decision-meaning variance

formal-classifier sensitivity

or a mixed cause
```

M12S must NOT:

```text
run any model calls
change BUY/SELL thresholds
change 0.5 increments
change HOLD lean mapping
change calibration tie-break
change financial-context selector
change first-class typed evidence architecture
change source mappings
change QTD/YTD validator
change working-capital validator
change Directional prompt
change output schema
change Price-Timing
change renderer
run a real holdout
merge/deploy production
resume monitoring schedules
```

The goal is to freeze the exact root cause and the smallest next repair, if any.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260909-qtd-ytd-plain-korean-period-validator-repair-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
b7eb58d997048799c499daa7b2be29a429791772781d1ab23c6540f03fa7a9a3
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M12D state:

```text
QTD/YTD repair = PASS

full fictional canary model contexts = 6 / 6 PASS

fictional output rows = 24 / 24 schema PASS

hard financial semantic violation count = 0

typed financial grounding failure count = 0

QTD/YTD false reject count = 0

QTD/YTD false accept count = 0

fresh real proof readiness = NOT_READY

production readiness = NOT_READY
```

Reported M12D provenance:

```text
base_sha =
6c1928846c25063b66662da6ff9465988ac44e98

work_instruction_commit =
dd28946351e9a1517d1c50992c93265113efdba0

implementation_commit =
3ad040f73f7f159519cb5d47058571c101f1a6c3

final/report =
e557b152c7f92e95e664b0cf58398a243c6fc60a

branch =
codex/20260909-qtd-ytd-plain-korean-period-validator-repair-full-fictional-canary
```

Use actual repository HEAD as authority at task start.

---

# 2. M12D hard semantic result is frozen

M12D completed all 6 fictional calls.

Runtime:

```text
model = gpt-5.6-sol
reasoning = xhigh

model calls = 6 / 6 success

timeout = 0
capacity failure = 0
orphan process = 0
wrapper retry = 0
```

Semantic audit:

```text
24 / 24 schema PASS

invalid financial refs = 0

price/technical/supply Directional refs = 0

partial PPE called FCF = 0

prior-year-end called YoY = 0

partial debt called total debt = 0

normalized earnings claims = 0

financial-sector generic misuse = 0

fixed financial score rules = 0

QTD/YTD conflict violations = 0

QTD/YTD false reject = 0
QTD/YTD false accept = 0

AI imperative primary action = 0
```

Financial grounding:

```text
selected typed refs = 45

first-class typed refs = 45

used typed refs = 45

material financial anchor grounding failure = 0

working-capital grounding failure = 0

narrative substitution failure = 0

irrelevant financial ref failure = 0
```

Message specificity advisory:

```text
specific financial anchor = PASS 24 / 24

period/basis specificity = PASS

typed financial anchor specificity = PASS

renderer-introduced repetition = 0
```

Do not reopen these solved issues in M12S.

---

# 3. M12D formal stability result

Formal stability counts:

```text
STABLE = 4

BOUNDARY_UNCERTAINTY = 3

UNSTABLE = 1

opposite direction reversal = 0
```

Per subject:

```text
FIC-FIN-01 = BOUNDARY_UNCERTAINTY

FIC-FIN-02 = UNSTABLE

FIC-FIN-03 = STABLE

FIC-FIN-04 = BOUNDARY_UNCERTAINTY

FIC-FIN-05 = BOUNDARY_UNCERTAINTY

FIC-FIN-06 = STABLE

FIC-FIN-07 = STABLE

FIC-FIN-08 = STABLE
```

M12S must audit all 8 subjects,
with detailed root-cause focus on the four non-STABLE subjects.

---

# 4. Frozen repeated-run values

## FIC-FIN-01 — strong quality

```text
run-1:
BUY 6.5 : 3.5
new buyer ATTRACTIVE
holder HOLDABLE

run-2:
BUY 6.0 : 4.0
new buyer WAIT
holder HOLDABLE

run-3:
BUY 6.5 : 3.5
new buyer ATTRACTIVE
holder HOLDABLE

business thesis change:
STRENGTHENED / STRENGTHENED / STRENGTHENED
```

The direction never changed.

The variance is:

```text
6.0 vs 6.5
and
ATTRACTIVE vs WAIT
```

## FIC-FIN-02 — profit/cash divergence

```text
run-1:
SELL 4.0 : 6.0
new buyer AVOID
holder REVIEW

run-2:
HOLD 4.5 : 5.5
SELL_LEAN
new buyer WAIT
holder REVIEW

run-3:
SELL 4.0 : 6.0
new buyer WAIT
holder REVIEW

business thesis change:
WEAKENED / WEAKENED / WEAKENED
```

Material typed anchors in all runs:

```text
operating cash flow
OCF less identified PPE cash-conversion proxy
```

The direction threshold changed only:

```text
SELL 6.0
↔
HOLD SELL_LEAN 5.5
```

No opposite-direction reversal occurred.

## FIC-FIN-04 — non-operating boost

```text
run-1:
HOLD 5.0 : 5.0
NEUTRAL

run-2:
HOLD 5.0 : 5.0
NEUTRAL

run-3:
HOLD 5.5 : 4.5
BUY_LEAN

business thesis change:
UNCHANGED / UNCHANGED / UNCHANGED

new buyer:
WAIT / WAIT / WAIT

holder:
HOLDABLE / HOLDABLE / HOLDABLE
```

Variance:

```text
5.0 vs 5.5
```

Direction remains HOLD.

## FIC-FIN-05 — leverage/liquidity pressure

```text
run-1:
SELL 4.0 : 6.0
new buyer AVOID
holder REDUCE

run-2:
SELL 4.0 : 6.0
new buyer AVOID
holder REVIEW

run-3:
SELL 4.0 : 6.0
new buyer AVOID
holder REDUCE

business thesis change:
WEAKENED / WEAKENED / WEAKENED
```

Direction and balance are identical.

Only holder stance varies:

```text
REDUCE ↔ REVIEW
```

---

# 5. Critical M12S principle

Do NOT equate:

```text
different output field
```

with:

```text
different economic interpretation
```

The review must explicitly separate:

```text
evidence selection

evidence interpretation

investment-thesis state

directional polarity

directional strength bucket

new-buyer stance

holder stance

wording / presentation
```

A field variance may be material or merely adjacent calibration ambiguity.

M12S must prove which.

---

# 6. Build an Evidence Interpretation Fingerprint

For every ticker × repetition,
build a normalized fingerprint from the preserved output.

At minimum include:

```text
ticker

overall_direction

buy balance
sell balance
hold_lean

business_thesis_change

fundamental_new_buyer stance

fundamental_holder stance

directional_confidence

material_directional_anchor_basis

dominant_evidence refs

dominant_evidence semantic category

buy_driver classifications

sell_driver classifications

unknown_treatment types

business_reevaluation_up domains

business_reevaluation_down domains

business_invalidation domain

valuation limitation

sector interpretation

financial-context domains actually used
```

Also normalize core reasoning into semantic flags such as:

```text
operating trend positive/neutral/negative

cash conversion positive/neutral/negative

debt/liquidity positive/neutral/negative

working capital positive/context/negative

non-operating effect positive/context/negative

period conflict present

missing-data confidence limit
```

Do not use an LLM to generate the fingerprint.

Use deterministic rules over preserved structured outputs.

---

# 7. Material Evidence Interpretation Delta

For every repeated pair within a ticker,
determine whether there is a material interpretation delta.

Allowed values:

```text
NO_MATERIAL_INTERPRETATION_DELTA

MINOR_EMPHASIS_DELTA

MATERIAL_INTERPRETATION_DELTA

NOT_MEASURED
```

Examples of `MATERIAL_INTERPRETATION_DELTA`:

```text
same cash-flow evidence treated as deterioration in one run
but neutral/context in another

same debt evidence treated as invalidation risk in one run
but irrelevant in another

same non-operating effect treated as operating improvement in one run
but correctly separated in another

material anchor domain changes from cash conversion to revenue
with different causal meaning
```

Examples of `MINOR_EMPHASIS_DELTA`:

```text
same material anchors
same polarity
same thesis state
different wording
one run includes an extra supporting ref
```

Do not call a 0.5 balance difference itself an interpretation delta.

---

# 8. Root-cause taxonomy

Each non-STABLE ticker must receive one primary classification:

```text
TRUE_SEMANTIC_VARIANCE

ADJACENT_BALANCE_BUCKET_CALIBRATION_AMBIGUITY

NEW_BUYER_STANCE_CALIBRATION_AMBIGUITY

HOLDER_STANCE_CALIBRATION_AMBIGUITY

ANCHOR_SELECTION_PRESENTATION_VARIANCE

FORMAL_CLASSIFIER_SENSITIVITY

MIXED

OTHER
```

Optional secondary classifications may be recorded.

But choose one primary root cause.

---

# 9. FIC-FIN-02 required forensic review

This is the only `UNSTABLE` ticker.

Compare run-1/run-2/run-3 in detail.

Known preserved facts:

```text
business thesis = WEAKENED in all 3

holder = REVIEW in all 3

same primary typed anchors:
OCF + simple cash-conversion proxy

same fundamental conflict:
accounting growth / healthy demand
vs
weaker cash conversion

same Unknown:
cause / reversibility / valuation limitations
```

Direction:

```text
SELL 6.0
HOLD SELL_LEAN 5.5
SELL 6.0
```

Required question:

```text
Did run-2 actually interpret the economics less negatively,
or did it apply the same economics to the adjacent 5.5 bucket?
```

If no material interpretation delta exists:

```text
do NOT classify as true semantic instability
```

but also do NOT change the formal stability classifier in M12S.

The current classifier can remain correct for detecting output instability
while root cause is separately classified as calibration ambiguity.

---

# 10. FIC-FIN-01 required review

Known:

```text
BUY in all 3

STRENGTHENED in all 3

holder HOLDABLE in all 3

same core economic pattern:
operating improvement
+
cash-conversion improvement
+
financial resilience
```

Variance:

```text
BUY 6.0 vs 6.5

new buyer WAIT vs ATTRACTIVE
```

Required questions:

```text
Is 6.0 vs 6.5 a material interpretation difference?

Is new-buyer WAIT vs ATTRACTIVE mechanically or semantically tied
to the 6.0/6.5 strength bucket?

Does valuation Unknown explain WAIT in one run?

Does the same valuation Unknown exist in all runs?
```

Classify:

```text
balance calibration

new-buyer stance calibration

or true semantic difference
```

separately.

---

# 11. FIC-FIN-04 required review

Known:

```text
HOLD all 3

business thesis UNCHANGED all 3

new buyer WAIT all 3

holder HOLDABLE all 3
```

Variance:

```text
5.0 NEUTRAL
5.0 NEUTRAL
5.5 BUY_LEAN
```

Core pattern:

```text
operating performance roughly flat

net income improvement

larger financial/non-operating effect

repeatability/operating acceleration unresolved
```

Required question:

```text
Does run-3 truly interpret the financial effect more positively,
or merely place the same mixed evidence in the adjacent 5.5 bucket?
```

---

# 12. FIC-FIN-05 required review

Known:

```text
SELL 4.0:6.0 all 3

WEAKENED all 3

new buyer AVOID all 3

same debt/cash anchors all 3
```

Only:

```text
holder REDUCE
REVIEW
REDUCE
```

varies.

Required questions:

```text
What exact current holder-stance contract distinguishes REVIEW vs REDUCE?

Did the run-2 reasoning actually change business severity?

Was the same business invalidation condition present?

Is REDUCE permitted from fundamental evidence alone under current contract?

Is REVIEW vs REDUCE currently under-specified?
```

Do not involve Price-Timing.

M12S must classify whether this is:

```text
holder stance calibration ambiguity
```

or true semantic variance.

---

# 13. Review stable controls

Use the four STABLE cases as controls.

## FIC-FIN-03

```text
HOLD 5.0:5.0
NEUTRAL
WAIT
REVIEW
```

all 3.

## FIC-FIN-06

```text
HOLD 5.5:4.5
BUY_LEAN
WAIT
HOLDABLE
```

all 3.

## FIC-FIN-07

```text
HOLD 5.0:5.0
NEUTRAL
WAIT
HOLDABLE
```

all 3.

## FIC-FIN-08

```text
HOLD 5.0:5.0
NEUTRAL
WAIT
REVIEW
```

all 3.

Compare their fingerprints to identify what stable decision contracts look like.

---

# 14. Calibration contract audit

Inspect the current Directional prompt / calibration contract for:

```text
5.0

5.5

6.0

6.5+
```

Both positive and negative directions.

Document the actual wording.

Do not change it.

Evaluate whether the existing definitions clearly distinguish:

```text
5.5 lean

6.0 minimum directional conclusion

6.5 stronger directional conclusion
```

for the newly added financial-context patterns.

Specifically audit:

```text
cash-conversion deterioration with healthy demand

strong quality with valuation Unknown

non-operating net-income boost with flat operations

high debt / low cash
```

If the contract is under-specified for these cases,
record the exact ambiguity.

---

# 15. New-buyer stance contract audit

Inspect how:

```text
ATTRACTIVE
WAIT
AVOID
```

are currently specified.

Determine whether they depend on:

```text
absolute Directional direction

balance strength

valuation availability

confirmation requirement

market expectations

business evidence quality
```

Freeze the actual current contract.

For FIC-FIN-01 and FIC-FIN-02,
identify exactly why repeated outputs diverged.

Do not change the contract in M12S.

---

# 16. Holder stance contract audit

Inspect:

```text
HOLDABLE
REVIEW
REDUCE
```

and current allowed evidence basis.

Required:

```text
business evidence only?
invalidation evidence?
valuation?
price?
```

Price-only holder REDUCE remains forbidden under the existing ownership contract.

For FIC-FIN-05,
determine why:

```text
same SELL 6.0
same WEAKENED thesis
same debt/liquidity anchors
```

can produce:

```text
REVIEW or REDUCE
```

If the contract has no crisp generic distinction,
classify `HOLDER_STANCE_CALIBRATION_AMBIGUITY`.

---

# 17. Formal classifier audit — no change by default

The formal stability classifier currently marks:

```text
direction change
or opposing HOLD lean change
```

as `UNSTABLE`.

It marks other field variance as `BOUNDARY_UNCERTAINTY`
under the frozen rules.

M12S must not weaken the classifier merely because FIC-FIN-02
looks economically similar.

Audit whether:

```text
the classifier is correctly detecting output instability
while the root cause is calibration ambiguity
```

If so:

```text
classifier = KEEP
```

Do not re-label the historical M12D formal result.

Only recommend a classifier change if a generic contract error is proven.

Expected default:

```text
formal_classifier_change_required = false
```

---

# 18. No retrospective success rewrite

M12D remains:

```text
full fictional canary status = FAIL
```

because:

```text
UNSTABLE = 1
```

Do not retroactively convert it to PASS
even if M12S finds the root cause is adjacent-bucket calibration ambiguity.

M12S is a root-cause review.

A later repaired canary must use a new generation.

---

# 19. Candidate repair decisions

At the end choose one:

```text
A. BOUNDED_FINANCIAL_CONTEXT_BOUNDARY_CALIBRATION_REPAIR

B. BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR

C. BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR

D. COMBINED_DIRECTIONAL_STANCE_CALIBRATION_REPAIR
   only if one generic root cause governs multiple fields

E. TRUE_FINANCIAL_INTERPRETATION_VARIANCE_REPAIR

F. FORMAL_STABILITY_CLASSIFIER_REPAIR

G. NO_SEMANTIC_REPAIR_REQUIRED_BUT_NEW_CANARY_REQUIRED

H. OTHER_BOUNDED_REPAIR
```

The decision must name the exact fields/contract.

Do not choose a combined repair for convenience.

---

# 20. Preferred repair minimality

If M12S finds:

```text
same evidence interpretation
same thesis state
same material anchors
only adjacent 0.5 bucket variance
```

prefer:

```text
a bounded calibration-clarity repair
```

over:

```text
new scorecard
new fixed arithmetic
new threshold
majority vote
balance averaging
```

Threshold remains:

```text
6.0
```

Increment remains:

```text
0.5
```

The repair should clarify when evidence belongs at:

```text
5.5
vs
6.0
vs
6.5
```

not change the threshold itself.

---

# 21. Conservative tie-break audit

Existing frozen tie-break:

```text
if supplied evidence reasonably fits adjacent buckets,
choose the less-directional bucket toward 5.0
```

Audit whether M12D outputs applied this consistently.

For FIC-FIN-02:

```text
if both 5.5 and 6.0 are reasonably supportable,
the frozen tie-break implies 5.5.
```

But do NOT assume both are reasonable.

First determine whether the evidence contract clearly supports 6.0
or genuinely spans both buckets.

Likewise for FIC-FIN-01:

```text
6.0 vs 6.5
```

and FIC-FIN-04:

```text
5.0 vs 5.5
```

---

# 22. Financial-context-specificity question

Determine whether richer financial context created a new ambiguity
because the model now has:

```text
more corroborating evidence
but also more explicit Unknown / limitation evidence.
```

Example:

```text
strong OCF deterioration
+
healthy demand
+
inventory increase as context
+
unknown cause/reversibility
```

may plausibly be:

```text
SELL 6.0
or
HOLD SELL_LEAN 5.5
```

under a vague calibration contract.

If so, the issue is not financial fact parsing.

It is:

```text
how corroboration vs limiting Unknowns map to the ordinal bucket.
```

Freeze this distinction.

---

# 23. No new financial-data work

M12S must not request or implement more parsers.

Do not add:

```text
new accounting domains
new source providers
new financial-context fields
```

The current six-domain financial evidence layer is sufficient for this review.

---

# 24. No model calls

Required:

```text
model_calls_real = 0
model_calls_fictional = 0
model_calls_judge = 0
```

Use preserved M12D 24 outputs only.

No new generation in M12S.

---

# 25. No prompt/calibration implementation

M12S may produce proposed text/contracts.

It must NOT activate them.

Required:

```text
directional_prompt_change_count = 0

calibration_contract_change_count = 0

new_buyer_contract_change_count = 0

holder_contract_change_count = 0

formal_classifier_change_count = 0
```

Implementation happens in the next separately authorized task.

---

# 26. Offline normalized comparison tooling

M12S may implement model-free tooling to:

```text
extract fingerprints

normalize evidence domains

compare repeated outputs

classify field variance

generate stability tables
```

Keep tooling offline/review-only.

Do not wire it into production runtime.

---

# 27. Required tests

If tooling changes:

```text
focused pytest

full repository pytest

ruff

git diff --check
```

must PASS.

No model tests.

No provider calls.

---

# 28. Production side-effect firewall

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

Observe approved 8 paused schedules at start/end.

---

# 29. Required artifacts — provenance / result integrity

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12s-scope-freeze

04-m12d-full-canary-reuse-proof

05-m12d-stability-result-freeze
```

---

# 30. Required artifacts — fingerprints

Produce:

```text
06-evidence-interpretation-fingerprint-contract

07-all-24-output-fingerprints

08-stable-control-fingerprint-summary

09-nonstable-fingerprint-summary

10-material-interpretation-delta-matrix
```

---

# 31. Required artifacts — ticker forensic reviews

Produce:

```text
11-fic-fin-01-stability-forensic

12-fic-fin-02-stability-forensic

13-fic-fin-04-stability-forensic

14-fic-fin-05-stability-forensic
```

Each must include:

```text
repeated values

material anchors

semantic polarity

Unknowns

reevaluation conditions

stance changes

primary root cause
```

---

# 32. Required artifacts — contract audits

Produce:

```text
15-directional-bucket-calibration-contract-audit

16-conservative-tiebreak-consistency-audit

17-new-buyer-stance-contract-audit

18-holder-stance-contract-audit

19-formal-stability-classifier-audit

20-financial-context-ordinal-interaction-audit
```

---

# 33. Required root-cause decision artifacts

Produce:

```text
21-stability-root-cause-classification

22-true-semantic-variance-decision

23-adjacent-bucket-calibration-decision

24-new-buyer-stance-calibration-decision

25-holder-stance-calibration-decision

26-formal-classifier-change-decision
```

---

# 34. Required next-repair contract

Produce:

```text
27-preferred-next-repair-decision

28-frozen-next-repair-contract

29-next-fictional-canary-scope

30-fresh-real-proof-readiness-decision
```

`fresh_real_proof_readiness` remains:

```text
NOT_READY
```

in M12S.

No repaired model canary is run here.

---

# 35. Required completion artifacts

Produce:

```text
31-production-no-change

32-schedule-pause-observation

33-master-workflow-update

34-program-completion
```

---

# 36. M12S acceptance criteria

M12S is COMPLETE only if:

```text
all 24 preserved outputs are fingerprinted

all 8 tickers receive stability classification support

all 4 non-STABLE tickers receive a primary root cause

FIC-FIN-02 true semantic variance vs adjacent-bucket ambiguity is explicitly decided

FIC-FIN-01 6.0/6.5 and ATTRACTIVE/WAIT variance is explicitly explained

FIC-FIN-04 5.0/5.5 variance is explicitly explained

FIC-FIN-05 REDUCE/REVIEW variance is explicitly explained

current 5.0/5.5/6.0/6.5 contract is audited

conservative tie-break consistency is audited

new-buyer stance contract is audited

holder stance contract is audited

formal classifier change need is explicitly decided

one bounded next repair is frozen

no model/provider/production calls occur

focused/full tests PASS if tooling changed

ruff PASS
git diff --check PASS
```

M12S does NOT require:

```text
a repaired prompt

a repaired calibration contract activated

a repaired fictional canary

fresh real proof

production readiness
```

---

# 37. Next-scope decision

## A. Adjacent bucket calibration ambiguity is primary

Recommended:

```text
BOUNDED_FINANCIAL_CONTEXT_BOUNDARY_CALIBRATION_REPAIR_AND_FULL_FICTIONAL_CANARY
```

The next task should:

```text
clarify 5.0 / 5.5 / 6.0 / 6.5 evidence sufficiency
without changing threshold/increment

freeze new-buyer/holder stance only if directly coupled

then rerun the full 8 × 3 fictional canary
under a new generation
```

## B. Holder stance ambiguity is independent and material

If FIC-FIN-05 is the only unresolved material defect after bucket repair decision:

```text
BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR
```

Decide whether to repair together or sequentially based on root-cause coupling.

## C. True financial interpretation variance is primary

Recommended:

```text
BOUNDED_FINANCIAL_EVIDENCE_INTERPRETATION_CONTRACT_REPAIR
```

Do not change thresholds.

## D. Formal classifier is incorrect

Only if generic classifier defect is proven:

```text
FORMAL_STABILITY_CLASSIFIER_REPAIR
```

Historical M12D result remains frozen.

## E. Multiple independent issues

Order:

```text
core direction/balance stability first

stance calibration second

message advisory later
```

Do not combine unrelated changes.

---

# 38. Production readiness

M12S remains:

```text
fresh_real_proof_readiness = NOT_READY

production_readiness = NOT_READY
```

Even a clear calibration root cause still requires:

```text
implementation
+
new full fictional canary
+
fresh unseen real generalization proof
```

Monitoring remains paused.

---

# 39. Program-completion fields

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

m12d_status

m12s_status

fingerprinted_output_count

stable_subject_count

boundary_uncertainty_subject_count

unstable_subject_count

true_semantic_variance_subject_count

adjacent_bucket_calibration_subject_count

new_buyer_stance_calibration_subject_count

holder_stance_calibration_subject_count

anchor_presentation_variance_subject_count

classifier_sensitivity_subject_count

fic_fin_01_root_cause

fic_fin_02_root_cause

fic_fin_04_root_cause

fic_fin_05_root_cause

fic_fin_02_material_interpretation_delta

directional_bucket_contract_status

conservative_tiebreak_consistency_status

new_buyer_stance_contract_status

holder_stance_contract_status

formal_classifier_change_required

preferred_next_repair

next_repair_fields

new_model_validation_required

new_full_fictional_canary_required

fresh_real_proof_readiness

model_calls_real

model_calls_fictional

model_calls_judge

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

production_readiness

status

stop_reason

next_scope
```

Anything not measured must remain:

```text
NOT_MEASURED
```

---

# 40. Artifact integrity

Freeze:

```text
program completion

master workflow

all forensic / calibration audit reports
```

before the final artifact index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 41. Final task principle

M12D solved the financial-data interpretation safety problem.

The 24-output sample shows:

```text
the model uses typed financial evidence

period semantics are correct

grounding is correct

financial hard safety is clean
```

The remaining issue is now:

```text
how the same economic evidence is placed
into adjacent Directional strength / stance buckets across repetitions.
```

The correct next move is:

```text
compare preserved outputs offline

→ separate real interpretation variance
  from calibration/stance variance

→ audit 5.0 / 5.5 / 6.0 / 6.5 meanings

→ audit new-buyer / holder stance meanings

→ freeze the smallest repair

→ only then run another full fictional canary
```

Not:

```text
add more financial parsers
```

Not:

```text
change the 6.0 threshold
```

Not:

```text
average the three runs
```

Not:

```text
majority-vote Directional output
```

Not:

```text
weaken the formal stability classifier just to pass FIC-FIN-02
```

Not:

```text
run a fresh real cohort before fictional stability is repaired
```

And not:

```text
resume production monitoring
```

The remaining problem is calibration stability, not financial evidence ingestion.
