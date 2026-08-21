# thesis-monitor — Phase 9.1D Work Instruction

## Metadata

- Phase: `9.1D`
- Title: `Selective Working-Capital Runtime Shadow Canary`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating:
  `d0dc76a2446ee5ef9188d1b06dcb241df004c143`
- Dependency:
  - Phase 9.1A: COMPLETE
  - Phase 9.1B: COMPLETE
  - Phase 9.1C: COMPLETE
- Phase 9.1C final gate:
  `PHASE_9_1D_READY = YES`
- Approved scope:
  `SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR`
- Current Phase 9.0E mode:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`
- User-visible working-capital change: `0`
- Production-delivery influence: `0`
- Required final state:
  `PHASE_9_1D_DEPLOYED = YES/NO`
- Natural proof:
  post-deployment, separate from implementation completion

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260821-phase-9-1d-selective-working-capital-runtime-shadow-canary.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify the current safe main/operating SHA:
   `d0dc76a2446ee5ef9188d1b06dcb241df004c143`
3. Commit/push this instruction as a docs-only instruction commit.
4. Record:
   - `instruction_path`
   - `instruction_commit_sha`
   - `instruction_version`
   - `implementation_base_sha`
5. Create the implementation branch from the latest safe main descendant containing the instruction commit.
6. No force push / history rewrite.
7. Do not silently edit this instruction after implementation begins.
8. If the parallel night-futures telemetry repair lands first, reconcile onto latest main explicitly before promotion.

Recommended branch:

`codex/phase-9-1d-selective-working-capital-runtime-shadow-canary`

---

# 1. Phase purpose

Phase 9.1C proved that only a narrow subset of working-capital reasoning materially improved analysis:

```text
Inventory relations:
5 selected
5 MATERIAL_IMPROVEMENT

Exact Trade AR relations:
2 selected
2 MATERIAL_IMPROVEMENT

Broad AR:
0 selected

Trade AP:
0 selected

Broad AP:
0 selected

DEGRADED:
0
```

Phase 9.1D moves only the proven-value subset into a **natural runtime shadow canary**.

It does not make working-capital reasoning user-visible.

The target runtime architecture is:

```text
Natural production packet
        ↓
Production delivery finalizes independently
        ↓
Detached working-capital shadow canary
        ↓
Same immutable packet / cutoff
        ↓
9.1B canonical facts
        ↓
9.1C PIT / freshness / materiality selector
        ↓
Inventory or exact Trade AR only
        ↓
Shadow reasoning
        ↓
Numeric / semantic / causal / quality validation
        ↓
Immutable canary receipt
```

Production must not wait for this canary.

---

# 2. Initial canary scope

INCLUDE:

- `inventory`
- exact `trade_accounts_receivable`
- compatible Revenue relation
- compatible COGS relation where already canonical and material
- compatible Phase 9.0 OCF/FCF context only where PIT/period-safe
- Unknown resolution
- industry/materiality selection
- causal-overclaim guard

EXCLUDE:

- `accounts_receivable_broad`
- exact/broad AP
- DSO
- Inventory Days
- DPO
- CCC
- contract assets
- accrued liabilities
- working-capital score
- user-visible text
- production AI injection

---

# 3. Dynamic eligibility — no ticker allowlist

Do not implement:

```python
if ticker in {"MU", "TSLA", ...}
```

Production/shadow eligibility must be contract-driven.

Tickers from 9.1C may appear only as regression fixtures/reports.

A subject is canary-eligible only when:

1. canonical 9.1B fact exists
2. metric family is allowed by 9.1D
3. exact semantic scope passes
4. PIT passes packet cutoff
5. latest-formal freshness is safe
6. compatible comparable relation exists where required
7. industry applicability permits use
8. 9.1C materiality selector selects it
9. no relevant quality taint
10. no duplicate stronger insight should suppress it

---

# 4. Canary contract

Implement a versioned runtime contract, suggested:

`working-capital-runtime-shadow-canary-v1`

Conceptual fields:

```text
canary_id
attempt_id
packet_id
market
assessment_date
production_receipt_sha

policy
status

eligible_subjects
selected_subjects

contexts:
  ticker
  metric_family
  semantic_scope
  balance_date
  freshness_state
  pit_state
  relation_id
  selected_fact_ids
  materiality_reason
  industry_applicability
  cash_flow_cross_link
  resolved_unknowns
  suppressed_reasons

validation:
  numeric
  semantic
  causal
  quality

production_influence
latency_ms
created_at
```

Actual naming follows repository conventions.

---

# 5. Production isolation

Critical contract:

```text
production delivery terminal
        ↓
detached canary
```

The canary must not:

- delay Telegram
- block Telegram
- alter fallback
- alter AI acceptance
- alter production receipt
- alter message count
- mutate assessment state
- open/close warnings
- modify valuation context
- modify Phase 9.0E cash-flow selection
- change current investment-logic state

`production_influence = 0` must be persisted/audited.

---

# 6. Runtime trigger

Prefer the same detached post-terminal architecture used by the Phase 9.0D cash-flow canary.

Requirements:

- trigger only after the production bundle reaches terminal delivery state
- consume immutable packet/archive reference
- consume the exact packet cutoff used by production
- do not re-fetch arbitrary newer company financials
- no manual invocation required for natural proof

If there is a shared canary dispatcher, extend it cleanly.

Do not create a second scheduler if the existing detached-canary architecture can handle this.

---

# 7. Market scope

Initial 9.1D canary supports:

- KR
- US / supported foreign issuers

Only if canonical facts pass the same PIT/freshness rules.

Unlike Phase 9.0E cash-flow rollout, KR is allowed here because 9.1 working-capital facts are point-in-time balance-sheet facts and were separately proven safe.

Insurance/reinsurance generic working-capital remains N/A.

---

# 8. Selected metric family: Inventory

Inventory canary context may be selected only when:

- canonical total inventory semantic
- comparable prior balance safe
- PIT/currentness safe
- materiality selected
- industry applicability appropriate

Preferred relation families:

- Inventory YoY
- Inventory vs Revenue
- Inventory vs exact COGS

Do not use component inventory.

---

# 9. Selected metric family: Exact Trade AR

Exact Trade AR canary context may be selected only when canonical semantic is:

`trade_accounts_receivable`

Broad AR is explicitly excluded from the initial runtime canary.

Preferred relation:

- Trade AR vs Revenue

Do not use:
- broad AR
- contract assets
- other receivables
- financing receivables

as exact Trade AR.

---

# 10. One primary insight per ticker

The canary should select at most one primary working-capital insight family per ticker by default.

If Inventory is stronger than AR:
select Inventory.

If exact Trade AR is the primary decision-relevant relation:
select Trade AR.

Do not stack multiple working-capital paragraphs.

A compatible cash-flow relation may be used as context without becoming a second numeric dump.

---

# 11. Materiality selector reuse

Reuse Phase 9.1C materiality logic.

Do not build a separate runtime-only selector that changes behavior.

The same immutable packet should produce the same:

- selected metric family
- selected relation
- semantic scope
- suppression reasons

between retrospective 9.1C replay and runtime canary, subject only to naturally different packet data.

---

# 12. PIT

Every consumed Fact must satisfy:

`source_available_at <= production packet cutoff`

A newer filing/restatement appearing after production cutoff must not enter the canary.

Target:

`future_fact_used = 0`

---

# 13. Freshness

Use latest-formal filing-cycle currentness.

Do not invent elapsed-day thresholds.

For:

`FORMAL_LAGGING_PROVISIONAL`

follow Phase 9.1C rules:
- context-only or suppress
- never relabel as newer provisional-period balance

---

# 14. Exact semantic preservation

Canary validation must hard-fail any claim that:

- converts broad AR to Trade AR
- converts contract assets to Trade AR
- converts broad AP to Trade AP
- uses inventory components as total Inventory

Broad AR/AP are excluded anyway, but the validator remains defensive.

---

# 15. Causal guard

Working-capital relation alone must not assert:

- customers are failing to pay
- demand collapsed
- inventory is excess
- suppliers are being paid late
- OCF deterioration was caused by AR/inventory

Allowed cautious reasoning includes:

- cash collection quality warrants checking
- inventory conversion warrants checking
- working-capital effects are a plausible follow-up area
- the relation is compatible with, but does not prove, a cash-conversion issue

---

# 16. Cash-flow cross-link

A compatible Phase 9.0 cash-flow relation may be used only when:

- same issuer
- compatible formal reporting date/period
- PIT safe
- currentness safe
- no FCF recomputation
- no causal overclaim

Do not alter user-visible Phase 9.0E cash-flow behavior.

---

# 17. Numeric binding

Any exact working-capital number in the canary shadow prose must bind automatically to canonical Facts/relations.

Targets:

```text
automatic > 0 when selected
manual = 0
rejected = 0
unresolved = 0
```

Gap/YoY arithmetic must come from canonical derived relation, not AI subtraction.

---

# 18. Shadow AI behavior

If the canary uses AI reasoning:

- provide only selected structured context
- no raw SEC/OpenDART rows
- no recalculation request
- no unsupported advanced ratios
- no causal language beyond allowed claims

The AI result is archive-only.

Do not use this AI result for production fallback or user delivery.

---

# 19. Deterministic shadow fallback

If the canary AI candidate fails:

the canary may produce a deterministic shadow interpretation using the same selected context.

This shadow fallback is for audit only.

Do not confuse it with production fallback.

Persist:

- AI shadow validation result
- shadow fallback used YES/NO

---

# 20. Canary status vocabulary

Suggested:

- `COMPLETE_PASS`
- `COMPLETE_PASS_FALLBACK`
- `SUPPRESSED_NO_ELIGIBLE_CONTEXT`
- `SUPPRESSED_LOW_MATERIALITY`
- `FAILED_VALIDATION`
- `FAILED_RUNTIME`
- `NOT_APPLICABLE`

Use repository equivalents if already defined.

---

# 21. Canary receipt

Persist immutable receipt containing:

- canary ID
- packet ID
- production receipt SHA
- selected contexts
- Fact IDs
- relation IDs
- validations
- production influence
- duration/latency
- terminal status

Do not mutate production receipt.

---

# 22. Idempotency

Same production packet should produce one canonical canary attempt identity.

Repeated observer execution must not create duplicate logical canaries.

If retries are needed:

- one canary ID
- multiple attempt IDs
- final terminal state

---

# 23. User-visible diff

Hard acceptance:

```text
Telegram diff = 0
Production AI input diff = 0
Production fallback diff = 0
Public Action diff = 0
Public snapshot diff = 0
Assessment DB mutation = 0
Warning lifecycle mutation = 0
```

---

# 24. Phase 9.0E isolation regression

Verify:

- cash-flow user-visible mode unchanged
- current full-FCF selection unchanged
- TSLA baseline consistency unchanged
- cash-flow AI/fallback parity unchanged
- KR cash-flow exclusion unchanged
- 9.0D cash-flow canary unchanged

---

# 25. Existing canary coexistence

If 9.0D cash-flow canary remains active:

- both canaries may run after terminal delivery
- neither waits for the other
- neither consumes the other's output as source of truth
- no recursive triggering
- independent receipts

Optional combined observability is allowed, but not required.

---

# 26. Runtime latency

Measure canary latency.

Do not create an arbitrary hard latency target unless an existing canary budget exists.

The canary should remain operationally lightweight.

Because production is already terminal, latency cannot block delivery.

---

# 27. Natural proof plan

Implementation completion does not require waiting for a natural run.

After deployment:

## First natural US run
Expected opportunity:
- Inventory examples such as memory/automotive if naturally eligible

Classify:
`INVENTORY_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED`

## First natural KR run
Expected opportunity:
- Inventory
- exact Trade AR if naturally eligible

Classify:
`TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED`

Do not hard-code tickers.

---

# 28. Natural proof and phase advancement

Implementation may be marked:

`PHASE_9_1D_DEPLOYED = YES`

before natural proof.

Possible runtime state:

`DEPLOYED_PENDING_NATURAL`

A natural proof for one metric family does not pretend the unobserved family has been proven.

Do not require arbitrary multiple days before continuing architecture work.

However, any future **user-visible working-capital enablement** should require natural evidence for each metric family it intends to expose.

---

# 29. Natural proof success

A metric family gets `LIVE_PASS` when a natural packet:

- has at least one eligible selected subject
- consumes correct Fact/relation IDs
- passes PIT/freshness
- preserves semantic scope
- passes causal guard
- passes numeric binding
- production influence = 0
- canary terminal state = pass

One clean natural example can prove the mechanism for that family.

Unobserved classes remain `NOT_OBSERVED`.

---

# 30. Natural proof failure

If a natural canary finds P0:

- do not affect production
- preserve evidence
- disable only the working-capital canary if necessary
- perform bounded repair

Do not disable Phase 9.0E cash flow or canonical 9.1B facts unless the defect actually affects them.

---

# 31. Initial rollout controls

No ticker whitelist.

No broad AR/AP.

No advanced ratios.

No user-visible output.

No production dependence.

This narrowness is intentional.

---

# 32. Test matrix — selector

Required:

- current-formal Inventory + material → select
- Inventory eligible but low materiality → suppress
- exact Trade AR + material → select
- broad AR only → suppress from 9.1D
- AP only → suppress
- insurance → N/A
- stale → suppress
- future Fact → block
- lagging provisional → context-only/suppress
- blocked newer formal → do not substitute old current

---

# 33. Test matrix — semantic

Required:

- exact Trade AR label correct
- broad AR rejected from canary
- contract asset rejected
- total inventory correct
- inventory component rejected
- no DSO/DPO/CCC wording
- no cause overclaim

---

# 34. Test matrix — binding

Required:

- Inventory YoY relation binds
- Inventory vs Revenue binds
- Inventory vs COGS binds
- Trade AR vs Revenue binds
- gap pp from canonical relation
- manual/rejected/unresolved = 0

---

# 35. Test matrix — cash-flow cross-link

Required:

- compatible formal periods allowed
- incompatible periods suppressed
- FCF/OCF not recomputed
- no causality
- production Phase 9.0E unchanged

---

# 36. Test matrix — isolation

Required:

- production succeeds, canary succeeds
- production succeeds, canary fails
- production fallback, canary succeeds
- no eligible WC context
- canary retry
- duplicate invocation
- canary timeout/error

In every case:
production delivery/receipt unchanged.

---

# 37. Regression

Preserve:

- Phase 9.1A/B/C
- 9.0E
- 9.0D / 9.0D.1
- run-31 KR behavior
- run-30 US behavior
- run-29/28/27 repaired behaviors
- exactly-once
- valuation/price/RR
- KRX telemetry
- night-futures existing behavior

---

# 38. Full validation

Required:

- focused 9.1D tests PASS
- selector parity with 9.1C PASS
- semantic/causal PASS
- numeric binding PASS
- isolation PASS
- idempotency PASS
- broader regression PASS
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

# 39. Promotion

Because 9.1D is detached shadow-only, it may be promoted after deterministic validation without waiting for a natural proof.

Before promotion:

- P0 = 0
- material P1 = 0
- production/user-visible diff = 0
- isolation PASS
- CI PASS
- main ancestry clean

If the parallel night-futures telemetry branch lands first:
reconcile onto latest main before promotion.

---

# 40. Next protected US window

Current instruction date is 2026-08-21 after the KR cycle.

Protect the next morning window:

- KRX telemetry around 08:05 KST
- US primary 08:15
- US backup 08:30

Do not deploy shared runtime during the repository-defined morning freeze.

If no explicit freeze exists, use a conservative pre-run freeze starting before 08:05 and lasting until the morning production/backup cycle reaches terminal state.

Do not rush promotion to catch a run.

---

# 41. Required architecture doc

Create:

`docs/architecture/WORKING_CAPITAL_RUNTIME_SHADOW_CANARY.md`

Include:

- runtime trigger
- isolation
- canary contract
- eligibility
- metric scope
- semantic guard
- causal guard
- numeric binding
- cash-flow cross-link
- natural-proof lifecycle

---

# 42. Required reports

Create:

1. `docs/reports/20260821-phase9-1d-implementation.md`
2. `docs/reports/20260821-phase9-1d-selector-parity.md`
3. `docs/reports/20260821-phase9-1d-isolation-audit.md`
4. `docs/reports/20260821-phase9-1d-semantic-causal-audit.md`
5. `docs/reports/20260821-phase9-1d-numeric-binding.md`
6. `docs/reports/20260821-phase9-1d-validation.md`
7. `docs/reports/20260821-phase9-1d-deployment-readiness.md`
8. `docs/reports/20260821-phase9-1d-natural-proof-plan.md`

Recommended JSON:

- `docs/reports/20260821-phase9-1d-readiness.json`

---

# 43. Complete report bundle

Create:

`20260821-phase9-1d-complete-report-bundle.zip`

Include sanitized:

- complete report
- selector parity
- isolation
- semantic/causal audit
- numeric binding
- validation
- natural-proof plan
- readiness JSON

Report ZIP SHA-256.

---

# 44. Completion report — repository

Report:

- instruction path
- instruction commit
- base
- branch
- implementation
- final
- previous main
- final main
- operating
- promotion method
- worktrees
- deviations

---

# 45. Completion report — scope

Report:

- Inventory selected-capable count in replay
- exact Trade AR selected-capable count
- broad AR selected count = 0
- AP selected count = 0
- N/A
- suppressed reasons

---

# 46. Completion report — runtime isolation

Report:

- production packets tested
- production influence violations
- delivery diff
- receipt diff
- duplicate canaries
- canary retries
- terminal statuses

Target production influence violations = `0`.

---

# 47. Completion report — semantics

Report:

- broad→trade mislabels
- contract-asset leakage
- inventory-component leakage
- causal overclaims
- DSO/DPO/CCC leakage

Targets all `0`.

---

# 48. Completion report — binding

Report:

- automatic
- manual
- rejected
- unresolved
- relation arithmetic errors

Targets manual/rejected/unresolved/errors `0`.

---

# 49. Completion report — natural state

At implementation completion:

```text
PHASE_9_1D_DEPLOYED = YES/NO

WORKING_CAPITAL_RUNTIME_CANARY =
DEPLOYED_PENDING_NATURAL
or actual state

INVENTORY_NATURAL_PROOF =
PENDING / LIVE_PASS / FAIL / NOT_OBSERVED

TRADE_AR_NATURAL_PROOF =
PENDING / LIVE_PASS / FAIL / NOT_OBSERVED
```

Do not fabricate natural proof.

---

# 50. Next phase gate

Report:

`PHASE_9_1E_ARCHITECTURE_READY = YES/NO`

This means architecture/research may continue.

It does **not** mean user-visible working-capital enablement is ready.

For future user-visible enablement, require natural proof for each included metric family.

---

# 51. P0 / P1 / P2

## P0
- canary affects production
- wrong Fact/relation
- future Fact
- broad→trade semantic error
- wrong period
- unsupported causal claim that passes validation
- advanced ratio fabricated

## P1
- selector materially diverges from 9.1C
- high-value relation systematically missed
- natural canary repeatedly fails
- industry applicability materially wrong

## P2
- wording polish
- AP/broad AR excluded
- small latency/observability improvements

P2 does not block deployment.

---

# 52. Final philosophy

Phase 9.1D is not a user-visible feature launch.

It is the production-runtime proof that the narrow working-capital reasoning discovered in 9.1C survives natural packets without affecting delivery.

The canary should answer:

```text
Did a natural packet have a material Inventory or exact Trade AR relation?

Did we select the same thing 9.1C would select?

Did the same canonical Facts survive PIT/currentness?

Did semantic scope remain exact?

Did the reasoning avoid causal overclaim?

Did production remain completely independent?
```

Only Inventory and exact Trade AR earned a place in this first canary.

Broad AR/AP remain useful canonical evidence but did not prove enough incremental daily reasoning value.

Do not expand the scope for symmetry.

Success is:

> Natural production runs normally, while a detached canary proves that selected Inventory and exact Trade AR reasoning is safe, useful, provenance-bound, and operationally invisible.
