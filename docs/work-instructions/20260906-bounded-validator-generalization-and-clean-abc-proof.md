# thesis-monitor — Bounded Validator Generalization + Clean A/B/C Proof
## Close only the five newly observed B-gate issues
## Preserve all hard semantic safety
## Do not tune judgment labels
## Run a completely new US14+KR8 generation
## Require FIRST 22/22 + A 22/22 + B 22/22 + C 22/22
## Keep night-futures production review independent from Structured Autonomy promotion

---

# 0. Immutable source result

Source bundle:

```text
thesis-monitor-20260906-validator-p1-night-futures-frozen-result-f10d4c8(3).zip
```

SHA-256:

```text
00ba4679155d9b7e64ee2d789d8d1d6fa03eb26fae0c5bde97883928e9134e76
```

Previous experiment generation:

```text
20260905-uskr22-validator-night-20260905T161259Z-1a32918a3962
```

Previous source lock:

```text
f3b7d4c08c32312c2207acae2cb9353926940e41a2bcf254a7214a041d246be0
```

Previous result:

```text
FIRST = 22/22
A     = 22/22
B     = 17/22
C     = NOT_RUN

stop state =
STOPPED_B_GATE
```

The previous generation is frozen forever.

Required:

```text
PREVIOUS_GENERATION_RESUME = 0
PREVIOUS_CANDIDATE_REUSE = 0
PREVIOUS_CANDIDATE_EDIT = 0
```

---

# 1. What is already proven

Do NOT reopen solved P1s unless a regression appears.

Proven:

```text
future-checkpoint primary owner =
STRUCTURED_METADATA

FIRST future-checkpoint false reject =
0

A future-checkpoint false reject =
0

logical-condition schema =
DISCRIMINATED_UNION

LEAF child-shape failure =
0

ticker exceptions =
0

Korean future-grammar regex additions =
0

global semantic threshold weakening =
0

hard-safety regression =
0
```

Night futures separately reached:

```text
READY_FOR_PRODUCTION_REVIEW
```

and remain outside Structured Autonomy packets.

---

# 2. B-gate failure inventory

Exactly five B candidates failed.

## GOOGL

```text
future_checkpoint_kind_not_owned
unsupported_metric_or_inference
```

Classification:

```text
INTENDED_FAIL_CLOSED
```

Reason:
the selected evidence owned the metric but did NOT own `STRENGTHENING` severity.

Do NOT weaken the validator.

---

## IBM

```text
future_checkpoint_kind_not_owned
unsupported_metric_or_inference
```

Classification:

```text
FALSE_REJECT
```

Reason:
FCF and ROIC were separately owned by selected evidence items with the same semantic severity/scope, but the validator required one evidence item to own all named metrics.

---

## MU

```text
directional_balance_probability_language
```

Classification:

```text
FALSE_POSITIVE
```

Reason:
`상승률` contains the substring `승률`.

---

## SNDK

```text
mandatory_trade_language
```

Classification:

```text
FALSE_POSITIVE
```

Reason:
`즉시 매수가 아닌` is negated safety language, not a buy instruction.

---

## TSLA

Same as SNDK.

---

# 3. Hard constraint

This task is NOT:

```text
make B pass
```

This task IS:

```text
repair four generic false rejects
+
keep GOOGL-style unsupported severity fail-closed
+
prove generalization on a completely new generation
```

If GOOGL-like unsupported strengthening claims start passing:

```text
STOP
```

---

# 4. P1-A — same-severity selected-evidence metric union

Current overly strict rule behaves like:

```text
one evidence ref
must own
all metrics in the claim
```

That creates IBM's false reject.

Target rule:

```text
for a single claim:
all selected evidence refs
that share the same semantic ownership domain
may contribute a UNION of owned metrics
```

Only if all of the following match:

```text
same ticker
same generation
same claim scope
same semantic severity
same checkpoint kind
same time scope
eligible selected evidence refs only
```

---

# 5. Metric-union safety boundary

Allowed example:

```text
selected evidence E1:
severity = INVALIDATION
metrics = [FCF]

selected evidence E2:
severity = INVALIDATION
metrics = [ROIC]

claim:
FCF and ROIC deteriorate under INVALIDATION context

→ PASS
```

Forbidden:

```text
E1:
STRENGTHENING
FCF

E2:
INVALIDATION
ROIC

claim:
FCF and ROIC strengthen

→ FAIL
```

Forbidden:

```text
same packet but evidence was not selected by the claim
→ cannot contribute ownership
```

Required:

```text
METRIC_UNION_PRIMARY_SCOPE =
SELECTED_EVIDENCE_ONLY
```

---

# 6. No packet-wide ownership

Do not implement:

```text
if any fact anywhere in the ticker packet owns the metric
then allow it
```

This would break evidence provenance.

Union is only across:

```text
claim-selected refs
with identical compatible semantic ownership
```

---

# 7. GOOGL regression must remain fail-closed

Create generic fixtures:

```text
metric owned + strengthening severity not owned
→ FAIL

metric owned + invalidation severity owned
→ invalidation claim PASS

same metric appears in packet but selected evidence lacks severity
→ FAIL

metric owned by strengthening evidence
→ strengthening claim PASS
```

GOOGL becomes one historical fixture, not a ticker exception.

Required:

```text
UNOWNED_STRENGTHENING_SEVERITY_ACCEPTED =
0
```

---

# 8. P1-B — probability-language token boundary

Do not detect probability language using raw substring matching.

Observed:

```text
상승률
contains
승률
```

Target:

```text
semantic token / word-boundary-aware detection
```

At minimum distinguish:

```text
승률
성공확률
확률
odds
probability
win rate
```

from:

```text
상승률
하락률
성장률
증가율
감소율
수익률
마진율
변동률
```

---

# 9. Probability detector safety

The fix must not simply remove `승률` detection.

True positives must remain blocked where probability language is unsupported.

Required fixtures:

```text
"승률 70%"
→ probability language

"성공확률이 높다"
→ probability language

"주가 상승률 8%"
→ rate metric, NOT probability language

"매출 성장률 20%"
→ rate metric, NOT probability language
```

Required:

```text
PROBABILITY_TRUE_POSITIVE_REGRESSION = 0
```

---

# 10. P1-C — negated trade-language semantics

Observed phrases:

```text
즉시 매수가 아닌
```

were treated as mandatory BUY instructions.

Target architecture:

```text
trade_language_semantic =
ACTIONABLE /
NEGATED /
DESCRIPTIVE /
NONE
```

Structured ownership should be primary where possible.

The prose detector may remain a fallback hard-safety layer.

---

# 11. Negation safety

Allowed:

```text
즉시 매수가 아니다
매도 명령이 아니다
자동 손절선이 아니다
향후 재검토 조건이다
```

Must remain blocked if unsupported/actionable:

```text
즉시 매수
반드시 매도
지금 전량 매도
무조건 매수
```

Do not solve using only an exact `"아닌"` whitelist.

Use:
- structured action semantics
- bounded negation scope
- token-aware fallback

---

# 12. Negation must not swallow actionability

Examples:

```text
"즉시 매수가 아닌 것 같지만 결국 지금 매수해야 한다"
→ ACTIONABLE / FAIL

"즉시 매수가 아닌 향후 재검토 조건이다"
→ NEGATED / PASS
```

Required:

```text
ACTIONABLE_TRADE_FALSE_NEGATIVE =
0
```

---

# 13. P1-D — repeated action/safety wrapper taxonomy

The identical SNDK/TSLA negated sentence was counted as substantive repetition.

Audit ownership before changing policy.

Target taxonomy:

```text
REQUIRED_SAFETY_REPEAT
ACTION_CONTEXT_WRAPPER_REPEAT
RENDERER_OWNED_REPEAT
MODEL_OWNED_SUBSTANTIVE_REPEAT
MATERIAL_SPAM_REPEAT
```

A short statement explaining that a price path is not an immediate buy/sell instruction is not automatically a substantive investment rationale.

---

# 14. Repetition hard boundary

Benign:

```text
"해당 가격은 자동 손절선이 아닙니다."
```

across multiple tickers.

Potentially material:

```text
a long identical investment rationale
claiming the same business drivers
across unrelated tickers
```

Do NOT whitelist the SNDK/TSLA sentence.

Classify by semantic ownership and content role.

Required:

```text
BENIGN_ACTION_WRAPPER_HARD_BLOCK =
0

MATERIAL_SUBSTANTIVE_REPEAT_PROTECTION =
PASS
```

---

# 15. P1-E — writer contract for severity ownership

The GOOGL failure is a writer-contract problem, not a validator bug.

For a claim with:

```text
checkpoint_kind = STRENGTHEN
```

the selected evidence must explicitly own strengthening severity.

If it does not:

writer options are:

```text
1. emit FUTURE_VALIDATION / OBSERVE
2. emit neutral evidence interpretation
3. omit the claim
```

The writer may NOT relabel neutral/invalidation evidence as strengthening.

---

# 16. Evidence interpretation constraints

Preserve the previous contract:

```text
EVIDENCE_INTERPRETATION
checkpoint_kind = null
direction = null

UNKNOWN_LIMIT
direction = OBSERVE
```

Do not use those neutral claim types to smuggle directional strengthening/weaking meaning.

Add explicit regression tests for semantic leakage.

---

# 17. No judgment tuning

Do NOT change:

```text
BUY/HOLD/SELL thresholds

BUY:SELL 6.0 threshold

HOLD lean rules

new-buyer enum

holder enum

entry mode semantics

price scenario logic
```

Required:

```text
INVESTMENT_JUDGMENT_LOGIC_CHANGED = 0
```

Prior blind-review results are diagnostic only.

---

# 18. Prior judgment observations are NOT targets

Previous observations:

```text
FIRST: BUY 5 / HOLD 13 / SELL 4
A:     BUY 4 / HOLD 13 / SELL 5
B:     BUY 6 / HOLD 12 / SELL 4

new-buyer WAIT:
16 / 14 / 18
```

Do not target:
- fewer HOLDs
- more ATTRACTIVE
- more SELLs
- any ticker's prior label

No target distribution.

No reference-label prompt.

---

# 19. Freeze before any new model call

Create a new experiment freeze receipt containing:

```text
code commit/tree
prompt hash
builder hash
validator hash
renderer hash
model
reasoning effort
source packet hashes
schema versions
```

After freeze:

```text
code/config/prompt/validator change = 0
```

until the experiment terminates.

---

# 20. Completely new generation

Use:

```text
US14 + KR8 = 22
```

with production-equivalent:

```text
gpt-5.6-sol
xhigh
```

or exact current operating model/effort if it changed.

Required:

```text
NEW_GENERATION_ID != previous generation
```

No reuse of:
- FIRST candidates
- A candidates
- B candidates
- previous blind candidates

---

# 21. FIRST gate

Run a brand-new FIRST.

Required:

```text
FIRST_VALIDATED = 22/22
```

If not:

```text
STOP
```

Do not:
- selective rerun
- repair failed candidate
- edit prompt
- relax validator

Return the frozen failure.

---

# 22. A/B/C gate

Only if FIRST = 22/22.

Then:

```text
A = 22/22
B = 22/22
C = 22/22
```

Same:
- source packets
- model
- effort
- prompt
- schema
- validator
- renderer
- numeric registry
- semantic ownership contracts

No run sees another run's outputs.

---

# 23. Stop policy

If A fails:

```text
stop before B/C
```

If B fails:

```text
stop before C
```

If C fails:

```text
freeze failure
```

No post-result hotfix in the same generation.

---

# 24. Required per-run failure taxonomy

Report counts for:

```text
metric_union_false_reject

unowned_severity_true_reject

probability_language_false_positive

mandatory_trade_false_positive

actionable_trade_true_positive

benign_action_wrapper_repetition

material_substantive_repetition

future_checkpoint_false_reject

LEAF_schema_failure

unsupported_numeric

cross-ticker evidence

cross-generation evidence

accounting/security-basis failure
```

---

# 25. Stability only after clean A/B/C

Do not calculate stability from partial runs.

Only after:

```text
FIRST 22
A 22
B 22
C 22
```

calculate:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Also record:
- balance spread
- direction changes
- new-buyer changes
- holder changes
- entry-mode changes

---

# 26. Boundary uncertainty is allowed

A movement such as:

```text
HOLD 5.5:4.5
↔
BUY 6.0:4.0
```

is not automatically an architecture defect.

Interpret together with:
- action context
- evidence selection
- valuation
- market expectations

Do not tune threshold behavior in this task.

---

# 27. Judgment diagnostic audit

After outputs are frozen, observe:

```text
HOLD basin width
WAIT frequency
Unknown handling
high-expectation valuation weighting
cyclical valuation handling
ADR/security-basis uncertainty
business direction vs entry timing
HOLDABLE vs REVIEW
```

Diagnostic only.

Do not mutate the experiment.

---

# 28. Independent hard-safety matrix

Re-run known safety cases:

```text
unsupported numeric
numeric semantic mismatch
nonexistent evidence ref
cross-ticker evidence ref
cross-generation ref
accounting attribution
ADR/share basis
valuation evidence eligibility
severity escalation
Unknown causal-driver invention
logical OR→AND
logical AND→OR
mandatory actionable trade language
duplicate/terminal lifecycle safety
```

Required:

```text
KNOWN_HARD_SAFETY_REGRESSION = 0
```

---

# 29. Night futures remain independent

Previous night-futures result:

```text
provider =
KRX official fut_bydd_trd archive/history path

support =
PARTIAL

new external dependency =
NO

data readiness =
READY_FOR_PRODUCTION_REVIEW
```

Acceptance fixture:

```text
KOSPI200 202609
2026-09-04 night

O 1055.65
H 1097.65
L 1043.85
C 1093.90
V 32666
```

Reference handling:

```text
prior-night close basis:
+4.28%

header +3.93%:
reference type remains UNKNOWN
```

Do not inject night futures into Structured Autonomy during this experiment.

---

# 30. Night-futures independent production review

Perform read-only / shadow production review only.

Review:

```text
approved provider coverage
session business-date semantics
18:00 → 06:00 cross-midnight
weekend/holiday closed state
contract month identity
roll safety
reference-basis rendering
staleness
fallback behavior
market-message placement
```

No production send.

No scheduler change.

No main merge in this task.

Maximum night-futures verdict:

```text
READY_FOR_BOUNDED_PRODUCTION_INTEGRATION
```

---

# 31. Night futures interpretation boundary

Night futures are:

```text
market/timing context
```

They are not:

```text
company business thesis evidence
earnings evidence
valuation evidence
next-day spot-return guarantee
```

This must remain true in production-review design.

The Investment Knowledge explicitly separates company fundamentals from price/positioning and market context. fileciteturn0file0

---

# 32. Natural infrastructure proof

Previous report states:

```text
INFRA_NATURAL_PROOF = PASS
```

Do not rerun infrastructure repairs unless a new regression is observed.

Preserve current operating behavior.

---

# 33. Production mutation

For this task:

```text
STRUCTURED_AUTONOMY_PRODUCTION_MUTATION = 0

NIGHT_FUTURES_PRODUCTION_MUTATION = 0

PRODUCTION_TELEGRAM_SEND = 0

PRODUCTION_SCHEDULER_CHANGE = 0

PRODUCTION_DB_MUTATION = 0

MAIN_MERGE = 0
```

This task ends at promotion review / integration handoff.

---

# 34. Maximum readiness

Structured Autonomy maximum:

```text
READY_FOR_PRODUCTION_REVIEW
```

only if:

```text
FIRST 22/22
A 22/22
B 22/22
C 22/22
known hard-safety regression = 0
validator false-positive families = 0
GOOGL-style unowned severity remains blocked
full tests pass
```

Night futures maximum:

```text
READY_FOR_BOUNDED_PRODUCTION_INTEGRATION
```

These two verdicts are independent.

---

# 35. Do not merge them automatically

Even if both are ready:

```text
NO MAIN MERGE
```

Return a next-task handoff describing:
- Structured Autonomy production candidate
- night-futures production candidate
- whether they should be integrated together or separately

Actual production integration is a later reviewed task.

---

# 36. Required reports

Create:

1. `docs/reports/20260906-selected-evidence-metric-union-root-cause.md`
2. `docs/reports/20260906-selected-evidence-metric-union-contract.md`
3. `docs/reports/20260906-probability-token-boundary-root-cause.md`
4. `docs/reports/20260906-trade-language-negation-contract.md`
5. `docs/reports/20260906-action-wrapper-repetition-taxonomy.md`
6. `docs/reports/20260906-strengthening-severity-writer-contract.md`
7. `docs/reports/20260906-hard-safety-regression.md`
8. `docs/reports/20260906-experiment-freeze.md`
9. `docs/reports/20260906-fresh-first.md`
10. `docs/reports/20260906-run-a.md`
11. `docs/reports/20260906-run-b.md`
12. `docs/reports/20260906-run-c.md`
13. `docs/reports/20260906-abc-stability.md`
14. `docs/reports/20260906-judgment-diagnostic-audit.md`
15. `docs/reports/20260906-structured-autonomy-promotion-review.md`
16. `docs/reports/20260906-night-futures-production-review.md`
17. `docs/reports/20260906-next-production-integration-handoff.md`
18. `docs/reports/20260906-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 37. Machine-readable proofs

Create:

```text
metric-union-proof.json
probability-token-proof.json
trade-negation-proof.json
repetition-taxonomy-proof.json
severity-writer-proof.json
hard-safety-regression.json
experiment-freeze.json
fresh-first.json
run-a.json
run-b.json
run-c.json
abc-stability.json
structured-autonomy-readiness.json
night-futures-production-review.json
next-integration-handoff.json
```

---

# 38. Required gates

```text
SOURCE_BUNDLE_SHA256 =
00ba4679155d9b7e64ee2d789d8d1d6fa03eb26fae0c5bde97883928e9134e76

PREVIOUS_GENERATION_RESUME =
0 / NONZERO

PREVIOUS_CANDIDATE_REUSE =
0 / NONZERO

CURRENT_MAIN_SHA =
...

CURRENT_OPERATING_SHA =
...

CURRENT_MODEL =
...

CURRENT_REASONING_EFFORT =
...

METRIC_UNION_PRIMARY_SCOPE =
SELECTED_EVIDENCE_ONLY / OTHER

SAME_SEVERITY_METRIC_UNION =
PASS / FAIL

CROSS_SEVERITY_METRIC_UNION_ACCEPTED =
0 / NONZERO

UNOWNED_STRENGTHENING_SEVERITY_ACCEPTED =
0 / NONZERO

PROBABILITY_TOKEN_BOUNDARY =
PASS / FAIL

PROBABILITY_TRUE_POSITIVE_REGRESSION =
0 / NONZERO

NEGATED_TRADE_LANGUAGE =
PASS / FAIL

ACTIONABLE_TRADE_FALSE_NEGATIVE =
0 / NONZERO

BENIGN_ACTION_WRAPPER_HARD_BLOCK =
0 / NONZERO

MATERIAL_SUBSTANTIVE_REPEAT_PROTECTION =
PASS / FAIL

INVESTMENT_JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

NEW_GENERATION_ID =
...

FIRST_VALIDATED =
22 / OTHER

RUN_A_VALIDATED =
22 / OTHER / NOT_RUN

RUN_B_VALIDATED =
22 / OTHER / NOT_RUN

RUN_C_VALIDATED =
22 / OTHER / NOT_RUN

FUTURE_CHECKPOINT_FALSE_REJECT =
0 / NONZERO

LEAF_SCHEMA_FAILURE =
0 / NONZERO

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO

STABLE_COUNT =
... / NOT_MEASURED

BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

UNSTABLE_COUNT =
... / NOT_MEASURED

STRUCTURED_AUTONOMY_READINESS =
READY_FOR_PRODUCTION_REVIEW /
NEEDS_MORE_SHADOW_WORK /
NOT_READY

NIGHT_FUTURES_PRODUCTION_REVIEW =
PASS / FAIL

NIGHT_FUTURES_READINESS =
READY_FOR_BOUNDED_PRODUCTION_INTEGRATION /
NEEDS_MORE_REPAIR /
NOT_READY

STRUCTURED_AUTONOMY_PRODUCTION_MUTATION =
0 / NONZERO

NIGHT_FUTURES_PRODUCTION_MUTATION =
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
```

---

# 39. Stop conditions

Stop if IBM metric union requires packet-wide evidence ownership.

Stop if fixing IBM allows GOOGL-style unowned strengthening severity.

Stop if probability detection is simply disabled.

Stop if trade-language safety is relaxed globally.

Stop if SNDK/TSLA exact text is whitelisted.

Stop if a new ticker exception is added.

Stop if FIRST != 22.

Stop on the first failed A/B/C run.

Do not hotfix in the same generation.

Do not tune BUY/HOLD/SELL distribution.

Do not inject night futures into company investment judgment.

---

# 40. Completion response

Return:

```text
BOUNDED REPAIRS =
IBM metric union ...
MU token boundary ...
SNDK/TSLA negation ...
repetition taxonomy ...
GOOGL severity writer ...

HARD SAFETY =
...

FRESH FIRST =
22/22 ...

A =
22/22 ...

B =
22/22 ...

C =
22/22 ...

STABILITY =
...

JUDGMENT DIAGNOSTICS =
...

STRUCTURED AUTONOMY READINESS =
...

NIGHT FUTURES PRODUCTION REVIEW =
...

NIGHT FUTURES READINESS =
...

PRODUCTION MUTATION =
0

MAIN MERGE =
0

NEXT INTEGRATION HANDOFF =
...

REPORT ZIP =
...

ZIP SHA256 =
...
```

---

# 41. Final principle

The goal is not to make validators permissive.

The goal is to make them precise:

```text
strict about
truth
evidence ownership
severity
numbers
accounting
actionability

flexible about
benign language
safe negation
metric wording
non-substantive repeated wrappers
```

And keep investment judgment independent from validator repair.

