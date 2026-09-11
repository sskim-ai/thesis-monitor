# Thesis Monitor — Boundary-Band Canary Policy + Financial-Framework Application Scope + Full Sol Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260910-boundary-band-canary-policy-and-financial-framework-application-scope-full-sol-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260910-boundary-band-canary-policy-financial-framework-application-scope-full-sol-canary-report.zip
```

Master-workflow phase:

```text
M12AA — GPT-5.6 Sol / xhigh
        A. Hard Semantic Failure vs Calibration Observation Separation
        B. FIC-FIN-05 Boundary-Band Canary Contract
        C. Financial-Framework Application/Exclusion Scope Repair
        D. Full 8 × 3 Fictional Financial Canary
```

This task begins after M12Z.

The user has explicitly rejected the assumption that FIC-FIN-05 must
mechanically converge on one exact point:

```text
BUY 4.0 / SELL 6.0
```

for the current frozen leverage fixture.

The user-approved methodological change is:

```text
FIC-FIN-05 is a boundary case.

HOLD 4.5:5.5 SELL_LEAN
and
SELL 4.0:6.0

are both semantically defensible outcomes
under the supplied evidence.

The purpose of the repeated canary is to measure
which side the model consistently prefers,
or whether the case is genuinely boundary-uncertain.
```

M12AA must also fix the broader harness problem:

```text
an adjacent calibration result must not be treated
as a hard semantic failure that stops the whole generation
before repetitions can be measured.
```

The full 6-call / 24-output fictional generation should now complete
unless there is a true runtime/schema/hard-semantic failure.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260910-business-delta-alias-resolution-balance-confidence-full-sol-canary-report.zip
```

Verified SHA-256:

```text
6c6c6c02dcc9b6b144af43c3903e328bbc185a6bf4a4edbf78932500bfdd0c39
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent inspection of the latest uploaded bundle found:

```text
ZIP entries = 193

latest result integrity = PASS
```

Use the bundle artifact index as authoritative
and independently recompute all indexed hashes/sizes.

Required:

```text
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

---

# 2. M12Z repository provenance

Reported:

```text
branch =
codex/20260910-business-delta-alias-resolution-m12z

base_sha =
89bee202be8a4ae2f0eac7ce2fdca1a095c7818e

work_instruction_commit =
55bb3e92e7f40455ff547340c7e876b36292e88b

implementation_commit =
ca63b25894b53f17c4b89f2ecb3dfff79227448c

report_commit =
e54d75eec5761f3e1616caceef950a96ed25920d
```

The exported program-completion file used:

```text
final_head_sha =
RESOLVED_FROM_GIT_AT_BUNDLE_EXPORT
```

Therefore at M12AA start record the actual repository HEAD directly.

Required:

```text
actual_branch
actual_head
working_tree_state
remote_branch_sha
```

If unexplained semantic drift exists:

```text
STOP
UNEXPLAINED_M12AA_BASELINE_DRIFT
```

---

# 3. Model/runtime target remains frozen

Proof-critical model:

```text
gpt-5.6-sol
```

Reasoning:

```text
xhigh
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

No Astra calls.

No fallback.

No timeout change.

No context-topology change.

No wrapper retry.

If runner does not attest:

```text
gpt-5.6-sol / xhigh
```

then:

```text
STOP
SOL_RUNNER_MODEL_TARGET_MISMATCH
```

---

# 4. M12Z runtime result proves context-02 is not a different/broken route

M12Z completed both first-repetition contexts successfully.

Program completion:

```text
model calls fictional = 2

model context success = 2

model context failure = 0

fictional output rows = 8

schema PASS = 8 / 8

timeout = 0

capacity failure = 0

orphan = 0

CLI internal retry = 0

wrapper retry = 0
```

Runtime summary:

```text
median elapsed ≈ 419.39 sec

max elapsed ≈ 507.66 sec
```

Therefore:

```text
context-02 is NOT failing because it uses a different model route.

The recurring stop is caused by the semantic/calibration validators
attached to the cases placed in context-02,
especially FIC-FIN-05 and FIC-FIN-08.
```

M12AA must not perform a runtime review.

---

# 5. M12Z business-delta alias repair — preserve

M12Z root cause:

```text
CANONICAL_REFS_COMPARED_TO_ALIAS_KEYED_CONTEXT
```

The new canary reported:

```text
business_delta_alias_resolution_failure_count = 0

delta_validator_false_reject_count = 0

delta_validator_false_accept_count = 0

delta_model_semantic_violation_count = 0

business_delta_contract_violation_count = 0

unsupported_absolute_state_to_delta_count = 0
```

Thus the alias/canonical normalization repair worked
on the completed 8-output sample.

Do NOT reopen it.

Required:

```text
business_delta_alias_resolution_semantic_change_count = 0
```

M12AA must preserve:

```text
model alias
→ per-ticker catalog
→ canonical evidence
→ comparison/delta semantics
```

---

# 6. M12Z positive stronger-bucket clarification — preserve

M12Z froze:

```text
primary root cause =
PERSISTENCE_LIMIT_PRIORITY_UNDERSPECIFIED

secondary =
BALANCE_CONFIDENCE_SEMANTIC_ENTANGLEMENT
```

and implemented one bounded clarification:

```text
directional_balance =
strength/balance of supplied directional evidence

directional_confidence =
epistemic confidence under missing data,
durability, valuation, or validation limits
```

It also clarified:

```text
future durability not yet proven
does not automatically cap the current balance

unless the supplied uncertainty directly challenges
the current improvement enough to make adjacent buckets
genuinely supportable.
```

FIC-FIN-01 target remained:

```text
BUY 6.5:3.5
```

M12AA does NOT redesign this contract.

However, an exact point miss in a future repetition
must be recorded as a calibration observation,
not used to stop the generation immediately.

---

# 7. M12Z FIC-FIN-05 actual output

M12Z first observation:

```text
overall direction =
HOLD

directional balance =
BUY 4.5 / SELL 5.5

HOLD lean =
SELL_LEAN

directional confidence =
MEDIUM

business thesis change =
UNCHANGED

new buyer =
WAIT

holder =
REVIEW
```

Key reasoning:

```text
"안정적인 수익성보다 재무 회복력 제약이 조금 더 무겁지만,
재조달 부담의 현실화가 확인되지 않아
부정 방향까지는 뒷받침되지 않는다."
```

Dominant evidence:

```text
large complete interest-bearing debt
+
thin cash buffer
```

Counterevidence:

```text
current operating profit remains positive and broadly stable
```

Unknown / severity limitation:

```text
maturity concentration not supplied

refinancing terms not supplied

safe current valuation not supplied
```

The model correctly kept:

```text
business_thesis_change = UNCHANGED
```

because no baseline deterioration is supplied.

This output is semantically coherent.

---

# 8. FIC-FIN-05 must no longer have one mandatory exact-point target

Previous M12Y/M12Z fixture target:

```text
SELL 4.0:6.0
```

is no longer a hard exact canary requirement.

M12AA freezes a semantic boundary band:

```text
FIC-FIN-05_ALLOWED_CORE_BAND = {
    HOLD 4.5:5.5 SELL_LEAN,
    SELL 4.0:6.0
}
```

Both represent:

```text
negative leverage/resilience evidence is material

positive/stable operating evidence remains real counterevidence

refinancing/maturity severity is not fully confirmed

the case sits at the HOLD/SELL threshold boundary
```

The repeated canary must measure
whether Sol consistently selects one side
or alternates between the two.

---

# 9. What FIC-FIN-05 still requires as HARD semantics

The boundary band does NOT weaken the economic contract.

Every FIC-FIN-05 output must preserve:

```text
1. high complete debt + thin cash
   are a real negative financial-resilience anchor

2. stable positive operating profit
   is real counterevidence

3. missing refinancing/maturity severity
   limits confidence/severity
   and is not itself bullish evidence

4. E07-like market expectation
   remains conditional on the same unresolved refinancing downside
   and is not automatically counted as an independent negative axis

5. business_thesis_change = UNCHANGED
   because the packet supplies current absolute weakness
   without explicit baseline deterioration

6. no invented debt-service/covenant/maturity facts

7. no price/technical/supply contamination
```

Violation of these can still be a hard semantic failure.

The exact 5.5 vs 6.0 placement is NOT a hard semantic failure.

---

# 10. FIC-FIN-05 allowed-band classification

For each repetition classify:

```text
IN_BAND_HOLD_SELL_LEAN
IN_BAND_MINIMUM_SELL
OUT_OF_BAND_MORE_POSITIVE
OUT_OF_BAND_MORE_NEGATIVE
SEMANTIC_CONTRACT_FAILURE
```

Examples:

```text
HOLD 4.5:5.5 SELL_LEAN
→ IN_BAND_HOLD_SELL_LEAN

SELL 4.0:6.0
→ IN_BAND_MINIMUM_SELL
```

A 6.5+ SELL without new supplied severity evidence:

```text
OUT_OF_BAND_MORE_NEGATIVE
```

A neutral or positive result that ignores the leverage anchor:

```text
OUT_OF_BAND_MORE_POSITIVE
```

But:

```text
OUT_OF_BAND
```

is a calibration observation,
not automatically an immediate-generation stop.

It fails the final calibration contract
but the remaining fictional repetitions should continue
unless a separate hard semantic failure exists.

---

# 11. Why the canary stop policy must change

The current canary goal is:

```text
measure repeated stability
```

But the historical harness repeatedly did:

```text
one adjacent target miss
→ hard failure
→ stop generation
→ only one repetition available
→ formal stability NOT_MEASURED
```

This is methodologically self-defeating.

A calibration canary cannot estimate repeated-run stability
if calibration variation itself stops the repetitions.

M12AA must separate:

```text
proof-safety hard failures
from
calibration observations
```

---

# 12. New canary outcome taxonomy

Every validation result must be assigned one of four top-level classes.

## A. RUNTIME_OR_SCHEMA_HARD_FAILURE

Examples:

```text
model timeout

capacity failure

process/orphan failure

schema parse failure

missing output

invalid runtime model/effort

invalid/unresolved evidence alias
```

Action:

```text
STOP GENERATION IMMEDIATELY
```

## B. OBJECTIVE_SEMANTIC_HARD_FAILURE

Examples:

```text
invalid financial evidence reference

price/technical/supply contamination of Directional Core

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

true financial-sector industrial-framework application

unsupported absolute state converted to business delta

missing optional evidence treated as bearish fact

actual QTD/YTD semantic collapse

narrative substitution where typed grounding is required

AI imperative primary action
```

Action:

```text
STOP GENERATION IMMEDIATELY
```

## C. CALIBRATION_OBSERVATION

Examples:

```text
6.0 vs 6.5 adjacent strength difference

5.5 HOLD lean vs 6.0 minimum direction

exact fixture point miss

new-buyer ATTRACTIVE vs WAIT

holder REVIEW vs REDUCE

directional confidence difference
```

Action:

```text
RECORD
CONTINUE GENERATION
```

unless a separate objective semantic failure exists.

## D. ADVISORY_QUALITY_OBSERVATION

Examples:

```text
generic wording repetition

message specificity

non-material presentation variance
```

Action:

```text
RECORD
CONTINUE
```

---

# 13. Exact target audit is no longer a first-failure gate

Existing exact/reference targets may remain useful.

For example:

```text
FIC-FIN-01 reference =
BUY 6.5:3.5

FIC-FIN-02 reference =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-04 reference =
HOLD 5.0:5.0 NEUTRAL
```

But a point deviation such as:

```text
FIC-FIN-01 6.0 instead of 6.5
```

must be:

```text
CALIBRATION_OBSERVATION
```

not:

```text
OBJECTIVE_SEMANTIC_HARD_FAILURE
```

provided the output still follows the same underlying economic direction
and hard semantic rules.

This allows the full 3-repetition sample to reveal:

```text
stable exact preference

adjacent boundary uncertainty

or true repeated instability.
```

Do not change the reference target after seeing the generation.

---

# 14. Opposite or economically contradictory direction

A calibration observation becomes an objective semantic failure
ONLY when the output contradicts a hard economic contract.

Examples:

```text
FIC-FIN-05 BUY
while material negative leverage anchor is acknowledged
and no stronger positive material anchor exists

FIC-FIN-04 BUY
solely because non-operating income improved
while operations are flat

FIC-FIN-07 SELL
solely because optional information is missing
```

Do not define contradiction only by distance from a numeric target.

Use the supplied economic contract.

---

# 15. Formal stability remains unchanged

The existing formal classifier must remain unchanged.

After the full generation completes, report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

No:

```text
majority vote
balance averaging
classifier weakening
```

The new stop policy changes:

```text
when the generation is allowed to continue
```

not:

```text
how final stability is classified.
```

---

# 16. FIC-FIN-05 formal interpretation

After three repetitions:

## Case A

```text
5.5
5.5
5.5
```

Interpretation:

```text
stable model preference for HOLD SELL_LEAN
within the allowed semantic band
```

## Case B

```text
6.0
6.0
6.0
```

Interpretation:

```text
stable model preference for minimum SELL
within the allowed semantic band
```

## Case C

```text
5.5
6.0
5.5
```

Interpretation:

```text
true HOLD/SELL boundary uncertainty
```

No hard semantic failure,
but:

```text
fresh real proof readiness remains NOT_READY
```

if this core direction boundary remains materially unstable.

Do not choose the majority output as the production answer.

---

# 17. FIC-FIN-05 exact-target fixture migration

Replace:

```text
fic_fin_05_frozen_target = 4.0 buy / 6.0 sell
```

with:

```text
fic_fin_05_allowed_band =
[
  {
    direction: HOLD,
    buy: 4.5,
    sell: 5.5,
    lean: SELL_LEAN
  },
  {
    direction: SELL,
    buy: 4.0,
    sell: 6.0
  }
]
```

This is:

```text
CANARY_EXPECTATION_CHANGE
```

not:

```text
PRODUCTION_DIRECTIONAL_SEMANTIC_CHANGE
```

Required:

```text
production_threshold_change_count = 0

production_increment_change_count = 0

production_tiebreak_change_count = 0
```

---

# 18. FIC-FIN-08 latest raw output

M12Z Sol output:

```text
overall direction =
HOLD 5.0:5.0 NEUTRAL

business thesis change =
UNCHANGED

new buyer =
WAIT

holder =
REVIEW
```

Sector interpretation:

```text
"보험사에는 산업회사식 순부채나 운전자본 틀 대신
인수 규율과 규제자본 틀이 적용된다."
```

Material Directional anchor basis:

```text
[]
```

The output actually used:

```text
underwriting economics

claims/loss volatility

regulatory capital
```

not industrial net debt.

Nevertheless M12Z exclusion audit reported:

```text
contrastive_exclusion_false_reject_count = 2
```

This is a validator false reject.

---

# 19. Stop adding phrase-by-phrase exclusion patches

The project has already encountered:

```text
적용하지 않는다

적용 대상이 아니다

순부채와 운전자본 대신 ...

순부채나 운전자본 대신 ...
```

Adding each Korean surface form individually
will not produce a robust financial-sector validator.

M12AA must move one level up:

```text
Did the candidate actually APPLY/ASSERT the industrial metric?

or

Did it merely MENTION it while explaining non-applicability?
```

The validator should operate on application role,
not bare token presence.

---

# 20. Financial metric/framework reference-role taxonomy

Introduce or formalize a bounded classification:

```text
ASSERTED_STATE

APPLIED_DECISION_FRAMEWORK

EXPLICIT_NON_APPLICATION

CONTRASTIVE_REPLACEMENT

CONTEXT_ONLY_MENTION

CONTRADICTORY_MIXED_USE

UNRESOLVED
```

For high-risk sector-inappropriate concepts such as:

```text
industrial net debt

generic operating working capital
```

only:

```text
ASSERTED_STATE
APPLIED_DECISION_FRAMEWORK
CONTRADICTORY_MIXED_USE
```

may trigger the corresponding hard misuse validator.

A genuine:

```text
EXPLICIT_NON_APPLICATION
CONTRASTIVE_REPLACEMENT
```

must not.

---

# 21. Use field role + evidence use, not text token alone

Application detection should inspect bounded evidence such as:

```text
field path

evidence refs attached to the claim

whether the metric appears in:
- material_directional_anchor_basis
- buy_drivers
- sell_drivers
- core_investment_judgment
- reevaluation conditions
- risk_context

whether a supplied typed financial ref for that metric is actually used

whether the sentence explicitly replaces/excludes the framework

whether another candidate field contradicts the exclusion
```

A mention inside:

```text
sector_interpretation
```

that says:

```text
industrial X is not the applicable framework;
sector-specific Y is
```

should normally be:

```text
CONTRASTIVE_REPLACEMENT
```

not application.

No general Korean NLP engine is required.

---

# 22. Net-debt claim validator scope

The net-debt completeness validator must not fire merely because:

```text
"순부채"
```

appears in a non-application sentence.

It should fire when the candidate actually asserts something equivalent to:

```text
net debt is high/low

net debt increased/decreased

net debt supports BUY/SELL

net debt is a material decision anchor
```

without valid complete net-debt evidence.

The same application-role result should be shared
with financial-sector generic-framework validation.

Avoid parallel lexical scanners reaching conflicting conclusions.

---

# 23. Financial-sector generic-framework scope

For a financial-sector issuer:

Hard FAIL:

```text
industrial net-debt/WC framework
is actually used as a business/investment decision framework.
```

PASS:

```text
the candidate explicitly says those industrial frameworks
are not the applicable evaluation framework
and instead uses sector-valid concepts.
```

For FIC-FIN-08:

```text
underwriting discipline
+
claims/loss economics
+
regulatory capital
```

are the intended framework.

---

# 24. Contradiction remains hard failure

Examples that must FAIL:

```text
"순부채 틀 대신 규제자본을 본다.
하지만 순부채가 높아서 SELL이다."

"운전자본은 적용하지 않는다."
+
sell_drivers actually cite/use industrial WC deterioration

sector_interpretation excludes industrial leverage
but material_directional_anchor_basis uses unsupported net debt
```

An exclusion sentence cannot immunize actual application elsewhere.

---

# 25. Application-role positive fixtures

Required PASS examples:

```text
"보험사에는 산업회사식 순부채나 운전자본 틀 대신
인수 규율과 규제자본 틀이 적용된다."

"산업회사식 순부채와 운전자본 틀 대신
언더라이팅과 규제자본을 본다."

"일반기업 순부채 틀은 적용 대상이 아니다."

"Use regulatory capital rather than industrial net debt."

"Industrial working capital is not the applicable framework."
```

All must have:

```text
no actual industrial metric use elsewhere.
```

---

# 26. Application-role negative fixtures

Required FAIL:

```text
unsupported net-debt magnitude assertion

industrial WC used as insurer SELL driver

explicit exclusion followed by actual metric application

unsupported industrial metric in material_directional_anchor_basis

net-debt claim citing unrelated sector-context evidence

ambiguous sentence where application cannot be safely resolved
and the metric is used materially
```

No false accept.

No false reject.

---

# 27. M12Z exact FIC-FIN-08 replay

After repair,
the exact preserved M12Z raw output must yield:

```text
reference role =
CONTRASTIVE_REPLACEMENT

net_debt_claim_without_complete_net_debt_evidence =
0

financial_sector_generic_reasoning =
0

actual industrial-framework misuse =
0
```

No raw-output rewrite.

---

# 28. Business-delta semantic contract remains hard

Unlike the 5.5-vs-6.0 calibration band,
business delta is a different semantic dimension.

For FIC-FIN-05:

```text
business_thesis_change = UNCHANGED
```

remains a hard fixture semantic requirement
because the packet provides no baseline deterioration.

A model output of:

```text
WEAKENED
```

based only on current high debt/thin cash
is not mere calibration variance.

It is:

```text
OBJECTIVE_SEMANTIC_HARD_FAILURE
```

unless it cites supplied change evidence that was not previously recognized.

---

# 29. Delta alias/canonical resolution regression

Preserve M12Z repair.

Before new model calls replay exact M12Z completed outputs.

Required:

```text
alias resolution failure = 0

false reject = 0

false accept = 0

unsupported absolute-state-to-delta = 0
```

Do not change the model-facing delta prompt.

---

# 30. Other hard financial semantics remain frozen

Preserve:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

selected-only financial projection

materiality-scoped working-capital grounding

QTD/YTD Korean period semantics

FCF label safety

prior-year-end vs YoY safety

debt completeness safety

normalized earnings safety

market-expectation economic-independence rule
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

# 31. Directional production calibration remains frozen

No production change to:

```text
BUY if buy >= 6.0

SELL if sell >= 6.0

otherwise HOLD

0.5 balance increments
```

HOLD lean:

```text
5.5:4.5 BUY_LEAN

5.0:5.0 NEUTRAL

4.5:5.5 SELL_LEAN
```

Tie-break:

```text
adjacent ambiguity → less directional bucket toward 5.0
```

The M12AA change is primarily:

```text
CANARY VALIDATION POLICY
```

not production scoring.

---

# 32. Canary hard-stop matrix

Create one authoritative matrix.

At minimum:

| Validation class | Example | Stop immediately? |
|---|---|---|
| Runtime | timeout | YES |
| Schema | invalid output schema | YES |
| Evidence identity | invalid alias/ref | YES |
| Accounting safety | partial PPE called FCF | YES |
| Security/basis safety | unsupported denominator/basis claim | YES |
| Direction ownership | price/technical/supply changes Core | YES |
| Business delta | absolute state falsely becomes change | YES |
| Sector application | actual industrial framework applied to insurer | YES |
| Exclusion mention | legitimate non-application wording | NO FAILURE |
| Exact balance target | 6.0 vs 6.5 | NO |
| FIC-FIN-05 band | 5.5 vs 6.0 | NO |
| New-buyer stance | WAIT vs AVOID/ATTRACTIVE | NO |
| Holder stance | REVIEW vs REDUCE/HOLDABLE | NO |
| Confidence | MEDIUM vs LOW/HIGH | NO |
| Message repetition | wording variance | NO |

The implementation must use this distinction consistently.

---

# 33. Calibration deviation does not equal semantic PASS

Do not overcorrect.

A `CALIBRATION_OBSERVATION` can still cause the FINAL proof to be:

```text
NOT_READY
```

For example:

```text
FIC-FIN-01:
6.5 / 6.0 / 6.5
```

may classify as:

```text
BOUNDARY_UNCERTAINTY
```

and block fresh real proof.

The difference is:

```text
we finish the 3 repetitions first
and measure the instability
instead of stopping after the first deviation.
```

---

# 34. Out-of-band calibration policy

If a case produces an ordinal result outside its expected point/band
but no objective semantic violation is found:

```text
record CALIBRATION_OUT_OF_BAND
continue generation
```

At final audit:

```text
target calibration contract = FAIL
```

if appropriate.

Do not silently treat out-of-band as acceptable.

This is observational continuation,
not target weakening.

---

# 35. Model-call continuation rule

Once the deterministic gate passes,
run the full new generation.

During the generation stop only for:

```text
RUNTIME_OR_SCHEMA_HARD_FAILURE

OBJECTIVE_SEMANTIC_HARD_FAILURE
```

Do NOT stop for:

```text
CALIBRATION_OBSERVATION

STANCE_OBSERVATION

CONFIDENCE_OBSERVATION

MESSAGE_ADVISORY
```

This is the central M12AA harness change.

---

# 36. Full Sol generation

Create a NEW generation.

Do not continue M12Z.

Do not reuse M12Z outputs in the formal sample.

Subjects remain:

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

---

# 37. Runtime hard gates

Require:

```text
6 / 6 contexts complete

24 / 24 outputs schema PASS

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0
```

CLI internal retries must be reported separately.

---

# 38. Hard semantic gates

Across all 24 outputs require zero:

```text
invalid evidence reference

material financial grounding failure

working-capital grounding failure

narrative substitution failure

price/technical/supply Directional contamination

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

true financial-sector industrial-framework application

legitimate exclusion false reject

unsupported absolute-state-to-business-delta

QTD/YTD true semantic violation

QTD/YTD false reject

QTD/YTD false accept

missing optional evidence treated as bearish fact

AI imperative primary action
```

---

# 39. Reference target/band audit after full generation

Audit:

## FIC-FIN-01

Reference:

```text
BUY 6.5:3.5
```

But exact-point deviation:

```text
CALIBRATION_OBSERVATION
```

during execution.

## FIC-FIN-02

Reference:

```text
HOLD 4.5:5.5 SELL_LEAN
```

Exact-point deviation:

```text
CALIBRATION_OBSERVATION
```

unless underlying economics are contradicted.

## FIC-FIN-04

Reference:

```text
HOLD 5.0:5.0 NEUTRAL
```

Exact-point deviation:

```text
CALIBRATION_OBSERVATION
```

unless the model uses non-operating support as an invalid fundamental anchor.

## FIC-FIN-05

Allowed band:

```text
HOLD 4.5:5.5 SELL_LEAN
OR
SELL 4.0:6.0
```

Both are semantically in-band.

---

# 40. FIC-FIN-05 final stability output

Report at least:

```text
repetition 1 result
repetition 2 result
repetition 3 result

in-band count

out-of-band count

unique core balance count

unique overall direction count

formal stability class
```

Also report:

```text
model stable preference =
HOLD_SELL_LEAN
MINIMUM_SELL
MIXED_BOUNDARY
OUT_OF_BAND
```

Do not majority-vote.

---

# 41. Formal stability

After all 6 calls complete,
run the unchanged formal classifier.

Required report:

```text
STABLE count

BOUNDARY_UNCERTAINTY count

UNSTABLE count

opposite-direction reversal count
```

No reclassification to make the proof pass.

---

# 42. Core-only stability

For all 8 subjects report:

```text
overall_direction values

directional_balance values

hold_lean values

unique counts
```

This must finally be measured
instead of remaining `NOT_MEASURED`.

---

# 43. Stance and confidence variance

Measure separately:

```text
fundamental_new_buyer

fundamental_holder

directional_confidence
```

Do not stop the generation because these differ.

At final readiness review,
determine whether remaining stance variance is materially unacceptable.

Possible follow-ups:

```text
BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL

BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL
```

Only if required after the full sample exists.

---

# 44. Business-delta full audit

For every output report:

```text
observed business_thesis_change

resolved supporting evidence aliases

canonical refs

supported change directions

unsupported absolute-state-to-delta count
```

FIC-FIN-05 requires:

```text
UNCHANGED
```

under the frozen source packet.

This remains semantic,
not calibration.

---

# 45. No prompt chasing for boundary points

M12AA must not add prompt lines saying:

```text
FIC-FIN-05 should be 5.5

FIC-FIN-05 should be 6.0

FIC-FIN-01 must be 6.5
```

The canary must observe the model under generic contracts.

Allowed model-facing prompt change:

```text
NONE by default
```

The main changes are:

```text
canary validator/stop policy

financial metric application-role validator
```

If a model-facing prompt change is claimed necessary:

```text
STOP
document the generic semantic defect separately
```

Do not mix it into M12AA without a clear deterministic root cause.

---

# 46. No target toggling after output

Hard rule:

```text
reference targets and FIC-FIN-05 allowed band
must be frozen BEFORE new model output exists.
```

After any new output:

```text
do not change the band

do not change exact reference targets

do not reinterpret a deviation into a PASS
```

Use the full sample for the next decision.

---

# 47. Deterministic fixtures — canary stop taxonomy

Create synthetic harness tests:

## STOP-01

```text
invalid evidence ref
→ immediate stop
```

## STOP-02

```text
partial PPE called FCF
→ immediate stop
```

## STOP-03

```text
actual insurer industrial net-debt application
→ immediate stop
```

## CONTINUE-01

```text
FIC-FIN-01-like 6.0 instead of reference 6.5
with valid economics
→ record calibration deviation
→ continue
```

## CONTINUE-02

```text
FIC-FIN-05 HOLD 5.5
→ in-band
→ continue
```

## CONTINUE-03

```text
FIC-FIN-05 SELL 6.0
→ in-band
→ continue
```

## CONTINUE-04

```text
new-buyer WAIT vs reference expectation
→ record stance variance
→ continue
```

## CONTINUE-05

```text
holder REVIEW vs REDUCE
→ record stance variance
→ continue
```

---

# 48. Deterministic fixtures — application scope

Create at minimum:

```text
APP-01:
"순부채나 운전자본 대신 인수 규율과 규제자본"
→ CONTRASTIVE_REPLACEMENT → PASS

APP-02:
"순부채와 운전자본 대신 ..."
→ CONTRASTIVE_REPLACEMENT → PASS

APP-03:
"순부채는 적용 대상이 아니다"
→ EXPLICIT_NON_APPLICATION → PASS

APP-04:
actual unsupported insurer net-debt assertion
→ ASSERTED_STATE → FAIL

APP-05:
actual insurer WC sell driver
→ APPLIED_DECISION_FRAMEWORK → FAIL

APP-06:
exclusion + later actual net-debt sell driver
→ CONTRADICTORY_MIXED_USE → FAIL

APP-07:
metric mentioned only in historical/context discussion,
not used as decision framework
→ CONTEXT_ONLY_MENTION → no misuse

APP-08:
ambiguous material use that cannot be resolved
→ fail closed / needs hard review
```

---

# 49. Preserve production source/lifecycle semantics

Required no change:

```text
source_sufficiency_semantic_change_count = 0

daily_delta_semantic_change_count = 0

monitoring_lifecycle_semantic_change_count = 0

warning_semantic_change_count = 0

Price-Timing semantic change count = 0

renderer substantive change count = 0
```

No source/provider work.

---

# 50. Hosted CI portability remains separate

Latest M12Z program completion reported:

```text
hosted_ci_status =
KNOWN_HISTORICAL_PORTABILITY_FAILURES_ONLY

hosted_ci_failure_count =
5

new_hosted_ci_failure_count =
0
```

M12AA must introduce:

```text
new hosted-CI failure count = 0
```

Do not broaden scope to historical portability cleanup.

Do not claim hosted CI PASS unless fully green.

---

# 51. Production side-effect firewall

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

Observe approved paused schedule paths at start/end.

Do not resume monitoring.

---

# 52. Phase A — required forensic/freeze artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12aa-scope-freeze

04-sol-runtime-freeze

05-m12z-stop-cause-reclassification

06-hard-semantic-vs-calibration-taxonomy

07-canary-stop-matrix

08-existing-target-gate-behavior-audit

09-fic-fin-05-boundary-band-contract

10-fic-fin-05-hard-semantic-contract

11-fic-fin-08-raw-output-forensic

12-financial-framework-reference-role-contract

13-net-debt-claim-application-scope-audit

14-financial-sector-framework-application-scope-audit
```

Freeze the band and taxonomy before implementation.

---

# 53. Phase B — required implementation artifacts

Produce:

```text
15-canary-stop-policy-before-after

16-calibration-observation-recording-contract

17-fic-fin-05-target-point-to-band-migration

18-reference-target-nonstop-contract

19-financial-framework-role-classifier-before-after

20-shared-application-scope-contract

21-net-debt-validator-before-after

22-financial-sector-validator-before-after

23-exclusion-contradiction-contract
```

No production threshold change.

---

# 54. Required deterministic fixture artifacts

Produce:

```text
24-stop-taxonomy-fixtures

25-continue-calibration-fixtures

26-fic-fin-05-band-fixtures

27-application-scope-positive-fixtures

28-application-scope-negative-fixtures

29-m12z-fic-fin-08-exact-replay

30-m12z-delta-alias-regression

31-fic-fin-05-delta-regression
```

---

# 55. Required freeze/no-change artifacts

Produce:

```text
32-directional-threshold-freeze

33-directional-increment-freeze

34-hold-lean-freeze

35-conservative-tiebreak-freeze

36-balance-confidence-contract-freeze

37-first-class-financial-evidence-freeze

38-working-capital-validator-freeze

39-qtd-ytd-validator-freeze

40-market-expectation-contract-freeze

41-business-delta-contract-freeze

42-source-sufficiency-no-change

43-daily-delta-no-change

44-price-timing-no-change

45-renderer-ownership-no-change

46-sol-runtime-no-change
```

---

# 56. Deterministic test gate

Before any new model calls require:

```text
latest ZIP integrity PASS

gpt-5.6-sol / xhigh runner target PASS

runtime freeze PASS

business-delta alias regression PASS

FIC-FIN-08 exact old output now PASS
for application-role reason

actual financial-sector misuse fixtures FAIL

net-debt assertion misuse fixtures FAIL

exclusion false reject = 0

exclusion false accept = 0

FIC-FIN-05 allowed band frozen

FIC-FIN-05 business delta target = UNCHANGED

hard semantic vs calibration taxonomy tests PASS

calibration deviations do NOT trigger generation stop

runtime/schema/objective semantic failures DO trigger stop

financial hard-safety regressions PASS

threshold/increment/lean/tie-break unchanged

no scorecard

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer unchanged

focused pytest PASS

full local pytest PASS

ruff PASS

git diff --check PASS

production firewall PASS
```

If any deterministic condition fails:

```text
STOP
NO_MODEL_CALLS
```

---

# 57. New full fictional generation

After deterministic PASS:

```text
create NEW generation

run all 6 planned contexts
unless runtime/schema/objective-semantic hard failure occurs
```

Do NOT stop because:

```text
FIC-FIN-01 returns 6.0 instead of 6.5

FIC-FIN-05 returns 5.5 instead of 6.0

new-buyer stance changes

holder stance changes

confidence changes
```

Those observations are the purpose of the repeated proof.

---

# 58. Model-call artifact preservation

For each of 6 contexts preserve:

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

Each context must have:

```text
unique invocation ID

unique runtime namespace

unique working directory

unique session identity
```

---

# 59. Full semantic audit after generation

After all 24 outputs:

Separate counts:

```text
runtime_hard_failure_count

schema_hard_failure_count

objective_semantic_hard_failure_count

calibration_observation_count

calibration_out_of_band_count

stance_observation_count

confidence_observation_count

message_advisory_count
```

Do NOT merge these into one:

```text
hard_financial_semantic_violation_count
```

without sub-classification.

The report must make it obvious
what would have stopped generation
and what was intentionally observed through completion.

---

# 60. Formal stability and calibration report

Required:

```text
formal STABLE count

formal BOUNDARY_UNCERTAINTY count

formal UNSTABLE count

opposite-direction reversal count
```

Plus per-subject:

```text
direction values

balance values

lean values

new-buyer stance values

holder stance values

confidence values

business-delta values
```

This is the first priority of M12AA.

---

# 61. Fresh-real readiness decision

Set:

```text
fresh_real_proof_readiness = READY
```

only if:

```text
6 / 6 Sol contexts complete

24 / 24 schema PASS

runtime hard failures = 0

objective semantic hard failures = 0

invalid evidence refs = 0

grounding failures = 0

financial-sector true misuse = 0

business-delta semantic violations = 0

formal UNSTABLE = 0

no unresolved material HOLD↔BUY/SELL threshold boundary
that would materially change new-buyer/holder meaning

no unresolved material stance instability

Sol runtime suitable for exposed real holdout

real issuer exposure = 0
```

Important:

```text
FIC-FIN-05 being consistently 5.5 OR consistently 6.0
can both be acceptable
if the hard semantic contract is satisfied.

FIC-FIN-05 alternating 5.5 ↔ 6.0
is boundary uncertainty and should keep real-proof readiness NOT_READY,
but it is NOT a hard semantic failure.
```

---

# 62. Next-scope logic

## A. Full canary completes and all core decisions are stable

If:

```text
hard semantics PASS
formal instability resolved
stance/delta acceptable
```

then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH
```

## B. FIC-FIN-05 alternates 5.5 ↔ 6.0

Set:

```text
next_scope =
LEVERAGE_HOLD_SELL_BOUNDARY_POLICY_REVIEW_GPT56_SOL
```

Use the complete three-repetition sample.

Do NOT majority-vote.

## C. FIC-FIN-01 alternates 6.0 ↔ 6.5

Set:

```text
next_scope =
POSITIVE_STRONGER_BUCKET_STABILITY_REVIEW_GPT56_SOL
```

Do not stop before collecting the full sample.

## D. Core stable but new-buyer stance varies

```text
next_scope =
BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL
```

## E. Core stable but holder stance varies

```text
next_scope =
BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL
```

## F. Financial-sector role validator still false-rejects legitimate exclusion

```text
next_scope =
FINANCIAL_FRAMEWORK_APPLICATION_SCOPE_ARCHITECTURE_REVIEW
```

Do not add another phrase whitelist.

## G. Sol runtime fails

```text
next_scope =
SOL_RUNTIME_REGRESSION_REVIEW
```

No Astra fallback.

---

# 63. Production readiness

Even if M12AA passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real GPT-5.6 Sol generalization proof

production integration review

explicit user authorization
```

Monitoring remains paused.

---

# 64. Required full-canary artifacts

If the model-call gate passes, produce:

```text
47-fictional-canary-generation-manifest

48-fictional-canary-source-lock

49-run-1-context-01

50-run-1-context-02

51-run-2-context-01

52-run-2-context-02

53-run-3-context-01

54-run-3-context-02

55-full-fictional-hard-semantic-audit

56-full-fictional-calibration-observation-audit

57-full-fictional-fic-fin-05-boundary-band-audit

58-full-fictional-financial-framework-role-audit

59-full-fictional-business-delta-audit

60-full-fictional-grounding-audit

61-full-fictional-formal-stability

62-full-fictional-core-only-stability

63-full-fictional-stance-confidence-variance

64-full-fictional-runtime-audit

65-full-fictional-message-specificity-advisory
```

---

# 65. Required completion artifacts

Produce:

```text
66-canary-stop-policy-success-decision

67-fic-fin-05-boundary-band-success-decision

68-financial-framework-application-scope-success-decision

69-business-delta-regression-success-decision

70-sol-full-canary-completion-decision

71-core-balance-stability-decision

72-new-buyer-stance-followup-decision

73-holder-stance-followup-decision

74-sol-runtime-real-holdout-suitability

75-fresh-real-proof-readiness-decision

76-hosted-ci-portability-handoff

77-astra-future-experiment-handoff

78-production-no-change

79-schedule-pause-observation

80-master-workflow-update

81-program-completion
```

---

# 66. Program-completion fields

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

m12z_status
m12aa_status

investment_judgment_model_target
investment_judgment_reasoning_effort
runner_model_target_match
model_target_fallback_count

canary_stop_policy_version
hard_failure_class_count
calibration_observation_class_count

calibration_deviation_stops_generation
stance_variance_stops_generation
confidence_variance_stops_generation

fic_fin_05_previous_exact_target
fic_fin_05_allowed_band
fic_fin_05_band_change_type

financial_framework_role_classifier_status
financial_framework_exclusion_false_reject_count
financial_framework_false_accept_count
financial_sector_true_misuse_count
net_debt_true_assertion_violation_count

business_delta_alias_resolution_status
business_delta_alias_resolution_failure_count
business_delta_false_reject_count
business_delta_false_accept_count
unsupported_absolute_state_to_delta_count

directional_prompt_change_count
directional_threshold_changed
directional_increment_changed
hold_lean_contract_changed
calibration_tiebreak_direction_changed

fixed_score_rule_count
evidence_count_bucket_rule_count

financial_context_selection_change_count
first_class_projection_change_count
working_capital_validator_semantic_change_count
qtd_ytd_validator_semantic_change_count
market_expectation_contract_change_count
business_delta_prompt_change_count

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

runtime_hard_failure_count
schema_hard_failure_count
objective_semantic_hard_failure_count

calibration_observation_count
calibration_out_of_band_count
stance_observation_count
confidence_observation_count

invalid_financial_reference_count
grounding_failure_count

fic_fin_01_directional_balance_values
fic_fin_02_directional_balance_values
fic_fin_04_directional_balance_values
fic_fin_05_directional_balance_values

fic_fin_05_in_band_hold_sell_lean_count
fic_fin_05_in_band_minimum_sell_count
fic_fin_05_out_of_band_count
fic_fin_05_stable_preference

formal_stable_count
formal_boundary_uncertainty_count
formal_unstable_count
opposite_direction_reversal_count

business_delta_variance_subject_count
new_buyer_stance_variance_subject_count
holder_stance_variance_subject_count
directional_confidence_variance_subject_count

runtime_median_elapsed_seconds
runtime_max_elapsed_seconds
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

Anything not measured:

```text
NOT_MEASURED
```

---

# 67. Artifact integrity

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

# 68. Final task principle

The repeated second-context stops are not evidence
that context-02 uses a different model route.

M12Z proved:

```text
both context-01 and context-02
completed normally under GPT-5.6 Sol / xhigh.
```

The real issue is methodological:

```text
the canary has been treating
adjacent calibration outcomes
as hard semantic failures,

so the experiment stops
before it can measure the repeated stability
it was created to measure.
```

FIC-FIN-05 is the clearest example.

Given:

```text
material leverage weakness

stable current operating profit

unconfirmed refinancing/maturity severity

no baseline deterioration
```

both:

```text
HOLD 4.5:5.5 SELL_LEAN
```

and:

```text
SELL 4.0:6.0
```

are defensible boundary outcomes.

Do not force the model to hit one arbitrary point.

Instead:

```text
freeze the economic semantics

→ permit the 5.5/6.0 boundary band

→ run all three repetitions

→ observe whether Sol consistently prefers one side
  or truly oscillates across HOLD/SELL

→ preserve hard semantic safety gates

→ classify stability only after the full sample exists
```

At the same time,
stop repairing FIC-FIN-08 by adding Korean phrase variants one by one.

The validator must answer:

```text
Was industrial net debt / working capital actually applied?

or

Was it explicitly mentioned only to say
that the framework does not apply?
```

The correct next proof is therefore:

```text
semantic hard-failure vs calibration-observation separation

+ FIC-FIN-05 boundary band

+ application-role financial-sector validator

+ one clean full Sol/xhigh 8 × 3 canary
```

Not:

```text
another exact-point target chase

another phrase whitelist

a runtime review

a threshold change

a scorecard

a majority vote

a partial-context continuation

Astra fallback

production monitoring resume
```

Measure the boundary instead of forcing it.
