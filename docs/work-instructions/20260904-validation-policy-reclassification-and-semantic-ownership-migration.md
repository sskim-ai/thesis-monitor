# thesis-monitor — Validation Policy Reclassification + Semantic Ownership Migration
## Stop natural-language regex overfitting
## Keep factual/accounting/provenance/lifecycle safety hard
## Move style/repetition/linguistic variation to soft quality
## Introduce structured semantic ownership so code does not re-parse Korean prose
## Shadow only — no production decision/send mutation in this task

---

# 0. Source context

Primary recent evidence bundle:

```text
file =
thesis-monitor-20260904-kr-v2-child-wait-ownership-repair-report-bundle.zip

sha256 =
bfeda2112578e507890f49a802dcbd432d4db5c7ed9335118280ea9d2503240c
```

Recent system state:

```text
KR explicit V2 real TEST:
market 1 + stock V2 8/8
Pilot 0
fallback 0
duplicate 0

KR V2 child runtime:
1092.99 sec
passed historical premature-interrupt boundary 168.3 sec

US shared model path:
14/14 ACCEPTED

US delivery:
0

US block reason:
combined quality / repeated typed prose
```

The current task is NOT to patch the US repeated sentence directly.

It is to determine which validation rules should:
- remain deterministic hard safety
- remain hard only for unambiguous semantic contradictions
- become soft quality / rewrite-only
- be replaced by structured semantic ownership

---

# 1. Problem statement

The validator has accumulated rules that sometimes infer meaning by parsing
natural-language surface forms.

Observed incident classes have included:

```text
"수주가 ... 회복"
misread as
"주가 ... 회복"

"자동 매도보다 재평가"
misread as
mandatory sell

"ROIC가 개선되면"
"향후 ROIC가 회복돼야"
"ROIC 악화로 이어질 수 있다"
misread as unsupported/current metric claim

generic business words:
가격
지지
회복
support-like terms

cross-ticker repeated sentence skeletons
treated as production-hard quality failure
```

These are not all equal in safety importance.

The architecture must distinguish:

```text
factual safety
from
semantic contradiction
from
stylistic quality
```

---

# 2. Non-negotiable principle

Do NOT "relax validation" globally.

Instead:

```text
RECLASSIFY OWNERSHIP
```

The desired architecture is:

```text
Fact Registry / Numeric Registry
        ↓
AI Semantic Planner
        ↓
AI Writer
        ↓
Deterministic Hard Safety Validator
        ↓
AI Semantic Reviewer / Soft Quality Reviewer
        ↓
Thin Renderer
        ↓
Delivery
```

The deterministic validator should not have to reverse-engineer the
meaning of free Korean prose when the AI can provide the intended
structured semantics directly.

---

# 3. Three validation classes

Every existing rule must be classified exactly once.

## CLASS A — HARD_DETERMINISTIC

Production fail-closed.

Examples:

```text
nonexistent evidence ref
cross-ticker evidence ref
cross-generation evidence ref
wrong fact_id / field_path
unsupported numeric value
wrong numeric semantic/unit
currency/security-basis mismatch
ADR/share-basis error
parent/common attribution error
unsafe EPS/BVPS reconstruction
PER/PBR denominator safety
claim/fencing violation
stale ownership
duplicate delivery
terminal state overwrite
schema corruption
```

These remain deterministic and strict.

---

## CLASS B — SEMANTIC_HARD

Production fail-closed only when contradiction or unsupported assertion is
unambiguous.

Examples:

```text
overall BUY
+
explicit mandatory "즉시 전량 매도"

"현재 ROIC 15%"
with no current ROIC evidence

"실적이 개선됐다"
when packet explicitly says decline

"현재 PBR 3.2배"
bound to a PER field
```

These should preferably rely on:
- structured claim metadata
- structured decision fields
- evidence ownership

not keyword-only prose parsing.

---

## CLASS C — SOFT_QUALITY

Does NOT block a factually safe message by default.

Examples:

```text
cross-ticker repeated wording
stylistic similarity
boilerplate repetition
verbosity
sentence skeleton reuse
linguistic variation
awkward phrasing
non-material redundancy
```

Policy:

```text
soft warning
or
bounded rewrite once
```

If rewrite fails but the original message is factually/semantically safe:

```text
delivery remains eligible
```

unless the text crosses into a Class A/B violation.

---

# 4. Mandatory full validator inventory

Do not start by editing the currently failing repetition rule.

First inventory every production/shadow validator that can affect:

```text
candidate acceptance
message quality
numeric/provenance
valuation
accounting
price semantics
supply semantics
holder/new-buyer semantics
trade-language semantics
confirmation/business-condition semantics
renderer/template quality
delivery eligibility
```

For each rule record:

```text
rule_id
file
function
regex/parser/schema field
current severity
current owner
what risk it protects against
known incident(s)
false-positive history
false-negative risk
proposed class
proposed owner
production gate impact
```

Required:

```text
VALIDATOR_RULES_INVENTORIED = 100%
UNCLASSIFIED_RULES = 0
```

---

# 5. Hard-rule preservation audit

For each proposed Class A rule, prove that the redesign does NOT weaken:

```text
numeric provenance
Fact identity
accounting attribution
Valuation basis
security basis
ADR ratio direction
currency basis
period comparability
claim ownership
fencing
exactly-once delivery
terminal-state immutability
```

Required:

```text
FACTUAL_SAFETY_REGRESSION = 0
ACCOUNTING_SAFETY_REGRESSION = 0
LIFECYCLE_SAFETY_REGRESSION = 0
```

---

# 6. Structured semantic ownership

Introduce or prototype a structured claim contract.

The model should emit meaning metadata alongside prose.

Example native equivalent:

```json
{
  "claim_id": "C12",
  "claim_type": "FUTURE_VALIDATION_CONDITION",
  "topic": "capital_efficiency",
  "metrics": ["FCF", "ROIC"],
  "direction": "IMPROVE",
  "evidence_refs": ["E05", "E08"],
  "text": "CAPEX가 실제 현금창출과 ROIC 개선으로 이어지는지를 확인해야 합니다."
}
```

The exact schema may differ.

Required semantic dimensions should support at least:

```text
CURRENT_FACT
CURRENT_NUMERIC_FACT
HISTORICAL_FACT
FUTURE_VALIDATION_CONDITION
RISK_CONDITION
BUSINESS_INVALIDATION_CONDITION
PRICE_REVIEW_CONDITION
VALUATION_INTERPRETATION
MARKET_EXPECTATION_INTERPRETATION
HOLDER_REASSESSMENT
NEW_BUYER_CONDITION
UNKNOWN
```

---

# 7. Code must validate metadata, not re-parse prose

For a future ROIC checkpoint:

bad architecture:

```text
search Korean sentence
for:
현재
향후
이어질 수 있다
개선되면
회복돼야
```

desired architecture:

```text
claim_type = FUTURE_VALIDATION_CONDITION
metric = ROIC
evidence_refs own ROIC?
same ticker?
same generation?
numeric current value invented?
```

The validator should not need to understand every Korean temporal
construction.

Required:

```text
TEMPORAL_GRAMMAR_REQUIRED_FOR_METRIC_OWNERSHIP = 0
```

for claims migrated to structured semantics.

---

# 8. Numeric ownership remains deterministic

AI must not gain freedom to invent numbers.

Preferred pattern:

```text
AI prose refers to numeric token/ref
↓
deterministic registry resolves exact value
```

Example:

```text
"현재 PBR은 {N1}로 과거 범위 하단입니다."
```

with:

```json
{
  "N1": {
    "fact_id": "valuation:current",
    "field_path": "fields.price_to_book"
  }
}
```

Required:

```text
FREEFORM_UNBOUND_NUMERIC = 0
```

No reverse calculation of missing EPS/BVPS/ROIC.

---

# 9. Decision fields remain structured

Structured Autonomy fields should remain machine-readable:

```text
overall direction
BUY:SELL balance
HOLD lean
new-buyer stance
holder stance
entry mode
price scenarios
business invalidation
```

Natural-language explanation may vary.

Validator should compare prose to structured fields only for
material contradictions.

Do not require identical stock-to-stock phrasing.

---

# 10. AI Writer ownership

Move substantive narrative to the AI Writer where currently a deterministic
renderer/template injects repeated judgment prose.

AI Writer owns:

```text
core explanation
why evidence matters
why uncertainty matters
holder explanation
new-buyer explanation
valuation interpretation
price/timing interpretation
supply relevance
```

The writer must not own raw numeric truth.

---

# 11. Thin renderer target

Long-term renderer responsibility should be limited to:

```text
section ordering
titles/icons
numeric token substitution
currency/number formatting
dates
line breaks
empty-section suppression
safe compatibility labels
```

Renderer should avoid substantive repeated boilerplate such as:

```text
"평균 이하 거래량은 확인 강도를 낮춥니다."
"가격은 사업 논리의 대체물이 아닙니다."
"자동 매도 구간이 아닙니다."
```

unless that wording is clearly deterministic/legal/safety text that must be
identical.

Audit all repeated deterministic prose ownership.

---

# 12. AI Semantic Reviewer

Prototype an AI semantic reviewer using ONLY:

```text
frozen candidate
structured semantic plan
same frozen evidence
same decision fields
```

It may assess:

```text
material contradiction
unsupported inference
mandatory trade instruction
semantic mismatch
material substantive repetition
unclear Unknown handling
```

It may NOT:
- add new facts
- add new numbers
- fetch external data
- rewrite unless explicitly invoked by bounded rewrite flow

---

# 13. AI reviewer is NOT initially a universal hard gate

Initial policy:

```text
Class A deterministic validator
= hard gate

Class B structured semantic contradictions
= hard gate where high-confidence/unambiguous

AI semantic reviewer
= shadow / advisory first

Class C quality
= warning or bounded rewrite
```

Do not replace one over-strict parser with an unstable AI veto.

---

# 14. Bounded rewrite policy

For Class C quality issues:

```text
candidate factually safe
+
quality warning
→ one bounded rewrite attempt
```

Rewrite constraints:

```text
same facts
same numeric refs
same decision fields
same evidence refs
same semantic claim types
no new price level
no new metric
no new recommendation
```

After rewrite:

```text
Class A/B validators rerun
```

If rewrite fails but original passes A/B:

```text
original remains delivery-eligible
```

unless explicitly classified as material semantic failure.

---

# 15. Repetition policy redesign

Do not use a raw sentence-similarity threshold as a universal delivery
blocker.

Classify repetition into:

```text
RENDERER_OWNED_REPEAT
MODEL_OWNED_SUBSTANTIVE_REPEAT
REQUIRED_SAFETY_REPEAT
BENIGN_TEMPLATE_REPEAT
MATERIAL_SPAM_REPEAT
```

Only `MATERIAL_SPAM_REPEAT` should be a candidate for hard block, and only
with a clear contract.

Examples of benign repeat:

```text
same section heading
same currency label
same required disclaimer
same short factual pattern
```

Examples of material repeat:

```text
multiple tickers receive a long identical investment rationale
despite materially different evidence
```

---

# 16. Generalization corpus — do not overfit to one incident

Build a regression corpus including ALL known incident classes plus
neighboring counterexamples.

Minimum known incident families:

```text
Korean token boundary:
수주가 / 발주가 / 주가

trade-language:
자동 매도
자동 매도보다
무조건 매도할 구간은 아님
반드시 매도해야 한다

metric temporal:
ROIC가 개선되면
ROIC 개선으로 이어져야
ROIC 악화로 이어질 수 있다
현재 ROIC는 12%

generic business words:
제품가격
평균판매가격
현재가
가격 구조
지지
사업을 지지함

repetition:
14-ticker repeated volume participation sentence
identical long rationale
required section headings
```

For each incident family add:
- historical false positive
- true positive
- semantically adjacent paraphrase
- unrelated negative control

---

# 17. No incident-specific exception

Required:

```text
TICKER_SPECIFIC_EXCEPTION = 0
EXACT_SENTENCE_WHITELIST = 0
EXACT_INCIDENT_HASH_BYPASS = 0
```

Historical incidents are regression examples, not special cases.

---

# 18. Cross-language / Korean morphology policy

Avoid expanding giant Korean keyword-negation regexes.

Where structured semantics are available:

```text
stop parsing Korean morphology for ownership
```

Where prose parsing remains unavoidable:
- use token-aware boundaries
- narrow scope
- pair positive and negative fixtures
- document why structured migration is not yet possible

---

# 19. Current US repeated-quality incident

The current US shared regression state:

```text
model path = 14/14 ACCEPTED
delivery = 0
reason = repeated typed prose quality gate
```

Do NOT automatically convert this exact case to PASS.

First determine:

```text
which repeated spans?
who owns them?
renderer or model?
are they substantive?
do they carry ticker-specific information?
would delivering them harm decision quality?
```

Classify under the new repetition taxonomy.

Only then determine whether:
- hard block was correct
- soft warning is correct
- bounded rewrite is appropriate
- renderer ownership should change

---

# 20. Shadow comparison on frozen historical artifacts

Use frozen historical artifacts where available.

No model rerun required for deterministic reclassification analysis.

Compare:

```text
OLD_POLICY
vs
NEW_POLICY_SHADOW
```

For each historical incident:

```text
old verdict
new verdict
true safety risk?
new false positive?
new false negative?
reason
```

Required:

```text
KNOWN_SAFETY_TRUE_POSITIVE_REGRESSION = 0
```

---

# 21. Fresh shadow US14 + KR8 generation

After contracts/tests are ready, run a NEW shadow generation.

Universe:

```text
US14 + KR8 = 22
```

Do not reuse candidate text from previous experiments.

Do not target a desired label distribution.

This run is to compare validation behavior, not to promote decisions.

Capture:

```text
Class A failures
Class B failures
Class C warnings
rewrite attempts
rewrite success
delivery-eligibility under old policy
delivery-eligibility under new shadow policy
```

No production send.

---

# 22. Structured Autonomy separation

This task does NOT change the investment decision algorithm.

Required:

```text
BUY_SELL_THRESHOLD_CHANGED = 0
HOLD_LEAN_CHANGED = 0
NEW_BUYER_ENUM_CHANGED = 0
HOLDER_ENUM_CHANGED = 0
```

It may introduce structured semantic claim metadata that future
Structured Autonomy production promotion can reuse.

But do not promote Structured Autonomy to production here.

---

# 23. Promotion metrics for validation architecture

Do not judge success by:

```text
more messages pass
```

alone.

Measure:

```text
hard-safety true positive retention
hard-safety false positive rate
semantic-hard precision
soft-quality warning rate
rewrite success rate
unnecessary production-block count
cross-ticker generalization
cross-market generalization
```

Suggested readiness questions:

```text
Did any unsupported numeric newly pass?
Did any cross-ticker evidence newly pass?
Did any accounting-basis error newly pass?
Did any lifecycle error newly pass?
Did historical false positives stop blocking?
Did repetition/style stop blocking safe messages?
```

---

# 24. Required safety gates

Hard rules:

```text
UNSUPPORTED_NUMERIC_ACCEPTED = 0
CROSS_TICKER_EVIDENCE_ACCEPTED = 0
CROSS_GENERATION_EVIDENCE_ACCEPTED = 0
ACCOUNTING_BASIS_ERROR_ACCEPTED = 0
ADR_SECURITY_BASIS_ERROR_ACCEPTED = 0
CLAIM_FENCING_ERROR_ACCEPTED = 0
DUPLICATE_DELIVERY_ACCEPTED = 0
```

If any nonzero:

```text
STOP
```

---

# 25. Production behavior in this task

This is shadow architecture work.

Required:

```text
PRODUCTION_VALIDATION_POLICY_MUTATION = 0
PRODUCTION_RENDERER_MUTATION = 0
PRODUCTION_DECISION_MUTATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
PRODUCTION_DB_MUTATION = 0
MAIN_MERGE = 0
```

Implementation can exist on a branch behind shadow/config flags.

---

# 26. Branch

Suggested:

```text
codex/20260904-validation-semantic-ownership-shadow
```

Work-instruction commit first.

Do not mix with:
- KR V2 child-wait production repair
- Structured Autonomy production promotion
- natural-run hotfix

---

# 27. Tests

Run:

```text
validator inventory consistency tests
Class A hard-safety fixtures
Class B semantic-hard fixtures
Class C soft-quality fixtures

Korean morphology incident corpus
numeric provenance corpus
accounting/ADR corpus
claim/fencing/lifecycle corpus
repetition taxonomy corpus

AI semantic reviewer contract tests
bounded rewrite invariance tests

frozen historical replay comparison
fresh US14+KR8 shadow comparison

full pytest
Ruff
git diff --check
Knowledge validation
Public Action validation
secret scan
```

---

# 28. Required reports

Create:

1. `docs/reports/20260904-validator-complete-inventory.md`
2. `docs/reports/20260904-validator-hard-semantic-soft-classification.md`
3. `docs/reports/20260904-hard-safety-preservation.md`
4. `docs/reports/20260904-structured-semantic-claim-contract.md`
5. `docs/reports/20260904-ai-writer-ownership-audit.md`
6. `docs/reports/20260904-thin-renderer-ownership-audit.md`
7. `docs/reports/20260904-ai-semantic-reviewer-contract.md`
8. `docs/reports/20260904-soft-quality-bounded-rewrite-policy.md`
9. `docs/reports/20260904-repetition-taxonomy.md`
10. `docs/reports/20260904-historical-validator-incident-corpus.md`
11. `docs/reports/20260904-old-vs-new-policy-frozen-comparison.md`
12. `docs/reports/20260904-us-repetition-ownership-audit.md`
13. `docs/reports/20260904-uskr22-shadow-policy-comparison.md`
14. `docs/reports/20260904-validation-architecture-promotion-readiness.md`
15. `docs/reports/20260904-validation-semantic-ownership-artifact-index.md`

Machine-readable:

```text
20260904-validator-inventory.json
20260904-validator-classification.json
20260904-incident-corpus-results.json
20260904-old-new-policy-comparison.json
20260904-uskr22-shadow-validation.json
20260904-validation-architecture-proof.json
```

---

# 29. Required gates

```text
VALIDATOR_RULES_INVENTORIED =
100% / OTHER

UNCLASSIFIED_RULES =
0 / NONZERO

CLASS_A_RULE_COUNT =
...

CLASS_B_RULE_COUNT =
...

CLASS_C_RULE_COUNT =
...

FACTUAL_SAFETY_REGRESSION =
0 / NONZERO

ACCOUNTING_SAFETY_REGRESSION =
0 / NONZERO

LIFECYCLE_SAFETY_REGRESSION =
0 / NONZERO

UNSUPPORTED_NUMERIC_ACCEPTED =
0 / NONZERO

CROSS_TICKER_EVIDENCE_ACCEPTED =
0 / NONZERO

CROSS_GENERATION_EVIDENCE_ACCEPTED =
0 / NONZERO

ACCOUNTING_BASIS_ERROR_ACCEPTED =
0 / NONZERO

ADR_SECURITY_BASIS_ERROR_ACCEPTED =
0 / NONZERO

CLAIM_FENCING_ERROR_ACCEPTED =
0 / NONZERO

DUPLICATE_DELIVERY_ACCEPTED =
0 / NONZERO

STRUCTURED_SEMANTIC_CLAIM_CONTRACT =
PASS / FAIL

TEMPORAL_GRAMMAR_REQUIRED_FOR_METRIC_OWNERSHIP =
0 / NONZERO

FREEFORM_UNBOUND_NUMERIC =
0 / NONZERO

AI_SEMANTIC_REVIEWER =
SHADOW_READY / NOT_READY

SOFT_QUALITY_CAN_BLOCK_PRODUCTION =
NO / YES

BOUNDED_REWRITE_INVARIANCE =
PASS / FAIL

TICKER_SPECIFIC_EXCEPTION =
0 / NONZERO

EXACT_SENTENCE_WHITELIST =
0 / NONZERO

KNOWN_SAFETY_TRUE_POSITIVE_REGRESSION =
0 / NONZERO

HISTORICAL_FALSE_POSITIVE_BLOCK_COUNT_OLD =
...

HISTORICAL_FALSE_POSITIVE_BLOCK_COUNT_NEW =
...

US_REPETITION_CLASS =
RENDERER_OWNED_REPEAT /
MODEL_OWNED_SUBSTANTIVE_REPEAT /
REQUIRED_SAFETY_REPEAT /
BENIGN_TEMPLATE_REPEAT /
MATERIAL_SPAM_REPEAT /
MIXED /
UNKNOWN

USKR22_CLASS_A_FAILURES =
...

USKR22_CLASS_B_FAILURES =
...

USKR22_CLASS_C_WARNINGS =
...

USKR22_REWRITE_ATTEMPTS =
...

USKR22_REWRITE_SUCCESS =
...

BUY_SELL_THRESHOLD_CHANGED =
0 / NONZERO

HOLD_LEAN_CHANGED =
0 / NONZERO

NEW_BUYER_ENUM_CHANGED =
0 / NONZERO

HOLDER_ENUM_CHANGED =
0 / NONZERO

PRODUCTION_VALIDATION_POLICY_MUTATION =
0 / NONZERO

PRODUCTION_RENDERER_MUTATION =
0 / NONZERO

PRODUCTION_DECISION_MUTATION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

READINESS =
READY_FOR_BOUNDED_PRODUCTION_POLICY_REVIEW /
NEEDS_MORE_SHADOW_WORK /
NOT_READY
```

---

# 30. Completion response

Return:

```text
VALIDATOR INVENTORY =
total ...
Class A ...
Class B ...
Class C ...

CURRENT PROBLEM =
which rules are too lexical
which rules are correctly hard

HARD SAFETY =
retained ...

STRUCTURED SEMANTIC OWNERSHIP =
implemented/prototyped ...

AI WRITER =
...

AI REVIEWER =
...

RENDERER =
...

REPETITION =
current US incident ownership ...

HISTORICAL INCIDENTS =
old false positives ...
new false positives ...
true-positive retention ...

USKR22 SHADOW =
...

SAFETY REGRESSION =
...

READINESS =
...

PRODUCTION MUTATION = 0
MAIN MERGE = 0

ZIP =
...
ZIP_SHA256 =
...
```

---

# 31. Stop conditions

Stop if the redesign requires weakening numeric/provenance/accounting/
lifecycle safety.

Stop if a Class C change causes any known Class A true positive to pass.

Stop if AI reviewer becomes a universal production veto in this task.

Stop if implementation starts optimizing for the current 14-ticker repeated
sentence rather than the general taxonomy.

Do not use passing-message count as the sole objective.

---

# 32. Final principle

The goal is NOT:

```text
make validation looser
```

The goal is:

```text
make validation strict about truth
and flexible about language
```

Hard fail on:
- wrong facts
- wrong numbers
- wrong ownership
- wrong accounting
- wrong lifecycle

Do not hard fail merely because:
- Korean phrasing changed
- a safe sentence is stylistically similar
- a future condition uses an unseen grammatical form
- multiple stocks share benign boilerplate

Move meaning ownership into structured AI output so the system no longer
has to reverse-engineer the AI's Korean prose with an ever-growing parser.
