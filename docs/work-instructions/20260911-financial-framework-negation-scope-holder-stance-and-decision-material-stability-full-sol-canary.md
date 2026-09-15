# Thesis Monitor — Financial-Framework Negation Scope + Holder Stance + Decision-Material Stability + Full Sol Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-financial-framework-negation-scope-holder-stance-and-decision-material-stability-full-sol-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-financial-framework-negation-scope-holder-stance-decision-material-stability-full-sol-canary-report.zip
```

Master-workflow phase:

```text
M12AD — GPT-5.6 Sol / xhigh
         A. Financial-Framework Contrastive Negation Scope Repair
         B. Holder REVIEW/REDUCE Contract Review + Bounded Repair
         C. Decision-Material Stability Policy
         D. Full 8 × 3 Fictional Financial Canary
```

M12AC completed the full intended fictional workload:

```text
6 / 6 model contexts complete
24 / 24 outputs schema PASS
timeout = 0
capacity failure = 0
orphan = 0
wrapper retry = 0
```

The remaining issues are now narrow:

```text
1. FIC-FIN-08:
one Korean contrastive-negation surface
"산업회사식 순부채·운전자본 틀이 아니라
 인수 규율과 규제자본으로 판단한다"
was falsely rejected as industrial-framework application.

2. FIC-FIN-05:
core direction/balance is now stable at SELL 4.0:6.0 ×3,
new-buyer is stable at AVOID ×3,
but holder stance remains REVIEW / REDUCE / REDUCE.

3. FIC-FIN-03:
raw balance is HOLD 5.0 / HOLD 5.5 / HOLD 5.5,
while overall direction remains HOLD ×3,
new-buyer WAIT ×3,
holder REVIEW ×3,
confidence LOW ×3.
The current M12AC reporting helper labels any exact raw-state variation
as UNSTABLE, which is too coarse for readiness decisions.
```

M12AD must NOT return to exact-point target chasing.

The goal is to distinguish:

```text
objective semantic failure

primary decision instability

holder/new-buyer action instability

same-direction calibration variance

confidence/advisory variance
```

and then rerun one full clean Sol/xhigh canary.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260910-financial-framework-scope-regression-threshold-zone-architecture-full-sol-canary-report.zip
```

Verified SHA-256:

```text
2b5dd84efcaf207e31e5fec15521c0879022fdb9fb411fb0b7cd2cedd80801fe
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
indexed payloads = 163
ZIP payloads excluding artifact-index = 163
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

Recompute before trusting the bundle.

---

# 2. M12AC provenance

Reported:

```text
branch =
codex/20260910-financial-framework-threshold-zone-m12ac

base_sha =
f22c3cef615c665150fe5e92b45e185345782d1c

implementation_commit =
6d4f8cfd4d8677e351cf9c0cbec3c250c9680e64

report_commit =
f8cade9fc51f9df902778700c8396d7436af1ba9
```

The exported completion file used:

```text
final_head_sha =
RESOLVED_FROM_GIT_AT_BUNDLE_EXPORT
```

At M12AD start use actual repository HEAD.

Record:

```text
actual_branch
actual_head
working_tree_state
remote_branch_sha
```

If unexplained drift exists in:

```text
financial-framework role classifier
business-delta alias resolution
holder stance prompt/contract
Directional ordinal contract
threshold-zone shadow service
Sol runtime
fictional source packets
```

then:

```text
STOP
UNEXPLAINED_M12AD_BASELINE_DRIFT
```

---

# 3. Proof-critical model/runtime — frozen

Use:

```text
model = gpt-5.6-sol
reasoning = xhigh
```

Runtime:

```text
MODEL_CONTEXT_COUPLED
4 subjects/context
1800-second finite watchdog
single authoritative watchdog
wrapper auto-retry = 0
batch split = 0
```

No Astra.

No fallback.

No timeout change.

No context-topology change.

If runner target differs:

```text
STOP
SOL_RUNNER_MODEL_TARGET_MISMATCH
```

---

# 4. M12AC runtime is healthy

Measured:

```text
model calls fictional = 6
model context success = 6
model context failure = 0

fictional outputs = 24
schema PASS = 24 / 24

timeout = 0
capacity failure = 0
orphan = 0
CLI internal retry = 0
wrapper retry = 0
```

Reported runtime:

```text
median ≈ 455.06 sec
max ≈ 540.92 sec

Sol runtime real-holdout suitability =
READY
```

M12AD is not a runtime-review task.

---

# 5. M12AC boundary architecture V2 — freeze the useful part, stop treating it as a production resolver

M12AC selected:

```text
DETERMINISTIC_THRESHOLD_ZONE
```

and retired Option F from the model-facing experiment:

```text
option_f_model_facing_disabled = true
option_f_final_status = RETIRED_FROM_MODEL_FACING_EXPERIMENT
```

This was the correct direction.

Threshold-zone contract:

```text
model self-declaration = false
raw state mutation = false
renderer enabled = false
source = validated raw direction/balance/lean
```

Keep threshold-zone as:

```text
SHADOW_DESCRIPTIVE_METADATA
```

not:

```text
a resolver that rewrites HOLD/BUY/SELL
```

M12AD must not introduce a deterministic HOLD→SELL or SELL→HOLD conversion.

---

# 6. M12AC FIC-FIN-05 result — the previous core boundary problem did not reproduce

M12AC full sample:

```text
FIC-FIN-05 run 1:
SELL 4.0:6.0

FIC-FIN-05 run 2:
SELL 4.0:6.0

FIC-FIN-05 run 3:
SELL 4.0:6.0
```

Threshold zone:

```text
NEGATIVE_THRESHOLD_ZONE ×3
```

Thus:

```text
raw core balance unique count = 1
raw overall direction = SELL ×3
zone unique count = 1
```

This means the prior M12AA:

```text
SELL / HOLD / SELL
```

boundary jitter did not reproduce under the restored non-self-introspection output contract.

Do not keep designing production HOLD/SELL resolvers around the old one-off repeated sample
unless the boundary returns.

---

# 7. M12AC FIC-FIN-05 economic semantics remained coherent

Across all three outputs:

```text
complete high debt + thin cash =
negative financial-resilience anchor

stable positive operating profit =
counterevidence

refinancing terms / maturity concentration =
unresolved severity limit

market-expectation downside =
conditional on the same unresolved refinancing risk

business_thesis_change =
UNCHANGED
```

New-buyer:

```text
AVOID ×3
```

Directional confidence:

```text
MEDIUM ×3
```

Only holder stance varied:

```text
REDUCE / REVIEW / REDUCE
```

Therefore the next FIC-FIN-05 issue is:

```text
HOLDER STANCE
```

not core Directional balance.

---

# 8. M12AC FIC-FIN-03 result — same primary direction, adjacent HOLD lean variance

Observed:

```text
run 1:
HOLD 5.0:5.0 NEUTRAL

run 2:
HOLD 5.5:4.5 BUY_LEAN

run 3:
HOLD 5.5:4.5 BUY_LEAN
```

Stable decision fields:

```text
overall direction = HOLD ×3

new buyer = WAIT ×3

holder = REVIEW ×3

directional confidence = LOW ×3
```

This is not equivalent to:

```text
HOLD ↔ BUY
```

or:

```text
HOLD ↔ SELL
```

It is:

```text
same-direction calibration/lean variance inside HOLD.
```

M12AD must report it honestly,
but must not automatically call it a production-decision failure.

---

# 9. M12AC raw-core reporting helper is too coarse

M12AC helper:

```text
_raw_core_stability
```

classifies:

```text
exact same tuple across 3 → STABLE
any tuple difference → UNSTABLE
```

where tuple includes:

```text
overall_direction
buy balance
sell balance
hold_lean
```

Therefore FIC-FIN-03:

```text
HOLD 5.0
HOLD 5.5
HOLD 5.5
```

is labeled:

```text
UNSTABLE
```

without distinguishing that primary direction and user stances are unchanged.

This helper is useful for:

```text
EXACT_RAW_STATE_VARIANCE
```

but must not be named or treated as the authoritative decision-material stability classifier.

---

# 10. Preserve historical formal classifier semantics

Do not rewrite historical results.

The project has previously distinguished:

```text
STABLE

BOUNDARY_UNCERTAINTY

UNSTABLE
```

and historically treated adjacent same-direction bucket variation
differently from primary-direction reversal.

M12AD must audit the existing frozen formal classifier implementation
and use its actual semantics where available.

Do not replace it with:

```text
unique_count > 1 = UNSTABLE
```

without qualification.

---

# 11. New decision-material stability layer

Add a separate model-free readiness classification.

Suggested classes:

```text
DECISION_STABLE

CALIBRATION_VARIANCE_SAME_DIRECTION

PRIMARY_DIRECTION_UNSTABLE

BUSINESS_DELTA_UNSTABLE

NEW_BUYER_STANCE_UNSTABLE

HOLDER_STANCE_UNSTABLE

MULTI_FIELD_MATERIAL_UNSTABLE
```

This classifier is for:

```text
readiness / downstream decision-material interpretation
```

not for rewriting the raw output.

---

# 12. Decision-material field hierarchy

Treat as decision-material:

```text
overall_direction

business_thesis_change

fundamental_new_buyer.stance

fundamental_holder.stance
```

Treat as calibration/intensity fields when the above remain stable:

```text
directional_balance

HOLD lean

directional_confidence
```

This does not make calibration irrelevant.

It changes whether a same-direction 0.5 difference blocks
the next generalization proof.

---

# 13. Same-direction 0.5 variance policy

If:

```text
overall direction is identical in all repetitions

business delta is identical and valid

new-buyer stance is identical

holder stance is identical

hard semantics pass
```

then a variation such as:

```text
HOLD 5.0 ↔ HOLD 5.5 BUY_LEAN

BUY 6.0 ↔ BUY 6.5

SELL 6.0 ↔ SELL 6.5
```

must be classified as:

```text
CALIBRATION_VARIANCE_SAME_DIRECTION
```

not:

```text
PRIMARY_DIRECTION_UNSTABLE
```

Report exact raw variation separately.

Do not majority-vote.

Do not average.

Do not mutate the raw balance.

---

# 14. Primary-direction crossing remains material

If repetitions cross:

```text
HOLD ↔ BUY

HOLD ↔ SELL

BUY ↔ SELL
```

classify:

```text
PRIMARY_DIRECTION_UNSTABLE
```

unless a separately predeclared production architecture resolves it.

No such production resolver is authorized in M12AD.

This remains a fresh-real readiness blocker.

---

# 15. HOLD lean is still visible

Do not hide:

```text
NEUTRAL ↔ BUY_LEAN
```

or:

```text
NEUTRAL ↔ SELL_LEAN
```

variance.

Report:

```text
exact_raw_state_variance = true

calibration variance = true

primary direction stable = true
```

The user should be able to see the difference.

The methodological change is only:

```text
same-HOLD lean variance does not automatically equal
material decision instability.
```

---

# 16. Threshold-zone status in M12AD

Keep threshold-zone as shadow/descriptive metadata.

M12AC observed:

```text
7 zone-stable subjects
1 zone-unstable subject
```

FIC-FIN-03:

```text
NEUTRAL
POSITIVE_THRESHOLD_ZONE
POSITIVE_THRESHOLD_ZONE
```

This is useful description,
but it should not determine production direction.

M12AD must separate:

```text
threshold_zone_mapper_correctness

from

observed threshold_zone stability.
```

The mapper can be technically PASS
even when a subject crosses zone labels.

Do not report:

```text
threshold-zone architecture FAIL
```

merely because observed raw calibration crosses a zone.

---

# 17. Issue A — exact FIC-FIN-08 false reject

M12AC repetitions 1 and 2 were classified correctly.

Examples:

```text
"보험사에는 인수 규율과 규제자본 관점이 적용되며
산업회사식 순부채·운전자본 틀은 배제한다."

"보험사이므로 인수 규율과 규제자본을 적용하며
산업회사식 순부채·운전자본 틀은 배제한다."
```

Both:

```text
EXPLICIT_NON_APPLICATION
```

and no hard failure.

M12AC repetition 3:

```text
"보험사이므로 산업회사식 순부채·운전자본 틀이 아니라
인수 규율과 규제자본으로 판단한다."
```

was classified:

```text
UNRESOLVED
```

for both:

```text
net debt
working capital
```

which produced two false rejects.

Actual industrial-framework application:

```text
0
```

---

# 18. Issue A root cause — freeze exact grammar class

M12AC completion recorded:

```text
KOREAN_BOUNDARY_NOUN_BEFORE_CONTRAST_MARKER_NOT_RECOGNIZED
```

The missing structure is not another random sentence.

It is a bounded contrastive-copular construction:

```text
[X framework noun phrase] + 이/가 아니라 + [Y replacement] + predicate
```

Example:

```text
X =
산업회사식 순부채·운전자본 틀

contrast =
이 아니라

Y =
인수 규율과 규제자본

predicate =
판단한다
```

The predicate applies to Y,
while X is explicitly rejected as the applicable framework.

---

# 19. Structural Korean contrastive-negation contract

Support bounded forms including:

```text
X이 아니라 Y로 판단한다

X가 아니라 Y를 본다

X이 아닌 Y를 적용한다

X가 아닌 Y가 적절하다

X보다는 Y를 본다
```

only when syntactic/local clause structure shows:

```text
X = excluded/rejected framework
Y = replacement/applied framework
```

Do not use a flat phrase whitelist.

Do not treat every `아니라` as exclusion.

---

# 20. Coordinated framework terms

The left excluded span may contain:

```text
순부채·운전자본

순부채와 운전자본

순부채나 운전자본

net debt and working capital
```

All forbidden concepts inside the left rejected span
must inherit:

```text
CONTRASTIVE_REPLACEMENT
or
EXPLICIT_NON_APPLICATION
```

not:

```text
ASSERTED_STATE
```

The application predicate on the right must not leak backward.

---

# 21. Shared application-role consumer requirement

Use one role classification result consistently for:

```text
net-debt claim/completeness validator

financial-sector generic-framework validator

working-capital sector-framework validator
```

Do not allow a downstream token scan to override
a valid local contrastive-negation scope.

Required:

```text
shared_application_scope_consistency = PASS
```

---

# 22. Contradiction and actual use remain hard failures

Must still FAIL:

```text
"순부채 틀이 아니라 규제자본으로 판단한다.
하지만 순부채가 높아 SELL이다."

"운전자본은 적용하지 않는다."
but sell_drivers use industrial WC deterioration.

sector_interpretation excludes industrial net debt
but material_directional_anchor_basis cites/uses unsupported net debt.
```

Exclusion is not immunity.

---

# 23. Exact M12AC FIC-FIN-08 rep-3 replay

After repair, the exact old row must classify:

```text
net debt role =
CONTRASTIVE_REPLACEMENT

working capital role =
CONTRASTIVE_REPLACEMENT

net_debt_claim_without_complete_net_debt_evidence =
0

financial_sector_generic_reasoning =
0

financial_sector_true_misuse =
0
```

No historical output rewrite.

---

# 24. Issue B — holder REVIEW vs REDUCE contract

M12AC FIC-FIN-05:

```text
core = SELL 4.0:6.0 ×3

business delta = UNCHANGED ×3

new buyer = AVOID ×3

holder =
REDUCE
REVIEW
REDUCE
```

The underlying economics remained the same.

Therefore:

```text
holder stance contract is under review.
```

Do NOT mechanically map:

```text
SELL → REDUCE
```

and do NOT assume:

```text
UNCHANGED → REVIEW
```

---

# 25. Holder stance semantics to audit

Audit the actual current contract for:

```text
HOLDABLE

REVIEW

REDUCE
```

Determine what distinguishes:

```text
material risk worth monitoring
```

from:

```text
fundamental evidence strong enough to reduce existing exposure
```

Relevant generic dimensions:

```text
confirmed business/financial impairment

severity

persistence

reversibility

business invalidation

structural deterioration

critical Unknowns

counterevidence

valuation limitations

current absolute condition vs new deterioration
```

No price/technical/supply input.

---

# 26. Holder stance candidate contract

Evaluate the following generic principle:

```text
HOLDABLE:
no material fundamental reason to reconsider the holding.

REVIEW:
material confirmed fundamental risk exists,
but a critical severity/persistence/reversibility question remains unresolved
such that active exposure reduction is not yet uniquely justified.

REDUCE:
confirmed fundamental downside is sufficiently established
that maintaining the same exposure is no longer justified
even before price/timing overlays.
```

Important:

```text
REDUCE does not require business_thesis_change=WEAKENED.

An absolute current condition can justify REDUCE.

But SELL 6.0 alone does not mechanically force REDUCE.
```

The review must accept, reject, or refine this generic contract.

---

# 27. FIC-FIN-05 holder target must be derived offline

Before model calls freeze exactly one:

```text
FIC_FIN_05_HOLDER_TARGET = REVIEW

or

FIC_FIN_05_HOLDER_TARGET = REDUCE

or

FIC_FIN_05_HOLDER_BOUNDARY_UNRESOLVED
```

Do not choose based on:

```text
2 of 3 outputs
```

Use the generic holder contract.

If:

```text
HOLDER_BOUNDARY_UNRESOLVED
```

and no unique generic rule can be frozen without scorecard/case-specific wording:

```text
STOP
NO MODEL CALLS

next_scope =
HOLDER_STANCE_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL
```

Do not prompt-chase.

---

# 28. Holder contract positive fixtures

At minimum:

## HOLD-01

```text
stable business
no material confirmed fundamental impairment
→ HOLDABLE
```

## HOLD-02

```text
material risk confirmed
but critical severity/persistence question unresolved
→ freeze REVIEW/REDUCE according to generic contract
```

## HOLD-03

```text
confirmed structural impairment or severe financial stress
with insufficient counterevidence
→ REDUCE may be supported
```

## HOLD-04

```text
price weakness only
→ cannot create REDUCE
```

## HOLD-05

```text
technical/supply deterioration only
→ cannot create REDUCE
```

## HOLD-06

```text
absolute negative fundamental state
without new deterioration
→ holder stance determined by current severity,
not mechanically by business_thesis_change
```

---

# 29. FIC-FIN-05 specific holder evidence

Frozen facts:

```text
complete high debt

thin cash buffer

stable positive operating profit

refinancing terms not supplied

maturity concentration not supplied

safe current valuation not supplied

market expectation conditional on same unresolved refinancing downside

business delta UNCHANGED
```

Do not invent:

```text
covenant breach

actual refinancing failure

interest coverage stress

maturity wall

cash burn
```

The holder target must reflect only supplied facts.

---

# 30. New-buyer stance remains frozen

M12AC:

```text
new-buyer stance variance count = 0
```

All eight subjects were stable.

FIC-FIN-05:

```text
AVOID ×3
```

Do not modify new-buyer contract in M12AD.

Required:

```text
new_buyer_contract_change_count = 0
```

---

# 31. Directional confidence remains advisory

M12AC confidence variance:

```text
1 subject
```

FIC-FIN-06:

```text
LOW / MEDIUM / MEDIUM
```

Core direction/balance and stances were stable.

M12AD must treat this as:

```text
CONFIDENCE_VARIANCE_ADVISORY
```

unless it causes an actual decision-field inconsistency.

Do not mechanically map confidence to balance or stance.

---

# 32. Business-delta semantics remain frozen

M12AC:

```text
business_delta_contract_violation_count = 0
alias-resolution failure = 0
false reject = 0
false accept = 0
unsupported absolute-state-to-delta = 0
```

Preserve M12Z/M12Y delta semantics.

No delta prompt change.

---

# 33. Financial semantics remain frozen except Issue A scope repair

No change to:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

financial-context selected-only projection

working-capital materiality grounding

QTD/YTD Korean semantics

FCF label safety

prior-year-end vs YoY

debt completeness

normalized earnings safety

market-expectation economic independence
```

Required:

```text
financial_context_selection_change_count = 0

first_class_projection_change_count = 0

working_capital_validator_semantic_change_count = 0

qtd_ytd_validator_semantic_change_count = 0

market_expectation_contract_change_count = 0
```

---

# 34. Production Directional calibration remains frozen

No change:

```text
BUY if buy >= 6.0

SELL if sell >= 6.0

otherwise HOLD

0.5 increments

HOLD 5.5:4.5 BUY_LEAN

HOLD 5.0:5.0 NEUTRAL

HOLD 4.5:5.5 SELL_LEAN

conservative adjacent tie-break toward 5.0
```

No majority vote.

No averaging.

No fixed scorecard.

No deterministic raw-balance rewrite.

---

# 35. Retire threshold-zone as a readiness gate

Threshold-zone remains:

```text
SHADOW_DESCRIPTIVE
```

Its mapper correctness can be:

```text
PASS
```

independently of whether every subject has the same zone in every repetition.

Do not set:

```text
boundary architecture success = FAIL
```

solely because FIC-FIN-03 moved:

```text
NEUTRAL ↔ POSITIVE_THRESHOLD_ZONE
```

Instead report:

```text
threshold_zone_variance_subject_count
```

as descriptive.

No renderer activation.

---

# 36. Decision-material readiness policy

Before the new canary freeze:

```text
decision-material instability blockers:
- primary overall_direction changes
- business_thesis_change changes materially
- fundamental_new_buyer stance changes
- fundamental_holder stance changes

non-blocking but reported calibration/advisory variance:
- same-direction 0.5 balance change
- HOLD lean change while overall direction is still HOLD
- directional confidence change
- threshold-zone label change without primary direction/stance change
```

Objective hard semantic failures remain blockers regardless.

This policy is for:

```text
fresh-real proof readiness
```

not for hiding raw diagnostics.

---

# 37. Exact-state and decision-material stability must both be reported

Produce separate views:

```text
EXACT_RAW_STATE_STABILITY

LEGACY_FORMAL_STABILITY

DECISION_MATERIAL_STABILITY

THRESHOLD_ZONE_OBSERVATION
```

Do not name exact-tuple uniqueness:

```text
formal stability
```

unless it actually uses the frozen formal classifier.

---

# 38. Decision-material examples

## Example A

```text
HOLD 5.0 / HOLD 5.5 / HOLD 5.5

business delta stable
new buyer stable
holder stable
```

Classification:

```text
CALIBRATION_VARIANCE_SAME_DIRECTION
```

Fresh-real readiness:

```text
may remain eligible
```

if all other hard/material gates pass.

## Example B

```text
SELL / HOLD / SELL
```

Classification:

```text
PRIMARY_DIRECTION_UNSTABLE
```

Fresh-real readiness:

```text
BLOCKED
```

## Example C

```text
SELL ×3
new buyer AVOID ×3
holder REDUCE / REVIEW / REDUCE
```

Classification:

```text
HOLDER_STANCE_UNSTABLE
```

Fresh-real readiness:

```text
BLOCKED
```

until holder contract is resolved.

---

# 39. Deterministic tests — stability classification

At minimum:

```text
STAB-01:
HOLD 5.0 ↔ HOLD 5.5, same stances
→ CALIBRATION_VARIANCE_SAME_DIRECTION

STAB-02:
BUY 6.0 ↔ BUY 6.5, same stances
→ CALIBRATION_VARIANCE_SAME_DIRECTION

STAB-03:
SELL 6.0 ↔ SELL 6.5, same stances
→ CALIBRATION_VARIANCE_SAME_DIRECTION

STAB-04:
HOLD ↔ SELL
→ PRIMARY_DIRECTION_UNSTABLE

STAB-05:
HOLD ×3, holder changes
→ HOLDER_STANCE_UNSTABLE

STAB-06:
HOLD ×3, new buyer changes
→ NEW_BUYER_STANCE_UNSTABLE

STAB-07:
confidence only changes
→ decision-material stable / confidence advisory

STAB-08:
business delta changes without new evidence
→ BUSINESS_DELTA_UNSTABLE / semantic review
```

No score.

---

# 40. Deterministic tests — contrastive negation scope

At minimum PASS:

```text
"산업회사식 순부채·운전자본 틀이 아니라
인수 규율과 규제자본으로 판단한다."

"순부채 틀이 아닌 규제자본 기준을 적용한다."

"순부채보다는 규제자본을 본다."

"not industrial net debt but regulatory capital"

"regulatory capital rather than industrial net debt"
```

At minimum FAIL:

```text
exclusion sentence + actual net-debt SELL driver

industrial WC materially applied to insurer

unsupported net-debt magnitude assertion

ambiguous/double-negative phrase with actual material use
```

False accept = 0.

False reject = 0.

---

# 41. Phase A forensic artifacts

Before implementation produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12ad-scope-freeze

04-sol-runtime-freeze

05-m12ac-full-sample-reclassification

06-m12ac-exact-vs-decision-material-stability-audit

07-fic-fin-03-same-hold-variance-audit

08-fic-fin-05-holder-three-run-forensic

09-current-holder-contract-audit

10-holder-review-reduce-root-cause-decision

11-fic-fin-05-holder-target-decision

12-fic-fin-08-rep3-false-reject-reproduction

13-korean-contrastive-copula-root-cause

14-shared-application-role-consumer-audit
```

No model calls before these are frozen.

---

# 42. Phase B bounded implementation artifacts

Produce:

```text
15-contrastive-negation-span-contract

16-korean-copula-contrast-contract

17-financial-framework-role-classifier-before-after

18-net-debt-consumer-regression

19-working-capital-consumer-regression

20-financial-sector-consumer-regression

21-fic-fin-08-exact-replay

22-holder-contract-before-after
or holder-contract-no-change-proof

23-holder-fixture-matrix

24-decision-material-stability-contract

25-stability-classifier-before-after

26-threshold-zone-shadow-only-contract

27-exact-vs-formal-vs-material-reporting-contract
```

---

# 43. No prompt chasing

Allowed model-facing change:

```text
one bounded generic holder stance clarification
ONLY if the offline review proves the current holder contract is under-specified.
```

Do NOT change the Directional balance prompt.

Do NOT add FIC-FIN-05-specific text.

Do NOT add another financial-sector phrase to the model prompt.
Issue A is deterministic validation scope.

If holder contract is already unambiguous
and the model simply violates it stochastically:

```text
STOP
NO MODEL CALLS

next_scope =
HOLDER_STANCE_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL
```

No repeated equivalent prompt tweaks.

---

# 44. Deterministic model-call gate

Before new model calls require:

```text
latest ZIP integrity PASS

Sol runtime freeze PASS

M12AC FIC-FIN-08 rep3 exact replay PASS after scope repair

application-role false reject = 0

application-role false accept = 0

actual financial-sector misuse controls still FAIL

holder REVIEW/REDUCE generic contract frozen

FIC-FIN-05 holder target frozen before new output

holder fixtures PASS

new-buyer contract unchanged

business-delta regressions PASS

financial grounding/QTD/WC/debt regressions PASS

decision-material stability fixtures PASS

exact raw diagnostics preserved

legacy formal classifier preserved/reported separately

threshold-zone shadow mapper deterministic tests PASS

threshold-zone not used to rewrite raw direction

Direction thresholds/increments/tie-break unchanged

no majority vote

no averaging

no scorecard

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer substantive change = 0

focused pytest PASS

full local pytest PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

If holder target cannot be frozen safely:

```text
STOP
NO MODEL CALLS
```

---

# 45. New full Sol generation

If deterministic gate passes:

```text
create NEW generation
```

Use exact frozen subjects:

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

Topology:

```text
8 subjects
2 contexts
4 subjects/context
3 repetitions

6 model calls
24 outputs
```

Model:

```text
gpt-5.6-sol
```

Reasoning:

```text
xhigh
```

No real issuers.

No judge calls.

Do not reuse M12AC outputs in the new formal sample.

---

# 46. Whole-generation stop policy

Stop immediately only for:

```text
runtime hard failure

schema failure

invalid evidence identity

objective financial semantic violation

business-delta unsupported change

financial-sector actual misuse

legitimate exclusion false reject

grounding failure
```

Do NOT stop for:

```text
same-direction balance variation

HOLD lean variation

confidence variance

threshold-zone variance

stance variance
```

However stance variance must be reported
and can block final readiness.

---

# 47. Full hard-semantic acceptance

Across 24 outputs require zero:

```text
runtime hard failure

schema hard failure

invalid financial evidence refs

material financial grounding failures

working-capital grounding failures

narrative substitution failures

price/technical/supply Directional contamination

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

true financial-sector industrial-framework application

legitimate contrastive exclusion false reject

business-delta false reject

business-delta false accept

unsupported absolute-state-to-delta

QTD/YTD false reject

QTD/YTD false accept

missing optional evidence treated as bearish fact

AI imperative primary action
```

---

# 48. FIC-FIN-05 full acceptance

Require hard semantics:

```text
high debt/thin cash recognized as negative

stable operating profit recognized as counterevidence

refinancing/maturity severity remains Unknown unless supplied

market-expectation conditionality preserved

business delta = UNCHANGED
```

Core Directional balance is observed,
not exact-target chased.

Holder stance:

```text
all 3 repetitions must match the offline-frozen holder contract target
```

if a unique target was frozen.

If not:

```text
M12AD must have stopped before model calls.
```

---

# 49. FIC-FIN-08 full acceptance

All repetitions:

```text
insurance-valid framework used

industrial net-debt/WC not actually applied

legitimate exclusion/contrastive-negation wording accepted
```

Required:

```text
application_scope_false_reject_count = 0

application_scope_false_accept_count = 0

financial_sector_true_misuse_count = 0
```

---

# 50. Stability reports after full generation

Produce:

## Exact raw state

```text
exact tuple values
exact unique count
```

## Legacy formal stability

Use existing frozen formal classifier semantics.

## Decision-material stability

For each subject:

```text
overall direction
business delta
new-buyer stance
holder stance
classification
```

## Calibration/advisory

```text
balance variance
HOLD lean variance
confidence variance
threshold-zone variance
```

Do not collapse them into one number.

---

# 51. Fresh-real readiness — revised materiality-aware rule

Set:

```text
fresh_real_proof_readiness = READY
```

if all are true:

```text
6 / 6 Sol contexts complete

24 / 24 schema PASS

objective semantic hard failures = 0

invalid evidence refs = 0

grounding failures = 0

business-delta violations = 0

financial-sector true misuse = 0

application/exclusion false reject = 0

PRIMARY_DIRECTION_UNSTABLE subject count = 0

BUSINESS_DELTA_UNSTABLE subject count = 0

NEW_BUYER_STANCE_UNSTABLE subject count = 0

HOLDER_STANCE_UNSTABLE subject count = 0

real issuer exposure = 0

Sol runtime suitable for exposed real holdout
```

The following alone do NOT block fresh-real readiness:

```text
same-direction 0.5 balance variance

HOLD NEUTRAL ↔ HOLD BUY_LEAN/SELL_LEAN variance

directional confidence variance

threshold-zone shadow variance

message advisory variance
```

They must still be reported.

---

# 52. Why this readiness rule is not lowering hard safety

This does NOT allow:

```text
HOLD ↔ SELL
HOLD ↔ BUY
BUY ↔ SELL
```

instability.

It does NOT allow:

```text
holder REVIEW ↔ REDUCE
```

if holder stance is user-decision material.

It does NOT allow:

```text
business delta instability

invalid evidence

financial semantic errors
```

It only stops treating:

```text
exact ordinal intensity variation
within the same primary decision
```

as equivalent to a different investment decision.

---

# 53. If full canary passes material readiness

Then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH
```

Do not start real proof inside M12AD.

Keep production readiness:

```text
NOT_READY
```

until the fresh unseen real proof and production integration review pass.

---

# 54. Failure handling

## A. FIC-FIN-08 scope false reject remains

```text
next_scope =
FINANCIAL_FRAMEWORK_NEGATION_SCOPE_ARCHITECTURE_REVIEW
```

Do not add more phrase patches.

## B. Holder contract cannot be uniquely frozen

```text
next_scope =
HOLDER_STANCE_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL
```

No model calls.

## C. Holder target is frozen but repeated Sol still varies

```text
next_scope =
HOLDER_STANCE_STABILITY_REVIEW_GPT56_SOL
```

Do not majority-vote.

## D. Primary direction varies

```text
next_scope =
PRIMARY_DIRECTION_BOUNDARY_STABILITY_REVIEW_GPT56_SOL
```

## E. Only same-direction calibration variance remains

Do not create another repair task solely to force exact points
if decision-material readiness is otherwise PASS.

Proceed to fresh real proof.

## F. Sol runtime fails

```text
next_scope =
SOL_RUNTIME_REGRESSION_REVIEW
```

No Astra fallback.

---

# 55. Production side-effect firewall

Required:

```text
model_calls_real = 0

real_issuer_model_exposure_count = 0

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

Observe approved paused schedules at start/end.

Do not resume them.

---

# 56. Hosted CI portability

M12AC:

```text
focused = 251 passed

full local = 3366 passed, 2 warnings

ruff = PASS

git diff --check = PASS

hosted CI =
3360 passed
5 failed
1 skipped

new M12AC hosted-CI failures = 0
```

The five failures remain historical portability dependencies.

M12AD must introduce:

```text
new hosted-CI failure count = 0
```

Do not broaden into portability cleanup.

---

# 57. Required full-canary artifacts

If model-call gate passes, produce:

```text
28-fictional-canary-generation-manifest

29-fictional-canary-source-lock

30-run-1-context-01

31-run-1-context-02

32-run-2-context-01

33-run-2-context-02

34-run-3-context-01

35-run-3-context-02

36-full-fictional-hard-semantic-audit

37-full-fictional-financial-framework-scope-audit

38-full-fictional-business-delta-audit

39-full-fictional-grounding-audit

40-full-fictional-exact-raw-state-stability

41-full-fictional-legacy-formal-stability

42-full-fictional-decision-material-stability

43-full-fictional-calibration-variance

44-full-fictional-threshold-zone-observation

45-full-fictional-holder-stance-audit

46-full-fictional-new-buyer-audit

47-full-fictional-confidence-advisory

48-full-fictional-runtime-audit

49-full-fictional-message-specificity-advisory
```

Preserve for every model call:

```text
prompt
schema
raw output
receipt
lifecycle receipt
stdout
stderr
transport log
run document
```

---

# 58. Required completion artifacts

Produce:

```text
50-financial-framework-negation-scope-success-decision

51-holder-contract-success-decision

52-decision-material-stability-policy-success-decision

53-sol-full-canary-completion-decision

54-primary-direction-stability-decision

55-business-delta-stability-decision

56-new-buyer-stability-decision

57-holder-stability-decision

58-calibration-variance-advisory

59-sol-runtime-real-holdout-suitability

60-fresh-real-proof-readiness-decision

61-threshold-zone-shadow-status

62-hosted-ci-portability-handoff

63-astra-future-experiment-handoff

64-production-no-change

65-schedule-pause-observation

66-master-workflow-update

67-program-completion
```

---

# 59. Program-completion fields

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

m12ac_status
m12ad_status

investment_judgment_model_target
investment_judgment_reasoning_effort
runner_model_target_match
model_target_fallback_count

financial_framework_negation_root_cause
financial_framework_negation_repair_status
application_scope_false_reject_count
application_scope_false_accept_count
financial_sector_true_misuse_count

holder_contract_root_cause
holder_contract_change_count
fic_fin_05_holder_target
fic_fin_05_holder_target_reason
holder_contract_fixture_count
holder_contract_fixture_pass_count

decision_material_stability_policy_version
legacy_formal_classifier_changed
exact_raw_state_classifier_changed
threshold_zone_readiness_gate_enabled

directional_prompt_change_count
directional_threshold_changed
directional_increment_changed
hold_lean_contract_changed
calibration_tiebreak_direction_changed

majority_vote_rule_count
balance_averaging_rule_count
fixed_score_rule_count
evidence_count_bucket_rule_count

financial_context_selection_change_count
first_class_projection_change_count
working_capital_validator_semantic_change_count
qtd_ytd_validator_semantic_change_count
market_expectation_contract_change_count
business_delta_semantic_change_count

fictional_generation_id
fictional_subject_count
fictional_context_count
fictional_repetition_count

model_calls_real
model_calls_fictional
model_calls_judge

model_context_success_count
model_context_failure_count
timeout_count
capacity_failure_count
orphan_process_count
cli_internal_retry_event_count
wrapper_retry_count

fictional_output_row_count
fictional_schema_pass_count

objective_semantic_hard_failure_count
invalid_financial_reference_count
grounding_failure_count
business_delta_contract_violation_count

exact_raw_state_stable_subject_count
exact_raw_state_variable_subject_count

legacy_formal_stable_count
legacy_formal_boundary_uncertainty_count
legacy_formal_unstable_count

decision_stable_subject_count
calibration_variance_same_direction_subject_count
primary_direction_unstable_subject_count
business_delta_unstable_subject_count
new_buyer_stance_unstable_subject_count
holder_stance_unstable_subject_count

threshold_zone_variance_subject_count
directional_confidence_variance_subject_count

fic_fin_03_raw_balance_values
fic_fin_03_overall_direction_values
fic_fin_03_decision_material_classification

fic_fin_05_raw_balance_values
fic_fin_05_holder_values
fic_fin_05_decision_material_classification

sol_runtime_real_holdout_suitability

hosted_ci_status
hosted_ci_failure_count
new_hosted_ci_failure_count

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

# 60. Artifact integrity

Freeze all reports/model artifacts/master workflow
before final artifact-index creation.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 61. Final task principle

M12AC changed the picture materially.

The old FIC-FIN-05 core problem:

```text
SELL / HOLD / SELL
```

did not reproduce.

Under the latest clean Sol model-facing contract:

```text
FIC-FIN-05 =
SELL 4.0:6.0 ×3

new buyer =
AVOID ×3

business delta =
UNCHANGED ×3
```

The remaining user-decision variance is:

```text
holder =
REDUCE / REVIEW / REDUCE
```

Meanwhile FIC-FIN-03 shows:

```text
HOLD 5.0
HOLD 5.5
HOLD 5.5
```

with the same:

```text
HOLD direction
WAIT new-buyer
REVIEW holder
LOW confidence
```

That should not be treated as the same class of instability
as a HOLD↔SELL crossing.

The correct M12AD flow is therefore:

```text
repair the last structural Korean contrastive-negation scope bug

→ derive a principled holder REVIEW/REDUCE contract

→ distinguish exact ordinal variance
  from decision-material instability

→ keep threshold-zone shadow-only

→ preserve all raw outputs and legacy diagnostics

→ run one full new Sol/xhigh 8 × 3 canary

→ require zero hard semantic errors
  and zero primary-direction/business-delta/new-buyer/holder instability

→ tolerate and report same-direction calibration/confidence variance

→ if those material gates pass,
   move to the fresh unseen real generalization proof
```

Not:

```text
force every 0.5 point to be identical

treat HOLD NEUTRAL ↔ HOLD BUY_LEAN as HOLD↔BUY

build another HOLD/SELL resolver around a boundary
that did not reproduce

majority-vote holder stance

map SELL mechanically to REDUCE

add another phrase whitelist

change Directional thresholds

return to Astra

resume production monitoring
```

Measure what changes the investment decision separately from what changes only its intensity.
