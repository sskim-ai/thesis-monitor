# thesis-monitor — Phase 9.1C Work Instruction

## Metadata

- Phase: `9.1C`
- Title: `Working Capital Shadow Consumption & Earnings-Quality Reasoning`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Dependency chain:
  - Phase 9.1A final: `d4a4daf08ff5f68bc1072cc065e69ca5de5da145`
  - Phase 9.1B final: `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6`
- Current main/operating before KR natural window: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- 9.1A/9.1B promotion: `PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`
- Phase 9.1B gate: `PHASE_9_1C_READY = YES`
- Approved scope: `WORKING_CAPITAL_SHADOW_CONSUMPTION_EARNINGS_QUALITY`
- Phase 9.0E cash-flow user-visible mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`
- User-visible working-capital change: `0`
- Required final gate: `PHASE_9_1D_READY = YES/NO`

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260821-phase-9-1c-working-capital-shadow-consumption.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify Phase 9.1B final SHA:
   `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6`
3. Create the Phase 9.1C branch from the Phase 9.1B final SHA.
4. Commit/push this instruction as a docs-only instruction commit before implementation.
5. Record:
   - `instruction_path`
   - `instruction_commit_sha`
   - `instruction_version`
   - `dependency_base_sha`
6. Implement only after the instruction commit exists.
7. If main moves before later promotion, reconcile explicitly.
8. No force push / history rewrite.
9. Do not silently edit this instruction after implementation begins.

Recommended branch:

`codex/phase-9-1c-working-capital-shadow-consumption`

Expected ancestry:

```text
operating/main 33c2...
        ↓
Phase 9.1A d4a4...
        ↓
Phase 9.1B 2ea8...
        ↓
9.1C instruction
        ↓
9.1C implementation/final
```

---

# 1. KR natural-window protection

Protected operating window:

- KRX telemetry: `16:05 KST`
- KR primary: `16:15 KST`
- KR backup: `16:55 KST`
- combined review: approximately after `17:05 KST`

Phase 9.1C development may proceed on the dependent branch.

Until the natural KR review is complete:

- main promotion: `0`
- operating checkout change: `0`
- API restart: `0`
- feature mode change: `0`
- scheduler change: `0`
- manual task: `0`
- manual Telegram: `0`

At `15:50 KST`, treat operating/shared-runtime as frozen through the natural cycle.

If 9.1C finishes before natural review:

push branch + reports and set:

`PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`

Do not wait/sleep solely to catch the natural run.

---

# 2. Phase purpose

Phase 9.1A established the working-capital evidence architecture.

Phase 9.1B implemented deterministic canonical:

- Inventory
- exact Trade AR
- Broad AR
- exact Trade AP
- Broad AP
- prior-year comparable balances
- absolute deltas
- safe YoY
- selective AR-vs-Revenue
- Inventory-vs-Revenue
- Inventory-vs-COGS
- AP-vs-COGS relations

Phase 9.1C asks:

> Can these canonical working-capital facts actually improve earnings-quality reasoning without overstating causality or semantic precision?

This phase is archive-only shadow consumption.

Target chain:

```text
Canonical working-capital Facts
        ↓
PIT
        ↓
Latest-formal freshness
        ↓
Comparable relation selection
        ↓
Trade-vs-Broad semantic preservation
        ↓
Industry applicability
        ↓
Materiality selection
        ↓
Shadow AI reasoning
        ↓
Numeric binding
        ↓
Semantic validation
        ↓
Runtime quality
        ↓
Before / After human audit
```

Production/user-visible path remains unchanged.

---

# 3. Phase 9.1B facts are source of truth

Do not recompute working-capital facts in 9.1C.

Consume only the canonical 9.1B facts and relations.

Known 9.1B results:

- selected reported Facts: `160`
- balance delta Facts: `44`
- balance YoY Facts: `44`
- flow YoY Facts: `31`
- eligible structured relations: `53`
- arithmetic errors: `0`
- provenance errors: `0`
- idempotency errors: `0`
- 9.1A newly blocked: `0`

Actual repository artifacts are authoritative.

---

# 4. Critical semantic rule

The shadow reasoning must preserve:

```text
Trade AR
≠
Broad AR

Trade AP
≠
Broad AP
```

A relation based on `accounts_receivable_broad` must never be described as trade receivables unless the canonical semantic explicitly is trade AR.

Likewise broad AP must never become trade AP or supplier-specific wording.

This is a hard semantic gate.

---

# 5. Explicit exclusions

Do NOT implement:

- production AI working-capital context
- fallback working-capital text
- Telegram working-capital text
- Public Action working-capital fields
- public snapshot fields
- production packet user-visible schema changes
- DSO
- Inventory Days
- DPO
- CCC
- working-capital score
- automatic warning thresholds
- automatic investment-logic state changes
- automatic warning lifecycle mutation
- automatic valuation-context change
- DB assessment mutation
- KR OpenDART cash-flow period recovery
- contract assets as trade AR
- accrued liabilities as trade AP
- inventory component aggregation
- arbitrary receivable-quality scores
- paid provider integration
- KRX breadth integration
- Phase 9.0E cash-flow feature-mode changes

---

# 6. Preferred shadow contract

Implement a shadow-consumption contract, suggested:

`working-capital-shadow-consumption-v1`

or cleanly extend an existing internal reasoning-sidecar contract.

Conceptual fields:

```text
ticker
market
packet_id
assessment_date
cutoff

status
usage_mode

latest_formal_balance_date
freshness_state
pit_state

industry_applicability
materiality_reason

inventory_context
trade_ar_context
broad_ar_context
trade_ap_context
broad_ap_context

selected_relations
selected_fact_refs

semantic_labels
allowed_claims
prohibited_claims

resolved_unknowns
remaining_unknowns
suppression_reasons
```

Do not dump the entire 9.1B canonical store into the AI context.

---

# 7. PIT safety

For historical replay, every working-capital Fact/relation used must satisfy:

```text
source_available_at <= packet cutoff
```

A later restatement may exist in today's canonical store but must not leak into an older replay before the restatement was available.

Target:

`future_fact_used = 0`

---

# 8. Freshness / currentness

Use the latest validated formal balance-sheet period.

Do not invent arbitrary 30/60/90-day thresholds.

Internal states should map to existing equivalents for:

- CURRENT_FORMAL
- FORMAL_LAGGING_PROVISIONAL
- STALE_CONTEXT_ONLY
- BLOCKED
- NOT_APPLICABLE

If a newer formal balance exists but a metric is blocked:

do not substitute an older metric as current.

---

# 9. Formal-lagging-provisional

If newer official provisional earnings exist but the latest working-capital balance remains from the prior formal period:

- canonical balance remains valid for its formal date
- it may be context-only
- do not describe it as the newer provisional quarter's current balance
- do not say "this quarter inventory" unless the formal balance date supports it

Mirror Phase 9.0C freshness discipline.

---

# 10. One primary working-capital insight

Do not generate a full working-capital data dump.

For each ticker, select at most one primary insight family by default:

- Inventory relation
- exact Trade AR relation
- Broad AR relation
- exact Trade AP relation
- Broad AP relation

A secondary relation is allowed only when necessary to explain the same earnings-quality mechanism.

Do not output all five balance metrics.

---

# 11. Materiality selector

Canonical eligibility does not imply reasoning usage.

Select context only if materially relevant.

Possible evidence:

- industry applicability PRIMARY / SECONDARY
- existing monitoring Unknown mentions inventory / AR / AP / collection / working capital
- existing next-check refers to inventory/receivables/cash conversion
- cash-flow reasoning would benefit from a working-capital qualifier
- relation changes an existing earnings-quality interpretation
- revenue / margin / OCF context makes it decision-relevant

Do not create a 0–100 materiality score.

---

# 12. No arbitrary significance threshold

Do not invent:

- AR growth 10pp above revenue = warning
- Inventory growth 15pp above sales = bad

The selector may use relation direction and existing monitoring relevance, but no new numeric warning threshold.

---

# 13. Relation semantics

Backend relations are factual.

Examples:

```text
Broad AR growth > Revenue growth
Inventory growth > Revenue growth
Inventory growth < COGS growth
Trade AP growth > COGS growth
```

The AI may interpret cautiously but cannot turn these into unsupported causal conclusions.

---

# 14. Core reasoning boundary

When supported, AI may say:

- receivables grew faster than revenue, so cash collection quality deserves checking
- inventory grew faster than revenue/COGS, so inventory conversion deserves checking
- receivables grew slower than revenue, which is compatible with stronger collection discipline
- inventory declined while revenue rose, which is compatible with inventory normalization

Prefer cautious language:

```text
consistent with
compatible with
warrants checking
needs confirmation
```

unless stronger evidence exists.

---

# 15. Forbidden causal overclaims

Reject statements equivalent to:

- AR rose because customers are not paying
- Inventory rose because demand collapsed
- AP rose because the company is delaying suppliers
- AP fell because liquidity improved
- Inventory decline proves stronger demand
- AR decline proves better collections

unless separate evidence directly supports the cause.

Working-capital relation alone is not causality.

---

# 16. Broad AR wording

If semantic is `accounts_receivable_broad`, keep wording broad.

Examples:

- `매출채권 범주`
- `넓은 범주의 매출채권`

Do not call it exact trade receivables.

Final Korean wording must preserve semantic precision.

---

# 17. Exact Trade AR wording

If semantic is `trade_accounts_receivable`, trade-receivable wording is allowed according to source meaning.

Do not broaden beyond the exact semantic.

---

# 18. Broad AP wording

For `accounts_payable_broad` use broad payable wording.

Do not imply:
- trade suppliers
- supplier payment terms
- DPO

unless exact trade AP semantic and additional evidence exist.

---

# 19. Exact Trade AP wording

Exact trade AP may be described as trade-payables context.

Still do not infer payment days.

---

# 20. Inventory wording

Use `재고` / `재고자산` only when canonical total inventory semantic is safe.

Do not mention:
- raw materials
- finished goods
- WIP

unless those component Facts separately exist in a future phase.

---

# 21. Revenue alignment

When using AR growth vs Revenue growth, the shadow context must carry compatible revenue comparison Fact IDs.

Do not compare AR relation to a different revenue period.

YTD-compatible relation must not be described as TTM or standalone-quarter comparison.

---

# 22. COGS alignment

When using:
- Inventory vs COGS
- AP vs COGS

the exact COGS semantic must be supplied.

If unavailable, do not reconstruct from operating expenses or other costs.

---

# 23. No advanced working-capital ratios

Shadow validator must reject:

- DSO
- days sales outstanding
- Inventory Days
- DPO
- payable days
- CCC / cash conversion cycle

until future explicit implementation.

---

# 24. Working capital ≠ OCF cause

If:
- AR grew faster than revenue
- OCF declined

AI may say:
`working-capital movement is an area to verify`

but not:
`AR caused the OCF decline`

without evidence.

This is a core semantic rule.

---

# 25. Working-capital + cash-flow interaction

Phase 9.0 cash-flow evidence may be used in shadow reasoning where PIT/freshness and periods are compatible.

Allowed:

```text
working-capital signal
+
OCF/FCF direction
→ earnings-quality context
```

But:
- no causal assignment
- no new OCF/FCF calculation
- no Phase 9.0E production sidecar changes
- shadow only

---

# 26. Period compatibility across balance and cash flow

A point-in-time balance at period end can be contextualized with compatible revenue/OCF/FCF flow ending on the same formal reporting date.

Do not combine a Q2 balance relation with unrelated TTM FCF as if same-period unless an explicit contract supports it.

---

# 27. Earnings-quality interpretation classes

Use small typed classes or structured metadata, e.g.:

```text
RECEIVABLE_GROWTH_OUTPACES_REVENUE
RECEIVABLE_GROWTH_LAGS_REVENUE
INVENTORY_GROWTH_OUTPACES_REVENUE
INVENTORY_GROWTH_LAGS_REVENUE
INVENTORY_GROWTH_OUTPACES_COGS
INVENTORY_GROWTH_LAGS_COGS
PAYABLE_GROWTH_OUTPACES_COGS
PAYABLE_GROWTH_LAGS_COGS
```

Preserve:
- trade vs broad semantic
- industry
- no good/bad verdict

Prefer structured metadata over enum proliferation where possible.

---

# 28. No automatic quality verdict

Do not create backend states like:

- GOOD_WORKING_CAPITAL
- BAD_WORKING_CAPITAL
- CASH_CONVERSION_WEAK

Deterministic layer supplies facts and relation directions only.

---

# 29. Industry-specific reasoning

Use Phase 9.1A applicability.

## Memory / semiconductor
Inventory may be material.
Interpret with ASP/mix/cycle/supply discipline where available.
Inventory rise alone does not prove demand weakness.

## Automotive
Inventory may be material.
Interpret with deliveries/incentives/mix where available.

## Steel / materials
Inventory and receivables may matter.
Interpret with spread/raw-material cycle/demand/pricing where available.

## Industrial / electrical equipment
AR/inventory can matter for order conversion.
Contract assets remain separate.

## Aerospace / defense / project
Do not treat contract assets as trade AR.

## Transport/logistics
AR/AP may be relevant; inventory often less so.

## Cloud/platform / software
Broad AR may be context; do not over-weight routine receivable movement.

## HPC/data-center
Working capital is usually secondary to CAPEX/financing/billing conversion.

## Biotech
Working capital usually not primary; cash burn/runway is more important.

## Insurance
Generic industrial working-capital reasoning remains N/A.

## Special financial-like platforms
Do not apply industrial AR/AP interpretation automatically.

---

# 30. Unknown-resolution logic

Existing messages may say:
- inventory unavailable
- receivables unavailable
- working capital unclear

If fresh canonical Facts now exist and are shadow-consumption eligible, the same-scope Unknown should be resolved or narrowed.

If only broad AR exists:
- exact trade AR may remain Unknown
- broad-receivable availability is known

Mandatory distinction.

---

# 31. Unknown-resolution states

Track:

- RESOLVED_EXACT
- RESOLVED_BROAD_ONLY
- STILL_VALID
- NOT_APPLICABLE
- STALE_CONTEXT_ONLY

Use repository-equivalent vocabulary if available.

No silent semantic inflation.

---

# 32. Availability vs materiality

A Fact can resolve an Unknown without becoming prose.

If broad AR is known but low-materiality:
- stop claiming broad AR unavailable
- no new AR sentence required

Availability and materiality are separate.

---

# 33. Numeric ownership

In shadow AI, exact working-capital numeric detail belongs to business/earnings-quality context.

Do not repeat exact numbers across:
- core
- valuation
- price
- observer
- holder
- next check

One primary numeric owner.

---

# 34. Prefer relation over numeric dump

Prefer:

`AR increased faster than revenue`

over listing all raw/current/prior/YoY values.

Exact numbers are allowed only when materially useful.

---

# 35. Numeric display policy in shadow preview

Default:
- one relation
- optionally one exact balance/YoY number

More requires explicit materiality.

This is quality discipline, not a rigid numeric cap.

---

# 36. PIT validator

Reject:
- future filing used
- future restatement before availability
- future flow relation fact
- relation with one future input

Target:
`0` PIT violations.

---

# 37. Freshness validator

Reject:
- old balance called current when newer formal exists
- older balance substituted for blocked newer period
- provisional period label attached to older formal balance

Allow:
- formal-lagging-provisional context-only with explicit period if material

---

# 38. Semantic validator — AR/AP

Reject:
- broad AR described as trade AR
- broad AP described as trade AP
- contract asset described as trade AR
- accrued liability described as trade AP
- financing receivable described as operating trade AR
- AP/COGS relation described as DPO
- AR/revenue relation described as DSO

---

# 39. Semantic validator — causality

Reject unsupported causal language where working-capital relation is the only evidence.

Examples:
- `고객 회수가 악화됐다`
- `재고 과잉이 확인됐다`
- `공급업체 지급을 늦췄다`

Allow cautious:
- `회수 속도를 추가 확인할 필요`
- `재고 전환을 확인할 필요`
- `운전자본 영향을 점검할 필요`

---

# 40. Semantic validator — investment state

Working-capital relation alone must not:
- strengthen
- weaken
- invalidate
- change valuation context
- open/close warning

unless wider evidence contract is satisfied.

Shadow status-delta candidate:
audit only.

No persistence.

---

# 41. Status-delta candidate audit

If enriched shadow proposes a different business-thesis state:

record:
- ticker
- baseline state
- shadow state
- working-capital Facts
- other supporting Facts
- evidence-contract result

Persistence:
`0`

---

# 42. Shadow sidecar generation

Build archive-only sidecar from:
- immutable replay packet
- 9.1B canonical facts
- PIT cutoff
- freshness
- industry applicability
- materiality
- existing investment logic/Unknowns
- compatible 9.0 cash-flow context

No raw SEC/OpenDART rows to AI.

---

# 43. Shadow AI generation

Generate archive-only candidates.

No Telegram.

No Scheduled Task prompt/config change.

Use same baseline before/after except working-capital sidecar.

---

# 44. Primary replay set

Use both:

## US
Latest appropriate repaired immutable US baseline, preferably run-30 or later repository-approved immutable packet.

Purpose:
- broad AR/AP
- inventory
- cash-flow cross-link
- non-calendar / foreign cases

## KR
run-29 repaired baseline or a later immutable KR packet if appropriate.

Purpose:
- safe KR point-in-time balance-sheet reasoning
- inventory/AR applicability
- insurance N/A
- independence from blocked KR cash-flow period

Do not use future filings relative to replay cutoff.

---

# 45. Before/after comparison

For every consumption-eligible ticker compare:

Before:
- business/earnings
- core
- Unknowns
- next checks

After:
- working-capital-enriched shadow versions

Record:
- selected relation
- canonical Fact IDs
- semantic scope
- interpretation change
- Unknown resolved/narrowed
- message-length change
- cash-flow context used or not

---

# 46. Human-value classification

Per ticker:

- MATERIAL_IMPROVEMENT
- MINOR_IMPROVEMENT
- NO_MEANINGFUL_CHANGE
- DEGRADED

Do not force improvement.

---

# 47. Degraded criteria

DEGRADED if:
- broad AR becomes trade AR
- causal overconfidence appears
- low-value working-capital noise crowds out important business evidence
- caveats overwhelm readability
- numeric dump reduces clarity
- industry-inappropriate relation is elevated

Target:
`DEGRADED = 0`
for proposed 9.1D scope.

---

# 48. Repetition control

Do not create portfolio templates such as:

`매출채권 증가율은 X이고 매출 증가율은 Y입니다.`

across many tickers.

Structured sidecar may repeat fields.
Prose must remain subject/industry/decision-specific.

Use existing runtime quality policy unchanged.

---

# 49. Broad-semantic repetition

The same broad AR/AP relation may be material for one ticker and irrelevant for another.

Materiality selector should suppress low-value repetitive prose.

---

# 50. Numeric binding

All shadow exact numbers:
- automatic canonical binding required
- manual = 0
- rejected = 0
- unresolved = 0

Semantic types distinguish:
- inventory
- trade AR
- broad AR
- trade AP
- broad AP
- YoY/growth-gap relations

Do not bind broad AR to a trade label.

---

# 51. Flow-relation numeric binding

If prose uses:

`AR growth exceeded revenue growth by X percentage points`

the gap must bind to canonical derived relation, not AI subtraction.

Same for inventory/revenue, inventory/COGS, AP/COGS.

No AI arithmetic.

---

# 52. Unsafe input guard

If one YoY input is unavailable:
- no gap
- no direction inferred from raw absolute values

---

# 53. Negative/zero denominator guard

If canonical relation is blocked by zero/negative/missing prior:
- do not generate standard growth relation
- no AI workaround

---

# 54. Cross-flow reasoning with OCF/FCF

If 9.0 cash-flow context is compatible:

Allowed:
`AR growth > revenue growth + weaker OCF → collection/working-capital conversion is worth checking`

Forbidden:
`AR increase caused OCF deterioration`

without attribution evidence.

---

# 55. Memory inventory + FCF reasoning

For memory:
- inventory relation
- ASP/margin context
- FCF

may jointly improve analysis.

But:
- inventory rise ≠ oversupply proof
- inventory decline ≠ structural demand proof

Cycle context required.

---

# 56. Industrial/project AR reasoning

If exact trade AR absent but broad AR exists:
- do not imply customer/order collection specifics
- contract assets remain separate

Audit this explicitly.

---

# 57. AP reasoning limitations

AP relations are usually weaker than inventory/AR.

If AP produces little value in 9.1C:
- keep canonical AP in 9.1B
- exclude AP from initial 9.1D canary

Do not force usage for symmetry.

---

# 58. Selector evidence output

For each ticker report:

```text
consumption_status
selected_metric_family
selected_relation
materiality_reason
semantic_scope
suppression_reason
```

Possible suppressions:
- low materiality
- industry not primary
- freshness lag
- no safe relation
- broad semantic too weak
- duplicate of stronger cash-flow insight
- N/A

---

# 59. Working-capital vs cash-flow insight priority

If both cash-flow and working-capital are material:
- do not stack both by default
- choose the relation that most improves investment interpretation

Examples:
- FCF already resolves main Unknown → suppress low-value AR prose
- FCF weakness + AR/revenue divergence clarifies follow-up → working-capital may be additive

No generic stacking.

---

# 60. Shadow message length

Record before/after average and per ticker.

No arbitrary limit.

Avoid large expansion.
Prefer replacing generic Unknowns over appending paragraphs.

---

# 61. Final-language rules

Korean shadow wording must distinguish:
- exact trade receivable
- broad receivable category
- exact trade payable
- broad payable category

Internal terms like semantic_scope/fact_id/PIT must not appear in user-style preview.

---

# 62. No user-visible integration

Critical:

```text
production AI = 0
fallback = 0
Telegram = 0
Public Action = 0
snapshot = 0
9.0E mode = unchanged
```

Archive-only shadow only.

---

# 63. 9.0E regression

Verify:
- selective current-formal FCF selector unchanged
- cash-flow user-visible mode unchanged
- AI/fallback cash-flow parity unchanged
- TSLA baseline consistency unchanged
- kill switch unchanged
- KR FCF leakage = 0
- 9.0D canary unchanged

Any 9.0E user-visible behavior change is outside scope.

---

# 64. Natural KR review integration boundary

After approximately `17:05 KST`, a separate natural KR review may be available.

Use it only for promotion safety.

Promotion check:
- production P0 = 0
- no shared-runtime material P1
- no relevant KRX infrastructure P0

---

# 65. If natural KR shows 9.0E leakage

Unexpected KR user-visible cash-flow is P0.

Do not promote 9.1A/B/C until current production P0 is handled.

Preserve branch evidence.

---

# 66. If natural KR has only P2

Do not block 9.1 promotion.

Record backlog.

---

# 67. Promotion chain

After KR review confirms no blocker and 9.1C passes, promote:

```text
main
→ 9.1A
→ 9.1B
→ 9.1C
```

only if ancestry remains clean.

Do not cherry-pick random implementation pieces.

If main drift:
explicit clean integration.

---

# 68. Zero-runtime-diff promotion

Before promotion prove:
- production working-capital input = 0
- production working-capital renderer = 0
- Telegram diff = 0
- Public Action diff = 0
- 9.0E cash-flow behavior unchanged

---

# 69. API restart

Restart only if changed imported runtime modules require it.

If shadow/audit-only:
avoid unnecessary restart.

After restart:
health PASS.

---

# 70. Scheduled tasks

Keep unchanged:
- US primary 08:15
- US backup 08:30
- KR primary 16:15
- KR backup 16:55

KRX telemetry:
- 08:05
- 16:05

Manual runs:
`0`

---

# 71. Production Assist

Remain:
`OFF`

---

# 72. Tests — PIT

Required:
- pre-cutoff allowed
- post-cutoff blocked
- future restatement blocked
- relation with one future input blocked

---

# 73. Tests — freshness

Required:
- current formal consumed
- formal-lagging-provisional context-only/suppressed
- older metric not substituted for blocked newer formal
- stale context not described current

---

# 74. Tests — broad/trade semantics

Required:
- broad AR never trade AR wording
- exact trade AR allowed
- broad AP never trade AP wording
- exact trade AP allowed
- relation preserves semantic scope
- Unknown resolution distinguishes exact vs broad

---

# 75. Tests — causal guard

Required:

1. AR growth > revenue
   - "verify collection quality" allowed
   - "customers are not paying" rejected

2. Inventory growth > revenue
   - "inventory conversion needs checking" allowed
   - "demand collapse confirmed" rejected

3. AP growth > COGS
   - contextual statement allowed
   - "supplier payments delayed" rejected

---

# 76. Tests — no advanced ratios

AI candidate attempting:
- DSO
- Inventory Days
- DPO
- CCC

must be rejected.

No derived refs for these metrics.

---

# 77. Tests — relation binding

Required:
- direction binds canonical relation
- gap pp binds canonical relation
- no AI subtraction
- missing relation → no gap
- broad/trade claim semantic matches relation

---

# 78. Tests — Unknown resolution

Required:
- exact AR available → exact unavailable claim removed
- broad AR only → exact trade AR remains Unknown; broad-unavailable claim removed
- stale context → current Unknown remains
- N/A → no generic working-capital Unknown
- low-materiality known Fact → availability Unknown resolved even without new prose

---

# 79. Tests — industry

Required:
- memory inventory material
- insurance N/A
- biotech suppress low-value working-capital
- cloud broad AR secondary
- project contract assets not trade AR
- HPC relation secondary
- KR industrial safe relation where canonical facts support it

---

# 80. Tests — cash-flow cross-link

Required:
- compatible AR/revenue + OCF relation can be context
- incompatible periods → blocked
- no causal claim
- 9.0 FCF not recomputed
- 9.0E production sidecar unaffected

---

# 81. Tests — message quality

Required:
- no generic portfolio WC boilerplate
- no numeric dump
- primary numeric ownership
- company/industry specificity
- Unknown specificity
- next-check specificity
- final Korean language
- existing thresholds unchanged

---

# 82. Tests — status delta

Working-capital alone must not persist or auto-change thesis state.

Any status-delta candidate:
audit only.

---

# 83. Replay regression

Must preserve:
- run-30 / 9.0D natural cash-flow evidence
- run-29 repaired KR quality
- run-28
- run-27
- Phase 8.5.5/.1/.2
- valuation safety
- dynamic price/RR
- night futures
- fallback
- exactly-once
- KRX telemetry
- 9.0B/9.0C/9.0D/9.0D.1/9.0E

---

# 84. Full validation

Required:
- focused 9.1C PIT/freshness/semantic tests PASS
- shadow AI replay PASS
- numeric binding PASS
- runtime quality PASS
- Unknown-resolution audit PASS
- industry audit PASS
- 9.0E regression PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- docs/state JSON PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- implementation exact-SHA Actions PASS
- final branch exact-SHA Actions PASS

After promotion:
- final main Actions PASS

---

# 85. Value-add audit questions

Answer:

1. Does canonical WC evidence resolve real Unknowns?
2. Does it improve earnings-quality reasoning beyond cash-flow evidence?
3. Does trade-vs-broad precision survive prose?
4. Does it avoid unsupported causality?
5. Does inventory reasoning improve memory/industrial analysis?
6. Does receivable reasoning improve collection/cash-conversion monitoring?
7. Is AP useful enough for runtime canary?
8. Does WC reasoning increase message clutter?
9. Which metric families should be excluded from first runtime canary?

---

# 86. Human value classification

Report counts:

```text
MATERIAL_IMPROVEMENT
MINOR_IMPROVEMENT
NO_MEANINGFUL_CHANGE
DEGRADED
```

Also by metric family:
- Inventory
- Trade AR
- Broad AR
- Trade AP
- Broad AP
- cross-growth relations

This determines 9.1D scope.

---

# 87. Initial runtime-canary candidate

If 9.1C succeeds, likely next phase:

`Phase 9.1D — Selective Working-Capital Runtime Shadow Canary`

Do not automatically include every implemented relation.

Use value-add evidence.

For example:
- Inventory in memory/industrial
- exact/broad AR vs revenue where material
- AP only if 9.1C shows real value

Do not implement 9.1D here.

---

# 88. PHASE_9_1D_READY gate

Must set exactly:

`PHASE_9_1D_READY = YES` or `NO`

YES requires:
- PIT PASS
- freshness PASS
- trade/broad semantic PASS
- no unsupported causality
- numeric binding PASS
- relation binding PASS
- Unknown resolution PASS
- industry applicability PASS
- runtime quality PASS
- no DSO/CCC leakage
- no 9.0E regression
- open P0 = 0
- open material P1 = 0
- degraded = 0 or degraded classes safely excluded from 9.1D scope
- full CI PASS
- production/user-visible working-capital diff = 0

100% universe usage is not required.

---

# 89. PHASE_9_1D_SCOPE

Output an evidence-based selective scope.

Possible examples:

```text
SELECTIVE_INVENTORY_AR_RUNTIME_SHADOW_CANARY
SELECTIVE_WORKING_CAPITAL_RELATION_RUNTIME_SHADOW_CANARY
INVENTORY_PRIMARY_AR_SECONDARY_SHADOW_CANARY
```

Do not force exact strings.

Report:
- included metric families
- excluded metric families
- included industry classes
- exclusion reasons

AP may be excluded if value-add is weak.

---

# 90. Advanced-ratio readiness

Re-state:

```text
DSO_READY_FOR_IMPLEMENTATION
INVENTORY_DAYS_READY_FOR_IMPLEMENTATION
DPO_READY_FOR_IMPLEMENTATION
CCC_READY_FOR_IMPLEMENTATION
```

Expected default remains DEFER.

Do not auto-upgrade because 9.1C passes.

---

# 91. Required architecture doc

Create:

`docs/architecture/WORKING_CAPITAL_SHADOW_CONSUMPTION.md`

Document:
- sidecar
- PIT
- freshness
- semantic labels
- materiality
- industry applicability
- causal guard
- Unknown resolution
- relation binding
- no-user-visible boundary
- cash-flow cross-link rules

---

# 92. Required PIT/freshness report

Create:

`docs/reports/20260821-phase9-1c-pit-freshness-audit.md`

Include:
- consumed Facts
- future blocked
- lagging cases
- stale/blocked
- violations

Target `0`.

---

# 93. Required semantic audit

Create:

`docs/reports/20260821-phase9-1c-semantic-scope-audit.md`

Include:
- exact trade AR used
- broad AR used
- exact trade AP used
- broad AP used
- semantic mislabels
- contract-asset leakage
- accrued-liability leakage

Targets `0`.

---

# 94. Required causal-guard report

Create:

`docs/reports/20260821-phase9-1c-causal-guard-audit.md`

Include:
- allowed cautious interpretation
- rejected causal overclaim
- inventory
- AR
- AP
- cash-flow cross-link

---

# 95. Required Unknown-resolution report

Create:

`docs/reports/20260821-phase9-1c-unknown-resolution-audit.md`

Report:
- before
- exact resolved
- broad-only narrowed
- still valid
- stale
- N/A
- contradictions

Target contradictory retained `0`.

---

# 96. Required before/after report

Create:

`docs/reports/20260821-phase9-1c-shadow-before-after.md`

Include representative full US and KR message previews.

No Telegram.

---

# 97. Required industry/value-add report

Create:

`docs/reports/20260821-phase9-1c-industry-value-add.md`

Show which relation families improve which industry classes.

This is the primary input for 9.1D scope.

---

# 98. Required validation report

Create:

`docs/reports/20260821-phase9-1c-validation.md`

Include:
- focused
- binding
- semantic
- causal guard
- quality
- regression
- full pytest
- Ruff/diff
- Knowledge/Action
- CI

---

# 99. Required readiness report

Create:

`docs/reports/20260821-phase9-1c-readiness.md`

Must include:

```text
PHASE_9_1D_READY = YES/NO
PHASE_9_1D_SCOPE = ...
```

and advanced-ratio readiness.

---

# 100. Recommended JSON

Create:
- `docs/reports/20260821-phase9-1c-shadow-context.json`
- `docs/reports/20260821-phase9-1c-readiness.json`

No secrets.

---

# 101. Complete report bundle

Create:

`docs/reports/20260821-phase9-1c-complete-report.md`

And:

`20260821-phase9-1c-complete-report-bundle.zip`

ZIP should contain sanitized reports/JSON only.

Report SHA-256.

Push reports to the 9.1C branch.

---

# 102. Promotion after KR review

After natural KR review:

If:
- production P0 = 0
- no relevant shared-runtime material P1
- 9.1C P0 = 0
- 9.1C material P1 = 0
- user-visible diff = 0
- validation/CI PASS
- ancestry clean

then promote:

```text
9.1A → 9.1B → 9.1C
```

to main/operating.

If main drift exists:
explicit clean integration.

---

# 103. Main/operating promotion

When approved:
- fetch origin
- verify ancestry
- clean fast-forward if possible
- operating HEAD = main
- clean worktree
- restart API only if needed
- health PASS
- 9.0E mode unchanged
- AI schedules unchanged
- KRX telemetry unchanged
- Production Assist OFF

No manual natural run.

---

# 104. Persistent state before promotion

```text
Phase 9.1A:
COMPLETE_PENDING_PROMOTION

Phase 9.1B:
COMPLETE_PENDING_PROMOTION

Phase 9.1C:
SHADOW_CONSUMPTION_CLOSED_RETROSPECTIVE_PENDING_PROMOTION

Working Capital User Visible:
NOT_ENABLED
```

Do not modify operating state prematurely.

---

# 105. Persistent state after promotion

```text
Phase 9.1A:
COMPLETE

Phase 9.1B:
COMPLETE

Phase 9.1C:
COMPLETE

Working Capital Canonical Core:
IMPLEMENTED_SHADOW

Working Capital Shadow Consumption:
CLOSED_RETROSPECTIVE

Working Capital User Visible:
NOT_ENABLED
```

9.0E remains independently enabled/selective.

---

# 106. P0 / P1 / P2

Continue Phase Advancement Rule.

## P0
- future Fact used
- broad/trade mislabel
- wrong balance period
- relation arithmetic/provenance error
- DSO/CCC fabricated
- 9.0E production regression
- unsafe KR basis

## P1
- material causal overclaim
- selector surfaces systematic irrelevant noise
- important relation systematically missed
- industry applicability materially wrong
- Unknown resolution creates false certainty

## P2
- wording polish
- AP low value
- prior-quarter relation absent
- inventory components absent
- unused industry classes

P2 does not block 9.1D if excluded.

---

# 107. Completion report — repository

Include:
- instruction path
- instruction commit
- version
- dependency base
- branch
- implementation
- final branch
- main/operating
- promotion
- working trees
- push
- deviations

---

# 108. Completion report — consumption coverage

Report:
- universe
- eligible
- actually consumed
- suppressed
- N/A
- lagging
- stale/blocked

By:
- Inventory
- Trade AR
- Broad AR
- Trade AP
- Broad AP

---

# 109. Completion report — relation usage

Report:
- AR vs Revenue
- Inventory vs Revenue
- Inventory vs COGS
- AP vs COGS

For each:
- eligible
- selected
- suppressed
- exact/broad semantic
- value-add class

---

# 110. Completion report — PIT/freshness

Report:
- PIT-valid consumed
- future blocked
- lagging
- stale
- violations

Target `0`.

---

# 111. Completion report — semantics

Report:
- broad→trade mislabels
- contract asset→AR
- accrued liability→AP
- AP→DPO
- AR→DSO
- inventory component→total

Targets all `0`.

---

# 112. Completion report — causal guard

Report:
- unsupported causal overclaim count
- allowed cautious interpretations
- rejected examples

Target unsupported causal claims `0`.

---

# 113. Completion report — Unknowns

Report:
- before
- exact resolved
- broad-only narrowed
- still valid
- N/A
- stale
- contradictions

Target contradictions `0`.

---

# 114. Completion report — cash-flow cross-link

Report:
- compatible working-capital + OCF/FCF cases
- selected cross-links
- incompatible periods suppressed
- causal claims
- value add

No 9.0 recomputation.

---

# 115. Completion report — human quality

Report:
- material improvement
- minor improvement
- no change
- degraded

By metric family / industry.

---

# 116. Completion report — numeric binding

Report:
- automatic
- manual
- rejected
- unresolved
- relation arithmetic errors

Targets:
manual/rejected/unresolved/arithmetic = `0`.

---

# 117. Completion report — regression

Report:
- 9.0E
- 9.0D
- 9.0D.1
- run-30
- run-29
- run-28
- run-27
- valuation
- price/RR
- night futures
- fallback/exactly-once
- KRX telemetry

---

# 118. Completion report — natural KR gate

If available:
- production delivery
- AI/fallback
- P0/P1
- KR cash-flow leakage 0
- KRX 16:05
- promotion decision

Keep separate from 9.1C shadow evidence.

---

# 119. Completion report — validation

Report:
- focused
- shadow replay
- binding
- semantic
- causal guard
- quality
- full pytest
- Ruff
- diff
- Knowledge
- docs
- Public Action
- operationId
- schema
- branch CI
- final-main CI if promoted
- operating smoke if promoted

---

# 120. Completion report — safety

Report:
- runtime/user-visible working-capital diff
- 9.0E mode changed: expected NO
- manual Telegram
- manual tasks
- Pilot
- DB
- archive rewrite
- receipt rewrite
- force push
- Production Assist

Targets manual mutation `0`.

---

# 121. Final gate

Must end with:

```text
PHASE_9_1D_READY = YES/NO
PHASE_9_1D_SCOPE = ...
```

Also:

```text
DSO_READY_FOR_IMPLEMENTATION = ...
INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = ...
DPO_READY_FOR_IMPLEMENTATION = ...
CCC_READY_FOR_IMPLEMENTATION = ...
```

If NO:
state exact bounded P0/P1.

If YES:
recommend a selective runtime-shadow-canary scope driven by observed value-add.

---

# 122. Final philosophy

Phase 9.1B made the working-capital evidence correct.

Phase 9.1C must determine whether that evidence is useful.

A correct fact is not automatically a useful daily insight.

The reasoning chain is:

```text
Canonical balance
        ↓
Comparable prior balance
        ↓
Typed growth relation
        ↓
PIT / freshness
        ↓
Exact semantic scope
        ↓
Industry relevance
        ↓
Existing cash-flow / earnings context
        ↓
Cautious interpretation
```

The hardest boundary is semantic precision.

If the Fact is broad AR:
say broad AR.

If it is trade AR:
trade AR is allowed.

Never gain readability by lying about semantic scope.

The second boundary is causality.

```text
AR grew faster than revenue
```

does not prove customers are paying slowly.

```text
Inventory grew faster than revenue
```

does not prove demand is weak.

```text
AP grew faster than COGS
```

does not prove supplier payments were delayed.

Those relations tell the analyst where to look next.
They do not supply the cause.

The third boundary is relevance.

If cash-flow already answers the important question, working-capital evidence should not be appended just because it exists.

If Inventory is highly relevant for a memory company, it may materially improve the analysis.

If broad AP adds little to a software company, suppress it.

Phase 9.1C should therefore produce a selective value-add map, not a maximal working-capital message.

And for today:

Build and validate the dependent branch now.

Leave the 16:05/16:15 operating evidence untouched.

After the natural KR review, promote the clean 9.1A→9.1B→9.1C chain only if production has no blocking P0.

Success is not:

> "Working-capital data is now available."

Success is:

> "We know exactly which working-capital relations improve the investment analysis, which ones do not, and we can prove that the AI preserves semantic precision and avoids causal overclaim."
