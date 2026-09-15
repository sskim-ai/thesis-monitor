# Thesis Monitor — Positive Stronger-Bucket Contract Review & Full GPT-5.6 Sol Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260910-positive-stronger-bucket-contract-review-and-full-sol-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260910-positive-stronger-bucket-contract-review-full-sol-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12X — Positive Stronger-Bucket Contract Consistency Review
       + Full GPT-5.6 Sol / xhigh Fictional Financial Canary
```

This task begins after M12W restored the proof-critical model to GPT-5.6 Sol / xhigh.

M12W proved that the Sol runtime restoration itself works:

```text
run-1/context-01
→ gpt-5.6-sol / xhigh
→ PASS
→ ~407.72 seconds
→ output complete
→ timeout 0
→ wrapper retry 0
```

The generation stopped because FIC-FIN-01 produced:

```text
BUY 6.5 : 3.5
```

while the frozen exact fixture target was:

```text
BUY 6.0 : 4.0
```

M12X must NOT assume that the model is wrong.

The current generic Directional contract itself also says:

```text
6.5-or-stronger can be supported by materially stronger
corroboration, persistence, quality, visibility, or valuation.

Missing one particular domain is not an automatic cap
when distinct stronger support is actually established.
```

FIC-FIN-01 contains:

```text
operating improvement
+
operating cash-flow improvement
+
net-cash / balance-sheet resilience
```

while also containing:

```text
valuation Unknown
+
durability beyond the current reporting cycle Unknown
+
elevated execution expectations
+
competition risk
```

Therefore M12X must first decide whether the exact 6.0 target is:

```text
A. correct under the generic contract

B. over-constrained relative to the generic contract

C. evidence of an internally under-specified 6.0-vs-6.5 boundary
```

Only after that decision may the full Sol canary run.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260910-gpt56-sol-xhigh-restoration-full-fictional-financial-canary-report.zip
```

Verified SHA-256:

```text
2e3d3c49081443d2b3646ba078460391db4aceea5b8656a721bcb609b4cb0700
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Artifact index independently verified:

```text
indexed payloads = 120
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

Recompute before trusting the bundle.

---

# 2. M12W repository provenance

Reported:

```text
branch =
codex/20260910-gpt56-sol-restoration-m12w

base_sha =
9e5861a2479aaae3fa473824a6f764435f2bba65

work_instruction_commit =
e8441e0543054534566e99c19fbdcd6c0722462c

implementation_commit =
538cb761e1c10754cd74dd66b22d3e2f803561ac

report_commit =
079213d7ff730c1d9eb60fca3b06b404ff34f0e5

final_head_sha =
079213d7ff730c1d9eb60fca3b06b404ff34f0e5
```

Use actual repository HEAD at M12X start.

If unexplained drift exists in:

```text
Directional ordinal prompt
target-audit fixtures
financial validators
first-class financial evidence
fictional source packet
Sol runtime contract
```

STOP:

```text
UNEXPLAINED_M12X_BASELINE_DRIFT
```

---

# 3. Model target remains GPT-5.6 Sol

Proof-critical model:

```text
gpt-5.6-sol / xhigh
```

Default Codex authoring/review target:

```text
gpt-5.6-sol / xhigh
```

Hard runner rule:

```text
actual model = gpt-5.6-sol
actual reasoning = xhigh
```

Otherwise:

```text
STOP
SOL_RUNNER_MODEL_TARGET_MISMATCH
```

No Astra fallback.

No alternate model fallback.

No lower reasoning effort.

---

# 4. M12W runtime result — restoration succeeded

M12W first model context:

```text
elapsed = 407.718801 seconds

status = PASS

output bytes = 15199

schema parse = PASS

timeout = false

capacity failure = 0

orphan = 0

CLI internal retry = 0

wrapper retry = 0
```

Observed model:

```text
gpt-5.6-sol
```

Observed effort:

```text
xhigh
```

This task must not reopen Astra transport debugging.

Keep:

```text
timeout = 1800
subjects/context = 4
wrapper auto-retry = 0
MODEL_CONTEXT_COUPLED
```

---

# 5. Historical Sol runtime evidence

M12W verified:

```text
historical completed Sol contexts = 38
historical Sol timeout count = 0
```

Including:

```text
M12D:
6 / 6 fictional contexts complete

historical real proof:
32 / 32 contexts complete
```

These are historical runtime reliability evidence.

They are not current semantic regression outputs because the contract changed.

---

# 6. M12W deterministic validation

M12W Phase A passed:

```text
focused pytest = 260 passed

full local pytest = 3255 passed
2 warnings

ruff = PASS

git diff --check = PASS
```

Hosted CI:

```text
3250 passed
5 failed
```

with:

```text
new M12W hosted-CI failures = 0
```

The 5 failures remain the known historical portability backlog.

M12X must not broaden into that cleanup.

---

# 7. M12W canary stop — exact state

Generation:

```text
20260910-m12w-fictional-20260910T020309Z-f8b8bd468c5a
```

Completed:

```text
run-1/context-01 only
```

Output rows:

```text
4
```

Schema:

```text
4 / 4 PASS
```

Observed core balances:

```text
FIC-FIN-01:
BUY 6.5:3.5

FIC-FIN-02:
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-03:
HOLD 5.0:5.0 NEUTRAL

FIC-FIN-04:
HOLD 5.0:5.0 NEUTRAL
```

Only hard failure:

```text
FIC-FIN-01
frozen_ordinal_contract_inconsistent
```

because the exact target audit expected:

```text
6.0
```

and observed:

```text
6.5
```

No repeated-run stability was measured.

FIC-FIN-05/06/07/08 were not run.

---

# 8. Important distinction — target fixture vs generic contract

The current canary has two different layers:

```text
generic Directional ordinal contract

fixture-specific expected target bucket
```

The fixture target must be DERIVED FROM the generic contract.

It must not silently become a stronger rule than the generic contract.

M12X must verify:

```text
Does FIC-FIN-01 = 6.0 actually follow from the generic contract?
```

If not, the fixture target is wrong.

Do not modify model behavior merely to satisfy a stale/over-constrained test target.

---

# 9. Exact generic prompt — positive 6.0/6.5 boundary

The M12W prompt states:

```text
6.0:4.0 is the minimum BUY and requires both
a positive issuer-level material anchor
and sufficiently current or independent corroboration.

6.5:3.5 and stronger positive balances require
progressively stronger corroboration, persistence, quality,
visibility, or valuation support.
```

It also states:

```text
A material unresolved causal, reversibility,
persistence, or critical-validation limit
constrains justified directional strength without becoming negative evidence.

When an anchor and support exist but such a limit
leaves adjacent buckets reasonably supportable,
apply the tie-break toward 5.0.
```

And:

```text
If an unresolved material confirmation leaves
both 6.0 and 6.5 reasonably supportable,
the tie-break selects 6.0.
```

But critically:

```text
missing one particular domain is not an automatic cap
when distinct stronger support is actually established.
```

M12X must reconcile these clauses.

---

# 10. FIC-FIN-01 evidence packet — frozen

Do not change the case.

Supplied positive evidence includes:

## Business/operating

```text
Recurring demand and disciplined reinvestment support durable economics.

Comparable-period revenue and operating profit both improved.
```

## Cash conversion

```text
QTD operating cash flow improved
vs prior-year comparable period.
```

The derived OCF-less-PPE metric is overlapping context
and must NOT be double-counted as another independent axis.

## Financial resilience

```text
safely derived net debt = negative
→ net-cash condition
```

## Limitations / risks

```text
no safe current valuation multiple

durability beyond current reporting cycle unproven

competition could narrow pricing power

market already expects continued profitable growth
```

These limitations must be considered.

But they are not automatically negative evidence.

---

# 11. M12W Sol reasoning — frozen

The preserved Sol candidate explicitly says:

```text
"영업 성장, 현금 전환 개선, 순현금이라는
구별되는 근거가 긍정 방향을 지지한다."
```

and uses:

```text
operating evidence
operating cash flow
net debt / net cash
```

as material directional anchors.

It also explicitly says:

```text
valuation is unavailable

durability is unproven

competition risk exists

execution expectations are high
```

and assigns:

```text
directional confidence = MEDIUM
```

This is not a missing-risk or hallucinated-support problem.

---

# 12. Primary forensic question

Before changing code or fixtures,
classify the M12W FIC-FIN-01 6.5 output as exactly one of:

```text
SOL_OUTPUT_CONTRACT_CONSISTENT_6_5

SOL_OUTPUT_CONTRACT_VIOLATION_EXPECT_6_0

EXACT_FIXTURE_TARGET_OVERCONSTRAINED

GENERIC_6_0_6_5_CONTRACT_UNDERSPECIFIED

MIXED
```

Root cause must be based on:

```text
generic ordinal wording
+
actual evidence
+
candidate reasoning
```

not on:

```text
historical majority label
```

---

# 13. Stronger-support economic independence

M12X must decide whether FIC-FIN-01 has sufficiently distinct stronger support.

Potential positive axes:

```text
A. operating/business improvement

B. cash-conversion improvement

C. balance-sheet resilience / net cash
```

Do not use reference count.

Audit economic independence:

```text
Is B genuinely distinct from A?

Is C genuinely distinct from A/B?

Does the evidence establish only minimum direction,
or materially stronger breadth/quality beyond minimum BUY?
```

The derived OCF-minus-PPE metric must not be counted separately from OCF.

---

# 14. Role of persistence Unknown

The case contains:

```text
durability beyond current reporting cycle remains unproven
```

M12X must distinguish:

```text
A. missing persistence evidence that merely prevents >6.5 strength

B. a material persistence uncertainty that makes both 6.0 and 6.5 reasonably supportable,
therefore invoking the existing tie-break to 6.0

C. an uncertainty so severe that even 6.0 is questionable
```

Freeze the generic rule.

Do not assume every persistence Unknown means 6.0 max.

---

# 15. Role of valuation Unknown

The case contains:

```text
No safe current valuation multiple is supplied.
```

M12X must preserve:

```text
valuation Unknown = conviction limitation
not negative evidence
```

Determine whether valuation absence:

```text
automatically caps 6.5
```

The current prompt says:

```text
NO
```

unless it leaves the adjacent bucket genuinely ambiguous.

Do not create a universal valuation-required-for-6.5 rule
unless the user explicitly authorizes a philosophy change.

---

# 16. Role of elevated market expectations

The market expects continued profitable growth.

This is a real negative/caution axis,
but not necessarily enough to reverse BUY.

Audit whether:

```text
high execution expectations
+
competition risk
```

materially reduce 6.5 to 6.0
under the current generic contract.

Do not treat market expectation as valuation multiple.

Do not invent price/valuation.

---

# 17. Preferred decision principle

M12X should prefer internal contract coherence over exact fixture preservation.

If the evidence clearly supports:

```text
minimum BUY
+
materially stronger independent corroboration
```

then:

```text
6.5 may be correct
```

despite missing valuation or longer-term persistence.

If both 6.0 and 6.5 remain genuinely reasonable
after applying all positive support and limitations:

```text
tie-break → 6.0
```

The key word is:

```text
genuinely
```

Do not invoke the tie-break merely because any Unknown exists.

---

# 18. Branch A — exact target is over-constrained

If root cause is:

```text
EXACT_FIXTURE_TARGET_OVERCONSTRAINED
```

or:

```text
SOL_OUTPUT_CONTRACT_CONSISTENT_6_5
```

then:

```text
do NOT change Directional prompt semantics
```

Instead:

```text
update the derived fictional target contract
for the strong-quality pattern
```

to the newly frozen generic outcome.

If the outcome is:

```text
BUY 6.5:3.5
```

state exactly why it follows from generic stronger-support semantics.

No ticker-specific production logic.

Fixture/test target changes are allowed because they are test expectations,
not runtime investment logic.

Then run deterministic validation
and the full new Sol canary.

---

# 19. Branch B — generic contract under-specified

If:

```text
GENERIC_6_0_6_5_CONTRACT_UNDERSPECIFIED
```

freeze ONE bounded generic clarification.

The clarification must resolve:

```text
when distinct current support is strong enough for 6.5
despite one or more unresolved domains

vs

when unresolved persistence/valuation/confirmation
keeps 6.0 and 6.5 genuinely adjacent
and invokes the conservative tie-break.
```

No fixed formula.

No evidence counting.

No ticker-specific rule.

After repair:

```text
freeze FIC-FIN-01 target
```

from the clarified generic rule.

Then run full new canary.

---

# 20. Branch C — Sol output violated a clear contract

If:

```text
SOL_OUTPUT_CONTRACT_VIOLATION_EXPECT_6_0
```

and the existing generic contract is already unambiguous,
do not change fixture target.

A bounded prompt clarification may be added
only if the current prompt failed to express the already-intended rule clearly enough.

Do not add:

```text
FIC-FIN-01 should be 6.0
```

or any synthetic case name.

Then run full new canary.

---

# 21. No hard exact-label gate before root-cause freeze

M12W stopped after one model call because the target was treated as a hard gate.

In M12X:

```text
offline root-cause and target derivation MUST complete
before any new model call.
```

Once the generic target is frozen,
it may again be used as a hard contract gate.

Do not run a model call merely to decide what the contract means.

---

# 22. Generic positive 6.0 / 6.5 fixture matrix

Create model-free contract fixtures.

At minimum:

## POS-ORD-01 — minimum BUY

```text
positive issuer-level anchor
+
one current/independent corroborating fact
+
material persistence/valuation limitations
+
no broader stronger support
```

Expected:

```text
6.0
```

## POS-ORD-02 — stronger breadth

```text
positive operating/business evidence
+
distinct cash-conversion support
+
distinct balance-sheet resilience
+
limitations present but not severe enough
to make current stronger support ambiguous
```

Freeze expected:

```text
6.5
or 6.0
```

based on the generic review.

This fixture should represent the FIC-FIN-01 pattern generically.

## POS-ORD-03 — stronger support but material adjacent ambiguity

```text
multiple positive axes
+
a material unresolved persistence/causal issue
that directly threatens whether the improvement is durable
```

Expected:

```text
6.0
```

via tie-break.

## POS-ORD-04 — stronger 6.5 with valuation missing

```text
strong, distinct current operating/cash/balance-sheet support
+
valuation missing only
```

Test whether valuation absence is a universal cap.

Under current philosophy it should NOT automatically be one.

## POS-ORD-05 — elevated expectations

```text
strong fundamental support
+
market expectations elevated
```

Determine whether the expectation evidence:
- merely limits upside conviction
- or is strong enough to reduce a 6.5 case to 6.0.

No fixed rule based only on the category.

---

# 23. Symmetric negative-side audit

The clarified positive rule must have a direction-symmetric analog.

Create:

```text
NEG-ORD-01 minimum SELL 6.0

NEG-ORD-02 stronger SELL 6.5

NEG-ORD-03 material adjacent ambiguity → 6.0 via tie-break
```

Do not make stronger BUY harder or easier than stronger SELL without explicit rationale.

---

# 24. No scorecard

Hard prohibition:

```text
three independent axes = 6.5

two axes = 6.0

one Unknown = -0.5

valuation missing = cap 6.0

net cash = +0.5
```

Required:

```text
fixed_score_rule_count = 0
evidence_count_bucket_rule_count = 0
```

The contract remains qualitative/ordinal.

---

# 25. Preserve FIC-FIN-02 / 04 / 05 contracts

M12W first context already showed:

```text
FIC-FIN-02 =
HOLD 4.5:5.5 SELL_LEAN
→ target PASS

FIC-FIN-04 =
HOLD 5.0:5.0 NEUTRAL
→ target PASS
```

Preserve unless the generic 6.0/6.5 clarification truly has a cross-case implication.

FIC-FIN-05 latest M12U contract remains:

```text
HOLD 4.5:5.5 SELL_LEAN
```

under conditional market-expectation/refinancing-risk logic.

Do not reopen it.

---

# 26. Preserve financial semantics

Required unchanged:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

financial-context selected-only projection

materiality-scoped working-capital grounding

QTD/YTD Korean period validator

financial-sector explicit non-applicability

FCF label safety

prior-year-end vs YoY safety

debt completeness safety

normalized earnings safety

market-expectation economic-independence rule
```

Change counters:

```text
financial_context_selection_change_count = 0
first_class_projection_change_count = 0
working_capital_validator_semantic_change_count = 0
qtd_ytd_validator_semantic_change_count = 0
financial_exclusion_validator_semantic_change_count = 0
market_expectation_contract_change_count = 0
```

unless Branch B specifically requires only the 6.0/6.5 ordinal clarification.

---

# 27. Runtime freeze

Keep Sol runtime exactly:

```text
model = gpt-5.6-sol

reasoning = xhigh

MODEL_CONTEXT_COUPLED

4 subjects/context

1800-second finite watchdog

wrapper retry = 0

batch split = 0
```

Do not increase timeout.

Do not retry contexts.

Do not return to Astra.

---

# 28. Phase A forensic artifacts

Before implementation produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12x-scope-freeze

04-sol-runtime-restoration-freeze

05-fic-fin-01-source-pattern

06-fic-fin-01-m12w-output-forensic

07-current-6-0-6-5-contract-text

08-positive-support-economic-independence-audit

09-persistence-unknown-boundary-audit

10-valuation-unknown-boundary-audit

11-market-expectation-boundary-audit

12-exact-target-vs-generic-contract-audit

13-fic-fin-01-root-cause-decision
```

No code/fixture changes before artifact 13 is frozen.

---

# 29. Phase B contract artifacts

Produce:

```text
14-positive-6-0-6-5-generic-contract

15-negative-symmetry-contract

16-pos-ord-01

17-pos-ord-02

18-pos-ord-03

19-pos-ord-04

20-pos-ord-05

21-neg-ord-01

22-neg-ord-02

23-neg-ord-03

24-fic-fin-01-derived-target-decision
```

---

# 30. Branch-specific implementation artifacts

If fixture-target correction only:

```text
25-target-fixture-before-after

26-directional-prompt-no-change-proof
```

If bounded generic prompt clarification:

```text
25-directional-ordinal-prompt-before-after

26-target-fixture-derivation-after-clarification
```

In all branches:

```text
27-no-scorecard-proof

28-threshold-increment-lean-tiebreak-freeze
```

---

# 31. Frozen no-change artifacts

Produce:

```text
29-first-class-financial-evidence-freeze

30-working-capital-validator-freeze

31-qtd-ytd-validator-freeze

32-financial-sector-exclusion-freeze

33-market-expectation-independence-freeze

34-source-sufficiency-no-change

35-daily-delta-no-change

36-price-timing-no-change

37-renderer-ownership-no-change

38-sol-runtime-no-change
```

---

# 32. Deterministic validation gate

Before model calls require:

```text
FIC-FIN-01 root cause frozen

generic positive 6.0/6.5 contract frozen

FIC-FIN-01 expected target derived from generic rule

positive fixture matrix PASS

negative symmetry matrix PASS

fixed score rule count = 0

evidence-count bucket rule count = 0

6.0 threshold unchanged

0.5 increment unchanged

HOLD lean unchanged

tie-break direction unchanged

FIC-FIN-02 target regression PASS

FIC-FIN-04 target regression PASS

FIC-FIN-05 latest target regression PASS

all financial semantic regressions PASS

Sol runtime unchanged

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

# 33. New full Sol fictional generation

Only after Phase A/B deterministic PASS.

Create a NEW generation.

Do not continue M12W.

Do not reuse M12W output in the formal stability sample.

Use exact frozen 8 subjects:

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

No source/case-value changes.

---

# 34. Full topology

Run:

```text
8 subjects
2 shared contexts
4 subjects/context
3 repetitions
```

Total:

```text
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

# 35. Whole-generation stop rule

On any:

```text
transport failure

timeout

schema failure

hard financial semantic failure

derived target-contract failure
```

stop the entire generation.

Required:

```text
no selective continuation

no failed-context retry

no stitching

wrapper retry = 0
```

Any repair requires a NEW full generation.

---

# 36. Runtime hard gates

Require:

```text
6 / 6 contexts success

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0
```

CLI internal retries, if any,
must be reported separately.

---

# 37. Financial hard gates

Require zero:

```text
invalid financial refs

material financial grounding failures

working-capital grounding failures

narrative substitution failures

price/technical/supply Directional refs

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

financial-sector true industrial misuse

explicit-exclusion false reject

missing optional context treated as bearish

fixed financial scoring

QTD/YTD false reject

QTD/YTD false accept

AI imperative primary action
```

---

# 38. Target-bucket hard gates

Use the newly frozen target contract.

Require:

```text
FIC-FIN-01:
all 3 repetitions match the newly derived generic target

FIC-FIN-02:
HOLD 4.5:5.5 SELL_LEAN
all 3

FIC-FIN-04:
HOLD 5.0:5.0 NEUTRAL
all 3

FIC-FIN-05:
HOLD 4.5:5.5 SELL_LEAN
all 3
```

If M12X freezes FIC-FIN-01 as 6.5:

```text
do not treat 6.0 as acceptable merely because it is adjacent
```

If M12X freezes 6.0:

```text
do not accept 6.5 merely because it is BUY
```

The point of the canary is repeated contract consistency.

---

# 39. Formal stability

Run the unchanged formal classifier.

Report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

No averaging.

No majority vote.

No classifier weakening.

Required:

```text
opposite-direction reversal = 0
```

---

# 40. Stance/delta measurement

Measure:

```text
business_thesis_change

fundamental_new_buyer

fundamental_holder
```

for all 24 outputs.

Do not repair them in M12X.

If core buckets are fully stable
but these fields remain materially variable:

```text
fresh_real_proof_readiness = NOT_READY
```

and choose the smallest next semantic repair.

---

# 41. New-buyer concern for FIC-FIN-01

Historical Sol outputs previously showed:

```text
ATTRACTIVE ↔ WAIT
```

variance for the strong-quality case.

M12W first run produced:

```text
ATTRACTIVE
```

This is NOT yet a repeated proof.

M12X must measure all 3 repetitions.

If balance is stable but new-buyer stance is not:

```text
next_scope =
BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL
```

Do not hide the variance.

---

# 42. Holder concern for FIC-FIN-05

Historical Sol outputs previously showed:

```text
REDUCE ↔ REVIEW
```

variance.

Current semantic contract changed the FIC-FIN-05 core balance target
to HOLD SELL_LEAN 5.5.

M12X must measure holder stance under the new contract.

Do not assume the historical variance will remain.

---

# 43. Real holdout readiness

Only set:

```text
fresh_real_proof_readiness = READY
```

if all are true:

```text
6 / 6 Sol calls complete

24 / 24 schema PASS

financial hard semantics PASS

all frozen target buckets stable and correct

formal STABLE = 8

BOUNDARY_UNCERTAINTY = 0

UNSTABLE = 0

business-delta unresolved material variance = 0

new-buyer unresolved material variance = 0

holder unresolved material variance = 0

runtime suitable for exposed real cohort

real issuer exposure = 0
```

Then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH
```

Do not start real proof inside M12X.

---

# 44. If FIC-FIN-01 remains unstable after contract clarification

If all three repetitions do not converge on the frozen target:

```text
STOP
```

Do not adjust the target after seeing the three model outputs.

That would contaminate the validation.

Set:

```text
next_scope =
POSITIVE_STRONGER_BUCKET_STABILITY_REVIEW_GPT56_SOL
```

Use the new full sample offline.

No majority voting.

---

# 45. If Sol runtime fails

If any Sol context times out:

```text
STOP

no Astra fallback

no timeout increase

no failed-context retry
```

Set:

```text
next_scope =
SOL_RUNTIME_REGRESSION_REVIEW
```

---

# 46. Production firewall

Required:

```text
model_calls_real = 0

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

# 47. Hosted CI portability

Keep separate backlog:

```text
HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR
```

M12W:

```text
5 known failures
0 new failures
```

M12X must introduce:

```text
0 new failures
```

Do not claim hosted CI PASS unless fully green.

---

# 48. Required validation/report artifacts

Produce:

```text
39-focused-test-results
40-full-local-test-results
41-ruff-and-diff-results
42-hosted-ci-portability-observation
43-model-call-gate

44-fictional-canary-generation-manifest
45-fictional-canary-source-lock

46-run-1-context-01
47-run-1-context-02
48-run-2-context-01
49-run-2-context-02
50-run-3-context-01
51-run-3-context-02

52-full-fictional-semantic-audit
53-full-fictional-target-bucket-audit
54-full-fictional-positive-stronger-bucket-audit
55-full-fictional-grounding-audit
56-full-fictional-formal-stability
57-full-fictional-core-only-stability
58-full-fictional-business-delta-audit
59-full-fictional-stance-variance
60-full-fictional-runtime-audit
61-full-fictional-message-specificity-advisory
```

Preserve for every attempted call:

```text
prompt
schema
raw output
receipt
lifecycle receipt
stderr
stdout
transport log
run document
```

---

# 49. Required completion artifacts

Produce:

```text
62-positive-stronger-bucket-contract-success-decision

63-sol-full-canary-success-decision

64-sol-runtime-real-holdout-suitability

65-core-balance-stability-decision

66-business-delta-followup-decision

67-new-buyer-stance-followup-decision

68-holder-stance-followup-decision

69-fresh-real-proof-readiness-decision

70-astra-future-experiment-handoff

71-hosted-ci-portability-handoff

72-production-no-change

73-schedule-pause-observation

74-master-workflow-update

75-program-completion
```

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

m12w_status
m12x_status

implementation_model_target
implementation_reasoning_effort
investment_judgment_model_target
investment_judgment_reasoning_effort
authoring_model_target_match
runner_model_target_match
model_target_fallback_count

fic_fin_01_root_cause
fic_fin_01_previous_target
fic_fin_01_frozen_target
fic_fin_01_target_change_reason
directional_prompt_change_count
fixture_target_change_count

positive_6_0_6_5_contract_status
negative_symmetry_contract_status
persistence_unknown_boundary_status
valuation_unknown_boundary_status
market_expectation_boundary_status

fixed_score_rule_count
evidence_count_bucket_rule_count

directional_threshold_changed
directional_increment_changed
hold_lean_contract_changed
calibration_tiebreak_direction_changed

financial_semantic_change_count
financial_context_selection_change_count
first_class_projection_change_count
working_capital_validator_semantic_change_count
qtd_ytd_validator_semantic_change_count
financial_exclusion_validator_semantic_change_count
market_expectation_contract_change_count

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

target_bucket_contract_violation_count

formal_stable_count
formal_boundary_uncertainty_count
formal_unstable_count
opposite_direction_reversal_count

business_delta_variance_subject_count
new_buyer_stance_variance_subject_count
holder_stance_variance_subject_count

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

Anything not actually measured:

```text
NOT_MEASURED
```

---

# 51. Artifact integrity

Freeze all reports/model artifacts/master workflow before final index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 52. Final task principle

M12W established an important separation:

```text
Astra runtime was the transport problem.

Sol restoration fixed the runtime problem.
```

The new stop is different:

```text
Sol produced BUY 6.5 for a strong-quality case
while a fixture expected exactly 6.0.
```

The current generic contract can plausibly support 6.5 because the case contains:

```text
operating improvement
+
cash-conversion improvement
+
balance-sheet resilience
```

and the prompt explicitly says:

```text
missing one domain is not an automatic 6.5 cap
when distinct stronger support is established.
```

Therefore the correct next move is:

```text
audit the contract first

→ determine whether 6.0 target is actually justified

→ if the test target is over-constrained,
   fix the test expectation rather than the model

→ if the generic rule is genuinely ambiguous,
   clarify only the 6.0-vs-6.5 boundary

→ keep all financial semantics and Sol runtime frozen

→ run one entirely new 8 × 3 Sol/xhigh canary

→ measure target consistency + formal stability + stance/delta

→ only then authorize the fresh real proof
```

Not:

```text
force Sol to imitate an arbitrary exact target
```

Not:

```text
change the 6.0 BUY threshold
```

Not:

```text
count evidence refs
```

Not:

```text
make valuation mandatory for 6.5
```

Not:

```text
return to Astra
```

Not:

```text
continue only the unfinished M12W contexts
```

And not:

```text
resume production monitoring
```

The fixture must follow the investment contract, not the other way around.
