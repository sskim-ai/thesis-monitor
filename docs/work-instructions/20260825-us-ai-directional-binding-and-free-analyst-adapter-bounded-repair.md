# thesis-monitor — US AI Directional Relation Binding + Free Analyst Natural-Packet Adapter Bounded Repair

## Metadata

- Workstream: `US_AI_BOUNDED_REPAIR`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Authoring context: approximately `10:00 KST`
- Repository: `sskim-ai/thesis-monitor`
- Repair type: `TWO-TRACK_BOUNDED_REPAIR`
- Production promotion policy:
  - Track A production AI compatibility repair: **eligible for promotion after immutable replay + full validation**
  - Track B Free Analyst/Open Research adapter repair: **shadow-only; must not be promoted by this task**

### Current production baseline

Expected current main/operating:

`2e3e37cc75867d56a69211bbe93a3675cd87acd1`

Resolve the actual latest safe `origin/main` and operating SHA before implementation.

### Triggering morning review

Review branch:

`codex/20260825-us-morning-multi-proof-review`

Known review commits:

```text
WORK_INSTRUCTION = 4988317ed8ca07c4193b0050f2896e14b5d1a3a4
REPORT_COMMIT    = 4d1c8a9ba753ee92c79be7de8f9cd1dd546df3a2
```

Observed morning gates:

```text
US_PRODUCTION_NATURAL = LIVE_PASS
DELIVERY = 14/14
DUPLICATE = 0
ORPHAN = 0

MACRO_TEMPORAL_NATURAL = LIVE_PASS
INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS
KRX_0805_ROLE_TARGET_NATURAL = LIVE_PASS

OPEN_RESEARCH_SOURCE_TIME_CAUSALITY = PASS
OPEN_RESEARCH_SIDECAR = 14/14 PASS

US_AI_COMPATIBILITY_NATURAL = FAIL
FREE_ANALYST_NATURAL_FORMAT = 0/14 PASS, 14/14 FALLBACK

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 2
```

### Known P1s

#### P1-A — Inventory directional relation semantic binding

Observed examples include:

```text
MU:
Inventory relation wording = 15.7%p lower

TSLA:
Inventory relation wording = 26.6%p lower
```

The visible direction was correct, but candidate provenance bound directional prose such as `lower` to an absolute-gap field equivalent to:

`gap_percentage_points_abs`

instead of a signed / directional / comparator-compatible relation.

Expected current hard errors from the triggering review: `4`.
Verify the exact current count from immutable artifacts before changing code.

#### P1-B — US natural production-format packet → Free Analyst adapter

Open Research sidecar itself passed `14/14`, but the natural US production packet could not be consumed successfully by the shadow Free Analyst path:

```text
Free Analyst natural-format validation:
0/14 PASS
14/14 FALLBACK
```

The common research engine is already proven in KR and the US research sidecar itself passed.
The repair target is the **natural production-format adapter / normalization boundary**, not a rewrite of Open Research or Free Analyst reasoning.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260825-us-ai-directional-binding-and-free-analyst-adapter-bounded-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse origin/main
git rev-parse origin/codex/open-research-event-attribution-shadow
git rev-parse origin/codex/adaptive-renderer-selector-shadow
git rev-parse origin/codex/20260825-us-morning-multi-proof-review
```

Then:

1. verify actual current production main/operating
2. verify triggering natural packet/report artifacts
3. verify actual latest shadow branch tips
4. commit/push this exact instruction as a **docs-only instruction commit**
5. record instruction path / commit / version
6. use separate worktrees/branches for Track A and Track B
7. no force push / no history rewrite

---

# 1. Branch separation — mandatory

This task repairs two different code ownership domains.

Do not mix them into one uncontrolled branch.

## Track A — production AI compatibility repair

Create from latest safe production main:

`codex/us-ai-directional-relation-binding-repair`

This branch may be promoted to main **only** if Track A promotion gates pass.

## Track B — shadow Free Analyst adapter repair

Create from latest safe:

`codex/open-research-event-attribution-shadow`

Recommended branch:

`codex/us-natural-packet-free-analyst-adapter-repair`

This branch remains shadow-only.

After Track A implementation is complete, bring the minimal Track A compatibility commit into the Track B worktree if required for full combined replay.

Preferred:
- clean cherry-pick of the scoped Track A implementation commit

Do not merge production main wholesale into shadow unless required.

---

# 2. Hard prohibitions

Do NOT:

- merge Free Analyst to production main
- merge Adaptive Renderer to production main
- merge Open Research to production main
- enable research in production
- change Production Assist
- send Telegram from repair/replay
- rerun production US task manually
- rerun production providers to recreate the morning packet
- mutate production DB
- mutate receipts
- mutate notificationdelivery rows
- mutate assessments / warnings / investment-logic versions / Pilot
- enable Trade AR
- disable Inventory
- change Phase 9.0E
- change macro temporal policy
- change KRX/night-futures schedules
- loosen numeric validator
- loosen semantic validator
- allow absolute-gap fields to validate directional wording
- patch benchmark fixtures to hide failures

---

# 3. Immutable evidence lock

Locate the exact natural US packet used in the 2026-08-25 morning review.

Persist a repair evidence manifest containing:

```text
natural_packet_id
assessment_date
packet_created_at
packet SHA/ref
AI candidate ref
validator report ref
fallback ref
sent bundle ref
Free Analyst shadow input ref
Open Research sidecar ref
Adaptive Renderer artifact ref
```

Do not recollect providers for mandatory acceptance replay.

The first acceptance replay must use the exact immutable morning evidence.

---

# Track A — Production AI directional relation binding

# 4. Root-cause trace

Trace the full pipeline for the failing Inventory relation claim:

```text
canonical Inventory Fact
canonical comparator Fact
derived working-capital relation
relation registry / claim catalog
AI candidate evidence refs
candidate provenance
numeric validator
semantic validator
final wording
```

Identify exactly where:

```text
directional phrase:
lower / higher / above / below
```

became bound to an absolute relation.

Do not assume the bug is only in the renderer.

Inspect:
- relation construction
- relation serialization
- prompt evidence view
- registry ownership
- candidate support-map generation
- validator matching

---

# 5. Directional relation semantic contract

Implement or reuse a typed contract that distinguishes at minimum:

```text
SIGNED_DIRECTIONAL_GAP
ABSOLUTE_GAP
CURRENT_VALUE
COMPARATOR_VALUE
```

For percentage-point relations, preserve:

```text
signed_gap_pp
abs_gap_pp
direction:
  higher
  lower
  equal / immaterial if supported
lhs semantic
rhs semantic
comparison basis
period / date
relation ID
```

Exact names may follow repository style.

Do not create duplicate competing relation semantics if an existing canonical signed relation already exists.

---

# 6. Directional wording ownership

Required semantic rule:

```text
"X%p lower than Y"
→ must bind to signed / direction-compatible relation

"X%p higher than Y"
→ must bind to signed / direction-compatible relation

"difference is X%p"
→ may bind to absolute-gap relation if no direction is claimed
```

Absolute gap must never independently validate:

- lower
- higher
- below
- above
- trails
- exceeds

unless the direction is separately and correctly bound.

---

# 7. Comparator integrity

For every directional relation validate:

```text
lhs semantic
rhs semantic
comparison basis
period compatibility
relation direction
rendered direction
```

Examples:

```text
Inventory growth vs COGS growth
Inventory growth vs Revenue growth
```

Do not allow:

```text
Inventory vs COGS relation
→ validate wording about Revenue
```

---

# 8. Sign / wording controls

Mandatory positive cases:

```text
signed gap = -15.7pp
→ "15.7%p lower"
PASS

signed gap = +12.3pp
→ "12.3%p higher"
PASS
```

Mandatory negative cases:

```text
abs gap = 15.7pp only
→ "15.7%p lower"
REJECT

signed gap = -15.7pp
→ "15.7%p higher"
REJECT

wrong comparator
→ REJECT

wrong relation ID
→ REJECT
```

---

# 9. Preserve working-capital safety

This repair must not change:

- Inventory selection logic
- Inventory materiality threshold
- total Inventory semantic
- PIT/date rules
- no Inventory Days / CCC
- no unsupported demand/oversupply conclusion
- no hidden FCF inference
- Trade AR OFF

Only relation/provenance ownership should change.

---

# 10. Current production AI replay

Using the immutable morning packet, rerun the current production AI candidate generation non-delivery.

Expected:

```text
pre-repair hard errors ≈ 4
post-repair hard errors = 0
```

Record actual before/after counts.

Required:

```text
numeric PASS
semantic PASS
final-language PASS
temporal PASS
current-price RR ownership PASS
FCF period identity PASS
```

Runtime-quality-only issues may be classified separately.

---

# 11. Track A fallback parity

Compare repaired AI candidate to the deterministic fallback.

Target factual mismatch:

`0`

Check:

- Inventory
- FCF
- price/RR
- valuation
- macro
- next checks
- warnings

---

# 12. Track A promotion gate

Set:

```text
US_AI_DIRECTIONAL_RELATION_REPAIR =
PASS / FAIL

US_AI_COMPATIBILITY_REPLAY =
PASS / FAIL
```

Track A is promotion-eligible only if:

```text
hard errors = 0
Fact mismatch = 0
Trade AR leak = 0
temporal violation = 0
price/RR ownership error = 0
FCF period error = 0
full tests PASS
CI PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1_FROM_TRACK_A = 0
```

---

# Track B — US natural production-format → Free Analyst adapter

# 13. Root-cause classification

Do not rewrite Free Analyst blindly.

Classify the 0/14 failure into one or more actual branches:

```text
A. production packet field shape mismatch
B. enum / semantic normalization mismatch
C. claim/support-ref namespace mismatch
D. missing canonical context expected by Free Analyst
E. research-sidecar merge mismatch
F. renderer/validation envelope mismatch
G. other — document precisely
```

Record per-message failure classes.

---

# 14. Adapter ownership principle

Create or repair a typed normalization layer:

```text
US natural production packet
        ↓
Free Analyst canonical shadow input
```

The adapter must normalize shape, not reinterpret facts.

It may:

- rename/normalize supported fields
- map known enums
- convert production evidence refs into canonical shadow refs
- attach existing research sidecar refs
- carry market/session metadata
- preserve stored investment logic
- preserve Unknowns
- preserve macro temporal roles

It may NOT:

- invent missing facts
- perform new arithmetic
- infer unsupported context
- rewrite time semantics
- synthesize new financial conclusions

---

# 15. Adapter parity with KR/common core

US natural-format normalization must land in the same semantic Free Analyst contract already proven in KR.

Target:

```text
KR normalized semantic object
US normalized semantic object
→ same common Free Analyst schema
```

Market-specific fields may remain adapter-specific only where necessary.

No US-only fork of Free Analyst reasoning.

---

# 16. Evidence-ref namespace repair

If production packet refs and shadow refs differ, introduce a deterministic ref-normalization map.

Every final Free Analyst claim must still resolve to:

- canonical production Fact/relation ref
- research evidence ref where applicable
- thesis/expectation/valuation ref where applicable

No dangling refs.

Target:

```text
unresolved support refs = 0
```

---

# 17. Research sidecar preservation

The existing US Open Research sidecar passed `14/14`.

The adapter repair must preserve:

```text
source provenance
entity binding
event time
causal-time eligibility
negative-evidence boundaries
competing hypotheses
research claim refs
```

Do not regenerate research conclusions for mandatory replay.

Use the immutable sidecar.

---

# 18. Free Analyst 14-message replay

Using the immutable morning packet and immutable research sidecar:

Target:

```text
FREE_ANALYST_INPUTS = 14
FREE_ANALYST_VALIDATED = 14
FREE_ANALYST_FALLBACK = 0
```

If a message legitimately has no research value:
the Free Analyst may still validate a no-research/minimal analysis object.

Do not require every message to contain novel research synthesis.

---

# 19. Free Analyst safety targets

Hard targets:

```text
Fact mismatch = 0
unsupported numeric claim = 0
unsupported causality = 0
temporal violation = 0
Trade AR leak = 0
hidden arithmetic accepted = 0
external unsourced fact accepted = 0
unresolved evidence ref = 0
```

---

# 20. Adaptive Renderer replay

Run all 14 validated Free Analyst outputs through the existing Adaptive Renderer.

Record per message:

```text
selected renderer
selection reasons
material information loss
final message
```

Hard target:

```text
material information loss = 0
```

Do not retune renderer thresholds unless the adapter exposes a genuine schema bug.
If renderer tuning is needed, classify separately and keep bounded.

---

# 21. Open Research preservation

Revalidate:

```text
Open Research sidecar = 14/14 PASS
SOURCE_PROVENANCE = PASS
ENTITY_TIME_VALIDATION = PASS
EVENT_ATTRIBUTION_FACT_BOUNDARY = PASS
CAUSAL_ATTRIBUTION_SAFETY = PASS
NEGATIVE_EVIDENCE_SAFETY = PASS
```

This task is not a rewrite of the Open Research engine.

---

# Track C — Combined immutable morning replay

# 22. Combined replay stack

After Track A and B pass individually, run:

```text
immutable natural US packet
        ↓
repaired production relation semantics
        +
immutable Open Research sidecar
        ↓
Free Analyst adapter
        ↓
Free Analyst
        ↓
synthesis validator
        ↓
Adaptive Renderer
        ↓
existing hard validators
        ↓
shadow would-send bundle
```

No provider recollection.
No Telegram.

---

# 23. Combined target

Required:

```text
messages = 14

production AI candidate hard errors = 0

Free Analyst validated = 14/14
Free Analyst fallback = 0/14

Open Research sidecar = 14/14 PASS

Adaptive Renderer = 14/14 PASS

Fact mismatch = 0
unsupported numeric = 0
unsupported causality = 0
temporal violation = 0
Trade AR leak = 0
hidden arithmetic = 0
external unsourced fact = 0
material information loss = 0

production mutation = 0
Telegram send = 0
```

---

# 24. Exact comparison bundle

Create exact message comparisons:

```text
ACTUAL_NATURAL_PRODUCTION_MESSAGE
REPAIRED_CURRENT_AI
FREE_ANALYST_NO_RESEARCH
FREE_ANALYST_WITH_RESEARCH
ADAPTIVE_SELECTED
DETERMINISTIC_REFERENCE
```

Mark non-production variants:

`REPLAY / SHADOW — NOT SENT`

---

# 25. Human quality check

For all 14 Adaptive messages review:

- clearer than current production?
- preserves material caveats?
- no duplicated next-check / Unknown?
- no excessive number recitation?
- research attribution adds value only where material?
- no forced "why" story on quiet names?
- direct/hybrid/minimal selection reasonable?

Classify:
- MATERIAL_IMPROVEMENT
- NO_MEANINGFUL_CHANGE
- WORSE

Any `WORSE` due factual/causal boundary = P1/P0 depending severity.

---

# Track D — Promotion policy

# 26. Production promotion scope

This task may promote **only Track A**.

Allowed production diff:

```text
directional relation semantic/provenance compatibility repair
+ directly required tests/docs
```

Forbidden production diff:

- Free Analyst
- Adaptive Renderer
- Open Research
- research trigger
- new production AI mode
- Trade AR

---

# 27. Track A promotion procedure

If Track A gates PASS:

1. full test suite
2. Ruff
3. `git diff --check`
4. Knowledge/Chart parity
5. Public Action/schema unchanged
6. implementation SHA GitHub Actions PASS
7. clean fast-forward or equally clean supported promotion
8. sync operating
9. restart API only if imported runtime code changed
10. `/health` PASS
11. final main SHA Actions PASS
12. worktrees clean

Set:

`US_AI_DIRECTIONAL_RELATION_REPAIR = DEPLOYED_PENDING_NATURAL`

Do not claim natural PASS for the repaired AI candidate until a later natural US run exercises it.

---

# 28. Track B state after repair

Even if 14/14 shadow replay passes:

```text
FREE_ANALYST_US_NATURAL_ADAPTER =
PASS_SHADOW

FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE =
YES_PENDING_SEPARATE_INTEGRATION
```

Do not merge Track B into production.

---

# 29. Open Research state after repair

If research remains safe:

```text
OPEN_RESEARCH_US_HOLDOUT =
PASS_SHADOW

OPEN_RESEARCH_PRODUCTION_CANDIDATE =
YES_PENDING_SEPARATE_SELECTIVE_INTEGRATION
```

No production integration in this task.

---

# 30. Required focused tests — Track A

Add tests for:

- signed negative gap → lower
- signed positive gap → higher
- abs-only gap cannot validate lower/higher
- wrong sign rejected
- wrong comparator rejected
- wrong relation ID rejected
- Inventory vs COGS
- Inventory vs Revenue
- no Trade AR leak
- current-price RR regression
- FCF period regression

---

# 31. Required focused tests — Track B

Add tests for:

- natural production packet normalization
- 14-message fixture compatibility
- enum normalization
- evidence-ref normalization
- research-sidecar merge
- macro temporal-role preservation
- thesis/expectation/valuation preservation
- no hidden arithmetic
- no external knowledge
- dangling ref rejection
- no-research value message
- Adaptive Direct/Hybrid/Minimal compatibility
- production isolation

---

# 32. Full validation

Required:

```text
focused Track A PASS
focused Track B PASS
combined replay PASS
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action 0.4.5 unchanged
operationId 20/20 unique
schema 4 unchanged
GitHub Actions PASS
```

Report exact counts.

---

# 33. Required architecture docs

Create/update:

1. `docs/architecture/WORKING_CAPITAL_RELATION_SEMANTICS.md`
   - signed vs absolute gap
   - directional wording ownership

2. `docs/architecture/FREE_ANALYST_NATURAL_PACKET_ADAPTER.md`
   - production packet → common shadow schema
   - ref namespace normalization

3. if needed:
   `docs/architecture/OPEN_RESEARCH_FREE_ANALYST_INTEGRATION.md`
   - clarify sidecar preservation across natural packet adapter

Do not document shadow features as production-enabled.

---

# 34. Required reports

Create:

1. `docs/reports/20260825-us-ai-directional-binding-root-cause.md`
2. `docs/reports/20260825-us-ai-directional-binding-repair.md`
3. `docs/reports/20260825-us-ai-directional-binding-negative-controls.md`
4. `docs/reports/20260825-us-ai-compatibility-post-repair-replay.md`
5. `docs/reports/20260825-free-analyst-us-natural-adapter-root-cause.md`
6. `docs/reports/20260825-free-analyst-us-natural-adapter-repair.md`
7. `docs/reports/20260825-free-analyst-us-natural-adapter-ref-audit.md`
8. `docs/reports/20260825-free-analyst-us-natural-14-message-replay.md`
9. `docs/reports/20260825-open-research-sidecar-preservation.md`
10. `docs/reports/20260825-adaptive-renderer-14-message-replay.md`
11. `docs/reports/20260825-us-ai-free-analyst-combined-replay.md`
12. `docs/reports/20260825-us-ai-free-analyst-message-comparison.md`
13. `docs/reports/20260825-us-ai-free-analyst-repair-readiness.md`
14. `docs/reports/20260825-us-ai-free-analyst-artifact-index.md`

Recommended JSON:

`docs/reports/20260825-us-ai-free-analyst-repair-readiness.json`

---

# 35. Mandatory ZIP

Create:

`20260825-us-ai-directional-binding-and-free-analyst-adapter-repair-bundle.zip`

Include all sanitized reports, exact message comparisons, readiness JSON, and artifact index.

Compute/report SHA-256.

---

# 36. Readiness gates

Set exactly:

```text
US_AI_DIRECTIONAL_RELATION_REPAIR =
PASS / FAIL

US_AI_COMPATIBILITY_REPLAY =
PASS / FAIL

FREE_ANALYST_US_NATURAL_ADAPTER =
PASS_SHADOW / FAIL

FREE_ANALYST_US_14_MESSAGE_REPLAY =
PASS / FAIL

OPEN_RESEARCH_SIDECAR_PRESERVATION =
PASS / FAIL

ADAPTIVE_RENDERER_US_14_MESSAGE_REPLAY =
PASS / FAIL

COMBINED_US_MORNING_REPLAY =
PASS / FAIL

FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE =
YES_PENDING_SEPARATE_INTEGRATION / NO

OPEN_RESEARCH_PRODUCTION_CANDIDATE =
YES_PENDING_SEPARATE_SELECTIVE_INTEGRATION / NO
```

---

# 37. P1 closure rule

The two triggering material P1s may be closed only if:

## P1-A closed

```text
directional prose uses direction-compatible relation
hard errors = 0
validator remains strict
immutable replay PASS
```

## P1-B closed

```text
Free Analyst natural packet adapter = 14/14 PASS
research sidecar preserved
no unsupported refs/claims
Adaptive replay PASS
```

Then:

```text
OPEN_MATERIAL_P1 = 0
```

---

# 38. Severity

## P0

- wrong user-visible number/fact
- wrong relation direction
- Trade AR leak
- temporal violation
- production DB/Telegram mutation from replay
- unsourced external claim
- hidden arithmetic accepted
- Open Research source/entity/time corruption

## P1

- directional relation still binds to abs field
- validator weakened to accept ambiguous direction
- Free Analyst adapter still falls back materially
- research sidecar provenance lost
- material information loss in Adaptive Renderer
- production AI/fallback factual mismatch

## P2

- harmless prose-quality issue
- some research messages choose Minimal
- renderer preference difference
- previous automation-registration tooling issue
- minor report formatting

---

# 39. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...

TRACK_A_BRANCH = ...
TRACK_A_BASE = ...
TRACK_A_IMPLEMENTATION = ...
TRACK_A_FINAL_MAIN = ...
TRACK_A_OPERATING = ...

TRACK_B_BRANCH = ...
TRACK_B_BASE = ...
TRACK_B_IMPLEMENTATION = ...
TRACK_B_REPORT_COMMIT = ...

TRIGGERING_NATURAL_PACKET = ...

PRE_REPAIR_AI_HARD_ERRORS = ...
POST_REPAIR_AI_HARD_ERRORS = 0

US_AI_DIRECTIONAL_RELATION_REPAIR = ...
US_AI_COMPATIBILITY_REPLAY = ...

FREE_ANALYST_US_NATURAL_ADAPTER = ...
FREE_ANALYST_US_14_MESSAGE_REPLAY = ...
FREE_ANALYST_VALIDATED = 14
FREE_ANALYST_FALLBACK = 0

OPEN_RESEARCH_SIDECAR_PRESERVATION = ...
ADAPTIVE_RENDERER_US_14_MESSAGE_REPLAY = ...
COMBINED_US_MORNING_REPLAY = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
TRADE_AR_LEAK = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0

FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE = ...
OPEN_RESEARCH_PRODUCTION_CANDIDATE = ...

PRODUCTION_PROMOTION_TRACK_A = ...
FREE_ANALYST_PRODUCTION_PROMOTION = 0
OPEN_RESEARCH_PRODUCTION_PROMOTION = 0

PRODUCTION_MUTATION_FROM_REPLAY = 0
TELEGRAM_SEND = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...

ZIP = ...
ZIP_SHA256 = ...
```

---

# 40. NEXT_ACTION

If all gates pass:

```text
NEXT_ACTION =
FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION
```

with Open Research selective integration remaining the next separate stage.

If Track A passes but Track B fails:

```text
NEXT_ACTION =
FREE_ANALYST_US_ADAPTER_BOUNDED_REPAIR
```

If Track B passes but Track A fails:

```text
NEXT_ACTION =
US_AI_DIRECTIONAL_BINDING_BOUNDED_REPAIR
```

Do not combine broader feature work into the repair.

---

# 41. Final principle

These are two narrow compatibility defects, not architecture failures.

Track A target:

```text
directional statement
→ directional relation provenance
```

not:

```text
make validator permissive
```

Track B target:

```text
natural production packet
→ canonical Free Analyst shadow schema
```

not:

```text
fork Free Analyst for US
```

The desired end state is:

```text
current production AI compatibility repaired
+
Free Analyst consumes the exact natural US packet
+
Open Research sidecar remains intact
+
Adaptive Renderer works 14/14
+
zero safety regression
```

Only the current production compatibility repair may enter main in this task.

Free Analyst / Adaptive / Open Research remain separate production-integration candidates.
