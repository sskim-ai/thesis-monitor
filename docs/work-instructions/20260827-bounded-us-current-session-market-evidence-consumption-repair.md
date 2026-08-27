# thesis-monitor — BOUNDED_US_CURRENT_SESSION_MARKET_EVIDENCE_CONSUMPTION_REPAIR
## Shared US market digest plan + evidence-utilization validator
## Immutable run-41 replay + next natural US morning reproof
## Price Structure v3 remains NOT ARMED

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `BOUNDED_US_CURRENT_SESSION_MARKET_EVIDENCE_CONSUMPTION_REPAIR`
- Task class: `BOUNDED_MATERIAL_P1_REPAIR`
- Source policy: preserve current production source policy
- Frozen natural run: `41`
- Frozen packet: `2026-08-27-us-run-41-ae4f42c23abc`
- Frozen target completed US session: `2026-08-26`
- Latest reported final/main/operating entering this repair:
  `d625eaca37a461f9754e080362778986cddb2b52`
- Previous main before the read-only report:
  `ae4d22a4134341f7dfeffc4aef918c97e56091b2`
- Current US Track A state:
  `BOUNDED_REPAIR_REQUIRED`
- Current Price Structure v3:
  `INTEGRATED_READY_NOT_ARMED`
- Price Structure Track C:
  `DO_NOT_START`
- Current KR natural reproof:
  `PENDING`
- Open P0:
  `0`
- Open material P1:
  `1`
- Production Assist:
  preserve `OFF`
- Runtime behavior diff entering this repair:
  `0`

Resolve actual latest clean `origin/main` and operating SHA first. Record lineage.

Do not reopen already-passing packet claim, temporal, numeric-registration, or exactly-once logic unless a
direct regression is demonstrated.

---

# 1. Source-supported defect statement

The 2026-08-27 natural US morning review for completed session `2026-08-26` proved that acquisition,
packet persistence, numeric registration, temporal classification, packet ownership and delivery all
worked.

The material P1 occurred downstream in evidence selection / digest consumption.

The canonical packet contained:

```text
SPY   766.08   +0.0222%
QQQ   711.37   +0.0915%
IWM   298.93   -0.1003%
SOXX  515.40   +0.2607%
RSP   222.11   +0.1533%   CURRENT_DIRECTIONAL
```

It also contained same-session sector context, including:

```text
XLI   Industrials   +1.0874%   CURRENT_DIRECTIONAL
XLV   Health Care   -0.9983%   CURRENT_DIRECTIONAL
```

The full supported sector set had 11 current-directional rows and one `CURRENT_LEVEL_ONLY` row
(XLC).

Yet the AI-authored `market-review.json` selected only:

```text
market:real_yield:DFII10
market:oil:DCOILWTICO
market:nominal_yield:DGS10
```

No current-session core ETF, RSP, or sector fact survived into AI reasoning.

The final delivered digest reduced this further to a single dated macro fact:

```text
공식 관측(8/25) 미국 실질금리가 -6bp 움직였습니다.
```

The deterministic fallback shared the same omission.

Therefore:

```text
acquisition                    PASS
numeric registration           PASS
temporal normalization         PASS
AI evidence input boundary     PASS
current-session evidence use   FAIL
deterministic fallback use     FAIL
```

This is NOT a prompt-only defect.

---

# 2. Frozen run-41 controls

Use immutable natural production evidence as the regression fixture.

```text
Run ID:
41

Target session:
2026-08-26

Packet:
2026-08-27-us-run-41-ae4f42c23abc

Packet ready:
2026-08-27 08:20:09 KST

Claim owner:
codex-us-backup

Route:
AI

Delivery:
14/14

Exactly once:
PASS

Duplicate / orphan / unowned retry:
0 / 0 / 0
```

The historical packet, delivery and receipt must never be mutated.

Replay creates only new test/report artifacts.

---

# 3. Existing passing gates — preserve exactly

The natural review already proved:

```text
CURRENT_PACKET_CLAIM = PASS
STALE_PENDING_PACKET_CLAIM = 0
WRONG_TARGET_SESSION_PACKET = 0

WAIT_CURRENT_PACKET_POLICY = PASS
PRIMARY_BACKUP_OWNERSHIP = PASS

EXACTLY_ONCE = PASS
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0

US_CORE_ETF_SESSION_MATCH = PASS
RSP_STATE_VALID = PASS

NASDAQ_BREADTH_BOUNDARY = PASS
PUBLICATION_PENDING_AS_ZERO = 0
FABRICATED_EXCHANGE_BREADTH = 0

MACRO_TEMPORAL_BOUNDARY = PASS
SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
STALE_MACRO_AS_CURRENT = 0

AI_EVIDENCE_CURRENT_SESSION = PASS
AI_UNREGISTERED_NUMERIC = 0
AI_CALCULATED_MARKET_NUMERIC = 0

AI_FALLBACK_MARKET_SEMANTIC_PARITY = PASS
AI_FALLBACK_TEMPORAL_PARITY = PASS

US_EXACT_MESSAGE_PAYLOAD_MATCH = PASS

V3_PRICE_STRUCTURE_LEAK = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
```

Do not trade these away to improve evidence utilization.

---

# 4. Current material loss

The evidence-utilization report classified these seven as material loss:

```text
SPY
QQQ
IWM
SOXX
RSP
XLI leader
XLV laggard
```

Natural review result:

```text
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 7
CURRENT_DIRECTIONAL_DROPPED = 11
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = FAIL
OPEN_MATERIAL_P1 = 1
```

Important distinction:

```text
all 11 directional sector facts do NOT need to appear in prose
```

The defect is that the entire current-session market cross-section disappeared.

---

# 5. Repair principle

The daily US market digest must first answer:

```text
What happened in the completed US market session?
```

before it answers:

```text
What did lagged rates / oil / macro observations say?
```

Canonical evidence order:

```text
1. current-session market direction / style
   SPY / QQQ / IWM / SOXX

2. participation / equal-weight context
   RSP

3. material current-session sector dispersion
   bounded leader / laggard context

4. exact-session breadth state
   if published / else PUBLICATION_PENDING

5. temporally valid macro context
   rates / VIX / oil / FX
```

This is an ownership hierarchy, not a requirement to print every number.

---

# 6. Required work split

This work MUST be splittable.

Recommended:

```text
Track A
shared UsMarketDigestPlan / evidence-selection ownership

Track B
runtime evidence-utilization validator / completeness gates

Track C
run-41 integrated replay + next natural US morning reproof
```

Tracks A and B may run in parallel in separate worktrees if ownership/files do not conflict.

Track C starts only after A and B are merged/rebased onto the same latest safe main.

Recommended branches:

```text
codex/us-shared-market-digest-plan-repair
codex/us-market-evidence-utilization-validator
codex/us-run41-integration-replay
```

---

# 7. Track A — shared US market digest plan

Introduce or extend one shared deterministic planning/selection layer, named according to repository
conventions.

Conceptually:

```text
canonical US packet
→ shared market digest plan
→ AI evidence-selection contract
→ deterministic fallback renderer
```

Do not create separate business logic for AI and fallback.

If a compatible existing plan object exists, extend it instead of adding a duplicate abstraction.

---

# 8. Plan ownership slots

The shared plan should explicitly represent semantic slots similar to:

```text
CURRENT_MARKET
PARTICIPATION_STYLE
SECTOR_DISPERSION
BREADTH_STATE
MACRO_CONTEXT
```

Use repository naming conventions.

Each selected evidence item must retain:

```text
evidence ID
canonical numeric references
observation date
state
temporal role
materiality
selection / omission reason
```

No AI-created numeric values.

---

# 9. CURRENT_MARKET slot

When safe current-session core ETF facts exist, the plan must preserve a market cross-section.

It does NOT need to print all:

```text
SPY
QQQ
IWM
SOXX
```

individually.

It MAY synthesize deterministic semantic structure such as:

```text
broad market roughly flat
Nasdaq/growth roughly flat
small caps slightly weaker
semiconductors relatively firmer
```

provided all claims map to backend-owned numbers/evidence refs.

Hard:

```text
CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = PASS
CORE_ETF_ALL_DROPPED = 0
```

---

# 10. Near-flat session handling

Do not allow tiny returns to be treated as "not useful, drop everything."

If current-session returns are near zero:

the market slot may be rendered as:

```text
mixed / near-flat / limited index movement
```

using existing deterministic threshold semantics if they already exist.

Do not invent new arbitrary thresholds without documenting/test-driving them.

The key invariant is:

```text
near-flat current market evidence
still owns the current-session market summary
```

instead of being replaced entirely by older macro.

---

# 11. RSP participation/style slot

RSP remains:

```text
equal-weight participation evidence
```

not exchange breadth.

For run-41:

```text
RSP = +0.1533%
state = CURRENT_DIRECTIONAL
```

It was classified as material loss when omitted.

The shared plan must preserve RSP when its directional/style relationship is material to the session
interpretation.

Hard:

```text
RSP_MATERIAL_EVIDENCE_DROPPED = 0
RSP_AS_EXCHANGE_BREADTH = 0
RSP_DIRECTION_INVENTED = 0
```

If RSP is `CURRENT_LEVEL_ONLY`, no direction may be invented.

---

# 12. Sector dispersion slot

Do not dump all 11 directional sectors.

Use backend-owned bounded ranking/materiality.

For run-41 the canonical extrema control is:

```text
leader:
XLI +1.0874%

laggard:
XLV -0.9983%
```

The plan should preserve material sector dispersion when it clearly adds current-session structure.

Hard:

```text
MATERIAL_SECTOR_EXTREMES_ALL_DROPPED = 0
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0
```

If sector dispersion is immaterial or no directional sector evidence is safe:

```text
SECTOR_DISPERSION = OMITTED_SAFE
```

No forced prose.

---

# 13. Breadth-state slot

Nasdaq exact-session breadth for the frozen review was:

```text
PUBLICATION_PENDING
latest official source session = 2026-08-24
```

The plan may preserve publication state when material.

It must not:

```text
reuse 8/24 breadth as 8/26
turn pending into zero
use RSP as Nasdaq breadth
```

Hard:

```text
NASDAQ_BREADTH_BOUNDARY = PASS
RSP_AS_EXCHANGE_BREADTH = 0
PUBLICATION_PENDING_AS_ZERO = 0
```

---

# 14. Macro-context slot

Macro remains useful but secondary when current-session market evidence exists.

For run-41, the delivered real-yield fact was explicitly dated `8/25`.

This temporal behavior was safe and must remain safe.

Required hierarchy:

```text
current market structure
→ first

macro
→ explanatory / contextual
```

Hard:

```text
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0
STALE_MACRO_AS_CURRENT = 0
```

---

# 15. Macro may lead only under explicit valid exception

Do not ban macro-led messages universally.

A macro-first digest may be valid only when an explicit existing policy says the current session is
dominated by a material same-session macro event and current-session market structure is still
represented sufficiently.

Required validator contract:

```text
macro-first
does NOT mean
market-cross-section absent
```

A message containing only prior/lagged macro while current market evidence is safely available is invalid.

---

# 16. AI evidence selection contract

The AI path must receive the shared plan or an equivalent structured selection contract.

The AI must not be free to discard every current-session market slot while selecting only macro IDs.

Require evidence references for:

```text
market slot
participation/style slot if selected
sector slot if selected
macro slot if selected
```

Hard:

```text
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
AI_MACRO_ONLY_SELECTION_WITH_CURRENT_MARKET = 0
```

Do not solve this with prompt wording alone.

---

# 17. Deterministic fallback contract

The fallback path must render from the same plan/semantic ownership.

Hard:

```text
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
AI_FALLBACK_MARKET_PLAN_DIVERGENCE = 0
```

The fallback must not recreate the prior macro-only omission.

---

# 18. Evidence omission reasons

For every eligible material evidence family, the plan must record one of:

```text
SELECTED
OMITTED_SAFE_NOT_MATERIAL
OMITTED_SAFE_LENGTH_BUDGET
OMITTED_UNAVAILABLE
OMITTED_TEMPORAL
```

Do not permit an unexplained omission state for mandatory current-market ownership.

Hard:

`UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION = 0`

---

# 19. Track B — evidence-utilization validator

Add a runtime-safe validator that checks whether the final candidate actually consumed the current-session
evidence required by the plan.

This validator must operate on:

```text
evidence refs / plan slots / provenance bindings
```

not keyword scanning of rendered Korean/English prose.

---

# 20. Validator mandatory gate

When:

```text
safe current-session core market evidence exists
```

the final digest must contain at least one bound current-market interpretation/claim from the shared plan.

Hard:

```text
CORE_MARKET_SLOT_UNCONSUMED = 0
```

Run-41 broken digest must fail this gate.

---

# 21. Validator RSP gate

When RSP is selected by the plan as material:

the rendered candidate must bind/use the RSP evidence ref or a plan-derived participation statement
that contains its provenance.

Hard:

`SELECTED_RSP_SLOT_UNCONSUMED = 0`

Run-41 broken digest should fail.

---

# 22. Validator sector gate

When material sector dispersion is selected:

at least one bounded sector-dispersion claim must survive.

It is NOT necessary to print every sector.

Hard:

```text
SELECTED_SECTOR_DISPERSION_UNCONSUMED = 0
MATERIAL_SECTOR_EXTREMES_ALL_DROPPED = 0
```

Run-41 broken digest should fail.

---

# 23. Macro-only detection

Add explicit rejection for:

```text
current-session market evidence safely available
+
final digest contains only macro evidence
```

Hard:

`MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0`

The exact broken run-41 digest is a positive failure fixture.

---

# 24. Evidence-utilization score must not be a vague heuristic

Do not add an opaque LLM score.

Use deterministic slot/evidence ownership.

Recommended counters:

```text
required_current_slots
selected_current_slots
consumed_current_slots
selected_material_refs
consumed_material_refs
safe_omissions
unexplained_omissions
```

The pass/fail contract must be reproducible.

---

# 25. Validator must not cause numeric dump

Do not satisfy the validator by forcing:

```text
SPY ...
QQQ ...
IWM ...
SOXX ...
RSP ...
XLE ...
...
```

all into the message.

The validator checks semantic coverage, not raw field count.

Hard:

`VALIDATOR_FORCED_NUMERIC_DUMP = 0`

---

# 26. Message-length budget

Preserve existing concise-message limits.

If length pressure requires omission:

```text
core current-market slot
has priority over secondary macro detail
```

Materiality priority:

```text
current-market cross-section
> selected participation/style
> selected sector dispersion
> breadth state when material
> macro context
```

Do not remove exact safety/temporal qualification to save characters.

---

# 27. Run-41 expected semantic repair

Do not hard-code this wording.

The integrated run-41 replay should be able to convey a current-session structure broadly equivalent to:

```text
US indices were near flat/mixed,
semiconductors were somewhat firmer,
small caps were slightly weaker,
equal-weight participation was modestly positive,
and sector dispersion was visible with industrials strong and health care weak.

Rates may then be added as dated secondary context.
```

Use actual packet evidence.

The repaired message does not need every sentence above.

---

# 28. Broken run-41 fixture must fail new validator

The exact historical delivered digest:

```text
🤖 AI 보조 미국시장 점검 · US Pilot 4/5

🎯 판단
공식 관측(8/25) 미국 실질금리가 -6bp 움직였습니다. 성장주 멀티플에는 우호적입니다.

🔎 왜 중요한가
현재는 경기 확장 하나로 모든 위험자산이 오르는 시장이라기보다, 위험선호와 할인율 신호가 함께 가격을 결정하는 시장입니다.

📌 다음 확인
• 다음 공식 실질금리와 명목금리 관측에서 할인율 완화가 이어지는지 확인합니다.
```

must fail for:

```text
CORE_MARKET_SLOT_UNCONSUMED
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE
```

and any selected RSP/sector slot that was required by the repaired plan.

This is a regression fixture, not a production mutation.

---

# 29. Positive control — bounded concise candidate

Create a deterministic test candidate that:

```text
uses one current-market cross-section statement
uses RSP if selected
uses one bounded sector dispersion statement if selected
optionally uses one macro context statement
```

It must pass without printing all ETF numbers.

---

# 30. Negative control — no safe current market data

If no safe current-session ETF evidence exists:

do not fail merely because there is no market slot.

Existing fail-closed behavior applies.

A macro-only message may be valid only if its macro evidence is temporally safe and the absence of current
market evidence is explicit in the plan state.

---

# 31. Negative control — level-only evidence

If RSP or a sector ETF is:

```text
CURRENT_LEVEL_ONLY
```

the plan may use the level only where existing policy permits.

No direction.

Hard:

```text
LEVEL_ONLY_DIRECTION_LEAK = 0
```

---

# 32. Negative control — publication pending breadth

If Nasdaq breadth is:

```text
PUBLICATION_PENDING
```

the validator must not require a breadth numeric.

No fake breadth.

---

# 33. Track C — integrated immutable run-41 replay

After Track A and B are merged/rebased to the same latest safe main:

replay:

```text
run = 41
packet = 2026-08-27-us-run-41-ae4f42c23abc
target = 2026-08-26
```

No Telegram send.

No manual task.

No DB mutation.

No assessment mutation.

No historical packet/delivery mutation.

---

# 34. Replay outputs

Produce:

```text
historical broken natural digest
shared plan for run-41
AI candidate after repair
deterministic fallback candidate after repair
exact diffs
evidence-ref utilization map
validator result
numeric provenance map
temporal map
```

---

# 35. Run-41 replay hard gates

Set:

```text
CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = PASS

CORE_ETF_ALL_DROPPED = 0
RSP_MATERIAL_EVIDENCE_DROPPED = 0
MATERIAL_SECTOR_EXTREMES_ALL_DROPPED = 0

MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0

AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS

AI_FALLBACK_MARKET_PLAN_DIVERGENCE = 0

CORE_MARKET_SLOT_UNCONSUMED = 0
SELECTED_RSP_SLOT_UNCONSUMED = 0
SELECTED_SECTOR_DISPERSION_UNCONSUMED = 0

UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION = 0
VALIDATOR_FORCED_NUMERIC_DUMP = 0

US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
```

---

# 36. Preserve run-41 safety gates

Replay must also preserve:

```text
CURRENT_PACKET_CLAIM = PASS
NASDAQ_BREADTH_BOUNDARY = PASS
MACRO_TEMPORAL_BOUNDARY = PASS

SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0

AI_UNREGISTERED_NUMERIC = 0
AI_CALCULATED_MARKET_NUMERIC = 0
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0

RSP_AS_EXCHANGE_BREADTH = 0
LEVEL_ONLY_DIRECTION_LEAK = 0
PUBLICATION_PENDING_AS_ZERO = 0
```

---

# 37. Do not repair packet timing / grace

Run-41 packet readiness/backup ownership passed.

This repair must not change:

```text
WAIT_CURRENT_PACKET
claim owner rules
primary/backup lease
fallback deadline
grace period
canary budget ownership
```

unless a new direct test failure proves necessity.

Hard:

`PACKET_OWNERSHIP_CODE_DIFF = 0`

---

# 38. Do not repair numeric registry

The US numeric registry passed in the natural review.

Do not broaden or alter numeric registry semantics merely to solve evidence utilization.

Hard:

`US_NUMERIC_REGISTRY_POLICY_DIFF = 0`

---

# 39. Do not repair macro temporal gate

Temporal safety passed.

Do not loosen it.

Hard:

`MACRO_TEMPORAL_POLICY_DIFF = 0`

Renderer/plan may change ordering/selection but temporal roles stay canonical.

---

# 40. Price Structure isolation

Price Structure v3 remains:

```text
INTEGRATED_READY_NOT_ARMED
```

Hard:

```text
PRICE_STRUCTURE_V3_CODE_DIFF = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
V3_PRICE_STRUCTURE_LEAK = 0
```

Do not start Price Structure Track C.

---

# 41. KR repair/reproof isolation

KR natural reproof remains an independent prerequisite.

Do not modify KR local-first or KR numeric-registry code in this task unless a shared generic helper requires a
strict compatibility-only change.

If shared code changes:

prove KR parity.

Hard:

`KR_MARKET_DIGEST_REGRESSION = 0`

---

# 42. Business investment-logic isolation

Market digest repair must not mutate stock investment logic.

Hard:

```text
BUSINESS_THESIS_MUTATION = 0
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
```

---

# 43. Focused Track A tests

Required:

```text
current market + macro
→ current market owns primary plan

near-flat SPY/QQQ + mixed IWM/SOXX
→ current-market slot still selected

RSP directional/material
→ participation slot selected

RSP level-only
→ no direction

material sector dispersion
→ bounded sector slot

no material sector dispersion
→ OMITTED_SAFE

Nasdaq breadth pending
→ pending preserved

macro prior-session
→ secondary/date-qualified
```

---

# 44. Focused Track B tests

Required:

```text
run-41 broken digest
→ validator FAIL

current-market-only concise digest
→ PASS

current-market + RSP + one sector dispersion + macro
→ PASS

numeric dump
→ not required

macro-only + current market available
→ FAIL

macro-only + no safe current market available
→ safe according to plan state

selected RSP omitted
→ FAIL

selected sector slot omitted
→ FAIL

safe omitted sector
→ PASS
```

---

# 45. Full regression

Required:

```text
Track A focused tests
Track B focused tests
run-41 integration replay tests
US market-message tests
numeric provenance tests
temporal tests
exactly-once tests
full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
```

No public Action change is expected.

---

# 46. Architecture docs

Create/update:

```text
docs/architecture/US_MARKET_DIGEST_EVIDENCE_OWNERSHIP.md
docs/architecture/US_MARKET_DIGEST_PLAN.md
docs/architecture/MARKET_EVIDENCE_UTILIZATION_VALIDATOR.md
```

Document:

```text
slot ownership
selection priority
safe omission reasons
AI/fallback shared ownership
validator semantics
macro-only rejection rule
near-flat session handling
```

---

# 47. Required reports

Create:

1. `docs/reports/20260827-us-current-session-evidence-root-cause.md`
2. `docs/reports/20260827-us-shared-market-digest-plan.md`
3. `docs/reports/20260827-us-market-evidence-selection-policy.md`
4. `docs/reports/20260827-us-evidence-utilization-validator.md`
5. `docs/reports/20260827-us-run41-shared-plan.md`
6. `docs/reports/20260827-us-run41-before-after-digest.md`
7. `docs/reports/20260827-us-run41-ai-fallback-after-repair.md`
8. `docs/reports/20260827-us-run41-evidence-utilization-after.md`
9. `docs/reports/20260827-us-run41-validator-result.md`
10. `docs/reports/20260827-us-market-message-safety-parity.md`
11. `docs/reports/20260827-us-bounded-repair-readiness.md`
12. `docs/reports/20260827-us-bounded-repair-artifact-index.md`

Machine-readable:

```text
docs/reports/20260827-us-run41-evidence-utilization-after.json
docs/reports/20260827-us-bounded-repair-readiness.json
```

---

# 48. Required repair gates

Set exactly:

```text
US_CURRENT_SESSION_EVIDENCE_ROOT_CAUSE =
PASS / FAIL

US_SHARED_MARKET_DIGEST_PLAN =
PASS / FAIL

CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED =
PASS / FAIL

CORE_ETF_ALL_DROPPED =
0 / NONZERO

RSP_MATERIAL_EVIDENCE_DROPPED =
0 / NONZERO

MATERIAL_SECTOR_EXTREMES_ALL_DROPPED =
0 / NONZERO

MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE =
0 / NONZERO

AI_CURRENT_SESSION_EVIDENCE_UTILIZATION =
PASS / FAIL

FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION =
PASS / FAIL

AI_FALLBACK_MARKET_PLAN_DIVERGENCE =
0 / NONZERO

CORE_MARKET_SLOT_UNCONSUMED =
0 / NONZERO

SELECTED_RSP_SLOT_UNCONSUMED =
0 / NONZERO

SELECTED_SECTOR_DISPERSION_UNCONSUMED =
0 / NONZERO

UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION =
0 / NONZERO

VALIDATOR_FORCED_NUMERIC_DUMP =
0 / NONZERO

US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS =
0 / NONZERO

RSP_AS_EXCHANGE_BREADTH =
0 / NONZERO

LEVEL_ONLY_DIRECTION_LEAK =
0 / NONZERO

PUBLICATION_PENDING_AS_ZERO =
0 / NONZERO

SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING =
0 / NONZERO

PRIOR_YIELD_AS_TODAY =
0 / NONZERO

PRIOR_VIX_AS_TODAY =
0 / NONZERO

LAGGING_WTI_AS_TODAY =
0 / NONZERO

AI_UNREGISTERED_NUMERIC =
0 / NONZERO

AI_CALCULATED_MARKET_NUMERIC =
0 / NONZERO

AI_DERIVED_SECTOR_RETURN =
0 / NONZERO

AI_DERIVED_SECTOR_RANKING =
0 / NONZERO

PACKET_OWNERSHIP_CODE_DIFF =
0 / NONZERO

US_NUMERIC_REGISTRY_POLICY_DIFF =
0 / NONZERO

MACRO_TEMPORAL_POLICY_DIFF =
0 / NONZERO

PRICE_STRUCTURE_V3_CODE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_RUNTIME_ARMED =
0 / NONZERO

KR_MARKET_DIGEST_REGRESSION =
0 / NONZERO

BUSINESS_THESIS_MUTATION =
0 / NONZERO

TELEGRAM_SEND =
0 / NONZERO

MANUAL_TASK =
0 / NONZERO

DB_MUTATION =
0 / NONZERO

OFFICIAL_ASSESSMENT_MUTATION =
0 / NONZERO

CODE_CORRECTNESS =
PASS / FAIL

US_BOUNDED_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING /
FAIL
```

---

# 49. Replay PASS state

If all repair/replay gates pass:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

US_BOUNDED_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING

US_TRACK_A =
REPLAY_PASS_NATURAL_REPROOF_PENDING

PRICE_STRUCTURE_TRACK_C =
DO_NOT_START

PRICE_STRUCTURE_V3 =
INTEGRATED_READY_NOT_ARMED
```

Do not claim US natural `LIVE_PASS` from replay.

---

# 50. Next natural US morning reproof

After repaired code is on operating main:

wait for the next naturally scheduled US morning run.

Do not manually trigger.

Read-only collect:

```text
run ID
target completed session
packet ID
route
shared digest plan
AI/fallback selection
exact delivery
receipt
current-session evidence utilization
```

---

# 51. Natural US reproof gates

The next natural message must prove:

```text
current packet/session correct
current-market slot consumed
RSP used if plan selects it
sector dispersion used if plan selects it
macro does not replace current market
temporal safety preserved
exactly once
```

Hard:

```text
NATURAL_US_CURRENT_MARKET_USED = PASS
NATURAL_US_MACRO_ONLY_WITH_CURRENT_MARKET = 0
NATURAL_US_MATERIAL_EVIDENCE_LOSS = 0
NATURAL_US_DUPLICATE = 0
NATURAL_US_ORPHAN = 0
```

Only then:

```text
US_TRACK_A = LIVE_PASS
```

---

# 52. Price Structure Track C relationship

Even after US natural reproof:

Price Structure Track C remains dependent on all master prerequisites, including KR natural reproof.

This repair must not automatically start or arm Price Structure.

---

# 53. Stop conditions

Stop and return bounded repair required if any:

```text
current-session market slot still disappears
AI path fixed but fallback remains macro-only
fallback fixed but AI remains macro-only
validator passes the historical broken run-41 digest
validator forces numeric dumping
RSP becomes exchange breadth
level-only direction leak appears
temporal macro safety regresses
packet ownership changes
numeric registry policy changes unexpectedly
Price Structure becomes armed
new P0
new material P1
```

---

# 54. Severity

## P0

- wrong-session market evidence becomes current
- duplicate live delivery
- unsupported numeric becomes authoritative
- historical run-41 production record mutated
- Price Structure accidentally armed

## P1

- all current-session core ETF evidence still omitted
- macro-only digest despite current market evidence
- selected material RSP omitted
- selected material sector dispersion omitted
- AI/fallback evidence ownership diverges materially
- evidence-utilization validator fails to reject broken run-41 digest
- validator requires raw numeric dump
- temporal safety regresses
- RSP mislabeled as breadth

## P2

- bounded wording differences
- nonmaterial sector omitted
- breadth remains publication pending
- natural reproof pending after replay PASS

---

# 55. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

INTEGRATION_BRANCH = ...
INTEGRATION_SHA = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

RUN41_PACKET =
2026-08-27-us-run-41-ae4f42c23abc

US_CURRENT_SESSION_EVIDENCE_ROOT_CAUSE = ...
US_SHARED_MARKET_DIGEST_PLAN = ...

CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = ...
CORE_ETF_ALL_DROPPED = 0

RSP_PLAN_STATE = ...
RSP_MATERIAL_EVIDENCE_DROPPED = 0

SECTOR_DISPERSION_PLAN_STATE = ...
MATERIAL_SECTOR_EXTREMES_ALL_DROPPED = 0

MACRO_CONTEXT_PLAN_STATE = ...
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0

AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = ...
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = ...
AI_FALLBACK_MARKET_PLAN_DIVERGENCE = 0

CORE_MARKET_SLOT_UNCONSUMED = 0
SELECTED_RSP_SLOT_UNCONSUMED = 0
SELECTED_SECTOR_DISPERSION_UNCONSUMED = 0

UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION = 0
VALIDATOR_FORCED_NUMERIC_DUMP = 0
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0

RUN41_BROKEN_DIGEST_VALIDATOR =
FAIL_AS_EXPECTED

RUN41_REPAIRED_AI_CANDIDATE =
...

RUN41_REPAIRED_FALLBACK_CANDIDATE =
...

RSP_AS_EXCHANGE_BREADTH = 0
LEVEL_ONLY_DIRECTION_LEAK = 0
PUBLICATION_PENDING_AS_ZERO = 0

SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0

AI_UNREGISTERED_NUMERIC = 0
AI_CALCULATED_MARKET_NUMERIC = 0
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0

PACKET_OWNERSHIP_CODE_DIFF = 0
US_NUMERIC_REGISTRY_POLICY_DIFF = 0
MACRO_TEMPORAL_POLICY_DIFF = 0

PRICE_STRUCTURE_V3_CODE_DIFF = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
KR_MARKET_DIGEST_REGRESSION = 0
BUSINESS_THESIS_MUTATION = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...

TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

US_BOUNDED_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING /
FAIL

NATURAL_US_REPROOF =
PENDING /
PASS /
FAIL

US_TRACK_A =
REPLAY_PASS_NATURAL_REPROOF_PENDING /
LIVE_PASS /
BOUNDED_REPAIR_REQUIRED

PRICE_STRUCTURE_TRACK_C =
DO_NOT_START

PRICE_STRUCTURE_V3 =
INTEGRATED_READY_NOT_ARMED

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_MORNING /
BOUNDED_REPAIR /
REVIEW_MASTER_GATES

ZIP = ...
ZIP_SHA256 = ...
```

---

# 56. Mandatory completion bundle

Create:

`20260827-bounded-us-current-session-market-evidence-consumption-repair-bundle.zip`

Include:

```text
exact work instruction
Track A implementation notes
Track B implementation notes
run-41 shared plan
broken/repaired exact digest
AI/fallback candidates
evidence-utilization JSON
validator result
safety parity
readiness
test/CI summary
artifact index
```

Do not include:

```text
secrets
auth headers
account identifiers
private tokens
hidden chain-of-thought
```

Compute SHA-256.

---

# 57. Final operating principle

A US daily market digest must not say:

```text
we had complete current-session market data,
but the only delivered market fact was yesterday's real yield.
```

The correct ownership is:

```text
current-session market structure
→ participation/style
→ material sector dispersion
→ breadth state
→ temporally safe macro context
```

The repair is complete only when AI and fallback share that ownership, a deterministic validator catches
material current-session evidence loss, run-41 replay passes, and the next natural US morning message
proves the behavior live.
