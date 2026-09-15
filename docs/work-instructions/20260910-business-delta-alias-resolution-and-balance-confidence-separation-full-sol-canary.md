# Thesis Monitor — Business-Delta Alias Resolution + Balance/Confidence Separation + Full Sol Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260910-business-delta-alias-resolution-and-balance-confidence-separation-full-sol-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260910-business-delta-alias-resolution-balance-confidence-full-sol-canary-report.zip
```

Master-workflow phase:

```text
M12Z — GPT-5.6 Sol / xhigh
       A. Business-Delta Audit Alias Resolution Repair
       B. Positive 6.0/6.5 Balance-vs-Confidence Stability Repair
       C. Full Fictional Financial Canary
```

This task begins after M12Y stopped during the first fictional context.

M12Y did NOT fail because of Sol runtime.

M12Y runtime:

```text
run-1/context-01
→ gpt-5.6-sol / xhigh
→ PASS
→ ~445.4 sec
→ timeout 0
→ wrapper retry 0
→ CLI internal retry 0
```

The generation stopped because:

```text
1. business-delta audit produced 3 false rejects
   caused by canonical-ref vs alias-keyed-context comparison

2. FIC-FIN-01 produced BUY 6.0:4.0
   while the currently frozen generic target is BUY 6.5:3.5
```

M12Z must resolve these two bounded issues.

M12Z must preserve all other completed M12Y semantic decisions.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260910-sol-leverage-target-delta-contract-contrastive-exclusion-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
67292aaaf81b8122c2c1a8bb62682d2889d83c5182317207fbd61fe9401169e3
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
indexed payloads = 176

missing = 0

extra = 0

hash mismatch = 0

size mismatch = 0
```

Recompute before trusting the bundle.

---

# 2. M12Y deterministic validation — frozen

M12Y completed Phase A/B/C deterministic work.

Validation:

```text
focused pytest =
217 passed

full local pytest =
3293 passed
2 warnings

ruff =
PASS

git diff --check =
PASS
```

Hosted CI:

```text
3288 passed

5 known historical portability failures

new M12Y hosted-CI failures =
0
```

Do not broaden M12Z into historical CI portability cleanup.

Preserve separate backlog:

```text
HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR
```

---

# 3. Model/runtime target — frozen

Proof-critical model:

```text
gpt-5.6-sol / xhigh
```

Default authoring/review target:

```text
gpt-5.6-sol / xhigh
```

Runtime:

```text
MODEL_CONTEXT_COUPLED

4 subjects/context

1800-second watchdog

single authoritative watchdog

wrapper auto-retry = 0

batch split = 0
```

No Astra calls.

No model fallback.

No timeout change.

No topology change.

No wrapper retry.

If actual runner is not:

```text
gpt-5.6-sol / xhigh
```

then:

```text
STOP
SOL_RUNNER_MODEL_TARGET_MISMATCH
```

---

# 4. M12Y completed semantic decisions — preserve

## 4.1 Contrastive financial-sector exclusion

M12Y root cause:

```text
CONTRASTIVE_REPLACEMENT_EXCLUSION_NOT_RECOGNIZED
```

Offline repair:

```text
PASS
```

The validator now supports genuine non-application semantics such as:

```text
산업회사식 순부채와 운전자본 틀 대신
언더라이팅과 규제자본을 본다.

X가 아니라 Y를 본다.

use Y instead of X.

rather than X, use Y.
```

while mixed exclusion + actual application remains invalid.

M12Z must not reopen this repair.

It must receive full-canary proof if the generation reaches FIC-FIN-08.

## 4.2 FIC-FIN-05 exact target

M12Y root cause:

```text
EXACT_FIXTURE_TARGET_OVERCONSTRAINED_EXPECT_6_0
```

Previous:

```text
HOLD 4.5:5.5 SELL_LEAN
```

Frozen target:

```text
SELL 4.0:6.0
```

Reason:

```text
complete high interest-bearing debt
+
current verified thin cash

jointly establish present balance-sheet resilience pressure
sufficient for minimum negative direction.

E03 is synthesis of the debt/cash condition,
not a third independent axis.

refinancing terms/maturity remain Unknown
and stable operating profit is counterevidence,
therefore stronger negative severity beyond minimum SELL is limited.
```

Do not revert to 5.5.

Market-expectation rule remains unchanged:

```text
E07-like expectation conditional on the same unresolved refinancing risk
does NOT automatically count as independent corroboration.
```

The 6.0 target is justified by the balance-sheet evidence itself.

## 4.3 FIC-FIN-05 business delta

M12Y root cause:

```text
ABSOLUTE_NEGATIVE_STATE_MISREAD_AS_WEAKENING_DELTA
```

Frozen target:

```text
UNCHANGED
```

because the source packet contains current high debt/thin cash
but no explicit prior/baseline deterioration.

Generic rule:

```text
business_thesis_change is a change assessment.

STRENGTHENED / WEAKENED requires supplied meaningful change
relative to a prior/baseline state.

Absolute positive/negative current state alone
does not establish change.
```

Preserve this contract.

---

# 5. M12Y new canary — exact completed sample

Generation:

```text
20260910-m12y-fictional-20260910T043154Z-2761aab01862
```

Completed:

```text
run-1/context-01 only
```

Model calls:

```text
1
```

Outputs:

```text
4 / 4 schema PASS
```

Runtime:

```text
elapsed ≈ 445.4 sec

timeout = 0

capacity failure = 0

orphan = 0

CLI internal retry = 0

wrapper retry = 0
```

Remaining contexts:

```text
NOT STARTED
```

Formal stability:

```text
NOT_MEASURED
```

Do not infer repeated stability.

---

# 6. M12Y observed context-01 balances

Observed:

```text
FIC-FIN-01 =
BUY 6.0:4.0

FIC-FIN-02 =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-03 =
HOLD 5.5:4.5 BUY_LEAN

FIC-FIN-04 =
HOLD 5.0:5.0 NEUTRAL
```

Frozen exact target audit:

```text
FIC-FIN-01:
expected 6.5
observed 6.0
FAIL

FIC-FIN-02:
expected 4.5 buy / 5.5 sell
PASS

FIC-FIN-04:
expected 5.0 / 5.0
PASS
```

This is the only actual bucket-target miss in the completed M12Y sample.

---

# 7. Issue A — business-delta audit false reject

M12Y business-delta audit produced:

```text
FIC-FIN-01 STRENGTHENED → false FAIL

FIC-FIN-02 WEAKENED → false FAIL

FIC-FIN-03 STRENGTHENED → false FAIL

FIC-FIN-04 UNCHANGED → PASS
```

Reported root cause:

```text
CANONICAL_REFS_COMPARED_TO_ALIAS_KEYED_CONTEXT
```

Failure classification:

```text
VALIDATOR_FALSE_REJECT_ALIAS_RESOLUTION_GAP
```

Reported:

```text
validator false rejects = 3

model semantic violations after raw-alias replay = 0
```

This is a validator/audit reference-space bug,
not a model business-delta semantic failure.

---

# 8. Exact raw-alias replay — authoritative

M12Y already demonstrated:

```text
FIC-FIN-01:
STRENGTHENED supported by E04/E08
comparable-period operating / OCF improvement

FIC-FIN-02:
WEAKENED supported by E08
lower comparable operating cash flow

FIC-FIN-03:
STRENGTHENED supported by E03
recent operating rebound

FIC-FIN-04:
UNCHANGED supported by stable/flat current-state evidence
```

M12Z must make the deterministic audit reach these conclusions
without manual/raw special replay.

---

# 9. Business-delta audit reference-space contract

The audit must resolve model-facing aliases and canonical evidence identity consistently.

Model output uses:

```text
E01
E02
...
```

The audit/context may internally store:

```text
canonical_ref
```

Do NOT directly compare:

```text
canonical_ref string
vs
alias-keyed map
```

Required resolution flow:

```text
output evidence_ref alias

→ per-ticker alias catalog

→ canonical evidence identity

→ context/source evidence item

→ comparison / period / change semantics
```

or the exact inverse normalization.

Use one canonical comparison space.

---

# 10. Alias resolution safety

Hard rules:

```text
no fuzzy matching

no label-text matching

no nearest-alias guessing

no cross-ticker alias lookup

no invented alias

no canonical-ref truncation

no silent many-to-one collision
```

If alias resolution is missing or ambiguous:

```text
fail closed
with explicit INVALID_OR_UNRESOLVED_EVIDENCE_REF
```

Do not reinterpret model reasoning.

The repair is audit-only reference resolution.

---

# 11. Evidence identity requirement

For a delta claim to be supported:

```text
1. output cites a supplied alias

2. alias resolves to one canonical evidence item

3. that evidence item contains actual change/baseline semantics
   appropriate to the claimed STRENGTHENED/WEAKENED direction

4. absolute current-state evidence alone is insufficient
```

This preserves the M12Y absolute-state-vs-delta contract.

---

# 12. Delta positive regression fixtures

Required PASS:

```text
comparable-period operating improvement
→ STRENGTHENED may be supported

comparable-period OCF deterioration
→ WEAKENED may be supported

recent operating rebound explicitly versus prior state
→ STRENGTHENED may be supported

current flat state with no change evidence
→ UNCHANGED
```

Use aliases resolved through the actual per-ticker catalog.

---

# 13. Delta negative regression fixtures

Required FAIL:

```text
current high debt only
→ WEAKENED unsupported

current high margin only
→ STRENGTHENED unsupported

unknown/refinancing gap only
→ WEAKENED unsupported

invalid alias

alias from another ticker

alias mapping collision

canonical ref not present in selected context

narrative current-state statement with no baseline comparison
```

No false accept.

No false reject.

---

# 14. Exact M12Y output replay after alias repair

Replay the exact preserved M12Y run-1/context-01 output.

Expected deterministic delta audit:

```text
FIC-FIN-01 = PASS STRENGTHENED

FIC-FIN-02 = PASS WEAKENED

FIC-FIN-03 = PASS STRENGTHENED

FIC-FIN-04 = PASS UNCHANGED
```

Required:

```text
validator_false_reject_count = 0

validator_false_accept_count = 0

model_semantic_violation_count = 0
```

Do not rewrite the historical output.

---

# 15. Issue B — FIC-FIN-01 positive stronger-bucket instability

The exact FIC-FIN-01 source context has remained stable across recent Sol phases.

Verified source-context SHA-256:

```text
33aca8f5cd505bb48f1a6cb09882a7d6899569622126eb246b081ca848870018
```

Observed same-model outputs:

```text
M12W:
BUY 6.5:3.5

M12X:
BUY 6.5:3.5

M12Y:
BUY 6.0:4.0
```

All:

```text
gpt-5.6-sol / xhigh
```

The M12Y prompt added the business-delta clarification,
but the core 5.0/5.5/6.0/6.5 ordinal text remained substantively unchanged.

Therefore the 6.0 observation cannot be dismissed as Astra/Sol cross-model drift.

It is a positive stronger-bucket stability issue.

---

# 16. FIC-FIN-01 semantic comparison

All three Sol outputs used the same broad material support:

```text
operating/business improvement

operating cash-flow improvement

net-cash / financial resilience
```

All also recognized limitations:

```text
longer-horizon durability/persistence unproven

safe current valuation unavailable

elevated execution expectations

competition risk
```

M12W/M12X mapped the pattern to:

```text
6.5
```

M12Y mapped it to:

```text
6.0
```

M12Y explanation:

```text
the positive axes support BUY,
but persistence and valuation gaps limit stronger conviction.
```

This is not a financial parsing failure.

---

# 17. Primary positive-bucket root-cause question

Before changing prompt/fixtures,
classify the 6.5→6.0 variation as exactly one primary root cause:

```text
BALANCE_CONFIDENCE_SEMANTIC_ENTANGLEMENT

PERSISTENCE_LIMIT_PRIORITY_UNDERSPECIFIED

GENERIC_6_0_6_5_CONTRACT_STILL_UNDERSPECIFIED

M12Y_BUSINESS_DELTA_PROMPT_INTERACTION

M12Y_6_0_IS_CLEAR_CONTRACT_VIOLATION

M12X_6_5_TARGET_WAS_STILL_OVERCONSTRAINED

TRUE_STOCHASTIC_ADJACENT_BUCKET_VARIANCE

OTHER
```

Do not change target before this root cause is frozen.

---

# 18. Balance vs confidence contract — required audit

The model has separate fields:

```text
directional_balance

directional_confidence
```

M12Z must audit whether the prompt clearly distinguishes them.

Generic principle to evaluate:

```text
directional_balance =
strength and balance of the supplied directional evidence

directional_confidence =
epistemic confidence in that judgment
given missing data, persistence, valuation, or validation limits
```

A candidate may legitimately have:

```text
BUY 6.5:3.5
+
MEDIUM confidence
```

if current evidence breadth/quality supports stronger direction
but longer-horizon certainty remains incomplete.

Do not mechanically map:

```text
MEDIUM confidence → max 6.0

LOW confidence → HOLD
```

unless explicitly intended by the investment philosophy.

---

# 19. Persistence Unknown priority contract

Clarify the difference between:

```text
A. future durability merely not yet proven

vs

B. a material unresolved issue that directly calls into question
   whether the observed current improvement is causal/persistent
```

Case A may lower:

```text
directional_confidence
```

without necessarily lowering:

```text
6.5 → 6.0
```

Case B may make:

```text
6.0 and 6.5 genuinely adjacent
```

and invoke the conservative tie-break.

This distinction must be generic.

---

# 20. Valuation Unknown remains separate

Preserve:

```text
valuation unavailable
=
confidence / price-attractiveness limitation

not automatically negative evidence

not an automatic 6.5 cap
```

Do not require valuation for stronger fundamental direction.

New-buyer stance may still be more conservative because valuation is unavailable,
but M12Z does not repair stance mapping.

---

# 21. Stronger-current-evidence rule

Evaluate and, only if needed, clarify:

```text
6.5 may be justified when current supplied evidence
materially exceeds the minimum-direction requirement
through distinct economic support in quality/breadth/visibility/resilience,
even when future durability or valuation is not fully proven.

A limitation reduces the bucket only when it makes
the stronger current-evidence conclusion itself genuinely ambiguous,
not merely because certainty is incomplete.
```

No numeric count.

No rule:

```text
3 axes = 6.5
```

Economic independence remains qualitative.

---

# 22. Conservative tie-break remains

Frozen:

```text
if evidence genuinely fits adjacent buckets,
choose the less-directional bucket toward 5.0.
```

M12Z may clarify:

```text
the tie-break is applied AFTER
balance-strength vs confidence-limit separation.

The existence of any Unknown does not automatically make
two adjacent buckets both reasonable.
```

Do not change the tie-break direction.

---

# 23. Branch A — balance/confidence separation under-specified

If root cause is:

```text
BALANCE_CONFIDENCE_SEMANTIC_ENTANGLEMENT

PERSISTENCE_LIMIT_PRIORITY_UNDERSPECIFIED

GENERIC_6_0_6_5_CONTRACT_STILL_UNDERSPECIFIED
```

allow ONE bounded generic Directional clarification covering only:

```text
balance strength vs confidence

future durability absence vs direct persistence challenge

tie-break ordering
```

Do not mention FIC-FIN-01 in production/model prompt.

Keep exact target:

```text
BUY 6.5:3.5
```

only if the offline generic contract still derives it.

---

# 24. Branch B — existing contract already clear, M12Y 6.0 is model violation

If root cause:

```text
M12Y_6_0_IS_CLEAR_CONTRACT_VIOLATION
```

do NOT add another equivalent prompt line.

Stop before model calls and set:

```text
next_scope =
POSITIVE_STRONGER_BUCKET_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL
```

Reason:

```text
repeated prompt-only clarification would not be a principled repair.
```

---

# 25. Branch C — 6.5 target still over-constrained

If offline review proves:

```text
M12X_6_5_TARGET_WAS_STILL_OVERCONSTRAINED
```

do NOT toggle the target merely because M12Y produced 6.0.

Require a generic explanation that reconciles:

```text
M12W 6.5

M12X 6.5

M12Y 6.0
```

with the contract.

Only change the target if the generic contract clearly says:

```text
6.0
```

for the source pattern independent of observed outputs.

If changed,
document why M12X's earlier derivation was wrong.

---

# 26. Branch D — true stochastic adjacent-bucket variance

If:

```text
TRUE_STOCHASTIC_ADJACENT_BUCKET_VARIANCE
```

and neither 6.0 nor 6.5 can be made uniquely correct
without inventing a scorecard or case-specific rule:

```text
STOP
NO_MODEL_CALLS
```

Set:

```text
next_scope =
DIRECTIONAL_STRENGTH_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL
```

Do not endlessly rewrite the prompt.

---

# 27. Generic positive-strength fixtures

If Branch A proceeds,
create model-free fixtures.

## POS-STAB-01 — stronger current evidence + medium confidence

```text
distinct operating improvement
+
distinct cash-conversion improvement
+
distinct financial resilience
+
future durability not yet proven
+
valuation missing

expected:
stronger bucket may coexist with MEDIUM confidence
if the limitations do not directly undermine current anchors
```

Freeze exact expected bucket from the generic review.

## POS-STAB-02 — persistence directly questionable

```text
strong current results
+
supplied evidence that the improvement may be temporary/reversal-prone

expected:
adjacent ambiguity may invoke 6.0 tie-break
```

## POS-STAB-03 — valuation only missing

```text
strong current evidence
+
only safe valuation missing

expected:
valuation absence alone does not automatically cap 6.5
```

## POS-STAB-04 — minimum support only

```text
material positive anchor
+
one sufficiently independent/current corroborating fact
+
no materially stronger breadth/quality

expected:
6.0
```

## POS-STAB-05 — confidence low due source completeness

Test that:

```text
confidence and balance are related but not mechanically mapped.
```

No fixed formula.

---

# 28. Negative symmetry fixtures

Create symmetric controls:

```text
NEG-STAB-01 stronger current negative evidence + medium confidence

NEG-STAB-02 unresolved persistence/causality directly limits stronger severity

NEG-STAB-03 valuation missing alone does not automatically cap stronger SELL

NEG-STAB-04 minimum SELL support only
```

No asymmetrical burden without rationale.

---

# 29. Preserve FIC-FIN-05 decisions

Hard freeze from M12Y:

```text
FIC-FIN-05 absolute target =
SELL 4.0:6.0

FIC-FIN-05 business delta target =
UNCHANGED
```

No market-expectation contract change.

No leverage prompt change.

M12Z must full-canary test these if it reaches context-02.

---

# 30. Preserve FIC-FIN-08 contrastive exclusion repair

M12Y offline repair status:

```text
PASS_OFFLINE_FULL_CANARY_NOT_REACHED
```

M12Z must not modify that repair unless deterministic replay regresses.

Full model proof remains required.

---

# 31. Preserve other target contracts

Unless Branch C explicitly changes FIC-FIN-01 generic target:

```text
FIC-FIN-01 =
BUY 6.5:3.5

FIC-FIN-02 =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-04 =
HOLD 5.0:5.0 NEUTRAL

FIC-FIN-05 =
SELL 4.0:6.0
```

Do not use model majority vote to derive targets.

---

# 32. Preserve financial semantics

Required unchanged:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

financial-context selected-only projection

materiality-scoped working-capital grounding

QTD/YTD Korean period semantics

contrastive/nominal financial-sector exclusion

FCF label safety

prior-year-end vs YoY safety

debt completeness safety

normalized earnings safety

market-expectation economic-independence contract
```

Required counters:

```text
financial_context_selection_change_count = 0

first_class_projection_change_count = 0

working_capital_validator_semantic_change_count = 0

qtd_ytd_validator_semantic_change_count = 0

financial_exclusion_validator_semantic_change_count = 0

market_expectation_contract_change_count = 0
```

---

# 33. Business-delta prompt remains frozen

M12Y added one bounded business-delta clarification.

M12Z must keep its semantics.

Required:

```text
business_delta_prompt_change_count = 0
```

relative to M12Y.

The M12Z delta repair is:

```text
auditor alias/canonical resolution
```

not another model prompt change.

---

# 34. Directional threshold/calibration freeze

Required unchanged:

```text
BUY threshold = 6.0

SELL threshold = 6.0

increment = 0.5

HOLD 5.5:4.5 = BUY_LEAN

HOLD 5.0:5.0 = NEUTRAL

HOLD 4.5:5.5 = SELL_LEAN

adjacent tie-break toward 5.0
```

No:

```text
scorecard

evidence-count bucket rule

majority vote

balance averaging
```

---

# 35. Runtime freeze

Use exactly:

```text
model = gpt-5.6-sol

reasoning = xhigh

MODEL_CONTEXT_COUPLED

4 subjects/context

1800-second watchdog

wrapper retry = 0

batch split = 0
```

No runtime review.

No Astra.

---

# 36. Phase A forensic artifacts

Before implementation produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12z-scope-freeze

04-sol-runtime-freeze

05-m12y-canary-stop-reproduction

06-business-delta-ref-space-trace

07-business-delta-alias-resolution-root-cause

08-m12y-raw-alias-delta-replay

09-fic-fin-01-sol-output-history

10-fic-fin-01-source-context-identity-proof

11-fic-fin-01-balance-confidence-forensic

12-persistence-limit-priority-audit

13-positive-6-0-6-5-root-cause-decision
```

No code/prompt/fixture changes before artifact 13.

---

# 37. Phase B alias-resolution artifacts

Produce:

```text
14-delta-ref-space-contract

15-alias-to-canonical-resolution-contract

16-invalid-ambiguous-alias-fail-closed-contract

17-delta-auditor-before-after

18-delta-positive-fixtures

19-delta-negative-fixtures

20-exact-m12y-context01-delta-regression
```

---

# 38. Phase C positive-bucket artifacts

If the selected root-cause branch permits implementation, produce:

```text
21-balance-vs-confidence-contract

22-persistence-unknown-priority-contract

23-tiebreak-ordering-contract

24-pos-stab-01

25-pos-stab-02

26-pos-stab-03

27-pos-stab-04

28-pos-stab-05

29-negative-symmetry-fixtures

30-fic-fin-01-derived-target-freeze
```

If no prompt change is justified,
produce an explicit no-change proof.

---

# 39. Required no-change/freeze artifacts

Produce:

```text
31-fic-fin-05-target-freeze

32-fic-fin-05-business-delta-freeze

33-fic-fin-08-exclusion-repair-freeze

34-first-class-financial-evidence-freeze

35-working-capital-validator-freeze

36-qtd-ytd-validator-freeze

37-market-expectation-contract-freeze

38-threshold-increment-lean-tiebreak-freeze

39-source-sufficiency-no-change

40-daily-delta-no-change

41-price-timing-no-change

42-renderer-ownership-no-change
```

---

# 40. Deterministic validation gate

Before model calls require:

```text
latest ZIP integrity PASS

Sol runtime freeze PASS

delta alias-resolution root cause frozen

exact M12Y context-01 delta replay PASS:
FIC-FIN-01 STRENGTHENED
FIC-FIN-02 WEAKENED
FIC-FIN-03 STRENGTHENED
FIC-FIN-04 UNCHANGED

delta false reject = 0

delta false accept = 0

positive 6.0/6.5 root cause frozen

FIC-FIN-01 exact generic target frozen BEFORE new output

positive-strength fixtures PASS

negative symmetry PASS

FIC-FIN-05 SELL 6.0 target regression PASS

FIC-FIN-05 UNCHANGED delta target regression PASS

FIC-FIN-08 contrastive exclusion offline replay PASS

financial architecture regressions PASS

business-delta prompt semantics unchanged

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

If the root-cause branch says architecture review is required:

```text
STOP
NO_MODEL_CALLS
```

Do not force another prompt tweak.

---

# 41. New full Sol generation

Only after deterministic gate PASS.

Create a NEW generation.

Do not continue M12Y.

Do not reuse M12Y run-1/context-01 in the formal sample.

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

No source-value changes.

No alias renumbering.

---

# 42. Full topology

Run:

```text
8 subjects

2 shared contexts

4 subjects/context

3 repetitions
```

Total intended:

```text
6 model calls

24 subject outputs
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

# 43. Whole-generation stop rule

On any:

```text
transport failure

timeout

schema failure

hard financial semantic failure

invalid evidence reference

delta-audit semantic failure

frozen target-contract failure
```

stop immediately.

Required:

```text
preserve emitted artifacts

no selective continuation

no failed-context retry

no stitching

wrapper retry = 0
```

Any repair requires a new generation.

---

# 44. Runtime hard gates

Require:

```text
6 / 6 contexts success

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0
```

Report CLI internal retries separately.

---

# 45. Financial hard gates

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

explicit/contrastive exclusion false reject

missing optional context treated as bearish

fixed financial scoring

QTD/YTD false reject

QTD/YTD false accept

AI imperative primary action
```

---

# 46. Business-delta hard gates

For every subject/repetition:

```text
STRENGTHENED / WEAKENED
must resolve through cited aliases
to supplied baseline/comparable change evidence.

UNCHANGED
must be accepted when only absolute current state is supplied.
```

Required:

```text
delta_alias_resolution_failure_count = 0

business_delta_false_reject_count = 0

business_delta_false_accept_count = 0

unsupported_absolute_state_to_delta_count = 0
```

FIC-FIN-05:

```text
target business delta = UNCHANGED
```

for all repetitions unless the frozen source packet is changed,
which is prohibited.

---

# 47. Frozen target-bucket gates

Use targets frozen before the generation.

At minimum:

```text
FIC-FIN-02 =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-04 =
HOLD 5.0:5.0 NEUTRAL

FIC-FIN-05 =
SELL 4.0:6.0
```

FIC-FIN-01:

```text
use the exact M12Z offline-derived target
frozen before model calls.
```

Do not change the target after seeing any new output.

---

# 48. Formal stability

If all 6 contexts complete,
run the unchanged formal classifier.

Report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

No majority vote.

No averaging.

No classifier weakening.

Required:

```text
opposite_direction_reversal_count = 0
```

---

# 49. Core-only stability

For all 8 subjects report:

```text
overall_direction unique count

directional_balance unique count

hold_lean unique count
```

Targeted subjects require:

```text
FIC-FIN-01 balance unique count = 1

FIC-FIN-02 balance unique count = 1

FIC-FIN-04 balance unique count = 1

FIC-FIN-05 balance unique count = 1
```

All must also be contract-consistent.

---

# 50. Stance variance

Measure:

```text
fundamental_new_buyer

fundamental_holder
```

Do not repair in M12Z.

If core + delta become stable but stance remains variable:

```text
fresh_real_proof_readiness = NOT_READY
```

and select the smallest stance follow-up.

---

# 51. Message specificity advisory

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

Do not alter copy solely for advisory quality.

---

# 52. Hosted CI portability

Preserve separate backlog.

M12Y:

```text
5 known historical failures

0 new failures
```

M12Z must introduce:

```text
0 new hosted-CI failures
```

Do not claim hosted CI PASS unless fully green.

---

# 53. Production side-effect firewall

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

Observe approved paused schedules at start/end.

---

# 54. Required deterministic validation artifacts

Produce:

```text
43-focused-test-results

44-full-local-test-results

45-ruff-and-diff-results

46-hosted-ci-portability-observation

47-model-call-gate
```

---

# 55. Required full-canary artifacts

If model-call gate passes:

```text
48-fictional-canary-generation-manifest

49-fictional-canary-source-lock

50-run-1-context-01

51-run-1-context-02

52-run-2-context-01

53-run-2-context-02

54-run-3-context-01

55-run-3-context-02

56-full-fictional-semantic-audit

57-full-fictional-target-bucket-audit

58-full-fictional-business-delta-audit

59-full-fictional-exclusion-audit

60-full-fictional-leverage-audit

61-full-fictional-grounding-audit

62-full-fictional-formal-stability

63-full-fictional-core-only-stability

64-full-fictional-stance-variance

65-full-fictional-runtime-audit

66-full-fictional-message-specificity-advisory
```

For every attempted context preserve:

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

# 56. Required completion artifacts

Produce:

```text
67-delta-alias-resolution-success-decision

68-positive-stronger-bucket-success-decision

69-contrastive-exclusion-full-proof-decision

70-leverage-target-full-proof-decision

71-business-delta-full-proof-decision

72-sol-full-canary-success-decision

73-sol-runtime-real-holdout-suitability

74-core-balance-stability-decision

75-new-buyer-stance-followup-decision

76-holder-stance-followup-decision

77-fresh-real-proof-readiness-decision

78-hosted-ci-portability-handoff

79-astra-future-experiment-handoff

80-production-no-change

81-schedule-pause-observation

82-master-workflow-update

83-program-completion
```

---

# 57. Deterministic acceptance criteria

Before model calls require:

```text
latest M12Y ZIP integrity PASS

Sol runtime frozen healthy

delta canonical/alias resolution repaired

exact M12Y context-01 delta replay fully PASS

delta false reject = 0

delta false accept = 0

positive 6.0/6.5 root cause frozen

FIC-FIN-01 target frozen generically before output

FIC-FIN-05 SELL 6.0 target preserved

FIC-FIN-05 UNCHANGED delta target preserved

FIC-FIN-08 contrastive exclusion repair preserved

financial architecture regressions PASS

threshold/increment/lean/tie-break unchanged

no scorecard

source sufficiency unchanged

Daily Delta unchanged

Price-Timing unchanged

renderer unchanged

focused/full local tests PASS

ruff PASS

git diff --check PASS

production firewall PASS
```

---

# 58. Full-canary acceptance criteria

Require:

```text
6 / 6 Sol contexts complete

24 / 24 schema PASS

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0

hard financial semantic violation = 0

delta alias resolution failure = 0

business delta false reject = 0

business delta false accept = 0

unsupported absolute-state-to-delta = 0

explicit/contrastive exclusion false reject = 0

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

all frozen target buckets contract-consistent

FIC-FIN-05 business delta = UNCHANGED in all repetitions

opposite-direction reversal = 0
```

Formal stability must be measured.

---

# 59. Fresh-real readiness

Set:

```text
fresh_real_proof_readiness = READY
```

only if:

```text
full 6-call Sol proof completes

hard semantics PASS

delta audit PASS

all frozen target buckets stable

formal STABLE = 8

BOUNDARY_UNCERTAINTY = 0

UNSTABLE = 0

business-delta unresolved variance = 0

new-buyer unresolved material variance = 0

holder unresolved material variance = 0

Sol runtime suitable for exposed real holdout

real issuer exposure = 0
```

Then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH
```

Do not start it inside M12Z.

---

# 60. Failure handling

## A. Alias repair fails

```text
next_scope =
BUSINESS_DELTA_EVIDENCE_IDENTITY_ARCHITECTURE_REVIEW
```

No model calls.

## B. Positive bucket contract remains inherently ambiguous

```text
next_scope =
DIRECTIONAL_STRENGTH_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL
```

Do not add another prompt-only line.

## C. Full canary FIC-FIN-01 remains unstable

```text
next_scope =
POSITIVE_STRONGER_BUCKET_STABILITY_REVIEW_GPT56_SOL
```

Do not change target after viewing outputs.

## D. FIC-FIN-05 target fails

```text
next_scope =
LEVERAGE_DIRECTIONAL_CONTRACT_REVIEW_GPT56_SOL
```

## E. Business delta still fails after alias repair

```text
next_scope =
BUSINESS_DELTA_CONTRACT_REPAIR_GPT56_SOL
```

## F. Core/delta stable but stance varies

Use smallest:

```text
BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL

or

BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL
```

## G. Sol runtime fails

```text
next_scope =
SOL_RUNTIME_REGRESSION_REVIEW
```

No Astra fallback.

---

# 61. Production readiness

Even if M12Z passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real GPT-5.6 Sol generalization proof

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

m12y_status
m12z_status

implementation_model_target
implementation_reasoning_effort
investment_judgment_model_target
investment_judgment_reasoning_effort
runner_model_target_match
model_target_fallback_count

delta_alias_resolution_root_cause
delta_alias_resolution_repair_status
delta_validator_false_reject_count
delta_validator_false_accept_count
delta_model_semantic_violation_count

fic_fin_01_positive_bucket_root_cause
fic_fin_01_previous_observations
fic_fin_01_frozen_target
balance_confidence_contract_status
persistence_limit_priority_status
directional_prompt_change_count

fic_fin_05_frozen_target
fic_fin_05_business_delta_target
fic_fin_05_target_change_count
market_expectation_contract_change_count

contrastive_exclusion_repair_status

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
financial_exclusion_validator_semantic_change_count
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

hard_financial_semantic_violation_count
invalid_financial_reference_count
grounding_failure_count

business_delta_alias_resolution_failure_count
business_delta_contract_violation_count
unsupported_absolute_state_to_delta_count

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

# 63. Artifact integrity

Freeze all reports/model artifacts/master workflow before final index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 64. Final task principle

M12Y made two useful discoveries.

First:

```text
FIC-FIN-05's old 5.5 target was too conservative.

The generic leverage contract supports minimum SELL 6.0,
while the lack of refinancing/maturity detail limits stronger severity.
```

Second:

```text
the new business-delta validator itself was wrong.

It compared canonical evidence IDs against an alias-keyed context,
causing valid STRENGTHENED / WEAKENED claims
to be rejected even though the cited raw aliases supported them.
```

The remaining core stability question is FIC-FIN-01:

```text
same Sol model
same source context
same material positive anchors

M12W = 6.5
M12X = 6.5
M12Y = 6.0
```

Do not toggle the test target again based on one output.

The correct flow is:

```text
repair delta evidence identity resolution

→ separate directional balance strength
  from epistemic confidence/Unknown limits

→ freeze the 6.0/6.5 contract generically

→ preserve FIC-FIN-05 SELL 6.0 + UNCHANGED delta

→ preserve FIC-FIN-08 contrastive exclusion

→ run one completely new Sol/xhigh 8 × 3 canary

→ measure core + delta + stance + formal stability

→ only then authorize a fresh unseen real cohort
```

Not:

```text
return to Astra

change the 6.0 threshold

count evidence axes numerically

map MEDIUM confidence mechanically to 6.0

toggle FIC-FIN-01 target after seeing outputs

retry only failed contexts

resume production monitoring
```

Fix evidence identity and decision-strength semantics, then prove the whole system.
