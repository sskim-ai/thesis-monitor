# Thesis Monitor — Financial Exclusion Validator Repair & Leverage Boundary Review + Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-financial-exclusion-validator-repair-and-leverage-boundary-review-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-financial-exclusion-validator-repair-leverage-boundary-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12F — Financial Exclusion Validator Repair
       + Leverage Boundary Review
       + Full Fictional Canary
```

This task begins only after the GPT-6 Astra M12E attempt stopped with:

```text
status = PARTIAL_STOPPED

fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_FINANCIAL_EXCLUSION_VALIDATOR_REPAIR_AND_LEVERAGE_BOUNDARY_REVIEW
```

M12F has two bounded root-cause items:

```text
A. FIC-FIN-08:
explicit sector-exclusion wording was falsely rejected
as unsupported net-debt / generic-financial-sector reasoning.

B. FIC-FIN-05:
under GPT-6 Astra, the first observation became
HOLD 4.5:5.5 / thesis UNCHANGED / new buyer WAIT,
rather than the historical GPT-5.6 Sol
SELL 4.0:6.0 / WEAKENED / AVOID pattern.
```

Item A is a validator defect.

Item B must NOT be called a regression until the new GPT-6 Astra ordinal contract is reviewed.
The prior GPT-5.6 Sol result is historical evidence only.

M12F must first freeze both root causes offline.
If both can be resolved by bounded generic contracts, implement them and rerun the entire
8-subject fictional canary from a NEW GPT-6 Astra generation.

M12F must NOT:

```text
change the 6.0 BUY/SELL threshold
change 0.5 balance increments
change HOLD lean mapping
change the conservative tie-break direction
add a fixed financial scorecard
change financial-context selection
change first-class typed evidence architecture
change source mappings
change source sufficiency
change Price-Timing
change renderer ownership
run a real issuer proof
merge/deploy production
resume monitoring schedules
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260909-bounded-financial-context-boundary-calibration-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
2cfab9aa676cc61af733198bddadb18971fcb631ca22b17e4735c05a9734484e
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest artifact index must also be recomputed.

Do not trust the report if:

```text
hash mismatch != 0
size mismatch != 0
missing indexed payload != 0
```

---

# 2. Latest M12E result — frozen facts

M12E deterministic implementation completed:

```text
boundary calibration clarification = IMPLEMENTED

focused pytest = PASS 107 / 107

full pytest = PASS 3123 / 3123

ruff = PASS

git diff --check = PASS

threshold changed = false

increment changed = false

HOLD lean changed = false

tie-break direction changed = false
```

GPT-6 Astra canary started a new generation but stopped during repetition 1:

```text
planned fictional calls = 6

completed fictional calls = 2

transport-success contexts = 2 / 2

schema-valid rows = 8 / 8

accepted canary contexts = 1

failed canary contexts = 1

remaining contexts started = 0
```

Runtime:

```text
timeout = 0
capacity failure = 0
orphan = 0
wrapper retry = 0
```

Formal repeated stability:

```text
NOT_MEASURED
```

Do not infer stability from one repetition.

---

# 3. Canonical model target from M12F forward

User-authorized target:

```text
display model =
GPT-6 Astra

canonical runtime model id =
gpt-6-astra

reasoning effort =
xhigh
```

This applies to:

```text
Codex implementation/review authoring

fictional investment-judgment canary

future real investment-judgment proof
```

Hard rules:

```text
no silent fallback

no gpt-5.6-sol fallback

no reasoning-effort downgrade

no "ultra" authoring

no alternative model substitution
```

At task start inspect the available Codex/task execution provenance.

Required:

```text
authoring model = gpt-6-astra
authoring effort = xhigh
```

If not:

```text
STOP
AUTHORING_MODEL_TARGET_MISMATCH
```

Before model-canary execution verify:

```text
runner model = gpt-6-astra
runner effort = xhigh
```

If unavailable:

```text
STOP
MODEL_TARGET_UNAVAILABLE
```

Required:

```text
model_target_fallback_count = 0
```

M12E historical note:

```text
implementation authoring was observed at gpt-6-astra / ultra
and did not match the requested effort.

frozen implementation review + canary execution were
gpt-6-astra / xhigh.
```

Preserve this disclosure.
Do not rewrite history.

---

# 4. Cross-model comparison rule

M12S was based on GPT-5.6 Sol preserved outputs.

M12E uses GPT-6 Astra.

Therefore:

```text
GPT-5.6 Sol output
vs
GPT-6 Astra output
```

may be compared descriptively,
but must NOT be treated as:

```text
same-model regression evidence
```

Required:

```text
cross_model_same_runtime_claim_count = 0
```

FIC-FIN-05 historical SELL 6.0 is not a hard expected label solely because the old model produced it.

The expected GPT-6 Astra bucket must come from the frozen generic calibration contract.

---

# 5. Issue A — FIC-FIN-08 false reject

Preserved candidate text:

```text
"보험 인수 규율과 규제자본으로 평가하는 보험사이며
일반 영업기업의 순부채·운전자본 틀은 적용하지 않는다."
```

Frozen validator errors:

```text
net_debt_claim_without_complete_net_debt_evidence

financial_sector_generic_reasoning
```

Independent forensic finding:

```text
EXPLICIT_NOT_APPLICABLE_CLAIM_FALSE_REJECT
```

The candidate did NOT:

```text
assert a net-debt value

apply industrial net-debt analysis

apply industrial working-capital analysis

use a typed industrial financial ref
```

It explicitly excluded those frameworks.

M12F must preserve the original failed generation verdict.
Do not hotfix the old raw output.

---

# 6. Issue A root cause

Current validator behavior includes token-presence / phrase-presence logic.

Known mechanisms:

```text
"순부채" token
→ treated as a net-debt claim
even in explicit negation / non-applicability text.

financial-sector forbidden-token scan
→ treated as generic industrial reasoning
even when the candidate says the framework does not apply.
```

M12F must repair:

```text
assertion/application semantics
vs
explicit exclusion/non-applicability semantics
```

generically.

Do NOT implement:

```text
if ticker == FIC-FIN-08
```

Do NOT patch only one exact Korean sentence.

---

# 7. Exclusion-claim contract

The validator must distinguish:

```text
ASSERTION_OR_APPLICATION

EXPLICIT_EXCLUSION

UNCERTAIN_OR_AMBIGUOUS
```

for high-risk generic financial framework language.

Examples:

## Unsupported assertion — reject

```text
"순부채가 높아 재무위험이 크다."
```

without valid complete net-debt evidence.

## Generic financial-sector misuse — reject

```text
"보험사의 순부채와 운전자본 악화가 핵심 리스크다."
```

using industrial-company framework.

## Explicit exclusion — allow

```text
"보험사에는 일반 영업기업의 순부채 틀을 적용하지 않는다."

"운전자본 기준은 이 금융업종의 핵심 평가틀로 사용하지 않는다."
```

when no contradictory application occurs elsewhere.

## Mixed / contradictory — reject or needs-review

```text
"보험사라 순부채 틀은 적용하지 않지만
순부채가 높아 SELL 근거다."
```

Explicit exclusion must not immunize a real misuse elsewhere in the same candidate.

---

# 8. Claim-polarity / scope detection

Prefer bounded structured detection over a loose phrase whitelist.

The validator may use:

```text
claim text

field path

linked evidence refs

sector framework

nearby negation / exclusion semantics

other candidate fields containing actual application
```

Do not build a general Korean NLP engine.

Required support for explicit Korean exclusion semantics may include bounded forms equivalent to:

```text
적용하지 않는다

사용하지 않는다

평가하지 않는다

해당하지 않는다

일반 틀을 배제한다

일반 영업기업 기준이 아니다
```

and equivalent supported English forms.

Do not pass every sentence containing `않`.

---

# 9. Exclusion validator negative controls

Required rejection fixtures:

```text
unsupported net-debt assertion with no valid net-debt evidence

financial-sector industrial WC assertion

financial-sector industrial net-debt assertion

sentence begins with exclusion but later applies the same metric

exclusion word appears in unrelated clause

"순부채가 중요하지 않지 않다" style ambiguous/double-negative

candidate has one exclusion sentence
but material_directional_anchor_basis uses unsupported industrial net-debt ref
```

No false immunity.

---

# 10. Exclusion validator positive controls

Required pass fixtures:

```text
insurance explicit industrial-net-debt exclusion

bank explicit generic-WC exclusion

financial sector exclusion + sector-valid capital/liquidity framework

non-financial issuer valid net-debt claim with complete typed evidence

candidate mentions "순부채" only to explain non-applicability
```

---

# 11. FIC-FIN-08 regression expectations

After repair, offline replay of the preserved M12E FIC-FIN-08 raw output should yield:

```text
net_debt_claim_without_complete_net_debt_evidence = 0

financial_sector_generic_reasoning = 0
```

only because the relevant sentence is explicit exclusion.

All other FIC-FIN-08 safety rules remain active.

If the candidate contains any actual industrial financial-sector misuse elsewhere:

```text
FAIL
```

Do not simply declare the entire row PASS based on one exclusion sentence.

---

# 12. Issue B — FIC-FIN-05 GPT-6 Astra leverage boundary

Preserved GPT-6 Astra M12E first observation:

```text
overall_direction = HOLD

directional_balance = 4.5 : 5.5

hold_lean = SELL_LEAN

business_thesis_change = UNCHANGED

new buyer = WAIT

holder = REVIEW
```

Material financial facts:

```text
complete interest-bearing debt total

cash and cash equivalents

thin financial buffer / high debt burden

stable positive operating profit

refinancing terms and maturity concentration Unknown

valuation Unknown
```

Candidate explicitly says:

```text
"높은 부채 부담과 얇은 현금 완충력은 부정적 근거다."

"안정적 영업이익과 미확인 차환 조건·만기 집중도를 함께 고려하면
부정적 기울기까지가 타당하다."
```

This is not a financial parsing error.

---

# 13. Historical FIC-FIN-05 context

Under the prior GPT-5.6 Sol full fictional sample:

```text
SELL 4.0:6.0 in all 3 repetitions

business thesis = WEAKENED in all 3

new buyer = AVOID in all 3

holder = REDUCE / REVIEW / REDUCE
```

M12S classified only the holder stance as a repeated-field ambiguity because core balance was stable in that old model sample.

Do NOT make the old SELL label a mandatory GPT-6 Astra result.

Use it only to identify the leverage-boundary question.

---

# 14. Leverage boundary review — primary question

Determine under the current generic M12E ordinal contract:

```text
Does complete high interest-bearing debt
plus thin compatible cash
constitute enough independent negative support
for minimum SELL 6.0

despite stable current operating profit
and missing refinancing/maturity confirmation?

Or do debt + cash together represent one financial-resilience anchor
whose severity/persistence remains materially unresolved,
making HOLD SELL_LEAN 5.5 the correct conservative bucket?
```

Freeze one generic answer before any new model call.

---

# 15. Debt/cash independence contract

Review whether:

```text
complete debt total
and
cash balance
```

are:

```text
A. two independent corroborating economic facts

B. two components of one financial-resilience / net-debt economic dimension

C. context-dependent
```

Do not decide based on evidence-ref count.

Relevant factors:

```text
derivation lineage

economic independence

whether both are needed to establish net debt

whether one can independently create financing risk

operating earnings support

maturity/refinancing information

debt service / coverage information

sector capital structure
```

No scorecard.

---

# 16. Minimum SELL 6.0 leverage contract

If the review concludes that minimum SELL 6.0 can be justified from leverage alone,
freeze the generic necessary/sufficient pattern.

Example dimensions to evaluate:

```text
complete debt scope

cash/liquidity adequacy

current operating cash/profit support

refinancing/maturity visibility

evidence of actual financing pressure

dilution/refinancing dependency

covenant/debt-service stress
```

Do NOT require all of them mechanically.

Do NOT create a numeric leverage threshold unless an existing sector-specific contract already has one.

---

# 17. HOLD SELL_LEAN 5.5 leverage contract

If 5.5 is correct when:

```text
high debt / thin cash is established

but operating profit remains stable

and refinancing/maturity/debt-service severity is unresolved
```

freeze that generic rule explicitly.

Missing refinancing details remain:

```text
confidence / strength limit

not bullish evidence
```

Do not make Unknown itself a positive factor.

---

# 18. Symmetry / positive financial resilience

Audit the positive-side symmetry.

Examples:

```text
low/complete debt
plus strong cash
```

should not automatically create BUY 6.0
without a separate positive enterprise-value/business anchor.

Financial resilience may:

```text
corroborate
limit downside
increase conviction
```

but must not become a standalone fixed score.

Freeze symmetry.

---

# 19. Business thesis change vs absolute Directional direction

M12F must separately review:

```text
business_thesis_change = UNCHANGED
```

vs:

```text
absolute direction = HOLD SELL_LEAN / SELL
```

A company can have:

```text
unchanged business thesis
but structurally weak balance sheet
```

if the weak leverage was already part of baseline.

Conversely:

```text
WEAKENED
```

requires actual deterioration/change relative to the relevant baseline,
not merely a negative absolute financial condition.

Because fictional canary cases mix absolute and synthetic change context,
audit the case contract before treating `UNCHANGED` as a regression.

Do NOT make business thesis change mechanically follow absolute BUY/HOLD/SELL.

---

# 20. FIC-FIN-05 fictional case contract audit

Inspect the frozen fictional input/manifest.

Determine:

```text
Was high debt / thin cash newly worsened in the synthetic scenario?

Or was it a current absolute condition with no explicit baseline deterioration?

What evidence, if any, supports WEAKENED rather than UNCHANGED?

What exactly is the intended test:
absolute financial resilience
or Daily Delta change?
```

If the case does not encode actual deterioration:

```text
UNCHANGED may be semantically correct
```

even when absolute Directional direction is negative.

Do not preserve a historical `WEAKENED` label merely because the old model emitted it.

---

# 21. New-buyer stance review for leverage case

Inspect:

```text
WAIT vs AVOID
```

under current contract.

Do not repair new-buyer stance globally in M12F unless the leverage review proves
one generic rule is inseparable from the core balance rule.

Default:

```text
new-buyer stance contract remains frozen
```

Record whether WAIT is acceptable when:

```text
leverage is a negative absolute condition
but severity / refinancing path remains unresolved
```

or whether AVOID is required only once the fundamental negative threshold is clearly met.

No mechanical mapping:

```text
SELL -> AVOID
```

unless existing contract already requires it.

---

# 22. Holder stance remains separate

Do not repair:

```text
HOLDABLE / REVIEW / REDUCE
```

in M12F.

Record FIC-FIN-05 holder = REVIEW descriptively.

Historical holder ambiguity remains a later independent issue.

Required:

```text
holder_stance_contract_change_count = 0
```

---

# 23. Leverage review root-cause classification

Freeze one:

```text
ASTRA_OUTPUT_CONSISTENT_WITH_CURRENT_5_5_CONTRACT

CURRENT_CONTRACT_SUPPORTS_MINIMUM_SELL_6_0

LEVERAGE_BOUNDARY_CONTRACT_UNDERSPECIFIED

FICTIONAL_CASE_CHANGE_SEMANTICS_MISMATCH

MIXED
```

If `LEVERAGE_BOUNDARY_CONTRACT_UNDERSPECIFIED`,
freeze a bounded generic clarification before model calls.

Do not use a ticker/case-specific label rule.

---

# 24. Branch logic before implementation

## Branch A — only exclusion validator defect; leverage output already contract-consistent

Implement only:

```text
financial exclusion validator repair
```

No calibration prompt change.

Then full new canary.

## Branch B — exclusion validator defect + bounded leverage contract ambiguity

Implement:

```text
financial exclusion validator repair

plus one bounded generic leverage-boundary clarification
```

Then full new canary.

## Branch C — leverage issue requires new data/sector model or broad redesign

Do NOT run model calls.

Set a bounded next scope.

## Branch D — FIC-FIN-05 historical expectation was invalid cross-model baggage

Document that result.
Do not change calibration merely to reproduce GPT-5.6 Sol.

Proceed after exclusion repair if current contract is clear.

---

# 25. No threshold/increment change

Hard freeze:

```text
BUY threshold = 6.0

SELL threshold = 6.0

balance increment = 0.5

HOLD 5.5:4.5 = BUY_LEAN

HOLD 5.0:5.0 = NEUTRAL

HOLD 4.5:5.5 = SELL_LEAN

conservative adjacent tie-break toward 5.0
```

Required:

```text
directional_threshold_changed = false

directional_increment_changed = false

hold_lean_contract_changed = false

calibration_tiebreak_direction_changed = false
```

---

# 26. No scorecard

Forbidden:

```text
debt = -0.5

cash = -0.5

high debt + low cash = SELL

Unknown refinancing = +0.5 toward HOLD

evidence count determines bucket
```

Required:

```text
fixed_financial_score_rule_count = 0

evidence_count_bucket_rule_count = 0
```

---

# 27. Preserve solved financial architecture

Required unchanged:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

selected-only typed projection

financial_decision_context detail

material-claim scoped working-capital grounding

QTD/YTD plain-Korean validator repair

FCF / YoY / debt-completeness / normalized-earnings validators
```

Required:

```text
financial_context_selection_change_count = 0

first_class_projection_change_count = 0

working_capital_validator_semantic_change_count = 0

qtd_ytd_validator_semantic_change_count = 0
```

Only the explicit exclusion-claim validator may change,
plus a bounded leverage calibration clarification under Branch B.

---

# 28. Prompt change boundary

If Branch A:

```text
Directional prompt change count = 0
```

If Branch B:

only one bounded generic leverage boundary clarification may change the prompt/calibration text.

No other prompt changes.

Produce line-by-line semantic diff.

---

# 29. Output schema / renderer / Price-Timing freeze

Required:

```text
output_schema_change_count = 0

renderer_substantive_change_count = 0

price_timing_prompt_change_count = 0

price_timing_semantic_change_count = 0
```

No new output grounding field.

---

# 30. Source sufficiency / lifecycle / warning freeze

Required:

```text
source_sufficiency_semantic_change_count = 0

daily_delta_semantic_change_count = 0

monitoring_lifecycle_semantic_change_count = 0

warning_semantic_change_count = 0
```

No source/provider changes.

---

# 31. Deterministic validator regression matrix

Before model calls, exclusion validator repair must classify:

## PASS

```text
preserved M12E FIC-FIN-08 explicit exclusion sentence

generic insurer explicit industrial-net-debt exclusion

generic bank explicit working-capital exclusion

non-financial valid net-debt claim with complete typed evidence
```

## FAIL

```text
unsupported net-debt assertion

insurance industrial net-debt assertion

insurance industrial WC assertion

mixed exclusion + actual use

contradictory exclusion / application

unsupported industrial metric used in material_directional_anchor_basis
```

False reject = 0.

False accept = 0.

---

# 32. Deterministic leverage fixtures

Freeze generic fixtures based on the selected leverage-boundary contract.

At minimum:

## LEV-01 — complete high debt + thin cash + stable operating profit + refinancing Unknown

Expected bucket must be frozen by M12F review:

```text
5.5 or 6.0
```

not left ambiguous.

## LEV-02 — same leverage + clear refinancing / debt-service stress

Expected:

```text
minimum negative direction may be supported
```

## LEV-03 — high debt but strong cash / liquidity and stable operating support

Expected:

```text
do not mechanically infer minimum SELL
```

## LEV-04 — partial debt components only

Expected:

```text
no total-debt / net-debt conclusion
```

## LEV-05 — financial sector

Expected:

```text
industrial leverage contract not applicable
```

No deterministic investment score.

These fixtures audit the ordinal contract, not calculate a score.

---

# 33. FIC-FIN-05 deterministic replay

Apply the frozen M12F leverage contract to the preserved GPT-6 Astra FIC-FIN-05 output.

Classify:

```text
CONTRACT_CONSISTENT

CONTRACT_INCONSISTENT

AMBIGUOUS
```

If inconsistent and Branch B repair is implemented,
create a corrected contract fixture.

Do NOT rewrite the historical model output.

Do NOT mark the old GPT-6 Astra observation PASS/FAIL retroactively based on new wording.

---

# 34. Phase A model-call gate

Before any new model calls require:

```text
Codex authoring provenance = gpt-6-astra / xhigh

latest ZIP integrity PASS

FIC-FIN-08 false reject reproduced

exclusion validator root cause frozen

exclusion validator positive fixtures PASS

exclusion validator negative fixtures rejected

FIC-FIN-05 case-change semantics audit complete

leverage boundary root cause frozen

LEV-01 expected bucket explicitly frozen

threshold/increment/lean/tie-break unchanged

no scorecard

first-class financial architecture unchanged

financial validators unchanged except exclusion-claim repair

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer unchanged

focused pytest PASS

full repository pytest PASS

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

# 35. New GPT-6 Astra full fictional generation

Only after Phase A PASS.

Create a NEW generation ID.

Use exact same frozen 8 subjects:

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

Do not change case data.

Do not continue M12E run-2.

Do not merge old-model outputs into the new stability sample.

---

# 36. Full canary topology

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

Model:

```text
gpt-6-astra
```

Reasoning:

```text
xhigh
```

No real issuer calls.

No judge calls.

---

# 37. Runtime contract

Use:

```text
runtime mode = MODEL_CONTEXT_COUPLED

subjects per context = 4

timeout = 1800 seconds

single authoritative watchdog = true

wrapper auto-retry = 0

batch split = 0
```

Each call:

```text
unique invocation ID

unique runtime namespace

unique working directory

unique session identity
```

Required actual receipt:

```text
model = gpt-6-astra

reasoning_effort = xhigh
```

No fallback.

---

# 38. Whole-generation stop rule

On any hard semantic failure:

```text
stop generation immediately

preserve emitted outputs

do not selectively continue later contexts
```

On runtime failure:

```text
classify separately

no wrapper retry
```

Any post-repair rerun requires a new generation.

---

# 39. Canary hard semantic gates

Require zero across all completed rows:

```text
invalid financial evidence refs

material financial grounding failures

working-capital grounding failures

narrative substitution failures

price/technical/supply Directional refs

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

financial-sector generic industrial financial reasoning

explicit financial-sector exclusion false rejects

missing optional evidence treated as bearish

fixed financial scoring

QTD/YTD false rejects

QTD/YTD false accepts

AI imperative primary action
```

---

# 40. FIC-FIN-08 hard expectation

Every repetition must satisfy:

```text
financial-sector routing is explicit

industrial net-debt/WC framework is not applied

an explicit sentence saying the industrial framework is not applicable
does not trigger a false reject

actual misuse would still fail
```

Required:

```text
exclusion_validator_false_reject_count = 0

financial_sector_true_misuse_count = 0
```

---

# 41. FIC-FIN-05 hard leverage expectation

Every repetition must be audited against the M12F-frozen generic leverage contract.

Required report per run:

```text
absolute leverage evidence

operating support

refinancing/maturity Unknown

business-thesis change semantics

directional balance

new-buyer stance

holder stance

contract consistency
```

Primary hard requirement:

```text
directional balance must be contract-consistent
```

Do NOT require reproduction of GPT-5.6 Sol labels.

---

# 42. M12E boundary calibration targets remain

For FIC-FIN-01 / 02 / 04,
audit the GPT-6 Astra outputs under the already-implemented M12E calibration:

```text
FIC-FIN-01:
strong quality + unresolved stronger confirmation

FIC-FIN-02:
cash-conversion divergence + shared lineage + causal Unknown

FIC-FIN-04:
flat operations + non-operating boost
```

Do not change these contracts in M12F.

Expected generic target buckets from the M12E contract remain:

```text
FIC-FIN-01:
minimum BUY 6.0 when stronger 6.5 support remains unresolved

FIC-FIN-02:
HOLD 4.5:5.5 SELL_LEAN
when shared-lineage cash evidence + causal/reversibility Unknown
do not justify independent 6.0 SELL

FIC-FIN-04:
HOLD 5.0:5.0 NEUTRAL
when operations are flat and non-operating support is the only positive offset
```

If GPT-6 Astra repeatedly violates these despite the frozen contract,
classify a calibration failure.

---

# 43. Core balance stability target

For the full 3-repetition GPT-6 Astra sample:

Required:

```text
FIC-FIN-01 directional_balance unique count = 1

FIC-FIN-02 directional_balance unique count = 1

FIC-FIN-04 directional_balance unique count = 1

FIC-FIN-05 directional_balance unique count = 1
```

and:

```text
each repeated bucket is contract-consistent
```

Do not accept stable-but-wrong labels.

---

# 44. New-buyer / holder stance measurement

Do not globally repair these fields in M12F.

Measure:

```text
new-buyer stance variance by subject

holder stance variance by subject
```

If independent stance ambiguity remains after core balance is stable:

```text
fresh real proof readiness = NOT_READY
```

and select the bounded stance-repair scope.

Do not hide it.

---

# 45. Formal stability classifier remains frozen

Run the SAME formal classifier.

Report:

```text
STABLE

BOUNDARY_UNCERTAINTY

UNSTABLE
```

No majority vote.

No averaging.

No classifier change.

Required:

```text
opposite_direction_reversal_count = 0
```

---

# 46. Core-only stability view

Also produce descriptive:

```text
CORE_BALANCE_DIRECTION_STABLE

CORE_BALANCE_DIRECTION_UNSTABLE
```

based only on:

```text
overall_direction

directional_balance

hold_lean
```

This does not replace formal stability.

---

# 47. Cross-model descriptive table

Produce a descriptive table:

```text
GPT-5.6 Sol historical M12D

GPT-6 Astra M12E partial

GPT-6 Astra M12F new full generation
```

for:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-04
FIC-FIN-05
```

But label explicitly:

```text
CROSS_MODEL_DESCRIPTIVE_ONLY
```

Do NOT compute a same-model improvement rate across GPT-5.6 Sol and GPT-6 Astra.

---

# 48. Message specificity advisory

If full canary completes,
run the existing advisory.

Measure:

```text
typed financial anchor specificity

period specificity

case-specific checkpoint

generic substantive repetition

renderer-introduced repetition
```

Do not change renderer/message copy in M12F.

---

# 49. No real issuer exposure

Required:

```text
model_calls_real = 0

real_issuer_model_exposure_count = 0
```

Fresh real proof remains later.

---

# 50. Production side-effect firewall

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

# 51. Required artifacts — provenance / model target

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12f-scope-freeze

04-model-target-contract

05-codex-authoring-model-provenance

06-investment-runner-model-provenance

07-cross-model-comparison-policy
```

---

# 52. Required artifacts — exclusion validator

Produce:

```text
08-fic-fin-08-false-reject-reproduction

09-financial-exclusion-claim-root-cause

10-exclusion-claim-semantics-contract

11-exclusion-validator-before-after

12-exclusion-positive-fixtures

13-exclusion-negative-fixtures

14-mixed-exclusion-application-control

15-fic-fin-08-offline-regression
```

---

# 53. Required artifacts — leverage review

Produce:

```text
16-fic-fin-05-case-change-semantics-audit

17-fic-fin-05-gpt6-output-forensic

18-debt-cash-independence-contract

19-minimum-sell-leverage-contract

20-sell-lean-leverage-contract

21-positive-resilience-symmetry-contract

22-lev-01-contract-fixture

23-lev-02-contract-fixture

24-lev-03-contract-fixture

25-lev-04-contract-fixture

26-lev-05-financial-sector-fixture

27-leverage-boundary-root-cause

28-fic-fin-05-contract-replay
```

---

# 54. Required freeze/no-change artifacts

Produce:

```text
29-threshold-increment-lean-tiebreak-freeze-proof

30-first-class-financial-evidence-freeze-proof

31-financial-selector-freeze-proof

32-working-capital-validator-freeze-proof

33-qtd-ytd-validator-freeze-proof

34-other-financial-validator-freeze-proof

35-output-schema-freeze-proof

36-price-timing-no-change-proof

37-renderer-ownership-no-change-proof

38-source-sufficiency-no-change-proof

39-daily-delta-no-change-proof
```

---

# 55. Required deterministic validation artifacts

Produce:

```text
40-focused-test-results

41-full-test-results

42-ruff-and-diff-results

43-model-call-gate
```

If leverage review cannot freeze a generic contract:

```text
43-model-call-gate =
NO_MODEL_CALLS
```

---

# 56. Required fictional-canary artifacts

Only if Phase A passes:

```text
44-fictional-canary-generation-manifest

45-fictional-canary-source-lock

46-run-1-context-01

47-run-1-context-02

48-run-2-context-01

49-run-2-context-02

50-run-3-context-01

51-run-3-context-02

52-full-fictional-semantic-audit

53-full-fictional-exclusion-validator-audit

54-full-fictional-leverage-boundary-audit

55-full-fictional-grounding-audit

56-full-fictional-formal-stability

57-full-fictional-core-only-stability

58-full-fictional-stance-variance-audit

59-cross-model-descriptive-table

60-full-fictional-message-specificity-advisory

61-runtime-observations
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

# 57. Required completion artifacts

Produce:

```text
62-exclusion-validator-repair-success-decision

63-leverage-boundary-success-decision

64-core-balance-stability-decision

65-new-buyer-stance-followup-decision

66-holder-stance-followup-decision

67-fresh-real-proof-readiness-decision

68-production-no-change

69-schedule-pause-observation

70-master-workflow-update

71-program-completion
```

---

# 58. Deterministic acceptance criteria

Before model calls require:

```text
authoring model = gpt-6-astra / xhigh

latest result integrity PASS

FIC-FIN-08 false reject reproduced

explicit financial-sector exclusions pass after repair

real unsupported/assertive financial-sector misuse still fails

no ticker-specific validator logic

FIC-FIN-05 case semantics audited

leverage boundary contract frozen generically

LEV fixtures PASS

6.0 threshold unchanged

0.5 increment unchanged

HOLD lean unchanged

tie-break direction unchanged

no scorecard

first-class financial architecture unchanged

all unrelated financial validators unchanged

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer unchanged

focused/full tests PASS

ruff PASS

git diff --check PASS
```

---

# 59. Full-canary acceptance criteria

If the full new GPT-6 Astra canary runs:

```text
6 / 6 model contexts complete

24 / 24 rows schema PASS

hard financial semantic violations = 0

explicit-exclusion false rejects = 0

financial-sector true misuse = 0

grounding failures = 0

QTD/YTD false reject = 0

QTD/YTD false accept = 0

price/technical/supply violations = 0

AI imperative primary action = 0

FIC-FIN-01 core balance unique count = 1

FIC-FIN-02 core balance unique count = 1

FIC-FIN-04 core balance unique count = 1

FIC-FIN-05 core balance unique count = 1

all four targeted buckets are contract-consistent

opposite-direction reversal count = 0

wrapper retry = 0

unexpected timeout/capacity/orphan = 0
```

Formal stability must be measured.

---

# 60. Fresh-real readiness logic

## A. Full semantics + core balance + formal stance fields all stable

```text
fresh_real_proof_readiness = READY

next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT6_ASTRA_XHIGH
```

## B. Core balance stable, new-buyer stance still ambiguous

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA
```

## C. Core balance stable, holder stance still ambiguous

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA
```

## D. Both stance ambiguities remain

Repair sequentially.

Default order:

```text
new-buyer stance
then holder stance
```

unless the new evidence proves otherwise.

## E. FIC-FIN-05 leverage boundary remains unstable or contract-inconsistent

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_LEVERAGE_BOUNDARY_CALIBRATION_REPAIR_GPT6_ASTRA
```

## F. Exclusion validator still false-rejects

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_FINANCIAL_EXCLUSION_VALIDATOR_REPAIR_V2
```

---

# 61. Production readiness

Even if M12F passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real GPT-6 Astra generalization proof

production integration review

explicit user authorization
```

Monitoring schedules remain paused.

---

# 62. Program-completion fields

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

m12e_status
m12f_status

implementation_model_target
implementation_reasoning_effort
investment_judgment_model_target
investment_judgment_reasoning_effort

authoring_model_target_match
investment_runner_target_match
model_target_fallback_count
cross_model_same_runtime_claim_count

financial_exclusion_validator_root_cause
financial_exclusion_validator_repair_status

fic_fin_08_offline_regression_status
explicit_exclusion_false_reject_count
financial_sector_true_misuse_count

fic_fin_05_case_change_semantics
leverage_boundary_root_cause
leverage_boundary_contract_status
fic_fin_05_contract_replay_status

directional_threshold_changed
directional_increment_changed
hold_lean_contract_changed
calibration_tiebreak_direction_changed

fixed_financial_score_rule_count
evidence_count_bucket_rule_count

financial_context_selection_change_count
first_class_projection_change_count
working_capital_validator_semantic_change_count
qtd_ytd_validator_semantic_change_count
other_financial_validator_change_count

directional_prompt_change_count
output_schema_change_count
price_timing_prompt_change_count
renderer_substantive_change_count

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

hard_financial_semantic_violation_count
invalid_financial_reference_count
grounding_failure_count

fic_fin_01_directional_balance_unique_count
fic_fin_02_directional_balance_unique_count
fic_fin_04_directional_balance_unique_count
fic_fin_05_directional_balance_unique_count

target_bucket_contract_violation_count

formal_stable_count
formal_boundary_uncertainty_count
formal_unstable_count
opposite_direction_reversal_count

core_only_stable_count
core_only_unstable_count

new_buyer_stance_variance_subject_count
holder_stance_variance_subject_count

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

Anything unmeasured must be:

```text
NOT_MEASURED
```

---

# 63. Artifact integrity

Freeze:

```text
program completion

master workflow

all deterministic reports

all attempted model-call artifacts
```

before final index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 64. Final task principle

The first GPT-6 Astra M12E attempt did not reveal a financial-data ingestion failure.

It revealed two narrower questions:

```text
1. explicit financial-sector exclusion language
   is being mistaken for actual misuse by frozen validators.

2. GPT-6 Astra places the leverage case at HOLD SELL_LEAN 5.5,
   while the old GPT-5.6 Sol sample placed it at minimum SELL 6.0.
```

The correct next flow is:

```text
fix assertion-vs-exclusion validation

→ audit the leverage boundary under the CURRENT generic contract

→ do not force old-model labels onto the new model

→ freeze one generic leverage rule

→ keep threshold/increment/tie-break unchanged

→ rerun all 8 fictional cases under
   gpt-6-astra / xhigh from a clean generation

→ measure full core + formal stability
```

Not:

```text
special-case FIC-FIN-08
```

Not:

```text
make "순부채" legal everywhere
```

Not:

```text
force FIC-FIN-05 back to SELL because GPT-5.6 Sol said SELL
```

Not:

```text
change the 6.0 threshold
```

Not:

```text
use a leverage scorecard
```

Not:

```text
author the task at ultra
```

Not:

```text
run a real cohort before the full GPT-6 Astra fictional proof passes
```

And not:

```text
resume production monitoring
```

Validate the new model against the generic contract, not against the old model's labels.
