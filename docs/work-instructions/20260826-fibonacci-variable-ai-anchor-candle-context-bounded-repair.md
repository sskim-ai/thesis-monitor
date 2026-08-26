# thesis-monitor — Fibonacci v2 P1 Closure
## Variable AI Anchor Trial + Rich Candle Context Bounded Repair
## Preserve existing multi-timeframe SR/Fibonacci engine; prove real AI swing selection before enablement

## Metadata

- Workstream: `FIBONACCI_V2_VARIABLE_AI_ANCHOR_P1_CLOSURE`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_P1_REPAIR_AND_SHADOW_VALIDATION`
- Source policy: `FREE_ONLY`
- User-visible production mutation: `0`
- Current live messages: `UNCHANGED`
- AI Fibonacci state at start: `SHADOW`
- Open Research production integration: preserve `0`
- Trade AR: preserve `OFF`
- Free Analyst full mode: preserve current state
- Existing live/canary configuration: preserve current state/limits
- Public Action / operationId / schema: preserve current values

### Required base

Latest reported safe main / operating after Fibonacci v2:

`cfb7838e065ea76f9c224bc71309fb251d67e4f8`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Previous Fibonacci v2 result

```text
EXISTING_FIBONACCI_PATH = COMPUTED_NOT_RENDERED
CURRENT_SR_ARCHITECTURE = MULTI_TIMEFRAME_COLLAPSED

MONTHLY_SR_ANALYSIS = PASS
WEEKLY_SR_ANALYSIS = PASS
DAILY_SR_ANALYSIS = PASS

MONTHLY_FIBONACCI = PASS
WEEKLY_FIBONACCI = PASS
DAILY_FIBONACCI = PASS
MULTI_TIMEFRAME_CONFLUENCE = PASS
TIMEFRAME_HIERARCHY = PASS

PRICE_STRUCTURE_EVIDENCE_PACKET = PASS
AI_SWING_ANCHOR_SELECTION = PASS
ANCHOR_SELECTION_STABILITY = PARTIAL
COMPACT_EVIDENCE_SUFFICIENCY = PASS

FIBONACCI_DETERMINISTIC_CALC = PASS
FIBONACCI_NUMERIC_PROVENANCE = PASS
LOOKAHEAD_SAFETY = PASS
KR_US_MULTI_TIMEFRAME_SCHEMA_COMMON = PASS

KR_SHADOW_REPLAY = 7/7
US_SHADOW_REPLAY = 13/13

MATERIAL_VALUE = 10
MINOR_VALUE = 2
NO_ADDED_VALUE = 8
WORSE = 0

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 1

AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = SHADOW
PRODUCTION_ENABLEMENT_READY = NO
```

### Exact remaining P1

The previous implementation proved:

```text
multi-timeframe deterministic structure
+ Fibonacci math
+ provenance
+ look-ahead safety
```

but did **not** prove production-equivalent variable AI anchor selection.

The previous selector evidence was also too compressed:

```text
confirmed pivot IDs
+ strong/medium support/resistance candidates
```

without enough raw candle structure for the AI to independently judge which swing is meaningful.

This instruction closes only that P1.

---

# 0. Objective

Do not redesign the Fibonacci engine.

The repair is:

```text
CURRENT
deterministic OHLCV
→ compressed pivot/zone evidence
→ reference/archived anchor selection
→ deterministic Fibonacci

TARGET
deterministic OHLCV
→ richer MONTHLY/WEEKLY/DAILY candle evidence
→ approved variable AI runtime selects anchor IDs
→ backend validates IDs
→ deterministic Fibonacci
→ deterministic confluence
→ AI bounded interpretation
```

The success condition is not:

```text
AI always selects exactly the same pivot ID
```

The success condition is:

```text
repeated variable-AI selections do not create materially unstable
user-visible price structures.
```

If materially unstable:
- keep the stock/timeframe shadow-only
- omit Fibonacci for that timeframe
- do not block the whole packet

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-fibonacci-variable-ai-anchor-candle-context-bounded-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating
2. commit/push this exact instruction as a docs-only instruction commit
3. record instruction commit/base SHA
4. create branch:

`codex/fibonacci-variable-ai-anchor-candle-context-repair`

5. no force push/history rewrite
6. no user-visible Fibonacci enablement in this instruction

---

# 2. Hard prohibitions

Do NOT:

- modify the existing deterministic Fibonacci formulas
- modify the monthly→weekly→daily hierarchy
- replace existing support/resistance numeric ownership
- let AI return raw anchor prices as authoritative facts
- let AI calculate Fibonacci levels
- let AI invent bar dates
- let AI reference bar/pivot IDs outside the supplied packet
- add a new paid AI/provider dependency
- bypass evidence-egress governance
- send private monitoring/user/account data to an unapproved external runtime
- send secrets/tokens/auth headers
- persist hidden chain-of-thought
- weaken numeric/semantic/temporal validators
- enable this feature in Telegram/live messages
- mutate monitoring state during trials
- change business investment logic from price/Fibonacci output

---

# 3. First task — audit the actual v2 selector path

Before changing code, document exactly what v2 did.

Create:

`docs/reports/20260826-fibonacci-v2-selector-path-audit.md`

Show:

```text
selector implementation
runtime used
whether runtime was variable
whether external inference actually occurred
exact fields supplied
exact fields omitted
how anchor IDs were selected
how archived/reference selection was used
why ANCHOR_SELECTION_STABILITY became PARTIAL
```

Mandatory explicit answer:

```text
WAS_VARIABLE_AI_RUNTIME_ACTUALLY_EXECUTED =
YES / NO
```

Do not call a deterministic reference harness a variable AI trial.

---

# 4. Evidence-egress governance audit

The prior blocker was that variable AI anchor selection could not run without approval for evidence egress.

Do not bypass this.

Audit whether the repository already has an approved AI inference route used for existing production/shadow AI analysis.

Set:

```text
APPROVED_VARIABLE_AI_RUNTIME =
AVAILABLE /
AVAILABLE_WITH_FIELD_RESTRICTIONS /
UNAVAILABLE
```

If unavailable:

```text
VARIABLE_AI_TRIAL = BLOCKED_EGRESS
PRODUCTION_ENABLEMENT_READY = NO
```

and stop before fake validation.

No alternative paid API may be added.

---

# 5. Price-only external evidence allowlist

The anchor-selection task should need only public market-price structure.

Build an explicit allowlist.

Allowed candidate fields:

```text
ticker/security identity
market
currency
timeframe
completed bar IDs/dates
OHLCV
trading value if public/available
pivot IDs / roles
deterministic candle features
support/resistance candidate IDs
Bollinger facts if public price-derived
current price
session/as_of
```

Do NOT include unless separately justified:

```text
user identity
account data
portfolio size
cost basis
private notes
API credentials
notification metadata
Telegram IDs
private thesis prose
unrelated company evidence
```

The first variable anchor-selection packet should be:

`PRICE_ONLY_AI_ANCHOR_PACKET`

---

# 6. Two-stage AI separation

Do not let calculated Fibonacci levels bias swing selection.

## Stage 1 — Anchor selection

AI receives:

```text
price-only candle/pivot/SR evidence
```

It does NOT receive:
- precomputed Fibonacci levels for candidate swings
- target-like outputs
- previous AI selected anchors unless explicitly testing stability/reference comparison

Returns only IDs/roles/confidence.

## Stage 2 — Interpretation

After backend:
- validates anchor IDs
- calculates Fib
- computes confluence

the bounded interpretation step may receive the validated results.

---

# 7. Rich candle context — general rule

The AI must be able to judge:

```text
why this low matters
why another low is less meaningful
whether the selected high belongs to the same swing
whether the correction is structural or noise
```

Therefore do not send only pivot IDs.

For each timeframe include:

```text
A. confirmed major pivot sequence
B. raw OHLCV around serious pivot candidates
C. recent continuous raw OHLCV window
D. deterministic candle-shape features
E. deterministic swing relations
F. existing timeframe-owned SR candidates
```

---

# 8. Raw OHLCV window policy

Use configurable bounded windows, not arbitrary prose summaries.

Recommended starting envelope for shadow evaluation:

```text
MONTHLY
- recent completed bars: up to 36
- candidate neighborhood: ±2 completed monthly bars

WEEKLY
- recent completed bars: up to 52
- candidate neighborhood: ±3 completed weekly bars

DAILY
- recent completed bars: up to 90
- candidate neighborhood: ±5 completed daily bars
```

These are benchmark defaults, not permanent sacred constants.

If the current token/context budget requires smaller windows:
- reduce only after compact-vs-full comparison
- document what was removed
- prove no material anchor loss

For older major pivots outside the recent window:
always include their bounded neighborhoods.

---

# 9. Candidate coverage rule

Do not only send the backend's top one or two pivot candidates.

For each timeframe send all confirmed major candidates that satisfy the current deterministic eligibility rule within the approved structural lookback, subject to the existing evidence budget.

If too many:

rank for packet inclusion by deterministic, non-AI features such as:

```text
prominence
touch/rejection count
volume confirmation
structural recency
breakout/reclaim relevance
```

but keep enough alternatives for the AI to make a real choice.

Report:

```text
eligible_candidate_count
included_candidate_count
omitted_candidate_count
omission_reason
```

---

# 10. Deterministic candle features

For every supplied raw bar, where safely computable, attach:

```text
range
body
upper_wick
lower_wick
close_location
gap relation
volume ratio
trading-value ratio
higher-high/lower-high
higher-low/lower-low
breakout
reclaim
rejection
```

Do not replace raw OHLCV with these features.

The AI receives both:
- raw bar values
- deterministic features

within the bounded window.

---

# 11. Swing-segment context

Between major candidate pivots, provide deterministic segment summaries:

```text
start/end pivot refs
bar count
price change
max drawdown from segment high if safely computed
volume expansion/contraction relation
breakout/reclaim/rejection facts
```

No model-generated summary in the anchor-selection packet.

---

# 12. Monthly packet requirements

Monthly AI anchor selection should have enough context to distinguish:

```text
major cycle low
large base low
structural breakout origin
minor monthly pullback
```

Minimum evidence:

```text
monthly pivot sequence
recent completed monthly OHLCV
all serious monthly low/high candidate neighborhoods
monthly SR candidates
major reclaim/rejection facts
```

Monthly remains structural.

---

# 13. Weekly packet requirements

Weekly AI anchor selection should distinguish:

```text
intermediate base
breakout/retest
higher-low
major corrective low
minor weekly noise
```

Minimum evidence:

```text
weekly pivot sequence
recent completed weekly OHLCV
candidate neighborhoods
weekly SR candidates
weekly breakout/retest facts
```

Weekly remains intermediate.

---

# 14. Daily packet requirements

Daily AI anchor selection should distinguish:

```text
nearest tactical swing
false breakout
reclaim
recent correction
short-term rejection
```

Minimum evidence:

```text
daily pivot sequence
recent completed daily OHLCV
candidate neighborhoods
daily SR candidates
volume/trading-value context
```

Daily remains tactical.

---

# 15. Variable AI output schema

The AI returns structured IDs only.

Required schema per timeframe:

```text
status:
  SELECTED /
  INSUFFICIENT_STRUCTURE /
  AMBIGUOUS

support_zone_id: optional
resistance_zone_id: optional

fib_mode:
  RETRACEMENT /
  EXTENSION /
  BOTH /
  NONE

low_pivot_id: optional
high_pivot_id: optional
correction_low_pivot_id: optional

alternative:
  low_pivot_id
  high_pivot_id
  correction_low_pivot_id
  reason_category
  optional

confidence:
  HIGH / MEDIUM / LOW

evidence_refs:
  pivot IDs
  bar IDs
  SR IDs

concise_reason:
  max bounded short rationale
```

No free numeric price fields.

---

# 16. Reason-category taxonomy

To make auditability stronger, require one or more bounded reason categories:

```text
MAJOR_BASE
BREAKOUT_ORIGIN
HIGHER_LOW
RETEST_SUPPORT
PRIOR_HIGH_RECLAIM
EXPANSION_SWING
CORRECTIVE_LOW
REJECTION_HIGH
STRUCTURAL_CYCLE_LOW
AMBIGUOUS_COMPETING_SWINGS
```

The concise prose reason is optional supporting text.

Do not use reason categories as mechanical selection rules.

---

# 17. Anchor validator remains authoritative

After AI output, backend validates:

```text
ID exists
ticker/security matches
timeframe matches
bar/pivot is eligible at cutoff
date/price matches canonical data
chronology valid
low < high where required
correction low valid
adjustment basis consistent
no future/partial pivot
```

If invalid:

```text
that timeframe = REJECTED
Fib omitted
current deterministic SR remains
```

No auto-repair by guessing.

---

# 18. Actual variable AI trial — mandatory

Once an approved runtime is available, run real repeated trials.

Use the same frozen evidence packet repeatedly with the **actual intended runtime path/configuration**.

Do not force deterministic settings solely to manufacture stability.

Record runtime revision/config hash where the system already supports it.

No secrets/model-private metadata in user-visible reports.

---

# 19. Trial counts

For the exact human benchmark set:

```text
5 independent variable-AI selections per frozen packet
```

For the wider monitored universe:

```text
minimum 3 independent selections per eligible packet
```

If runtime governance/cost constraints make this impossible:
report the exact constraint and do not claim full stability PASS.

No new paid provider may be introduced.

---

# 20. Benchmark universe

Use at least:

```text
2 KR stocks
2 US stocks
```

and include evidence-driven cases representing:

```text
strong extension/uptrend
retracement/pullback
mixed monthly/weekly/daily structure
ambiguous/no-value structure
```

Do not hard-code only names that produce stable anchors.

Also run the broader monitored universe where OHLCV suffices.

---

# 21. Stability metrics — exact anchor stability

For every timeframe compute:

```text
primary low anchor selection frequency
primary high anchor selection frequency
correction low selection frequency
fib_mode frequency
support zone selection frequency
resistance zone selection frequency
```

Do not judge stability from final prose.

---

# 22. Stability metrics — structural equivalence

Different pivot IDs may still create materially equivalent price structures.

Define:

`STRUCTURE_EQUIVALENT`

when repeated runs may choose different eligible anchors but, after deterministic calculation:

```text
same timeframe role
same Fib mode or functionally equivalent mode
same major support/resistance relation
same final visible zone under canonical zone proximity/tolerance
no material change in structural interpretation
```

Use the existing canonical price-zone tolerance.

Do not invent a wide tolerance to pass the test.

---

# 23. Stability classification

Classify each timeframe:

## STABLE

```text
anchor choice identical
OR
anchor differs but all resulting user-visible structures are equivalent
```

## MINOR_VARIATION

```text
different anchor/ratio detail
but same visible structural/tactical conclusion and same canonical zone
```

## MATERIAL_VARIATION

```text
different runs create materially different visible support/resistance/Fib zones
or change structural interpretation
```

No user-visible eligibility for a timeframe classified `MATERIAL_VARIATION`.

---

# 24. Stock-level eligibility

A stock may still be eligible if:

```text
monthly = STABLE
weekly = STABLE
daily = MATERIAL_VARIATION
```

with daily Fibonacci omitted.

The shadow renderer should fall back per timeframe, not per whole stock.

Example:

```text
monthly SR/Fib shown
weekly SR/Fib shown
daily deterministic SR only
```

---

# 25. Higher-timeframe safety threshold

Because monthly/weekly are structurally more important:

If:

```text
MONTHLY = MATERIAL_VARIATION
or
WEEKLY = MATERIAL_VARIATION
```

then:

```text
AI_FIBONACCI_USER_VISIBLE_ELIGIBLE = false
```

for that stock in the first enablement candidate pool.

Do not expose unstable structural anchors.

---

# 26. Daily variation rule

If daily anchor selection materially varies but monthly/weekly are stable:

- keep daily deterministic support/resistance
- omit daily Fibonacci
- do not invalidate higher-timeframe price structure

This preserves the monthly→weekly→daily hierarchy.

---

# 27. Full-OHLCV debug comparison

For the benchmark set, compare:

```text
COMPACT/RICH PACKET
vs
FULL_OHLCV_DEBUG
```

where full debug is feasible and governance-approved.

Compare:

```text
monthly selected anchors
weekly selected anchors
daily selected anchors
fib_mode
visible confluence
```

The full-debug output is shadow-only.

Set:

`RICH_PACKET_SUFFICIENCY = PASS / PARTIAL / FAIL`

---

# 28. Information-loss gate

Fail packet sufficiency if the full-debug evidence repeatedly selects a major structural pivot that the rich compact packet did not include.

Hard target for enablement candidates:

```text
MATERIAL_ANCHOR_OMISSION = 0
```

---

# 29. No previous-selection anchoring in primary trial

Primary variable-AI stability trials must not include:

```text
previous selected anchor
human-approved anchor
reference-harness anchor
prior Fibonacci result
```

in the prompt.

Otherwise the trial does not prove independent candle judgment.

A separate comparison report may compare against prior reference selections afterward.

---

# 30. Reference-harness comparison

After independent AI selection, compare with the previous archived/reference anchors.

Classify:

```text
MATCH
DIFFERENT_BUT_EQUIVALENT
AI_MATERIAL_DIFFERENCE
REFERENCE_MATERIAL_DIFFERENCE
```

Do not automatically assume the old reference is correct.

Human review decides material differences using evidence/provenance.

---

# 31. Interpretability requirement

For every selected primary anchor set, reports must be able to answer:

```text
Why this low?
Why this high?
Why is the alternative weaker?
Which actual candle/bar refs support the selection?
```

The rationale must be concise and evidence-linked.

Do not persist private chain-of-thought.

---

# 32. Deterministic Fibonacci calculator — no change

Do not modify the existing proven calculator except for compatibility bugs.

Required preserved state:

```text
MONTHLY_FIBONACCI = PASS
WEEKLY_FIBONACCI = PASS
DAILY_FIBONACCI = PASS
FIBONACCI_DETERMINISTIC_CALC = PASS
FIBONACCI_NUMERIC_PROVENANCE = PASS
```

AI continues to calculate zero user-visible Fib prices itself.

---

# 33. Multi-timeframe confluence — no redesign

Preserve:

```text
monthly
→ weekly
→ daily
→ synthesis
```

and current confluence logic.

The P1 repair is anchor evidence/runtime validation, not confluence redesign.

---

# 34. Shadow renderer comparison

Generate exact shadow output after variable-AI selection.

Compare:

```text
V2_REFERENCE_SHADOW
vs
VARIABLE_AI_SHADOW
```

For each timeframe show:

```text
selected support/resistance
selected anchors
Fib refs
confluence
visible text
```

---

# 35. Current production isolation

Hard target:

```text
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```

This repair remains shadow-only.

No Telegram Fib section.

No production message-route change.

No canary expansion.

---

# 36. External runtime failure behavior

If approved variable AI runtime:
- times out
- returns malformed output
- violates schema
- produces invalid IDs

then:

```text
anchor selection = unavailable for that timeframe/message
Fib omitted
current deterministic SR survives
packet continues
```

No packet-level failure.

---

# 37. Egress minimization test

Add a test that serializes the actual external anchor packet and verifies banned fields are absent.

Hard target:

```text
PRIVATE_FIELD_EGRESS = 0
SECRET_EGRESS = 0
UNRELATED_THESIS_EGRESS = 0
```

---

# 38. Numeric safety targets

Preserve and re-run:

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

# 39. Semantic safety targets

Preserve:

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

# 40. Focused tests — evidence packet

Required:

- public price-only allowlist
- banned private fields excluded
- recent monthly raw OHLCV included
- recent weekly raw OHLCV included
- recent daily raw OHLCV included
- major candidate neighborhoods included
- candidate count metadata
- omitted-candidate metadata
- raw OHLCV + deterministic candle features both present
- no precomputed Fib in Stage-1 packet

---

# 41. Focused tests — variable AI output

Required:

- valid ID-only output accepted
- invented price field ignored/rejected
- nonexistent pivot ID rejected
- wrong ticker ID rejected
- wrong timeframe ID rejected
- unconfirmed pivot rejected
- invalid chronology rejected
- AMBIGUOUS accepted
- INSUFFICIENT_STRUCTURE accepted
- alternative structure bounded to max one
- concise rationale bounded

---

# 42. Focused tests — stability

Required:

- exact same anchors → STABLE
- different IDs / same canonical zone → STABLE or MINOR_VARIATION
- different visible zones → MATERIAL_VARIATION
- monthly material variation → stock ineligible
- weekly material variation → stock ineligible
- daily material variation → daily Fib omitted, higher timeframes survive
- no wide tolerance to convert materially different zones into equivalent

---

# 43. Focused tests — runtime failure

Required:

- timeout
- malformed JSON
- schema violation
- invalid evidence ref
- refused output
- unavailable runtime

All must:

```text
fail closed per timeframe/message
preserve deterministic SR
not block packet
```

---

# 44. KR/US parity

Use the same external anchor-selection schema for KR and US.

Market differences only in:

```text
calendar
currency
OHLCV source
adjustment basis
```

Set:

`KR_US_VARIABLE_AI_ANCHOR_SCHEMA_COMMON = PASS / FAIL`

---

# 45. Human benchmark report

Create:

`docs/reports/20260826-variable-ai-anchor-exact-benchmark.md`

For each benchmark stock and timeframe show:

```text
FROZEN_EVIDENCE_HASH
CANDIDATE_IDS
RAW CANDLE WINDOW RANGE

RUN 1 selection
RUN 2 selection
RUN 3 selection
RUN 4 selection
RUN 5 selection

EXACT ANCHOR FREQUENCY
STRUCTURE EQUIVALENCE
FINAL STABILITY CLASS

REFERENCE HARNESS SELECTION
COMPARISON CLASS

DETERMINISTIC FIB RESULT PER DISTINCT VALID STRUCTURE
VISIBLE ZONE EFFECT
USER_VISIBLE_ELIGIBLE
```

Do not include hidden reasoning.

---

# 46. Candle-context audit report

Create:

`docs/reports/20260826-ai-anchor-candle-context-audit.md`

For each timeframe report:

```text
total canonical bars available
recent raw bars included
eligible pivot candidates
candidate neighborhoods included
bars omitted
reason
token/context footprint
full-debug comparison result
```

---

# 47. Egress audit report

Create:

`docs/reports/20260826-price-only-ai-evidence-egress-audit.md`

Report:

```text
approved runtime status
allowlisted fields
blocked fields
sample sanitized packet
private-field egress count
secret egress count
governance blocker if any
```

Do not include secrets.

---

# 48. Stability report

Create:

`docs/reports/20260826-variable-ai-anchor-stability.md`

Aggregate:

```text
monthly STABLE / MINOR / MATERIAL
weekly STABLE / MINOR / MATERIAL
daily STABLE / MINOR / MATERIAL

stock-level eligible count
stock-level ineligible count
timeframe-fallback count
runtime failure count
```

---

# 49. Replay reports

Create:

1. `docs/reports/20260826-variable-ai-anchor-kr-shadow-replay.md`
2. `docs/reports/20260826-variable-ai-anchor-us-shadow-replay.md`
3. `docs/reports/20260826-variable-ai-vs-reference-shadow-comparison.md`

Use latest safe frozen packets.

No provider recollection required for the primary stability test.

---

# 50. Production readiness gate

Set:

`PRODUCTION_ENABLEMENT_READY = YES`

only if:

```text
APPROVED_VARIABLE_AI_RUNTIME is available
VARIABLE_AI_TRIAL = PASS
PRICE_ONLY_EVIDENCE_EGRESS = PASS
RICH_PACKET_SUFFICIENCY = PASS or bounded safe PARTIAL
MONTHLY material variation = 0 among enablement candidates
WEEKLY material variation = 0 among enablement candidates
invalid AI output safely falls back
all numeric/temporal/security safety errors = 0
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
full tests / CI PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

This still does not enable it.

Expected state after success:

```text
AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE =
INTEGRATED_READY_NOT_ARMED
```

---

# 51. If egress remains blocked

Do not treat this as a code failure.

Set:

```text
APPROVED_VARIABLE_AI_RUNTIME = UNAVAILABLE
VARIABLE_AI_TRIAL = BLOCKED_EGRESS
ANCHOR_SELECTION_STABILITY = PARTIAL
AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = SHADOW
PRODUCTION_ENABLEMENT_READY = NO
```

Then the next action is governance/runtime enablement, not more Fibonacci math.

Do not fabricate trial results.

---

# 52. Required architecture docs

Create/update:

1. `docs/architecture/VARIABLE_AI_SWING_ANCHOR_SELECTION.md`
2. `docs/architecture/PRICE_ONLY_AI_ANCHOR_PACKET.md`
3. `docs/architecture/AI_ANCHOR_STABILITY_POLICY.md`
4. update `AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE.md`
5. update `PRICE_STRUCTURE_SHADOW_POLICY.md`

---

# 53. Required reports

Create:

1. `docs/reports/20260826-fibonacci-v2-selector-path-audit.md`
2. `docs/reports/20260826-price-only-ai-evidence-egress-audit.md`
3. `docs/reports/20260826-ai-anchor-candle-context-audit.md`
4. `docs/reports/20260826-variable-ai-anchor-exact-benchmark.md`
5. `docs/reports/20260826-variable-ai-anchor-stability.md`
6. `docs/reports/20260826-variable-ai-anchor-kr-shadow-replay.md`
7. `docs/reports/20260826-variable-ai-anchor-us-shadow-replay.md`
8. `docs/reports/20260826-variable-ai-vs-reference-shadow-comparison.md`
9. `docs/reports/20260826-fibonacci-p1-closure-safety-parity.md`
10. `docs/reports/20260826-fibonacci-p1-closure-readiness.md`
11. `docs/reports/20260826-fibonacci-p1-closure-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-fibonacci-p1-closure-readiness.json`

---

# 54. Full validation

Required:

```text
selector-path audit complete
egress audit PASS or explicit BLOCKED_EGRESS
focused evidence-packet tests PASS
focused variable-output tests PASS
focused stability tests PASS
runtime-failure tests PASS
KR shadow replay PASS
US shadow replay PASS
reference comparison complete
lookahead safety PASS
numeric provenance PASS
current user-visible diff = 0
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action unchanged
operationId/schema unchanged
implementation SHA Actions PASS
final main Actions PASS if merged
API /health PASS
worktrees clean
```

---

# 55. Gates

Set exactly:

```text
WAS_VARIABLE_AI_RUNTIME_ACTUALLY_EXECUTED =
YES / NO

APPROVED_VARIABLE_AI_RUNTIME =
AVAILABLE /
AVAILABLE_WITH_FIELD_RESTRICTIONS /
UNAVAILABLE

PRICE_ONLY_EVIDENCE_EGRESS =
PASS / FAIL / BLOCKED

RICH_CANDLE_CONTEXT_PACKET =
PASS / FAIL

RICH_PACKET_SUFFICIENCY =
PASS / PARTIAL / FAIL

VARIABLE_AI_TRIAL =
PASS / PARTIAL / BLOCKED_EGRESS / FAIL

MONTHLY_ANCHOR_STABILITY =
PASS / PARTIAL / FAIL

WEEKLY_ANCHOR_STABILITY =
PASS / PARTIAL / FAIL

DAILY_ANCHOR_STABILITY =
PASS / PARTIAL / FAIL

ANCHOR_SELECTION_STABILITY =
PASS / PARTIAL / FAIL

REFERENCE_HARNESS_COMPARISON =
PASS / REVIEW_REQUIRED / FAIL

FIBONACCI_DETERMINISTIC_CALC =
PASS / FAIL

FIBONACCI_NUMERIC_PROVENANCE =
PASS / FAIL

LOOKAHEAD_SAFETY =
PASS / FAIL

KR_US_VARIABLE_AI_ANCHOR_SCHEMA_COMMON =
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

# 56. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

WAS_VARIABLE_AI_RUNTIME_ACTUALLY_EXECUTED = ...
APPROVED_VARIABLE_AI_RUNTIME = ...
PRICE_ONLY_EVIDENCE_EGRESS = ...

RICH_CANDLE_CONTEXT_PACKET = ...
RICH_PACKET_SUFFICIENCY = ...

VARIABLE_AI_TRIAL = ...

MONTHLY_ANCHOR_STABILITY = ...
WEEKLY_ANCHOR_STABILITY = ...
DAILY_ANCHOR_STABILITY = ...
ANCHOR_SELECTION_STABILITY = ...

BENCHMARK_RUNS_PER_PACKET = ...
WIDER_UNIVERSE_RUNS_PER_PACKET = ...

MONTHLY_MATERIAL_VARIATION_COUNT = ...
WEEKLY_MATERIAL_VARIATION_COUNT = ...
DAILY_MATERIAL_VARIATION_COUNT = ...

STOCK_USER_VISIBLE_ELIGIBLE = ...
STOCK_USER_VISIBLE_INELIGIBLE = ...
TIMEFRAME_FIB_FALLBACK_COUNT = ...

REFERENCE_HARNESS_COMPARISON = ...

FIBONACCI_DETERMINISTIC_CALC = ...
FIBONACCI_NUMERIC_PROVENANCE = ...
LOOKAHEAD_SAFETY = ...

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

KR_US_VARIABLE_AI_ANCHOR_SCHEMA_COMMON = ...
KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_MULTI_TIMEFRAME_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
RUNTIME_GOVERNANCE_ENABLEMENT /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 57. Mandatory ZIP

Create:

`20260826-fibonacci-variable-ai-anchor-candle-context-bounded-repair-bundle.zip`

Include:
- this exact instruction
- architecture docs
- sanitized price-only evidence examples
- candle-context audit
- egress audit
- exact 5-run benchmark
- stability report
- KR/US shadow replay
- reference comparison
- safety parity
- readiness report
- artifact index

Never include:
- credentials
- tokens
- auth headers
- account/user identifiers
- private chain-of-thought

Compute/report SHA-256.

---

# 58. Severity

## P0

- unapproved private evidence egress
- secret/token exposure
- AI-created price presented as authoritative
- wrong ticker/timeframe anchor
- future/unconfirmed pivot
- wrong adjusted basis
- unsupported target/stop
- price/Fib mutates business investment logic
- shadow feature becomes user-visible
- replay mutates production state

## P1

- variable AI runtime still not actually executed but stability reported PASS
- rich packet lacks material candle structure needed for anchor choice
- monthly/weekly anchor material variation remains user-visible eligible
- different material structures are collapsed into "equivalent" using wide tolerance
- prior reference anchor is leaked into primary trial prompt
- invalid AI output blocks the whole packet
- full-debug evidence reveals omitted major pivot not available to compact packet

## P2

- daily Fib omitted due tactical instability
- exact pivot ID differs while visible zone remains structurally equivalent
- ambiguous stock remains shadow-only
- many stocks still get no Fibonacci because it adds no value
- runtime governance remains blocked but code path is otherwise ready
- harmless prose differences

---

# 59. Final principle

The remaining problem is not Fibonacci math.

It is proving that a real variable AI can look at enough candle structure and repeatedly choose a defensible swing without making user-visible price zones unstable.

So close the P1 with:

```text
richer public candle evidence
→ real approved variable AI selection
→ ID-only output
→ deterministic validation
→ deterministic Fibonacci
→ material-zone stability test
→ per-timeframe fallback
```

Do not optimize for exact anchor-ID consistency.

Optimize for:

```text
stable structural meaning
+ stable validated price zones
+ safe omission when ambiguous
```

Only after that should a separate bounded task enable the monthly→weekly→daily Fibonacci section in live messages.
