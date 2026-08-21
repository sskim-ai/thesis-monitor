# thesis-monitor — Phase 9.1A Work Instruction

## Metadata

- Phase: `9.1A`
- Title: `Working Capital Evidence Architecture`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating at instruction creation: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- Current cash-flow user-visible mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`
- Task type: `ARCHITECTURE / COVERAGE / READ-ONLY EVIDENCE`
- User-visible runtime change in this phase: `0`
- Major objective: determine whether Inventory / Trade AR / Trade AP can be safely canonicalized and compared before implementing DSO / Inventory Days / DPO / CCC.
- Required final gate: `PHASE_9_1B_READY = YES/NO`

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260821-phase-9-1a-working-capital-evidence-architecture.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify latest safe main/operating SHA and clean worktrees.
3. Commit/push this instruction as a **docs-only instruction commit** before implementation.
4. Record:
   - `instruction_path`
   - `instruction_commit_sha`
   - `instruction_version`
5. Create the implementation branch from the latest safe main descendant containing the instruction commit.
6. If main drift exists, reconcile explicitly.
7. No force push / history rewrite.
8. Do not silently edit the instruction after implementation begins. Material changes require a new committed instruction version.

Recommended branch:

`codex/phase-9-1a-working-capital-evidence-architecture`

Completion report must cite the exact instruction commit SHA.

---

# 1. Today’s operating-window rule

Current local planning time is before today’s KR close-monitoring window.

Protected natural window:

- KRX telemetry: `16:05 KST`
- KR primary: `16:15 KST`
- KR backup: `16:55 KST`
- Combined natural review target: after approximately `17:05 KST`

## Critical rule

Phase 9.1A must **not disturb today’s natural KR evidence**.

Therefore:

- architecture / audit / tests / docs work may proceed now
- branch commits/pushes are allowed
- do not change operating runtime before the KR window
- do not change shared runtime/config/schedulers after `15:50 KST`
- do not deploy into operating during `15:50–17:05 KST`
- do not manually trigger KRX/KR tasks
- do not manually send Telegram
- do not wait/sleep merely to observe 16:05 or 16:15

Preferred:
complete the Phase 9.1A branch independently, push it, and leave main/operating untouched until the natural KR review is complete.

If a docs-only instruction/report commit is pushed to a non-operating branch, that is fine.

---

# 2. Phase purpose

Phase 9.0 created the first safe cash-flow chain:

```text
Revenue / Earnings
        ↓
OCF
        ↓
PPE CAPEX
        ↓
FCF
```

The next missing earnings-quality layer is working capital.

This phase does **not** implement CCC.

It first asks whether the backend can safely know:

```text
Inventory
Trade Accounts Receivable
Trade Accounts Payable
        ↓
Point-in-time identity
        ↓
Comparable prior balance
        ↓
Revenue / COGS compatible flow period
        ↓
Balance movement
        ↓
Potential cash-conversion evidence
```

The goal is to define the architecture and actual coverage before any production implementation.

---

# 3. Key principle

Do not start with:

```text
DSO
Inventory Days
DPO
CCC
```

Start with:

```text
Can we trust the raw balance-sheet facts?

Can we compare the right dates?

Can we distinguish trade balances from broad "other" balances?

Can we align point-in-time balances with the correct revenue/COGS period?

Can we say "AR grew faster than revenue" safely?
```

Only after those are closed should advanced working-capital ratios be considered.

---

# 4. Phase 9.1A target metrics

## Tier A — raw point-in-time facts

Primary:

- `inventory`
- `trade_accounts_receivable`
- `trade_accounts_payable`

Supporting:

- `revenue`
- `cost_of_goods_sold` / compatible cost-of-revenue fact
- balance-sheet date
- entity scope
- statement basis
- currency / unit
- filing date
- source occurrence

## Tier B — safe comparable movements

Architecture candidates:

- inventory absolute delta
- inventory YoY %
- trade AR absolute delta
- trade AR YoY %
- trade AP absolute delta
- trade AP YoY %
- revenue YoY %
- COGS YoY %
- AR growth minus revenue growth
- inventory growth minus revenue growth
- inventory growth minus COGS growth
- AP growth minus COGS growth

Only if comparability is safe.

## Tier C — explicitly deferred

- DSO
- Inventory Days
- DPO
- CCC
- cash-conversion cycle score
- working-capital quality score

---

# 5. Hard exclusions

Do NOT implement in Phase 9.1A:

- user-visible working-capital messages
- AI packet integration
- fallback integration
- Public Action fields
- public snapshot changes
- DSO
- Inventory Days
- DPO
- CCC
- working-capital score
- arbitrary materiality thresholds
- ROIC
- ROIC proxy
- new valuation multiples
- working-capital-triggered thesis state mutation
- warning lifecycle mutation
- DB assessment mutation
- KR OpenDART cash-flow period recovery
- KRX breadth integration
- paid provider
- new paid API
- manual Scheduled Task
- manual Telegram
- Pilot mutation
- Production Assist ON

---

# 6. Source policy

Use existing official/free source architecture only.

Preferred:

- SEC EDGAR / official XBRL for US
- OpenDART official financial statements for KR
- existing validated foreign-issuer official paths

Do not add a new commercial financial-data provider.

Stored raw evidence/cache first.

Live official read-only provider calls are allowed only if needed for coverage verification.

Report all provider call counts.

---

# 7. Existing architecture first

Do not create a parallel working-capital truth store.

Extend or reuse:

- `financial-lineage-v2`
- `financial-quality-taint-v2`
- canonical financial Fact architecture
- entity / period / statement-basis validation
- source occurrence identity
- existing unit/currency normalization
- Phase 9.0 canonical financial evidence patterns

Working capital must be another canonical financial fact family, not a separate analytics shortcut.

---

# 8. Active universe

Use the actual active monitored universe from repository state.

Known recent universe size:

- total: 20
- KR: 7
- US/foreign: 13

Do not hard-code this.

Generate a fresh read-only universe snapshot and report actual counts.

---

# 9. Point-in-time fact model

Inventory / AR / AP are balance-sheet facts.

Each must have at minimum:

```text
metric
value
currency
unit
balance_date

fiscal_year
fiscal_quarter if determinable

entity_scope
statement_basis

source_provider
source_document
filing_date
source_occurrence_id
raw_sha

semantic_mapping
quality
eligibility
cautions
```

Do not model them as flow-period metrics.

---

# 10. Balance date is primary

The canonical time identity for Inventory / AR / AP is:

`balance_date`

not:

- filing date
- report publication date
- quarter label alone

Filing date is still required for PIT availability.

---

# 11. Comparative balance architecture

For working-capital quality, prefer:

```text
current balance date
vs
prior-year comparable balance date
```

Example concept:

Q2 2026 balance
vs
Q2 2025 balance

Do not default to:

Q2 2026
vs
FY2025

and call it YoY.

---

# 12. Prior-quarter relation

Prior-quarter comparison may be useful as a secondary relation.

But:

- do not replace YoY comparable
- seasonality can be material
- do not call QoQ balance movement a structural cash-conversion trend

Architecture should support it only if exact prior-quarter balance is safe.

9.1B may defer it if coverage/meaning is weak.

---

# 13. Fiscal-calendar safety

Do not assume calendar quarters.

Important for non-calendar issuers.

Comparability must follow:

- issuer fiscal year
- actual balance date
- fiscal-quarter context if available

A 2026-05-xx balance may be a valid quarter-end for one issuer.

---

# 14. Restatement / comparative columns

If current filing presents restated prior comparative balances:

- preserve source version
- prefer authoritative restated comparable
- do not mix an old original prior balance with a newer restated current comparative when unsafe

Document version-selection policy.

---

# 15. Inventory semantic contract

Canonical inventory should represent total inventories only when clearly mapped.

Do not mix:

- inventories
- raw materials only
- finished goods only
- work in process only

into a single total unless the source explicitly supports aggregation and the aggregation rule is proven safe.

Preferred canonical metric:

`inventory_total`

Component facts may remain separately available but are out of initial scope unless needed for semantic verification.

---

# 16. Inventory exclusions

Do not treat the following as generic inventory without explicit business/financial semantic support:

- investment property
- biological assets
- securities inventory
- contract assets
- prepaid expenses

---

# 17. Trade AR semantic contract

The initial preferred metric is:

`trade_accounts_receivable`

or repository-equivalent.

Need to distinguish:

- trade receivables
- accounts receivable, net
- total receivables
- loans receivable
- financing receivables
- other receivables
- contract assets

Do not silently map broad "other receivables" to trade AR.

---

# 18. AR fallback policy

If only a broader accounts-receivable metric is safely available:

Architecture may classify it as:

`accounts_receivable_broad`

but must not silently call it trade AR.

9.1A must decide whether:

A. broad AR is acceptable as a separate secondary metric

or

B. initial 9.1B uses trade AR only.

This must be an explicit final decision.

---

# 19. Trade AP semantic contract

Preferred:

`trade_accounts_payable`

Distinguish:

- trade payables
- accounts payable
- total payables
- accrued liabilities
- accrued expenses
- other payables
- contract liabilities
- debt

Do not map accrued liabilities broadly to trade AP.

---

# 20. AP fallback policy

As with AR, decide explicitly whether:

- broad AP may exist as a separate metric
- or 9.1B initial core requires trade AP only

Do not silently broaden semantics for coverage.

---

# 21. Net values / allowances

If AR is reported net of allowance:

preserve source semantic.

Do not attempt to gross it up without evidence.

If one period is gross and another net:

do not compare as identical AR.

---

# 22. Current vs noncurrent

If source distinguishes current/noncurrent receivables/payables:

- preserve scope
- do not sum automatically unless the semantic mapping explicitly defines total trade balance
- report whether initial working-capital architecture uses current only or total trade balance

This must be a final architecture decision.

---

# 23. Entity scope

All comparable balances must match:

- consolidated vs standalone
- issuer/entity scope

Do not compare CFS inventory to OFS prior inventory.

---

# 24. Currency and unit

Same comparison requires compatible currency and normalized units.

Do not use share-price currency.

Do not convert currencies merely to improve coverage.

Within the same issuer, if financial reporting currency changed, treat carefully and fail closed unless comparable basis is explicit.

---

# 25. PIT availability

A historical/replay working-capital fact may be used only if:

`filing/publication available_at <= packet/replay cutoff`

Even though 9.1A is architecture-only, design PIT metadata now so later consumption can remain safe.

---

# 26. Revenue comparison alignment

For:

`AR growth vs Revenue growth`

the revenue comparison must use a compatible flow period.

Preferred:

- YTD revenue vs prior-year comparable YTD revenue
- FY revenue vs prior FY revenue
- QTD revenue vs prior-year comparable QTD revenue

Do not compare:

- Q2 point-in-time AR YoY
with
- unrelated TTM revenue growth

unless the architecture explicitly supports that relation and documents why.

Initial recommendation: use the filing-period compatible YoY flow.

---

# 27. Inventory comparison alignment

Potential relations:

- inventory growth vs revenue growth
- inventory growth vs COGS growth

Architecture must determine which is more economically appropriate by industry/data availability.

Do not force COGS if the source semantic is weak.

Do not force revenue if inventory economics are not meaningfully linked.

---

# 28. AP comparison alignment

Trade AP often relates more directly to purchasing/COGS than revenue.

But purchases are usually not directly available.

Do not claim DPO-like interpretation from AP/COGS without implementing DPO.

For 9.1A/9.1B:

AP balance movement can be a contextual working-capital fact.

`AP growth vs COGS growth` may be an optional comparative relation if COGS semantics are safe.

Do not label it supplier-payment-days change.

---

# 29. Safe growth formula

For positive balance values:

```text
growth = (current - prior) / prior
```

But architecture must fail closed if prior denominator is:

- zero
- missing
- economically nonsensical
- incompatible

Do not convert missing prior to zero.

---

# 30. Negative / unusual balances

Inventory / trade AR / trade AP are normally nonnegative, but do not assume blindly.

If source-normalized balance is negative:

- investigate semantic/source context
- do not calculate a standard growth percentage automatically
- classify quality/eligibility

---

# 31. Absolute delta

Even when percentage growth is unsafe, an absolute balance delta may still be valid if:

- both values are comparable
- same currency/unit
- same scope

Architecture may preserve:

`current - prior`

as a deterministic fact.

---

# 32. Relative growth relations

Safe architecture may compute exact difference in percentage points:

```text
AR growth - Revenue growth
Inventory growth - Revenue growth
Inventory growth - COGS growth
AP growth - COGS growth
```

Do not convert this automatically into:

- good
- bad
- warning
- strengthening
- weakening

It is a relation Fact.

---

# 33. No arbitrary warning threshold

Do not create:

- AR exceeds revenue growth by 10% → warning
- inventory exceeds revenue by 20% → bad

unless an existing documented industry contract already has such a threshold.

Initial architecture should preserve relation, not verdict.

---

# 34. Zero-crossing / denominator safety

If revenue/COGS prior period is zero or negative:

do not produce a standard growth comparison.

If AR/inventory/AP prior balance is zero:

percentage growth unavailable.

Absolute delta may remain safe.

---

# 35. Canonical relation taxonomy

Propose a minimal typed relation taxonomy.

Examples:

```text
BALANCE_INCREASED
BALANCE_DECREASED
BALANCE_UNCHANGED

AR_GROWTH_GT_REVENUE_GROWTH
AR_GROWTH_LT_REVENUE_GROWTH

INVENTORY_GROWTH_GT_REVENUE_GROWTH
INVENTORY_GROWTH_LT_REVENUE_GROWTH

INVENTORY_GROWTH_GT_COGS_GROWTH
INVENTORY_GROWTH_LT_COGS_GROWTH

AP_GROWTH_GT_COGS_GROWTH
AP_GROWTH_LT_COGS_GROWTH
```

Actual naming follows repository conventions.

Avoid interpretive labels like:

`POOR_CASH_CONVERSION`.

---

# 36. Comparable-period relation identity

Every derived relation must retain:

- current balance Fact ID
- prior balance Fact ID
- current flow Fact ID if used
- prior flow Fact ID if used
- formulas
- relation type
- currency/unit compatibility
- period/basis comparability

No relation without input Fact refs.

---

# 37. Potential contract

Propose or finalize a contract such as:

`working-capital-evidence-v1`

Conceptual structure:

```text
ticker
industry

inventory:
  current_fact
  prior_comparable_fact
  absolute_delta
  yoy_pct
  status

trade_ar:
  ...

trade_ap:
  ...

revenue_comparison:
  current
  prior
  yoy_pct

cogs_comparison:
  ...

relations:
  - type
  - input_fact_ids
  - value/ppt_difference
  - eligibility

applicability
quality
cautions
```

9.1A may finalize schema without production implementation.

---

# 38. Source-occurrence identity

For each raw balance Fact:

preserve:

- exact source document
- exact source occurrence
- raw source semantic/tag
- balance date
- filing date
- unit
- raw SHA if existing architecture supports it

Do not store only the normalized final number.

---

# 39. SEC mapping audit

For US/foreign SEC-supported issuers:

Audit actual tags/semantics for:

- inventory
- AR
- AP
- revenue
- COGS / cost of revenue

Do not create a huge guessed tag allowlist.

Prefer actual observed tags from monitored universe + validated standard taxonomy.

Issuer extension tags require explicit statement-context evidence.

---

# 40. OpenDART mapping audit

For KR:

Balance-sheet point-in-time context may differ from the cash-flow-period problem.

Audit separately.

Do not assume the Phase 9.0 OpenDART cash-flow blockage means balance-sheet facts are also blocked.

Need to determine actual safe coverage for:

- inventory
- trade AR
- trade AP
- revenue
- COGS if available

CFS/OFS rules remain strict.

---

# 41. KR CFS/OFS priority

For KR companies with consolidated statements:

CFS is preferred for group-level working-capital analysis.

OFS fallback must be explicitly classified and not mixed with CFS revenue/COGS.

---

# 42. Insurance / financial-industry applicability

Korean Re / financial-like subjects must not be forced into generic industrial working-capital analysis.

For insurance/reinsurance:

- inventory typically not meaningful
- trade AR/AP may not reflect core economics
- generic working-capital relation should be N/A or context-only

Use industry applicability contract.

---

# 43. Memory / semiconductor applicability

For memory/semiconductor:

Inventory is often PRIMARY.

AR:
SECONDARY / context-dependent.

AP:
SECONDARY / context-dependent.

Potential interpretation later:

inventory vs revenue/COGS
+
ASP/margin/cycle

But 9.1A does not implement investment prose.

---

# 44. Automotive applicability

Inventory:
PRIMARY.

AR:
SECONDARY.

AP:
SECONDARY/context.

Need to distinguish manufacturing working capital from financial-subsidiary receivables if source taxonomy mixes them.

If mixed entity segmentation cannot be resolved, caution or block the relation.

---

# 45. Steel / materials applicability

Inventory:
PRIMARY.

Trade AR:
PRIMARY/SECONDARY.

Trade AP:
SECONDARY.

Working capital can be significant due to raw materials, finished goods, and cycle pricing.

Do not infer demand weakness from inventory growth alone.

---

# 46. Industrial / electrical equipment

LS ELECTRIC-like businesses:

Trade AR:
PRIMARY.

Inventory:
PRIMARY/SECONDARY.

Trade AP:
SECONDARY.

Order/project conversion can make receivables important.

Contract assets are not automatically trade AR.

---

# 47. Aerospace / defense / project businesses

Hanwha Aerospace-like businesses:

Receivables and contract assets can differ materially.

Do not merge contract assets into trade AR.

If working-capital economics require contract assets, mark as a future extension rather than broadening trade AR incorrectly.

---

# 48. Transport / logistics

Hyundai Glovis-like businesses:

AR:
SECONDARY/PRIMARY depending actual coverage.

Inventory may be less primary than in manufacturing.

AP:
context.

Use actual industry matrix; do not force inventory as primary.

---

# 49. Cloud / platform

GOOGL-like platform:

Trade AR may matter.
Inventory often not primary.
AP may be less decision-relevant.

Working-capital user-visible relevance may be limited.

Architecture can support facts without marking them PRIMARY.

---

# 50. Software / services

IBM-like:

AR may matter.
Inventory often secondary.
AP context.

Need to avoid turning ordinary receivable movement into a strong earnings-quality conclusion without services/software context.

---

# 51. HPC / data-center infrastructure

CORZ / HUT / WULF-like:

AR/payables can matter, but CAPEX/build-out and financing may dominate cash flow.

Working-capital metrics are secondary to OCF/CAPEX/FCF unless actual evidence shows materiality.

No automatic user-visible priority.

---

# 52. Biotech / pre-profit

RXRX-like:

Inventory/AR/AP may have limited investment relevance.

Cash burn/runway remains more important.

Working-capital facts can be canonical but applicability may be CONTEXT_ONLY or NOT_PRIMARY.

---

# 53. Stablecoin / financial-like platform

CRCL-like business requires caution.

Receivables/payables may not map cleanly to industrial working capital.

Use existing industry framework / actual business model.

Do not force generic AR/AP quality reasoning.

---

# 54. Foreign issuers

Issuer-level balance-sheet working-capital facts can be used without ADR ratio when:

- statement basis
- financial currency
- issuer identity

are safe.

Per-share/security-level calculations are irrelevant to 9.1A.

---

# 55. Working-capital evidence vs thesis status

No derived relation may automatically set:

- strengthened
- weakened
- invalidated

Working-capital evidence is a validation signal.

Interpretation comes later.

---

# 56. Working-capital evidence vs cash-flow evidence

Future reasoning may connect:

```text
AR / inventory movement
→ OCF conversion
```

But 9.1A must not assume causality.

Example:

OCF down + AR up

can be consistent with weaker collection, but other factors may exist.

Architecture should permit later cross-fact reasoning without encoding cause now.

---

# 57. Earnings-quality future consumption

Design for a future consumption layer where safe relations can support statements such as:

- revenue grew faster than trade AR
- trade AR grew faster than revenue
- inventory increased faster than revenue/COGS
- working-capital balances moved against cash conversion

But the backend relation remains factual/typed.

No user-visible prose in 9.1A.

---

# 58. No DSO architecture shortcut

Do not say:

"we already have AR and revenue, therefore DSO is ready."

DSO additionally requires:

- average AR
- correct flow duration
- actual period days
- trade AR semantic
- period alignment

9.1A may document prerequisites but not implement.

---

# 59. No Inventory Days shortcut

Requires:

- average inventory
- safe COGS
- duration days

Not in 9.1A implementation.

---

# 60. No DPO shortcut

Requires:

- average trade AP
- safe denominator policy
- ideally purchases, often unavailable

COGS proxy limitations must be explicit.

Not implemented.

---

# 61. No CCC shortcut

CCC requires all safe components.

Keep:

`CCC = DEFERRED`

unless 9.1A evidence surprisingly proves all prerequisites broadly; even then only architecture recommendation, no implementation.

---

# 62. Coverage matrix

Generate for every active monitored ticker:

```text
Ticker
Industry
Source
Latest formal balance date

Inventory current
Inventory prior comparable
Inventory YoY eligible

Trade AR current
Trade AR prior comparable
Trade AR YoY eligible

Trade AP current
Trade AP prior comparable
Trade AP YoY eligible

Revenue comparable
COGS comparable

AR vs Revenue relation eligible
Inventory vs Revenue relation eligible
Inventory vs COGS relation eligible
AP vs COGS relation eligible

Industry applicability
Block reasons
```

Status vocabulary:

- ELIGIBLE
- PARTIAL
- BLOCKED
- NOT_APPLICABLE

---

# 63. Coverage cannot be inflated

A raw field existing is not enough.

Eligible requires:

- semantic identity
- point-in-time identity
- source occurrence
- currency/unit
- entity scope
- statement basis
- prior comparable
- PIT metadata if required for future replay

---

# 64. Coverage drift audit

Compare architecture expectation vs actual observed source evidence.

Classify:

- STRONG
- SELECTIVE
- WEAK
- NOT_APPLICABLE

Do not force a specific numeric coverage target.

---

# 65. Representative lineage proofs

Create deep proofs from the actual monitored universe for at least:

1. US industrial/operating company
2. memory/semiconductor
3. automotive
4. capital-intensive/HPC
5. biotech negative-control
6. KR non-financial industrial
7. insurance N/A
8. foreign issuer if source path differs materially
9. non-calendar fiscal issuer

One ticker may satisfy multiple classes only if documented.

---

# 66. Each lineage proof

Show:

```text
source filing
source occurrence
semantic mapping
balance date
filing date
currency/unit
entity scope
statement basis

current Fact
prior comparable Fact

derived delta
derived growth if safe

flow comparison facts
typed relation eligibility
```

No hidden inference.

---

# 67. Source quality conflicts

If two comparable official occurrences disagree:

Use existing conflict rules.

Only create numeric conflict when:

- same semantic
- same period/date
- same basis
- compatible source version

Do not call different broad-vs-trade receivable metrics a numeric conflict.

---

# 68. Balance-sheet amendment handling

If amended/restated filing changes a balance:

- source version must be tracked
- latest authoritative restated comparable preferred
- derived relation inputs must point to the chosen version

---

# 69. PIT design

Even though no runtime consumption occurs now, every architecture Fact/relation should support future PIT replay.

Need:

`source_available_at`

or equivalent.

A later historical packet must not see future-restated working-capital data.

---

# 70. Freshness concept

Point-in-time working-capital data is normally refreshed at formal balance-sheet filings.

Do not invent 30/60/90-day freshness thresholds.

Future currentness should align with latest validated formal balance-sheet period.

If newer formal balance sheet exists but working-capital field is blocked, older balance should not automatically become current substitute.

---

# 71. Official provisional earnings boundary

If a newer provisional earnings release has revenue/operating income but no balance sheet:

working-capital canonical balance remains latest formal.

Do not call the old balance "current quarter inventory" for the provisional period.

Future consumption must distinguish:

`formal-lagging-provisional`.

Reuse 9.0C freshness philosophy.

---

# 72. Relation to Phase 9.0E

9.1A must not change current selective FCF user-visible feature.

Do not touch:

- `cash-flow-user-visible-v1`
- 9.0E selector
- kill switch
- FCF AI/fallback rendering

except read-only regression tests if architecture modules share imports.

Today’s KR natural run must remain clean evidence for the current 9.0E operating baseline.

---

# 73. Today’s natural KR expected checks — do not execute manually

After approximately 17:05 KST, separate review should inspect:

- KR cash-flow user-visible injection = 0
- KR OpenDART blocked leakage = 0
- shared runtime regression = 0
- actual AI/fallback delivery mode
- validator/runtime quality
- price/RR/supply/valuation integrity
- exactly-once
- KRX 16:05 telemetry result

Phase 9.1A does not need to wait for this review.

---

# 74. 15:50 freeze

From `15:50 KST` until the KR natural cycle is complete:

Do not:

- merge 9.1A to main
- change operating checkout
- restart API
- change runtime feature modes
- modify schedules
- deploy shared runtime code

Branch development may continue locally/remotely if it cannot affect operating.

---

# 75. Promotion policy for 9.1A

Preferred today:

- instruction commit: push
- implementation/report branch: push
- **no main/operating promotion before 17:05 natural review**

After natural review:

If:
- no production P0
- 9.1A tests PASS
- 9.1A runtime user-visible diff = 0
- no shared-runtime risk

then main promotion may be done as a separate safe completion step.

If Codex task finishes before 17:05:

report:

`PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`

This is not failure.

---

# 76. Runtime diff requirement

Phase 9.1A should primarily consist of:

- architecture docs
- evidence/audit scripts
- schemas/contracts not wired into production
- fixtures/tests
- coverage reports

Production user-visible behavior diff:

`0`

If a code change enters a production import path, explain why and prove no behavior change.

---

# 77. Evidence generator

Recommended:

`scripts/phase9_1a_working_capital_evidence.py`

Requirements:

- read-only
- deterministic from stored evidence when possible
- no production mutation
- no DB mutation
- provider calls counted
- output sanitized reports/JSON

Do not auto-run from production service.

---

# 78. Proposed canonical contract decision

By end of phase, decide exact names for:

- inventory metric
- trade AR metric
- trade AP metric
- broader AR/AP if supported
- comparable-balance relation
- growth relation
- flow comparison relation

Do not leave naming ambiguous.

---

# 79. Trade vs broad AR decision gate

Mandatory final decision:

`AR_INITIAL_SCOPE = TRADE_ONLY / TRADE_PLUS_SEPARATE_BROAD / OTHER`

State reason.

Do not silently collapse.

---

# 80. Trade vs broad AP decision gate

Mandatory final decision:

`AP_INITIAL_SCOPE = TRADE_ONLY / TRADE_PLUS_SEPARATE_BROAD / OTHER`

State reason.

---

# 81. Current vs total balance decision

Mandatory:

- use current balances only?
- total trade balances?
- issuer-reported net AR?

State exact policy for 9.1B.

---

# 82. Inventory policy decision

Mandatory:

- total inventory only
- component aggregation allowed or not
- restatement policy

---

# 83. Revenue alignment decision

Mandatory:

Define exact compatible revenue period rule for:

`AR growth vs revenue growth`

and inventory relation where used.

---

# 84. COGS alignment decision

Mandatory:

Define exact COGS/cost-of-revenue semantic requirements for:

- inventory vs COGS
- AP vs COGS

If coverage is weak, 9.1B can defer COGS-relative relations.

---

# 85. 9.1B recommended minimal scope

The default preferred next implementation is:

```text
Canonical Inventory / Trade AR / Trade AP
+
Prior-year comparable balances
+
Absolute deltas
+
Safe YoY growth
+
Selective AR-vs-Revenue / Inventory-vs-Revenue relations
```

Potentially defer:

- COGS-relative relations
- broad AR/AP
- prior-quarter relations

if evidence is weak.

The final 9.1B scope must be evidence-driven.

---

# 86. No lowest-common-denominator design

If AP coverage is weak but Inventory/AR are strong:

Do not block the entire working-capital core.

Selective metric implementation is allowed.

Possible 9.1B scope:

`SELECTIVE_INVENTORY_AR_CORE`

if evidence supports that better than full AR/AP.

---

# 87. Coverage by metric, not just ticker

A ticker may be:

- inventory eligible
- AR eligible
- AP blocked

Do not force one all-or-nothing working-capital status.

---

# 88. Industry applicability matrix

Create matrix for actual supported industry taxonomy:

```text
Industry
Inventory
AR
AP
AR-vs-Revenue
Inventory-vs-Revenue
Inventory-vs-COGS
AP-vs-COGS
```

Classify:

- PRIMARY
- SECONDARY
- CONTEXT_ONLY
- NOT_APPLICABLE

Do not invent irrelevant cross-industry metrics.

---

# 89. Cash-flow cross-link readiness

For tickers with Phase 9.0 FCF:

Audit whether working-capital facts can later explain/qualify OCF/FCF.

Do not infer cause.

Classify future cross-link:

- HIGH_VALUE
- MEDIUM_VALUE
- LOW_VALUE
- NOT_APPLICABLE

No score.

---

# 90. User-visible future design — architecture only

Sketch how future AI could use safe relations without numeric dumping.

Examples conceptually:

```text
매출 증가율보다 매출채권 증가율이 높았다.
→ 회수 속도와 현금전환을 확인할 필요.
```

```text
재고 증가가 매출 증가보다 빨랐다.
→ 수요/제품믹스/사이클과 함께 확인.
```

But do not implement user-visible prose.

---

# 91. No causal overclaim

Architecture must explicitly prohibit:

- AR up → customers not paying
- inventory up → demand collapse
- AP up → liquidity stress

without additional evidence.

Working-capital facts are signals, not causes.

---

# 92. Negative-control industries

Must demonstrate correct suppression for:

- insurance/reinsurance
- businesses where trade AR/AP semantics do not reflect operating working capital
- biotech if not material
- financial-like platforms where industrial relation is inappropriate

---

# 93. KR evidence objective

Because KR cash-flow period remains blocked, working-capital architecture provides an opportunity to recover useful earnings-quality evidence from point-in-time statements if safe.

But:

do not lower standards to get KR coverage.

Need to prove:

- balance dates
- CFS/OFS
- semantic identity
- comparable prior-year balance

independently.

---

# 94. Provider-call policy

Stored evidence first.

If live official calls are necessary:

Report:

```text
Provider
Requests
Success
Failure
Cache hits
Purpose
```

No brute-force broad crawling.

No paid source.

---

# 95. Required reports

Create:

1. `docs/architecture/WORKING_CAPITAL_EVIDENCE.md`
2. `docs/reports/20260821-phase9-1a-provider-coverage.md`
3. `docs/reports/20260821-phase9-1a-active-universe-coverage.md`
4. `docs/reports/20260821-phase9-1a-inventory-lineage-audit.md`
5. `docs/reports/20260821-phase9-1a-receivables-lineage-audit.md`
6. `docs/reports/20260821-phase9-1a-payables-lineage-audit.md`
7. `docs/reports/20260821-phase9-1a-comparable-period-audit.md`
8. `docs/reports/20260821-phase9-1a-industry-applicability.md`
9. `docs/reports/20260821-phase9-1a-representative-proofs.md`
10. `docs/reports/20260821-phase9-1a-readiness.md`

Recommended JSON:

- `docs/reports/20260821-phase9-1a-coverage.json`
- `docs/reports/20260821-phase9-1a-readiness.json`

---

# 96. Coverage JSON

Recommended per ticker:

```text
ticker
industry
source
latest_balance_date

inventory:
  status
  current_fact
  prior_fact
  yoy_eligible

trade_ar:
  ...

trade_ap:
  ...

revenue:
  comparable_status

cogs:
  comparable_status

relations:
  ar_vs_revenue
  inventory_vs_revenue
  inventory_vs_cogs
  ap_vs_cogs

industry_applicability
block_reasons
```

No secrets/raw tokens.

---

# 97. Representative proof report

For each representative class, show:

- exact source
- tags/semantic
- balance date
- prior comparable
- entity scope
- currency/unit
- derived movement
- relation eligibility
- reason for blocked fields

No user-visible recommendation.

---

# 98. Test design — raw facts

Required tests:

- inventory total mapped correctly
- inventory component not silently treated as total
- trade AR vs other receivable separation
- trade AP vs accrued liabilities separation
- current/noncurrent scope
- CFS/OFS
- currency/unit
- negative unusual value fails safe
- missing != zero

---

# 99. Test design — comparable dates

Required:

- same fiscal quarter prior-year PASS
- FY vs prior FY PASS
- Q2 vs prior FY-end as YoY FAIL
- non-calendar fiscal PASS
- restated prior comparative PASS
- incompatible basis FAIL
- different currency/unit FAIL

---

# 100. Test design — growth

Required:

- positive prior denominator
- zero prior denominator unavailable
- missing prior unavailable
- absolute delta still safe where applicable
- percentage relation carries Fact IDs
- no arbitrary warning label

---

# 101. Test design — flow alignment

Required:

- AR YoY with comparable YTD revenue PASS
- AR with unrelated TTM revenue relation FAIL
- inventory with compatible revenue PASS
- inventory/COGS only when COGS semantic safe
- AP/COGS only when AP/COGS safe
- no DSO/DPO inference

---

# 102. Test design — provisional lag

Required:

formal balance Q1
+
provisional earnings Q2
→ Q1 working-capital balance not called Q2 current balance.

Future consumption state:
formal-lagging-provisional.

---

# 103. Test design — industry

Required:

- memory inventory primary
- insurance generic WC N/A
- biotech no forced primary working-capital
- industrial AR/inventory applicable
- project contract asset not trade AR
- foreign issuer works without ADR ratio

---

# 104. Regression — 9.0E

Must verify no regression to current selective cash-flow rollout:

- user-visible selector unchanged
- kill switch unchanged
- AI/fallback parity unchanged
- TSLA baseline consistency unchanged
- KR cash-flow injection remains 0
- 9.0D canary unchanged

---

# 105. Regression — existing runtime

Preserve:

- Phase 8.5.5 / .1 / .2
- run-27 / 28 / 29
- current PBR ownership
- CORZ typed valuation
- dynamic price/RR
- confirmation lifecycle
- night futures
- fallback
- exactly-once/receipt
- KRX telemetry

---

# 106. Full validation

Required:

- focused 9.1A evidence tests PASS
- coverage generator deterministic PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- documentation links PASS
- exact implementation SHA CI Test/Lint PASS

If branch is not promoted before natural KR window, a final-main CI is not required yet; report branch CI and promotion-deferred state clearly.

---

# 107. P0 / P1 / P2

Continue Phase Advancement Rule.

## P0 examples
- wrong balance period
- wrong trade-vs-other semantic mapping
- CFS/OFS mixing
- future filing in historical relation
- false current balance from provisional-only period
- fabricated DSO/CCC
- 9.1A shared code breaks 9.0E runtime

## P1 examples
- important eligible AR/inventory systematically missed due to architecture bug
- industry applicability materially wrong
- broad receivable/payable mapping creates misleading relation

## P2 examples
- optional AP relation weak
- report formatting
- prior-quarter relation deferred
- component inventory breakdown deferred

P2 does not block 9.1B.

---

# 108. PHASE_9_1B_READY gate

Must set exactly:

`PHASE_9_1B_READY = YES` or `NO`

## YES requires

- canonical Inventory semantic closed
- canonical AR semantic closed for chosen initial scope
- canonical AP semantic closed or explicitly deferred/selective
- point-in-time identity closed
- comparable prior-year balance rule closed
- entity/currency/unit rules closed
- coverage matrix complete
- representative US evidence audited
- representative KR evidence audited
- financial-industry exclusion audited
- non-calendar fiscal audited
- relation formulas defined
- no DSO/CCC leakage
- open P0 = 0
- open material P1 = 0
- CI PASS
- runtime user-visible diff = 0

100% metric/ticker coverage is not required.

---

# 109. PHASE_9_1B_SCOPE decision

Must output one evidence-based scope.

Examples:

```text
INVENTORY_AR_AP_CANONICAL_CORE
INVENTORY_AR_CANONICAL_CORE_AP_SELECTIVE
SELECTIVE_WORKING_CAPITAL_CANONICAL_CORE
```

Do not force a predefined one if evidence suggests another.

The scope must state:

- raw metrics
- comparable deltas
- YoY growth
- which cross-growth relations are included
- which relations are deferred

---

# 110. DSO / CCC final phase decision

At end of 9.1A report:

```text
DSO_READY_FOR_IMPLEMENTATION = YES/NO/DEFER
INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = YES/NO/DEFER
DPO_READY_FOR_IMPLEMENTATION = YES/NO/DEFER
CCC_READY_FOR_IMPLEMENTATION = YES/NO/DEFER
```

Expected default is DEFER unless evidence is unexpectedly strong.

These do not block 9.1B canonical raw-balance core.

---

# 111. Promotion decision after KR natural window

If 9.1A finishes before 17:05:

do not wait idly.

Push branch and reports.

State:

`PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`

After KR review, promotion can proceed if:

- KR production P0 = 0
- KRX/AI shared runtime shows no relevant regression
- 9.1A runtime behavior diff = 0
- full tests/CI PASS
- main ancestry clean

Do not combine promotion with an unreviewed natural P0.

---

# 112. If 9.1A finishes after the natural window

Then:

- inspect whether the separate KR review has already identified a P0
- if no blocking P0 and 9.1A is zero-runtime-diff, normal clean promotion is allowed
- if KR P0 exists, preserve 9.1A branch evidence and repair the P0 before main promotion if shared architecture risk exists

---

# 113. Main/operating promotion

When allowed:

- `git fetch origin`
- verify main drift
- clean fast-forward if linear
- operating sync
- API restart only if required
- health PASS
- task schedules unchanged
- KRX telemetry unchanged
- Production Assist OFF

User-visible behavior remains unchanged.

---

# 114. No operating feature enablement

9.1A has no feature mode to enable.

Do not touch the current cash-flow user-visible operating mode.

Keep current 9.0E mode exactly as configured.

---

# 115. Work-instruction compliance

Completion report must include:

- instruction path
- instruction commit SHA
- instruction version
- implementation base
- deviations YES/NO
- exact reason/safety impact if deviated

---

# 116. Complete report bundle

Create:

`docs/reports/20260821-phase9-1a-complete-report.md`

Recommended:

`docs/reports/20260821-phase9-1a-complete-report.json`

And one downloadable bundle:

`20260821-phase9-1a-complete-report-bundle.zip`

ZIP should contain sanitized reports/JSON only.

Report SHA-256.

Push sanitized reports to the Phase 9.1A branch.

---

# 117. Completion report — repository

Report:

- instruction commit
- branch
- base
- implementation commit
- final branch SHA
- main/operating SHA
- promotion YES/NO/deferred
- reason
- working trees
- push

---

# 118. Completion report — active universe

Report:

- total
- KR
- US/foreign
- industry distribution

Use actual runtime state.

---

# 119. Completion report — source/provider

Report:

- SEC stored/live
- OpenDART stored/live
- foreign official paths
- request counts
- cache hits
- failures
- new paid providers = 0

---

# 120. Completion report — Inventory

Report:

- semantic definition
- current coverage
- prior comparable coverage
- YoY eligible
- blocked reasons
- component policy

---

# 121. Completion report — AR

Report:

- chosen initial semantic
- trade/broad policy
- current coverage
- prior comparable
- YoY
- AR-vs-revenue relation coverage
- blocked reasons

---

# 122. Completion report — AP

Report:

- chosen semantic
- trade/broad policy
- coverage
- comparable
- relation eligibility
- blocked reasons

---

# 123. Completion report — Revenue/COGS alignment

Report:

- revenue relation coverage
- COGS relation coverage
- deferred relations
- period rules

---

# 124. Completion report — KR

Report:

- balance-sheet working-capital coverage
- CFS/OFS handling
- what is safe despite KR cash-flow period gap
- unresolved KR working-capital limitations

---

# 125. Completion report — industry applicability

Summarize:

- memory
- semiconductor
- automotive
- steel/materials
- industrial
- transport
- cloud/software
- HPC
- biotech
- insurance
- special financial-like businesses

No generic one-size-fits-all.

---

# 126. Completion report — representative proofs

List proof tickers/classes and:

- current balance
- prior comparable
- Fact IDs
- source occurrence
- relation
- status

---

# 127. Completion report — advanced ratios

Report:

- DSO readiness
- Inventory Days readiness
- DPO readiness
- CCC readiness

with reasons.

---

# 128. Completion report — validation

Report:

- focused
- generator
- full pytest
- Ruff
- diff
- Knowledge
- docs
- Public Action
- operationId
- schema
- CI

---

# 129. Completion report — operating safety

Report:

- runtime diff
- user-visible diff
- 9.0E mode unchanged
- Telegram manual
- task manual
- Pilot
- DB
- archive rewrite
- API
- schedules
- Production Assist

Targets manual mutation = 0.

---

# 130. Completion report — severity

Report:

- Open P0
- Open material P1
- P2 backlog

---

# 131. Final gate

Must end with:

```text
PHASE_9_1B_READY = YES/NO
PHASE_9_1B_SCOPE = ...
```

If NO:

state exact bounded blocker.

If YES:

recommend:

`Phase 9.1B — Canonical Working Capital Core`

with exact evidence-driven scope.

---

# 132. Parallel-track state

Report separately:

```text
9.0E user-visible cash-flow natural proof:
PENDING / actual latest state

KRX telemetry:
actual latest state

Natural AI-Assisted Delivery:
actual latest state
```

Do not make any of these automatically block 9.1B unless they contain a relevant P0.

---

# 133. Final philosophy

Working capital is where many apparently good earnings stories become more or less credible.

But the system must not jump from:

```text
AR increased
```

to:

```text
cash collection deteriorated
```

without the right comparison.

The correct chain is:

```text
Exact balance-sheet Fact
        ↓
Point-in-time identity
        ↓
Prior comparable balance
        ↓
Compatible revenue / COGS period
        ↓
Deterministic relation
        ↓
Industry context
        ↓
Later investment interpretation
```

Phase 9.1A is only responsible for the evidence architecture.

Therefore:

- inventory is not automatically bad when it rises
- AR is not automatically bad when it rises
- AP is not automatically liquidity stress when it rises
- contract assets are not trade AR
- accrued liabilities are not automatically trade AP
- quarterly filing labels are not enough to infer comparable periods
- non-calendar issuers require fiscal-period awareness
- CFS and OFS cannot be mixed
- missing prior balances are not zero
- broad receivables/payables must not be silently renamed as trade balances
- DSO/CCC must not be fabricated simply because some inputs exist

The first implementation target should be the **smallest safe canonical working-capital core**, not the largest possible ratio set.

If Inventory and Trade AR are strong across the universe but AP/COGS are weak, implement the strong subset first.

If KR point-in-time balance-sheet evidence is safe even though KR cash-flow period context remains blocked, use that distinction rather than treating all KR financial data as unavailable.

And for today’s operating schedule:

**do useful architecture work now, then leave the 16:05/16:15 natural KR window untouched.**

Phase 9.1A should improve tomorrow’s architecture without contaminating today’s evidence.
