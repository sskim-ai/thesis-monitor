# thesis-monitor — Nominal Negation Scope Repair + Clean A/B/C + Dev-Set Retirement
## Repair exactly one newly exposed generic Korean negation scope defect
## Preserve actionable-trade hard safety
## Run a completely new US14+KR8 generation
## Require FIRST 22/22 → A 22/22 → B 22/22 → C 22/22
## If clean, retire the current 22-subject cohort from further tuning
## Prepare the next unseen-ticker cold-start proof without changing production

---

# 0. Immutable source result

Source report bundle:

```text
thesis-monitor-20260906-bounded-validator-generalization-clean-abc-proof-report.zip
```

SHA-256:

```text
6ea876ee720c830fc59cd745a002960d83cb27d90abc634a58128c5d9fabf276
```

Source generation:

```text
20260906-uskr22-validator-generalization-20260905T234949Z-6347e07b3702
```

Source result:

```text
FIRST = 21/22
A = NOT_RUN
B = NOT_RUN
C = NOT_RUN

STOP_STATE = STOPPED_FIRST_GATE
```

Single FIRST failure:

```text
WULF
mandatory_trade_language
audited classification =
NOMINAL_NEGATION_SCOPE_FALSE_POSITIVE
```

Observed safe sentence shape:

```text
두 가격 경로 모두 즉시 매수 신호가 아니며
준공과 청구 확대가 확인된 뒤에만 재고할 조건이다.
```

The source generation is permanently frozen.

Required:

```text
SOURCE_GENERATION_RESUME = 0
SOURCE_CANDIDATE_EDIT = 0
SOURCE_CANDIDATE_REUSE = 0
```

---

# 1. What is already proven — do not reopen without regression evidence

The previous bounded work already proved:

```text
same-severity selected-evidence metric union = PASS
packet-wide metric union = NOT USED
cross-severity union accepted = 0

probability token boundary = PASS
"상승률" vs "승률" false positive = 0

direct negated trade language = PASS

future-checkpoint false reject = 0
LEAF schema failure = 0
unsupported numeric = 0
cross-ticker evidence = 0
cross-generation evidence = 0
known hard-safety regression = 0

focused tests = 274 passed
full pytest = 2465 passed
Ruff = PASS
git diff --check = PASS
```

Do not rewrite those systems just because one new nominal-negation form appeared.

---

# 2. Scope of this task

This task may change only what is necessary to model generic clause-level nominal negation.

The defect is:

```text
trade action token
+
nominal predicate head
+
explicit copular negation
```

Example semantic structure:

```text
[즉시 매수] [신호] [가 아니다]
```

The current validator sees the trade token but fails to bind the later negation to the whole nominal predicate.

This is NOT a WULF-specific problem.

---

# 3. Explicit anti-overfit prohibition

Forbidden fixes:

```text
if ticker == "WULF"
exact source-sentence whitelist
"신호가 아니며" exact-string whitelist
"매수 신호" whitelist
per-company prompt instruction
post-result candidate rewrite
global mandatory-trade validator disable
```

Required:

```text
TICKER_SPECIFIC_EXCEPTION = 0
EXACT_SOURCE_PHRASE_WHITELIST = 0
GLOBAL_TRADE_SAFETY_WEAKENING = 0
```

---

# 4. Do NOT change the writer merely to avoid the phrase

The WULF candidate was semantically safe.

Therefore:

```text
WRITER_PROMPT_CHANGE_FOR_WULF_WORDING = 0
```

Do not teach the model to avoid:
- "신호가 아니다"
- "명령이 아니다"
- "조건이 아니다"

The validator must correctly understand safe bounded negation.

Writer changes are permitted only if an unrelated generic contract defect is independently proven before the new experiment freeze.
Otherwise leave the writer unchanged.

---

# 5. Target trade-language semantic model

Preserve:

```text
ACTIONABLE
NEGATED
DESCRIPTIVE
NONE
```

Add or strengthen clause-level scope ownership so that a trade-action mention can be negated through a nominal predicate.

Conceptually:

```text
ACTION_TERM
→ optional modifiers
→ nominal predicate phrase
→ explicit negation operator
```

Examples of nominal predicate roles may include semantic classes such as:

```text
signal
instruction
reason
condition
basis
recommendation
entry trigger
exit trigger
```

Do not implement this as a WULF noun list only.

Use the repository's existing tokenizer / semantic-role architecture where available.

---

# 6. Required safe-negation forms

The following semantic forms should be recognized as `NEGATED` when the negation clearly governs the trade-action proposition:

```text
즉시 매수 신호가 아니다
즉시 매수 신호는 아니다
즉시 매수 신호가 아니며 향후 재검토 조건이다
지금 매도하라는 명령이 아니다
매수의 근거가 아니다
매수 조건은 아니다
자동 매도 조건이 아니다
즉시 진입 사유가 아니다
```

English equivalents, if the validator is multilingual, should also remain safe:

```text
not a buy signal
not an instruction to sell
not an immediate entry condition
```

Do not require English expansion if the current validator has a separate established English path.

---

# 7. Clause boundary is critical

Negation applies only to the clause it actually governs.

Must remain actionable / fail-closed:

```text
즉시 매수 신호가 아니지만 지금은 매수해야 한다

매도 명령은 아니나 보유자는 전량 매도하라

자동 매수 신호가 아니다. 다만 지금 즉시 매수한다

매수 신호가 아니라고 보긴 어렵다
```

The last example is epistemically/double-negation ambiguous.

Fail closed unless the parser can safely prove negation.

Required:

```text
LATER_ACTIONABLE_DIRECTIVE_DETECTED = PASS
DOUBLE_NEGATION_FAIL_CLOSED = PASS
```

---

# 8. Negation scope must not cross punctuation blindly

Do not let one negative predicate suppress later independent clauses.

At minimum preserve boundaries around:

```text
sentence termination
semicolon
strong contrast conjunction
independent imperative/deontic clause
```

Use actual repository tokenization conventions.

Do not build a general Korean NLP engine in this task.

Keep the repair bounded.

---

# 9. Semantic precedence

Recommended precedence:

```text
1. explicit structured trade-language semantics, if trusted and evidence-safe
2. clause-aware deterministic semantic parsing
3. conservative lexical fallback
```

A `NEGATED` clause may coexist with a later `ACTIONABLE` clause.

Overall hard-safety result in that case:

```text
ACTIONABLE
```

---

# 10. Synthetic anti-overfit matrix before any model call

Before a new model generation, build a ticker-free synthetic test corpus.

No real ticker names.

Minimum matrix:

```text
>= 12 safe NEGATED examples
>= 12 true ACTIONABLE examples
>= 6 DESCRIPTIVE/NONE examples
>= 6 adversarial contrast/double-negation examples
```

Include lexical variation across:
- buy / sell / enter / exit
- signal / condition / basis / instruction / reason
- direct negation / nominal negation
- one-clause / multi-clause

Required:

```text
SYNTHETIC_NEGATION_MATRIX_PASS = 1
```

---

# 11. Historical regression examples are secondary

After the generic synthetic matrix passes, verify historical forms:

```text
"즉시 매수가 아닌 ..."
→ NEGATED

"즉시 매수 신호가 아니며 ..."
→ NEGATED

"즉시 매수"
→ ACTIONABLE

"반드시 매도"
→ ACTIONABLE
```

The exact WULF sentence may be included as a historical regression fixture only after the generic matrix exists.

Required:

```text
HISTORICAL_FIXTURE_IS_PRIMARY_IMPLEMENTATION_TARGET = 0
```

---

# 12. Hard-safety test matrix

Re-run the full known hard-safety families:

```text
unsupported numeric
numeric semantic mismatch
nonexistent evidence ref
cross-ticker evidence ref
cross-generation evidence ref
accounting attribution
ADR/share basis
valuation eligibility
severity escalation
Unknown causal-driver invention
logical OR→AND mutation
logical AND→OR mutation
mandatory actionable trade language
terminal lifecycle / exactly-once safety
```

Required:

```text
KNOWN_HARD_SAFETY_REGRESSION = 0
```

---

# 13. Preserve previous generic repairs

Explicitly re-test:

```text
IBM-style same-severity selected-evidence metric union
GOOGL-style unowned strengthening severity
MU-style 상승률 / 승률 boundary
SNDK/TSLA-style direct negation
benign action-wrapper repetition
material substantive repetition
future-checkpoint ownership
LEAF discriminated-union schema
```

Required:

```text
METRIC_UNION_FALSE_REJECT = 0
UNOWNED_STRENGTHENING_SEVERITY_ACCEPTED = 0
PROBABILITY_LANGUAGE_FALSE_POSITIVE = 0
DIRECT_NEGATION_FALSE_POSITIVE = 0
FUTURE_CHECKPOINT_FALSE_REJECT = 0
LEAF_SCHEMA_FAILURE = 0
```

---

# 14. No investment-judgment tuning

Do not modify:

```text
BUY / HOLD / SELL thresholds
BUY:SELL balance rules
HOLD lean rules
new-buyer stance rules
holder stance rules
entry-mode rules
valuation framework weighting
market-expectation weighting
Unknown directional policy
```

Required:

```text
INVESTMENT_JUDGMENT_LOGIC_CHANGED = 0
```

The previous decision distributions are not targets.

---

# 15. Freeze the experiment before model calls

After code/tests pass, record:

```text
current main SHA
working branch SHA
implementation SHA
prompt hash
writer hash
validator hash
renderer hash
schema hash
source packet hashes
model
reasoning effort
```

Then freeze.

After freeze:

```text
PROMPT_MUTATION_AFTER_FREEZE = 0
VALIDATOR_MUTATION_AFTER_FREEZE = 0
BUILDER_MUTATION_AFTER_FREEZE = 0
RENDERER_MUTATION_AFTER_FREEZE = 0
```

---

# 16. Create a completely new generation

Do not resume:

```text
20260906-uskr22-validator-generalization-20260905T234949Z-6347e07b3702
```

Create a new generation ID.

Use the current production-equivalent model and reasoning effort.

Expected currently:

```text
gpt-5.6-sol / xhigh
```

but resolve from runtime instead of hardcoding if operating config changed.

---

# 17. Fresh source lock

Build one source cohort for:

```text
US14 + KR8 = 22 subjects
```

Freeze it before FIRST.

All subsequent A/B/C must use the exact same source lock.

No run-to-run market or price refresh.

Required:

```text
SOURCE_LOCK_DRIFT_ACROSS_FIRST_ABC = 0
```

---

# 18. FIRST gate

Run FIRST once.

Required:

```text
FIRST_VALIDATED = 22/22
```

If FIRST != 22:

```text
STOP
```

No:
- selective rerun
- candidate edit
- same-generation hotfix
- prompt patch
- validator patch

Return frozen failure evidence.

---

# 19. A/B/C gate

Only if FIRST = 22/22.

Run:

```text
A = 22/22
B = 22/22
C = 22/22
```

All runs use:
- same source lock
- same model
- same effort
- same prompt
- same schema
- same validator
- same renderer
- same code tree

No run sees another run's output.

---

# 20. Stop policy

```text
FIRST fail → stop before A
A fail → stop before B
B fail → stop before C
C fail → freeze C failure
```

No repair inside the same generation.

This is mandatory.

---

# 21. Required run taxonomy

For FIRST/A/B/C record:

```text
validated_count
mandatory_trade_false_positive
actionable_trade_true_positive
nominal_negation_false_positive
direct_negation_false_positive
probability_language_false_positive
metric_union_false_reject
unowned_severity_true_reject
future_checkpoint_false_reject
LEAF_schema_failure
unsupported_numeric
accounting_security_basis_failure
cross_ticker_evidence
cross_generation_evidence
material_substantive_repetition
benign_action_wrapper_repetition
```

---

# 22. Stability only after clean A/B/C

Do not calculate stability on partial cohorts.

Only after all four full runs complete:

```text
FIRST = 22
A = 22
B = 22
C = 22
```

calculate:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Also report:
- direction switches
- BUY:SELL spread
- new-buyer stance switches
- holder stance switches
- entry-mode switches

No majority-vote production decision.

---

# 23. Judgment diagnostics remain advisory

Observe only:

```text
HOLD basin
WAIT frequency
ATTRACTIVE frequency
Unknown handling
cyclical valuation weighting
ADR uncertainty
high-expectation valuation weighting
business quality vs entry timing separation
HOLDABLE vs REVIEW separation
```

Do NOT change decision rules in this task.

---

# 24. Dev-set retirement gate

The current 22-subject cohort has served as the development/regression cohort repeatedly.

If and only if:

```text
FIRST 22/22
A 22/22
B 22/22
C 22/22
KNOWN_HARD_SAFETY_REGRESSION = 0
```

then declare:

```text
USKR22_DEVSET_STATUS =
RETIRED_FROM_TUNING
```

Meaning:

```text
the 22 subjects remain regression fixtures
but future validator/prompt design may no longer be changed
merely to fit a failure observed only in this cohort
```

This is an explicit anti-overfit transition.

---

# 25. What "retired from tuning" means

Allowed later:

```text
generic ontology repair proven on unseen data
hard-safety regression fix
accounting/security-basis correctness fix
source/provider correctness fix
```

Not allowed later:

```text
change rule because MU output looks undesirable
change threshold because CRCL label differs from reviewer
add WULF wording exception
adjust WAIT frequency to preferred distribution
```

---

# 26. Prepare unseen-ticker cold-start handoff

Do NOT execute unseen-ticker tuning in this task.

If clean A/B/C succeeds, create a next-task handoff for a blind unseen cohort.

The unseen protocol must require:

```text
code/prompt/validator frozen before ticker selection is revealed to the model run

no current 22 ticker may appear in the unseen cohort

no prior blind-review labels

no desired BUY/HOLD/SELL distribution

no post-result repair inside the cold-start generation
```

Recommended cohort size:

```text
12–20 unseen securities
```

with diverse business types where the existing generic pipeline already supports source ingestion.

---

# 27. Unseen cohort category diversity

The handoff should seek diversity such as:

```text
bank
insurance
consumer
industrial
construction/EPC
software/SaaS
semiconductor or hardware
biotech
asset-heavy/cyclical
transport
foreign/ADR if safely supported
pre-profit growth
```

Do not force categories that the current source pipeline cannot safely ingest.

Pipeline support is a prerequisite.

---

# 28. Unseen test success criterion

Do not define success as 100% arbitrary pass at any cost.

Classify failures into:

```text
SOURCE_COVERAGE_LIMIT
ONTOLOGY_GAP
MODEL_SEMANTIC_MISUSE
VALIDATOR_FALSE_POSITIVE
HARD_SAFETY_TRUE_REJECT
ACCOUNTING_OR_SECURITY_BASIS_BLOCK
```

The purpose is to measure generalization, not to make every unseen ticker pass.

---

# 29. Night futures — no change in this task

Previous result:

```text
NIGHT_FUTURES_READINESS =
READY_FOR_BOUNDED_PRODUCTION_INTEGRATION
```

Provider support:

```text
KRX official archive/history path
PARTIAL
```

Do not modify night-futures code in this task unless a regression is found.

Required:

```text
NIGHT_FUTURES_CODE_MUTATION = 0
```

Keep its next production integration independent from Structured Autonomy.

---

# 30. Live production remains untouched

Current live messages may still use the legacy daily-review renderer.

That is expected until a later explicit production integration task.

This task must not activate Structured Autonomy in scheduled live delivery.

Required:

```text
STRUCTURED_AUTONOMY_PRODUCTION_ACTIVATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
PRODUCTION_DB_MUTATION = 0
MAIN_MERGE = 0
```

---

# 31. Promotion readiness

Maximum Structured Autonomy verdict in this task:

```text
READY_FOR_UNSEEN_COLD_START
```

not production deployment.

Only if:

```text
FIRST 22
A 22
B 22
C 22
hard-safety regression 0
nominal-negation false positive 0
```

Otherwise:

```text
NEEDS_MORE_SHADOW_WORK
```

---

# 32. Required reports

Create:

1. `docs/reports/20260906-nominal-negation-root-cause.md`
2. `docs/reports/20260906-nominal-negation-scope-contract.md`
3. `docs/reports/20260906-negation-anti-overfit-matrix.md`
4. `docs/reports/20260906-negation-hard-safety-regression.md`
5. `docs/reports/20260906-experiment-freeze.md`
6. `docs/reports/20260906-fresh-first.md`
7. `docs/reports/20260906-run-a.md`
8. `docs/reports/20260906-run-b.md`
9. `docs/reports/20260906-run-c.md`
10. `docs/reports/20260906-abc-stability.md`
11. `docs/reports/20260906-judgment-diagnostic-audit.md`
12. `docs/reports/20260906-devset-retirement.md`
13. `docs/reports/20260906-unseen-coldstart-next-handoff.md`
14. `docs/reports/20260906-night-futures-no-change-handoff.md`
15. `docs/reports/20260906-promotion-readiness.md`
16. `docs/reports/20260906-artifact-index.md`

Use actual completion date if the run crosses dates.

---

# 33. Required machine-readable proofs

Create:

```text
nominal-negation-proof.json
negation-anti-overfit-matrix.json
hard-safety-regression.json
experiment-freeze.json
fresh-first.json
run-a.json
run-b.json
run-c.json
abc-stability.json
judgment-diagnostics.json
devset-retirement.json
unseen-coldstart-handoff.json
night-futures-no-change.json
promotion-readiness.json
```

---

# 34. Required gates

```text
SOURCE_REPORT_SHA256 =
6ea876ee720c830fc59cd745a002960d83cb27d90abc634a58128c5d9fabf276

SOURCE_GENERATION_RESUME =
0 / NONZERO

TICKER_SPECIFIC_EXCEPTION =
0 / NONZERO

EXACT_SOURCE_PHRASE_WHITELIST =
0 / NONZERO

WRITER_PROMPT_CHANGE_FOR_WULF_WORDING =
0 / NONZERO

TRADE_NEGATION_MODEL =
CLAUSE_AWARE / OTHER

SYNTHETIC_NEGATION_MATRIX_PASS =
1 / 0

LATER_ACTIONABLE_DIRECTIVE_DETECTED =
PASS / FAIL

DOUBLE_NEGATION_FAIL_CLOSED =
PASS / FAIL

HISTORICAL_FIXTURE_IS_PRIMARY_IMPLEMENTATION_TARGET =
0 / NONZERO

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO

METRIC_UNION_FALSE_REJECT =
0 / NONZERO

UNOWNED_STRENGTHENING_SEVERITY_ACCEPTED =
0 / NONZERO

PROBABILITY_LANGUAGE_FALSE_POSITIVE =
0 / NONZERO

DIRECT_NEGATION_FALSE_POSITIVE =
0 / NONZERO

NOMINAL_NEGATION_FALSE_POSITIVE =
0 / NONZERO

FUTURE_CHECKPOINT_FALSE_REJECT =
0 / NONZERO

LEAF_SCHEMA_FAILURE =
0 / NONZERO

INVESTMENT_JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

NEW_GENERATION_ID =
...

SOURCE_LOCK_DRIFT_ACROSS_FIRST_ABC =
0 / NONZERO

FIRST_VALIDATED =
22 / OTHER

RUN_A_VALIDATED =
22 / OTHER / NOT_RUN

RUN_B_VALIDATED =
22 / OTHER / NOT_RUN

RUN_C_VALIDATED =
22 / OTHER / NOT_RUN

STABLE_COUNT =
... / NOT_MEASURED

BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

UNSTABLE_COUNT =
... / NOT_MEASURED

USKR22_DEVSET_STATUS =
RETIRED_FROM_TUNING /
ACTIVE_REGRESSION_ONLY /
NOT_RETIRED

UNSEEN_COLDSTART_HANDOFF =
READY / NOT_READY

NIGHT_FUTURES_CODE_MUTATION =
0 / NONZERO

STRUCTURED_AUTONOMY_PRODUCTION_ACTIVATION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

STRUCTURED_AUTONOMY_READINESS =
READY_FOR_UNSEEN_COLD_START /
NEEDS_MORE_SHADOW_WORK /
NOT_READY
```

---

# 35. Stop conditions

Stop if:
- WULF ticker or exact sentence is special-cased
- trade hard safety is globally weakened
- a negation clause suppresses a later actionable directive
- double negation is treated as safely negated without proof
- writer prompt is changed merely to avoid the failing wording
- FIRST != 22
- A != 22
- B != 22
- C != 22
- any same-generation hotfix is proposed
- any decision threshold is tuned
- night futures are injected into company judgment
- production live path is modified

---

# 36. Completion response

Return:

```text
NOMINAL NEGATION REPAIR =
...

ANTI-OVERFIT MATRIX =
...

HARD SAFETY =
...

FIRST =
...

A =
...

B =
...

C =
...

STABILITY =
...

JUDGMENT DIAGNOSTICS =
...

DEVSET RETIREMENT =
...

UNSEEN COLD-START HANDOFF =
...

NIGHT FUTURES =
unchanged / regression

PRODUCTION MUTATION =
0

MAIN MERGE =
0

READINESS =
...

REPORT ZIP =
...

ZIP SHA256 =
...
```

---

# 37. Final principle

This is the last allowed language-generalization repair driven by the current 22-subject development cohort before the cohort is retired from tuning, if clean A/B/C succeeds.

The validator should be:

```text
strict about actionability
strict about evidence and numbers
strict about severity and accounting

but capable of understanding
a bounded, explicit negation
without mistaking "not a buy signal"
for "buy now"
```

After clean A/B/C, generalization must be proven on unseen tickers rather than by further fitting this cohort.
