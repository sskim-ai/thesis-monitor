# thesis-monitor — Fibonacci v2 Final P1 Closure
## Deterministic SR Ownership + Canonical Swing-Structure IDs + Variable-AI Consensus / Safe Fallback
## Preserve monthly → weekly → daily hierarchy and all existing Fibonacci math

## Metadata

- Workstream: `FIBONACCI_V2_FINAL_P1_CLOSURE`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_P1_REPAIR`
- Source policy: `FREE_ONLY`
- User-visible production mutation: `0`
- Current Fibonacci state: `SHADOW`
- Current live messages: `UNCHANGED`
- Open Research production integration: preserve `0`
- Trade AR: preserve `OFF`
- Production Assist: preserve current state
- Public Action / operationId / schema: preserve current values

### Required current base

Latest reported safe final main / operating:

`987a684f72b96c9d549eaf4d4328590bb0b7cd81`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Previous implementation

```text
Instruction commit =
d9e6e2327f0f32256a1bd0d8caf2c0b0f1faf890

Implementation =
9ac9a3cf2f6c759fa73ba5cbee6ab55c08ee1901

Report/final main/operating =
987a684f72b96c9d549eaf4d4328590bb0b7cd81
```

### Proven state — do not reopen

```text
MONTHLY_SR_ANALYSIS = PASS
WEEKLY_SR_ANALYSIS = PASS
DAILY_SR_ANALYSIS = PASS

MONTHLY_FIBONACCI = PASS
WEEKLY_FIBONACCI = PASS
DAILY_FIBONACCI = PASS

MULTI_TIMEFRAME_CONFLUENCE = PASS
TIMEFRAME_HIERARCHY = PASS

RICH_CANDLE_CONTEXT_PACKET = PASS
PRICE_ONLY_EVIDENCE_EGRESS = PASS
VARIABLE_AI_RUNTIME_EXECUTED = YES

FIBONACCI_DETERMINISTIC_CALC = PASS
FIBONACCI_NUMERIC_PROVENANCE = PASS
LOOKAHEAD_SAFETY = PASS
KR_US_SCHEMA_COMMON = PASS

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0

P0 = 0
```

### Current material P1

```text
1. Higher-timeframe variable-anchor OR AI-selected deterministic-SR material variation.
2. Ambiguous / insufficient variable-output semantics can be rejected by the backend.
```

### Important root-cause distinction from the frozen trial

The previous aggregate "anchor stability" metric combined two different things:

```text
A. actual Fibonacci swing-anchor variation
B. AI selection of deterministic support/resistance zone IDs
```

The frozen 20-stock trial shows many MATERIAL_VARIATION classifications where the
low/high/correction anchors were identical across all runs and only the AI-selected
support/resistance zone ID changed.

Examples include the prior benchmark pattern:

```text
same low anchor 5/5
same high anchor 5/5
same Fib mode 5/5
but support/resistance zone choices vary
→ previous classifier = MATERIAL_VARIATION
```

This task must separate those ownership domains.

---

# 0. Objective

Close the remaining P1 without weakening any tolerance and without forcing Fibonacci
onto unstable structures.

Target architecture:

```text
deterministic OHLCV
→ deterministic monthly/weekly/daily pivot candidates
→ deterministic monthly/weekly/daily support/resistance ownership
→ deterministic valid swing-structure candidate generation
→ variable AI selects one canonical swing_structure_id OR explicitly abstains
→ backend validates the structure ID
→ backend calculates Fibonacci
→ backend calculates confluence with deterministic SR
→ bounded AI interpretation
→ per-timeframe safe eligibility
→ shadow renderer
```

The AI should no longer choose the authoritative support/resistance zone ID.

The AI's variable judgment should be narrowed to the question the user actually wants AI
to answer:

```text
"Which valid swing structure is the meaningful monthly / weekly / daily Fibonacci basis?"
```

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-fibonacci-anchor-sr-ownership-consensus-bounded-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify current main / operating
2. commit/push this exact instruction as docs-only instruction commit
3. create branch:

`codex/fibonacci-anchor-sr-ownership-consensus-repair`

4. use latest safe main as base
5. no force push/history rewrite
6. remain shadow-only throughout this instruction

---

# 2. Hard prohibitions

Do NOT:

- change deterministic Fibonacci formulas
- widen canonical zone tolerance
- lower look-ahead requirements
- change monthly → weekly → daily hierarchy
- let AI calculate a Fibonacci price
- let AI author authoritative support/resistance numerics
- let AI invent low/high/correction prices or dates
- hard-code ticker-specific anchors
- hard-code stable tickers
- mark an unstable higher-timeframe structure eligible merely to increase coverage
- treat abstention as a failure
- force every stock/timeframe to have Fibonacci
- mutate business investment logic from price structure
- enable the new price section in Telegram in this task
- add a paid provider
- bypass price-only egress governance
- use previous/reference anchor selection inside the primary variable-AI prompt

---

# 3. P1-A — separate deterministic SR ownership from variable AI

## Current problem

The previous variable AI output included:

```text
support_zone_id
resistance_zone_id
```

alongside:

```text
low_pivot_id
high_pivot_id
correction_low_pivot_id
fib_mode
```

This caused support/resistance choice variability to contaminate the Fibonacci anchor-stability
metric even when the actual anchors were identical.

## Required change

Remove authoritative SR ownership from Stage-1 variable AI output.

The backend owns:

```text
monthly canonical support zone
monthly canonical resistance zone

weekly canonical support zone
weekly canonical resistance zone

daily canonical support zone
daily canonical resistance zone
```

using the existing deterministic SR engine.

AI may receive SR zones as context, but may not select the authoritative zone IDs in Stage 1.

---

# 4. Deterministic SR hierarchy — preserve user requirement

For every sufficiently supported stock, keep:

```text
MONTHLY
  deterministic support
  deterministic resistance

WEEKLY
  deterministic support
  deterministic resistance

DAILY
  deterministic support
  deterministic resistance
```

The final analysis order remains:

```text
월봉
→ 주봉
→ 일봉
→ 종합
```

Even when Fibonacci is omitted, deterministic support/resistance remains available.

---

# 5. SR ranking ownership

Audit how the existing deterministic engine chooses/ranks zones.

Reuse current canonical logic.

Do not invent AI-owned ranking.

If more than one deterministic zone is valid per side:

store:

```text
primary_support
secondary_support optional
primary_resistance
secondary_resistance optional
```

using deterministic priority such as the currently owned combination of:

```text
timeframe
zone strength
current-price relation
touch/rejection/reclaim evidence
canonical proximity
```

Do not change the existing ranking algorithm unless an actual correctness defect is found.

---

# 6. Variable AI may interpret SR only after ownership is fixed

Stage-2 interpretation may say:

```text
"주봉 저항이 더 중요한 중기 확인 구간이다"
```

when supported.

But it cannot change:

```text
zone_id
zone_low
zone_high
```

The numeric SR stays backend-owned.

---

# 7. Recompute the old stability results with SR removed

Before introducing any new consensus logic, rerun the frozen archived trial results through a
new diagnostic classifier that ignores AI SR selection.

Report separately:

```text
ANCHOR_STRUCTURE_VARIATION
vs
SR_SELECTION_VARIATION_LEGACY
```

Mandatory counts:

```text
monthly:
  true anchor material variation
  SR-only material variation

weekly:
  true anchor material variation
  SR-only material variation

daily:
  true anchor material variation
  SR-only material variation
```

This report is required to prove that the root cause is correctly separated.

---

# 8. P1-B — canonical swing-structure candidate objects

Do not ask AI to independently compose arbitrary low/high/correction combinations.

The backend should deterministically enumerate valid candidate structures from eligible
confirmed pivots.

Create:

`CANONICAL_SWING_STRUCTURE_CANDIDATE`

Suggested fields:

```text
swing_structure_id
ticker/security
timeframe

mode_eligibility:
  RETRACEMENT
  EXTENSION
  BOTH

low_pivot_id
high_pivot_id
correction_low_pivot_id optional

chronology
anchor prices/dates from canonical refs
structural role candidate
segment refs
candle-neighborhood refs
current regime relation
```

The AI chooses a valid structure ID.

It does not construct one.

---

# 9. Candidate-generation validity rules

A retracement candidate requires:

```text
confirmed low
confirmed later high
low price < high price
same ticker/timeframe/security basis
```

An extension candidate requires:

```text
confirmed low
confirmed later high
confirmed later correction low
date(L) < date(H) < date(C)
same security/timeframe/basis
```

Respect:

```text
pivot confirmation date
cutoff
completed-bar rule
corporate-action basis
```

No future candidate.

---

# 10. Candidate set must preserve real AI choice

Do not collapse to one backend-selected structure.

The candidate set should contain plausible structurally valid alternatives.

The AI still judges:

```text
major base low
breakout origin
higher-low
retest low
major expansion high
correction low
```

from the rich candle evidence.

The backend only eliminates impossible or semantically invalid combinations.

---

# 11. Candidate-count control

Avoid combinatorial explosion.

Rank possible valid structures deterministically for packet inclusion using non-AI features,
for example:

```text
pivot prominence
recency appropriate to timeframe
segment magnitude
reclaim/breakout relevance
volume/trading-value evidence
existing SR interaction
```

Suggested bounded maximum per timeframe:

```text
MONTHLY <= 8 candidate structures
WEEKLY  <= 10
DAILY   <= 12
```

These are starting limits.

If all eligible structures fit, include all.

Report omitted valid structures and reason.

---

# 12. Rich candle evidence remains

Preserve the previous successful price-only evidence packet.

Do not regress:

```text
MONTHLY recent raw OHLCV + candidate neighborhoods
WEEKLY recent raw OHLCV + candidate neighborhoods
DAILY recent raw OHLCV + candidate neighborhoods

body / wick
close location
gap
volume/trading-value relation
HH/LH/HL/LL
breakout/reclaim/rejection
segment context
```

Set:

`RICH_CANDLE_CONTEXT_REGRESSION = PASS / FAIL`

---

# 13. New Stage-1 variable AI schema

Replace the prior Stage-1 support/resistance selection schema.

Per timeframe:

```text
status:
  SELECTED
  AMBIGUOUS
  INSUFFICIENT_STRUCTURE

swing_structure_id:
  required only when SELECTED

alternative_swing_structure_id:
  optional only when SELECTED

confidence:
  HIGH / MEDIUM / LOW

reason_categories:
  bounded taxonomy

evidence_refs:
  pivot / bar / segment refs

concise_reason:
  bounded
```

Remove from Stage 1:

```text
support_zone_id
resistance_zone_id
raw price fields
raw Fibonacci numeric fields
```

---

# 14. Strict output semantics

## SELECTED

Must have:

```text
valid swing_structure_id
```

May have:

```text
one alternative_swing_structure_id
```

Must not have unsupported free-form anchor IDs outside the selected structure.

## AMBIGUOUS

Must have:

```text
swing_structure_id = null
alternative = null
```

May include evidence refs and concise reason.

Result:

```text
Fib omitted for that timeframe
deterministic SR preserved
```

## INSUFFICIENT_STRUCTURE

Must have:

```text
swing_structure_id = null
alternative = null
```

Result:

```text
Fib omitted for that timeframe
deterministic SR preserved
```

Do not allow a semantically "insufficient" output to simultaneously select authoritative zones
or a partial Fib structure.

---

# 15. Ambiguous/insufficient is a valid terminal state

This is important.

The backend should classify a schema-valid abstention as:

```text
VALID_ABSTENTION
```

not:

```text
semantic rejection
```

A true rejection is reserved for:

```text
invalid ID
wrong ticker
wrong timeframe
invalid evidence ref
malformed schema
chronology mismatch
future pivot
```

Target:

`VALID_ABSTENTION_REJECTED = 0`

---

# 16. Evidence-ref semantics for abstention

For `AMBIGUOUS` / `INSUFFICIENT_STRUCTURE`:

evidence refs may point to:

```text
bars
pivots
segments
```

that justify abstention.

They should not be required to include a selected structure.

Validate all refs exist in the same timeframe packet.

This closes the prior ambiguous/insufficient evidence-ref semantic P1.

---

# 17. Actual variable AI consensus trial

After the schema/candidate repair, rerun the same frozen protocol.

For exact benchmark packets:

```text
5 independent variable-AI calls
```

For wider eligible universe:

```text
3 independent variable-AI calls
```

Use the same approved price-only runtime path.

Do not lower randomness or otherwise manufacture deterministic output solely to pass.

---

# 18. Consensus classification — structure IDs only

Measure Stage-1 stability from:

```text
status
swing_structure_id
alternative structure
```

Do not include deterministic SR zone IDs.

Classify:

## STABLE

All repeated valid selections:
- choose the same structure ID
- OR choose structures whose deterministic Fib / confluence output is structurally equivalent
  under the existing canonical tolerance.

## MINOR_VARIATION

Different valid structures produce:
- same user-visible price zone
- same timeframe role
- same structural interpretation

## MATERIAL_VARIATION

Repeated runs produce:
- different visible Fib/confluence zones
- or SELECTED vs materially different SELECTED structures
- or materially different structural interpretation

`AMBIGUOUS` / `INSUFFICIENT_STRUCTURE` is not itself material variation.

---

# 19. Strict higher-timeframe consensus gate

For first user-visible eligibility:

## MONTHLY

Eligible Fibonacci only when:

```text
5-run benchmark or 3-run wider trial
= no MATERIAL_VARIATION
```

## WEEKLY

Same.

If monthly or weekly is materially unstable:

```text
that timeframe Fib omitted
```

Do not automatically reject the whole stock if deterministic SR remains safe.

However first full price-structure enablement may require at least monthly/weekly SR to remain
deterministic and stable, which they already should.

---

# 20. Daily consensus gate

Daily Fibonacci may be omitted more aggressively.

If:

```text
daily = MATERIAL_VARIATION
```

then:

```text
daily deterministic SR remains
daily Fib omitted
```

Monthly/weekly outputs survive.

---

# 21. Per-timeframe eligibility object

Create:

```text
price_structure_eligibility:
  monthly:
    sr = ELIGIBLE / UNAVAILABLE
    fib = ELIGIBLE / OMIT_AMBIGUOUS / OMIT_UNSTABLE / OMIT_INSUFFICIENT

  weekly:
    same

  daily:
    same
```

Do not use one stock-level boolean as the only gate.

A stock can therefore show:

```text
월봉 SR + Fib
주봉 SR only
일봉 SR + Fib
```

if that is what the evidence supports.

---

# 22. Optional consensus selection state

For shadow/readiness, generate a canonical trial consensus result:

```text
CONSENSUS_SELECTED
VALID_ABSTENTION
UNSTABLE
```

Do not persist it as business/monitoring state.

If later enabled, a separate task may decide whether to persist technical anchor state.

This task should not introduce thesis-state mutation.

---

# 23. No tolerance widening

All structure-equivalence decisions must use:

```text
existing canonical zone tolerance
```

Hard target:

`TOLERANCE_WIDENING = 0`

Do not reduce material-variation counts by making distant levels "equivalent."

---

# 24. Reference harness role

Keep the old deterministic/reference harness only as:

```text
POST_TRIAL COMPARISON
```

It must not:

- seed AI
- decide current eligibility
- override variable-AI consensus

Compare after the independent trial.

---

# 25. Stage-2 interpretation

After:

```text
deterministic SR
+ validated/consensus Fib structure
+ deterministic Fib calculation
+ confluence
```

AI may interpret:

```text
월봉 구조
주봉 구조
일봉 구조
timeframe conflict/alignment
which nearby zone matters first
which higher-timeframe zone matters structurally
```

It may not change IDs or prices.

---

# 26. Shadow message contract

Keep the intended layout:

```text
📐 가격 구조

월봉
• 지지
• 저항
• 피보나치 — only if eligible

주봉
• 지지
• 저항
• 피보나치 — only if eligible

일봉
• 지지
• 저항
• 피보나치 — only if eligible

종합
• 구조적으로 중요한 구간
• 현재가가 먼저 만나는 tactical 구간
• 다중 timeframe confluence if eligible
• 다음 확인
```

A missing Fib line must not remove the timeframe's SR analysis.

---

# 27. Coverage is not the objective

Do not define success as:

```text
20/20 stocks show Fibonacci
```

Success is:

```text
deterministic SR always safe where available
+
Fibonacci shown only on defensible variable-AI swing structures
```

A lower Fib coverage rate is acceptable.

---

# 28. Reclassify P1 vs safe omission

After this repair:

```text
unstable Fib timeframe
→ safe omission
```

should be a normal controlled state, not an open material P1, provided:

```text
no unstable Fib becomes eligible
deterministic SR remains correct
packet continues
```

The P1 is:

```text
unstable structure exposed
```

not:

```text
AI sometimes abstains
```

---

# 29. Required frozen diagnostic report

Create:

`docs/reports/20260826-fibonacci-anchor-vs-sr-variation-root-cause.md`

Must show previous 20-stock results split into:

```text
true anchor variation
SR-only selection variation
mixed variation
stable
```

by timeframe.

Include exact ticker/timeframe list.

---

# 30. Required candidate-structure audit

Create:

`docs/reports/20260826-canonical-swing-structure-candidate-audit.md`

For every ticker/timeframe:

```text
eligible pivots
valid retracement structures
valid extension structures
included structures
omitted structures
reason
```

No raw secret/private data.

---

# 31. Required semantic-abstention audit

Create:

`docs/reports/20260826-fibonacci-abstention-semantics-audit.md`

Report:

```text
AMBIGUOUS count
INSUFFICIENT count
VALID_ABSTENTION count
true semantic rejection count
invalid evidence-ref count
```

Target:

```text
VALID_ABSTENTION_REJECTED = 0
```

---

# 32. Required exact benchmark

Create:

`docs/reports/20260826-fibonacci-consensus-exact-benchmark.md`

Use the previous 4 human benchmark stocks at minimum.

For each timeframe show:

```text
deterministic SR

candidate swing structures

RUN 1
RUN 2
RUN 3
RUN 4
RUN 5

status
selected swing_structure_id
alternative if any

deterministic Fib from each distinct selected structure
visible zone result
consensus classification

final timeframe eligibility
```

---

# 33. Required full shadow replay

Run:

```text
KR monitored universe
US monitored universe
```

with the repaired variable selection path.

Report actual counts.

Do not hard-code the prior 7/13 if the monitored universe changes.

---

# 34. Stability summary

Report separately:

```text
MONTHLY
stable
minor
material
valid abstention

WEEKLY
stable
minor
material
valid abstention

DAILY
stable
minor
material
valid abstention
```

Also report:

```text
eligible Fib timeframes
omitted unstable timeframes
omitted ambiguous timeframes
omitted insufficient timeframes
```

---

# 35. Critical exposure metric

Set:

```text
UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0
```

This is the primary safety target.

Do not require:

```text
MATERIAL_VARIATION = 0 across the entire universe
```

if those cases are safely omitted.

---

# 36. Deterministic SR stability metric

Because SR is now backend-owned:

rerun the same frozen evidence multiple times and confirm:

```text
MONTHLY_SR_RUNTIME_VARIATION = 0
WEEKLY_SR_RUNTIME_VARIATION = 0
DAILY_SR_RUNTIME_VARIATION = 0
```

The AI runtime must have no ownership over those numeric zones.

---

# 37. Existing numeric safety — preserve

Hard targets:

```text
AI_CALCULATED_FIB_PRICE = 0
UNREGISTERED_FIBONACCI_NUMERIC = 0
ANCHOR_PRICE_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_TICKER_MISMATCH = 0
LOOKAHEAD_LEAK = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0
```

---

# 38. Semantic safety — preserve

Hard targets:

```text
FIBONACCI_AS_CERTAIN_CAUSE = 0
FIBONACCI_AS_GUARANTEED_REVERSAL = 0
FIBONACCI_AS_BUSINESS_THESIS_CHANGE = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
TIMEFRAME_ROLE_CONFUSION = 0
ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
```

---

# 39. Runtime/egress safety — preserve

Hard targets:

```text
PRIVATE_FIELD_EGRESS = 0
SECRET_EGRESS = 0
UNRELATED_THESIS_EGRESS = 0
```

Use the same approved price-only runtime restrictions.

No new provider.

---

# 40. Focused tests — SR ownership

Required:

- Stage-1 AI schema has no authoritative SR selection fields
- deterministic monthly SR independent of AI run
- deterministic weekly SR independent of AI run
- deterministic daily SR independent of AI run
- AI may interpret but cannot change SR ID/value
- invalid/absent Fib does not remove deterministic SR

---

# 41. Focused tests — candidate structures

Required:

- valid low→high retracement candidate
- valid low→high→correction extension candidate
- chronology enforcement
- confirmed-pivot enforcement
- same-timeframe enforcement
- security/basis enforcement
- no future candidate
- bounded candidate count
- omitted candidate audit

---

# 42. Focused tests — output semantics

Required:

### SELECTED
- valid structure ID accepted
- invalid structure ID rejected

### AMBIGUOUS
- null structure accepted as VALID_ABSTENTION
- no Fib emitted
- SR survives

### INSUFFICIENT_STRUCTURE
- null structure accepted as VALID_ABSTENTION
- no Fib emitted
- SR survives

### malformed
- true rejection
- packet continues

---

# 43. Focused tests — consensus

Required:

- 3/3 same structure → STABLE
- 5/5 same structure → STABLE
- different structures / same canonical visible zone → STABLE or MINOR
- materially different visible zones → MATERIAL
- MATERIAL → Fib omitted
- deterministic SR remains
- no tolerance widening
- one timeframe unstable does not remove other timeframe outputs

---

# 44. Regression — rich candle context

Ensure the prior repair does not regress:

```text
raw OHLCV windows
candidate neighborhoods
deterministic candle features
segment refs
price-only egress
```

Set:

`RICH_CANDLE_CONTEXT_REGRESSION = PASS`

---

# 45. KR/US schema parity

Use one common:

```text
swing_structure_id
status
confidence
reason categories
```

schema.

Market differences remain only:

```text
calendar
provider
currency
corporate-action basis
```

Set:

`KR_US_SWING_STRUCTURE_SCHEMA_COMMON = PASS / FAIL`

---

# 46. Shadow-only production isolation

Hard target:

```text
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```

Also:

```text
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

This instruction must not enable the feature.

---

# 47. Readiness policy

The engine may become:

```text
AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE =
INTEGRATED_READY_NOT_ARMED
```

when all of the following hold:

```text
deterministic SR ownership separated
valid abstention semantics PASS
candidate structure schema PASS
variable AI trial actually executed
rich candle context preserved
no unstable Fib is user-visible eligible
numeric/security/lookahead safety all zero
KR/US shadow replay PASS
full tests/CI PASS
P0 = 0
material P1 = 0
```

It is NOT required that every timeframe on every stock have a stable Fib.

---

# 48. Production enablement readiness

Set:

`PRODUCTION_ENABLEMENT_READY = YES`

only when the engine is safe for a later bounded enablement.

Do not enable it here.

The next task after PASS should be:

```text
BOUNDED_MULTI_TIMEFRAME_FIBONACCI_ENABLEMENT
```

---

# 49. Required architecture docs

Create/update:

1. `docs/architecture/FIBONACCI_SR_OWNERSHIP.md`
2. `docs/architecture/CANONICAL_SWING_STRUCTURE_CANDIDATE.md`
3. `docs/architecture/FIBONACCI_VALID_ABSTENTION.md`
4. `docs/architecture/AI_ANCHOR_CONSENSUS_POLICY.md`
5. update `AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE.md`
6. update `PRICE_STRUCTURE_SHADOW_POLICY.md`

---

# 50. Required reports

Create:

1. `docs/reports/20260826-fibonacci-anchor-vs-sr-variation-root-cause.md`
2. `docs/reports/20260826-fibonacci-sr-ownership-repair.md`
3. `docs/reports/20260826-canonical-swing-structure-candidate-audit.md`
4. `docs/reports/20260826-fibonacci-abstention-semantics-audit.md`
5. `docs/reports/20260826-fibonacci-consensus-exact-benchmark.md`
6. `docs/reports/20260826-fibonacci-consensus-stability.md`
7. `docs/reports/20260826-fibonacci-consensus-kr-shadow-replay.md`
8. `docs/reports/20260826-fibonacci-consensus-us-shadow-replay.md`
9. `docs/reports/20260826-fibonacci-final-p1-safety-parity.md`
10. `docs/reports/20260826-fibonacci-final-p1-readiness.md`
11. `docs/reports/20260826-fibonacci-final-p1-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-fibonacci-final-p1-readiness.json`

---

# 51. Full validation

Required:

```text
root-cause split audit complete
focused SR ownership tests PASS
focused candidate structure tests PASS
focused abstention tests PASS
focused consensus tests PASS
rich candle context regression PASS
KR shadow replay PASS
US shadow replay PASS
variable AI 5/3 protocol completed
lookahead safety PASS
numeric provenance PASS
egress safety PASS
current user-visible diff = 0
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action unchanged
operationId/schema unchanged
implementation SHA Actions PASS
final main Actions PASS
API /health PASS
worktrees clean
```

---

# 52. Gates

Set exactly:

```text
SR_AI_OWNERSHIP_SEPARATED =
PASS / FAIL

MONTHLY_SR_RUNTIME_VARIATION =
0 / NONZERO

WEEKLY_SR_RUNTIME_VARIATION =
0 / NONZERO

DAILY_SR_RUNTIME_VARIATION =
0 / NONZERO

CANONICAL_SWING_STRUCTURE_CANDIDATES =
PASS / FAIL

VARIABLE_AI_SWING_STRUCTURE_SELECTION =
PASS / PARTIAL / FAIL

VALID_ABSTENTION_SEMANTICS =
PASS / FAIL

VALID_ABSTENTION_REJECTED =
0 / NONZERO

MONTHLY_FIB_STABILITY =
PASS / PARTIAL / FAIL

WEEKLY_FIB_STABILITY =
PASS / PARTIAL / FAIL

DAILY_FIB_STABILITY =
PASS / PARTIAL / FAIL

UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

RICH_CANDLE_CONTEXT_REGRESSION =
PASS / FAIL

FIBONACCI_DETERMINISTIC_CALC =
PASS / FAIL

FIBONACCI_NUMERIC_PROVENANCE =
PASS / FAIL

LOOKAHEAD_SAFETY =
PASS / FAIL

KR_US_SWING_STRUCTURE_SCHEMA_COMMON =
PASS / FAIL

KR_SHADOW_REPLAY =
PASS / FAIL

US_SHADOW_REPLAY =
PASS / FAIL

CURRENT_USER_VISIBLE_MESSAGE_DIFF =
0 / NONZERO

AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 53. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

SR_AI_OWNERSHIP_SEPARATED = ...

PREVIOUS_TRUE_ANCHOR_MATERIAL_VARIATION =
  monthly ...
  weekly ...
  daily ...

PREVIOUS_SR_ONLY_MATERIAL_VARIATION =
  monthly ...
  weekly ...
  daily ...

MONTHLY_SR_RUNTIME_VARIATION = ...
WEEKLY_SR_RUNTIME_VARIATION = ...
DAILY_SR_RUNTIME_VARIATION = ...

CANONICAL_SWING_STRUCTURE_CANDIDATES = ...
VARIABLE_AI_SWING_STRUCTURE_SELECTION = ...

VALID_ABSTENTION_SEMANTICS = ...
VALID_ABSTENTION_COUNT = ...
VALID_ABSTENTION_REJECTED = ...

MONTHLY_FIB_STABILITY = ...
WEEKLY_FIB_STABILITY = ...
DAILY_FIB_STABILITY = ...

MONTHLY_MATERIAL_VARIATION_COUNT = ...
WEEKLY_MATERIAL_VARIATION_COUNT = ...
DAILY_MATERIAL_VARIATION_COUNT = ...

MONTHLY_VALID_ABSTENTION_COUNT = ...
WEEKLY_VALID_ABSTENTION_COUNT = ...
DAILY_VALID_ABSTENTION_COUNT = ...

ELIGIBLE_FIB_TIMEFRAMES = ...
OMITTED_UNSTABLE_FIB_TIMEFRAMES = ...
OMITTED_AMBIGUOUS_FIB_TIMEFRAMES = ...
OMITTED_INSUFFICIENT_FIB_TIMEFRAMES = ...

UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0

RICH_CANDLE_CONTEXT_REGRESSION = ...

AI_CALCULATED_FIB_PRICE = 0
UNREGISTERED_FIBONACCI_NUMERIC = 0
ANCHOR_PRICE_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_TICKER_MISMATCH = 0
LOOKAHEAD_LEAK = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

PRIVATE_FIELD_EGRESS = 0
SECRET_EGRESS = 0
UNRELATED_THESIS_EGRESS = 0

FIBONACCI_AS_CERTAIN_CAUSE = 0
FIBONACCI_AS_GUARANTEED_REVERSAL = 0
FIBONACCI_AS_BUSINESS_THESIS_CHANGE = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

KR_US_SWING_STRUCTURE_SCHEMA_COMMON = ...
KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_MULTI_TIMEFRAME_FIBONACCI_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 54. Mandatory ZIP

Create:

`20260826-fibonacci-anchor-sr-ownership-consensus-bounded-repair-bundle.zip`

Include:
- this exact instruction
- root-cause split report
- SR ownership report
- candidate structure audit
- abstention audit
- exact 5-run benchmark
- consensus stability report
- KR/US shadow replay
- safety parity
- readiness report
- artifact index

Never include secrets, credentials, auth headers, account identifiers, or private chain-of-thought.

Compute/report SHA-256.

---

# 55. Severity

## P0

- wrong price/date/ticker anchor
- future/unconfirmed pivot
- AI-calculated numeric exposed
- wrong adjustment/security basis
- unsupported target/stop
- business investment logic changed by price/Fib
- private/secret egress
- shadow output leaks into live message
- replay mutates production state

## P1

- AI still owns authoritative SR zone selection
- valid abstention is rejected as an error
- materially unstable monthly/weekly Fib remains eligible
- candidate structure generator omits a material valid swing without audit
- wide tolerance hides real structural difference
- deterministic SR varies across identical frozen evidence because of variable AI
- malformed variable output blocks the entire packet

## P2

- some timeframes omit Fib because AI is ambiguous
- daily Fib often omitted
- exact anchor IDs vary but visible canonical zone is equivalent
- no Fib value on range-bound names
- coverage is lower than the monitored-stock count
- minor wording differences

---

# 56. Final principle

The previous trial proved a useful fact:

```text
variable AI can read the candle evidence,
but asking it to own both swing selection and support/resistance selection
creates unnecessary instability.
```

The final architecture should therefore be:

```text
DETERMINISTIC:
monthly/weekly/daily support-resistance

VARIABLE AI:
which valid swing structure is the meaningful Fibonacci basis?

DETERMINISTIC:
validate structure
calculate Fibonacci
calculate confluence

AI:
interpret the validated structure
```

And when the swing is genuinely ambiguous:

```text
show deterministic monthly/weekly/daily SR
omit Fibonacci
```

That is a successful output, not a failure.

Do not make Fibonacci coverage the objective.
Make defensible price structure the objective.
