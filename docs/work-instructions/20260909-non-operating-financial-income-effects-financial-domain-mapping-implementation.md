# Thesis Monitor — Non-Operating / Financial Income Effects Financial Domain Mapping Implementation

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-non-operating-financial-income-effects-financial-domain-mapping-implementation.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-non-operating-financial-income-effects-financial-domain-mapping-implementation-report.zip
```

Master-workflow phase:

```text
M11 — Higher-Risk Financial Domain Mapping
       Non-Operating / Financial Income Effects
```

This task begins only after M10 has completed.

M10 implemented:

```text
inventory
trade/broad receivables
trade/broad payables
working-capital point-in-time comparison context
```

and recommended:

```text
NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION
```

M11 implements only the final M4 financial-domain backlog:

```text
non-operating / financial income effects
```

M11 must NOT implement:

```text
Directional Core financial_context consumption
source-sufficiency gate changes
new warning semantics
normalized earnings
adjusted earnings
model proof
real holdout
production deployment
schedule resume
```

The purpose is to represent, with exact statement/period/basis provenance:

```text
financial income
financial cost
interest income / expense
foreign-exchange effects
other income / expense
asset disposal effects
tax effects where separately relevant
```

so future reasoning can distinguish:

```text
operating business performance
from
non-operating / financing / other effects
```

without inventing normalization.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260909-inventory-receivables-working-capital-financial-domain-mapping-implementation-report.zip
```

Verified SHA-256:

```text
942274b7dd10150ddbe5972d77f4804fbf275502dc989f0672ca8de7d9b8da81
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M10 state:

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
M10 = COMPLETE

status = M10_COMPLETE
production_readiness = NOT_READY

next_scope =
NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION
```

Reported M10 provenance:

```text
base_sha =
2e93eb9dcfab7594007af0139d6e2bd7c15a5009

work_instruction_commit =
584876a091fbf3ad10b833fe3706c7c2daf5a3c2

implementation_commit =
c898343db3d416243183c2c62746b08dc461b6a2

branch =
codex/20260909-inventory-receivables-working-capital-financial-domain-mapping-implementation
```

M10 uses the established pre-report-commit artifact convention:

```text
report_commit = NOT_MEASURED
final_head_sha = NOT_MEASURED
```

At M11 start use actual repository HEAD as authority and record the actual M10 final/report state.

M10 artifact integrity:

```text
payload count = 47
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

---

# 2. M10 facts frozen for M11

M10 measured:

```text
KR non-financial candidates = 6

KR inventory direct = 6
KR trade receivables direct = 5
KR trade payables direct = 5
KR comparable balance pairs = 38

financial-sector candidates = 1
financial-sector generic working-capital emissions = 0
```

Comparison semantics:

```text
prior-year comparable inventory = 0
prior-year-end inventory = 6

prior-year comparable receivables = 0
prior-year-end receivables = 8

prior-year comparable payables = 0
prior-year-end payables = 6

comparison labeling violations = 0
```

M10 safety:

```text
NO universal operating-working-capital formula
DSO/DIO/DPO/CCC derivations = 0
ticker-specific mappings = 0
SEC fuzzy mappings = 0
OpenDART fuzzy mappings = 0

compact AI context changed = 0
Directional prompt changed = 0
Price-Timing prompt changed = 0
renderer changed = 0
source sufficiency changed = 0
Daily Delta changed = 0
warning semantics changed = 0
```

Preserve all M10 boundaries.

---

# 3. M4 frozen non-operating / financial-effects design

M4 defined the purpose as:

```text
separate operating business performance
from
financial / other / non-operating effects
```

Potential evidence:

```text
financial income
financial cost

interest income
interest expense

foreign-exchange gain/loss
other financial gain/loss

other income
other expense

asset disposal gain/loss

tax expense / tax benefit where separately relevant
```

Hard safety:

```text
do not call an item non-operating
when the sector treats it as core operating economics
```

Especially:

```text
banks
insurers
reinsurance
financial institutions
```

Future Directional purpose:

```text
net income improvement
must not automatically be called operating improvement
when material non-operating effects explain the change

operating deterioration
must not be hidden by a material non-operating gain
```

M4 forbids:

```text
invented normalization
```

M11 implements representation/mapping only.

---

# 4. User-approved operating constraints

## 4.1 Free/public sources only

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

Observe the approved eight US/KR monitoring paths at task start/end.

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
income-statement normalization
M6–M10 financial adapters
period/comparison projection
OpenDART exact-context promotion
SEC/IFRS source-class mappings
compact AI context
source sufficiency
Daily Delta lifecycle
```

If unexplained semantic drift prevents a stable M11 baseline:

```text
STOP
UNEXPLAINED_M11_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 6. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement M11.

---

# 7. Primary M11 safety principle

M11 maps financial/non-operating evidence.

It does NOT decide what is recurring, normalized or high-quality earnings.

Required:

```text
exact direct components first

derived net effects only where component scope is explicit

no adjusted net income
no normalized EPS
no recurring-earnings score
```

If classification is ambiguous:

```text
keep direct source semantic
or
block generic non-operating promotion
```

Prefer Unknown over a misleading operating/non-operating split.

---

# 8. Sector routing gate

## 8.1 Generic operating-company path

M11 generic non-operating separation may apply to:

```text
standard operating companies
semiconductor / memory
automotive
shipping / transport
consumer
EPC / construction
SaaS / platform
biotech
pre-profit technology
holding company
```

subject to source semantics.

## 8.2 Financial-sector exclusion

For:

```text
bank
insurance
reinsurance
financial institution
```

do NOT use generic rules such as:

```text
interest income = non-operating
financial income = non-operating
financial cost = non-operating
```

These may be core business economics.

Required:

```text
financial_sector_generic_non_operating_emission_count = 0
```

Use:

```text
SECTOR_FRAMEWORK_REQUIRED
```

or current canonical equivalent.

Direct source facts may remain in existing financial-sector accounting data,
but M11 must not promote them into the generic operating-company non-operating contract.

---

# 9. Period contract

Income-statement financial/non-operating effects are duration facts.

Required period types may include:

```text
QTD
YTD
FY
```

and later:

```text
TTM
```

only if an existing safe derivation already exists.

For direct source mapping preserve:

```text
period_start
period_end
period_type
duration_days
fiscal_year
fiscal_quarter where applicable
```

Do not compare:

```text
QTD effect
with
YTD operating profit
```

as though same period.

Do not annualize a quarter.

---

# 10. Currency / unit / basis contract

Any direct/derived combination must require compatible:

```text
financial currency
unit scale
entity scope
statement basis
attribution basis where applicable
period
```

No FX conversion in M11.

Do not use price currency.

Do not combine:

```text
consolidated financial expense
with
separate-company net income
```

Fail closed.

---

# 11. Direct taxonomy — financial income

Inspect current canonical official-source support for exact semantics such as:

```text
financial_income
finance_income
interest_income
foreign_exchange_gain
derivative_gain
financial_asset_valuation_gain
```

according to actual source taxonomy.

Do not assume all are present.

Do not classify:

```text
revenue
operating income
investment income of a financial institution
```

as generic non-operating financial income.

Use exact source meaning.

---

# 12. Direct taxonomy — financial cost

Potential exact classes may include:

```text
financial_cost
finance_cost
interest_expense
foreign_exchange_loss
derivative_loss
financial_asset_valuation_loss
```

according to actual canonical source semantics.

Do not classify:

```text
COGS
SG&A
lease payment cash flow
total liabilities
```

as financial cost.

No fuzzy concept matching.

---

# 13. Interest income / expense

For non-financial operating companies:

```text
interest income
interest expense
```

may be represented as separate financial components.

Do not automatically net them if:

```text
one side is absent
period differs
statement basis differs
```

If both exact compatible components exist:

```text
financial_interest_net_effect
```

may be a safe derived metric only if M11 explicitly freezes that formula.

Default preference:

```text
represent direct components
```

and derive net only when the formula is clearly useful and non-overlapping.

No model interpretation.

---

# 14. Foreign-exchange effects

M11 must distinguish, where source semantics permit:

```text
foreign_exchange_gain
foreign_exchange_loss
```

or official aggregate net FX effect.

Do not reconstruct:

```text
FX gain - FX loss
```

if official source presents an aggregate that may include overlapping components
without a clear parent/child hierarchy.

Do not assume FX is recurring or non-recurring.

Future reasoning may treat material FX separately.

M11 only maps exact semantics.

---

# 15. Other income / other expense

`other income` and `other expense` are broad categories.

Default M11 policy:

```text
SEPARATE_BROAD_CONTEXT
```

They must not automatically be called:

```text
financial income
financial cost
one-off
non-recurring
```

If exact child components exist, preserve them separately.

Do not create a generic:

```text
other_income_minus_other_expense
```

unless the source scope is explicit and non-overlapping.

---

# 16. Asset disposal effects

If exact official source facts exist for:

```text
gain on disposal of PPE
loss on disposal of PPE
gain/loss on disposal of investment assets
```

represent as separate direct components.

Do not classify all disposal gains/losses as recurring/non-recurring automatically.

Do not subtract them from net income to create normalized earnings.

Future reasoning may use them as explanatory context.

---

# 17. Fair-value / valuation gains and losses

If exact source facts exist:

```text
fair_value_gain
fair_value_loss
valuation_gain
valuation_loss
```

keep them separate.

Do not merge unrelated:

```text
financial instruments
investment property
biological assets
derivatives
```

into one generic valuation effect unless official aggregate semantics prove the grouping.

No recurrence assumption.

---

# 18. Equity-method / associate income

Income from:

```text
equity-method investments
associates
joint ventures
```

may be economically important.

M11 must NOT automatically classify it as:

```text
financial income
```

or:

```text
one-off non-operating
```

Default:

```text
SEPARATE_INVESTMENT_RESULT_CONTEXT
```

unless the project's frozen source taxonomy already has a specific semantic.

Holding-company caution is especially important.

---

# 19. Tax effects

Tax expense/benefit is below pre-tax income.

M11 may map exact:

```text
income_tax_expense
income_tax_benefit
```

as separate context.

Do NOT use tax to explain:

```text
operating performance
```

and do not construct:

```text
normalized after-tax earnings
```

M11 may support future statements such as:

```text
net income changed partly because tax burden changed
```

only after Directional semantics are activated later.

No effective tax rate derivation unless a separate frozen contract exists.

Required:

```text
effective_tax_rate_derivation_count = 0
```

---

# 20. Operating-profit boundary

M11 must preserve the authoritative operating-profit metric where available.

Do not reconstruct operating profit as:

```text
pre-tax income
minus/plus selected financial effects
```

unless an official operating profit fact is absent and a separately frozen accounting bridge exists.

Current M11 default:

```text
NO reconstructed operating profit
```

Required:

```text
reconstructed_operating_profit_count = 0
```

---

# 21. Net-income attribution boundary

Net income may have:

```text
total
parent
common shareholders
continuing operations
discontinued operations
```

bases.

M11 must not compare a financial/non-operating component with a net-income basis
that is attribution-incompatible when making a derived bridge.

M11 does NOT need to derive a full net-income bridge.

Default:

```text
direct net-income fact remains separate
direct financial/non-operating components remain separate
```

Future reasoning may reference them if periods/bases are compatible.

---

# 22. Continuing vs discontinued operations

If source evidence distinguishes:

```text
continuing operations
discontinued operations
```

M11 must preserve the distinction.

Do not treat discontinued-operation gain/loss as ordinary operating performance.

Do not create a normalized continuing-operations metric unless official direct facts exist.

If official continuing-operations income exists:

```text
represent directly
```

under its own canonical metric.

No subtraction from total net income unless a frozen safe derivation exists.

---

# 23. Parent / child taxonomy overlap

Income statements often contain:

```text
financial_income aggregate
interest_income child
FX_gain child
```

or:

```text
other_income aggregate
asset_disposal_gain child
```

M11 must prevent double counting.

Define deterministic precedence / hierarchy.

Do not sum:

```text
aggregate + children
```

Required counts:

```text
aggregate_child_overlap_conflict_count
aggregate_precedence_count
child_detail_preserved_count
```

A parent aggregate may be represented alongside children for descriptive lineage only
if the contract marks the hierarchy and prevents derived summation.

---

# 24. Derived net financial effect

M11 may define ONE bounded safe derived metric only if useful:

```text
net_financial_income_effect
=
compatible financial income
-
compatible financial cost
```

Conditions:

```text
both sides are exact official aggregate concepts
same period/currency/unit/entity/basis
the aggregates do not overlap external components
```

If only child components exist:

```text
do not synthesize a total
```

unless completeness is explicitly proven.

If the source uses sign-convention expenses already negative:

normalize arithmetic only through an existing canonical sign helper.

Do not guess sign convention.

If safe aggregate derivation cannot be frozen:

```text
do not implement it
```

and represent direct components only.

---

# 25. No universal non-operating total

M11 must NOT create:

```text
total_non_operating_income
total_non_operating_expense
net_non_operating_effect
```

by summing arbitrary:

```text
financial
other
FX
disposal
valuation
associate
tax
```

components.

These categories can overlap and differ by accounting presentation.

Required:

```text
universal_non_operating_total_formula_count = 0
```

unless an official direct aggregate exists under a canonical metric.

---

# 26. No adjusted / normalized earnings

Hard acceptance gate.

Required zero:

```text
adjusted_net_income_derivation_count
normalized_net_income_derivation_count
normalized_eps_derivation_count
recurring_earnings_score_count
```

Do not subtract one-offs.

Do not decide recurrence.

Do not produce:

```text
core earnings
underlying earnings
```

unless an official company-reported metric already exists and is clearly labeled as company-defined/non-GAAP context; even then do not treat it as canonical GAAP/IFRS earnings.

M11 mapping is accounting evidence, not analyst normalization.

---

# 27. Materiality is not activated

M4 defined future qualitative materiality states.

M11 does NOT decide:

```text
MATERIAL
SUPPORTIVE
CONTEXT_ONLY
```

for investment reasoning.

It may preserve raw amount/period evidence.

Do not create percentage-of-net-income thresholds or scorecards.

Required:

```text
materiality_scoring_rule_count = 0
```

---

# 28. Source taxonomy — KR OpenDART

Use exact official OpenDART/XBRL concepts and exact duration contexts.

Potential classes may include official concepts equivalent to:

```text
finance income
finance costs
interest income
interest expense
foreign exchange gain/loss
other income/expense
income tax expense
```

only where exact semantics exist.

M8 exact-context promotion remains authoritative.

Required:

```text
period start/end
entity identifier
currency/unit
statement basis
filing identity
```

No fuzzy Korean account-name mapping.

Required:

```text
new_opendart_fuzzy_mapping_count = 0
```

Exact generic concept mappings are allowed where source-standard semantics are clear.

---

# 29. Source taxonomy — US / foreign issuers

Without provider calls, inspect preserved official SEC/IFRS source/cache evidence.

Potential source classes:

```text
US-GAAP income-statement concepts
IFRS foreign-issuer concepts
filing XBRL exact facts
```

Do not assume preserved archive coverage.

If real source rows are absent:

```text
NO_REAL_US_ARCHIVE_COVERAGE_CLAIM
```

Synthetic contract fixtures may prove mapping capability separately.

No ticker-specific mapping.

Required:

```text
ticker_specific_mapping_count = 0
new_sec_fuzzy_mapping_count = 0
```

---

# 30. Sign convention contract

Financial expense/loss facts may be reported:

```text
positive magnitude
negative signed amount
```

depending on source.

M11 must define a canonical sign policy for each metric.

Do not perform arithmetic until sign semantics are explicit.

Preferred representation:

```text
direct source amount
+
canonical economic role metadata:
INCOME / EXPENSE / GAIN / LOSS
```

If current repository already normalizes signs, reuse it.

Do not create a second sign engine.

Required artifact:

```text
sign-convention-contract
```

---

# 31. Statement presentation contract

Some issuers present:

```text
finance income and finance cost separately
```

others:

```text
net finance income/cost
```

others embed selected items within broader lines.

M11 must preserve the issuer's official presentation.

Do not force all issuers into the same component granularity.

Allowed state:

```text
DIRECT_AGGREGATE
DIRECT_COMPONENT
BROAD_CONTEXT
UNAVAILABLE
```

Future reasoning should use what is safely known.

---

# 32. Operating-company vs holding-company caution

Holding companies may have large:

```text
dividend income
equity-method income
investment disposal gains
financial income
```

that are economically central.

M11 generic mapping may represent exact components,
but must not label them:

```text
non-core
one-off
low-quality
```

Attach sector/framework context only.

Directional interpretation comes later.

---

# 33. Pre-profit / biotech caution

For pre-profit companies:

```text
interest income
FX
fair-value changes
```

may materially affect net loss.

M11 may map them,
but must not call a smaller net loss:

```text
operating improvement
```

This is a future Directional reasoning rule.

No operating-quality conclusion in M11.

---

# 34. `financial_context` emission boundary

Eligible direct metrics may include, according to canonical vocabulary:

```text
financial_income
financial_cost
interest_income
interest_expense
foreign_exchange_gain
foreign_exchange_loss
other_income_context
other_expense_context
asset_disposal_gain
asset_disposal_loss
fair_value_gain
fair_value_loss
equity_method_income_context
income_tax_expense
income_tax_benefit
continuing_operations_income
discontinued_operations_income
```

Eligible derived metric:

```text
net_financial_income_effect
```

ONLY if M11 freezes the exact aggregate formula under section 24.

Default derived metrics NOT allowed:

```text
net_non_operating_effect
normalized_net_income
adjusted_net_income
normalized_eps
effective_tax_rate
reconstructed_operating_profit
recurring_earnings_score
```

---

# 35. Missing-data semantics

Required:

```text
missing financial-income breakdown
!= operating improvement

missing other-income detail
!= clean earnings

missing tax detail
!= negative evidence

missing FX breakdown
!= stable earnings
```

Use:

```text
UNAVAILABLE
PARTIAL
SECTOR_FRAMEWORK_REQUIRED
```

as appropriate.

No bullish/bearish default.

---

# 36. Model semantic input remains dormant

M11 may increase packet `financial_context` coverage.

M11 must NOT change compact AI context.

For representative fixtures:

```text
pre-M11 compact AI context hash
=
post-M11 compact AI context hash
```

Required:

```text
compact_ai_context_changed_count = 0
```

If leakage occurs:

```text
STOP
M11_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
```

---

# 37. Directional / Timing / renderer no-change

Required all zero:

```text
directional_prompt_change_count
price_timing_prompt_change_count
renderer_change_count
ownership_semantic_change_count
```

No model calls.

---

# 38. Source sufficiency no-change

M11 must not make non-operating breakdown a universal source gate.

Required:

```text
source_sufficiency_semantic_change_count = 0
universal_non_operating_gate_added_count = 0
```

Missing breakdown does not make the directional model ineligible.

---

# 39. Daily Delta no-change

M3 lifecycle remains frozen.

Historical/baseline promotion of financial/non-operating components:

```text
!= Daily Delta
```

Required fixture:

```text
late-mapped historical financial income/cost
→ baseline enrichment
→ no strengthened/weakened
```

Required:

```text
daily_delta_semantic_change_count = 0
```

---

# 40. Warning no-change

M11 does not activate warnings such as:

```text
earnings-quality warning
FX warning
non-operating gain warning
```

Required:

```text
warning_semantic_change_count = 0
warning_mutations = 0
```

These may be designed later after Directional semantics are activated.

---

# 41. Idempotency / deterministic identity

Repeated mapping must produce:

```text
same direct fact IDs
same safe derived financial-net-effect ID if implemented
no duplicates
```

Derived identity must depend on:

```text
formula/version
ordered canonical input refs
period/basis identity
```

No runtime/random identity.

---

# 42. Positive fixture matrix

At minimum:

```text
non-financial issuer:
direct financial income + financial cost same YTD period

direct interest income
direct interest expense

direct FX gain
direct FX loss

broad other income context
broad other expense context

asset disposal gain

income tax expense

official continuing-operations income

KR exact OpenDART financial-income context

KR exact OpenDART financial-cost context

US/IFRS exact synthetic source-class capability fixture

aggregate financial income/cost safe net derivation
IF implemented under section 24

holding-company component preserved without "non-core" label

idempotent repeated mapping
```

Synthetic fixtures must be labeled separately from real archive coverage.

---

# 43. Negative fixture matrix

At minimum:

```text
bank interest income promoted as generic non-operating

insurer investment income promoted as generic non-operating

financial-sector finance cost promoted through operating-company route

QTD financial income + YTD financial cost netted

currency mismatch

consolidated vs separate basis mismatch

financial-income aggregate + child components double-counted

other income automatically labeled financial income

other income automatically labeled one-off

equity-method income automatically labeled financial income

disposal gain subtracted to create normalized net income

tax benefit used to reconstruct operating profit

net income attribution mismatch

continuing vs discontinued operations mixed

universal non-operating total derived

normalized EPS derived

effective tax rate derived

ticker-specific mapping branch

OpenDART fuzzy account-name mapping

price currency copied into financial fact
```

---

# 44. Real archive coverage audit

Using preserved repository/cache evidence only, report separately:

```text
US/foreign non-financial issuer candidates
US financial-income direct
US financial-cost direct
US interest-income direct
US interest-expense direct
US FX direct
US other-income/expense context
US tax direct
US safe derived financial-net-effect count

KR non-financial issuer candidates
KR financial-income direct
KR financial-cost direct
KR interest-income direct
KR interest-expense direct
KR FX direct
KR other-income/expense context
KR tax direct
KR safe derived financial-net-effect count

financial-sector candidates routed out
```

Do not claim universal market coverage.

If US preserved official income-statement payloads are incomplete:

```text
coverage claim must say so explicitly
```

---

# 45. Period-comparison coverage audit

Where compatible current/prior periods already exist,
report separately:

```text
QTD comparable component pairs
YTD comparable component pairs
FY comparable component pairs
```

Do not mix duration types.

M11 does not need to derive growth percentages.

Comparison lineage is enough.

---

# 46. Overlap / conflict accounting

Required reason taxonomy should include at least:

```text
sector_not_applicable

aggregate_child_overlap

period_mismatch

currency_mismatch

entity_scope_mismatch

statement_basis_mismatch

attribution_basis_mismatch

continuing_discontinued_mismatch

broad_context_not_specific

sign_semantics_unresolved

source_conflict

exact_context_unresolved

component_scope_incomplete
```

Do not weaken rules to reduce denials.

---

# 47. Mapping activation surface

Preferred changed code:

```text
generic non-operating/financial-effects adapter
exact canonical income-statement concept registry
OpenDART/SEC/IFRS exact source mapping
sign/role metadata helper
tests
```

Avoid:

```text
Directional Core
Price-Timing
renderer
monitoring lifecycle
warning engine
notification
scheduler
```

If M11 requires model semantic activation:

```text
STOP
M11_SCOPE_EXCEEDED
```

---

# 48. Validation requirements

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
M6/M7 duration/comparison/lineage
M8 source-class mapping
M9 debt/liquidity regression
M10 working-capital regression
M11 non-operating/financial-effects mapping
OpenDART exact-context mapping
SEC/IFRS exact source mapping
compact AI non-leak
source sufficiency no-change
Daily Delta no-change
historical packet compatibility
```

No model tests.

No live provider tests.

---

# 49. Production side-effect firewall

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

# 50. Required artifacts — provenance / design reuse

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m11-scope-freeze
04-m4-non-operating-contract-reuse-proof
05-m5-m10-contract-reuse-proof
```

---

# 51. Required artifacts — mapping design / implementation

Produce:

```text
06-current-non-operating-source-inventory
07-sector-routing-contract
08-financial-income-cost-taxonomy
09-interest-income-expense-taxonomy
10-fx-and-valuation-effects-taxonomy
11-other-income-expense-policy
12-disposal-effects-policy
13-equity-method-investment-result-policy
14-tax-effects-policy
15-continuing-discontinued-operations-policy
16-sign-convention-contract
17-aggregate-child-overlap-contract
18-net-financial-effect-derivation-decision
19-non-operating-adapter-contract
20-non-operating-implementation-diff
21-source-mapping-activation-surface
```

---

# 52. Required artifacts — coverage / controls

Produce:

```text
22-us-non-operating-source-support-audit
23-kr-non-operating-source-support-audit
24-financial-sector-routing-audit
25-aggregate-child-overlap-control
26-normalized-earnings-negative-control
27-tax-operating-boundary-control
28-continuing-discontinued-boundary-control
29-sign-semantics-control
30-real-archive-coverage
31-period-comparison-coverage
32-denial-accounting
```

---

# 53. Required artifacts — semantic no-change proofs

Produce:

```text
33-compact-ai-context-non-leak-proof
34-directional-prompt-no-change-proof
35-price-timing-no-change-proof
36-source-sufficiency-no-change-proof
37-daily-delta-no-change-proof
38-warning-no-change-proof
39-historical-packet-compatibility
40-non-operating-idempotency-proof
```

---

# 54. Required artifacts — tests / decisions

Produce:

```text
41-positive-fixture-manifest
42-negative-fixture-manifest
43-focused-test-results
44-full-test-results
45-ruff-and-diff-results

46-financial-domain-coverage-completion-decision
47-directional-specificity-readiness-decision
48-source-sufficiency-future-review-decision
49-production-no-change
50-schedule-pause-observation
51-master-workflow-update
52-program-completion
```

Expected in M11:

```text
Directional specificity activation =
NOT_IN_M11

source sufficiency =
UNCHANGED_IN_M11
```

---

# 55. M11 acceptance criteria

M11 is COMPLETE if:

```text
financial/non-operating taxonomy is explicit

financial-sector generic non-operating treatment is blocked

period/currency/entity/statement/attribution compatibility is enforced

financial-income aggregate and children cannot double count

other income/expense remains broad context unless exact semantics exist

equity-method / associate income is not automatically classified as financial income

tax is kept separate from operating performance

continuing/discontinued operations remain distinct

no reconstructed operating profit

no universal non-operating total

no adjusted/normalized earnings

no normalized EPS

no effective-tax-rate derivation

no recurrence score

missing breakdown remains nonnegative

no ticker-specific mapping
no fuzzy OpenDART/SEC mapping

M9 debt/liquidity and M10 working-capital semantics remain unchanged

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

M11 does NOT require:

```text
all issuers to have detailed non-operating coverage

normalized earnings

financial-sector investment-income interpretation

Directional Core consumption of financial_context

model proof

real holdout

production readiness
```

---

# 56. Post-M11 Directional readiness decision

M11 completes the six-domain M4 financial evidence backlog.

At completion, perform a model-free readiness review covering:

```text
same-period comparison
OCF
PPE/simple cash conversion
debt/liquidity
inventory/receivables/working capital
non-operating/financial effects
```

The review must answer:

```text
Are the typed financial domains sufficiently represented
to activate the frozen M4 Directional specificity contract
without first requiring another source-mapping package?
```

Classify:

```text
READY_FOR_DIRECTIONAL_SPECIFICITY_IMPLEMENTATION

READY_WITH_KNOWN_OPTIONAL_GAPS

NOT_READY_GENERIC_SOURCE_GAP

NOT_READY_SCHEMA_OR_SEMANTIC_GAP
```

Do not use model calls.

---

# 57. Next-scope decision

## A. Six-domain contract is sufficiently implementable

Default:

```text
next_scope =
DIRECTIONAL_FINANCIAL_CONTEXT_CONSUMPTION_AND_SPECIFICITY_IMPLEMENTATION
```

This task should finally expose selected `financial_context` to Directional Core
under the frozen M4 specificity contract.

It must still separate:

```text
data activation
from
final real-model proof
```

## B. Generic source gap remains material

```text
next_scope =
BOUNDED_FINANCIAL_SOURCE_MAPPING_REPAIR
```

Only if generic, not ticker-specific.

## C. Schema/semantic gap remains

```text
next_scope =
FINANCIAL_CONTEXT_SEMANTIC_CONTRACT_REPAIR
```

Do not activate the model prematurely.

## D. Only optional / sector-specific gaps remain

Proceed to:

```text
DIRECTIONAL_FINANCIAL_CONTEXT_CONSUMPTION_AND_SPECIFICITY_IMPLEMENTATION
```

and record the limitations.

---

# 58. Master workflow update

Update:

```text
docs/MASTER_WORKFLOW.md
```

Expected transition:

```text
M10 COMPLETE
→
M11 COMPLETE
→
Directional financial_context activation / specificity implementation
or measured bounded repair
```

Production readiness remains:

```text
NOT_READY
```

Monitoring remains paused.

---

# 59. Program-completion fields

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
m11_status

non_operating_adapter_status

financial_income_component_class_count
financial_cost_component_class_count
interest_income_component_class_count
interest_expense_component_class_count
fx_component_class_count
other_income_expense_component_class_count
disposal_component_class_count
tax_component_class_count

financial_sector_candidate_count
financial_sector_generic_non_operating_emission_count

us_nonfinancial_candidate_count
us_financial_income_direct_count
us_financial_cost_direct_count
us_interest_income_direct_count
us_interest_expense_direct_count
us_fx_direct_count
us_tax_direct_count
us_safe_net_financial_effect_count

kr_nonfinancial_candidate_count
kr_financial_income_direct_count
kr_financial_cost_direct_count
kr_interest_income_direct_count
kr_interest_expense_direct_count
kr_fx_direct_count
kr_tax_direct_count
kr_safe_net_financial_effect_count

aggregate_child_overlap_conflict_count
sign_semantics_unresolved_count
source_conflict_count

universal_non_operating_total_formula_count
adjusted_net_income_derivation_count
normalized_net_income_derivation_count
normalized_eps_derivation_count
effective_tax_rate_derivation_count
reconstructed_operating_profit_count
recurring_earnings_score_count
materiality_scoring_rule_count

ticker_specific_mapping_count
new_sec_fuzzy_mapping_count
new_opendart_fuzzy_mapping_count

non_operating_idempotency_status

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

financial_domain_coverage_readiness
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

Anything not actually measured:

```text
NOT_MEASURED
```

---

# 60. Artifact integrity

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

# 61. Final task principle

M10 answered:

```text
what is actual inventory / receivables / payables
and what comparison is safe
```

M11 must answer:

```text
what part of reported profit comes from operating business
and what direct financial / other effects are separately observable
```

without pretending to know normalized earnings.

The correct flow is:

```text
exact direct income-statement components
→ sector routing
→ period / basis / sign validation
→ overlap control
→ limited typed financial_context
```

Not:

```text
other income = one-off
```

Not:

```text
financial income = bad-quality earnings
```

Not:

```text
interest income = non-operating for banks
```

Not:

```text
subtract selected gains to create adjusted net income
```

Not:

```text
net income growth = operating growth
```

Not:

```text
let financial_context leak into model input
```

And not:

```text
resume production monitoring
```

Complete the accounting-evidence layer first,
then activate Directional specificity in a separate task.
