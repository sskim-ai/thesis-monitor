# thesis-monitor — Price Structure / Wave / Fibonacci v3 Final Stability Repair
## Hypothesis Equivalence Classes + Fib-Family Consensus + Confluence Filtering
## Resolve MATERIAL_VARIATION without forcing one Elliott count
## SK hynix mandatory regression; TSLA/TSM true-conflict controls
## Shadow-only in this task

## Metadata

- Workstream: `PRICE_STRUCTURE_V3_FAMILY_CONSENSUS_STABILITY`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_P1_STABILITY_REPAIR`
- Source policy: `FREE_ONLY`
- Current v3 state: `INTEGRATED_READY_NOT_ARMED`
- User-visible production mutation in this task: `0`
- Telegram send: `0`
- Manual Task / DB / official assessment mutation: `0`
- Open Research production integration: preserve `0`
- Trade AR: preserve `OFF`
- Production Assist: preserve `OFF`
- Public Action / operationId / schema: preserve current values

### Required base

Latest reported safe final/main/operating:

`2984d7658b79d9c09d43e23929b71719f88a8c82`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Previous bounded-repair result

```text
Instruction:
82cb04e2880d1ed7b0405e1ddd20c5f333305394

Implementation:
bea877d3a6a9977c19832cbde28ed235676929d2

Final/main/operating:
2984d7658b79d9c09d43e23929b71719f88a8c82

BAR_COMPLETION_TEMPORAL_CONTRACT = PASS
DAILY_1200 = PASS
WAVE_DEGREE_MODEL = PASS
SK_HYNIX_CURRENT_CYCLE_COVERAGE = PASS
VARIABLE_AI_SELECTION_CONNECTED_TO_V3_ENGINE = YES
SELECTED_BUT_NOT_FED_TO_ENGINE = 0
CURRENT_REBOUND_FIB = PASS
PRIMARY_CYCLE_FIB = PASS
CROSS_TIMEFRAME_CONFLUENCE_V3 = PASS
NO_FORCED_ELLIOTT = PASS
UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
PRICE_STRUCTURE_WAVE_FIB_V3 = INTEGRATED_READY_NOT_ARMED
PRODUCTION_ENABLEMENT_READY = YES
```

This instruction does **not** reopen the core v3 design.

It closes the remaining quality problem:

```text
7 subjects = MATERIAL_VARIATION
```

without weakening safety or manufacturing an exact hypothesis selection.

---

# 0. Observed material-variation cohort — mandatory frozen baseline

The previous exact AI-feedback trial produced:

```text
STABLE_SUBJECTS = 7
VALID_ABSTENTION_SUBJECTS = 6
MATERIAL_VARIATION_SUBJECTS = 7
```

Material cohort:

```text
000660  SK hynix
003690  Korean Re
005490  POSCO Holdings
005930  Samsung Electronics
010120  LS ELECTRIC
TSLA
TSM
```

Do not replace this cohort with a favorable subset for the root-cause audit.

The full monitored universe remains 20 subjects.

---

# 1. Observed divergence patterns — preserve as frozen evidence

## 000660 SK hynix

```text
5 runs
SELECTED same hypothesis = 3
AMBIGUOUS = 2

selected degree =
PRIMARY_CURRENT_CYCLE

representative W0-W4 =
2023-01
2024-07
2024-09
2026-06 provisional
2026-07 provisional
```

The ambiguous runs explicitly said leading current-cycle candidates:

```text
share W1-W4
differ only at W0
```

Observed nearby alternative includes a 2022-09 W0 with the same W1-W4.

This is the canonical **early-anchor ambiguity** control.

## 003690

```text
3 runs
same SELECTED = 2
AMBIGUOUS = 1
```

Ambiguity:

```text
leading current-cycle candidates
share W1-W5
differ at W0
```

## 005930

```text
3 runs
same SELECTED = 2
AMBIGUOUS = 1
```

Ambiguity:

```text
share W1-W4
differ at W0
```

## 010120

```text
3 runs
same SELECTED = 2
AMBIGUOUS = 1
```

Ambiguity:

```text
leading candidates share W3-W5
but earlier W0-W2 sequences differ
```

This is an **early-leg ambiguity with shared active phase** control.

## 005490

```text
3 runs
same GRAND_CYCLE SELECTED = 2
AMBIGUOUS = 1
PRIMARY_CURRENT_CYCLE candidates = 0
```

Top grand-cycle alternatives can differ at W0 while sharing later structure.

This is the **grand-cycle-only ambiguity** control.

## TSLA

```text
3 runs
AMBIGUOUS = 1
SELECTED hypothesis A = 1
SELECTED hypothesis B = 1
```

The two selected current-cycle counts are materially different full structures.

This is the mandatory **true competing-hypothesis** negative control.

## TSM

```text
3 runs
same SELECTED = 2
AMBIGUOUS = 1
```

Representative and close alternative share:

```text
W0
W1
W2
W4
W5
```

but differ at:

```text
W3
```

This is a **mid-wave dependency conflict** control.

---

# 2. Core design principle

Do not define stability as:

```text
"Did AI choose one exact full Elliott count every run?"
```

Define it as:

```text
"Which current price-structure conclusions are invariant
across the defensible competing hypotheses?"
```

A stock can have:

```text
full-wave ambiguity
```

while still having:

```text
stable current-rebound Fib
stable wave3 retracement
stable pivot/Bollinger zone
stable cross-timeframe resistance
```

if those outputs do not depend on the disputed endpoints.

Conversely, if competing counts change the actual visible price zone:

```text
omit that Fib family
```

Do not force consensus.

---

# 3. Objective

Build a deterministic hypothesis/family consensus layer:

```text
validated wave candidates
→ deterministic equivalence classes
→ variable AI selects class / hypothesis / ambiguity set
→ deterministic endpoint-dependency analysis
→ Fib family-by-family stability
→ filter unstable Fib sources
→ rebuild cross-timeframe confluence
→ shadow render only stable technical conclusions
```

Target result:

```text
full hypothesis may remain ambiguous
BUT
stable Fib families can survive
AND
materially unstable families stay omitted
```

---

# 4. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-price-structure-v3-family-consensus-stability-bounded-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify latest safe main/operating
2. commit/push exact instruction as docs-only instruction commit
3. branch:

`codex/price-structure-v3-family-consensus-stability`

4. use latest safe main as base
5. no force push / history rewrite
6. remain shadow-only

---

# 5. User reference engine — this package includes the original archive

This work package should include:

`reference_input/codex_stock_wave_engine(1).zip`

Expected SHA-256:

`2726c2d1cd49b8fdbbf86a9b784772fcf52023f6d5f489933445884ce1effb59`

The previous run reported:

```text
USER_REFERENCE_ENGINE_AVAILABLE = NO
REFERENCE_METHOD_COMPARISON = NOT_OBSERVED
```

For this task:

1. verify the bundled archive SHA
2. extract/stage sanitized files under:

`docs/reference/user-wave-engine/`

3. mark:

```text
REFERENCE_ONLY
NOT_PRODUCTION_RUNTIME
USER_SUPPLIED_SK_HYNIX_REFERENCE
```

4. do not import runtime production code from `docs/reference`
5. compare method/results after implementation

If the archive is somehow unavailable:
- do not invent it
- set `USER_REFERENCE_ENGINE_AVAILABLE = NO`
- continue the stability repair
- keep comparison `NOT_OBSERVED`

Reference comparison is important, but a missing reference archive must not cause unsafe code changes.

---

# 6. Do not solve instability by lowering AI variability

Do NOT manufacture stability using:

```text
temperature = 0 only to pass
fixed random seed only to pass
hard-coded ticker choice
hard-coded preferred hypothesis ID
prompt including prior selected answer
prompt including human reference answer
forced "always choose top score"
```

The goal is safe structural consensus, not deterministic-looking AI.

---

# 7. Do not solve instability by score threshold hacks

Do NOT:

- add a ticker-specific bonus
- widen score-gap threshold until SK hynix selects
- treat first-ranked candidate as truth when scores are close
- remove valid alternatives merely to simplify the packet

Valid ambiguity is allowed.

---

# 8. Hypothesis endpoint dependency graph — mandatory

Audit every deterministic Fibonacci family/formula and encode which wave endpoints it actually depends on.

At minimum audit:

```text
WAVE1_RETRACEMENT
WAVE3_RETRACEMENT
PRIMARY_CYCLE_RETRACEMENT
CURRENT_REBOUND

W5_PROJECTION:
  WAVE1_MULTIPLE
  WAVE3_MULTIPLE
  SPAN03_MULTIPLE
```

Do not assume dependencies from this instruction if production formulas differ.

Produce a machine-readable dependency registry.

Illustrative examples only:

```text
WAVE1_RETRACEMENT
→ W0, W1

WAVE3_RETRACEMENT
→ W2, W3

CURRENT_REBOUND
→ active decline/rebound high + low
  according to actual wave_state/formula

W5 / WAVE1_MULTIPLE
→ W0, W1, W4

W5 / WAVE3_MULTIPLE
→ W2, W3, W4

W5 / SPAN03_MULTIPLE
→ W0, W3, W4
```

The backend source code is authoritative.

Create:

`FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY`

---

# 9. Dependency registry contract

Each entry:

```text
family
method_family optional
wave_state applicability
required_endpoint_labels
formula_version
source_degree
```

Every Fib numeric registry entry should be able to point back to this dependency contract.

Hard target:

`FIB_FAMILY_WITHOUT_ENDPOINT_DEPENDENCY = 0`

---

# 10. Hypothesis equivalence class

Create deterministic:

`WAVE_HYPOTHESIS_EQUIVALENCE_CLASS`

Suggested fields:

```text
equivalence_class_id
ticker
source_degree
wave_state

member_hypothesis_ids

shared_endpoint_refs:
  W0 optional
  W1 optional
  W2 optional
  W3 optional
  W4 optional
  W5 optional

divergent_endpoint_labels

active_structure_signature

family_dependency_status
```

AI does not create this class.

Backend creates it from validated candidates.

---

# 11. Active structure signature

The active structure signature should describe the currently relevant wave phase, not merely the oldest anchor.

Make it state-aware.

Examples:

```text
W4_CANDIDATE_W5_UNCONFIRMED
→ current structural phase is primarily defined by
  the expansion/correction endpoints surrounding W3/W4,
  plus only the earlier endpoint dependencies required
  by a specific Fib family

W5_CANDIDATE
→ active structure includes the late impulse phase,
  while earlier anchors may remain family-specific dependencies
```

Do not create one universal hard-coded "last 3 endpoints" rule.

The family dependency graph remains authoritative.

---

# 12. Exact equivalence vs family equivalence

Separate:

```text
FULL_HYPOTHESIS_EXACT
```

from:

```text
FAMILY_EQUIVALENT
```

Two hypotheses may be different full counts but equivalent for:

```text
CURRENT_REBOUND
```

if all required endpoint refs for that formula are the same.

Likewise they may be different for:

```text
PRIMARY_CYCLE_RETRACEMENT
```

if W0 differs.

This distinction is the central repair.

---

# 13. AI selection schema — support bounded ambiguity sets

Current `AMBIGUOUS` outputs often return no hypothesis ID.

Extend Stage-1 schema safely.

## SELECTED

```text
status = SELECTED
hypothesis_id = valid ID
alternative_hypothesis_id = optional valid ID
equivalence_class_id = optional valid backend class
```

## AMBIGUOUS

Allow:

```text
status = AMBIGUOUS
hypothesis_id = null

competing_hypothesis_ids =
  2 or 3 valid supplied IDs when ambiguity is between known candidates

equivalence_class_id =
  optional backend-provided class if all competing IDs belong to it

confidence
reason_categories
evidence refs
concise reason
```

## INSUFFICIENT_STRUCTURE

```text
no candidate IDs required
```

Do not confuse known-candidate ambiguity with insufficient structure.

---

# 14. Ambiguous output is not a request to guess

When AI returns:

```text
AMBIGUOUS
+ competing IDs
```

backend must NOT pick one.

Instead:

```text
evaluate invariant Fib families across the supplied ambiguity set
```

If none are safe:

```text
Fib omitted
deterministic SR survives
```

---

# 15. Repeated-run consensus universe

For each frozen subject, create a deterministic consensus candidate universe from:

```text
all SELECTED hypothesis IDs
all alternative IDs
all AMBIGUOUS competing IDs
```

Do not include:
- random non-mentioned candidates
- human reference answer
- previous harness selection not returned by current trial

This set becomes the family-stability evaluation universe.

---

# 16. Fib-family stability states

For each subject and each family/method:

```text
EXACT_INVARIANT
PRICE_EQUIVALENT
MATERIAL_VARIATION
NOT_APPLICABLE
INSUFFICIENT
```

## EXACT_INVARIANT

All relevant candidate hypotheses have identical required endpoint refs.

## PRICE_EQUIVALENT

Endpoint refs differ but deterministic calculated levels resolve to the same existing canonical visible zone and same structural role under existing tolerance.

## MATERIAL_VARIATION

Different candidate hypotheses produce materially different visible technical levels/zones or structural meaning.

## NOT_APPLICABLE

Formula not relevant to current wave state.

## INSUFFICIENT

Required safe endpoint/provenance unavailable.

---

# 17. No tolerance widening

`PRICE_EQUIVALENT` must use the already-approved canonical price-zone/confluence tolerances.

Hard target:

`TOLERANCE_WIDENING = 0`

Do not make distant Fib values equivalent to reduce variation counts.

---

# 18. Family-level eligibility

Create:

```text
fib_family_eligibility:
  WAVE1_RETRACEMENT:
    status
    reason

  WAVE3_RETRACEMENT:
    status
    reason

  PRIMARY_CYCLE_RETRACEMENT:
    status
    reason

  CURRENT_REBOUND:
    status
    reason

  W5_PROJECTION:
    method families individually
```

Eligible only when:

```text
EXACT_INVARIANT
or
PRICE_EQUIVALENT
```

---

# 19. Current-rebound priority

The user's intended resistance analysis gives special importance to the current correction/rebound structure.

Therefore report separately:

```text
CURRENT_REBOUND_FAMILY_STABILITY
```

Do not automatically promote it.

It still requires stable endpoint dependencies.

---

# 20. SK hynix mandatory expected behavior

Do not hard-code prices or IDs.

Use the frozen candidate set.

Observed ambiguity:

```text
leading candidates share W1-W4
and differ primarily at W0
```

Therefore the repair should test whether:

```text
families independent of W0
```

remain invariant.

Expected conceptual outcome if the production dependency graph supports it:

```text
CURRENT_REBOUND
→ may remain usable

WAVE3_RETRACEMENT
→ may remain usable if W2/W3 shared

W0-dependent PRIMARY_CYCLE family
→ may remain unstable / omitted

W0-dependent W5 projection methods
→ may remain unstable / omitted

W3/W4-dependent projection methods
→ may remain usable if invariant
```

Do NOT force this outcome.

Derive it from the dependency registry.

---

# 21. SK hynix acceptance condition

Success is NOT:

```text
5/5 exact same hypothesis ID
```

Success is:

```text
all user-visible Fib families are invariant or price-equivalent
and
all materially variant families are omitted
```

Set:

```text
SK_HYNIX_FULL_HYPOTHESIS_STABILITY =
STABLE / MATERIAL_VARIATION / VALID_ABSTENTION

SK_HYNIX_FAMILY_LEVEL_PRICE_STRUCTURE =
PASS / PARTIAL / FAIL
```

A full-hypothesis `MATERIAL_VARIATION` may coexist with family-level `PASS`.

---

# 22. SK hynix exact family table

Mandatory report:

```text
Family / method
Required endpoints
Candidate A endpoints
Candidate B endpoints
Exact dependency match?
Calculated values
Visible zone
Stability
Eligible?
```

Show at least every currently implemented Fib family.

---

# 23. 003690 / 005930 W0-only controls

For both names:

audit whether the ambiguity is effectively:

```text
W0-only
```

for the leading class.

If so:

- W0-independent families can remain eligible
- W0-dependent families require their own consensus
- do not force one W0

---

# 24. 010120 early-leg ambiguity control

Observed:

```text
candidate alternatives share W3-W5
but W0-W2 can differ
```

This should test the dependency design.

A late-phase/current-rebound family may be stable even when earlier retracement families are not.

Do not assume.

Compute.

---

# 25. 005490 grand-cycle-only control

No valid `PRIMARY_CURRENT_CYCLE` was supplied in the prior trial.

Do not turn a grand cycle into a current cycle.

Set explicit degree-role policy:

```text
GRAND_CYCLE Fib
= LONG_HORIZON_CONTEXT
```

not:

```text
PRIMARY_CURRENT_RESISTANCE
```

A stable grand-cycle family can be retained in shadow long-horizon context, but should not automatically become the main near-term price-structure line.

Create:

`GRAND_CYCLE_USER_ROLE_POLICY`

---

# 26. TSLA true-conflict negative control

TSLA selected two materially different `PRIMARY_CURRENT_CYCLE` hypotheses across runs.

Do not hide this with equivalence classes if their active dependencies or visible zones differ.

Required:

```text
if current relevant Fib families materially differ
→ family MATERIAL_VARIATION
→ Fib omitted
→ deterministic SR only
```

TSLA is the mandatory proof that the new consensus logic is not simply a "make everything stable" mechanism.

---

# 27. TSM mid-wave conflict control

TSM leading alternatives share:

```text
W0 W1 W2 W4 W5
```

but differ at:

```text
W3
```

Therefore families depending on W3 must be evaluated carefully.

The repair must show that:

```text
W3-dependent families
```

do not become eligible merely because most other endpoints match.

---

# 28. Confluence must be rebuilt after family filtering

Do not calculate confluence from unstable Fib and then merely hide the Fib label.

Pipeline must be:

```text
deterministic SR sources
+ only eligible Fib-family sources
→ rebuild timeframe confluence
→ rebuild cross-timeframe confluence
```

Hard target:

`UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0`

---

# 29. Confluence provenance

Every family-filtered confluence zone must preserve:

```text
source family
source method family
source degree
hypothesis equivalence class or consensus set
family stability
target timeframe
```

---

# 30. Confluence stability

Set per visible zone:

```text
CONFLUENCE_EXACT_INVARIANT
CONFLUENCE_PRICE_EQUIVALENT
CONFLUENCE_MATERIAL_VARIATION
```

A resistance band is eligible only when every material source contributing to the rendered explanation is eligible.

---

# 31. Deterministic SR remains independent

Preserve:

```text
MONTHLY_SR_RUNTIME_VARIATION = 0
WEEKLY_SR_RUNTIME_VARIATION = 0
DAILY_SR_RUNTIME_VARIATION = 0
```

Fib ambiguity must not delete deterministic support/resistance.

---

# 32. Renderer hierarchy

Shadow renderer remains:

```text
월봉
→ 구조적 SR
→ stable primary/current wave context
→ only stable Fib families

주봉
→ intermediate SR
→ higher-degree stable Fib confluence

일봉
→ tactical SR
→ higher-degree stable Fib interaction

종합
→ nearest tactical barrier
→ important structural barrier
→ strongest stable confluence
→ provisional/ambiguous caveat
```

Do not dump all stable ratios.

---

# 33. Ambiguity wording

If full wave count is ambiguous but current-rebound family is stable:

Allowed:

```text
장기 파동 시작점에는 복수 가설이 남아 있지만,
현재 조정 구간을 기준으로 한 회복 저항은 동일 구간에 모입니다.
```

Not allowed:

```text
파동이 확정됐다.
```

Do not expose internal class IDs to users.

---

# 34. Stable family, unstable full count

Create an explicit state:

```text
FULL_WAVE_AMBIGUOUS_FAMILY_STABLE
```

This is a safe analytical state.

Do not treat it as an error.

---

# 35. Family consensus must be deterministic

Once the candidate set is frozen:

```text
dependency analysis
Fib calculation
price-equivalence test
eligibility
confluence filtering
```

must all be deterministic.

AI only supplies candidate/class judgment.

---

# 36. Variable AI repeated protocol

Rerun:

```text
SK hynix = 5 independent calls
all other 6 prior MATERIAL_VARIATION names = 5 calls recommended
stable/abstention controls = 3 calls
```

Minimum:
- exact 7 variation cohort: 5 each
- representative stable controls: 3 each
- representative valid-abstention controls: 3 each

Do not reduce to 3 runs on the difficult cohort merely to save variance visibility.

---

# 37. Trial outcome classification

Report both:

```text
FULL_HYPOTHESIS_STABILITY
```

and:

```text
FAMILY_LEVEL_OUTPUT_STABILITY
```

Do not collapse them.

---

# 38. Required root-cause taxonomy

Classify each variation subject into one primary reason:

```text
EARLY_ANCHOR_ONLY_AMBIGUITY
EARLY_LEG_AMBIGUITY_ACTIVE_PHASE_SHARED
MID_WAVE_DEPENDENCY_CONFLICT
TRUE_ACTIVE_STRUCTURE_CONFLICT
GRAND_CYCLE_ONLY_AMBIGUITY
DEGREE_CONFLICT
INSUFFICIENT_STRUCTURE
OTHER
```

Multiple secondary tags allowed.

---

# 39. Material-value benchmark

For each of the 7 prior variation subjects compare:

```text
BEFORE:
full hypothesis unstable → all Fib shadow-only

AFTER:
stable families preserved
unstable families omitted
confluence rebuilt
```

Human-review classification:

```text
MATERIAL_IMPROVEMENT
MINOR_IMPROVEMENT
NO_ADDED_VALUE
WORSE
```

`WORSE = 0` is required for readiness.

---

# 40. Stable-control regression

Use at least:

```text
012450
086280
GOOGL
IBM
MU
WULF
```

or the actual previous stable cohort if changed.

Their previously stable family outputs must not regress.

Hard target:

`PREVIOUS_STABLE_REGRESSION = 0`

---

# 41. Valid-abstention regression

Use:

```text
CORZ
CRCL
RXRX
SKHY
SNDK
WRD
```

or actual safe abstention cohort.

Do not invent wave structure to increase coverage.

Hard target:

`VALID_ABSTENTION_FORCED_TO_SELECTION = 0`

---

# 42. Reference engine comparison — now source-backed

If bundled user reference is available, create:

`docs/reports/20260826-user-reference-wave-engine-byte-audit.md`

Compare the actual supplied:

```text
CODEX_IMPLEMENTATION_GUIDE.md
stock_structure_engine.py
SK하이닉스_structure_analysis_auto.json
regression_check_sk_hynix.py
```

against current v3 semantics.

For SK hynix compare:

```text
reference W0-W4/W5
confirmed/provisional treatment
current rebound Fib
primary-cycle Fib
W5 projections
zone/confluence concept
```

Do not make the reference code production authority.

Classify:

```text
REFERENCE_MATCH
DIFFERENT_BUT_DEFENSIBLE
REFERENCE_TEMPORAL_ISSUE
THESIS_MONITOR_METHOD_ISSUE
MATERIAL_METHOD_CONFLICT
```

---

# 43. Reference temporal caveat

The current v3 has a stricter repaired partial-bar completion contract.

If the user reference marks an endpoint differently because of incomplete-bar assumptions:

do not weaken temporal safety to match it.

Document:

`REFERENCE_TEMPORAL_ISSUE`

when appropriate.

---

# 44. OHLCV default consistency audit

The user's canonical internal SR history requirement is:

```text
daily = 1200
weekly = 600
monthly = 300
```

Audit repository documentation / runtime policy for stale internal defaults such as:

```text
500/300/100
300/60/60
```

Update only the internal price-structure calculation contract where appropriate.

Do not change public snapshot semantics that do not expose raw OHLCV.

Set:

`STALE_INTERNAL_OHLCV_DEFAULT_REFERENCE = 0`

after the audit.

---

# 45. No score-as-buy-signal

Preserve:

```text
technical zone score
= evidence density / structural importance
```

not:
- buy score
- sell score
- expected return
- probability of reversal

---

# 46. Numeric provenance — preserve

Hard targets:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
ANCHOR_TICKER_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_PRICE_MISMATCH = 0
LOOKAHEAD_LEAK = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0
```

---

# 47. Semantic safety — preserve

Hard targets:

```text
PROVISIONAL_WAVE_AS_CONFIRMED = 0
PROJECTION_AS_CONFIRMED_TARGET = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0
```

---

# 48. Family consensus safety targets

Hard targets:

```text
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
FAMILY_DEPENDENCY_MISMATCH = 0
TOLERANCE_WIDENING = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0
```

---

# 49. Shadow isolation

This task must keep:

```text
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

No selective live enablement here.

---

# 50. Focused tests — dependency graph

Required:

- correct dependency set for every implemented family
- W0-only difference does not contaminate W0-independent family
- W3 difference contaminates W3-dependent family
- formula version change invalidates stale dependency registry
- unknown family fails closed

---

# 51. Focused tests — equivalence classes

Required:

- same degree/state + shared active structure groups safely
- materially different active structures remain separate
- grand/current cycle never merged
- provisional/confirmed status difference prevents unsafe equivalence where material
- member IDs all validate

---

# 52. Focused tests — ambiguity schema

Required:

- `AMBIGUOUS + competing IDs` valid
- invalid competing ID rejected
- competing ID from wrong ticker rejected
- competing ID from wrong degree/class rejected
- true insufficient structure can still return no IDs
- backend never chooses one member during ambiguity

---

# 53. Focused tests — family consensus

Required:

- exact same dependencies → EXACT_INVARIANT
- different dependencies / same canonical zone → PRICE_EQUIVALENT
- different visible zone → MATERIAL_VARIATION
- not applicable → NOT_APPLICABLE
- materially variant family omitted
- stable sibling family survives

---

# 54. Focused tests — SK hynix

Fixture must prove:

```text
W0 ambiguity
does not automatically delete W0-independent current-rebound analysis
```

but also:

```text
W0-dependent family
cannot be declared stable without its own consensus
```

---

# 55. Focused tests — TSLA

Fixture must prove:

```text
true competing current-cycle structures
remain material when visible zones differ
```

No false stabilization.

---

# 56. Focused tests — TSM

Fixture must prove:

```text
W3-dependent family becomes material
when alternative W3 endpoints materially alter its output
```

even if W0/W1/W2/W4/W5 match.

---

# 57. Focused tests — confluence filtering

Required:

- unstable Fib removed before confluence calculation
- deterministic pivot/Bollinger remains
- stable Fib remains
- confluence score recalculated
- explanation cannot cite removed unstable family
- cross-timeframe source provenance remains exact

---

# 58. Full-universe shadow replay

Run all 20 monitored subjects.

Per subject report:

```text
full hypothesis stability
equivalence class count
family states
eligible Fib family count
omitted unstable family count
SR-only fallback
cross-timeframe confluence count
shadow render status
```

---

# 59. SK hynix exact shadow comparison

Create both:

```text
BEFORE family-consensus repair
AFTER family-consensus repair
```

Show:

```text
월봉
주봉
일봉
종합
```

For every displayed Fib-derived zone list:

```text
family
method family
dependency endpoints
consensus state
source degree
```

Do not dump IDs in user-like prose; keep IDs in audit tables.

---

# 60. Readiness policy

The task can finish with:

```text
PRICE_STRUCTURE_V3_FAMILY_CONSENSUS =
INTEGRATED_READY_NOT_ARMED
```

when:

```text
dependency graph PASS
equivalence class PASS
ambiguous candidate-set contract PASS
family consensus PASS
confluence filtering PASS
SK hynix family-level result safe
TSLA false-stabilization = 0
TSM dependency-conflict handling PASS
previous stable regression = 0
valid abstention regression = 0
numeric/temporal/security safety all pass
full replay safe
P0 = 0
material P1 = 0
```

It is NOT necessary that:

```text
all 20 subjects have one stable Elliott hypothesis
```

---

# 61. Production enablement readiness

Set:

`PRODUCTION_ENABLEMENT_READY = YES`

only if a later bounded enablement can safely expose:

```text
deterministic SR
+ only family-stable Fib/confluence
```

Do not enable it in this task.

Expected next action after full PASS:

`BOUNDED_PRICE_STRUCTURE_V3_FAMILY_SELECTIVE_ENABLEMENT`

---

# 62. Required architecture docs

Create/update:

1. `docs/architecture/WAVE_HYPOTHESIS_EQUIVALENCE_CLASS.md`
2. `docs/architecture/FIB_FAMILY_ENDPOINT_DEPENDENCY.md`
3. `docs/architecture/FIB_FAMILY_CONSENSUS_POLICY.md`
4. `docs/architecture/PRICE_STRUCTURE_V3_AMBIGUITY_SET.md`
5. `docs/architecture/FAMILY_FILTERED_CONFLUENCE.md`
6. update `PRICE_STRUCTURE_WAVE_FIB_V3.md`
7. update `PRICE_STRUCTURE_V3_AI_FEEDBACK_LOOP.md`
8. update `PRICE_STRUCTURE_V3_SHADOW_POLICY.md`

---

# 63. Required reports

Create:

1. `docs/reports/20260826-v3-material-variation-root-cause.md`
2. `docs/reports/20260826-v3-fib-family-dependency-audit.md`
3. `docs/reports/20260826-v3-hypothesis-equivalence-class-audit.md`
4. `docs/reports/20260826-v3-ambiguity-set-validation.md`
5. `docs/reports/20260826-v3-family-consensus-stability.md`
6. `docs/reports/20260826-v3-family-filtered-confluence-audit.md`
7. `docs/reports/20260826-sk-hynix-family-consensus-validation.md`
8. `docs/reports/20260826-v3-tsla-true-conflict-control.md`
9. `docs/reports/20260826-v3-tsm-w3-dependency-control.md`
10. `docs/reports/20260826-v3-seven-subject-before-after.md`
11. `docs/reports/20260826-v3-full-universe-family-replay.md`
12. `docs/reports/20260826-user-reference-wave-engine-byte-audit.md`
13. `docs/reports/20260826-v3-ohlcv-default-consistency-audit.md`
14. `docs/reports/20260826-v3-family-consensus-safety-parity.md`
15. `docs/reports/20260826-v3-family-consensus-readiness.md`
16. `docs/reports/20260826-v3-family-consensus-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-v3-family-consensus-readiness.json`

---

# 64. Required root-cause table

For the original 7 variation subjects, show:

```text
Ticker
Runs
Selection frequency
Degree frequency
Primary divergence category
Divergent endpoint labels
Shared endpoint labels
Full-hypothesis stability
Family-level stability
Safe families
Omitted families
```

---

# 65. Required SK hynix table

At minimum:

```text
FULL_HYPOTHESIS_STABILITY
EQUIVALENCE_CLASS_COUNT

WAVE1_RETRACEMENT
WAVE3_RETRACEMENT
PRIMARY_CYCLE_RETRACEMENT
CURRENT_REBOUND

W5:
WAVE1_MULTIPLE
WAVE3_MULTIPLE
SPAN03_MULTIPLE

FINAL_MONTHLY_RESISTANCE
FINAL_WEEKLY_RESISTANCE
FINAL_DAILY_RESISTANCE
FINAL_CROSS_TIMEFRAME_RESISTANCE
```

Each with:

```text
EXACT_INVARIANT /
PRICE_EQUIVALENT /
MATERIAL_VARIATION /
N/A
```

---

# 66. Required AI protocol report

Report actual runtime:

```text
model
reasoning effort
call count
runtime failures
semantic rejections

7 difficult subjects:
  5 runs each

stable controls:
  3 runs each

abstention controls:
  3 runs each
```

Do not expose hidden chain-of-thought.

---

# 67. Gates

Set exactly:

```text
MATERIAL_VARIATION_ROOT_CAUSE =
PASS / FAIL

FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY =
PASS / FAIL

FIB_FAMILY_WITHOUT_ENDPOINT_DEPENDENCY =
0 / NONZERO

WAVE_HYPOTHESIS_EQUIVALENCE_CLASS =
PASS / FAIL

AMBIGUITY_SET_CONTRACT =
PASS / FAIL

FAMILY_CONSENSUS =
PASS / PARTIAL / FAIL

SK_HYNIX_FULL_HYPOTHESIS_STABILITY =
STABLE /
MATERIAL_VARIATION /
VALID_ABSTENTION

SK_HYNIX_FAMILY_LEVEL_PRICE_STRUCTURE =
PASS / PARTIAL / FAIL

SK_HYNIX_CURRENT_REBOUND_STABILITY =
EXACT_INVARIANT /
PRICE_EQUIVALENT /
MATERIAL_VARIATION /
NOT_APPLICABLE

TSLA_TRUE_CONFLICT_PRESERVED =
PASS / FAIL

TSM_W3_DEPENDENCY_CONFLICT =
PASS / NOT_OBSERVED / FAIL

GRAND_CYCLE_USER_ROLE_POLICY =
PASS / FAIL

FAMILY_FILTERED_CONFLUENCE =
PASS / FAIL

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE =
0 / NONZERO

UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

PREVIOUS_STABLE_REGRESSION =
0 / NONZERO

VALID_ABSTENTION_FORCED_TO_SELECTION =
0 / NONZERO

USER_REFERENCE_ENGINE_AVAILABLE =
YES / NO

REFERENCE_METHOD_COMPARISON =
REFERENCE_MATCH /
DIFFERENT_BUT_DEFENSIBLE /
REFERENCE_TEMPORAL_ISSUE /
THESIS_MONITOR_METHOD_ISSUE /
MATERIAL_METHOD_CONFLICT /
NOT_OBSERVED

STALE_INTERNAL_OHLCV_DEFAULT_REFERENCE =
0 / NONZERO

TOLERANCE_WIDENING =
0 / NONZERO

CURRENT_USER_VISIBLE_MESSAGE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_V3_FAMILY_CONSENSUS =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 68. Hard targets

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PROVISIONAL_WAVE_AS_CONFIRMED = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

FAMILY_DEPENDENCY_MISMATCH = 0
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

TOLERANCE_WIDENING = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0

TSLA_FALSE_STABILIZATION = 0
PREVIOUS_STABLE_REGRESSION = 0
VALID_ABSTENTION_FORCED_TO_SELECTION = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

---

# 69. Full validation

Required:

```text
focused dependency tests PASS
focused equivalence tests PASS
focused ambiguity-set tests PASS
focused family-consensus tests PASS
focused SK hynix tests PASS
focused TSLA negative-control tests PASS
focused TSM dependency tests PASS
focused confluence-filter tests PASS

7-subject 5-run trial complete
stable controls complete
abstention controls complete

full 20-subject replay safe
reference source byte audit completed if source available
OHLCV default consistency audit complete

full pytest PASS
Ruff PASS
git diff --check PASS
Knowledge / Chart Knowledge version-consistency PASS
Public Action unchanged
operation IDs unchanged
implementation SHA Actions PASS
final main Actions PASS
API /health PASS
worktrees clean
```

---

# 70. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

MATERIAL_VARIATION_ROOT_CAUSE = ...

ORIGINAL_MATERIAL_VARIATION_SUBJECTS =
000660,003690,005490,005930,010120,TSLA,TSM

FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY = ...
FIB_FAMILY_WITHOUT_ENDPOINT_DEPENDENCY = 0

WAVE_HYPOTHESIS_EQUIVALENCE_CLASS = ...
AMBIGUITY_SET_CONTRACT = ...
FAMILY_CONSENSUS = ...

SK_HYNIX_FULL_HYPOTHESIS_STABILITY = ...
SK_HYNIX_EQUIVALENCE_CLASS_COUNT = ...
SK_HYNIX_FAMILY_LEVEL_PRICE_STRUCTURE = ...

SK_HYNIX_WAVE1_RETRACEMENT = ...
SK_HYNIX_WAVE3_RETRACEMENT = ...
SK_HYNIX_PRIMARY_CYCLE_RETRACEMENT = ...
SK_HYNIX_CURRENT_REBOUND_STABILITY = ...

SK_HYNIX_W5_WAVE1_MULTIPLE = ...
SK_HYNIX_W5_WAVE3_MULTIPLE = ...
SK_HYNIX_W5_SPAN03_MULTIPLE = ...

SK_HYNIX_FINAL_MONTHLY_RESISTANCE = ...
SK_HYNIX_FINAL_WEEKLY_RESISTANCE = ...
SK_HYNIX_FINAL_DAILY_RESISTANCE = ...
SK_HYNIX_FINAL_CROSS_TIMEFRAME_RESISTANCE = ...

TSLA_TRUE_CONFLICT_PRESERVED = ...
TSLA_FALSE_STABILIZATION = 0

TSM_W3_DEPENDENCY_CONFLICT = ...

GRAND_CYCLE_USER_ROLE_POLICY = ...

FAMILY_FILTERED_CONFLUENCE = ...
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

SEVEN_SUBJECT_MATERIAL_IMPROVEMENT = ...
SEVEN_SUBJECT_MINOR_IMPROVEMENT = ...
SEVEN_SUBJECT_NO_ADDED_VALUE = ...
SEVEN_SUBJECT_WORSE = 0

PREVIOUS_STABLE_REGRESSION = 0
VALID_ABSTENTION_FORCED_TO_SELECTION = 0

USER_REFERENCE_ENGINE_AVAILABLE = ...
REFERENCE_SOURCE_SHA256 = ...
REFERENCE_METHOD_COMPARISON = ...

STALE_INTERNAL_OHLCV_DEFAULT_REFERENCE = 0

AI_RUNTIME_CALLS = ...
AI_RUNTIME_FAILURES = ...
AI_SEMANTIC_REJECTIONS = ...

KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
LOOKAHEAD_LEAK = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

FAMILY_DEPENDENCY_MISMATCH = 0
TOLERANCE_WIDENING = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

PRICE_STRUCTURE_V3_FAMILY_CONSENSUS = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_FAMILY_SELECTIVE_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 71. Mandatory completion ZIP

Create:

`20260826-price-structure-v3-family-consensus-stability-bounded-repair-bundle.zip`

Include:

- exact instruction
- root-cause report
- dependency registry audit
- equivalence-class audit
- ambiguity-set audit
- family consensus report
- family-filtered confluence report
- SK hynix exact validation
- TSLA negative control
- TSM dependency control
- 7-subject before/after
- full-universe replay
- reference byte audit if available
- OHLCV default consistency audit
- safety parity
- readiness
- artifact index

Do not include:
- secrets
- auth headers
- account identifiers
- hidden chain-of-thought

Compute/report SHA-256.

---

# 72. Severity

## P0

- wrong security/price basis
- look-ahead pivot
- AI authoritative technical price
- unstable Fib exposed as confirmed user-visible level
- projection presented as guaranteed target
- technical output mutates business investment logic
- shadow leaks into live output
- replay mutates production state
- secret/private egress

## P1

- Fib family has no endpoint dependency registry
- W0 ambiguity suppresses an otherwise exact-invariant current family without explanation
- unstable family remains in confluence
- materially different TSLA structures are falsely collapsed
- W3-dependent TSM family is incorrectly called stable
- equivalence class mixes grand/current degrees
- ambiguity set backend silently chooses one member
- previous stable subjects regress
- valid abstention is forced into a wave
- tolerance widened to manufacture stability

## P2

- full Elliott count remains ambiguous while stable family output is usable
- grand-cycle context omitted from short renderer
- some stocks have SR only and no Fib
- short-listing history remains partial
- reference method differs but both are defensible
- minor wording differences

---

# 73. Final principle

Do not make the system answer:

```text
"Which one Elliott count is the only correct count?"
```

when the evidence does not support that.

Make it answer:

```text
"Across the defensible counts,
which price-structure conclusions do not change?"
```

For SK hynix, if competing current-cycle counts only disagree about W0:

```text
do not force W0
do not throw away every Fib
```

Instead:

```text
keep Fib families whose required endpoints are invariant
omit Fib families whose required endpoints are disputed
rebuild confluence from only safe sources
```

For TSLA, if the competing structures truly change the active price map:

```text
do not stabilize it artificially
show deterministic SR only
```

That is the final stability philosophy for v3.
