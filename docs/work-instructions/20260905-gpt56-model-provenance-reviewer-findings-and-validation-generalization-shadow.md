# thesis-monitor — GPT-5.6 Production-Equivalent Validation Shadow
## Trace why the previous fresh US14+KR8 used GPT-5.5
## Pin the exact production-equivalent GPT-5.6 runtime
## Close the five advisory reviewer findings with structured ownership
## Expand Class-C generalization stress
## Re-run a completely fresh US14+KR8 under GPT-5.6/xhigh
## Shadow only — no production policy mutation in this task

---

# 0. Source lock

Previous validation-architecture result bundle:

```text
file =
thesis-monitor-20260904-validation-policy-reclassification-and-semantic-ownership-migration-report-bundle.zip

sha256 =
0ccdd2e91d8b0c7f6d1296644332227876380c01c11d7aef5b7c3e2dcb3ce5f1
```

Previous result:

```text
validator inventory =
64 / 64

Class A HARD =
33

Class B SEMANTIC_HARD =
16

Class C SOFT_QUALITY =
15

historical old-policy false-positive blocks =
8

new-shadow false-positive blocks =
0

known safety true-positive regression =
0
```

Previous fresh US14 + KR8:

```text
subjects =
22

model =
gpt-5.5

reasoning =
xhigh

Class A failures =
0

Class B failures =
0

Class C warnings =
0

old-policy eligible =
22 / 22

new-shadow eligible =
22 / 22
```

AI semantic reviewer:

```text
PASS subjects =
18

WARN subjects =
4

findings =
5
```

Promotion verdict:

```text
READY_FOR_BOUNDED_PRODUCTION_POLICY_REVIEW
```

---

# 1. Important correction — GPT-5.5 run is NOT promotion evidence

The user normally operates the production AI path with GPT-5.6.

The previous report states only:

```text
Fresh signed-in Codex CLI gpt-5.5 / xhigh
```

It does NOT establish why GPT-5.5 was selected.

Therefore:

```text
PREVIOUS_GPT55_FRESH_RUN =
ARCHITECTURE_REFERENCE_ONLY
```

It may support:
- contract prototyping
- reviewer finding discovery
- historical comparison

It must NOT be used as the final production-equivalent promotion run.

Required:

```text
GPT55_RUN_COUNTS_TOWARD_PROMOTION =
0
```

---

# 2. First task — trace model-selection provenance

Before changing semantic contracts or launching a new model run, identify the exact model-selection chain for:

```text
production KR V2
production US V2
validation shadow generator
AI semantic reviewer
bounded rewrite
```

Trace:

```text
CLI command
model argument
environment variable
config file
runtime default
script default
fallback model
app-server default
skill instruction
caller override
```

Relevant known shadow generator from the previous report:

```text
scripts/validation_semantic_ownership_shadow.py
```

Relevant service:

```text
app/services/validation_policy_shadow_service.py
```

Do not assume either file caused the downgrade until proven.

---

# 3. Required model-selection report

For each execution path record:

```text
path
requested_model
resolved_model
reasoning_effort
source_of_model_choice
fallback_allowed?
fallback_model
runtime/CLI version
CODEX_HOME policy
sandbox mode
```

Required classification:

```text
GPT55_SELECTION_CAUSE =
EXPLICIT_SCRIPT_OVERRIDE /
CONFIG_DEFAULT /
CLI_DEFAULT /
APP_SERVER_DEFAULT /
FALLBACK_PATH /
SKILL_INSTRUCTION /
ENVIRONMENT_OVERRIDE /
OTHER /
UNKNOWN
```

If unknown:
stop before promotion-equivalent fresh generation.

---

# 4. Production-equivalent model identity

Discover the exact model identifier from the current approved production V2 runtime.

Expected family based on current operating practice:

```text
GPT-5.6 Sol
```

Do NOT hardcode an identifier merely from this instruction if the repository/runtime
uses a canonical spelling.

The task must resolve:

```text
PRODUCTION_MODEL_ID =
...
```

Then require:

```text
SHADOW_PROMOTION_MODEL_ID
==
PRODUCTION_MODEL_ID
```

No silent fallback.

---

# 5. Fail closed on model mismatch

Before the new US14+KR8 generation:

```text
MODEL_EQUIVALENCE_PREFLIGHT = PASS
```

Must verify:

```text
resolved model exactly matches production
reasoning effort matches production target
same signed-in CLI family
same auth mode
same trust path
same sandbox/runtime class where relevant
```

If resolved model is GPT-5.5:

```text
STOP
```

Do not say:
- "close enough"
- "architecture only"
- "we can compare later"

The new fresh run must be production-equivalent.

---

# 6. No silent downgrade / fallback

If model fallback exists, make it explicit in audit.

For promotion-equivalent shadow:

```text
SILENT_MODEL_FALLBACK =
0
```

If GPT-5.6 is unavailable:

```text
MODEL_EQUIVALENCE_PREFLIGHT =
FAIL
```

Do not automatically run GPT-5.5 instead.

This requirement applies to:
- primary fresh generation
- AI semantic reviewer
- bounded rewrite

unless a component is intentionally designed to use a different model and the
production architecture explicitly says so.

If different:
document the reason and keep the primary writer production-equivalent.

---

# 7. Five reviewer findings to close

The previous AI semantic reviewer reported five findings.

## CRCL — UNSUPPORTED_UNKNOWN_CONTEXT

Evidence states:
- revenue impact is unknown

Candidate adds:
- payment / stablecoin usage expansion as the unresolved driver

Need generic evidence-scope ownership.

---

## RXRX — CLAIM_TYPE_SEVERITY_MISMATCH

Evidence:
- thesis weakening condition

Candidate claim type:
- BUSINESS_INVALIDATION_CONDITION

This overstates severity.

This is structured metadata and should not depend on free prose parsing.

---

## RXRX — UNSUPPORTED_UNKNOWN_CONTEXT

Evidence states:
- revenue impact unknown

Candidate adds:
- research achievement / business expansion context

Need generic evidence-scope ownership.

---

## TSM — INELIGIBLE_VALUATION_REF_OWNERSHIP

Security-basis evidence says:
- security identity unknown
- valuation fields not prose eligible

Candidate also cites:
- raw valuation book reference

This creates risk that an ineligible valuation multiple supports prose.

This is NOT a style problem.

---

## 012450 — UNSUPPORTED_UNKNOWN_CONTEXT

Evidence states:
- FCF impact unknown

Candidate adds:
- positive order-expansion premise

Available order evidence instead includes:
- demand slowdown / order decline / backlog contraction invalidation risk

Need generic evidence-scope ownership.

---

# 8. Finding ownership classification

Classify the five findings before implementation.

Target architecture:

```text
TSM valuation ref eligibility
→ deterministic HARD or structured SEMANTIC_HARD

RXRX weakening vs invalidation severity
→ structured SEMANTIC_HARD

CRCL/RXRX/012450 unsupported unknown context
→ structured evidence-scope contract
```

Do not fix them by:
- ticker exception
- exact phrase blacklist
- exact phrase whitelist
- adding more Korean regex

Required:

```text
TICKER_SPECIFIC_FIX =
0
```

---

# 9. TSM — evidence eligibility must be machine-readable

Every evidence reference used by prose/semantic claims should expose an equivalent of:

```text
prose_eligible
semantic_eligible
numeric_eligible
valuation_eligible
```

Exact schema may differ.

For a claim of type:

```text
VALUATION_INTERPRETATION
```

the selected evidence refs must be valuation-interpretation eligible.

If:

```text
security basis unknown
```

causes a raw valuation ref to be ineligible:

```text
claim cannot cite it as interpretation support
```

The AI may cite the security-basis caution itself.

Required:

```text
INELIGIBLE_VALUATION_REF_ACCEPTED =
0
```

This should be deterministic where possible.

---

# 10. RXRX — severity ordering contract

Define machine-readable severity relationships.

Example native equivalent:

```text
STRENGTHENING
MAINTAIN
WEAKENING
INVALIDATION_CANDIDATE
INVALIDATION
```

A claim must not escalate:

```text
WEAKENING evidence
→ BUSINESS_INVALIDATION_CONDITION
```

without evidence that owns invalidation severity.

Required:

```text
UNSUPPORTED_SEVERITY_ESCALATION_ACCEPTED =
0
```

Do not infer severity from words like:
- 악화
- 약화
- 훼손
alone.

Use structured source semantics.

---

# 11. Unknown evidence-scope contract

The writer should be free to explain Unknown naturally, but may not invent a new causal driver.

Introduce a structured distinction such as:

```text
unknown_subject
unknown_metric
unknown_effect
allowed_context_refs
```

Example:

```json
{
  "claim_type": "UNKNOWN",
  "unknown_subject": "revenue_impact",
  "allowed_context_refs": ["E04"],
  "text": "..."
}
```

The exact schema may differ.

---

# 12. Allowed paraphrase vs new driver

The contract must distinguish:

Allowed:

```text
Evidence:
FCF impact is unknown

Writer:
현금흐름에 어떤 영향을 줄지는 아직 확인되지 않았습니다.
```

Not allowed without new evidence:

```text
Evidence:
FCF impact is unknown

Writer:
해외 수주 확대가 FCF 개선으로 이어질지는 확인되지 않았습니다.
```

because:

```text
해외 수주 확대
```

is a new premise.

Required:

```text
UNSUPPORTED_NEW_CAUSAL_DRIVER_ACCEPTED =
0
```

---

# 13. Do not solve Unknown scope with open-ended NLP parsing

Prefer:

```text
structured context/evidence ownership
```

over:

```text
scan Korean prose for nouns
compare keyword sets
```

A limited diagnostic similarity check may exist in shadow,
but it cannot become the primary ownership rule.

Required target:

```text
UNKNOWN_SCOPE_PRIMARY_OWNER =
STRUCTURED_METADATA
```

---

# 14. AI semantic reviewer role after repair

The reviewer remains useful for discovering problems that structured rules do not yet encode.

After this repair:

```text
TSM valuation eligibility
and
RXRX severity mismatch
```

should ideally be caught before the reviewer.

Unknown-scope findings may remain reviewer-audited until the structured contract proves reliable.

Reviewer remains:

```text
SHADOW / ADVISORY
```

for this task.

No universal hard veto.

---

# 15. Expanded Class-C stress corpus

The previous fresh 22 happened to produce:

```text
Class C warnings = 0
```

That does not adequately stress the new soft-quality policy.

Expand the controlled corpus.

Minimum families:

```text
benign repeated headings
short bound-numeric wrapper repetition
short safety disclaimer repetition
renderer-owned repeated phrase
model-owned short factual repetition
model-owned long substantive rationale repetition
long cross-ticker rationale with different evidence
near-identical rationale with ticker-specific numeric substitutions
verbosity
boilerplate
Korean paraphrase diversity
```

---

# 16. Repetition stress labels

Each corpus item must have a source-owned expected class:

```text
BENIGN_TEMPLATE_REPEAT
REQUIRED_SAFETY_REPEAT
RENDERER_OWNED_REPEAT
MODEL_OWNED_SUBSTANTIVE_REPEAT
MATERIAL_SPAM_REPEAT
```

Do NOT derive expected labels from the new implementation's output.

Manual corpus labels are only for validator-quality testing,
not investment BUY/HOLD/SELL judgments.

---

# 17. Material repetition policy

A long substantive rationale duplicated across unrelated tickers despite different evidence may be:

```text
SEMANTIC_HARD
or
bounded rewrite required
```

depending on whether it creates factual/decision misrepresentation.

A short safe wrapper should remain:

```text
SOFT_QUALITY
```

or benign.

Do not turn all repetition into pass.

---

# 18. Bounded rewrite stress

For Class C issues that trigger rewrite:

```text
one rewrite attempt
```

Invariance requirements:

```text
same decision fields
same claim types
same evidence refs
same numeric refs
same prices
same holder/new-buyer stance
no new metric
no new causal premise
```

If rewrite fails but original is Class A/B safe:

```text
original remains eligible
```

unless the repetition itself is classified material semantic misrepresentation.

---

# 19. Historical safety corpus must still pass

Preserve all prior incident families:

```text
수주가 vs 주가
자동 매도 vs 자동 매도보다
ROIC current vs future condition
제품가격 vs technical price
사업을 지지함 vs support level
nonexistent evidence
cross-ticker evidence
numeric semantic mismatch
ADR/security basis
KR accounting attribution
claim/fencing
duplicate delivery
```

Required:

```text
KNOWN_SAFETY_TRUE_POSITIVE_REGRESSION =
0
```

---

# 20. Completely fresh GPT-5.6 US14 + KR8

After:
- model provenance PASS
- five finding contracts implemented
- stress corpus PASS

run a COMPLETELY NEW generation.

Universe:

```text
US14 + KR8 = 22
```

Do not reuse:
- GPT-5.5 candidates
- prior 22/22 candidates
- prior reviewer outputs
- prior rewrites

Prior results must be hidden until the new candidate set is frozen.

---

# 21. Fresh run model contract

Required:

```text
PRIMARY_WRITER_MODEL =
PRODUCTION_MODEL_ID

PRIMARY_WRITER_REASONING =
production-equivalent xhigh

AI_REVIEWER_MODEL =
document exact resolved model

BOUNDED_REWRITE_MODEL =
document exact resolved model
```

If production uses GPT-5.6 Sol/xhigh,
the primary writer must resolve to that exact production identifier.

---

# 22. Fresh run outputs

For all 22 record:

```text
Class A failures
Class B failures
Class C warnings

AI reviewer PASS/WARN
reviewer finding types

rewrite required?
rewrite result

old-policy eligibility
new-shadow eligibility
```

Also record:

```text
model requested
model resolved
runtime version
```

per model-consuming stage.

---

# 23. Fresh run safety gate

Required:

```text
CLASS_A_FALSE_NEGATIVE =
0

CLASS_B_KNOWN_FALSE_NEGATIVE =
0

UNSUPPORTED_NUMERIC_ACCEPTED =
0

CROSS_TICKER_EVIDENCE_ACCEPTED =
0

CROSS_GENERATION_EVIDENCE_ACCEPTED =
0

ACCOUNTING_BASIS_ERROR_ACCEPTED =
0

ADR_SECURITY_BASIS_ERROR_ACCEPTED =
0

INELIGIBLE_VALUATION_REF_ACCEPTED =
0

UNSUPPORTED_SEVERITY_ESCALATION_ACCEPTED =
0

UNSUPPORTED_NEW_CAUSAL_DRIVER_ACCEPTED =
0
```

---

# 24. Fresh run quality success is not "22/22 pass"

The purpose is not to maximize eligibility.

A healthy outcome may include:
- soft warnings
- bounded rewrites
- valid semantic-hard rejection

Promotion readiness depends on correct classification.

Do not lower rules merely to reach 22/22.

---

# 25. Model-comparison audit

Compare previous GPT-5.5 exploratory run to the new GPT-5.6 run ONLY after new outputs are frozen.

Measure:

```text
claim-type distribution
evidence-selection changes
reviewer finding distribution
Class C warning distribution
rewrite rate
```

Do NOT:
- majority vote
- choose whichever output passes
- retune against the differences

The purpose is to quantify model drift and prove why model equivalence matters.

---

# 26. Structured Autonomy judgment logic remains frozen

Do not change:

```text
BUY/HOLD/SELL thresholds
BUY:SELL balance rule
HOLD lean
new-buyer enums
holder enums
entry modes
price scenario semantics
```

Required:

```text
JUDGMENT_LOGIC_CHANGED =
0
```

This task is validation architecture only.

---

# 27. Production remains unchanged

Required:

```text
PRODUCTION_VALIDATOR_MUTATION =
0

PRODUCTION_RENDERER_MUTATION =
0

PRODUCTION_DECISION_MUTATION =
0

PRODUCTION_TELEGRAM_SEND =
0

PRODUCTION_SCHEDULER_CHANGE =
0

PRODUCTION_DB_MUTATION =
0

MAIN_MERGE =
0
```

Implement behind shadow/test-only boundaries.

---

# 28. Relationship to KR V2 child-wait repair

The separate KR V2 child-wait repair finished at:

```text
ebc2350
```

with:

```text
KR TEST:
market 1 + explicit V2 stock 8/8

runtime:
1092.99 sec

Pilot:
0

fallback:
0

duplicate:
0
```

It remains unmerged because the US shared path was blocked by quality policy.

Do NOT reimplement that repair here.

After this validation shadow reaches readiness,
the NEXT production task may combine:

```text
KR child-wait repair
+
bounded production validation-policy changes
```

on a clean integration branch.

---

# 29. Readiness target

Maximum verdict for this task:

```text
READY_FOR_BOUNDED_PRODUCTION_POLICY_REPAIR
```

Not:
- READY_FOR_MAIN
- READY_FOR_PRODUCTION

Required for readiness:

```text
model provenance known
GPT-5.6 production equivalence PASS
five findings closed generically
Class-C stress corpus PASS
historical safety regression 0
fresh GPT-5.6 US14+KR8 complete
AI reviewer remaining findings understood
production mutation 0
```

---

# 30. Required reports

Create:

1. `docs/reports/20260905-model-selection-provenance.md`
2. `docs/reports/20260905-gpt55-selection-root-cause.md`
3. `docs/reports/20260905-gpt56-production-equivalence-preflight.md`
4. `docs/reports/20260905-reviewer-five-findings-ownership.md`
5. `docs/reports/20260905-valuation-evidence-eligibility-contract.md`
6. `docs/reports/20260905-semantic-severity-contract.md`
7. `docs/reports/20260905-unknown-evidence-scope-contract.md`
8. `docs/reports/20260905-expanded-soft-quality-stress-corpus.md`
9. `docs/reports/20260905-bounded-rewrite-invariance-stress.md`
10. `docs/reports/20260905-historical-safety-regression.md`
11. `docs/reports/20260905-fresh-uskr22-gpt56-shadow.md`
12. `docs/reports/20260905-gpt55-vs-gpt56-shadow-drift.md`
13. `docs/reports/20260905-validation-policy-production-repair-readiness.md`
14. `docs/reports/20260905-validation-generalization-artifact-index.md`

Machine-readable:

```text
20260905-model-provenance.json
20260905-reviewer-findings-proof.json
20260905-soft-quality-stress.json
20260905-historical-safety-regression.json
20260905-uskr22-gpt56-shadow.json
20260905-gpt55-gpt56-drift.json
20260905-validation-readiness-proof.json
```

---

# 31. Required gates

```text
SOURCE_BUNDLE_SHA256 =
0ccdd2e91d8b0c7f6d1296644332227876380c01c11d7aef5b7c3e2dcb3ce5f1

PREVIOUS_GPT55_RUN_PROMOTION_WEIGHT =
0

GPT55_SELECTION_CAUSE =
EXPLICIT_SCRIPT_OVERRIDE /
CONFIG_DEFAULT /
CLI_DEFAULT /
APP_SERVER_DEFAULT /
FALLBACK_PATH /
SKILL_INSTRUCTION /
ENVIRONMENT_OVERRIDE /
OTHER /
UNKNOWN

PRODUCTION_MODEL_ID =
...

PRODUCTION_REASONING_EFFORT =
...

SHADOW_PRIMARY_MODEL_ID =
...

MODEL_EQUIVALENCE_PREFLIGHT =
PASS / FAIL

SILENT_MODEL_FALLBACK =
0 / NONZERO

GPT55_USED_IN_NEW_PROMOTION_RUN =
0 / NONZERO

REVIEWER_FINDINGS_TOTAL =
5

REVIEWER_FINDINGS_CLASSIFIED =
5 / OTHER

INELIGIBLE_VALUATION_REF_ACCEPTED =
0 / NONZERO

UNSUPPORTED_SEVERITY_ESCALATION_ACCEPTED =
0 / NONZERO

UNSUPPORTED_NEW_CAUSAL_DRIVER_ACCEPTED =
0 / NONZERO

UNKNOWN_SCOPE_PRIMARY_OWNER =
STRUCTURED_METADATA / OTHER

TICKER_SPECIFIC_FIX =
0 / NONZERO

EXACT_SENTENCE_WHITELIST =
0 / NONZERO

CLASSC_STRESS_CASE_COUNT =
...

CLASSC_STRESS_EXPECTED_LABEL_MATCH =
100% / OTHER

BOUNDED_REWRITE_INVARIANCE =
PASS / FAIL

KNOWN_SAFETY_TRUE_POSITIVE_REGRESSION =
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

FRESH_USKR22_GENERATION =
PASS / FAIL

FRESH_USKR22_PRIMARY_MODEL =
...

FRESH_USKR22_SUBJECT_COUNT =
22 / OTHER

FRESH_USKR22_CLASS_A_FAILURES =
...

FRESH_USKR22_CLASS_B_FAILURES =
...

FRESH_USKR22_CLASS_C_WARNINGS =
...

FRESH_USKR22_REVIEWER_WARN_SUBJECTS =
...

FRESH_USKR22_REVIEWER_FINDINGS =
...

FRESH_USKR22_REWRITE_ATTEMPTS =
...

FRESH_USKR22_REWRITE_SUCCESS =
...

JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

PRODUCTION_VALIDATOR_MUTATION =
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
READY_FOR_BOUNDED_PRODUCTION_POLICY_REPAIR /
NEEDS_MORE_SHADOW_WORK /
BLOCKED_MODEL_MISMATCH /
NOT_READY
```

---

# 32. Stop conditions

Stop before fresh USKR22 if:

```text
GPT55_SELECTION_CAUSE = UNKNOWN
```

or:

```text
MODEL_EQUIVALENCE_PREFLIGHT != PASS
```

Stop if the primary writer resolves to GPT-5.5.

Stop if any fix requires:
- ticker exception
- exact sentence whitelist
- numeric/provenance weakening
- accounting/security-basis weakening

Stop if the new policy is optimized to make all 22 pass.

Stop if AI reviewer is promoted to universal hard veto.

---

# 33. Completion response

Return:

```text
MODEL SELECTION =
why previous run used GPT-5.5
production model ID
new resolved model
silent fallback ...

FIVE FINDINGS =
CRCL ...
RXRX severity ...
RXRX unknown ...
TSM valuation ...
012450 ...

STRUCTURED OWNERSHIP =
valuation eligibility ...
severity ...
unknown scope ...

CLASS-C STRESS =
...

HISTORICAL SAFETY =
...

FRESH GPT-5.6 USKR22 =
model
22 subjects
Class A/B/C
reviewer findings
rewrite

GPT-5.5 vs GPT-5.6 =
drift summary

READINESS =
...

NEXT PRODUCTION HANDOFF =
KR child-wait ebc2350
+
bounded validation-policy repair
→ integration TEST KR/US
→ main only after both PASS

PRODUCTION MUTATION = 0
MAIN MERGE = 0

ZIP =
...
ZIP_SHA256 =
...
```

---

# 34. Final principle

Do not compensate for an unexplained model mismatch by interpreting results
more generously.

The validation architecture should be judged on the same model/runtime family
that production will actually use.

At the same time:

```text
strict about truth
flexible about language
```

remains the policy.

Use structured ownership to close the five real semantic/provenance gaps,
not a return to Korean regex overfitting.
