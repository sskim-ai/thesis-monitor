# thesis-monitor — Phase 9.1B Work Instruction

## Metadata

- Phase: `9.1B`
- Title: `Canonical Working Capital Core`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Dependency: `Phase 9.1A Working Capital Evidence Architecture`
- Phase 9.1A final branch SHA: `d4a4daf08ff5f68bc1072cc065e69ca5de5da145`
- Phase 9.1A implementation SHA: `0d3b42715fc8964fe053d72e0ecc979fb78b14cc`
- Current main/operating before KR natural window: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- Phase 9.1A promotion state: `PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`
- Phase 9.1A gate: `PHASE_9_1B_READY = YES`
- Approved scope: `SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE`
- Current Phase 9.0E user-visible cash-flow mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`
- User-visible working-capital change in 9.1B: `0`
- Required final gate: `PHASE_9_1C_READY = YES/NO`

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260821-phase-9-1b-canonical-working-capital-core.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify the Phase 9.1A final branch SHA exists:
   `d4a4daf08ff5f68bc1072cc065e69ca5de5da145`
3. Verify Phase 9.1A is a clean descendant of the current operating/main baseline.
4. Because 9.1B depends on 9.1A and 9.1A is intentionally not yet promoted, create the 9.1B branch from the **Phase 9.1A final SHA**, not from the older operating main.
5. Commit/push this instruction as a **docs-only instruction commit** before implementation.
6. Record:
   - `instruction_path`
   - `instruction_commit_sha`
   - `instruction_version`
   - `dependency_base_sha`
7. Implement only after the instruction commit exists.
8. Do not silently edit this instruction after implementation begins.
9. No force push / history rewrite.

Recommended branch:

`codex/phase-9-1b-canonical-working-capital-core`

Expected ancestry before later promotion:

```text
main/operating 33c2...
        ↓
Phase 9.1A final d4a4...
        ↓
9.1B instruction commit
        ↓
9.1B implementation/final
```

If `origin/main` moves before eventual promotion, reconcile explicitly.

---

# 1. Today’s KR natural-window rule

Current operating main remains intentionally frozen for the 2026-08-21 KR natural cycle.

Protected window:

- KRX telemetry: `16:05 KST`
- KR primary: `16:15 KST`
- KR backup: `16:55 KST`
- combined natural review: approximately after `17:05 KST`

Phase 9.1B development may proceed now on the dependent branch.

Until the natural KR review is complete:

- main promotion: `0`
- operating checkout change: `0`
- API restart: `0`
- runtime feature-mode change: `0`
- scheduler change: `0`
- manual KRX/KR task: `0`
- manual Telegram: `0`

If 9.1B is complete before the KR natural review, push the branch and reports and set:

`PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`

This is expected operating safety, not phase failure.

---

# 2. Phase 9.1A decisions are authoritative

Phase 9.1B must implement the exact architecture decisions from 9.1A.

Contract:

`working-capital-evidence-v1`

Closed raw metric semantics:

```text
inventory
trade_accounts_receivable
accounts_receivable_broad
trade_accounts_payable
accounts_payable_broad
```

Inventory:
- total inventory semantic only
- no silent component aggregation

AR:
`TRADE_PLUS_SEPARATE_BROAD`

AP:
`TRADE_PLUS_SEPARATE_BROAD`

Scope:
- source current/noncurrent/total scope preserved
- no automatic current+noncurrent summation
- no AR gross-up
- broad AR is never renamed trade AR
- broad AP is never renamed trade AP

Primary comparable:
- same issuer fiscal quarter in prior fiscal year
- exact semantic
- exact/compatible currency and unit
- same entity scope
- same statement basis
- authoritative source version

Revenue:
- same compatible filing period
- Q2/Q3 YTD preferred where applicable

COGS:
`INCLUDE_SELECTIVELY_EXACT_SEMANTIC`

PIT:
- source availability retained
- future source not allowed in historical/replay context

Provisional:
- newer provisional earnings does not create/relabel a balance-sheet period

Advanced ratios:
- DSO: DEFER
- Inventory Days: DEFER
- DPO: DEFER
- CCC: DEFER

Do not reopen these architecture decisions without a concrete P0/P1 discovered during implementation.

---

# 3. Phase purpose

Implement the first deterministic canonical working-capital core.

The canonical chain is:

```text
Official balance-sheet occurrence
        ↓
Exact semantic mapping
        ↓
Point-in-time Fact
        ↓
Prior-year comparable Fact
        ↓
Absolute delta
        ↓
Safe YoY growth
        ↓
Compatible revenue / COGS YoY
        ↓
Typed cross-growth relation
        ↓
Internal shadow/audit output
```

This phase converts Phase 9.1A architecture into production-quality backend contracts and deterministic facts.

It does **not** expose working-capital data to users or AI.

---

# 4. Initial implementation scope

Implement:

## Raw point-in-time canonical facts
- `inventory`
- `trade_accounts_receivable`
- `accounts_receivable_broad`
- `trade_accounts_payable`
- `accounts_payable_broad`

## Comparable balance facts
- current formal balance
- prior-year same-fiscal-quarter comparable balance

## Derived facts
- absolute delta
- safe YoY percentage

## Selective typed cross-growth relations
- AR vs Revenue
- Inventory vs Revenue
- Inventory vs COGS
- AP vs COGS

Only where exact Phase 9.1A comparability rules pass.

---

# 5. Explicit exclusions

Do NOT implement:

- user-visible working-capital text
- AI working-capital sidecar
- fallback working-capital text
- Public Action working-capital fields
- public snapshot working-capital fields
- DSO
- Inventory Days
- DPO
- CCC
- working-capital score
- arbitrary warning thresholds
- ROIC
- working-capital valuation multiple
- automatic investment-logic state change
- automatic warning lifecycle change
- DB assessment mutation
- KR OpenDART cash-flow period recovery
- contract-assets-as-AR broadening
- accrued-liabilities-as-trade-AP broadening
- inventory component aggregation
- prior-quarter lifecycle
- paid provider integration
- KRX breadth integration

---

# 6. Existing canonical architecture first

Do not build a parallel store.

Reuse/extend:

- financial-lineage-v2
- financial-quality-taint-v2
- canonical financial Fact architecture
- source occurrence identity
- currency/unit normalization
- entity/statement-basis validation
- PIT/source-availability model
- restatement/version handling
- Phase 9.0 deterministic derived-Fact patterns

Working-capital facts must be first-class canonical financial facts.

---

# 7. Canonical raw Fact contract

Implement or finalize canonical Fact representation for each raw balance metric.

Minimum fields:

```text
fact_id
metric
semantic_scope

value
currency
unit

balance_date
fiscal_year
fiscal_quarter

entity_scope
statement_basis

source_provider
source_document_id
source_document_type
filing_date
source_available_at
source_occurrence_id
source_semantic
raw_payload_sha256

source_reported_value
source_reported_unit

quality
eligibility
cautions

as_of_date
```

Use repository conventions.

Do not fabricate missing metadata.

---

# 8. Point-in-time identity

Balance-sheet facts use:

`balance_date`

as their economic period identity.

Filing date is availability metadata, not balance date.

Do not derive balance date from:

- filing date
- report name alone
- quarter label alone

unless existing verified filing context explicitly provides it.

---

# 9. Deterministic raw Fact identity

Fact ID must deterministically distinguish:

- issuer
- canonical metric
- semantic scope
- balance date
- entity scope
- statement basis
- currency/unit
- authoritative source occurrence/version

Repeated processing of the same authoritative occurrence must not create duplicate facts.

---

# 10. Inventory implementation

Canonical metric:

`inventory`

Meaning:

total inventory only.

Accepted:
- source occurrence semantically representing total inventories

Rejected or separate:
- raw materials only
- WIP only
- finished goods only
- inventory components lacking proven total aggregation
- contract assets
- prepaid expenses
- investment property
- securities inventory unless industry-specific architecture explicitly says otherwise; initial generic inventory contract should reject such substitution

No silent component sum.

If source provides both total and components:
- total Fact is canonical
- components may remain source evidence but are not part of 9.1B canonical core.

---

# 11. Trade AR implementation

Canonical metric:

`trade_accounts_receivable`

Only exact trade semantic.

Examples of categories that must not silently map:
- other receivables
- loans receivable
- financing receivables
- contract assets
- broad total receivables without trade identity

If the source label is "accounts receivable, net" and Phase 9.1A mapping proved it is a broad/non-trade-specific semantic, use `accounts_receivable_broad`, not trade AR.

---

# 12. Broad AR implementation

Canonical metric:

`accounts_receivable_broad`

This is intentionally separate.

It may include safely mapped issuer-reported:
- broad accounts receivable
- current/broad receivable categories
- trade-and-other receivables

But the exact source semantic/scope must be retained.

User-facing "trade receivable" semantics must never be inferred from this metric.

No broad-to-trade alias.

---

# 13. Trade AP implementation

Canonical metric:

`trade_accounts_payable`

Only exact trade semantic.

Do not map:
- accrued liabilities
- accrued expenses
- other payables
- contract liabilities
- debt
- total liabilities

to trade AP.

---

# 14. Broad AP implementation

Canonical metric:

`accounts_payable_broad`

May preserve a broader exact source semantic proven in 9.1A.

Broad AP is never renamed trade AP.

Exact semantic/scope metadata must survive into every derived relation.

---

# 15. Current/noncurrent/total scope

Preserve source scope.

Do not automatically:

```text
current AR + noncurrent AR
```

or:

```text
current AP + noncurrent AP
```

unless a future explicit contract proves the sum is the intended canonical semantic.

9.1B implements source-scope-preserving facts.

Comparability requires compatible scope.

---

# 16. Net/gross receivable scope

If source reports AR net of allowance:

preserve net semantic.

Do not reconstruct gross AR.

Do not compare:
- gross prior AR
vs
- net current AR

as identical semantic.

Fail closed or mark non-comparable.

---

# 17. SEC mapping implementation

Implement only:

- validated standard tags
- validated issuer extension mappings evidenced in 9.1A

Do not create a speculative broad taxonomy allowlist.

Mapping registry should retain:

```text
canonical metric
source taxonomy
source tag
statement role/context
semantic scope
entity scope expectations
verification basis
```

Issuer extensions require actual balance-sheet context.

---

# 18. OpenDART mapping implementation

Implement the safe 9.1A mappings for KR point-in-time balance-sheet facts.

Rules:

- CFS preferred where consolidated statements exist
- OFS not mixed with CFS
- explicit balance dates
- exact current/prior comparable context
- Korean Re generic industrial working-capital remains N/A
- KR cash-flow duration gap is unrelated and remains unresolved

Do not let the cash-flow period blocker suppress safe balance-sheet point-in-time facts.

---

# 19. Foreign issuer implementation

Issuer-level working-capital facts require:

- safe issuer identity
- financial currency
- statement basis
- balance date

ADR/share ratio is not required.

Do not combine these facts with share-price/security calculations in 9.1B.

---

# 20. Prior-year comparable selector

Primary comparable rule:

```text
same issuer
same canonical metric
same semantic scope
same entity scope
same statement basis
same/compatible currency and unit
prior fiscal year
same fiscal quarter
authoritative source version
```

For FY:
- current FY-end vs prior FY-end

For non-calendar issuer:
- fiscal-quarter identity and actual balance date, not calendar-quarter assumption.

---

# 21. Date-compatibility safety

Protect the 9.1A repaired defect:

A prior FY-end balance republished in a later Q1 filing must not become a Q1 comparable merely because it appears in a Q1 document.

Comparability needs both:
- fiscal context
- economically compatible balance-date relation

Preserve the approximately-one-fiscal-year / source-frame checks defined by 9.1A.

Do not invent a loose date tolerance that weakens semantics.

---

# 22. Restatement/version selection

If a later authoritative filing restates a prior balance:

- use latest authoritative occurrence for current canonical relation
- preserve source version and source availability
- historical PIT replay must not see restatement before it was published
- input Fact IDs must identify the chosen occurrence/version

Do not combine original current with restated prior inconsistently.

---

# 23. Absolute delta derived Fact

For each safe comparable pair:

```text
absolute_delta = current_balance - prior_balance
```

Implement as deterministic derived Fact/relation.

Required lineage:

- current Fact ID
- prior Fact ID
- formula/version
- currency/unit
- semantic scope
- comparable identity

Negative delta is valid.

---

# 24. YoY growth derived Fact

For safe comparable positive prior denominator:

```text
yoy_growth = (current - prior) / prior
```

Rules:

- prior > 0 required
- missing prior != 0
- zero prior → YoY unavailable
- negative prior → standard YoY unavailable / review
- current negative unusual balance → raw semantic quality review, not blind growth calculation

Preserve exact input Fact IDs.

---

# 25. No growth quality verdict

Derived YoY Fact is factual.

Do not emit:
- good
- bad
- healthy
- weak
- warning
- deteriorating cash conversion

Those are future reasoning-layer interpretations.

---

# 26. Revenue canonical dependency

Cross-growth relations may reuse existing safe revenue Facts.

Do not build another revenue truth path.

Revenue comparison must be:

- current compatible flow period
- prior-year comparable flow period
- same issuer
- same entity/basis
- same currency/unit
- safe period type

For Q2/Q3:
YTD-compatible relation preferred as decided in 9.1A.

---

# 27. COGS canonical dependency

Only exact safe COGS/cost-of-revenue semantics approved by 9.1A.

Do not use:
- generic expense
- operating cost bundle
- unknown cost line

as COGS.

`COGS_RELATION = selective exact semantic`

is a core 9.1B rule.

---

# 28. AR vs Revenue relation

Available for exact trade AR or broad AR separately.

Do not erase semantic.

Examples of typed identity:

```text
TRADE_AR_GROWTH_GT_REVENUE_GROWTH
BROAD_AR_GROWTH_GT_REVENUE_GROWTH
```

or repository-equivalent metadata:

```text
balance_metric = trade_accounts_receivable
relation = growth_vs_revenue
direction = greater
```

Preferred: avoid proliferating relation enum names if structured fields can express type.

The key is that broad vs trade survives.

---

# 29. Inventory vs Revenue relation

Inputs:

- safe inventory YoY
- safe comparable revenue YoY

Derived relation:

- inventory growth greater / lower / equal to revenue growth

No demand-quality verdict.

---

# 30. Inventory vs COGS relation

Only when exact COGS semantic is safe.

Relation must preserve:

- inventory Fact IDs
- COGS flow Fact IDs
- both YoY values
- difference in percentage points if calculated
- semantic scope

Do not call this Inventory Days.

---

# 31. AP vs COGS relation

Exact trade AP and broad AP relations remain semantically distinct.

Do not call result:

- DPO
- supplier payment period
- supplier financing

It is only a growth relation.

---

# 32. Percentage-point difference

If both YoY inputs are safe:

```text
growth_gap_pp = balance_yoy_pct - flow_yoy_pct
```

This is deterministic.

No arbitrary threshold.

Do not convert +15pp to "warning".

---

# 33. Relation Fact identity

Every relation must preserve:

- relation ID
- balance metric semantic
- flow metric semantic
- current balance Fact ID
- prior balance Fact ID
- current flow Fact ID
- prior flow Fact ID
- balance YoY Fact ID
- flow YoY Fact ID
- formula/version
- relation direction
- growth gap if safe
- eligibility/cautions

No relation without full input lineage.

---

# 34. Suggested relation model

Prefer one structured derived relation contract over many hard-coded prose-like enum names.

Conceptual:

```text
working_capital_relation:
  relation_id
  balance_metric
  balance_scope
  flow_metric
  relation_type = yoy_growth_comparison
  direction = greater/lower/equal
  gap_pct_points
  input_fact_ids
  comparability
  quality
```

Actual repository conventions prevail.

---

# 35. Formal-lagging-provisional state

If newer official provisional earnings exist but no newer formal balance sheet:

- canonical balance remains valid for its formal date
- do not relabel to the provisional period
- mark future consumption state as `FORMAL_LAGGING_PROVISIONAL` or equivalent
- no user-visible/AI use in 9.1B

This should reuse the Phase 9.0C freshness philosophy.

---

# 36. Latest safe working-capital snapshot

Create an internal selector for:

`latest_safe_working_capital_period`

per metric, not necessarily one all-or-nothing period.

Example:
- Inventory may have a safe latest balance
- trade AR may be blocked
- broad AR may be safe

Do not fail all metrics because one is missing.

---

# 37. Selective metric coverage

Per ticker:

```text
inventory_status
trade_ar_status
broad_ar_status
trade_ap_status
broad_ap_status
```

are independent.

Do not invent one `working_capital_available=true` if it hides important semantic differences.

A compact summary may exist, but detailed per-metric eligibility is source of truth.

---

# 38. Industry applicability contract

Implement/reuse Phase 9.1A applicability metadata.

Examples:

- memory/semiconductor: Inventory PRIMARY
- automotive: Inventory PRIMARY
- steel/materials: Inventory PRIMARY
- industrial/EPC: AR PRIMARY when safe
- transport: AR/AP selective
- cloud/software: broad AR/AP SECONDARY
- HPC: working-capital relations CONTEXT/SECONDARY
- biotech: CONTEXT_ONLY
- special financial-like: CONTEXT_ONLY unless specifically proven
- insurance/reinsurance: NOT_APPLICABLE

Do not make industry applicability user-visible in 9.1B.

---

# 39. Insurance N/A

Korean Re must not receive generic industrial working-capital relations.

If raw balance fields happen to exist:

- do not automatically make them investment-working-capital facts for this contract
- maintain N/A applicability

No user-visible statement.

---

# 40. Contract assets remain separate

Do not map:
`contract assets`
to:
`trade_accounts_receivable`

This is especially important for project/EPC/aerospace businesses.

Record as P2/future extension if needed.

Do not broaden 9.1B.

---

# 41. Accrued liabilities remain separate

Do not map:
`accrued liabilities`
to:
`trade_accounts_payable`

Broad AP can only use mappings approved by 9.1A.

---

# 42. Cash-flow cross-link metadata

Because Phase 9.0 FCF now exists, optionally record internal cross-link eligibility:

```text
working_capital_to_cash_flow_link:
  HIGH_VALUE
  MEDIUM_VALUE
  LOW_VALUE
  NOT_APPLICABLE
```

Only if 9.1A already produced this matrix or it can be deterministically derived from its industry applicability.

Do not create causal conclusions.

Do not make user-visible.

---

# 43. No causality in canonical layer

The canonical layer may know:

```text
AR grew faster than revenue
OCF declined
```

but must not derive:

```text
AR caused OCF decline
```

without future reasoning-layer evidence.

No causal field.

---

# 44. Canonical shadow output

Create internal/audit-only working-capital core snapshot.

Suggested shape:

```text
ticker
balance_date
freshness_state

inventory:
  current
  prior
  delta
  yoy
  status

trade_ar:
  ...

broad_ar:
  ...

trade_ap:
  ...

broad_ap:
  ...

relations:
  ar_vs_revenue
  inventory_vs_revenue
  inventory_vs_cogs
  ap_vs_cogs

industry_applicability
cautions
denial_reasons
```

No Public Action exposure.

No production AI injection.

---

# 45. Evidence generator

Recommended:

`scripts/phase9_1b_evidence.py`

Requirements:

- deterministic
- read-only
- use stored evidence first
- no production service auto-run
- no DB mutation
- provider calls counted
- sanitized outputs

---

# 46. Expected architecture coverage reference

Phase 9.1A observed:

| Metric | Eligible | Partial | Blocked | N/A |
|---|---:|---:|---:|---:|
| Inventory | 11 | 3 | 5 | 1 |
| Exact trade AR | 6 | 1 | 12 | 1 |
| Broad AR | 9 | 3 | 7 | 1 |
| Exact trade AP | 8 | 1 | 10 | 1 |
| Broad AP | 10 | 1 | 8 | 1 |

Relations:

| Relation | Eligible | Blocked | N/A |
|---|---:|---:|---:|
| AR vs Revenue | 14 | 5 | 1 |
| Inventory vs Revenue | 11 | 8 | 1 |
| Inventory vs COGS | 11 | 8 | 1 |
| AP vs COGS | 14 | 5 | 1 |

These are regression references, not hard-coded acceptance quotas.

---

# 47. Coverage drift audit

After implementation compare 9.1A expectation vs 9.1B actual.

Per metric/ticker classify:

- UNCHANGED
- RECOVERED
- NEWLY_BLOCKED
- NEWLY_ELIGIBLE
- SEMANTIC_RECLASSIFIED

Any large coverage change requires root-cause explanation.

Coverage can decrease if implementation discovers stricter evidence constraints.

Do not weaken semantics merely to preserve counts.

---

# 48. Strong implementation criterion

9.1B is strong if:

- eligible facts are fully reproducible
- broad/trade semantics remain distinct
- prior comparable is exact
- all derived facts have input Fact IDs
- unsupported metrics fail closed

It is not defined by matching the exact 9.1A counts.

---

# 49. Representative implementation proofs

Re-run the Phase 9.1A representative classes through actual canonical implementation.

At minimum:

- KR memory inventory
- US platform broad AR
- non-calendar memory inventory
- foreign issuer inventory
- HPC broad AR
- biotech broad AP negative-control/context-only
- insurance N/A

Use actual tickers from 9.1A evidence.

---

# 50. Representative proof requirements

For each:

```text
raw occurrence
canonical Fact ID
metric/semantic scope
balance date
filing date
source availability
currency/unit
entity/basis
prior comparable Fact ID
absolute delta
YoY if safe
flow comparison Fact IDs
relation ID/result
eligibility/cautions
```

---

# 51. Numeric arithmetic safety

Financial balance amounts should use integer/Decimal-safe arithmetic.

Avoid binary float drift for:
- raw amounts
- absolute delta

Percentage calculations should follow existing deterministic financial numeric policy.

Report rounding only at presentation/audit layer.

---

# 52. Missing vs zero

Hard rule:

- missing raw fact ≠ zero
- missing prior ≠ zero
- missing revenue/COGS ≠ zero

A reported zero may be valid.

Derived growth from zero prior:
unavailable.

---

# 53. Negative unusual balance

If a normalized Inventory/AR/AP balance is negative:

- preserve raw evidence
- flag semantic/quality review
- do not emit standard YoY relation automatically
- classify eligibility according to architecture

Do not absolute-value a balance.

---

# 54. Currency/unit mismatch

If current and prior facts differ in currency/unit and safe normalization is not explicit:

- comparable relation blocked

Do not perform ad-hoc FX.

---

# 55. Entity/basis mismatch

Examples:

- current CFS vs prior OFS
- consolidated AR vs standalone revenue

Relations blocked.

No cross-scope repair in 9.1B.

---

# 56. PIT for canonical facts

Store `source_available_at` or equivalent.

Historical replay must later be able to enforce:

`source_available_at <= cutoff`

Implementation tests must include future-restatement control.

---

# 57. Restatement PIT control

A restated prior balance is authoritative today, but a historical replay before its publication must not use it.

Test both:
- current canonical view
- historical PIT selector

No look-ahead.

---

# 58. Latest-formal currentness

Working-capital facts are current-formal only relative to the latest validated formal balance sheet.

Newer provisional-only earnings:
- do not upgrade balance currentness

No arbitrary stale-day threshold.

---

# 59. No user-visible or AI integration

Critical acceptance:

Phase 9.1B must not add any working-capital fact to:

- production AI packet
- AI prompt
- fallback renderer
- Telegram
- public snapshot
- Public Action
- market digest

User-visible diff from working-capital feature:

`0`

Current Phase 9.0E cash-flow feature remains unchanged.

---

# 60. 9.0E regression

Because shared financial lineage may be touched, verify:

- 9.0E selector
- current-formal full FCF
- AI/fallback parity
- kill switch
- TSLA consistency
- user-visible cash-flow selected preview
- KR cash-flow injection 0
- canary isolation

all remain PASS.

Do not change the 9.0E operating mode.

---

# 61. Natural KR review boundary

At/after today’s KR natural cycle, a separate review may discover a production P0.

If 9.1B is still branch-only:
- preserve branch
- do not promote shared changes until P0 triage

If the natural result only has P2:
- do not block 9.1B promotion

If a P0 is unrelated to 9.1B but affects current production safety:
- follow Phase Advancement Rule before main promotion if shared code risk exists

---

# 62. KRX telemetry boundary

Do not modify KRX telemetry code/config.

Read-only latest evidence may be reported after the natural window.

No provider calls for KRX as part of 9.1B.

---

# 63. DSO remains deferred

No code paths for:

```text
DSO = avg AR / revenue × days
```

in 9.1B.

Do not sneak in average AR helper intended to output DSO.

You may preserve raw current/prior AR, which is prerequisite evidence only.

---

# 64. Inventory Days remains deferred

No:

```text
avg inventory / COGS × days
```

user/internal metric implementation.

---

# 65. DPO remains deferred

No:

```text
avg AP / COGS × days
```

or purchases proxy.

---

# 66. CCC remains deferred

No:

```text
DSO + Inventory Days - DPO
```

No partial CCC.

---

# 67. Public Action boundary

Keep:

- version `0.4.5`
- operationId `20/20`
- schema `4`

No working-capital public fields.

---

# 68. Database/storage

Prefer existing canonical financial/fact storage model.

DB migration target:

`0`

If the existing model truly cannot represent:
- semantic scope
- balance date
- source occurrence
- derived input lineage

do not perform an unplanned migration.

Classify as architecture blocker and report.

No manual DB mutation.

---

# 69. Idempotency

Same source occurrence processed twice:
- one canonical raw Fact

Same comparable pair processed twice:
- one derived delta/YoY relation identity

No duplicate canonical facts.

---

# 70. Derived Fact versioning

If relation/formula contract version changes later:
- deterministic derivation version must be preserved

9.1B uses versioned formula/contract identity.

---

# 71. Quality taint propagation

Reuse financial-quality-taint behavior.

Hard-tainted raw input:
- no derived relation

Soft caution:
- propagate to derived fact where allowed

Do not silently drop source cautions.

---

# 72. Partial status

Examples:

- safe current Inventory, no prior comparable → PARTIAL
- safe broad AR, exact trade AR missing → broad eligible; trade blocked
- safe AP but COGS missing → AP YoY can be eligible, AP-vs-COGS blocked

Do not collapse all to one status.

---

# 73. Block reasons

Use structured reasons, e.g.:

```text
missing_current_fact
missing_prior_comparable
semantic_scope_mismatch
balance_date_mismatch
fiscal_context_mismatch
entity_scope_mismatch
statement_basis_mismatch
currency_unit_mismatch
prior_denominator_nonpositive
unsafe_cogs_semantic
financial_industry_not_applicable
source_conflict
```

Actual naming follows repository conventions.

---

# 74. Industry applicability is not eligibility

A metric can be canonically eligible but low/not-primary in an industry.

Keep separate:

- data eligibility
- industry applicability

9.1B is canonical data implementation, not message selection.

---

# 75. Cross-growth relations are factual

Examples:

```text
broad AR YoY = 20%
revenue YoY = 10%
growth gap = +10pp
```

Backend may store:
`AR growth > revenue growth`

It may not store:
`collection deteriorated`

Reasoning comes later.

---

# 76. Relation semantics must expose broad/trade identity

Never allow:

`accounts_receivable_broad`
relation

to later render as:
`trade receivables`

through a generic relation label.

The relation object must carry the canonical balance semantic.

---

# 77. Future user-facing safety metadata

Although not consumed now, every relation should have enough metadata to later support:

- PIT
- freshness
- semantic label
- industry applicability
- Unknown resolution

Do not include renderer prose here.

---

# 78. Active-universe audit output

Generate an implementation matrix:

```text
Ticker
Industry
Source
Latest formal balance date

Inventory:
 current Fact
 prior Fact
 delta
 YoY
 status

Trade AR:
 ...

Broad AR:
 ...

Trade AP:
 ...

Broad AP:
 ...

Revenue relation
COGS relation

Block reasons
```

---

# 79. Canonical fact audit JSON

Recommended:

`docs/reports/20260821-phase9-1b-canonical-facts.json`

For each raw/derived fact:

```text
ticker
issuer_id
fact_id
metric
semantic_scope

value
currency
unit
balance_date

source_document
source_occurrence
source_available_at
source_sha

fact_type
input_fact_ids
derivation
eligibility
cautions
```

No secrets.

---

# 80. Working-capital core internal preview

Create:

`docs/reports/20260821-phase9-1b-shadow-core-preview.md`

It is not AI prose.

It should show compact canonical facts/relations for eligible subjects.

No buy/sell language.

---

# 81. Tests — raw semantic mapping

Required:

- total inventory accepted
- inventory component rejected as total
- exact trade AR accepted
- broad AR separate
- other receivable rejected as trade
- contract asset rejected as trade AR
- exact trade AP accepted
- broad AP separate
- accrued liabilities rejected as trade AP
- debt rejected as AP

---

# 82. Tests — point-in-time identity

Required:

- correct balance date
- filing date not treated as balance date
- same filing with multiple comparative balance dates selected correctly
- FY-end republished in Q1 not relabeled Q1
- non-calendar fiscal quarter handled

---

# 83. Tests — comparability

Required:

- same fiscal quarter prior-year PASS
- FY vs prior FY PASS
- Q2 current vs prior FY-end as YoY FAIL
- current/total scope mismatch FAIL
- CFS/OFS mismatch FAIL
- currency/unit mismatch FAIL
- restated authoritative prior PASS
- future restatement excluded in historical PIT

---

# 84. Tests — delta/YoY

Required:

- absolute delta
- positive prior YoY
- zero prior → unavailable
- negative prior → no standard YoY
- missing prior → unavailable
- negative unusual current balance → quality block
- exact Fact lineage

---

# 85. Tests — AR vs Revenue

Required:

- trade AR relation preserves trade semantic
- broad AR relation preserves broad semantic
- safe YTD revenue comparison
- unrelated TTM revenue blocked
- missing revenue blocks cross relation, not AR YoY

---

# 86. Tests — Inventory vs Revenue/COGS

Required:

- safe inventory/revenue relation
- safe inventory/COGS exact-semantic relation
- unsafe COGS blocked
- no Inventory Days
- no demand verdict

---

# 87. Tests — AP vs COGS

Required:

- exact trade AP/COGS
- broad AP remains broad
- accrued liabilities not used
- missing COGS blocks relation only
- no DPO
- no supplier-stress verdict

---

# 88. Tests — KR

Required:

- six KR non-financial safe CFS balances where supported
- CFS/OFS no mixing
- explicit balance dates
- Korean Re N/A
- cash-flow period gap does not block safe working-capital facts
- no user-visible injection

---

# 89. Tests — provisional lag

Required:

formal balance period older than newer provisional earnings:
- canonical balance valid for formal date
- not relabeled provisional period
- future consumption state marked lagging/context-only
- no user-visible change

---

# 90. Tests — industry

Required:

- memory inventory PRIMARY metadata
- industrial AR applicability
- cloud broad AR secondary
- HPC context
- biotech context-only
- insurance N/A
- foreign issuer independent of ADR ratio

---

# 91. Tests — idempotency

Required:

- repeated source processing → same Fact ID
- repeated derived pair → same relation ID
- no duplicate facts
- source version change results in appropriate version-aware identity

---

# 92. Regression suite

Preserve:

- 9.0E selective user-visible cash-flow
- 9.0E kill switch
- 9.0D canary
- 9.0D.1 baseline consistency
- 9.0B FCF core
- 9.0C shadow consumption
- Phase 8.5.5/.1/.2
- run-27/28/29
- current PBR ownership
- CORZ typed valuation
- dynamic price/RR
- confirmation lifecycle
- night futures
- fallback
- exactly-once/receipt
- KRX telemetry

---

# 93. Full validation

Required:

- focused working-capital core tests PASS
- deterministic evidence generator PASS
- coverage audit PASS
- representative lineage proofs PASS
- broader financial/runtime regression PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- docs links/state JSON PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- implementation exact-SHA GitHub Actions Test/Lint PASS

If not yet promoted:
- branch final-SHA CI PASS

After eventual promotion:
- exact main/final SHA CI PASS

---

# 94. User-visible zero-diff gate

Before any main promotion, prove:

- production AI working-capital input: 0
- fallback working-capital rendering: 0
- Telegram working-capital diff: 0
- Public Action diff: 0
- public snapshot diff: 0
- 9.0E cash-flow mode unchanged

9.1B canonical implementation must not alter today's working user experience.

---

# 95. Provider-call policy

Stored/cached evidence first.

Official live calls only if needed.

Report:

```text
provider
requests
success
failure
cache_hit
purpose
```

No brute force.

No paid providers.

No credential exposure.

---

# 96. Required architecture update

Update:

`docs/architecture/WORKING_CAPITAL_EVIDENCE.md`

Add:

- 9.1B implementation status
- canonical Fact model
- derived Fact/relation model
- idempotency
- quality/taint behavior
- current implementation scope
- deferred metrics

---

# 97. Required reports

Create:

1. `docs/reports/20260821-phase9-1b-canonical-core-implementation.md`
2. `docs/reports/20260821-phase9-1b-active-universe-results.md`
3. `docs/reports/20260821-phase9-1b-lineage-verification.md`
4. `docs/reports/20260821-phase9-1b-comparable-balance-audit.md`
5. `docs/reports/20260821-phase9-1b-derived-relations-audit.md`
6. `docs/reports/20260821-phase9-1b-coverage-drift.md`
7. `docs/reports/20260821-phase9-1b-shadow-core-preview.md`
8. `docs/reports/20260821-phase9-1b-validation.md`
9. `docs/reports/20260821-phase9-1b-readiness.md`

Recommended JSON:

- `docs/reports/20260821-phase9-1b-canonical-facts.json`
- `docs/reports/20260821-phase9-1b-readiness.json`

---

# 98. Complete report bundle

Create:

`docs/reports/20260821-phase9-1b-complete-report.md`

Recommended JSON:

`docs/reports/20260821-phase9-1b-complete-report.json`

And:

`20260821-phase9-1b-complete-report-bundle.zip`

ZIP:
- sanitized docs/JSON only
- no secret-bearing raw provider payloads unless already intentionally sanitized
- include SHA-256

Push sanitized reports to the 9.1B branch.

---

# 99. Promotion after KR natural review

After approximately 17:05 KST, do not automatically promote.

First consume the separate KR natural review result.

If:
- production Open P0 = 0
- no material P1 relevant to shared financial/runtime architecture
- 9.1B P0 = 0
- 9.1B material P1 = 0
- zero-runtime-diff PASS
- branch CI PASS
- main ancestry clean

then promote the full dependent chain:

```text
main
→ Phase 9.1A
→ 9.1B instruction
→ 9.1B implementation/final
```

via clean fast-forward if still linear.

If main drift exists:
explicit clean integration.

No cherry-picking random pieces that break the Phase 9.1A dependency.

---

# 100. If KR review finds a P0

Do not discard 9.1A/9.1B work.

Keep branch/evidence intact.

Then:

- classify whether P0 affects shared code
- if unrelated but production safety requires urgent repair, repair P0 first
- rebase/merge safely only after P0 resolution
- do not rewrite history

9.1B readiness can remain valid even if promotion is temporarily deferred.

---

# 101. Operating promotion

When approved:

- main fast-forward/integration
- operating HEAD = main
- working trees clean
- API restart only if imported runtime code requires it
- health PASS
- 9.0E mode unchanged
- AI schedules unchanged
- KRX telemetry unchanged
- Production Assist OFF

No manual natural run.

---

# 102. Persistent state on implementation PASS

Before promotion, branch docs may record:

```text
Phase 9.1A:
COMPLETE_PENDING_PROMOTION

Phase 9.1B:
IMPLEMENTED_PENDING_PROMOTION

Working Capital Canonical Core:
IMPLEMENTED_SHADOW

Working Capital User Visible:
NOT_ENABLED

DSO:
DEFERRED

Inventory Days:
DEFERRED

DPO:
DEFERRED

CCC:
DEFERRED
```

Do not modify operating persistent state before promotion.

---

# 103. Persistent state on promotion PASS

After safe promotion:

```text
Phase 9.1A:
COMPLETE

Phase 9.1B:
COMPLETE

Working Capital Canonical Core:
IMPLEMENTED_SHADOW

Working Capital User Visible:
NOT_ENABLED
```

9.0E user-visible cash-flow keeps its independent current state.

---

# 104. Next phase definition

Recommended next phase if 9.1B passes:

`Phase 9.1C — Working Capital Shadow Consumption & Earnings-Quality Reasoning`

The 9.1C purpose would be analogous to 9.0C:

```text
Canonical working-capital Facts
        ↓
PIT / freshness
        ↓
Industry applicability
        ↓
Materiality
        ↓
Shadow AI reasoning
        ↓
Unknown resolution
        ↓
Quality validation
```

Do not implement 9.1C in this task.

---

# 105. PHASE_9_1C_READY gate

Must set exactly:

`PHASE_9_1C_READY = YES` or `NO`

## YES requires

- raw canonical metrics implemented
- trade vs broad semantics preserved
- balance-date identity safe
- prior-year comparable selector safe
- absolute delta deterministic
- YoY deterministic where eligible
- derived relation lineage complete
- COGS relation selective exact semantic
- KR safe point-in-time coverage implemented where eligible
- insurance N/A preserved
- non-calendar fiscal PASS
- PIT/restatement PASS
- no DSO/CCC leakage
- open P0 = 0
- open material P1 = 0
- full CI PASS
- working-capital user-visible diff = 0

Full 20-ticker coverage is not required.

---

# 106. PHASE_9_1C_SCOPE

If READY, recommend an evidence-based scope.

Default candidate:

`WORKING_CAPITAL_SHADOW_CONSUMPTION_EARNINGS_QUALITY`

But report whether shadow consumption should initially include:

- Inventory
- exact trade AR
- broad AR
- exact trade AP
- broad AP
- AR-vs-Revenue
- Inventory-vs-Revenue
- Inventory-vs-COGS
- AP-vs-COGS

It may exclude weak/low-value relation families.

---

# 107. Advanced-ratio readiness re-evaluation

At completion, re-state:

```text
DSO_READY_FOR_IMPLEMENTATION = ...
INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = ...
DPO_READY_FOR_IMPLEMENTATION = ...
CCC_READY_FOR_IMPLEMENTATION = ...
```

9.1B implementation may improve prerequisites, but do not automatically upgrade these.

Expected default remains DEFER unless average-balance/duration/purchases requirements are truly closed.

---

# 108. P0 / P1 / P2

Use Phase Advancement Rule.

## P0 examples
- wrong balance date
- wrong semantic mapping
- trade/broad collapse
- CFS/OFS mixing
- incorrect restatement/PIT
- wrong derived arithmetic
- DSO/CCC accidentally emitted
- 9.0E production regression caused by 9.1B

## P1 examples
- valid facts systematically lost due to canonical implementation bug
- relation drops semantic scope
- important industry applicability misapplied
- implementation substantially diverges from 9.1A without evidence

## P2 examples
- AP relation coverage weaker than hoped
- prior-quarter comparison deferred
- inventory components deferred
- contract assets deferred
- advanced ratios deferred
- report formatting

P2 does not block 9.1C.

---

# 109. Completion report — repository

Report:

- instruction path
- instruction commit
- instruction version
- dependency base SHA
- branch
- implementation SHA
- final branch SHA
- main/operating SHA
- promotion state
- promotion method if performed
- working trees
- deviations YES/NO

---

# 110. Completion report — contract

Report:

- contract/version
- raw canonical metrics
- exact semantic rules
- Fact identity
- derived relation identity
- PIT/restatement
- eligibility statuses

---

# 111. Completion report — coverage

For each raw metric:

- eligible
- partial
- blocked
- N/A

For each relation:

- eligible
- blocked
- N/A

Compare against 9.1A.

List drift reasons.

---

# 112. Completion report — semantic integrity

Report:

- broad AR → trade AR misclassification count
- broad AP → trade AP misclassification count
- inventory component → total misclassification
- contract asset → trade AR
- accrued liability → trade AP

Targets:

all `0`.

---

# 113. Completion report — lineage

Report:

- raw canonical Fact count
- derived delta count
- YoY count
- cross-growth relation count
- missing input Fact refs
- arithmetic errors
- PIT errors
- source-occurrence missing

Targets:
lineage/arithmetic/PIT errors `0`.

---

# 114. Completion report — representative proofs

List actual examples and their:

- Fact IDs
- balance dates
- source occurrences
- current/prior values
- derived values
- relation IDs

---

# 115. Completion report — KR

Report:

- safe KR working-capital metric coverage
- CFS/OFS behavior
- insurance N/A
- no dependency on blocked KR cash-flow period context
- no user-visible injection

---

# 116. Completion report — 9.0E regression

Report:

- feature mode
- selected FCF preview unchanged
- kill switch
- baseline consistency
- AI/fallback parity
- KR FCF leakage
- natural state if new evidence exists

No 9.0E configuration changes.

---

# 117. Completion report — natural KR gate

If KR review is available:

- production P0/P1
- delivery mode
- exactly-once
- KRX 16:05
- 9.0E KR leakage check

Use it only for promotion safety.

Do not turn it into a 9.1B implementation input.

---

# 118. Completion report — validation

Report:

- focused
- broader regression
- full pytest
- evidence generator reproducibility
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

# 119. Completion report — safety

Report:

- runtime/user-visible diff
- manual Telegram
- manual AI task
- Pilot mutation
- DB migration/mutation
- archive rewrite
- receipt rewrite
- force push
- Production Assist
- AI schedules
- KRX schedule

Targets:
manual mutation `0`.

---

# 120. Completion report — final gate

Must end with:

```text
PHASE_9_1C_READY = YES/NO
PHASE_9_1C_SCOPE = ...
```

Also report:

```text
DSO_READY_FOR_IMPLEMENTATION = ...
INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = ...
DPO_READY_FOR_IMPLEMENTATION = ...
CCC_READY_FOR_IMPLEMENTATION = ...
```

If NO:
state exact bounded P0/P1.

If YES:
recommend Phase 9.1C and exact metric/relation families for shadow consumption.

---

# 121. Complete report delivery

Create one final ZIP:

`20260821-phase9-1b-complete-report-bundle.zip`

Include sanitized:

- complete report
- readiness
- coverage
- lineage
- representative proofs
- canonical facts audit JSON
- validation

Report ZIP SHA-256.

Push sanitized reports to the 9.1B branch.

---

# 122. Final philosophy

Phase 9.1B is not about creating more financial ratios.

It is about turning balance-sheet working-capital evidence into deterministic canonical facts.

The critical distinction is:

```text
Trade AR
≠
Broad AR

Trade AP
≠
Broad AP

Inventory total
≠
Inventory component
```

Coverage must never be increased by erasing those distinctions.

The correct chain is:

```text
Official source occurrence
        ↓
Exact semantic scope
        ↓
Point-in-time balance
        ↓
Same-fiscal-period prior comparable
        ↓
Absolute delta / safe YoY
        ↓
Compatible Revenue / COGS YoY
        ↓
Typed factual relation
```

The canonical layer should be able to say:

```text
Broad AR grew faster than revenue.
```

when the exact facts support it.

It should not say:

```text
Customers are paying more slowly.
```

That interpretation belongs to a later reasoning phase.

Likewise:

```text
Inventory grew faster than COGS.
```

is a factual relation.

It is not automatically:

```text
Demand is weakening.
```

The purpose of 9.1B is to make the evidence trustworthy enough that 9.1C can later reason about it safely.

Do not implement DSO, Inventory Days, DPO, or CCC merely because some prerequisites now exist.

Do not make AP weakness block a strong Inventory/AR core.

Do not make KR cash-flow period limitations erase safe KR point-in-time balance-sheet evidence.

And for today’s operating schedule:

**build the dependent 9.1B branch now, keep operating untouched through the KR natural window, then promote the clean 9.1A→9.1B chain only after the natural review confirms there is no production P0.**

The success criterion is not maximum coverage.

It is:

**every Fact and every relation that is marked eligible is semantically exact, period-correct, lineage-complete, and reproducible.**
