# Thesis Monitor — Financial-Sector Exclusion Validator & Market-Expectation/Leverage Boundary Repair + Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260910-financial-sector-exclusion-validator-and-market-expectation-leverage-boundary-repair-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260910-financial-sector-exclusion-validator-market-expectation-leverage-boundary-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12U — Bounded GPT-6 Astra Financial Context Repair
       A. Financial-Sector Explicit-Exclusion Validator
       B. Market-Expectation vs Leverage Corroboration Boundary
       C. New Full Fictional Canary
```

This task begins only after M12T completed its runtime review and a new GPT-6 Astra generation stopped during repetition 1 because of two semantic-contract blockers:

```text
1. FIC-FIN-08:
explicit non-applicability wording
"일반 사업회사의 부채·운전자본 틀은 적용 대상이 아니다"
was falsely rejected as financial-sector generic reasoning.

2. FIC-FIN-05:
GPT-6 Astra used supplied market-expectation evidence E07
as an additional negative axis alongside debt/cash resilience,
producing SELL 4.0:6.0 instead of the M12F frozen HOLD 4.5:5.5 target.
```

M12T also showed that the prior 1800-second timeout did NOT reproduce:

```text
new context-01 elapsed ≈ 321.7 seconds
new context-02 elapsed ≈ 331.9 seconds
timeout = 0
CLI internal retry = 0
wrapper retry = 0
```

Therefore M12U is NOT a transport-repair phase.

M12U must first resolve the two bounded semantic-contract questions offline.
If both are frozen safely and deterministic validation passes,
rerun the entire 8-subject × 3-repeat fictional canary from a NEW generation.

M12U must NOT:

```text
increase timeout
add wrapper retry
split contexts
change model
change reasoning effort
change BUY/SELL threshold
change 0.5 increments
change HOLD lean mapping
change conservative tie-break direction
change financial-context selector
change first-class typed evidence architecture
change source mappings
change source sufficiency
change Price-Timing
change renderer substantive ownership
run real issuers
merge/deploy production
resume monitoring schedules
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260910-bounded-astra-transport-timeout-review-new-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
d3202a35bcf5b13cd0afc86b59b1eda76c5088ecab377f3e63f316f6ca7a004b
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest artifact integrity:

```text
indexed payloads = 142
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Recompute independently before trusting the bundle.

---

# 2. M12T repository provenance

Reported final state:

```text
branch =
codex/20260910-astra-transport-review-m12t

base_sha =
be3ee8d17e97edcf82ab2c8535d222c03b13667f

work_instruction_commit =
09f434f3353db01e75af8b6c7b1526679f16fe99

implementation_commit =
695464f2b122bfe6e5378476b066cd945415eb61

report_commit =
e8e82e353ff71f251c66a1c6940af4d70ff0c778

final_head_sha =
e8e82e353ff71f251c66a1c6940af4d70ff0c778
```

At task start use actual repository HEAD as authority.

Record:

```text
actual_branch
actual_head
working_tree_state
remote_branch_sha
```

If unexplained semantic drift exists in:

```text
Directional balance contract
financial validators
first-class evidence projection
fictional fixtures
runtime runner
```

STOP:

```text
UNEXPLAINED_M12U_BASELINE_DRIFT
```

---

# 3. Model target — authoritative

From this task forward:

```text
Codex implementation/review authoring =
gpt-6-astra / xhigh

investment-judgment model =
gpt-6-astra / xhigh
```

Hard rules:

```text
no gpt-5.6-sol fallback
no alternative model fallback
no "ultra"
no reasoning downgrade
no silent model-id substitution
```

Before implementation verify actual authoring provenance.

Required:

```text
authoring_model_target_match = true
```

If not:

```text
STOP
AUTHORING_MODEL_TARGET_MISMATCH
```

Before canary calls verify runner target.

If unavailable:

```text
STOP
MODEL_TARGET_UNAVAILABLE
```

Required:

```text
model_target_fallback_count = 0
```

---

# 4. M12T transport conclusion is frozen

M12T classified:

```text
transport_root_cause =
TRANSIENT_WEBSOCKET_OR_SERVICE_DEGRADATION_LIKELY

runtime_change_required =
false
```

New M12T runtime observations:

```text
context-01:
321.698460 seconds

context-02:
331.906627 seconds

timeout count = 0
capacity failure = 0
orphan = 0
CLI internal retry events = 0
wrapper retry = 0
```

This returned near the earlier M12E Astra latency.

Therefore M12U must freeze:

```text
timeout = 1800 seconds

wrapper auto-retry = 0

subjects per context = 4

MODEL_CONTEXT_COUPLED
```

No transport changes in M12U.

If a new timeout occurs during M12U:

```text
stop the generation
next_scope = ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW
```

Do not stretch the watchdog inside the generation.

---

# 5. M12T semantic stop — exact state

The M12T generation completed:

```text
run-1/context-01 = semantic PASS
run-1/context-02 = transport/schema PASS, semantic FAIL
```

Total:

```text
model calls = 2
subject outputs = 8
schema PASS = 8 / 8
```

No further contexts were started.

Formal stability:

```text
NOT_MEASURED
```

The two blockers were:

```text
M12T_EXCLUSION_FALSE_REJECT

M12T_LEVERAGE_BUCKET_INCONSISTENCY
```

Do not infer repeated stability from the single repetition.

---

# 6. Solved financial architecture remains frozen

Across completed M12T outputs:

```text
selected financial refs = 15
used financial refs = 15

material financial anchor grounding failures = 0

working-capital grounding failures = 0

narrative substitution failures = 0

invalid financial refs = 0

price/technical/supply Directional violations = 0

QTD/YTD false reject = 0
QTD/YTD false accept = 0

partial PPE called FCF = 0

prior-year-end called YoY = 0

partial debt called total debt = 0

normalized earnings claims = 0

actual financial-sector industrial misuse count = 0

AI imperative primary action = 0
```

M12U must NOT reopen:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

materiality-scoped WC grounding

QTD/YTD Korean validator

FCF / YoY / debt completeness / normalized earnings validators
```

except the explicit-exclusion classification logic described below.

---

# 7. Issue A — exact FIC-FIN-08 false reject

Preserved GPT-6 Astra text:

```text
"보험사에 맞춰 보험영업 규율과 규제자본을 평가한다.
일반 사업회사의 부채·운전자본 틀은 적용 대상이 아니다."
```

Validator produced:

```text
financial_sector_generic_reasoning
```

Forensic classification in M12T:

```text
EXPLICIT_NON_APPLICABILITY_NOMINAL_COMPLEMENT_NOT_RECOGNIZED
```

Actual industrial-framework misuse:

```text
false
```

The candidate did not:

```text
calculate industrial net debt
use industrial WC as a decision anchor
select generic industrial financial refs
```

It explicitly excluded the framework.

This is a validator false reject.

---

# 8. Issue A repair target

Extend the existing assertion/exclusion classifier generically.

Current valid direct exclusion forms remain supported:

```text
적용하지 않는다
사용하지 않는다
평가하지 않는다
해당하지 않는다
```

M12U must also correctly recognize bounded nominal-complement non-applicability forms such as:

```text
적용 대상이 아니다

평가 대상이 아니다

사용 대상이 아니다

해당 기준의 적용 대상이 아니다

일반 영업기업 기준의 대상이 아니다
```

and supported English equivalents such as:

```text
is not applicable

does not apply

is not an applicable framework

is not the relevant framework
```

Do NOT implement a sentence whitelist.

Do NOT special-case insurance/FIC-FIN-08.

---

# 9. Exclusion assertion polarity

The validator must distinguish:

```text
ASSERTION_OR_APPLICATION

EXPLICIT_EXCLUSION

AMBIGUOUS_OR_CONTRADICTORY
```

A term like:

```text
순부채
운전자본
```

does not itself establish application.

Required examples:

## PASS — exclusion

```text
"보험사에는 일반 기업의 순부채 틀이 적용 대상이 아니다."

"운전자본 기준은 이 업종의 핵심 평가틀이 아니다."
```

when no actual use occurs elsewhere.

## FAIL — application

```text
"보험사의 순부채가 높아 SELL 근거다."
```

## FAIL — contradiction

```text
"순부채 틀은 적용 대상이 아니지만
순부채가 높아 부정 판단을 강화한다."
```

## FAIL — unsupported material anchor

Even if an exclusion sentence exists elsewhere,
a candidate that uses an unsupported industrial metric in:

```text
material_directional_anchor_basis
core_investment_judgment
sell_drivers
```

must still fail.

---

# 10. Issue A deterministic fixtures

Before any model call add at least:

### Positive

```text
적용하지 않는다
적용 대상이 아니다
평가 대상이 아니다
is not applicable
does not apply
```

in genuine non-application context.

### Negative

```text
actual industrial net-debt assertion
actual industrial WC assertion
mixed exclusion + later actual use
double-negative/ambiguous wording
exclusion in an unrelated clause
unsupported material anchor despite exclusion elsewhere
```

Required:

```text
false reject = 0
false accept = 0
```

Offline replay of the preserved M12T FIC-FIN-08 row must pass
for the correct exclusion reason.

Do not rewrite the old raw output.

---

# 11. Issue B — FIC-FIN-05 exact evidence

Frozen FIC-FIN-05 source packet includes:

```text
E01:
Current operating profit is positive and broadly stable.

E03:
A high complete debt balance and thin cash buffer reduce resilience.

E05:
typed complete interest-bearing debt total

E06:
typed cash and cash equivalents

E07:
"Expectations do not appear to allow for a prolonged refinancing burden."

E08:
"Refinancing terms and maturity concentration are not supplied."

E09:
The business remains profitable,
but balance-sheet resilience constrains optionality.
```

M12F froze the generic leverage target as:

```text
HOLD 4.5:5.5 SELL_LEAN
```

for:

```text
high complete debt
+
thin cash
+
stable operating profit
+
refinancing/maturity severity unresolved
```

M12T GPT-6 Astra instead produced:

```text
SELL 4.0:6.0

business thesis change = UNCHANGED

new buyer = AVOID

holder = REDUCE
```

and explicitly used E07 as a separate negative driver.

---

# 12. Issue B is NOT a fabricated-evidence problem

M12T FIC-FIN-05 cited:

```text
E05 complete debt
E06 cash
E07 market expectation
```

The market-expectation evidence is actually supplied.

Therefore the question is NOT:

```text
Did the model hallucinate a second negative fact?
```

It did not.

The question is:

```text
Is E07 economically independent enough
from the same unresolved refinancing-risk premise
to satisfy the independent-corroboration requirement
for crossing from 5.5 SELL_LEAN to minimum SELL 6.0?
```

This is a contract question.

---

# 13. Market-expectation independence contract — required review

Before implementation classify E07 under one of:

```text
INDEPENDENT_MARKET_EXPECTATION_AXIS

CONDITIONAL_ON_SAME_UNRESOLVED_RISK

PARTIALLY_INDEPENDENT_BUT_NOT_MINIMUM_DIRECTION_SUFFICIENT

AMBIGUOUS_CONTRACT

OTHER
```

The decision must be generic,
not FIC-FIN-05-specific.

Evaluate:

```text
What underlying fact makes the expectation elevated/misaligned?

Is that underlying downside itself confirmed or still Unknown?

Does market expectation add a separate investment-return asymmetry?

Or is it merely a conditional consequence of the same unconfirmed refinancing burden?

Is valuation/price evidence supplied?

Can market expectation independently support direction without safe valuation?
```

No model calls for this review.

---

# 14. Generic economic-independence principle

Freeze a generic distinction:

```text
source-category independence
!=
economic independence
```

Two evidence items from different categories:

```text
FINANCIAL_RESILIENCE
MARKET_EXPECTATIONS
```

do not automatically count as independent corroboration
if both depend on the same unresolved underlying premise.

Likewise,
same-source-lineage items are not automatically non-independent
if they establish genuinely different economic facts.

The test is:

```text
Does the second evidence axis add a distinct, sufficiently established
economic proposition relevant to the investment conclusion?
```

No evidence-count rule.

---

# 15. Conditional expectation rule — candidate design

M12U must review and either adopt or reject the following generic rule:

```text
When a market-expectation downside is conditional on an underlying
business/financing risk whose severity or persistence is still materially unresolved,
the expectation evidence does not automatically provide independent corroboration
for a stronger Directional bucket.

It may increase downside asymmetry / new-buyer caution,
but the core balance crosses to the stronger bucket only if:
(a) the underlying adverse condition is sufficiently established,
or
(b) the expectation evidence itself establishes a distinct current pricing/expectation risk
under the frozen market-expectation contract.
```

This is not a predetermined outcome.

The review must decide whether this fits the current Thesis Monitor philosophy.

---

# 16. Independent expectation rule — candidate design

Also review the opposite legitimate case:

```text
A confirmed negative fundamental condition exists,
and market expectations remain clearly elevated / do not price that confirmed condition.
```

In that case market expectation may be a genuinely independent investment-return axis.

A stronger negative directional bucket may be supported.

Required positive-control pattern:

```text
confirmed financing stress
+
elevated expectations that assume benign refinancing
```

No fixed rule that market expectation always counts or never counts.

---

# 17. Valuation boundary

Market expectations and valuation are related but distinct.

M12U must preserve:

```text
no safe valuation multiple supplied
```

as a limitation.

Do not infer:

```text
stock is expensive
```

solely because:

```text
expectations do not allow for a downside scenario.
```

Market expectation can express:

```text
priced-in assumptions / surprise asymmetry
```

without a numeric valuation.

But if the stronger bucket requires actual current valuation evidence
under the current contract,
state that explicitly.

Do not invent multiples.

---

# 18. Business-thesis delta separation

FIC-FIN-05 current frozen case contains:

```text
high debt / thin cash as current absolute condition

no explicit baseline deterioration

business thesis change = UNCHANGED
```

Preserve the M12F finding:

```text
CURRENT_ABSOLUTE_CONDITION_WITHOUT_EXPLICIT_BASELINE_DETERIORATION
```

M12U must not force:

```text
WEAKENED
```

merely because the absolute condition is negative.

Absolute direction and Daily/business delta remain separate.

---

# 19. New-buyer and holder stance — do not pre-repair

FIC-FIN-05 M12T output used:

```text
new buyer AVOID
holder REDUCE
```

The new-buyer/holder contracts remain separate secondary calibration fields.

M12U must not globally change them in the semantic repair.

Measure them in the full new canary.

If core balance stabilizes but stance variance remains:

```text
fresh_real_proof_readiness = NOT_READY
```

and choose a separate stance repair.

---

# 20. Leverage-boundary outcome — must be frozen before canary

After the offline review, freeze one generic result:

```text
A. LEV_EXPECTATION_NOT_INDEPENDENT_HOLD_5_5

B. LEV_EXPECTATION_INDEPENDENT_MINIMUM_SELL_6_0

C. LEV_EXPECTATION_CONTEXT_DEPENDENT_WITH_EXPLICIT_RULE

D. CONTRACT_REQUIRES_SEPARATE_REDESIGN
```

If A/B/C:

```text
freeze a generic rule
freeze LEV-01 expected bucket
continue deterministic validation
```

If D:

```text
STOP
NO_MODEL_CALLS
next_scope =
MARKET_EXPECTATION_DIRECTIONAL_INDEPENDENCE_ARCHITECTURE_REVIEW
```

Do not leave the canary target ambiguous.

---

# 21. Required leverage fixtures

At minimum:

## LEV-MKT-01

```text
high debt + thin cash
stable operating profit
refinancing severity Unknown
market expectation merely says benign refinancing is assumed
```

Freeze expected bucket under the chosen contract.

## LEV-MKT-02

```text
confirmed refinancing stress
+
market expectation still assumes benign financing
```

Test whether independent expectation corroboration may support minimum SELL.

## LEV-MKT-03

```text
high debt + thin cash
but no market-expectation evidence
```

Compare to LEV-MKT-01.

## LEV-MKT-04

```text
high debt + thin cash
expectations are already depressed / price in stress
```

Market expectation should not mechanically add negative corroboration.

## LEV-MKT-05

Positive symmetry:

```text
strong balance sheet
+
market expectations already very high
```

Strong resilience plus elevated expectations must not mechanically create BUY.

## LEV-MKT-06

```text
market-expectation statement depends on an entirely different confirmed risk axis
```

Test true economic independence.

These are ordinal-contract fixtures,
not numeric scoring fixtures.

---

# 22. No evidence-count calibration

Forbidden:

```text
debt = one negative point
cash = one negative point
market expectations = one negative point
two axes = 6.0
three axes = 6.5
```

Required:

```text
fixed_financial_score_rule_count = 0
evidence_count_bucket_rule_count = 0
```

Corroboration is economic and qualitative.

---

# 23. Existing M12E ordinal contract remains

Freeze:

```text
5.0 =
balanced / unresolved / too incomplete for lean

5.5 =
material issuer-level anchor
but sufficient corroboration/currentness/persistence/valuation/critical KPI support missing

6.0 =
minimum directional conclusion
with material anchor + sufficiently current/independent corroboration

6.5+ =
stronger persistence/quality/visibility/valuation support beyond minimum direction
```

Threshold:

```text
6.0
```

does not change.

Increment:

```text
0.5
```

does not change.

Tie-break:

```text
when adjacent buckets both reasonably fit,
choose the less-directional bucket toward 5.0
```

does not change.

---

# 24. Prompt change boundary

Issue A should be validator-only.

For Issue B:

If the current Directional calibration text does not explicitly encode
the frozen expectation-independence rule,
one bounded generic clarification may be added.

Allowed prompt/calibration change:

```text
market-expectation corroboration counts as independent only under the
newly frozen economic-independence rule
```

No other prompt changes.

Do not modify:

```text
QTD/YTD guidance
WC grounding
financial grounding
sector routing
source-sufficiency
price/supply exclusion
```

Produce line-by-line diff.

---

# 25. Financial-sector validator repair boundary

Only change:

```text
explicit exclusion / non-applicability claim classification
```

Do not weaken:

```text
actual financial-sector industrial-framework misuse detection
```

Required:

```text
actual true misuse still rejected
```

No ticker/case branches.

---

# 26. Preserve all solved contracts

Required unchanged:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

financial-context selected-only projection

materiality-scoped working-capital grounding

QTD/YTD plain-Korean validator

FCF label validator

prior-year-end vs YoY validator

debt completeness validator

normalized earnings validator

source sufficiency

Daily Delta

Price-Timing ownership

renderer ownership
```

Required change counters:

```text
financial_context_selection_change_count = 0

first_class_projection_change_count = 0

working_capital_validator_semantic_change_count = 0

qtd_ytd_validator_semantic_change_count = 0

non_exclusion_financial_validator_change_count = 0
```

---

# 27. Runtime freeze

M12T showed transport returned to normal latency.

Keep:

```text
model = gpt-6-astra

reasoning = xhigh

runtime mode = MODEL_CONTEXT_COUPLED

subjects per context = 4

timeout = 1800

single authoritative watchdog = true

wrapper auto-retry = 0

batch split = 0
```

No runtime repair in M12U.

---

# 28. Hosted CI portability remains separate P1

M12T hosted CI:

```text
3174 passed
5 failed
```

Failures remain historical git-object / local-artifact portability issues.

M12U should not broaden scope to fix all portability failures.

However:

```text
new M12U tests must be hosted-CI portable
new M12U failure count introduced = 0
```

Preserve handoff:

```text
HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR
```

Do not claim hosted CI PASS unless actually green.

---

# 29. Phase A offline forensic gate

Before implementation freeze:

```text
A. exclusion root cause =
EXPLICIT_NON_APPLICABILITY_NOMINAL_COMPLEMENT_NOT_RECOGNIZED

B. market-expectation leverage independence classification

C. final generic FIC-FIN-05 target bucket

D. whether a Directional calibration wording change is required
```

No implementation before these artifacts exist.

---

# 30. Phase B deterministic implementation gate

Before model calls require:

```text
authoring model = gpt-6-astra / xhigh

latest result integrity PASS

FIC-FIN-08 old row reproduced as false reject

new exclusion classifier PASSes old row for correct reason

exclusion positive fixtures PASS

exclusion negative/mixed fixtures rejected

market-expectation independence contract frozen

LEV-MKT fixtures PASS

FIC-FIN-05 target bucket explicitly frozen

threshold unchanged

increment unchanged

HOLD lean unchanged

tie-break unchanged

no scorecard

first-class financial architecture unchanged

all unrelated financial validators unchanged

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer unchanged

focused pytest PASS

full local pytest PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

If any fails:

```text
STOP
NO_MODEL_CALLS
```

---

# 31. New full GPT-6 Astra generation

Only after Phase B passes.

Create a NEW generation ID.

Use the exact frozen 8 cases:

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

Do not change source facts or narrative evidence
merely to make the target easier.

Do not continue M12T repetition 1.

Start from:

```text
run-1/context-01
```

---

# 32. Full canary topology

Run:

```text
8 subjects
2 shared contexts
4 subjects/context
3 repetitions
```

Total intended:

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

No real issuers.

No judge calls.

---

# 33. Whole-generation stop rule

If any context:

```text
times out
transport fails
hard semantic validation fails
target calibration contract fails
```

then:

```text
stop immediately

preserve emitted artifacts

do not selectively continue later contexts

do not wrapper-retry

do not increase timeout
```

Any future rerun must use a NEW generation.

---

# 34. Hard semantic gates

Across completed rows require zero:

```text
invalid financial evidence refs

material financial grounding failures

WC grounding failures

narrative substitution failures

price/technical/supply Directional refs

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

true financial-sector industrial-framework misuse

explicit-exclusion false rejects

missing optional evidence treated as bearish

fixed financial score behavior

QTD/YTD false reject

QTD/YTD false accept

AI imperative primary action
```

---

# 35. FIC-FIN-08 hard target

All three repetitions must:

```text
use insurance/financial-sector valid framework

not apply industrial net-debt/WC logic

allow explicit wording equivalent to:
"일반 사업회사의 부채·운전자본 틀은 적용 대상이 아니다"

without false reject
```

Required:

```text
explicit_exclusion_false_reject_count = 0

financial_sector_true_misuse_count = 0
```

---

# 36. FIC-FIN-05 hard target

All three repetitions must be audited against the newly frozen M12U generic expectation/leverage contract.

Required:

```text
same expected balance bucket across all 3

target bucket unique count = 1

target bucket contract violation count = 0
```

Do NOT hard-code:

```text
HOLD 5.5
```

or:

```text
SELL 6.0
```

inside the validator until the offline M12U contract review has frozen the generic answer.

The canary validator must compare against that frozen contract artifact.

No old Sol label target.

---

# 37. Existing M12E core calibration targets remain

Unless M12U's market-expectation clarification generically changes their contract,
preserve:

```text
FIC-FIN-01:
BUY 6.0:4.0
when stronger 6.5 support remains unresolved

FIC-FIN-02:
HOLD 4.5:5.5 SELL_LEAN
for shared-lineage cash-conversion divergence
with material causal/reversibility Unknown

FIC-FIN-04:
HOLD 5.0:5.0 NEUTRAL
for flat operations + non-operating boost alone
```

Any cross-case effect from the expectation-independence clarification
must be explicitly audited.

Do not silently shift unrelated cases.

---

# 38. Core balance stability

If all 6 contexts complete:

Required:

```text
FIC-FIN-01 balance unique count = 1

FIC-FIN-02 balance unique count = 1

FIC-FIN-04 balance unique count = 1

FIC-FIN-05 balance unique count = 1
```

All targeted buckets must be contract-consistent.

Do not accept:

```text
stable but contract-inconsistent
```

---

# 39. Formal stability

Run the unchanged formal stability classifier.

Report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

No majority vote.

No balance averaging.

No classifier change.

Required:

```text
opposite_direction_reversal_count = 0
```

---

# 40. Stance variance

Measure:

```text
fundamental_new_buyer

fundamental_holder
```

for all 8 × 3 outputs.

Do not globally repair stance semantics in M12U.

If core balance is fully stable but stance variance remains:

```text
fresh_real_proof_readiness = NOT_READY
```

Choose the smallest next stance repair.

Default sequence if both remain:

```text
new-buyer stance
then holder stance
```

unless evidence shows otherwise.

---

# 41. Business-thesis delta audit

For FIC-FIN-05 specifically report:

```text
business_thesis_change
```

across all 3 repetitions.

Given the frozen case contains no explicit baseline deterioration,
`UNCHANGED` may be semantically valid even if absolute direction is negative.

Do not require:

```text
WEAKENED
```

without actual delta evidence.

If repeated outputs fluctuate solely on delta status,
classify that as a separate lifecycle/thesis-change semantics issue.

Do not let it alter the absolute bucket target.

---

# 42. Runtime audit

Record each of 6 calls:

```text
elapsed seconds

prompt bytes

output bytes

CLI internal retry count

timeout

return code

runtime namespace

working directory

session ID
```

Require unique runtime identities.

Report:

```text
median latency

max latency

CLI retry events

retry-success events
```

If a timeout recurs:

```text
stop
next_scope = ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW
```

---

# 43. Cross-model and cross-generation comparison

Produce two separate tables.

## Cross-model

```text
GPT-5.6 Sol historical
vs
GPT-6 Astra
```

Label:

```text
CROSS_MODEL_DESCRIPTIVE_ONLY
```

No improvement rate.

## Same-model Astra

Compare:

```text
M12E
M12F
M12T
M12U
```

only where:

```text
input case
model
reasoning
relevant contract
```

are comparable.

If contract changed,
label:

```text
CONTRACT_CHANGED_NOT_DIRECT_REGRESSION
```

---

# 44. Message specificity advisory

If full canary completes,
run the existing advisory.

Measure:

```text
typed financial anchor specificity

period specificity

case-specific checkpoints

generic substantive repetition

renderer-introduced repetition
```

Do not change copy in M12U solely for advisory quality.

---

# 45. No real issuer exposure

Required:

```text
model_calls_real = 0

real_issuer_model_exposure_count = 0
```

Fresh real proof remains later.

---

# 46. Production side-effect firewall

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

Observe the approved 8 paused schedule paths at start/end.

---

# 47. Required artifacts — provenance / integrity

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12u-scope-freeze

04-model-target-contract

05-authoring-model-provenance

06-runner-model-provenance

07-m12t-transport-recovery-freeze
```

---

# 48. Required artifacts — financial-sector exclusion

Produce:

```text
08-fic-fin-08-false-reject-reproduction

09-nominal-non-applicability-root-cause

10-exclusion-assertion-polarity-contract

11-exclusion-validator-before-after

12-exclusion-positive-fixtures

13-exclusion-negative-fixtures

14-exclusion-mixed-contradiction-control

15-fic-fin-08-offline-regression
```

---

# 49. Required artifacts — market expectation / leverage

Produce:

```text
16-fic-fin-05-m12t-forensic

17-market-expectation-independence-question

18-economic-independence-contract

19-conditional-expectation-corroboration-contract

20-independent-expectation-corroboration-contract

21-valuation-expectation-boundary

22-fic-fin-05-business-delta-separation

23-lev-mkt-01

24-lev-mkt-02

25-lev-mkt-03

26-lev-mkt-04

27-lev-mkt-05-positive-symmetry

28-lev-mkt-06-independent-risk-axis

29-market-expectation-leverage-root-cause

30-frozen-fic-fin-05-target-contract
```

---

# 50. Required freeze/no-change artifacts

Produce:

```text
31-threshold-increment-lean-tiebreak-freeze-proof

32-first-class-financial-evidence-freeze-proof

33-financial-selector-freeze-proof

34-working-capital-validator-freeze-proof

35-qtd-ytd-validator-freeze-proof

36-other-financial-validator-freeze-proof

37-output-schema-freeze-proof

38-price-timing-no-change-proof

39-renderer-ownership-no-change-proof

40-source-sufficiency-no-change-proof

41-daily-delta-no-change-proof
```

---

# 51. Required deterministic validation artifacts

Produce:

```text
42-focused-test-results

43-full-local-test-results

44-ruff-and-diff-results

45-hosted-ci-portability-observation

46-model-call-gate
```

No new hosted-CI portability regressions.

Do not claim hosted CI PASS if historical failures remain.

---

# 52. Required full-canary artifacts

If deterministic gate passes:

```text
47-fictional-canary-generation-manifest

48-fictional-canary-source-lock

49-run-1-context-01

50-run-1-context-02

51-run-2-context-01

52-run-2-context-02

53-run-3-context-01

54-run-3-context-02

55-full-fictional-semantic-audit

56-full-fictional-exclusion-audit

57-full-fictional-market-expectation-leverage-audit

58-full-fictional-grounding-audit

59-full-fictional-business-delta-audit

60-full-fictional-formal-stability

61-full-fictional-core-only-stability

62-full-fictional-stance-variance

63-full-fictional-runtime-latency

64-cross-model-descriptive-table

65-same-model-astra-generation-comparison

66-full-fictional-message-specificity-advisory

67-runtime-observations
```

Preserve for every attempted context:

```text
prompt
schema
raw output
receipt
transport log
run document
```

---

# 53. Required completion artifacts

Produce:

```text
68-exclusion-validator-success-decision

69-market-expectation-leverage-contract-success-decision

70-core-balance-stability-decision

71-business-delta-followup-decision

72-new-buyer-stance-followup-decision

73-holder-stance-followup-decision

74-fresh-real-proof-readiness-decision

75-hosted-ci-portability-handoff

76-production-no-change

77-schedule-pause-observation

78-master-workflow-update

79-program-completion
```

---

# 54. Deterministic acceptance criteria

Before model calls require:

```text
authoring model = gpt-6-astra / xhigh

latest ZIP integrity PASS

M12T transport recovery frozen

FIC-FIN-08 false reject reproduced

"적용 대상이 아니다" explicit non-applicability recognized generically

actual financial-sector industrial misuse still rejected

false exclusion accept = 0

market-expectation economic-independence contract frozen

FIC-FIN-05 target bucket frozen generically

LEV-MKT fixtures PASS

threshold unchanged

increment unchanged

HOLD lean unchanged

tie-break unchanged

no fixed scorecard

first-class financial architecture unchanged

unrelated financial validators unchanged

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer unchanged

focused/full local tests PASS

ruff PASS

git diff --check PASS
```

---

# 55. Full-canary acceptance criteria

If new generation runs:

```text
6 / 6 contexts return successfully

24 / 24 rows schema PASS

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0

hard financial semantic violations = 0

explicit exclusion false reject = 0

financial-sector true misuse = 0

grounding failures = 0

QTD/YTD false reject = 0

QTD/YTD false accept = 0

price/technical/supply violations = 0

AI imperative primary action = 0

FIC-FIN-01 balance unique count = 1

FIC-FIN-02 balance unique count = 1

FIC-FIN-04 balance unique count = 1

FIC-FIN-05 balance unique count = 1

FIC-FIN-05 target bucket contract violations = 0

all targeted core buckets are contract-consistent

opposite-direction reversal = 0
```

Formal stability must be measured.

---

# 56. Fresh-real readiness

Set:

```text
fresh_real_proof_readiness = READY
```

only if:

```text
full 6-call Astra generation completes

financial hard semantics PASS

exclusion validator PASS

FIC-FIN-05 expectation/leverage contract PASS

core balance direction stable

formal stability has no unresolved material stance/delta ambiguity

no transport blocker

no real issuer exposure
```

Then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT6_ASTRA_XHIGH
```

Do not start it inside M12U.

If core balance is stable but stance/delta ambiguity remains,
select the smallest bounded follow-up first.

---

# 57. Failure handling

## A. Explicit-exclusion false reject persists

```text
next_scope =
BOUNDED_FINANCIAL_EXCLUSION_ASSERTION_SCOPE_REPAIR_V2
```

## B. FIC-FIN-05 target remains unstable or contract-inconsistent

```text
next_scope =
BOUNDED_MARKET_EXPECTATION_LEVERAGE_CALIBRATION_REPAIR_GPT6_ASTRA
```

## C. Market-expectation independence cannot be frozen safely

```text
next_scope =
MARKET_EXPECTATION_DIRECTIONAL_INDEPENDENCE_ARCHITECTURE_REVIEW
```

No model calls.

## D. Core stable but new-buyer stance ambiguous

```text
next_scope =
BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA
```

## E. Core stable but holder stance ambiguous

```text
next_scope =
BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA
```

## F. Timeout recurs

```text
next_scope =
ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW
```

No watchdog increase in this task.

---

# 58. Production readiness

Even if M12U passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real GPT-6 Astra generalization proof

production integration review

explicit user authorization
```

Existing monitoring remains paused.

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

m12t_status
m12u_status

implementation_model_target
implementation_reasoning_effort
investment_judgment_model_target
investment_judgment_reasoning_effort

authoring_model_target_match
runner_model_target_match
model_target_fallback_count

transport_root_cause_frozen
runtime_change_count
timeout_seconds
timeout_change_count
wrapper_retry_change_count

financial_exclusion_root_cause
financial_exclusion_repair_status
explicit_exclusion_false_reject_count
financial_sector_true_misuse_count

market_expectation_independence_classification
market_expectation_leverage_contract_status
fic_fin_05_target_direction
fic_fin_05_target_buy
fic_fin_05_target_sell
fic_fin_05_target_lean

business_delta_contract_change_count
new_buyer_contract_change_count
holder_contract_change_count

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
non_exclusion_financial_validator_change_count

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
cli_internal_retry_event_count
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

fic_fin_05_target_bucket_contract_violation_count

formal_stable_count
formal_boundary_uncertainty_count
formal_unstable_count
opposite_direction_reversal_count

core_only_stable_count
core_only_unstable_count

business_delta_variance_subject_count
new_buyer_stance_variance_subject_count
holder_stance_variance_subject_count

message_specificity_advisory_status

hosted_ci_status
hosted_ci_failure_count
new_hosted_ci_failure_count
hosted_ci_portability_backlog_count

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

Anything not actually measured:

```text
NOT_MEASURED
```

---

# 60. Artifact integrity

Freeze:

```text
program completion
master workflow
all deterministic reports
all attempted model-call artifacts
```

before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

---

# 61. Final task principle

M12T answered the runtime question:

```text
the prior Astra timeout did not reproduce,
and the same workload returned near normal latency.
```

The next blockers are semantic but narrow:

```text
1. explicit non-applicability language
must not be mistaken for framework application.

2. market expectations are not automatically independent corroboration
just because they are a different evidence category.
Their economic independence from the underlying risk must be defined.
```

The correct M12U flow is:

```text
repair assertion-vs-exclusion scope generically

→ determine whether E07-like expectation evidence
   is economically independent or conditional on the same unresolved risk

→ freeze one generic 5.5/6.0 contract

→ preserve threshold/increment/tie-break

→ run one clean NEW GPT-6 Astra/xhigh
   8-subject × 3-repeat canary

→ measure full core + formal stability

→ only then decide readiness for the fresh real cohort
```

Not:

```text
whitelist "적용 대상이 아니다"
```

Not:

```text
count evidence categories
```

Not:

```text
force HOLD 5.5 just because M12F expected it
```

Not:

```text
force SELL 6.0 just because Astra emitted it once
```

Not:

```text
use old GPT-5.6 Sol labels as ground truth
```

Not:

```text
change the 6.0 threshold
```

Not:

```text
increase timeout
```

Not:

```text
run real issuers before full fictional stability is clean
```

And not:

```text
resume production monitoring
```

Resolve economic independence, not evidence-counting.
