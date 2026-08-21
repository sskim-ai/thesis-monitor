# thesis-monitor — Phase 9.1E Work Instruction

## Metadata

- Phase: `9.1E`
- Title: `Selective Working-Capital User-Visible Pre-Integration Architecture`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating:
  `af89324ad865a7f1cf6fdc5599db335629649cca`
- Dependency:
  - Phase 9.1A COMPLETE
  - Phase 9.1B COMPLETE
  - Phase 9.1C COMPLETE
  - Phase 9.1D `DEPLOYED_PENDING_NATURAL`
- 9.1D approved metric scope:
  - Inventory
  - exact Trade AR
- Phase 9.1D natural proof at instruction time:
  - Inventory: not yet proven naturally
  - exact Trade AR: not yet proven naturally
- Current 9.0E cash-flow user-visible mode:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`
- Feature state during this phase:
  `WORKING_CAPITAL_USER_VISIBLE = OFF`
- User-visible working-capital diff during implementation:
  `0`
- Goal:
  build all pre-integration contracts/validators/parity/preview/kill-switch plumbing now, but prohibit enablement until natural proof gates are satisfied.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260821-phase-9-1e-working-capital-user-visible-preintegration.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify latest safe main/operating.
3. Commit/push this instruction as a docs-only instruction commit.
4. Record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
5. Create the implementation branch from latest safe main.
6. If the KR investor-flow repair lands first, reconcile explicitly onto latest main before promotion.
7. No force push / history rewrite.
8. Do not silently edit this instruction after implementation begins.

Recommended branch:

`codex/phase-9-1e-working-capital-user-visible-preintegration`

The two parallel workstreams must remain independent.

---

# 1. Phase purpose

Phase 9.1D proves the selected working-capital reasoning on natural runtime packets.

Phase 9.1E should prepare the **user-visible integration architecture** in advance so that after natural proof the system does not need another large design phase.

This phase implements:

```text
canonical 9.1B facts
        ↓
9.1C selector
        ↓
9.1D runtime-canary contract
        ↓
user-visible eligibility contract
        ↓
numeric ownership
        ↓
AI/fallback parity
        ↓
semantic/causal validation
        ↓
message preview
        ↓
feature mode / kill switch
```

But keeps the feature OFF.

---

# 2. Natural-proof gate is hard

Do not enable working-capital user-visible integration in this task.

Required future enablement evidence:

```text
Inventory natural proof = LIVE_PASS
for any rollout including Inventory

Exact Trade AR natural proof = LIVE_PASS
for any rollout including exact Trade AR
```

A metric family that remains `NOT_OBSERVED` cannot be user-visible enabled.

If Inventory passes naturally before Trade AR:
a later rollout may choose Inventory-only.

Do not assume both must launch together.

---

# 3. Initial candidate metric families

Architect only:

- `inventory`
- exact `trade_accounts_receivable`

Do NOT prepare broad AR/AP for initial enablement beyond rejecting them cleanly.

Excluded:

- broad AR
- trade AP
- broad AP
- DSO
- Inventory Days
- DPO
- CCC
- contract assets
- accrued liabilities
- working-capital score

---

# 4. Proposed feature mode

Implement/reuse a safe feature-mode mechanism.

Suggested:

```text
OFF
SELECTIVE_INVENTORY
SELECTIVE_EXACT_TRADE_AR
SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
```

If the repo already has a better generic feature flag model, use that.

Critical:

- default/missing/invalid → `OFF`
- deployment in this phase ends with `OFF`
- no natural-proof state → cannot switch ON through normal operator path
- kill switch OFF must immediately stop future working-capital enrichment

---

# 5. Enablement prerequisite contract

Implement a machine-readable gate, suggested:

`working-capital-user-visible-enable-gate-v1`

Fields:

```text
metric_family
natural_proof_state
canonical_core_state
shadow_consumption_state
runtime_canary_state
open_p0
open_material_p1
semantic_validation_state
causal_guard_state
numeric_binding_state
eligible_for_enablement
blocking_reasons
```

The feature config must not bypass this gate accidentally.

---

# 6. Natural-proof source of truth

Do not manually mark proof in renderer code.

Use Phase 9.1D natural-canary evidence/receipt state.

Proof must be:

- packet-linked
- Fact-linked
- PIT-safe
- semantic-safe
- causal-safe
- production influence = 0

No manual "we saw it once" boolean without evidence reference.

---

# 7. User-visible contract

Implement a versioned contract, suggested:

`working-capital-user-visible-v1`

Conceptual fields:

```text
ticker
packet_id
assessment_date
cutoff

feature_mode

metric_family
semantic_scope
balance_date
currentness
pit_state

selected_relation
selected_fact_ids
industry_applicability
materiality_reason

display_reason
numeric_owner
resolved_unknowns

allowed_claims
prohibited_claims

ai_enabled
fallback_enabled
user_visible_enabled
enablement_gate_ref
```

This contract is generated in preview/test mode while feature OFF.

---

# 8. Eligibility

A ticker can become user-visible eligible only if:

1. metric family enabled by feature mode
2. metric family natural-proof gate PASS
3. canonical 9.1B fact/relation eligible
4. PIT safe
5. latest-formal currentness safe
6. exact semantic scope
7. 9.1C materiality selector selects it
8. 9.1D canary-compatible context
9. industry applicability permits
10. no relevant quality taint
11. semantic/causal validator can support safe wording
12. no stronger existing insight makes it redundant

During this phase:
`user_visible_enabled = false`
for all production runs because feature mode remains OFF.

---

# 9. No ticker hard-coding

No production allowlist.

Tickers may appear in tests/previews.

Eligibility is dynamic.

---

# 10. Numeric owner

Working-capital exact numbers belong to:

`business_earnings` / earnings-quality context.

Do not repeat the same exact working-capital number in:

- core judgment
- valuation
- price
- observer
- holder
- warnings
- next checks

Other sections may reference meaning without exact duplicate numeric value.

---

# 11. Message placement

Do not create a mandatory standalone working-capital section for every ticker.

Preferred:

- one concise sentence inside business/earnings-quality
or
- one optional compact working-capital line only when selected

The preview must compare both if current renderer architecture makes the choice non-obvious.

Choose the lower-noise placement.

---

# 12. One primary relation

Default user-visible working-capital content:

- one primary relation
- optionally one exact number

Do not dump:

- current balance
- prior balance
- YoY
- revenue YoY
- COGS YoY
- gap pp

all together.

The relation is more important than the tuple.

---

# 13. Inventory wording

Allowed if exact canonical total Inventory.

Possible concise concepts:

- `재고 증가율이 매출 증가율을 웃돌았다`
- `재고 증가율이 매출 증가율보다 낮았다`
- equivalent natural phrasing

Do not say:

- excess inventory confirmed
- demand collapse
- inventory days
- finished-goods buildup

without evidence.

---

# 14. Exact Trade AR wording

Allowed only for exact `trade_accounts_receivable`.

Possible concept:

- `매출채권 증가율이 매출 증가율을 웃돌아 회수 흐름을 확인할 필요가 있다`

Do not say:

- customers are not paying
- DSO worsened
- broad receivables if exact scope differs

No broad AR substitution.

---

# 15. Causal guard

User-visible validator must reject unsupported causal statements.

Inventory relation alone cannot prove:

- weak demand
- oversupply
- poor execution

Trade AR relation alone cannot prove:

- deteriorating collections
- customer stress
- channel stuffing

Use cautious follow-up language unless stronger evidence exists.

---

# 16. Industry-specific interpretation

## Memory / semiconductor
Inventory relation should be interpreted with:
- ASP
- mix
- cycle
- supply discipline
when available.

## Automotive
Inventory relation with:
- deliveries
- incentives
- mix

## Steel/materials
Inventory with:
- cycle/pricing/raw materials

## Industrial / electrical equipment
Trade AR may be more useful for order-to-cash monitoring.

## Transport/logistics
Trade AR can matter selectively.

## HPC
Working capital remains secondary to CAPEX/financing unless material.

## Biotech
Usually suppress working-capital user-visible context.

## Insurance
N/A.

Do not force a metric because it exists.

---

# 17. Interaction with Phase 9.0E cash flow

Cash flow is already user-visible selectively.

Avoid stacking:

```text
FCF sentence
+
working-capital sentence
```

unless working capital materially clarifies the FCF/earnings-quality question.

Implement an insight-priority rule.

Possible result:

- cash flow wins
- working capital wins
- one combined cautious sentence
- both suppressed if redundant

Do not create two number-heavy sections.

---

# 18. Combined cash-flow / working-capital sentence

If both are compatible and material:

AI/fallback may later use one integrated interpretation.

Example concept:

`현금흐름이 약한 가운데 매출채권 증가가 매출보다 빨라 운전자본 전환을 확인할 필요가 있습니다.`

But:

- periods must be compatible
- no causal claim
- exact working-capital semantic preserved
- no AI arithmetic
- FCF remains canonical 9.0 fact

Preview only in this phase.

---

# 19. Unknown resolution

If exact Trade AR becomes known:

remove/narrow same-scope unknown.

If only Inventory becomes known:
do not imply receivables are known.

If broad AR exists but exact Trade AR does not:
exact Trade AR unknown remains.

Feature OFF:
production Unknown behavior must remain unchanged in this phase.

Preview should show future replacement behavior.

---

# 20. AI packet preview

Build preview-only structured user-visible context.

Do not inject it into production AI while feature OFF.

AI preview input may include:

- selected relation
- Fact IDs
- balance date
- period relation
- semantic scope
- materiality
- industry context
- allowed/prohibited claims
- compatible cash-flow relation

No raw provider rows.

---

# 21. AI behavior

AI must not:

- calculate YoY/gap
- calculate DSO/CCC
- infer cause
- change investment-logic state from working capital alone
- change valuation context
- invent missing exact Trade AR from broad AR

All numbers come from canonical relations.

---

# 22. Deterministic fallback

Build a deterministic fallback preview using the same `working-capital-user-visible-v1` contract.

AI/fallback parity required for:

- ticker selection
- metric family
- Fact IDs
- balance date
- semantic scope
- relation direction
- currentness
- Unknown suppression
- causal constraints

Prose need not be identical.

---

# 23. Preview-only parity key

Add an audit key such as:

`working_capital_user_visible_context_id`

The same context ID should be visible in AI/fallback preview artifacts.

No production receipt dependency while feature OFF.

---

# 24. Feature OFF behavior

Hard regression:

with feature mode OFF:

```text
production AI input diff = 0
production fallback diff = 0
Telegram diff = 0
Public Action diff = 0
snapshot diff = 0
assessment DB diff = 0
warning lifecycle diff = 0
```

The architecture may produce shadow/preview artifacts only.

---

# 25. Kill switch

Document/implement user-visible working-capital kill switch now.

When OFF:

- no working-capital production enrichment
- canonical 9.1B facts remain
- 9.1C shadow remains
- 9.1D runtime canary remains
- Phase 9.0E cash flow remains independent

Invalid config → OFF.

---

# 26. Enablement command safety

If there is an operator config command/process:

it must verify metric-family natural proof before accepting ON.

If repo configuration is file/env based:
provide a preflight validator that fails enablement when proof is missing.

Do not implement a remote control system solely for this.

---

# 27. Preview replay set

Use immutable:

- recent US natural packet(s), including classes that selected Inventory in 9.1C
- recent KR natural packet(s), including exact Trade AR classes

This phase is allowed to generate previews even though natural 9.1D proof is pending.

But clearly mark:

`PREVIEW_ONLY_NOT_ENABLEMENT_EVIDENCE`

Do not rewrite original archives.

---

# 28. Required preview classes

Inventory:
- memory/semiconductor
- automotive or industrial if naturally available

Exact Trade AR:
- KR industrial / logistics examples if canonical

Negative controls:
- broad AR only
- AP only
- insurance
- biotech low materiality
- stale
- lagging provisional
- missing natural proof

---

# 29. Natural-proof-gate negative tests

Required:

- Inventory proof NOT_OBSERVED + mode request Inventory → blocked
- Trade AR proof NOT_OBSERVED + mode request Trade AR → blocked
- Inventory LIVE_PASS + Trade AR NOT_OBSERVED → Inventory-only may be eligible
- both LIVE_PASS → combined mode may be eligible
- natural FAIL → corresponding family blocked
- open P0 → all enablement blocked

---

# 30. Numeric validation

Exact displayed preview numbers:

- automatic binding
- correct Fact/relation
- correct currency/unit
- correct period
- correct semantic scope

Targets:

```text
manual = 0
rejected = 0
unresolved = 0
```

---

# 31. Semantic validation

Reject preview claims:

- broad AR as exact Trade AR
- contract assets as Trade AR
- inventory component as total
- wrong period
- stale as current
- DSO
- Inventory Days
- DPO
- CCC
- working-capital cause overclaim
- working-capital-only valuation change
- working-capital-only status change

---

# 32. Runtime quality preview

Reject:

- portfolio boilerplate
- numeric tuple dumping
- duplicate exact number
- generic "핵심 숫자는"
- working-capital paragraph on every ticker
- repetitive causal disclaimers

Prefer replacing an existing generic Unknown/next-check when useful.

---

# 33. Message-length audit

Report full before/after previews.

No arbitrary percentage blocker.

Classify:
- materially clearer
- minor improvement
- no change
- degraded

Any materially degraded class must be excluded from future rollout or repaired before enablement.

---

# 34. Materiality selector parity

The user-visible preview selector must not diverge materially from:

- 9.1C retrospective selector
- 9.1D runtime-canary selector

Same packet/facts should produce same selected metric family unless a documented user-visible redundancy rule suppresses it.

Any difference requires explicit reason.

---

# 35. User-visible redundancy rule

A user-visible selector may suppress an otherwise canary-selected relation when:

- Phase 9.0E cash flow already communicates the same decision-relevant point
- price/valuation message is already dense and WC adds no incremental value
- working-capital relation resolves no Unknown and adds no monitoring value

This is allowed only as a suppression, not as broader selection.

---

# 36. No enablement in this task

Even if all previews pass:

end state remains:

```text
WORKING_CAPITAL_USER_VISIBLE = OFF
```

Do not switch to selective mode.

Do not manually send preview messages.

---

# 37. 9.1D natural proof remains independent

The next natural US/KR runs should continue to produce 9.1D canary evidence.

Do not make the canary depend on 9.1E preview contracts.

9.1E may consume canary receipts for future gate decisions, but not vice versa.

---

# 38. Interaction with night-futures telemetry

No code/config interaction.

If the parallel night-futures telemetry repair lands first:
reconcile onto latest main before promotion.

No shared behavior assumptions.

---

# 39. Interaction with KR investor-flow repair

No coupling.

Investor-flow repair affects supply/positioning wording.

9.1E affects working-capital preview architecture only.

If investor-flow branch lands first:
reconcile cleanly.

Do not combine both user-facing concepts in one new renderer refactor.

---

# 40. Tests — feature modes

Required:

- missing config → OFF
- invalid config → OFF
- OFF → zero production diff
- Inventory requested without proof → blocked
- Trade AR requested without proof → blocked
- eligible proof states accepted by preflight
- kill switch OFF suppresses future enrichment

No actual production ON during this phase.

---

# 41. Tests — Inventory

Required:

- exact total Inventory
- safe YoY/relation
- material selected
- low materiality suppressed
- component rejected
- industry context
- causal guard
- cash-flow redundancy suppression

---

# 42. Tests — exact Trade AR

Required:

- exact Trade AR
- AR vs Revenue
- broad AR negative control
- contract asset negative control
- causal guard
- exact Unknown resolution
- broad-only Unknown not falsely resolved

---

# 43. Tests — AI/fallback parity

For same preview context:

- selected ticker
- metric family
- Fact IDs
- relation ID
- balance date
- semantic scope
- direction
- numeric value
- suppression reason
- Unknown resolution

mismatch target = `0`.

---

# 44. Tests — 9.0E coexistence

Required:

- FCF-only selected
- WC-only preview selected
- both material, WC redundant → suppress WC
- both material, combined context useful
- incompatible periods → no combination
- no FCF recomputation
- existing production cash-flow output unchanged

---

# 45. Regression

Preserve:

- Phase 9.0E
- Phase 9.1A/B/C/D
- 9.0D canary
- 9.0D.1 baseline consistency
- run-31 KR
- run-30 US
- valuation
- price/RR
- supply
- exactly-once
- KRX
- night futures

---

# 46. Full validation

Required:

- focused 9.1E tests PASS
- natural-proof gate tests PASS
- feature OFF regression PASS
- AI/fallback preview parity PASS
- numeric/semantic/causal PASS
- runtime quality PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions PASS
- exact final/main SHA Actions PASS after promotion

---

# 47. Promotion

Because user-visible feature remains OFF, 9.1E pre-integration architecture may be promoted after deterministic validation without waiting for natural proof.

Promotion requires:

- P0 = 0
- material P1 = 0
- production/user-visible diff = 0
- enablement gate cannot be bypassed
- feature OFF confirmed
- CI PASS
- main ancestry clean

Do not promote during protected natural execution windows.

---

# 48. Required architecture doc

Create:

`docs/architecture/WORKING_CAPITAL_USER_VISIBLE_PREINTEGRATION.md`

Include:

- feature modes
- natural-proof gate
- user-visible contract
- numeric ownership
- placement
- cash-flow coexistence
- AI/fallback parity
- semantic/causal validation
- kill switch
- future enablement procedure

---

# 49. Required reports

Create:

1. `docs/reports/20260821-phase9-1e-implementation.md`
2. `docs/reports/20260821-phase9-1e-natural-proof-gate.md`
3. `docs/reports/20260821-phase9-1e-selector-parity.md`
4. `docs/reports/20260821-phase9-1e-ai-fallback-preview.md`
5. `docs/reports/20260821-phase9-1e-before-after-preview.md`
6. `docs/reports/20260821-phase9-1e-numeric-semantic-validation.md`
7. `docs/reports/20260821-phase9-1e-feature-off-regression.md`
8. `docs/reports/20260821-phase9-1e-kill-switch.md`
9. `docs/reports/20260821-phase9-1e-readiness.md`

Recommended JSON:

`docs/reports/20260821-phase9-1e-readiness.json`

---

# 50. Complete bundle

Create:

`20260821-phase9-1e-preintegration-complete-report-bundle.zip`

Include sanitized reports/JSON.

Report SHA-256.

---

# 51. Completion report — repository

Report:

- instruction commit
- branch
- base
- implementation
- final
- previous/final main
- operating
- promotion
- worktrees
- deviations

---

# 52. Completion report — feature state

Report:

```text
WORKING_CAPITAL_USER_VISIBLE_MODE = OFF
INVENTORY_NATURAL_PROOF = ...
TRADE_AR_NATURAL_PROOF = ...
```

No ON state permitted in this task.

---

# 53. Completion report — previews

Report:

- Inventory preview selected count
- exact Trade AR preview selected count
- broad AR selected = 0
- AP selected = 0
- AI/fallback mismatches
- numeric binding
- causal/semantic errors
- human quality classification
- message length change

---

# 54. Completion report — natural-proof gate

Report each family:

```text
metric_family
proof_state
enablement_eligible
blocking_reason
evidence_ref
```

At instruction time, both should remain blocked pending natural proof unless natural evidence arrives legitimately during implementation.

Do not manufacture proof with manual runs.

---

# 55. Completion report — production safety

Report:

- production AI diff
- fallback diff
- Telegram diff
- Public Action diff
- snapshot diff
- DB mutation
- warning mutation
- manual tasks
- Production Assist

Targets all user/runtime mutation `0`.

---

# 56. Final gate

Set:

```text
PHASE_9_1E_PREINTEGRATION_READY = YES/NO
```

If YES, also report:

```text
INVENTORY_USER_VISIBLE_ENABLEMENT_READY =
YES / NO_PENDING_NATURAL / NO_OTHER_BLOCKER

TRADE_AR_USER_VISIBLE_ENABLEMENT_READY =
YES / NO_PENDING_NATURAL / NO_OTHER_BLOCKER
```

But do not enable.

---

# 57. Next natural review

After the next natural morning/afternoon runs:

review:

- Inventory natural proof
- exact Trade AR natural proof
- 9.1D canary receipt
- production influence
- semantic/causal validation

If a metric family reaches LIVE_PASS and 9.1E pre-integration is otherwise clean, a later **small enablement-only instruction** may turn on only that proven family.

No new architecture phase should be necessary.

---

# 58. P0 / P1 / P2

## P0
- feature accidentally becomes user-visible
- natural-proof gate bypass
- wrong Fact/period/semantic
- causal overclaim passes validator
- broad AR exposed as Trade AR
- production behavior changes under OFF

## P1
- selector materially diverges from 9.1C/D
- AI/fallback fact parity mismatch
- cash-flow coexistence creates contradictory user meaning
- kill switch fails

## P2
- wording polish
- exact placement preference
- broad AR/AP remains excluded
- minor length difference

P2 does not block pre-integration completion.

---

# 59. Final philosophy

Phase 9.1E should eliminate future integration engineering risk without prematurely exposing working-capital reasoning.

The correct order is:

```text
canonical facts
→ retrospective value-add
→ natural runtime canary
→ pre-integration architecture
→ natural proof
→ tiny enablement-only change
```

Do not reverse the last two steps.

A clean preview is not natural proof.

A passing natural canary is not permission to expose a metric family that the user-visible validator/placement architecture cannot handle.

This phase succeeds when:

- everything needed for user-visible integration is implemented and tested,
- feature OFF produces exactly zero production diff,
- natural-proof gates are machine-readable and non-bypassable,
- Inventory and exact Trade AR can be enabled independently later,
- AI and fallback will use the same canonical facts,
- causal overclaim remains blocked,
- Phase 9.0E cash-flow context is not duplicated.

At completion, the only missing step should be evidence—not architecture.
