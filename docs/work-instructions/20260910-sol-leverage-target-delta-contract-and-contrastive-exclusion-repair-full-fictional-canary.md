# Thesis Monitor — Sol Leverage Target/Delta Contract + Contrastive Exclusion Repair & Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260910-sol-leverage-target-delta-contract-and-contrastive-exclusion-repair-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260910-sol-leverage-target-delta-contract-contrastive-exclusion-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12Y — GPT-5.6 Sol / xhigh
       A. Contrastive Financial-Sector Exclusion Validator Repair
       B. FIC-FIN-05 Leverage Exact-Target Contract Review
       C. Absolute-State vs Business-Delta Contract Repair
       D. Full Fictional Financial Canary
```

This task begins after M12X.

M12X established:

```text
GPT-5.6 Sol runtime restoration = healthy

FIC-FIN-01 old 6.0 target = over-constrained

FIC-FIN-01 new generic target = BUY 6.5:3.5

run-1/context-01 = semantic PASS

run-1/context-02 = transport PASS but semantic FAIL
```

M12Y must NOT follow the M12X generated handoff:

```text
SOL_RUNTIME_REGRESSION_REVIEW
```

because the preserved runtime receipts show:

```text
context-01 ≈ 389.98 sec PASS

context-02 ≈ 313.49 sec PASS

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0

CLI internal retry = 0
```

There was no Sol runtime regression.

The actual M12X blockers are:

```text
FIC-FIN-08:
explicit contrastive sector-framework exclusion
was falsely rejected by the financial semantic validator

FIC-FIN-05:
observed SELL 4.0:6.0
vs frozen HOLD 4.5:5.5 target

FIC-FIN-05:
business_thesis_change = WEAKENED
despite the fixture containing current absolute leverage weakness
but no explicit baseline deterioration
```

M12Y is a bounded semantic-contract task.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260910-positive-stronger-bucket-contract-review-full-sol-fictional-canary-report.zip
```

Verified SHA-256:

```text
828e0ac45bae7fd095907cf6db2e11c0333f3d30e87e94a4a6beb566ac38aff8
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Artifact integrity independently verified:

```text
artifact-index payloads = 217
ZIP entries including artifact-index = 218

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

Recompute before trusting the bundle.

---

# 2. M12X repository provenance

Reported:

```text
branch =
codex/20260910-positive-stronger-bucket-m12x

base_sha =
079213d7ff730c1d9eb60fca3b06b404ff34f0e5

work_instruction_commit =
239b799a1361b8ad8168aef2310f03eaf8fc641e

implementation_commit =
7b1407eab18182defc3bafc261064008a65e20c1

report_commit =
ee0d30900ff643804596c27c88f34c358ae0bf8f
```

Use actual repository HEAD at task start.

Record:

```text
actual_branch
actual_head
working_tree_state
remote_branch_sha
```

If unexplained drift exists in:

```text
Directional ordinal contract
M12U market-expectation rule
financial-sector validator
business_thesis_change semantics
fictional source packet
Sol runtime
```

STOP:

```text
UNEXPLAINED_M12Y_BASELINE_DRIFT
```

---

# 3. Model target remains Sol

Proof-critical target:

```text
model = gpt-5.6-sol

reasoning = xhigh
```

Default Codex authoring/review target:

```text
gpt-5.6-sol / xhigh
```

Required:

```text
runner_model_target_match = true

model_target_fallback_count = 0
```

No:

```text
GPT-6 Astra fallback

alternative GPT fallback

reasoning downgrade
```

If actual investment runner differs:

```text
STOP
SOL_RUNNER_MODEL_TARGET_MISMATCH
```

---

# 4. Sol runtime is frozen healthy

M12X new generation:

```text
run-1/context-01:
389.976433 sec PASS

run-1/context-02:
313.492384 sec PASS
```

Both:

```text
gpt-5.6-sol / xhigh

1800-sec watchdog

4 subjects/context

MODEL_CONTEXT_COUPLED

wrapper retry = 0

timeout = 0

orphan = 0
```

M12Y must not perform a runtime-regression review.

Keep:

```text
timeout = 1800

subjects/context = 4

wrapper retry = 0

batch split = 0
```

If Sol itself later times out:

```text
STOP
next_scope = SOL_RUNTIME_REGRESSION_REVIEW
```

---

# 5. M12X deterministic result — FIC-FIN-01 is closed

M12X independently froze:

```text
root cause =
EXACT_FIXTURE_TARGET_OVERCONSTRAINED

previous target =
BUY 6.0:4.0

new target =
BUY 6.5:3.5

directional prompt change =
0
```

Reason:

```text
distinct current operating improvement
+
reported cash-conversion improvement
+
net-cash resilience

materially exceed minimum BUY support.

Valuation/persistence Unknowns and expectation/competition cautions
limit stronger conviction but do not make 6.0 and 6.5
genuinely adjacent under the existing contract.
```

This is now frozen.

Do not reopen FIC-FIN-01 in M12Y.

---

# 6. M12X first-context observed core outputs

Preserved:

```text
FIC-FIN-01 =
BUY 6.5:3.5
→ new target PASS

FIC-FIN-02 =
HOLD 4.5:5.5 SELL_LEAN
→ target PASS

FIC-FIN-03 =
HOLD 5.5:4.5 BUY_LEAN
→ not enough repetitions to judge stability

FIC-FIN-04 =
HOLD 5.0:5.0 NEUTRAL
→ target PASS
```

Do not infer repeated stability from one observation.

FIC-FIN-03 is not an M12Y pre-model repair target unless deterministic semantics reveal a separate hard defect.

---

# 7. M12X second-context actual blockers

Preserved output:

## FIC-FIN-05

```text
overall_direction = SELL

directional_balance = 4.0 : 6.0

business_thesis_change = WEAKENED

new buyer = AVOID

holder = REDUCE

transport = PASS

financial grounding = PASS
```

M12X target audit:

```text
expected = HOLD 4.5:5.5 SELL_LEAN

observed = SELL 4.0:6.0

status = FAIL
```

## FIC-FIN-08

```text
overall_direction = HOLD 5.0:5.0

sector logic itself = insurance-appropriate

actual industrial-framework application = not observed

validator errors =
net_debt_claim_without_complete_net_debt_evidence
financial_sector_generic_reasoning
```

M12X generation stopped after context-02.

Formal repeated stability:

```text
NOT_MEASURED
```

---

# 8. Issue A — exact FIC-FIN-08 wording

Preserved sector interpretation:

```text
"보험사이므로 산업회사식 순부채와 운전자본 틀 대신
언더라이팅과 규제자본을 본다."
```

This is contrastive replacement:

```text
industrial-company net-debt/WC framework
→ NOT the applied framework

underwriting + regulatory capital
→ applied framework
```

The validator incorrectly treated the mention of:

```text
순부채
운전자본
```

as actual application/assertion.

This is another explicit non-application false reject.

---

# 9. Issue A root cause class

Freeze one generic root cause before implementation.

Expected candidate:

```text
CONTRASTIVE_REPLACEMENT_EXCLUSION_NOT_RECOGNIZED
```

Alternative allowed classifications:

```text
NET_DEBT_SCANNER_BYPASSES_SHARED_EXCLUSION_SCOPE

FINANCIAL_SECTOR_SCANNER_BYPASSES_SHARED_EXCLUSION_SCOPE

MIXED

OTHER_BOUNDED_EXCLUSION_DEFECT
```

The forensic report must identify:

```text
which validator/scanner emitted each error

whether both use one shared assertion/exclusion classifier

whether "X 대신 Y" reaches that classifier

whether net-debt and financial-sector scans apply the same scope result
```

No code change before this is frozen.

---

# 10. Generic contrastive-exclusion contract

Support bounded contrastive non-application semantics such as:

```text
X 대신 Y를 본다

X보다 Y를 사용한다

X가 아니라 Y를 본다

X보다는 Y가 적절한 평가틀이다

rather than X, use Y

use Y instead of X

X is not the relevant framework; Y is

not X but Y
```

ONLY when the sentence actually means:

```text
X is excluded / not applied
and
Y is the replacement framework
```

Do not treat every occurrence of:

```text
대신
rather than
instead
```

as exclusion.

---

# 11. Exclusion contradiction controls

Must still FAIL:

```text
"순부채 대신 규제자본을 보지만
순부채가 높아 SELL 근거다."

"산업회사 틀은 적용하지 않지만
운전자본 악화가 핵심 투자 리스크다."

"X 대신 Y" appears in an unrelated clause,
while another material field actually applies X.

material_directional_anchor_basis
contains unsupported industrial net-debt evidence
despite an exclusion sentence elsewhere.
```

An exclusion sentence must not immunize actual misuse.

---

# 12. Shared exclusion-scope requirement

The following checks must use a consistent assertion/application scope:

```text
net-debt claim validator

financial-sector generic-framework validator

working-capital generic-framework validator
```

If they currently classify exclusion independently,
prefer one bounded shared helper/contract.

Do not broadly refactor unrelated semantic validators.

Required:

```text
exclusion_scope_semantics_consistent = true
```

---

# 13. FIC-FIN-08 offline regression

After repair,
replay the exact preserved M12X FIC-FIN-08 output.

Expected:

```text
net_debt_claim_without_complete_net_debt_evidence = 0

financial_sector_generic_reasoning = 0
```

ONLY because:

```text
the industrial framework is explicitly contrastively excluded.
```

All genuine misuse negative controls must still fail.

---

# 14. Issue B — FIC-FIN-05 source packet

Frozen evidence:

```text
E01:
Current operating profit is positive and broadly stable.

E02:
No safe current valuation multiple is supplied.

E03:
A high complete debt balance and thin cash buffer reduce resilience.

E04:
A standard operating-company debt and liquidity framework applies.

E05:
complete interest-bearing debt total = 900

E06:
cash and cash equivalents = 40

E07:
Expectations do not appear to allow for a prolonged refinancing burden.

E08:
Refinancing terms and maturity concentration are not supplied.

E09:
The business remains profitable,
but balance-sheet resilience constrains optionality.
```

Financial values are in the frozen fictional packet.

Do not invent:

```text
debt/EBITDA
interest coverage
maturity wall
covenant stress
```

---

# 15. Issue B — preserved Sol reasoning

Sol M12X candidate said:

```text
"확인된 높은 부채와 얇은 현금 완충력이
안정적 영업수익보다 방향 판단에 더 중요하다."
```

Material anchor basis:

```text
E03
E05
E06
```

Market expectation:

```text
E07 + E03
```

Sell drivers:

```text
high complete debt + thin cash

market expectation does not appear to allow
for prolonged refinancing burden
```

Risk limitation:

```text
refinancing terms and maturity concentration are absent,
limiting additional negative strengthening.
```

This reasoning is internally coherent with:

```text
minimum SELL = 6.0
stronger SELL >6.0 blocked by unresolved refinancing detail
```

M12Y must audit the target, not assume the model is wrong.

---

# 16. Cross-model descriptive evidence for FIC-FIN-05

Historical GPT-6 Astra M12T also produced:

```text
SELL 4.0:6.0
```

on the same broad evidence pattern.

This is:

```text
CROSS_MODEL_DESCRIPTIVE_ONLY
```

not proof that 6.0 is correct.

But it is relevant evidence that the existing 5.5 exact fixture target
may be over-constrained.

Do not use model agreement as ground truth.

Use the generic contract.

---

# 17. Current generic 5.5 / 6.0 negative contract

Frozen Directional ladder:

```text
4.5:5.5 =
negative issuer-level material anchor exists,
but missing corroboration/currentness/persistence/valuation/
critical KPI support prevents full negative direction.

4.0:6.0 =
minimum SELL,
requiring a negative issuer-level material anchor
plus sufficiently current or independent corroboration;
unresolved counterevidence must not keep the case at lean-only.

3.5:6.5 and stronger =
progressively stronger corroboration/persistence/quality/
visibility/valuation support.
```

Tie-break:

```text
if the same evidence genuinely fits adjacent buckets,
choose the less directional bucket toward 5.0.
```

M12Y must derive FIC-FIN-05 target from this rule.

---

# 18. Debt + cash economic-independence question

Determine whether:

```text
complete high debt
+
thin cash
```

in this packet represent:

```text
A. one financial-resilience proposition with two components

B. a material leverage anchor plus sufficiently current corroboration

C. two distinct economic axes

D. context-dependent
```

Do not decide by reference count.

Consider:

```text
E03 is a narrative synthesis of E05/E06,
not automatically independent.

E05/E06 are both current point-in-time financial facts.

Debt and cash jointly establish balance-sheet resilience.

Stable operating profit is real counterevidence.

Refinancing severity remains Unknown.
```

No fixed score.

---

# 19. Market-expectation contract remains frozen

M12U classification remains:

```text
CONDITIONAL_ON_SAME_UNRESOLVED_RISK
```

E07 does NOT automatically supply an independent axis
for minimum SELL when its downside depends on
the same materially unresolved refinancing burden.

Do not change this contract in M12Y.

However:

```text
FIC-FIN-05 may still support 6.0
from the balance-sheet evidence itself
without counting E07 independently.
```

This must be the core target question.

---

# 20. FIC-FIN-05 target root-cause classification

Freeze exactly one:

```text
EXACT_FIXTURE_TARGET_OVERCONSTRAINED_EXPECT_6_0

MODEL_CONTRACT_VIOLATION_EXPECT_5_5

GENERIC_5_5_6_0_LEVERAGE_CONTRACT_UNDERSPECIFIED

MIXED

OTHER
```

Do not freeze a target until this is completed.

---

# 21. Branch A — 5.5 target was over-constrained

If:

```text
EXACT_FIXTURE_TARGET_OVERCONSTRAINED_EXPECT_6_0
```

then:

```text
change the FIC-FIN-05 derived fixture target only

HOLD 4.5:5.5
→
SELL 4.0:6.0
```

Do NOT change:

```text
6.0 threshold
market-expectation independence contract
Directional prompt
```

Document why:

```text
current complete leverage evidence itself
meets minimum negative direction,
while unresolved refinancing detail caps stronger severity.
```

No ticker-specific production logic.

---

# 22. Branch B — 5.5 remains correct

If:

```text
MODEL_CONTRACT_VIOLATION_EXPECT_5_5
```

and the current generic prompt already clearly expresses the rule,
do NOT add another prompt-only line.

Set:

```text
STOP
NO_MODEL_CALLS

next_scope =
LEVERAGE_EVIDENCE_RELATION_ARCHITECTURE_REVIEW
```

Reason:

```text
the same prompt-only contract has already been violated
by more than one model family.
```

Do not force model output via repeated wording changes.

---

# 23. Branch C — leverage contract genuinely under-specified

If:

```text
GENERIC_5_5_6_0_LEVERAGE_CONTRACT_UNDERSPECIFIED
```

one bounded generic ordinal clarification is allowed.

It must answer:

```text
when complete debt + thin cash constitute
minimum-direction corroboration

vs

when they remain one unresolved financial-resilience dimension
limited to 5.5.
```

No formulas.

No leverage score.

No required debt/cash numerical threshold unless an existing sector contract already contains one.

Then derive the FIC-FIN-05 exact target from that generic rule.

---

# 24. Issue C — absolute current state vs business delta

The M12X FIC-FIN-05 output used:

```text
business_thesis_change = WEAKENED
```

But the frozen source packet contains:

```text
current high debt

current thin cash

current stable operating profit

current Unknown refinancing terms/maturity
```

It does NOT supply:

```text
prior-period debt deterioration

cash deterioration

new covenant breach

new refinancing shock

new margin deterioration

a prior baseline from which the business thesis weakened
```

M12Y must audit this independently.

---

# 25. Business-delta root-cause classification

Freeze exactly one:

```text
ABSOLUTE_NEGATIVE_STATE_MISREAD_AS_WEAKENING_DELTA

SOURCE_PACKET_ACTUALLY_SUPPLIES_DETERIORATION

BUSINESS_DELTA_CONTRACT_UNDERSPECIFIED

OTHER
```

Expected default from current evidence is NOT precommitted.

Use the actual packet.

---

# 26. Generic business-delta contract

If the source audit confirms only current absolute state,
freeze or clarify the generic rule:

```text
business_thesis_change is a change assessment,
not an absolute quality label.

STRENGTHENED / WEAKENED requires supplied evidence
of a meaningful change relative to a prior/baseline state.

A negative current condition alone does not mean WEAKENED.

A positive current condition alone does not mean STRENGTHENED.

When the packet supplies only current absolute state
and no directional baseline change,
use UNCHANGED unless another supplied fact establishes change.
```

Do not make:

```text
UNCHANGED = good
```

It only means:

```text
no supported change.
```

This is separate from absolute BUY/HOLD/SELL.

---

# 27. Business-delta positive fixtures

At minimum:

## DELTA-01

```text
high debt and thin cash current state
no prior/baseline change evidence
→ UNCHANGED
```

## DELTA-02

```text
high debt worsened materially vs prior supplied baseline
→ WEAKENED may be supported
```

## DELTA-03

```text
strong current margins
no prior/baseline change
→ not automatically STRENGTHENED
```

## DELTA-04

```text
operating + cash-conversion improvement
explicitly versus prior comparable period
→ STRENGTHENED may be supported
```

## DELTA-05

```text
current neutral condition
with newly confirmed structural deterioration
→ WEAKENED may be supported
```

No fixed scoring.

---

# 28. Absolute Directional direction remains separate

Hard freeze:

```text
absolute_direction
!=
business_thesis_change
```

Valid combinations can include:

```text
SELL + UNCHANGED

BUY + UNCHANGED

HOLD + WEAKENED

HOLD + STRENGTHENED
```

if supplied evidence supports them.

Do not mechanically map:

```text
BUY → STRENGTHENED

SELL → WEAKENED
```

---

# 29. New-buyer / holder stance remain separate

Do not repair:

```text
ATTRACTIVE / WAIT / AVOID

HOLDABLE / REVIEW / REDUCE
```

in M12Y.

Measure them in the full canary.

If they remain variable after core/delta stability:

```text
fresh_real_proof_readiness = NOT_READY
```

and choose a separate bounded stance repair.

---

# 30. FIC-FIN-01 target remains frozen 6.5

Hard regression:

```text
FIC-FIN-01 =
BUY 6.5:3.5
```

under the existing frozen strong-quality packet.

Do not revert to 6.0.

Do not modify source data.

---

# 31. FIC-FIN-02 / 04 frozen targets

Preserve:

```text
FIC-FIN-02 =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-04 =
HOLD 5.0:5.0 NEUTRAL
```

unless the generic FIC-FIN-05 leverage clarification has a proven cross-case implication.

Do not silently shift unrelated cases.

---

# 32. Financial semantic freeze

Required unchanged except Issue A exclusion scope:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

financial-context selected-only projection

materiality-scoped WC grounding

QTD/YTD Korean period validator

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

market_expectation_contract_change_count = 0
```

---

# 33. Threshold / calibration freeze

Required unchanged:

```text
BUY threshold = 6.0

SELL threshold = 6.0

increment = 0.5

HOLD 5.5:4.5 BUY_LEAN

HOLD 5.0:5.0 NEUTRAL

HOLD 4.5:5.5 SELL_LEAN

adjacent tie-break toward 5.0
```

No:

```text
fixed scorecard

evidence-count bucket rule

majority vote

balance averaging
```

---

# 34. Runtime freeze

Use exactly:

```text
model = gpt-5.6-sol

reasoning = xhigh

MODEL_CONTEXT_COUPLED

4 subjects/context

1800-second watchdog

single authoritative watchdog

wrapper retry = 0

batch split = 0
```

No Astra calls.

No runtime changes.

---

# 35. Phase A forensic gate

Before implementation produce and freeze:

```text
FIC-FIN-08 exact scanner root cause

shared exclusion-scope decision

FIC-FIN-05 5.5-vs-6.0 target root cause

FIC-FIN-05 derived exact target

FIC-FIN-05 business-delta root cause

business-delta generic contract decision
```

No code/fixture/prompt changes before these are frozen.

---

# 36. Phase B implementation boundary

Allowed:

```text
contrastive exclusion validator repair

shared assertion/exclusion scope helper if bounded

FIC-FIN-05 fixture target correction
if Branch A

one bounded generic leverage ordinal clarification
if Branch C only

one bounded business-delta clarification
if the existing prompt does not already express the frozen rule
```

Forbidden:

```text
another market-expectation prompt tweak

financial schema expansion

new financial parser

source-provider work

output schema change

Price-Timing change

renderer change
```

---

# 37. Exclusion deterministic fixtures

At minimum:

## PASS

```text
"산업회사식 순부채와 운전자본 틀 대신
언더라이팅과 규제자본을 본다."

"일반 부채틀이 아니라 규제자본을 본다."

"use regulatory capital instead of industrial net debt."

"rather than industrial working capital,
evaluate underwriting and capital."
```

## FAIL

```text
actual unsupported net-debt assertion

actual industrial WC assertion for insurer

contrastive exclusion sentence + later actual use

unsupported industrial metric in material anchor

ambiguous/double-negative contrast
```

Required:

```text
false reject = 0
false accept = 0
```

---

# 38. Leverage deterministic fixtures

After target root-cause freeze create:

## LEV-SOL-01

Exact FIC-FIN-05 generic pattern:

```text
complete high debt
thin cash
stable operating profit
refinancing severity Unknown
conditional market expectation
```

Expected:

```text
exactly one frozen 5.5 or 6.0 outcome
```

## LEV-SOL-02

```text
same balance-sheet stress
+
confirmed refinancing stress
```

Stronger negative direction may be supported.

## LEV-SOL-03

```text
high debt
+
strong cash/liquidity
+
stable operation
```

No mechanical SELL.

## LEV-SOL-04

```text
partial debt only
```

No complete-debt conclusion.

## LEV-SOL-05

```text
financial sector
```

Industrial leverage contract not applicable.

No numeric score.

---

# 39. Business-delta deterministic fixtures

Run DELTA-01 through DELTA-05.

Required:

```text
absolute-negative-state-only does not become WEAKENED

absolute-positive-state-only does not become STRENGTHENED

explicit comparable-period improvement/deterioration may support change
```

Do not use ticker branches.

---

# 40. Phase C deterministic validation

Before model calls require:

```text
latest ZIP integrity PASS

Sol runtime healthy/frozen

FIC-FIN-01 6.5 target regression PASS

FIC-FIN-02 target regression PASS

FIC-FIN-04 target regression PASS

FIC-FIN-08 contrastive exclusion replay PASS

exclusion positive fixtures PASS

exclusion negative fixtures rejected

FIC-FIN-05 target root cause frozen

FIC-FIN-05 exact target frozen

LEV-SOL fixtures PASS

business-delta contract frozen

DELTA fixtures PASS

no scorecard

threshold/increment/lean/tie-break unchanged

financial architecture regressions PASS

market-expectation contract unchanged

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

If Branch B says the model structurally cannot obey a clear 5.5 contract:

```text
STOP
NO_MODEL_CALLS
```

and use the architecture handoff.

---

# 41. New full Sol generation

Only after Phase C PASS.

Create a NEW generation.

Do not continue M12X.

Do not stitch M12X run-1 output into the sample.

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

No source/case-value changes.

---

# 42. Full topology

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

No real issuer calls.

No judge calls.

---

# 43. Whole-generation stop rule

On any:

```text
transport failure

timeout

schema failure

hard financial semantic failure

exclusion validator failure

frozen target-bucket failure

business-delta semantic hard failure
```

stop immediately.

Required:

```text
preserve outputs

no selective continuation

no failed-context retry

no sample stitching

wrapper retry = 0
```

A later repaired proof uses a NEW generation.

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

CLI internal retries must be reported separately.

---

# 45. Financial hard gates

Require zero:

```text
invalid financial refs

material financial grounding failures

WC grounding failures

narrative substitution failures

price/technical/supply Directional refs

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

true financial-sector industrial misuse

explicit/contrastive exclusion false reject

missing optional context treated as bearish

fixed financial scoring

QTD/YTD false reject

QTD/YTD false accept

AI imperative primary action
```

---

# 46. Frozen target-bucket gates

Use exact post-forensic targets:

```text
FIC-FIN-01 =
BUY 6.5:3.5

FIC-FIN-02 =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-04 =
HOLD 5.0:5.0 NEUTRAL

FIC-FIN-05 =
the exact target frozen by M12Y forensic review
```

All 3 repetitions for each targeted subject must match.

Do not modify the target after observing new outputs.

---

# 47. Business-delta hard audit

For every subject/repetition,
audit:

```text
does STRENGTHENED / WEAKENED
have supplied change/baseline evidence?
```

Required:

```text
unsupported_absolute_state_to_delta_count = 0
```

For FIC-FIN-05,
if the source packet remains current-state-only,
all 3 repetitions must not infer WEAKENED solely from current leverage weakness.

Freeze the exact expected delta status before the generation.

---

# 48. Formal stability

If all 6 contexts complete,
run the unchanged classifier:

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
opposite-direction reversal = 0
```

---

# 49. Core-only stability

Report:

```text
overall direction unique count

directional balance unique count

HOLD lean unique count
```

for all 8 subjects.

Targeted subjects require:

```text
unique balance count = 1
```

---

# 50. Stance variance

Measure:

```text
fundamental_new_buyer

fundamental_holder
```

for all subjects.

Do not repair in M12Y.

If core + delta are stable but stance variance remains:

```text
fresh_real_proof_readiness = NOT_READY
```

and choose the smallest stance follow-up.

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

Do not change copy solely for advisory quality.

---

# 52. Hosted CI portability

Preserve:

```text
HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR
```

M12X hosted CI:

```text
3261 passed
5 known failures
0 new M12X failures
```

M12Y must introduce:

```text
new hosted-CI failure count = 0
```

Do not broaden into portability cleanup.

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

# 54. Required provenance/integrity artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12y-scope-freeze

04-sol-runtime-freeze

05-m12x-next-scope-correction
```

Artifact 05 must state:

```text
M12X next_scope=SOL_RUNTIME_REGRESSION_REVIEW
is not supported by its own runtime receipts.

Actual blockers are semantic.
```

---

# 55. Required FIC-FIN-08 artifacts

Produce:

```text
06-fic-fin-08-m12x-output-forensic

07-exclusion-scanner-path-audit

08-contrastive-exclusion-root-cause

09-shared-exclusion-scope-contract

10-contrastive-exclusion-validator-before-after

11-exclusion-positive-fixtures

12-exclusion-negative-fixtures

13-fic-fin-08-exact-offline-replay
```

---

# 56. Required FIC-FIN-05 leverage artifacts

Produce:

```text
14-fic-fin-05-source-packet-freeze

15-fic-fin-05-m12x-output-forensic

16-cross-model-fic-fin-05-descriptive-only

17-current-negative-5-5-6-0-contract

18-debt-cash-economic-independence-audit

19-market-expectation-contract-reuse-proof

20-fic-fin-05-target-root-cause

21-fic-fin-05-derived-target

22-lev-sol-01

23-lev-sol-02

24-lev-sol-03

25-lev-sol-04

26-lev-sol-05
```

---

# 57. Required business-delta artifacts

Produce:

```text
27-fic-fin-05-business-delta-source-audit

28-business-delta-root-cause

29-absolute-state-vs-delta-contract

30-delta-01

31-delta-02

32-delta-03

33-delta-04

34-delta-05

35-fic-fin-05-derived-delta-target
```

---

# 58. Required freeze/no-change artifacts

Produce:

```text
36-fic-fin-01-6-5-target-freeze

37-fic-fin-02-target-freeze

38-fic-fin-04-target-freeze

39-first-class-financial-evidence-freeze

40-working-capital-validator-freeze

41-qtd-ytd-validator-freeze

42-market-expectation-independence-freeze

43-threshold-increment-lean-tiebreak-freeze

44-source-sufficiency-no-change

45-daily-delta-no-change

46-price-timing-no-change

47-renderer-ownership-no-change
```

---

# 59. Required deterministic validation artifacts

Produce:

```text
48-focused-test-results

49-full-local-test-results

50-ruff-and-diff-results

51-hosted-ci-portability-observation

52-model-call-gate
```

---

# 60. Required full-canary artifacts

If deterministic gate passes:

```text
53-fictional-canary-generation-manifest

54-fictional-canary-source-lock

55-run-1-context-01

56-run-1-context-02

57-run-2-context-01

58-run-2-context-02

59-run-3-context-01

60-run-3-context-02

61-full-fictional-semantic-audit

62-full-fictional-target-bucket-audit

63-full-fictional-contrastive-exclusion-audit

64-full-fictional-leverage-target-audit

65-full-fictional-business-delta-audit

66-full-fictional-grounding-audit

67-full-fictional-formal-stability

68-full-fictional-core-only-stability

69-full-fictional-stance-variance

70-full-fictional-runtime-audit

71-full-fictional-message-specificity-advisory
```

Preserve for every attempted call:

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

# 61. Required completion artifacts

Produce:

```text
72-contrastive-exclusion-success-decision

73-leverage-target-success-decision

74-business-delta-success-decision

75-sol-full-canary-success-decision

76-sol-runtime-real-holdout-suitability

77-core-balance-stability-decision

78-new-buyer-stance-followup-decision

79-holder-stance-followup-decision

80-fresh-real-proof-readiness-decision

81-hosted-ci-portability-handoff

82-astra-future-experiment-handoff

83-production-no-change

84-schedule-pause-observation

85-master-workflow-update

86-program-completion
```

---

# 62. Deterministic acceptance criteria

Before model calls:

```text
latest M12X ZIP integrity PASS

Sol runtime freeze PASS

FIC-FIN-08 contrastive-exclusion root cause frozen

FIC-FIN-08 exact output offline replay PASS after repair

exclusion false accept = 0

exclusion false reject = 0

FIC-FIN-05 exact target root cause frozen

FIC-FIN-05 exact target frozen generically

market-expectation contract unchanged

FIC-FIN-05 business-delta root cause frozen

absolute-state vs delta contract frozen

FIC-FIN-05 exact delta target frozen

FIC-FIN-01 6.5 target regression PASS

FIC-FIN-02 target regression PASS

FIC-FIN-04 target regression PASS

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

# 63. Full-canary acceptance criteria

Require:

```text
6 / 6 Sol contexts complete

24 / 24 schema PASS

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0

hard financial semantic violation = 0

explicit/contrastive exclusion false reject = 0

financial-sector true misuse = 0

grounding failures = 0

QTD/YTD false reject = 0

QTD/YTD false accept = 0

unsupported absolute-state-to-delta = 0

price/technical/supply violations = 0

AI imperative primary action = 0

FIC-FIN-01 balance unique count = 1

FIC-FIN-02 balance unique count = 1

FIC-FIN-04 balance unique count = 1

FIC-FIN-05 balance unique count = 1

all exact target buckets contract-consistent

all exact delta targets contract-consistent

opposite-direction reversal = 0
```

Formal stability must be measured.

---

# 64. Fresh-real readiness

Set:

```text
fresh_real_proof_readiness = READY
```

only if:

```text
full Sol proof complete

hard semantics PASS

all frozen target buckets stable

business-delta semantics stable

formal STABLE = 8

BOUNDARY_UNCERTAINTY = 0

UNSTABLE = 0

new-buyer stance has no unresolved material variance

holder stance has no unresolved material variance

Sol runtime suitable for exposed real holdout

real issuer exposure = 0
```

Then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH
```

Do not start the real proof inside M12Y.

---

# 65. Failure handling

## A. FIC-FIN-05 target review concludes 5.5 is clearly correct
but prompt already clearly expresses it

```text
STOP
NO_MODEL_CALLS

next_scope =
LEVERAGE_EVIDENCE_RELATION_ARCHITECTURE_REVIEW
```

No another prompt-only tweak.

## B. Contrastive exclusion still false-rejects

```text
next_scope =
FINANCIAL_EXCLUSION_SCOPE_VALIDATOR_REPAIR_V3
```

## C. Business delta remains unsupported/variable

```text
next_scope =
BOUNDED_BUSINESS_DELTA_CONTRACT_REPAIR_GPT56_SOL
```

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

## F. Sol runtime fails

```text
next_scope =
SOL_RUNTIME_REGRESSION_REVIEW
```

Do not return to Astra automatically.

---

# 66. Production readiness

Even if M12Y passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real GPT-5.6 Sol generalization proof

production integration review

explicit user authorization
```

Production monitoring remains paused.

---

# 67. Program-completion fields

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

m12x_status
m12y_status

m12x_reported_next_scope
m12x_next_scope_correction

implementation_model_target
implementation_reasoning_effort
investment_judgment_model_target
investment_judgment_reasoning_effort
runner_model_target_match
model_target_fallback_count

contrastive_exclusion_root_cause
contrastive_exclusion_repair_status
exclusion_false_reject_count
exclusion_false_accept_count

fic_fin_05_leverage_target_root_cause
fic_fin_05_previous_target
fic_fin_05_frozen_target
fic_fin_05_target_change_reason
fic_fin_05_market_expectation_contract_changed

fic_fin_05_business_delta_root_cause
fic_fin_05_business_delta_target
business_delta_prompt_change_count
unsupported_absolute_state_to_delta_count

directional_prompt_change_count
fixture_target_change_count

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
business_delta_contract_violation_count

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

Anything not measured:

```text
NOT_MEASURED
```

---

# 68. Artifact integrity

Freeze all reports/model artifacts/master workflow before final index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 69. Final task principle

M12X answered the FIC-FIN-01 question correctly:

```text
the test target was too strict,
not the model.
```

The same discipline now applies to FIC-FIN-05.

Do not assume:

```text
HOLD 5.5 is correct because an earlier offline review froze it.
```

Do not assume:

```text
SELL 6.0 is correct because Astra and Sol both emitted it.
```

Instead:

```text
derive the exact target from the generic economic contract.
```

At the same time:

```text
"산업회사식 순부채 틀 대신 보험업 틀을 본다"
must be recognized as explicit non-application,
not as an unsupported net-debt claim.
```

And:

```text
a bad absolute current condition
must not automatically become
business_thesis_change = WEAKENED
without supplied delta evidence.
```

The correct flow is:

```text
fix the contrastive exclusion scope

→ re-audit FIC-FIN-05 5.5 vs 6.0 without model-label anchoring

→ separate absolute state from business delta

→ freeze exact generic targets

→ keep Sol/xhigh runtime unchanged

→ run one completely new 8 × 3 full fictional canary

→ measure core + delta + stance + formal stability

→ only then move to the fresh real cohort
```

Not:

```text
run a runtime review

force old fixture labels

add another market-expectation prompt tweak

score debt/cash numerically

return to Astra

continue only the unfinished repetition

resume production monitoring
```

The contract must determine the test, not the test determine the contract.
