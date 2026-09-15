# Thesis Monitor — Inventory, Receivables & Working-Capital Financial Domain Mapping Implementation

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-inventory-receivables-working-capital-financial-domain-mapping-implementation.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-inventory-receivables-working-capital-financial-domain-mapping-implementation-report.zip
```

Master-workflow phase:

```text
M10 — Higher-Risk Financial Domain Mapping
       Inventory / Receivables / Working-Capital
```

This task begins only after M9 has completed.

M9 implemented the higher-risk:

```text
interest-bearing debt / liquidity
```

domain and recommended:

```text
INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION
```

M10 implements only:

```text
inventory
receivables
working-capital component context
```

M10 must NOT implement:

```text
non-operating / financial-income effects
Directional Core financial_context consumption
source-sufficiency gate changes
warning activation
model proof
real holdout
production deployment
schedule resume
```

The goal is to map safe direct balance-sheet working-capital evidence into
`financial_context`, with exact period/basis provenance and sector applicability,
without inventing operating-working-capital formulas or efficiency ratios.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-interest-bearing-debt-liquidity-financial-domain-mapping-implementation-report.zip
```

Verified SHA-256:

```text
f175e53c0c1e7ae9e17d885f7348040cec77a4333c75e5b84220f86916e5d790
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M9 state:

```text
M1 = COMPLETE
M2 = COMPLETE
M3 = COMPLETE
M4 = COMPLETE
M5 = COMPLETE
M6 = COMPLETE
M7 = COMPLETE
M8 = COMPLETE
M9 = COMPLETE

status = M9_COMPLETE
production_readiness = NOT_READY

next_scope =
INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION
```

Reported M9 provenance:

```text
base_sha =
5e46a5ff80fbff32145cef0ccf68d906dfcdf5b4

work_instruction_commit =
af361e68ba843ee211bcd1e12750c1cf95a8461e

implementation_commit =
357a1d577ffd24c96bb0f3ce2c0baf1f13458658

branch =
codex/20260908-interest-bearing-debt-liquidity-financial-domain-mapping-implementation
```

M9 completion artifacts used the established pre-report-commit convention:

```text
final_head_sha = NOT_MEASURED
report_commit = NOT_MEASURED
```

At M10 start, use actual repository HEAD as authority and record the actual M9 final/report state.

---

# 2. M9 facts frozen for M10

M9 result:

```text
debt_liquidity_adapter_status =
IMPLEMENTED_INTERNAL_ONLY

KR non-financial candidates = 6
KR direct cash = 6
KR direct debt components = 17
KR complete debt totals = 5
KR net debt = 5

financial-sector candidates = 1
financial-sector generic net-debt emissions = 0

US non-financial candidates = 13
US preserved balance-sheet payloads = 0
US real debt/liquidity coverage claim = none
```

M9 safety controls:

```text
total liabilities used as debt = 0
partial debt labeled total = 0
ticker-specific mappings = 0
OpenDART fuzzy mappings = 0

lease liabilities =
SEPARATE_CONTEXT_ONLY

restricted cash =
EXCLUDE_FROM_NET_DEBT_CASH_BASIS

compact AI context changed = 0
source sufficiency changed = 0
Daily Delta changed = 0
warning semantics changed = 0
```

Preserve all M9 semantics.

The absence of preserved US balance-sheet payloads in M9 is an offline-evidence limitation,
not evidence that the US production source stack cannot support balance-sheet facts.

M10 must not perform live provider fetches to fill that gap.

---

# 3. M4 frozen working-capital design principles

M4 established that inventory / receivables / working-capital evidence can be useful for:

```text
cash-conversion quality
growth quality
inventory build
receivables collection risk
working-capital consumption
```

especially for:

```text
manufacturing
hardware
consumer / retail
EPC / project companies
selected distributors
```

Caution / often non-applicable:

```text
banks
insurers
asset managers
many software / platform businesses
```

M4 explicitly requires:

```text
balance-sheet date vs prior year-end
and
balance-sheet date vs prior-year comparable date
to be labeled differently
```

and forbids calling:

```text
year-end → half-year movement
```

YoY.

M4 also forbids deriving:

```text
DSO
inventory days
cash conversion cycle
```

without valid:

```text
average balances
revenue / COGS denominators
period length
```

M10 preserves these rules.

---

# 4. User-approved operating constraints

## 4.1 Free/public source only

No paid provider.

Use repository/cache/fixture evidence only.

Required:

```text
provider_source_fetches = 0
```

## 4.2 No model calls

Required:

```text
model_calls_real = 0
model_calls_fictional = 0
model_calls_judge = 0
```

## 4.3 Monitoring remains paused

Observe the approved eight US/KR monitoring schedule paths at task start/end.

If all remain paused:

```text
scheduler mutation = 0
```

If one exact approved path unexpectedly becomes active:

```text
pause only that exact path
record actual mutation
```

Do not resume automatically.

---

# 5. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Audit drift in:

```text
FinancialContext
M6–M9 financial adapters
balance-sheet source normalization
prior-year comparison projection
OpenDART exact-context promotion
compact AI context
source sufficiency
Daily Delta lifecycle
```

If unexplained semantic drift prevents a stable M10 baseline:

```text
STOP
UNEXPLAINED_M10_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 6. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement M10.

---

# 7. Primary M10 safety principle

M10 maps working-capital evidence.

It does NOT create a universal working-capital score.

Required:

```text
direct components first
derived metrics only when explicitly safe and frozen
missing data remains Unknown / unavailable
```

Do not optimize coverage by broad aliases or balance-sheet aggregates.

A safe blocked result is acceptable.

---

# 8. M10 sector routing

Before working-capital mapping, classify sector/framework.

## 8.1 Generic working-capital applicable / potentially material

Examples:

```text
manufacturing
memory / semiconductor
automotive
hardware
consumer / retail
EPC / construction
shipping / transport where trade balances are meaningful
selected distributors
product-stage biotech / medtech where inventory is material
```

## 8.2 Context-only / sector-dependent

Examples:

```text
holding company
SaaS
cloud / platform
asset-light services
pre-profit technology
```

These sectors may still have receivables/current liabilities,
but generic inventory/working-capital interpretation may be low-value.

## 8.3 Financial-sector exclusion

For:

```text
bank
insurance
reinsurance
financial institution
```

do not use generic operating-company inventory/receivables/working-capital semantics.

Required:

```text
financial_sector_generic_working_capital_emission_count = 0
```

Use:

```text
SECTOR_FRAMEWORK_REQUIRED
```

or existing equivalent.

---

# 9. Direct inventory taxonomy

Inventory may include exact source concepts such as:

```text
inventory
inventories
merchandise inventory
raw materials
work in process
finished goods
```

according to current canonical source semantics.

M10 must choose one of two representation strategies:

## Strategy A — exact aggregate inventory available

Prefer:

```text
inventory_total
```

as the direct canonical metric.

Do not also sum child components into another total.

## Strategy B — only child components available

Represent child components separately.

Do not derive an aggregate inventory total unless:

```text
component coverage is complete
non-overlapping
same date/currency/basis
```

and the M4/M10 contract explicitly defines the aggregate formula.

Default preference:

```text
official aggregate inventory fact
```

over reconstructed totals.

---

# 10. Inventory exclusions

Do not classify as operating inventory automatically:

```text
investment property
property held for sale
financial assets
biological assets
construction assets without semantic review
contract assets
prepaid expenses
other current assets
```

If a sector-specific inventory-like concept needs separate treatment:

```text
record separate semantic
```

rather than forcing it into generic inventory.

No fuzzy keyword matching.

---

# 11. Direct receivables taxonomy

M10 must distinguish:

```text
trade receivables / accounts receivable
```

from broader receivable concepts.

Preferred direct metrics:

```text
trade_receivables
accounts_receivable_trade
```

Broader concepts such as:

```text
other receivables
loans receivable
finance receivables
tax receivables
related-party receivables
total receivables
```

must not be silently treated as trade receivables.

If the source only supplies broad receivables:

```text
represent as broad_receivables_context
```

or leave unavailable according to canonical metric vocabulary.

Do not use it for trade-receivable growth interpretation.

---

# 12. Gross vs net receivables

If the official source provides:

```text
gross receivables
allowance
net receivables
```

define deterministic precedence.

Preferred user-facing financial-context metric for collection exposure:

```text
net trade receivables
```

when exact net carrying amount is official.

Do not sum gross + allowance.

Do not compare:

```text
current-period net
vs
prior-period gross
```

If only gross is available:

```text
preserve gross basis explicitly
```

and do not compare to net facts.

---

# 13. Trade payables / operating-liability context

Working-capital analysis may need:

```text
trade payables / accounts payable
```

as a direct component.

M10 may map exact trade-payable facts as:

```text
trade_payables
```

but must not classify:

```text
total current liabilities
debt
lease liabilities
tax liabilities
provisions
contract liabilities
```

as trade payables.

Trade payables are:

```text
working-capital context
```

not interest-bearing debt.

Preserve M9 debt semantics.

---

# 14. Current assets / current liabilities

M10 may preserve direct:

```text
current_assets
current_liabilities
```

as liquidity/context facts if already canonical.

But:

```text
current_assets - current_liabilities
```

must NOT automatically be labeled:

```text
operating_working_capital
```

because current assets/liabilities include:

```text
cash
debt
tax
other financing/non-operating items
```

Default M10 rule:

```text
NO universal net-working-capital derivation
```

unless an already-frozen canonical formula exists.

Do not create a new broad NWC formula in M10.

---

# 15. Point-in-time contract

Inventory, receivables and trade payables are balance-sheet facts.

Required:

```text
period.type = POINT_IN_TIME
period.end = exact balance-sheet date
period.start = null
duration_days = null
```

All direct comparison facts must retain exact dates.

No stale carry-forward.

---

# 16. Currency / unit / basis contract

Comparisons or any future derived context require:

```text
same verified financial currency
compatible unit scale
same entity scope
same statement basis
same semantic basis
```

No FX conversion in M10.

Do not copy price currency into financial facts.

Do not compare:

```text
consolidated inventory
vs
separate-company inventory
```

---

# 17. Comparison semantics

M10 should reuse the M7 prior-year projection / M6 comparison contract.

Allowed comparison labels:

## Prior-year comparable

```text
current 2026-06-30
vs
prior-year comparable 2025-06-30
```

where exact compatible point-in-time facts exist.

This may support:

```text
year-over-year balance growth
```

## Prior year-end

```text
current 2026-06-30
vs
2025-12-31
```

This is:

```text
change since prior year-end
```

NOT:

```text
YoY
```

Required explicit kind:

```text
prior_year_comparable
prior_year_end
```

Do not merge them.

---

# 18. Balance-delta derivation

M5/M6 already support derived-safe metadata such as:

```text
balance_absolute_delta
```

M10 may use a safe derived:

```text
current balance - prior balance
```

only if:

```text
same metric/basis/currency/entity
exact dates known
comparison kind explicit
```

The result must remain a balance change.

Do not interpret the delta in M10.

No percentage growth derivation unless already canonical and period denominator semantics are explicit.

Default:

```text
absolute delta + comparison lineage
```

is sufficient.

---

# 19. Inventory vs revenue growth

M4 identified:

```text
inventory growth vs revenue growth
```

as potentially useful decision evidence.

M10 does NOT activate this interpretation yet.

M10 may only ensure that future comparison can safely access:

```text
inventory balance comparison
revenue period comparison
```

with valid lineage.

Do not calculate a "inventory growth warning" or score.

Do not compare a point-in-time inventory balance directly to a revenue amount.

Future Directional reasoning may compare their growth rates qualitatively after the relevant contract is activated.

---

# 20. Receivables vs revenue growth

Same rule as inventory.

M10 may map:

```text
trade receivables balance
prior comparable trade receivables balance
revenue period facts
```

but does not create:

```text
collection risk score
```

or assume that receivables growing faster than revenue is automatically negative.

Interpretation remains dormant until Directional specificity activation.

---

# 21. DSO / inventory days / CCC forbidden by default

M10 must NOT derive:

```text
DSO
days inventory outstanding
days payable outstanding
cash conversion cycle
```

unless all required denominators/average balances/period lengths are already present
and a separate frozen design explicitly authorizes the formula.

Current M10 default:

```text
derived_efficiency_ratio_count = 0
```

Required negative fixtures proving such ratios are not produced from:

```text
single ending balance
single-quarter revenue
annualized quarter
incomplete COGS
```

---

# 22. Contract assets / unbilled receivables

EPC / construction / project companies may use:

```text
contract assets
unbilled receivables
```

These are not automatically trade receivables.

M10 must classify:

```text
SEPARATE_WORKING_CAPITAL_CONTEXT
```

or equivalent if exact canonical source semantics exist.

Do not merge them into trade receivables by default.

Future sector-specific reasoning may use them separately.

---

# 23. Contract liabilities / deferred revenue

Likewise:

```text
contract liabilities
deferred revenue
```

may be important working-capital/business context in selected sectors.

M10 must NOT subtract them into a universal operating-working-capital formula.

If existing exact canonical source facts exist:

```text
separate context only
```

unless current frozen design explicitly says otherwise.

---

# 24. Financial sector special handling

Banks/insurers often have receivables and current assets,
but these do not correspond to generic operating-company working capital.

Required:

```text
generic trade-receivable growth interpretation = disabled
generic inventory interpretation = disabled
generic working-capital derivation = disabled
```

Direct accounting facts remain in their existing financial-sector framework.

Do not promote them into M10 generic financial_context domain.

---

# 25. SaaS / platform caution

For many SaaS/platform businesses:

```text
inventory may be not applicable
trade receivables may matter
deferred revenue may matter
```

M10 should not require inventory.

Missing inventory:

```text
SECTOR_NOT_APPLICABLE
```

or equivalent,
not negative / unavailable evidence where sector routing proves non-applicability.

Do not create a universal source gate.

---

# 26. Manufacturing / hardware emphasis

For manufacturing/hardware,
M10 should prioritize exact support for:

```text
inventory
trade receivables
trade payables
```

where available.

However:

```text
high inventory
```

is not itself negative.

No thesis interpretation in M10.

---

# 27. Source taxonomy — US

Without provider fetches, inspect current official source support for exact US-GAAP/IFRS concepts.

Potential exact concept classes may include:

```text
InventoryNet
AccountsReceivableNetCurrent
AccountsReceivableNet
AccountsPayableCurrent
CurrentAssets
CurrentLiabilities
```

or canonical equivalents actually present in current source mapping.

Do not assume these names exist universally.

Implement only exact, reusable source-class mappings.

Required:

```text
new_sec_fuzzy_mapping_count = 0
ticker_specific_mapping_count = 0
```

If preserved US balance-sheet source payloads remain absent:

```text
do not claim real US archive coverage
```

Synthetic source-contract tests may prove mapper capability separately.

---

# 28. Source taxonomy — KR OpenDART

Use official OpenDART/XBRL exact concepts / canonical statement rows.

Potential semantic classes may include exact official concepts for:

```text
inventories
trade receivables
accounts receivable
trade payables
current assets
current liabilities
contract assets
contract liabilities
```

only when exact context and semantic identity are established.

M8 exact-context promotion remains authoritative.

Required:

```text
instant date
entity identifier
currency/unit
statement basis
filing identity
```

No account-name fuzzy matching.

Required:

```text
new_opendart_fuzzy_mapping_count = 0
```

---

# 29. Source conflict / precedence

If multiple official facts represent the same economic metric/date:

define deterministic precedence.

Prefer:

```text
exact aggregate fact
```

over child reconstruction when both are valid.

Prefer:

```text
net trade receivable
```

over gross/allowance reconstruction when exact net is available.

If equal-authority facts materially conflict:

```text
block promotion
record conflict
```

Do not average.

---

# 30. Duplicate / overlap control

Do not double count:

```text
inventory aggregate + inventory children

trade receivables aggregate + current/noncurrent child if aggregate includes both

accounts payable aggregate + child trade payable components
```

Required:

```text
overlap_conflict_count
overlap_blocked_count
aggregate_precedence_count
```

No parent+children summation without a complete explicit component contract.

---

# 31. `financial_context` emission boundary

Eligible direct metrics may include:

```text
inventory_total
inventory_child_component
trade_receivables_net
trade_receivables_gross
trade_payables
current_assets
current_liabilities
contract_assets_context
contract_liabilities_context
```

according to actual canonical metric vocabulary.

Eligible derived evidence in M10:

```text
balance_absolute_delta
```

only with safe comparison lineage.

Default derived evidence NOT allowed:

```text
operating_working_capital
net_working_capital
DSO
DIO
DPO
CCC
working_capital_score
```

unless an already-frozen project contract explicitly authorizes it.

Required:

```text
new_operating_working_capital_formula_count = 0
derived_efficiency_ratio_count = 0
```

---

# 32. Missing-data semantics

Required:

```text
missing inventory
!= negative

missing receivables
!= collection problem

missing payables
!= working-capital improvement

missing comparison
!= deterioration
```

Use:

```text
UNAVAILABLE
PARTIAL
SECTOR_NOT_APPLICABLE
```

according to existing evidence-quality/sector contracts.

No bearish default.

---

# 33. Model semantic input remains dormant

M10 may increase packet `financial_context` coverage.

M10 must NOT change compact AI context.

For representative working-capital fixtures:

```text
pre-M10 compact AI context hash
=
post-M10 compact AI context hash
```

Required:

```text
compact_ai_context_changed_count = 0
```

If leakage occurs:

```text
STOP
M10_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
```

---

# 34. Directional / Timing / renderer no-change

Required all zero:

```text
directional_prompt_change_count
price_timing_prompt_change_count
renderer_change_count
ownership_semantic_change_count
```

No model calls.

---

# 35. Source sufficiency no-change

M10 must not make inventory/receivables/working-capital a universal source gate.

Required:

```text
source_sufficiency_semantic_change_count = 0
universal_working_capital_gate_added_count = 0
```

Future Directional specificity may use these fields when available.

Missing fields do not make the model ineligible.

---

# 36. Daily Delta no-change

M3 lifecycle contract remains frozen.

Historical/baseline mapping of inventory/receivables:

```text
!= Daily Delta
```

Re-run fixtures proving:

```text
late-mapped prior balance
→ baseline enrichment
→ no strengthened/weakened
```

Required:

```text
daily_delta_semantic_change_count = 0
```

---

# 37. Warning no-change

M10 does not activate:

```text
inventory warning
receivables warning
working-capital warning
```

Required:

```text
warning_semantic_change_count = 0
warning_mutations = 0
```

Future warning logic may be a separate task after Directional semantics are frozen.

---

# 38. Idempotency / deterministic identity

Repeated mapping must produce:

```text
same direct fact IDs
same comparison/delta derived IDs
no duplicates
```

Derived balance-delta identity should depend on:

```text
formula/version
ordered input refs
comparison kind
dates
metric/basis identity
```

No random/runtime identity.

---

# 39. Positive fixture matrix

At minimum:

```text
manufacturing inventory aggregate direct fact

inventory prior-year comparable

inventory prior-year-end comparison

trade receivables net direct fact

trade receivables comparable prior-year fact

trade payables direct fact

current assets / current liabilities direct context

contract asset separate context

contract liability separate context

KR exact OpenDART inventory context

KR exact OpenDART trade receivables context

US exact SEC source-class synthetic contract fixture

balance absolute delta with prior-year comparable

balance absolute delta with prior-year-end label

same input rerun idempotent
```

Synthetic fixtures must be labeled separately from real archive coverage.

---

# 40. Negative fixture matrix

At minimum:

```text
year-end → half-year labeled YoY rejected

inventory aggregate + children double-count attempt

gross current receivables vs net prior-period comparison

broad receivables treated as trade receivables

loan receivable treated as trade receivable

total current assets treated as inventory

total current liabilities treated as trade payables

contract asset merged into trade receivables

contract liability subtracted into universal NWC

current assets - current liabilities labeled operating working capital

DSO derived from ending AR + one-quarter revenue

inventory days from ending inventory + incomplete COGS

CCC with missing DPO/average balances

different balance-sheet dates

currency mismatch

entity/statement basis mismatch

financial-sector generic working-capital emission

ticker-specific source mapping branch

OpenDART fuzzy account-name mapping

price currency copied to financial fact
```

---

# 41. Real archive coverage audit

Using preserved repository/cache evidence only, report separately:

```text
US non-financial candidates
US inventory direct
US trade receivables direct
US trade payables direct
US comparable balance pairs

KR non-financial candidates
KR inventory direct
KR trade receivables direct
KR trade payables direct
KR comparable balance pairs

financial-sector candidates routed out

sector-not-applicable candidates
```

Do not claim universal market coverage.

If US preserved balance-sheet payload count remains zero:

```text
coverage_claim =
NO_REAL_US_ARCHIVE_COVERAGE_CLAIM
```

while still testing generic mapper capability synthetically/offline.

---

# 42. Comparison coverage audit

Required counts:

```text
prior_year_comparable_inventory_count
prior_year_end_inventory_count

prior_year_comparable_receivables_count
prior_year_end_receivables_count

prior_year_comparable_payables_count
prior_year_end_payables_count
```

Keep these categories separate.

Do not collapse them into "YoY count".

---

# 43. Denial reason taxonomy

Required reasons should include at least:

```text
sector_not_applicable
unsupported_semantic
broad_receivable_not_trade
aggregate_child_overlap
gross_net_basis_mismatch
point_in_time_mismatch
currency_mismatch
entity_scope_mismatch
statement_basis_mismatch
comparison_kind_ambiguous
prior_comparable_missing
prior_year_end_missing
source_conflict
exact_context_unresolved
```

Report counts.

Do not weaken rules to reduce denials.

---

# 44. Mapping activation surface

Preferred changed code:

```text
generic inventory/receivables/working-capital component adapter
exact canonical balance-sheet concept registry
OpenDART exact-context mapping
comparison projection plumbing
tests
```

Avoid:

```text
Directional Core
Price-Timing
renderer
monitoring lifecycle
notification
scheduler
```

If M10 requires semantic model activation:

```text
STOP
M10_SCOPE_EXCEEDED
```

---

# 45. Validation requirements

Run:

```text
focused pytest
full repository pytest
ruff
git diff --check
```

Required all PASS.

Focused suite should include:

```text
M5 FinancialContext
M6/M7 comparison/lineage
M8 source-class mapping
M9 debt/liquidity regression
M10 working-capital mapping
OpenDART exact-context
SEC exact source-class mapping
compact AI non-leak
source sufficiency no-change
Daily Delta no-change
historical packet compatibility
```

No model tests.

No live provider tests.

---

# 46. Production side-effect firewall

Required:

```text
model_calls_real = 0
model_calls_fictional = 0
model_calls_judge = 0

provider_source_fetches = 0

production_db_mutations = 0
monitoring_registrations = 0
assessment_persistence_mutations = 0
warning_mutations = 0
notification_queue_writes = 0
production_sends = 0

main_merges = 0
deployments = 0
live_v2_changes = 0
night_futures_changes = 0

automatic_monitoring_resume = 0
```

---

# 47. Required artifacts — provenance / design reuse

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m10-scope-freeze
04-m4-working-capital-contract-reuse-proof
05-m5-m9-contract-reuse-proof
```

---

# 48. Required artifacts — mapping design / implementation

Produce:

```text
06-current-working-capital-source-inventory
07-sector-routing-contract
08-inventory-taxonomy
09-receivables-taxonomy
10-trade-payables-taxonomy
11-contract-assets-liabilities-policy
12-working-capital-formula-boundary
13-comparison-kind-contract
14-working-capital-adapter-contract
15-working-capital-implementation-diff
16-source-mapping-activation-surface
```

---

# 49. Required artifacts — coverage / controls

Produce:

```text
17-us-working-capital-source-support-audit
18-kr-working-capital-source-support-audit
19-financial-sector-routing-audit
20-gross-net-receivables-control
21-aggregate-child-overlap-control
22-comparison-labeling-control
23-efficiency-ratio-negative-control
24-real-archive-coverage
25-comparison-coverage-audit
26-denial-accounting
```

---

# 50. Required artifacts — semantic no-change proofs

Produce:

```text
27-compact-ai-context-non-leak-proof
28-directional-prompt-no-change-proof
29-price-timing-no-change-proof
30-source-sufficiency-no-change-proof
31-daily-delta-no-change-proof
32-warning-no-change-proof
33-historical-packet-compatibility
34-working-capital-idempotency-proof
```

---

# 51. Required artifacts — tests / decisions

Produce:

```text
35-positive-fixture-manifest
36-negative-fixture-manifest
37-focused-test-results
38-full-test-results
39-ruff-and-diff-results

40-non-operating-next-scope-decision
41-directional-specificity-activation-decision
42-source-sufficiency-future-review-decision
43-production-no-change
44-schedule-pause-observation
45-master-workflow-update
46-program-completion
```

Expected:

```text
Directional specificity activation =
NOT_IN_M10

source sufficiency =
UNCHANGED_IN_M10
```

---

# 52. M10 acceptance criteria

M10 is COMPLETE if:

```text
inventory taxonomy is explicit

trade receivables are distinguished from broad/non-trade receivables

trade payables are distinguished from total current liabilities

contract assets/liabilities remain separate context

point-in-time dates are exact

prior-year comparable and prior-year-end comparisons are distinct

year-end → half-year is never labeled YoY

no universal operating-working-capital formula is invented

DSO/DIO/DPO/CCC are not derived without a separately frozen valid contract

financial-sector generic working-capital logic is blocked

missing inventory/receivables remains nonnegative

no ticker-specific mapping
no fuzzy OpenDART mapping

M9 debt/liquidity semantics remain unchanged

compact AI context unchanged

Directional / Timing / renderer unchanged

source sufficiency unchanged

Daily Delta unchanged

warning semantics unchanged

historical packet compatibility preserved

focused/full tests PASS
ruff PASS
git diff --check PASS

all model/provider/production side-effect counts = 0
```

M10 does NOT require:

```text
all issuers to have working-capital coverage

universal US real archive coverage

operating working capital formula

efficiency ratios

non-operating effect mapping

Directional Core consumption of financial_context

model proof
real holdout
production readiness
```

---

# 53. Next-scope decision

If M10 passes, the remaining M4 higher-risk domain is:

```text
NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION
```

unless M10 exposes a bounded generic mapping defect requiring repair first.

Possible outcomes:

## A. M10 complete

Default:

```text
next_scope =
NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION
```

## B. Generic working-capital source mapping incomplete

```text
next_scope =
BOUNDED_WORKING_CAPITAL_SOURCE_MAPPING_REPAIR
```

only if the gap is generic and material.

## C. Only sector-specific / ticker-specific gaps remain

Do not add exceptions.

Proceed to:

```text
NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION
```

## D. M4 financial domains become sufficiently covered after M10

Do not activate Directional Core in M10.

Record future:

```text
DIRECTIONAL_SPECIFICITY_READINESS_REVIEW
```

after non-operating domain decision is resolved.

---

# 54. Master workflow update

Update:

```text
docs/MASTER_WORKFLOW.md
```

Expected transition:

```text
M9 COMPLETE
→
M10 COMPLETE
→
next bounded higher-risk financial domain
```

Production readiness remains:

```text
NOT_READY
```

Monitoring remains paused.

---

# 55. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
report_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

m1_status
m2_status
m3_status
m4_status
m5_status
m6_status
m7_status
m8_status
m9_status
m10_status

working_capital_adapter_status

inventory_component_class_count
receivables_component_class_count
trade_payables_component_class_count

contract_asset_policy
contract_liability_policy
working_capital_formula_policy

us_nonfinancial_candidate_count
us_inventory_direct_count
us_trade_receivables_direct_count
us_trade_payables_direct_count
us_comparable_balance_pair_count

kr_nonfinancial_candidate_count
kr_inventory_direct_count
kr_trade_receivables_direct_count
kr_trade_payables_direct_count
kr_comparable_balance_pair_count

financial_sector_candidate_count
financial_sector_generic_working_capital_emission_count
sector_not_applicable_count

prior_year_comparable_inventory_count
prior_year_end_inventory_count
prior_year_comparable_receivables_count
prior_year_end_receivables_count
prior_year_comparable_payables_count
prior_year_end_payables_count

gross_net_basis_conflict_count
aggregate_child_overlap_conflict_count
comparison_labeling_violation_count

new_operating_working_capital_formula_count
derived_efficiency_ratio_count

ticker_specific_mapping_count
new_sec_fuzzy_mapping_count
new_opendart_fuzzy_mapping_count

working_capital_idempotency_status

compact_ai_context_changed_count
directional_prompt_change_count
price_timing_prompt_change_count
renderer_change_count

source_sufficiency_semantic_change_count
daily_delta_semantic_change_count
warning_semantic_change_count

legacy_fixture_count
legacy_parse_pass_count
legacy_hash_unchanged_count

positive_fixture_count
positive_fixture_pass_count
negative_fixture_count
negative_fixture_rejected_count

recommended_next_scope

model_calls_real
model_calls_fictional
model_calls_judge
provider_source_fetches

production_db_mutations
monitoring_registrations
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

main_merges
deployments
live_v2_changes
night_futures_changes

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

production_readiness
status
stop_reason
next_scope
```

Anything not measured must remain:

```text
NOT_MEASURED
```

---

# 56. Artifact integrity

Freeze:

```text
program completion
master workflow update
all reports
```

before final artifact-index creation.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

---

# 57. Final task principle

M9 answered:

```text
what is safe debt
what is safe liquidity
when net debt can be derived
```

M10 should answer:

```text
what is actual inventory
what is actual trade receivables/payables
what balance comparison is valid
and what should NOT be called operating working capital
```

The correct flow is:

```text
exact direct balance-sheet components
→ sector routing
→ same-date / same-basis validation
→ safe comparison lineage
→ financial_context only
```

Not:

```text
all receivables = trade receivables
```

Not:

```text
current assets - current liabilities = operating working capital
```

Not:

```text
year-end → half-year = YoY
```

Not:

```text
ending receivables / quarterly revenue = DSO
```

Not:

```text
missing inventory = bearish
```

Not:

```text
let financial_context leak into model input
```

And not:

```text
resume production monitoring
```

Prefer exact component context over a misleading working-capital summary.
