# thesis-monitor — Structured Actionability + Renderer Ownership + Unseen Cold-Start
## End phrase-by-phrase validator tuning on the current 22-subject development cohort
## Move action meaning into structured fields
## Make the renderer own user-facing action wording
## Narrow deterministic prose safety to explicit actionable/deontic language
## Retire USKR22 from tuning immediately
## Prove generalization on a new unseen cohort
## Keep production/live V2 and night-futures integration out of scope until proof completes

---

# 0. Immutable source result

Source report bundle:

```text
thesis-monitor-20260906-nominal-negation-clean-abc-devset-retirement-report.zip
```

SHA-256:

```text
ef76df0ed4eb8c551eaf8827431e3b8d44274da9ecd1a4ac46713e0f231cadc9
```

Frozen generation:

```text
20260906-uskr22-nominal-negation-20260906T010416Z-e45acd16cf43
```

Frozen source lock:

```text
12be1745fa048b04a075a5b965048afaf0d2d9dd1b731c039877436889b39bd0
```

Model / effort:

```text
gpt-5.6-sol / xhigh
```

Frozen result:

```text
FIRST = 22/22
A     = 20/22
B     = NOT_RUN
C     = NOT_RUN

Known hard-safety regression = 0
Future-checkpoint false reject = 0
LEAF schema failure = 0
Unsupported numeric = 0
Production mutation = 0
Main merge = 0
```

A failures were two safe-language false positives:

```text
RXRX:
"두 경로 모두 즉시 진입점이 아니라 임상과 파트너 성과가 동반될 때의 추후 재검토 조건이다."

047810:
"현재 위치의 가격 여유에도 기술적 피로와 분산 수급이 있어 즉시 진입 확신은 부족하다."
```

The source report classified these as validator false positives.

This generation must never be resumed, edited, or selectively rerun.

---

# 1. Architecture decision

Do NOT add:

```text
진입점
확신 부족
매수 매력
추격 이유
진입 타이밍
```

or any new phrase-specific noun/suffix list merely to pass the current cohort.

The repeated pattern now demonstrates an architectural boundary:

```text
free-form AI rationale
→ deterministic code attempts to fully understand arbitrary Korean action wording
→ new safe phrase appears
→ validator vocabulary expands
→ cohort-specific tuning risk increases
```

This loop ends in this task.

---

# 2. Target architecture

Move to:

```text
FACT / EVIDENCE
        ↓
AI substantive judgment
        ↓
STRUCTURED ACTIONABILITY CONTRACT
        ↓
deterministic decision fields
        ↓
THIN ACTION RENDERER
        ↓
user-facing action summary

AI free prose
        ↓
rationale / interpretation only
```

The renderer, not unrestricted prose, owns the primary user-facing action statement.

---

# 3. Preserve the existing decision system

Do not change the existing investment-decision semantics:

```text
overall_direction =
BUY / HOLD / SELL

directional_balance =
BUY + SELL = 10
0.5 increments

BUY when buy >= 6
SELL when sell >= 6
otherwise HOLD

HOLD lean:
5.5:4.5 BUY_LEAN
5.0:5.0 NEUTRAL
4.5:5.5 SELL_LEAN

new_buyer_stance =
ATTRACTIVE / WAIT / AVOID

entry_mode =
PULLBACK / CONFIRMATION / BOTH / NONE

holder_stance =
HOLDABLE / REVIEW / REDUCE
```

Required:

```text
INVESTMENT_DECISION_THRESHOLD_MUTATION = 0
```

This task changes representation/validation ownership, not investment labels.

---

# 4. Structured Actionability Contract

Define a first-class structured contract for every user-facing action context.

Suggested conceptual fields:

```json
{
  "action_subject": "NEW_BUYER | HOLDER | PRICE_REVIEW | NONE",
  "action_stance": "ATTRACTIVE | WAIT | AVOID | HOLDABLE | REVIEW | REDUCE | NONE",
  "entry_mode": "PULLBACK | CONFIRMATION | BOTH | NONE",
  "directive_state": "NO_DIRECTIVE | NEGATED_DIRECTIVE | ACTIONABLE_DIRECTIVE",
  "action_role": "SUMMARY | RATIONALE | PRICE_CONDITION | REVIEW_CONDITION | NONE"
}
```

Exact field names should follow repository conventions.

Important:

```text
directive_state
is NOT the BUY/HOLD/SELL investment decision.
```

It means whether prose contains a user command.

---

# 5. Structured ownership rules

Primary action meaning must come from existing structured decision fields.

Examples:

```text
new_buyer_stance = WAIT
entry_mode = BOTH

→ renderer can safely display:
신규 관찰자: WAIT
진입 방식: 눌림 또는 확인
```

The AI rationale may explain why, but it must not be the authoritative action source.

Similarly:

```text
holder_stance = REVIEW
```

is authoritative over a prose phrase such as:

```text
보유 근거를 재검토할 필요가 있다
```

---

# 6. Renderer ownership

Move the following user-facing components to deterministic rendering:

```text
overall BUY/HOLD/SELL label
BUY:SELL balance
HOLD lean
new-buyer stance
entry mode
holder stance
price review label
business invalidation label
```

AI may still generate:
- business rationale
- earnings interpretation
- valuation interpretation
- expectation interpretation
- risk explanation
- why the structured stance was chosen

But AI does not need to invent the primary action wording.

---

# 7. Thin renderer principle

The renderer must stay thin.

Allowed:

```text
enum → localized label
safe punctuation
numeric formatting
conditional omission
short standardized connective text
```

Forbidden:

```text
new investment reasoning
new risk conclusion
new valuation conclusion
invented price target
invented stop loss
reclassification of BUY/HOLD/SELL
```

The renderer must never upgrade/downgrade a decision.

---

# 8. Action summary should be renderer-owned

Preferred display concept:

```text
판단: HOLD · BUY:SELL 5.5:4.5
신규 관찰자: WAIT · 진입: BOTH
보유자: HOLDABLE
```

Optional short safe explanatory renderer sentence may be generated from enums, e.g.:

```text
현재는 즉시 행동보다 조건 확인이 우선입니다.
```

But this sentence must not be required if it creates localization complexity.
Enum labels alone are sufficient.

---

# 9. Free prose becomes rationale, not command

AI prose fields should be explicitly designated as:

```text
RATIONALE_ONLY
```

or equivalent.

Prompt/schema instruction:

```text
Explain evidence and reasoning.
Do not issue a direct command to the user.
Do not restate the action label as an imperative.
```

Do NOT require the model to avoid ordinary words such as:
- 매수
- 매도
- 진입
- 보유

Those words are legitimate in analysis.

---

# 10. Deterministic prose hard-safety boundary

Stop trying to determine every safe negative/hedged Korean phrase through noun registries.

Hard deterministic prose blocking should focus on high-precision ACTIONABLE patterns.

Examples that must remain blocked:

```text
지금 매수해야 한다
즉시 매수하라
지금 진입하라
반드시 매도해야 한다
전량 매도하라
무조건 매수
지금 비중을 늘려라
```

Examples that should NOT hard-fail merely because they contain action vocabulary:

```text
즉시 진입점이 아니다
즉시 진입 확신은 부족하다
매수 매력은 낮다
추격할 근거가 약하다
매도 명령이 아니다
현재는 진입보다 확인이 중요하다
```

Do not add phrase-specific safe whitelists for these examples.
They are acceptance semantics, not implementation dictionaries.

---

# 11. High-precision deontic/actionable detector

Prefer detecting structures like:

```text
ACTION VERB
+
imperative / obligation / necessity / direct instruction

해야 한다
하라
하십시오
해라
해야만 한다
무조건
반드시
즉시 ... 하라
전량 ... 하라
```

Use tokenizer/clause parsing already available in the repository where possible.

Do not attempt complete Korean semantic parsing.

---

# 12. Contradiction hard gate

Structured action fields and explicit actionable prose may not contradict.

Examples:

```text
structured:
new_buyer_stance = WAIT

prose:
"지금 즉시 매수해야 한다"

→ HARD FAIL
```

```text
structured:
holder_stance = HOLDABLE

prose:
"보유자는 지금 전량 매도하라"

→ HARD FAIL
```

If prose is merely descriptive or negative:

```text
"추격 매력은 낮다"
```

do not infer a new action enum from prose.

---

# 13. Unknown remains non-directional

Preserve:

```text
UNKNOWN != SELL evidence
```

Unknown/insufficient evidence may limit confidence or support WAIT/REVIEW through the structured decision process,
but deterministic prose parsing must not manufacture SELL direction.

---

# 14. Severity/evidence/numeric safety remains unchanged

This task must NOT weaken:
- numeric provenance
- accounting attribution
- security/ADR basis
- evidence identity
- cross-ticker fencing
- cross-generation fencing
- logical condition ownership
- future-checkpoint ownership
- severity ownership
- lifecycle / exactly-once guarantees

Required:

```text
KNOWN_HARD_SAFETY_REGRESSION = 0
```

---

# 15. AI semantic reviewer remains advisory

Do not introduce a universal AI reviewer hard veto in this task.

An AI semantic reviewer may flag:
- subtle contradiction
- confusing wording
- rationale/action mismatch

but initially:

```text
AI_SEMANTIC_REVIEWER_ROLE = ADVISORY
```

Hard gates remain deterministic for:
- facts
- numbers
- provenance
- accounting/security basis
- explicit actionable commands
- structured contradictions
- lifecycle/fencing

---

# 16. Actionability synthetic suite

Before any subject run, create a ticker-free synthetic test suite.

Minimum:

```text
20 explicit ACTIONABLE commands
20 safe descriptive/negative action mentions
10 ambiguous/double-negation cases
10 structured/prose contradiction cases
10 structured/prose consistent cases
```

No real company names.

Required:

```text
ACTIONABLE_TRUE_POSITIVE = 100%
SAFE_ACTION_MENTION_FALSE_POSITIVE = 0
STRUCTURED_CONTRADICTION_DETECTION = PASS
```

If 100% on synthetic actionable commands requires phrase-specific company logic, stop.

---

# 17. Remove current cohort from tuning immediately

Policy change:

```text
USKR22_DEVSET_STATUS =
RETIRED_FROM_TUNING
```

effective at the beginning of this task.

This does NOT mean deleting it.

It means:

```text
the 22 subjects remain regression fixtures
but no new validator/prompt/ontology rule may be added
solely to fix a safe-language failure observed in these 22 subjects.
```

This retirement does not depend on clean A/B/C anymore.

---

# 18. What is allowed after retirement

Allowed:

```text
fix a proven hard-safety regression
fix numeric/accounting/security-basis correctness
fix provider/source corruption
fix a generic schema bug proven independently
```

Forbidden:

```text
add "진입점" because RXRX used it
add "확신 부족" because 047810 used it
change WAIT threshold because the 22 have many WAIT labels
adjust valuation weights to match prior blind review
```

---

# 19. One-shot USKR22 regression audit

After architecture implementation and synthetic tests:

Run the retired USKR22 cohort exactly once as a regression audit.

Purpose:

```text
detect catastrophic regression
not prove generalization
not tune language
```

Required:

```text
USKR22_REGRESSION_RERUN_COUNT = 1
```

If it fails because of a new benign natural-language pattern:

```text
record it
do not patch it in this task
```

If it reveals a true hard-safety regression:

```text
STOP
```

Do not proceed to unseen cohort.

---

# 20. Do not require USKR22 clean A/B/C anymore

The retired 22 cohort is no longer the promotion target.

Do NOT repeat:

```text
FIRST → A → B → C
```

on USKR22 until it is clean by phrase tuning.

One regression run is enough.

Generalization proof moves to unseen data.

---

# 21. Unseen cohort selection must occur after code freeze

Before selecting unseen subjects, freeze:

```text
code tree
prompt
schema
validator
renderer
model
reasoning effort
source eligibility policy
cohort selection algorithm
```

Then select unseen subjects.

No current 22 ticker is eligible.

No subject may be chosen because its expected judgment is known.

---

# 22. Unseen cohort size

Target:

```text
16 unseen securities
```

Allowed range if ingestion limitations require:

```text
12–20
```

Minimum promotable eligible subjects:

```text
12
```

If fewer than 12 can pass objective source-ingestion preflight:

```text
UNSEEN_COLDSTART = NOT_EXECUTABLE_SOURCE_COVERAGE
```

Do not lower evidence standards.

---

# 23. Unseen cohort diversity

Where safely supported, select across distinct economic/valuation frameworks.

Aim for diversity such as:

```text
bank/financial
insurance
consumer
industrial
construction/EPC
software/SaaS
semiconductor/hardware
biotech/healthcare
asset-heavy/cyclical
transport
foreign/ADR
pre-profit growth
```

Do not force an unsupported sector merely to fill quotas.

---

# 24. Objective preflight exclusions

A ticker may be excluded before model generation only for objective reasons such as:

```text
identity unresolved
insufficient required source packet
security basis unresolved where per-share interpretation is required
provider data unavailable
unsupported market/security type
duplicate issuer
```

Record every exclusion.

Do not exclude a ticker because:
- the model may struggle with it
- its valuation is unusual
- expected label is inconvenient

---

# 25. Blind unseen generation

Create:

```text
UNSEEN_GENERATION_ID
```

and source-lock all eligible unseen subjects.

No:
- USKR22 candidate visibility
- old blind decision visibility
- external reviewer label visibility
- desired BUY/HOLD/SELL distribution
- post-result candidate editing

---

# 26. Unseen FIRST gate

Run one fresh FIRST over the unseen eligible cohort.

Do not hotfix.

Classify every result into:

```text
VALIDATED
SOURCE_COVERAGE_LIMIT
ONTOLOGY_GAP
MODEL_SEMANTIC_MISUSE
VALIDATOR_FALSE_POSITIVE
HARD_SAFETY_TRUE_REJECT
ACCOUNTING_OR_SECURITY_BASIS_BLOCK
SCHEMA_FAILURE
```

Important:

```text
a HARD_SAFETY_TRUE_REJECT is not a validator regression
```

---

# 27. Unseen FIRST readiness

Preferred clean outcome:

```text
all eligible subjects validated
hard-safety regression = 0
validator false positive = 0
```

But do not force 100% by repair.

If any false positive or ontology gap occurs:

```text
freeze result
do not patch same generation
```

The result remains valuable generalization evidence.

---

# 28. Unseen A/B/C stability

Only if unseen FIRST has:

```text
validator false positive = 0
schema failure = 0
hard-safety regression = 0
```

and the eligible cohort is complete enough for comparison,

run:

```text
A
B
C
```

with the exact same source lock and frozen architecture.

No run sees another run.

No majority-vote production label.

---

# 29. Unseen stability classification

After clean unseen FIRST/A/B/C:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Measure:
- overall direction
- BUY:SELL balance
- new-buyer stance
- entry mode
- holder stance

A 5.5↔6.0 threshold movement can be legitimate boundary uncertainty.

Do not tune it away.

---

# 30. Generalization verdict

Suggested verdicts:

```text
GENERALIZATION_STRONG
GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY
GENERALIZATION_NEEDS_ARCHITECTURE_WORK
GENERALIZATION_BLOCKED_BY_SOURCE_COVERAGE
```

Do not use raw validation pass rate alone.

Consider:
- false-positive family
- hard-safety behavior
- ontology gaps
- source limits
- stability across runs

---

# 31. No unseen same-generation repair

This is critical.

After unseen results are revealed:

```text
PROMPT_CHANGE = 0
VALIDATOR_CHANGE = 0
RENDERER_CHANGE = 0
ONTOLOGY_CHANGE = 0
SELECTIVE_RERUN = 0
```

Any repair becomes a separately authorized next task and a new unseen cohort.

---

# 32. Do not turn unseen cohort into the next dev set casually

If architecture work is later needed:

- preserve the failed unseen generation
- fix the generic issue using ticker-free synthetic fixtures where possible
- select a NEW unseen holdout for the next proof

Do not repeatedly fit the same unseen subjects.

---

# 33. Action renderer shadow output

Generate shadow user messages for:
- at least 4 retired USKR22 subjects
- at least 4 unseen subjects if available

Choose examples spanning:
- BUY
- HOLD
- SELL
- WAIT
- AVOID
- REVIEW/REDUCE if present

Verify that primary action lines are renderer-owned.

---

# 34. Shadow message acceptance

A rendered stock block should clearly expose structured action information without AI imperative prose.

Example structure:

```text
판단: HOLD · BUY:SELL 5.5:4.5
신규 관찰자: WAIT · 진입: BOTH
보유자: REVIEW

핵심 해석:
<AI rationale>

가격 재점검:
<structured price review context>

기업가치 무효화:
<structured business invalidation context>
```

Exact styling may follow V2 renderer conventions.

---

# 35. Price review vs business invalidation

Preserve strict separation:

```text
price review level != stop-loss
price weakness != automatic SELL
business invalidation != chart invalidation
```

Renderer must not turn a review level into:
- target price
- stop-loss order
- forced sell instruction

---

# 36. Live V2 remains inactive

Current production live messages may continue to use the legacy daily-review format.

That is expected.

This task must NOT activate the new Structured Autonomy renderer in scheduled KR/US delivery.

Required:

```text
LIVE_STRUCTURED_AUTONOMY_ACTIVATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
```

---

# 37. Future live integration acceptance

Prepare a handoff for the later production task that must prove:

```text
scheduled KR/US authoritative job
actually calls
the promoted Structured Autonomy decision source + V2 renderer
```

A CLI/shadow V2 render alone is NOT production activation proof.

Future natural proof must show:
- authoritative scheduled run
- exact renderer identity
- decision-source identity
- exactly-once delivery
- no legacy compatibility path
- no fallback unless explicitly triggered

Do not execute that integration here.

---

# 38. Night futures stays separate

Previous readiness:

```text
READY_FOR_BOUNDED_PRODUCTION_INTEGRATION
```

Keep night-futures code unchanged.

Do not inject night futures into individual-company investment logic.

It remains:
- market context
- timing context
- opening-gap/risk context

not:
- business thesis evidence
- earnings evidence
- valuation evidence

Required:

```text
NIGHT_FUTURES_CODE_MUTATION = 0
```

---

# 39. Production mutation policy

This entire task is shadow/research only.

Required:

```text
MAIN_MERGE = 0
PRODUCTION_DB_MUTATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
LIVE_STRUCTURED_AUTONOMY_ACTIVATION = 0
NIGHT_FUTURES_PRODUCTION_MUTATION = 0
```

---

# 40. Maximum readiness from this task

If synthetic, retired-cohort regression, unseen FIRST/A/B/C, and hard safety are clean:

```text
STRUCTURED_AUTONOMY_READINESS =
READY_FOR_PRODUCTION_INTEGRATION_REVIEW
```

Not deployed.

If unseen results expose generic architecture weakness:

```text
NEEDS_ARCHITECTURE_WORK
```

If only objective source coverage blocks the cohort:

```text
BLOCKED_BY_SOURCE_COVERAGE
```

---

# 41. Required reports

Create:

1. `docs/reports/20260906-structured-actionability-root-cause.md`
2. `docs/reports/20260906-structured-actionability-contract.md`
3. `docs/reports/20260906-action-renderer-ownership-contract.md`
4. `docs/reports/20260906-actionability-hard-validator-boundary.md`
5. `docs/reports/20260906-actionability-synthetic-suite.md`
6. `docs/reports/20260906-uskr22-devset-retirement.md`
7. `docs/reports/20260906-uskr22-one-shot-regression.md`
8. `docs/reports/20260906-unseen-cohort-selection.md`
9. `docs/reports/20260906-unseen-source-preflight.md`
10. `docs/reports/20260906-unseen-first.md`
11. `docs/reports/20260906-unseen-run-a.md`
12. `docs/reports/20260906-unseen-run-b.md`
13. `docs/reports/20260906-unseen-run-c.md`
14. `docs/reports/20260906-unseen-stability.md`
15. `docs/reports/20260906-generalization-audit.md`
16. `docs/reports/20260906-action-renderer-shadow-proof.md`
17. `docs/reports/20260906-hard-safety-regression.md`
18. `docs/reports/20260906-production-integration-next-handoff.md`
19. `docs/reports/20260906-night-futures-no-change-handoff.md`
20. `docs/reports/20260906-program-completion.md`
21. `docs/reports/20260906-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 42. Machine-readable proofs

Create:

```text
structured-actionability-contract.json
action-renderer-ownership.json
actionability-synthetic-suite.json
uskr22-devset-retirement.json
uskr22-regression.json
unseen-cohort-selection.json
unseen-source-preflight.json
unseen-first.json
unseen-run-a.json
unseen-run-b.json
unseen-run-c.json
unseen-stability.json
generalization-audit.json
action-renderer-shadow-proof.json
hard-safety-regression.json
production-integration-handoff.json
night-futures-no-change.json
program-completion.json
```

---

# 43. Required gates

```text
SOURCE_REPORT_BUNDLE_SHA256 =
ef76df0ed4eb8c551eaf8827431e3b8d44274da9ecd1a4ac46713e0f231cadc9

SOURCE_GENERATION_RESUME =
0 / NONZERO

USKR22_DEVSET_STATUS =
RETIRED_FROM_TUNING / OTHER

ACTIONABILITY_PRIMARY_OWNER =
STRUCTURED_FIELDS / PROSE / OTHER

PRIMARY_USER_ACTION_WORDING_OWNER =
RENDERER / AI_PROSE / OTHER

INVESTMENT_DECISION_THRESHOLD_MUTATION =
0 / NONZERO

AI_SEMANTIC_REVIEWER_ROLE =
ADVISORY / HARD_GATE / NONE

ACTIONABLE_TRUE_POSITIVE =
100% / OTHER

SAFE_ACTION_MENTION_FALSE_POSITIVE =
0 / NONZERO

STRUCTURED_CONTRADICTION_DETECTION =
PASS / FAIL

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO

USKR22_REGRESSION_RERUN_COUNT =
1 / OTHER

USKR22_POST_RESULT_TUNING =
0 / NONZERO

UNSEEN_SELECTION_AFTER_FREEZE =
PASS / FAIL

UNSEEN_SELECTED_COUNT =
...

UNSEEN_ELIGIBLE_COUNT =
...

UNSEEN_CURRENT_DEVSET_OVERLAP =
0 / NONZERO

UNSEEN_FIRST_VALIDATED =
...

UNSEEN_FIRST_VALIDATOR_FALSE_POSITIVE =
0 / NONZERO

UNSEEN_FIRST_HARD_SAFETY_TRUE_REJECT =
...

UNSEEN_FIRST_ONTOLOGY_GAP =
...

UNSEEN_FIRST_SOURCE_COVERAGE_LIMIT =
...

UNSEEN_RUN_A_VALIDATED =
... / NOT_RUN

UNSEEN_RUN_B_VALIDATED =
... / NOT_RUN

UNSEEN_RUN_C_VALIDATED =
... / NOT_RUN

UNSEEN_STABLE_COUNT =
... / NOT_MEASURED

UNSEEN_BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

UNSEEN_UNSTABLE_COUNT =
... / NOT_MEASURED

GENERALIZATION_VERDICT =
GENERALIZATION_STRONG /
GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY /
GENERALIZATION_NEEDS_ARCHITECTURE_WORK /
GENERALIZATION_BLOCKED_BY_SOURCE_COVERAGE

ACTION_RENDERER_SHADOW =
PASS / FAIL

LIVE_STRUCTURED_AUTONOMY_ACTIVATION =
0 / NONZERO

NIGHT_FUTURES_CODE_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

STRUCTURED_AUTONOMY_READINESS =
READY_FOR_PRODUCTION_INTEGRATION_REVIEW /
NEEDS_ARCHITECTURE_WORK /
BLOCKED_BY_SOURCE_COVERAGE /
NOT_READY
```

---

# 44. Stop conditions

STOP if:
- RXRX/047810/WULF or any current ticker gets a phrase-specific exception
- action vocabulary is expanded merely to pass USKR22
- renderer invents investment reasoning
- structured BUY/HOLD/SELL thresholds change
- explicit actionable commands stop being caught
- safe descriptive action mentions still trigger a hard gate in the synthetic suite
- a true hard-safety regression appears in the retired-cohort one-shot regression
- unseen cohort selection occurs before architecture freeze
- an unseen result is repaired in the same generation
- unseen subjects overlap the retired 22
- night futures are injected into company investment logic
- production scheduled delivery is modified

---

# 45. Completion response

Return:

```text
STRUCTURED ACTIONABILITY =
primary owner
schema
directive semantics

ACTION RENDERER =
owned user-facing fields
thin-renderer proof

PROSE HARD SAFETY =
synthetic true positives
safe false positives
contradiction proof

USKR22 =
retired from tuning
one-shot regression result
post-result tuning = 0

UNSEEN COHORT =
selection
source eligibility
subject count

UNSEEN FIRST =
...

UNSEEN A/B/C =
...

GENERALIZATION =
...

HARD SAFETY =
...

ACTION RENDERER SHADOW =
...

LIVE V2 =
not activated

NIGHT FUTURES =
unchanged

PRODUCTION MUTATION =
0

READINESS =
...

NEXT PRODUCTION INTEGRATION HANDOFF =
...

REPORT ZIP =
...

ZIP SHA256 =
...
```

---

# 46. Final principle

The system must not need to understand every possible Korean phrase before it can safely judge a stock.

Instead:

```text
structured fields own action meaning
renderer owns primary user action wording
AI owns substantive investment reasoning
deterministic validators own truth, evidence, numbers, accounting and explicit commands
```

The current 22-subject cohort is now a regression set, not a language-training set.

The next proof of quality must come from unseen tickers.
