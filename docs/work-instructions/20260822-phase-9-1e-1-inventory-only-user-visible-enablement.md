# thesis-monitor — Phase 9.1E.1 Work Instruction

## Metadata

- Phase: `9.1E.1`
- Title: `Inventory-Only User-Visible Enablement`
- Instruction version: `1.0`
- Date: `2026-08-22 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating:
  `fb445104f491a57ea67f435eab37426b0acd0c63`
- Phase 9.1D:
  `DEPLOYED_PENDING_NATURAL`
- Phase 9.1D Inventory natural proof:
  `LIVE_PASS`
- Phase 9.1D exact Trade AR natural proof:
  `NOT_OBSERVED`
- Phase 9.1E pre-integration:
  `READY`
- Current working-capital user-visible mode:
  `OFF`
- Current Phase 9.0E cash-flow mode:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- US AI compatibility repair:
  `PASS`
- US AI compatibility natural proof:
  `PENDING`
- XKRX role-target repair:
  `PASS / DEPLOYED_PENDING_NATURAL`
- Night-futures deadline:
  `DEADLINE_UNPROVEN`
- Production Assist:
  `OFF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`
- Runtime policy:
  `daily-review-v3.10`
- Goal:
  enable **Inventory only** for selective user-visible working-capital reasoning, while exact Trade AR and all broader working-capital families remain OFF.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260822-phase-9-1e-1-inventory-only-user-visible-enablement.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify latest safe main/operating SHA
2. verify Phase 9.1E pre-integration artifacts/contracts are present
3. verify Inventory natural proof state is `LIVE_PASS`
4. verify exact Trade AR natural proof remains `NOT_OBSERVED`
5. commit/push this instruction as a docs-only instruction commit
6. record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
7. create implementation branch from latest safe main descendant containing the instruction commit
8. no force push / history rewrite
9. no silent edit after implementation begins

Recommended branch:

`codex/phase-9-1e-1-inventory-only-user-visible-enablement`

---

# 1. Phase purpose

All architecture for selective working-capital user-visible integration already exists.

This phase is intentionally small.

The only user-visible change allowed is:

```text
Inventory natural-proof-gated context
        ↓
existing Phase 9.1E user-visible contract
        ↓
AI + deterministic fallback
        ↓
selective user-visible Inventory reasoning
```

Exact Trade AR must remain OFF.

Do not redesign Phase 9.1 architecture.

---

# 2. Hard enablement boundary

ENABLE:

- canonical total `inventory`
- Inventory YoY relation
- Inventory vs Revenue relation
- Inventory vs exact COGS relation
- only when existing 9.1C/9.1D materiality chooses it
- only when natural proof gate is satisfied

KEEP OFF:

- exact Trade AR
- broad AR
- exact Trade AP
- broad AP
- contract assets
- accrued liabilities
- DSO
- Inventory Days
- DPO
- CCC
- working-capital score

---

# 3. No ticker allowlist

Do not implement:

```python
if ticker in {"000660", "005930", ...}
```

Inventory user-visible eligibility must remain dynamic.

The following may appear only in tests/reports as evidence classes:
- memory/semiconductor
- automotive
- steel/materials
- industrial

Production selection is contract-driven.

---

# 4. Natural-proof gate

The Inventory family may be enabled only because:

`INVENTORY_NATURAL_PROOF = LIVE_PASS`

The exact Trade AR family must remain disabled because:

`TRADE_AR_NATURAL_PROOF = NOT_OBSERVED`

The implementation must enforce this at feature/preflight level.

Do not permit combined Inventory+Trade-AR mode.

---

# 5. Feature mode

Use the existing Phase 9.1E feature-mode mechanism.

Target operating mode after successful enablement:

`SELECTIVE_INVENTORY`

or exact repository-equivalent value.

Before activation:
mode remains `OFF`.

Invalid/missing config:
fail safe to `OFF`.

Do not create another independent feature flag if the existing pre-integration mechanism already supports metric-family modes.

---

# 6. Enablement preflight

Before operator/config activation, require machine-readable gate PASS:

```text
Inventory natural proof = LIVE_PASS
canonical core = PASS
shadow consumption = PASS
runtime canary = PASS
semantic validator = PASS
causal guard = PASS
numeric binding = PASS
AI/fallback parity = PASS
open P0 = 0
open material P1 = 0
```

The preflight must reject:
- Trade AR enablement
- combined mode
- broad AR/AP
- advanced ratios

---

# 7. User-visible contract reuse

Reuse:

`working-capital-user-visible-v1`

Do not create a new Inventory-specific user-visible contract unless necessary for compatibility.

Expected selected context:

```text
ticker
packet_id
assessment_date
feature_mode = SELECTIVE_INVENTORY

metric_family = inventory
semantic_scope = total_inventory
balance_date
pit_state
freshness_state

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
natural_proof_ref
```

---

# 8. Inventory semantic requirement

Only canonical **total Inventory** may become user-visible.

Do not expose:
- raw materials only
- finished goods only
- WIP only
- component aggregation
- contract assets
- other non-inventory balances

If total Inventory semantic is blocked:
no Inventory user-visible context.

---

# 9. PIT / freshness

Every user-visible Inventory relation must satisfy:

```text
source_available_at <= production packet cutoff
```

and currentness must be safe under existing formal-filing rules.

If:
`FORMAL_LAGGING_PROVISIONAL`

then follow existing 9.1C/9.1D suppression/context rule.

Do not call an old formal Inventory balance the current provisional quarter balance.

---

# 10. Materiality remains selective

Inventory natural proof does not mean every eligible Inventory fact is shown.

Use existing selector.

Display only when Inventory materially improves:
- earnings-quality reasoning
- inventory conversion monitoring
- cycle interpretation
- an existing Unknown
- a decision-relevant cash-flow relation

No new universal threshold.

---

# 11. One Inventory insight max by default

Default user-visible Inventory content:

- one primary Inventory relation
- optionally one exact numeric detail

Do not display:
- current Inventory
- prior Inventory
- YoY
- revenue YoY
- COGS YoY
- gap pp

as a full tuple.

Prefer relation meaning over data dump.

---

# 12. Numeric owner

Primary exact Inventory numeric owner:

`business_earnings` / earnings-quality context.

Do not duplicate exact Inventory numbers in:
- core judgment
- valuation
- price
- observer
- holder
- warnings
- next check

A next check may mention Inventory conceptually without repeating the exact number.

---

# 13. User-facing placement

Do not create a mandatory standalone `운전자본` section.

Preferred:
- one concise sentence inside existing business/earnings-quality reasoning
or
- one compact optional Inventory line only for selected tickers

Use the placement chosen/validated by Phase 9.1E preview.

Do not redesign the whole message renderer.

---

# 14. Inventory relation wording

Allowed concepts:

- Inventory growth exceeded Revenue growth
- Inventory growth lagged Revenue growth
- Inventory growth exceeded COGS growth
- Inventory growth lagged COGS growth
- Inventory increased/decreased on a safe comparable basis

Use natural Korean wording.

Do not expose internal relation enum names.

---

# 15. Causal guard

Inventory relation alone cannot assert:

- demand collapse
- oversupply confirmed
- excess inventory confirmed
- channel stuffing
- weak execution
- inventory quality deterioration

Allowed cautious interpretation:

- inventory conversion should be monitored
- relation is compatible with, but does not prove, a cycle/demand issue
- inventory build is worth checking against ASP/margin/sales context

Existing causal validator remains strict.

---

# 16. Industry-specific interpretation

## Memory / semiconductor
Inventory interpretation may use:
- ASP
- HBM/DRAM mix
- cycle
- supply discipline
when available.

Inventory rise alone is not negative.

## Automotive
Interpret with:
- delivery volume
- incentives
- mix

## Steel / materials
Interpret with:
- raw-material prices
- spreads
- cycle/demand

## Industrial
Inventory may matter for order conversion / production cadence.

## Cloud/software/HPC/biotech
Suppress unless materiality contract actually selects Inventory.

## Insurance
N/A.

---

# 17. Interaction with Phase 9.0E cash flow

Cash flow is already selectively user-visible.

Do not stack both automatically.

Apply the existing Phase 9.1E redundancy/priority rule.

Possible outcomes:

- cash flow wins → suppress Inventory
- Inventory wins → show Inventory
- both materially additive → one integrated cautious sentence
- both redundant → suppress one

Do not create two dense accounting blocks.

---

# 18. Compatible cash-flow combination

If Inventory and FCF are both selected and period-compatible:

a combined interpretation may be allowed.

Example concept:

`현금흐름이 약한 가운데 재고 증가가 매출보다 빨라 재고 전환을 확인할 필요가 있습니다.`

But:
- no causal claim
- no FCF recomputation
- exact period compatibility required
- one number owner
- no duplicate FCF number

---

# 19. Unknown resolution

If safe Inventory evidence resolves:
- inventory unavailable
- inventory trend unclear

replace/narrow that Unknown.

Do not resolve:
- Trade AR
- AP
- CCC
- DSO

Unknowns.

Inventory enablement is Inventory-only.

---

# 20. AI production path

After selective Inventory activation:

production AI may receive only the selected Inventory user-visible context.

Do not expose:
- broad AR/AP
- raw SEC/OpenDART rows
- unselected Inventory facts

AI must use supplied:
- relation
- fact IDs
- period/balance date
- semantic scope
- allowed/prohibited claims

No AI arithmetic.

---

# 21. Deterministic fallback path

Fallback must consume the same `working-capital-user-visible-v1` context.

Parity required for:

- selection
- Fact IDs
- relation ID
- balance date
- PIT/currentness
- semantic scope
- relation direction
- Unknown resolution
- suppression reasons

Prose may differ.

---

# 22. AI/fallback parity key

Use existing:

`working_capital_user_visible_context_id`

or repository-equivalent.

The same selected Inventory context must be identifiable in:
- AI candidate
- fallback candidate
- receipt/audit

No separate selector path.

---

# 23. Production AI compatibility repair regression

The recently completed US AI compatibility repair must remain PASS.

Verify:
- FCF period identity
- current-price RR Fact ownership
- validators
- no new hard errors caused by Inventory context

Do not loosen those validators.

---

# 24. User-visible receipt metadata

Add/reuse only minimum audit metadata:

```text
working_capital_user_visible_mode
working_capital_selected_count
working_capital_context_ids
working_capital_fact_ids
working_capital_metric_families
```

Do not dump raw facts into production receipts.

Preserve historical receipt compatibility.

---

# 25. Kill switch

Inventory user-visible must be instantly disableable through the existing Phase 9.1E OFF mode.

OFF must stop:
- future Inventory AI enrichment
- future Inventory fallback enrichment

OFF must NOT stop:
- 9.1B canonical facts
- 9.1C shadow consumption
- 9.1D runtime canary
- Phase 9.0E cash-flow feature

Invalid config → OFF.

---

# 26. Feature-OFF regression

Before enablement, prove:

```text
mode = OFF
→ production output equals current safe baseline
```

Inventory user-visible diff:
`0`

9.1D canary remains active.

---

# 27. Inventory-ON replay preview

Before operating activation, replay immutable recent US and KR packets with:

`SELECTIVE_INVENTORY`

Generate full message previews for:
- AI path
- fallback path

Include:
- selected subjects
- suppressed subjects
- exact context IDs
- Fact IDs
- full before/after message
- length delta
- Unknown changes
- FCF redundancy handling

Do not modify original archives.

---

# 28. Mandatory positive controls

Use naturally supported replay classes:

- memory/semiconductor Inventory
- automotive Inventory if available
- materials/industrial Inventory if available

No hard-coded production selection.

---

# 29. Mandatory negative controls

Required:

- exact Trade AR-only case → no user-visible WC
- broad AR-only case → no user-visible WC
- AP-only case → no user-visible WC
- insurance → N/A
- stale Inventory → suppressed
- formal-lagging-provisional → suppressed/context-only
- low-materiality Inventory → suppressed
- feature OFF → suppressed
- missing natural-proof ref → enablement rejected

---

# 30. No Trade AR leakage

Hard target:

```text
Trade AR user-visible selected count = 0
Broad AR selected count = 0
AP selected count = 0
```

If any Trade AR wording appears due to existing baseline message, distinguish baseline text from new 9.1E.1 enrichment.

Do not introduce new Trade AR enrichment.

---

# 31. Numeric validation

Every exact Inventory numeric claim must:
- bind automatically
- use canonical Fact/relation
- preserve units/currency
- preserve balance date/comparison period

Targets:

```text
manual = 0
rejected = 0
unresolved = 0
```

No AI subtraction.

---

# 32. Semantic validation

Reject:

- Inventory component as total
- stale as current
- wrong balance date
- wrong comparable period
- Inventory Days
- CCC
- demand collapse claim without evidence
- FCF causal overclaim
- working-capital-only valuation change
- working-capital-only investment-logic state change

---

# 33. Runtime quality

Prevent:
- Inventory boilerplate across many tickers
- numeric tuple dumps
- repeated exact Inventory number
- generic `재고가 중요합니다`
- repetitive causal disclaimers

Selected Inventory prose must be company/industry specific.

---

# 34. Message-length discipline

Report before/after lengths.

No arbitrary blocker threshold.

Classify:
- MATERIAL_IMPROVEMENT
- MINOR_IMPROVEMENT
- NO_MEANINGFUL_CHANGE
- DEGRADED

Any degraded selected message is a material enablement blocker unless safely suppressed.

---

# 35. Production safety

Must preserve:
- exactly-once
- message count
- receipts
- AI/fallback fallback semantics
- Phase 9.0E FCF behavior
- price/RR
- valuation
- supply
- KRX telemetry
- night-futures telemetry
- investor-flow repair

---

# 36. No state mutation from Inventory alone

Inventory user-visible evidence must not automatically:
- strengthen investment logic
- weaken investment logic
- invalidate
- open/close warning
- alter valuation context

Any existing status delta must still satisfy broader evidence contracts.

---

# 37. Deployment timing — today’s KR window

Current instruction time is before the 2026-08-22 KR natural cycle.

Protected schedule:
- KRX 16:05
- KR primary 16:15
- KR backup 16:55

Recommended freeze:
`15:50–17:05 KST`

If implementation + validation + promotion + activation are fully complete before the freeze:
Inventory-only mode may be activated and the natural KR run can serve as first user-visible proof.

Do not rush to catch it.

If not safely complete by the freeze:
- leave mode OFF
- defer activation until after the protected KR cycle
- do not deploy shared runtime mid-cycle

---

# 38. Staged rollout

## Stage A — implementation
- mode OFF

## Stage B — replay previews
- AI
- fallback
- negative controls

## Stage C — validation
- numeric
- semantic
- causal
- quality
- kill switch
- feature-OFF regression

## Stage D — main/operating promotion
- mode still OFF

## Stage E — operating readiness
- health
- schedules unchanged
- 9.1D active
- 9.0E unchanged

## Stage F — Inventory-only activation
- set `SELECTIVE_INVENTORY`
- no manual Telegram/task
- next natural KR/US run becomes user-visible proof

---

# 39. Enablement gate

Set:

`INVENTORY_ONLY_ROLLOUT_READY = YES/NO`

YES requires:
- Inventory natural proof LIVE_PASS
- Phase 9.1E preintegration ready
- AI compatibility repair PASS
- open P0 = 0
- material P1 = 0
- AI/fallback parity PASS
- numeric PASS
- semantic PASS
- causal PASS
- runtime quality PASS
- feature-OFF regression PASS
- kill switch PASS
- full tests/CI PASS
- operating health PASS

Trade AR proof is not required for Inventory-only mode.

---

# 40. Activation state

After safe activation:

```text
WORKING_CAPITAL_USER_VISIBLE_MODE =
SELECTIVE_INVENTORY

INVENTORY_USER_VISIBLE =
ENABLED_PENDING_NATURAL

TRADE_AR_USER_VISIBLE =
OFF_PENDING_NATURAL_PROOF
```

Do not mark Inventory user-visible LIVE PASS until an actual natural delivered message exercises it safely.

---

# 41. Natural proof after activation

Next natural KR or US run that naturally selects Inventory should verify:

- actual delivered Inventory sentence
- correct Fact/relation ID
- correct balance date
- semantic scope
- causal guard
- AI/fallback path
- no duplicate numeric ownership
- Phase 9.0E coexistence
- exactly-once
- message quality

Set:

`INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

One valid actual delivered Inventory enrichment can establish selective-family LIVE PASS.

---

# 42. Emergency rollback

If a natural user-visible Inventory P0 occurs:

- set working-capital mode OFF
- leave canonical 9.1B facts active
- leave 9.1C/9.1D active
- leave Phase 9.0E cash flow independent
- preserve immutable production evidence
- perform targeted repair

No archive rewrite.

---

# 43. Exact Trade AR remains blocked

Final report must state:

```text
TRADE_AR_NATURAL_PROOF = NOT_OBSERVED
TRADE_AR_USER_VISIBLE = OFF
```

unless a legitimate natural proof occurs during implementation without any manual trigger.

Even if such proof arrives naturally:
do not enable Trade AR in this task.

Trade AR requires its own later enablement decision.

---

# 44. Tests — feature gate

Required:

- OFF → no Inventory enrichment
- Inventory mode with LIVE_PASS proof → allowed
- Inventory mode without proof → blocked
- combined mode request with Trade AR unproven → blocked
- invalid config → OFF
- kill switch OFF → enrichment stops

---

# 45. Tests — selector

Required:
- material Inventory → selected
- low materiality → suppressed
- stale → suppressed
- lagging provisional → suppressed/context-only
- insurance → N/A
- Trade AR-only → suppressed
- broad AR-only → suppressed
- AP-only → suppressed

---

# 46. Tests — AI/fallback parity

For each selected replay context compare:
- ticker
- context ID
- Fact IDs
- relation
- balance date
- scope
- direction
- selected/suppressed
- Unknown resolution

Mismatch target:
`0`

---

# 47. Tests — Phase 9.0E coexistence

Required:
- FCF only
- Inventory only
- both material, Inventory redundant
- both material, combined sentence useful
- incompatible periods
- no duplicated FCF number
- no FCF recomputation

---

# 48. Full validation

Required:
- focused 9.1E.1 tests PASS
- feature gate PASS
- replay previews PASS
- AI/fallback parity PASS
- numeric PASS
- semantic/causal PASS
- runtime quality PASS
- feature-OFF regression PASS
- kill switch PASS
- Phase 9.0E regression PASS
- AI compatibility regression PASS
- broader runtime regression PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions PASS
- exact final main SHA Actions PASS

---

# 49. Required architecture update

Update:

`docs/architecture/WORKING_CAPITAL_USER_VISIBLE_PREINTEGRATION.md`

Add:
- Inventory-only enablement state
- natural-proof gate
- Trade AR blocked state
- operating mode
- kill-switch procedure
- natural user-visible proof lifecycle

---

# 50. Required reports

Create:

1. `docs/reports/20260822-phase9-1e-1-inventory-enablement-implementation.md`
2. `docs/reports/20260822-phase9-1e-1-enablement-gate.md`
3. `docs/reports/20260822-phase9-1e-1-ai-fallback-parity.md`
4. `docs/reports/20260822-phase9-1e-1-before-after-preview.md`
5. `docs/reports/20260822-phase9-1e-1-negative-controls.md`
6. `docs/reports/20260822-phase9-1e-1-numeric-semantic-validation.md`
7. `docs/reports/20260822-phase9-1e-1-feature-off-regression.md`
8. `docs/reports/20260822-phase9-1e-1-kill-switch.md`
9. `docs/reports/20260822-phase9-1e-1-rollout-readiness.md`
10. if activated:
    `docs/reports/20260822-phase9-1e-1-operating-activation.md`

Recommended JSON:

`docs/reports/20260822-phase9-1e-1-readiness.json`

---

# 51. Complete report bundle

Create:

`20260822-phase9-1e-1-inventory-only-enablement-bundle.zip`

Include sanitized reports/JSON.

Report ZIP SHA-256.

---

# 52. Completion report — repository

Report:
- instruction path
- instruction commit
- branch
- base
- implementation
- final
- previous main
- final main
- operating
- promotion method
- activation state
- worktrees
- deviations

---

# 53. Completion report — enablement

Report:

```text
INVENTORY_NATURAL_PROOF
TRADE_AR_NATURAL_PROOF

INVENTORY_ONLY_ROLLOUT_READY

WORKING_CAPITAL_USER_VISIBLE_MODE

INVENTORY_USER_VISIBLE
TRADE_AR_USER_VISIBLE
```

---

# 54. Completion report — preview

Report:
- eligible Inventory
- selected Inventory
- suppressed Inventory
- Trade AR selected = 0
- Broad AR selected = 0
- AP selected = 0
- AI/fallback mismatch
- numeric binding
- causal/semantic errors
- human quality
- message-length delta

---

# 55. Completion report — production safety

Report:
- production AI diff under OFF
- fallback diff under OFF
- Telegram manual count
- Scheduled Task manual count
- DB/Pilot mutation
- receipt/exactly-once regression
- 9.0E mode
- 9.1D canary
- XKRX/night telemetry
- Production Assist

Manual mutation targets:
`0`

---

# 56. Final states

If implemented/promoted but not activated:

```text
PHASE_9_1E_1 = IMPLEMENTED_READY_TO_ENABLE
WORKING_CAPITAL_USER_VISIBLE_MODE = OFF
```

If activated safely:

```text
PHASE_9_1E_1 = DEPLOYED_INVENTORY_ONLY_PENDING_NATURAL
WORKING_CAPITAL_USER_VISIBLE_MODE = SELECTIVE_INVENTORY
INVENTORY_USER_VISIBLE = ENABLED_PENDING_NATURAL
TRADE_AR_USER_VISIBLE = OFF_PENDING_NATURAL_PROOF
```

Do not mark natural LIVE PASS before actual natural delivery.

---

# 57. Next action gate

At completion set:

```text
NEXT_ACTION =
WAIT_FOR_INVENTORY_USER_VISIBLE_NATURAL
or
BOUNDED_REPAIR_REQUIRED
```

Do not start Trade AR enablement.

---

# 58. P0 / P1 / P2

## P0
- Trade AR or broad AR leaks user-visible
- wrong Inventory fact/period
- causal overclaim passes validator
- feature OFF still enriches production
- exactly-once/receipt break
- kill switch fails

## P1
- AI/fallback Inventory fact mismatch
- material redundant stacking with FCF
- selector materially diverges from 9.1C/D
- message quality materially degraded

## P2
- wording polish
- minor placement preference
- Trade AR still pending natural proof
- small length increase

P2 does not block Inventory-only rollout.

---

# 59. Final philosophy

This phase should be small because the difficult architecture is already done.

Do not reopen working-capital design.

The only question is:

```text
Has Inventory earned user-visible exposure?
```

It has earned the right to be enabled because:
- canonical facts are safe,
- retrospective reasoning added value,
- runtime canary passed naturally,
- user-visible architecture is already prepared.

Exact Trade AR has not yet earned that right.

Therefore:

```text
Inventory → selective enablement
Trade AR  → remain OFF
```

The rollout remains selective.

Even after enablement:

```text
eligible Inventory
≠
must be shown
```

Materiality and redundancy suppression still decide.

Success is not that every Inventory fact appears in the message.

Success is that the few Inventory relations which genuinely improve the investment interpretation can now appear safely in both AI and deterministic fallback, while every unproven working-capital family remains off.
