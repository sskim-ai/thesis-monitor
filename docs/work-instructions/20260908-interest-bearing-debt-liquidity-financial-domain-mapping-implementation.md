# Thesis Monitor — Interest-Bearing Debt & Liquidity Financial Domain Mapping Implementation

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-interest-bearing-debt-liquidity-financial-domain-mapping-implementation.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-interest-bearing-debt-liquidity-financial-domain-mapping-implementation-report.zip
```

Master-workflow phase:

```text
M9 — Higher-Risk Financial Domain Mapping
      Interest-Bearing Debt & Liquidity
```

This task begins only after M8 has completed.

M8 closed the low-risk source-class work and recommended:

```text
HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_INTEREST_BEARING_DEBT_LIQUIDITY
```

M9 implements only:

```text
interest_bearing_debt_and_liquidity
```

M9 must NOT implement:

```text
inventory_receivables_working_capital
non_operating_financial_income_effects
Directional Core financial_context consumption
source-sufficiency gate changes
model proof
real holdout
production deployment
schedule resume
```

The goal is to create safe direct/derived debt-liquidity facts in `financial_context`
for eligible non-financial issuers, while preserving fail-closed behavior.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-source-class-financial-mapping-implementation-report.zip
```

Verified SHA-256:

```text
7c5f614dc146a1d56f9c10235a1a42858268e7efa3a330732801cd0ab06203d6
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M8 state:

```text
M1 = COMPLETE
M2 = COMPLETE
M3 = COMPLETE
M4 = COMPLETE
M5 = COMPLETE
M6 = COMPLETE
M7 = COMPLETE
M8 = COMPLETE

status = M8_COMPLETE
production_readiness = NOT_READY

next_scope =
HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION_INTEREST_BEARING_DEBT_LIQUIDITY
```

Reported M8 provenance:

```text
base_sha =
3ac2359a16c8b6e03a146ecc32676005e1589db4

work_instruction_commit =
86f361fb92431c8725087e082bf06b83a399480d

implementation_commit =
00a8663c1adbd32b487f4672fea4011d159ee945

branch =
codex/20260908-source-class-financial-mapping-implementation
```

M8 completion artifacts used the existing pre-report-commit convention:

```text
final_head_sha = NOT_MEASURED
report_commit = NOT_MEASURED
```

At M9 start use actual repository HEAD as authority and record the actual M8 final/report state.

---

# 2. M8 facts frozen for M9

M8 result:

```text
KR OCF real coverage:
0 resolved / 7 blocked
→ 7 resolved / 0 blocked

KR PPE real coverage:
0 resolved / 6 blocked
→ 6 resolved / 0 blocked
```

M8 generic source-class outcomes:

```text
HUT historical PPE gap:
SOURCE_EVIDENCE_INSUFFICIENT
→ DEFER_NO_TICKER_EXCEPTION

SKHY historical OCF/PPE gap:
generic foreign-issuer IFRS class already supported
but preserved official statement occurrence absent
→ DEFER_NO_TICKER_EXCEPTION

KR OpenDART exact-context promotion:
SOURCE_CLASS_IMPLEMENTED
real source candidates = 14
real promoted facts = 14
real denials = 0
```

M8 kept:

```text
ticker_specific_mapping_count = 0
new derivation formulas = 0
higher-risk domain emission = 0
```

M9 must preserve those source-class safety principles.

---

# 3. M4 frozen debt/liquidity contract

M4 defined the debt/liquidity purpose as:

```text
financial resilience
refinancing risk
dilution / financing pressure
```

Applicable primarily to:

```text
standard operating company
capital-intensive company
pre-profit company
holding company
```

Caution / separate framework:

```text
bank
insurance / reinsurance
financial institution
```

M4 explicitly forbids:

```text
total liabilities substituted for debt

net debt from incomplete debt components

price currency copied to financial facts

ordinary industrial net-debt logic for banks or insurers

missing debt detail treated as bearish evidence
```

Safe future derivations:

```text
interest_bearing_debt_total
= sum verified non-overlapping interest-bearing debt components

net_debt
= complete interest-bearing debt total
  - compatible cash basis
```

M9 implements that mapping/derivation contract only.

---

# 4. User-approved operating constraints

## 4.1 Free/public source only

No paid provider or paid fallback.

M9 uses existing repository/cache/fixture evidence only.

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

Observe the approved eight US/KR monitoring paths at start/end.

If all remain paused:

```text
scheduler mutation = 0
```

If an exact approved path unexpectedly resumes:

```text
pause only that path
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
financial snapshot model
balance-sheet source normalization
M6/M7/M8 financial adapters
compact AI context
source sufficiency
Daily Delta lifecycle
```

If unexplained semantic drift prevents a stable M9 baseline:

```text
STOP
UNEXPLAINED_M9_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 6. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement M9.

---

# 7. Primary M9 safety principle

M9 is a high-risk accounting-mapping task.

Coverage must never override semantic safety.

Required rule:

```text
UNKNOWN / INCOMPLETE
→ no derived interest-bearing debt total
→ no derived net debt
```

Do not attempt to maximize issuer coverage by broad aliases.

A safe blocked result is valid.

---

# 8. M9 sector routing gate

Before mapping debt/liquidity for a subject, classify the analysis framework / sector.

## 8.1 Eligible generic operating-company path

May use M9 industrial debt/liquidity mapping for:

```text
standard operating company
semiconductor / memory
automotive
shipping / transport
consumer
EPC / construction
SaaS / recurring revenue
cloud / platform
biotech
pre-profit / robotaxi-like
holding company
```

subject to actual evidence.

## 8.2 Financial-sector path

For:

```text
bank
insurance
reinsurance
financial institution
```

do NOT use ordinary industrial:

```text
interest_bearing_debt_total
net_debt
current_ratio
```

as generic thesis evidence.

M9 result for financial-sector generic debt logic should be:

```text
SECTOR_FRAMEWORK_REQUIRED
```

or existing equivalent.

Direct source facts may remain stored by existing accounting systems, but M9 must not promote them into the industrial debt/liquidity semantic contract.

Required:

```text
financial_sector_generic_net_debt_emission_count = 0
```

---

# 9. Direct debt component taxonomy

M9 must first inventory current canonical balance-sheet concepts.

Do not assume all of the following exist.

Candidate interest-bearing debt classes may include, only when source semantics are explicit:

```text
short_term_borrowings
current_portion_of_long_term_debt
long_term_borrowings
bonds_payable
notes_payable
convertible_debt
other_interest_bearing_debt
```

Exact canonical names must follow repository conventions.

Do not classify as interest-bearing debt merely because the item is a liability.

Forbidden automatic inclusion:

```text
accounts payable
trade payables
lease liabilities unless separately approved by the frozen contract
provisions
contract liabilities / deferred revenue
tax liabilities
pension liabilities
derivative liabilities
total current liabilities
total non-current liabilities
total liabilities
```

If the project already has a canonical approved treatment for lease liabilities:
document it and preserve it.

Do not create one ad hoc in M9.

---

# 10. Direct cash / liquidity taxonomy

At minimum inspect current canonical support for:

```text
cash_and_cash_equivalents
```

Potential additional liquidity items may exist:

```text
short_term_financial_assets
marketable_securities
restricted_cash
term_deposits
```

M9 must NOT automatically include them in `cash_basis`.

Default safe net-debt cash basis:

```text
cash_and_cash_equivalents only
```

unless an existing canonical rule explicitly approves additional components.

If additional liquid financial assets are reported:

```text
represent separately
```

and do not silently call them unrestricted cash.

Restricted cash must never be automatically netted against debt.

---

# 11. Point-in-time contract

Debt and liquidity are balance-sheet facts.

Required:

```text
period.type = POINT_IN_TIME
period.end = exact balance-sheet date
period.start = null
duration_days = null
```

For any derived total:

```text
all components must share the same point-in-time date
```

Do not combine:

```text
cash at June 30
with
debt at December 31
```

No stale component carry-forward in M9.

---

# 12. Currency / unit contract

All components in one derived debt/liquidity calculation must have:

```text
same verified financial currency
compatible unit scale
```

No FX conversion in M9.

Do not use:

```text
price.currency
```

as financial currency.

If unit normalization uses an existing canonical helper, it may be used.

Otherwise:

```text
block derivation
```

---

# 13. Entity / statement basis contract

All components used in one derived debt/liquidity result must match:

```text
issuer/entity scope
consolidated vs separate statement basis
attribution basis where applicable
```

Do not combine:

```text
consolidated cash
with separate-company debt
```

Do not combine parent-only component with consolidated component.

Fail closed.

---

# 14. Debt component completeness

`interest_bearing_debt_total` may be emitted only when M9 can establish:

```text
all relevant debt component classes for the selected canonical debt scope
are represented or explicitly known absent
```

M9 must define a completeness contract.

Allowed states:

```text
COMPLETE
PARTIAL
UNKNOWN
```

Only:

```text
COMPLETE
```

may produce:

```text
interest_bearing_debt_total
```

unless the frozen design creates an explicitly named partial metric.

Default M9 rule:

```text
no generic partial debt total
```

Do not label:

```text
known debt components
```

as total debt when completeness is uncertain.

---

# 15. Component overlap contract

Before summing debt components, M9 must detect potential overlap.

Example risk:

```text
short_term_borrowings
+
current_portion_of_long_term_debt
+
current_debt_total
```

may double count.

Define non-overlapping component groups based on actual canonical concepts.

If both:

```text
aggregate debt concept
and
its child components
```

exist, deterministic precedence must choose one representation.

Do not sum parent + children.

Required:

```text
overlap_conflict_count
overlap_blocked_count
aggregate_precedence_count
component_precedence_count
```

---

# 16. Total liabilities negative control

This is a hard M9 acceptance gate.

Any source field representing:

```text
total liabilities
total current liabilities
total non-current liabilities
```

must NOT be used as:

```text
interest_bearing_debt_total
```

or as an input to net debt solely by virtue of being a liability.

Required negative fixtures:

```text
total_liabilities_only
→ debt total blocked

total_current_liabilities_only
→ debt total blocked
```

Required production mapping audit:

```text
legacy_liabilities_as_debt_usage_count
```

If any existing code path currently presents total liabilities as debt in the new `financial_context` contract:

```text
fix only that bounded unsafe bridge
```

with tests.

Do not broadly rewrite unrelated legacy user-visible metrics unless necessary for M9 safety.

---

# 17. Interest-bearing debt derivation

When complete compatible direct components exist:

```text
metric =
interest_bearing_debt_total

evidence_status =
DERIVED_SAFE

period =
POINT_IN_TIME

derivation.formula =
interest_bearing_debt_total

derivation.input_source_refs =
all non-overlapping direct debt component refs

derivation.version =
frozen M9 version
```

Identity must be deterministic.

No random UUID/runtime timestamp in derived identity.

---

# 18. Net debt derivation

`net_debt` may be emitted only when:

```text
interest_bearing_debt_total = COMPLETE + valid

cash basis = valid + compatible

same date
same currency/unit
same entity/statement basis
```

Formula:

```text
net_debt
=
interest_bearing_debt_total
-
cash_and_cash_equivalents
```

unless an existing canonical M4-approved cash basis is broader.

Do not automatically subtract:

```text
short-term investments
restricted cash
marketable securities
```

without an explicit canonical rule.

If net debt is negative:

```text
negative value is allowed
```

and represents net cash under the same formula.

Do not silently relabel it as `net_cash` unless current metric conventions support that separately.

---

# 19. Liquidity context

M9 may represent direct:

```text
cash_and_cash_equivalents
current_assets
current_liabilities
```

when canonical point-in-time facts exist.

However:

```text
current_assets / current_liabilities
```

must remain liquidity context, not interest-bearing debt components.

M9 may derive:

```text
current_ratio
```

ONLY if that derivation was already frozen in the M4 debt/liquidity design.

The M4 design did not require a current-ratio derivation.

Default:

```text
do not add current_ratio in M9
```

Use direct current-assets/current-liabilities context only if useful and schema-safe.

---

# 20. Short-term financing pressure

M9 may preserve direct point-in-time information for:

```text
short_term_borrowings
current_portion_of_long_term_debt
```

as separate direct evidence.

Do not create a new "refinancing risk score".

No fixed scorecard.

Directional interpretation remains inactive until the later specificity package.

---

# 21. Convertible debt / dilution sensitivity

If convertible debt is explicitly mapped as an interest-bearing financing component:

```text
represent it as direct debt component
```

and optionally attach a limitation:

```text
convertible_dilution_terms_not_evaluated
```

unless conversion terms are separately available under an existing canonical contract.

Do not infer dilution probability.

Do not treat all convertible liabilities as ordinary straight debt without semantic review.

If ambiguous:

```text
exclude from complete debt total
→ completeness becomes PARTIAL/UNKNOWN
```

---

# 22. Lease-liability policy

M9 must explicitly decide the treatment of:

```text
lease liabilities
```

based on existing project/accounting conventions.

Allowed outcomes:

```text
INCLUDE_IN_DEBT_SCOPE
EXCLUDE_FROM_DEBT_SCOPE
SEPARATE_CONTEXT_ONLY
NOT_MEASURED
```

Do not silently include them.

If included:

```text
current + non-current lease liability overlap
must be handled
```

If excluded:

```text
document the resulting debt-scope limitation
```

The decision must be frozen in an artifact.

---

# 23. Cash restriction / liquidity quality

If the source distinguishes:

```text
restricted cash
```

do not include it in net-debt cash basis by default.

If only a combined:

```text
cash_and_restricted_cash
```

figure exists and unrestricted cash cannot be separated:

```text
net debt derivation blocked
```

unless an existing canonical rule explicitly permits the combined basis.

No optimistic liquidity assumption.

---

# 24. Holding-company caution

Holding companies may have:

```text
parent debt
subsidiary debt
consolidated debt
holding-company cash
```

M9 must preserve statement/entity basis.

Do not infer parent-level refinancing capacity from consolidated net debt alone.

Generic M9 may emit consolidated debt/liquidity facts if safe.

Attach limitation where project conventions support it:

```text
holding_company_parent_subsidiary_funding_separation_not_resolved
```

Do not build look-through SOTP financing logic in M9.

---

# 25. Pre-profit / financing-dependent companies

Debt/liquidity may be especially material, but M9 still must not interpret it.

M9 only maps evidence.

Do not create:

```text
runway months
financing probability
dilution probability
```

unless a separately frozen future design authorizes them.

---

# 26. US source mapping scope

Without provider calls, inspect current canonical US/SEC balance-sheet facts.

Possible source families:

```text
US-GAAP official balance-sheet facts
IFRS foreign-issuer balance-sheet facts where canonical
```

M9 may implement generic mappings for approved debt/cash classes only when source concepts are semantically clear.

Do not add ticker-specific mappings.

Do not add broad fuzzy concept matching.

Report each source concept/class and mapping decision.

---

# 27. KR OpenDART source mapping scope

Use official OpenDART/XBRL canonical paths only.

M8 exact-context promotion principles remain authoritative.

For debt/liquidity point-in-time facts require:

```text
exact instant date
entity identifier
currency/unit
statement basis
account concept
filing identity
```

Do not infer debt from:

```text
total liabilities
```

Do not use account-name fuzzy matching unless an existing canonical mapping already supports the concept.

New bounded explicit IFRS/OpenDART concept mappings may be added in M9 only if:

```text
they map an exact debt/cash component class
and
are generic across issuers
```

Report:

```text
new_opendart_exact_mapping_count
new_opendart_fuzzy_mapping_count
```

Required:

```text
new_opendart_fuzzy_mapping_count = 0
```

---

# 28. Foreign issuer / ADR safety

Debt/liquidity is issuer-level financial statement data.

Do not use ADR ratio or traded-security share basis in financial amounts.

Required:

```text
adr_share_basis_financial_amount_conversion_count = 0
```

Financial currency may differ from price currency.

Preserve verified financial currency.

---

# 29. Source precedence / conflicts

If the same debt/cash fact appears in multiple canonical official paths:

define deterministic precedence.

Prefer:

```text
exact official structured fact
with full basis/date provenance
```

over a derived/legacy snapshot field lacking provenance.

If equal-authority facts conflict materially:

```text
block the derived total
record conflict
```

Do not average.

---

# 30. Existing FinancialSnapshot audit

M4 identified likely locations:

```text
app/models/financial.py::FinancialSnapshot
app/services/financial_snapshot_service.py
app/services/coldstart_fundamental_enrichment_service.py
```

M9 must audit whether existing fields such as:

```text
debt
liabilities
cash
```

have ambiguous semantics.

Classify each:

```text
SAFE_DIRECT_COMPONENT
SAFE_LIQUIDITY_CONTEXT
LEGACY_AMBIGUOUS
UNSAFE_FOR_NEW_CONTRACT
NOT_APPLICABLE
```

Do not silently reinterpret a legacy `debt` field without proving its source semantics.

---

# 31. `financial_context` emission boundary

Eligible direct evidence:

```text
cash_and_cash_equivalents
approved interest-bearing debt components
optional current_assets/current_liabilities context
```

Eligible derived evidence:

```text
interest_bearing_debt_total
net_debt
```

only under M9 completeness/compatibility rules.

No higher-risk domain other than debt/liquidity.

Required:

```text
working_capital_domain_emission_count = 0
non_operating_effect_domain_emission_count = 0
```

---

# 32. Missing-data semantics

Required:

```text
missing debt detail
!= bearish evidence

missing cash detail
!= bearish evidence

partial debt mapping
!= high leverage

no net-debt derivation
!= negative investment conclusion
```

M9 does not activate model reasoning.

Missing/incomplete evidence remains:

```text
UNAVAILABLE / PARTIAL / UNKNOWN
```

according to existing evidence-quality contract.

---

# 33. Model semantic input remains dormant

M9 may increase packet `financial_context` coverage.

M9 must NOT change compact AI context.

For representative newly-supported debt/liquidity fixtures:

```text
pre-M9 compact AI context hash
=
post-M9 compact AI context hash
```

Required:

```text
compact_ai_context_changed_count = 0
```

If leakage occurs:

```text
STOP
M9_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
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

No model call.

---

# 35. Source sufficiency no-change

M4 marked debt/liquidity as a future sector-conditional source-sufficiency candidate.

M9 must NOT activate that gate.

Required:

```text
source_sufficiency_semantic_change_count = 0
```

Presence/absence of mapped debt/liquidity must not alter current directional-model eligibility.

A future separate review may decide whether financing-dependent sectors need a gate.

---

# 36. Daily Delta no-change

M3 lifecycle semantics remain frozen.

Historical/baseline debt/liquidity enrichment:

```text
!= Daily Delta
```

Required fixture:

```text
newly mapped historical debt facts
→ baseline enrichment
→ no strengthened/weakened
```

Required:

```text
daily_delta_semantic_change_count = 0
```

---

# 37. Warning no-change

M4 design allows debt/liquidity to support future warning logic.

M9 must NOT activate warning creation.

Required:

```text
warning_semantic_change_count = 0
warning_mutations = 0
```

No refinancing warning score in M9.

---

# 38. Idempotency / deterministic identity

Repeated mapping must produce:

```text
same direct fact IDs
same debt-total derived ID
same net-debt derived ID
no duplicate refs
```

Derived identity should depend on:

```text
formula/version
ordered canonical input refs
point-in-time date
entity/basis identity
```

No runtime timestamp/random UUID.

---

# 39. Positive fixture matrix

At minimum:

```text
US non-financial:
cash + short-term borrowing + long-term debt
→ complete debt total + net debt

US:
current portion + long-term non-current portion
→ non-overlapping total

KR:
exact OpenDART cash + borrowings + bonds
→ complete total where source fixture proves scope

point-in-time compatible same date

different unit scale normalized through canonical helper

negative net debt / net cash numerical result allowed

holding-company consolidated context preserved

legacy direct cash representation + new financial_context

idempotent repeated mapping
```

Synthetic contract fixtures must be labeled separately from real source-support proof.

---

# 40. Negative fixture matrix

At minimum:

```text
total liabilities only → debt blocked

total current liabilities only → debt blocked

cash date != debt date

currency mismatch

consolidated cash + separate debt

parent aggregate + child debt components double-count attempt

incomplete debt component scope

restricted cash only used for net debt

cash+restricted combined with no separation

lease-liability ambiguous scope

financial-sector generic net debt

bank industrial debt mapping

insurance industrial debt mapping

ADR ratio applied to debt amount

ticker-specific mapping branch

price currency copied into financial fact

partial debt labeled total

working-capital domain emitted accidentally

non-operating domain emitted accidentally
```

---

# 41. Real archive coverage audit

Using repository/cache evidence only, report separately:

```text
US non-financial issuer candidates
US direct cash mapped
US direct debt components mapped
US complete debt-total derived
US net-debt derived

KR non-financial issuer candidates
KR direct cash mapped
KR direct debt components mapped
KR complete debt-total derived
KR net-debt derived

financial-sector candidates routed to sector framework
```

Do not claim universal market coverage.

Coverage is descriptive.

---

# 42. Completeness-denial accounting

Required reason taxonomy:

```text
missing_cash
missing_debt_components
debt_scope_incomplete
component_overlap
point_in_time_mismatch
currency_mismatch
entity_scope_mismatch
statement_basis_mismatch
restricted_cash_ambiguity
financial_sector_not_applicable
source_conflict
unsupported_component_semantic
```

Report counts pre/post M9 where a comparable baseline exists.

Do not optimize counts by weakening rules.

---

# 43. Mapping activation surface

Preferred changed code:

```text
generic debt/liquidity domain adapter
canonical balance-sheet source mapping
exact OpenDART/SEC concept registry where necessary
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

If M9 requires changing model input or source sufficiency:

```text
STOP
M9_SCOPE_EXCEEDED
```

---

# 44. Validation requirements

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
M5 financial_context schema
M6 financial adapter
M7 lineage projection
M8 source-class mapping
M9 debt/liquidity mapping
financial snapshot tests
SEC/OpenDART balance-sheet mapping tests
compact AI non-leak
source sufficiency no-change
Daily Delta no-change
historical packet compatibility
```

No model tests.

No live provider tests.

---

# 45. Production side-effect firewall

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

# 46. Required artifacts — provenance / design reuse

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m9-scope-freeze
04-m4-debt-liquidity-contract-reuse-proof
05-m5-m8-contract-reuse-proof
```

---

# 47. Required artifacts — mapping design / implementation

Produce:

```text
06-current-balance-sheet-source-inventory
07-interest-bearing-debt-component-taxonomy
08-cash-liquidity-taxonomy
09-sector-routing-contract
10-debt-completeness-contract
11-component-overlap-and-precedence-contract
12-lease-liability-policy
13-restricted-cash-policy
14-debt-liquidity-adapter-contract
15-debt-liquidity-implementation-diff
16-source-mapping-activation-surface
```

---

# 48. Required artifacts — coverage / controls

Produce:

```text
17-us-debt-liquidity-source-support-audit
18-kr-debt-liquidity-source-support-audit
19-financial-sector-routing-audit
20-total-liabilities-negative-control
21-completeness-denial-accounting
22-source-conflict-and-dedup-audit
23-real-archive-coverage
```

---

# 49. Required artifacts — semantic no-change proofs

Produce:

```text
24-compact-ai-context-non-leak-proof
25-directional-prompt-no-change-proof
26-price-timing-no-change-proof
27-source-sufficiency-no-change-proof
28-daily-delta-no-change-proof
29-warning-no-change-proof
30-historical-packet-compatibility
31-debt-liquidity-idempotency-proof
```

---

# 50. Required artifacts — tests / decisions

Produce:

```text
32-positive-fixture-manifest
33-negative-fixture-manifest
34-focused-test-results
35-full-test-results
36-ruff-and-diff-results

37-working-capital-next-scope-decision
38-directional-specificity-activation-decision
39-source-sufficiency-future-review-decision
40-production-no-change
41-schedule-pause-observation
42-master-workflow-update
43-program-completion
```

Expected:

```text
Directional specificity activation =
NOT_IN_M9

source sufficiency =
UNCHANGED_IN_M9
```

---

# 51. M9 acceptance criteria

M9 is COMPLETE if:

```text
debt/liquidity source taxonomy is explicit

total liabilities cannot become debt

interest-bearing components are mapped only from exact semantics

component overlap is controlled

debt completeness is explicit

interest_bearing_debt_total only emits when scope is complete

net_debt only emits with compatible complete debt + cash

restricted cash is not optimistically netted

financial-sector generic industrial debt logic is blocked

holding-company basis is preserved

no ticker-specific mapping

no broad fuzzy OpenDART mapping

working-capital and non-operating domains remain inactive

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

M9 does NOT require:

```text
all issuers to have complete net debt

bank/insurance capital adequacy mapping

working-capital mapping

non-operating effects mapping

Directional Core consumption of financial_context

model proof

real holdout

production readiness
```

---

# 52. Next-scope decision

If M9 passes, default M4/M8 order is:

```text
INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION
```

unless the M9 result exposes a generic debt/liquidity blocker that must be repaired first.

Possible outcomes:

## A. Debt/liquidity mapping complete enough

```text
next_scope =
INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION
```

## B. Generic low-risk debt source mapping still missing

```text
next_scope =
BOUNDED_DEBT_LIQUIDITY_SOURCE_MAPPING_REPAIR
```

## C. Only financial-sector debt logic remains missing

Do not implement industrial net-debt logic for financials.

Defer to a later sector-specific capital-framework task if needed.

Proceed to:

```text
INVENTORY_RECEIVABLES_WORKING_CAPITAL_MAPPING_IMPLEMENTATION
```

## D. Current evidence coverage is already sufficient for frozen Directional specificity

Do not activate model use in M9.

Record the case for later review.

---

# 53. Master workflow update

Update:

```text
docs/MASTER_WORKFLOW.md
```

Expected transition:

```text
M8 COMPLETE
→
M9 COMPLETE
→
next bounded higher-risk financial domain
```

Production readiness remains:

```text
NOT_READY
```

Monitoring remains paused.

---

# 54. Program-completion fields

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

debt_liquidity_adapter_status

debt_component_class_count
cash_liquidity_component_class_count

lease_liability_policy
restricted_cash_policy

us_nonfinancial_candidate_count
us_cash_direct_count
us_debt_component_direct_count
us_complete_debt_total_count
us_net_debt_count

kr_nonfinancial_candidate_count
kr_cash_direct_count
kr_debt_component_direct_count
kr_complete_debt_total_count
kr_net_debt_count

financial_sector_candidate_count
financial_sector_generic_net_debt_emission_count

total_liabilities_used_as_debt_count
partial_debt_labeled_total_count

component_overlap_conflict_count
component_overlap_blocked_count

debt_scope_incomplete_count
net_debt_blocked_incomplete_debt_count
net_debt_blocked_cash_basis_count

source_conflict_count
source_conflict_blocked_count
deduplicated_fact_count

ticker_specific_mapping_count
new_sec_fuzzy_mapping_count
new_opendart_fuzzy_mapping_count
adr_share_basis_financial_amount_conversion_count

working_capital_domain_emission_count
non_operating_effect_domain_emission_count

debt_liquidity_idempotency_status

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

Anything not measured:

```text
NOT_MEASURED
```

---

# 55. Artifact integrity

Freeze:

```text
program completion
master workflow update
all reports
```

before final artifact index creation.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 56. Final task principle

M8 finished the low-risk source-class layer.

M9 must now answer a narrower, higher-risk accounting question:

```text
What is verified interest-bearing debt,
what is verified liquidity,
and when is the scope complete enough to derive net debt?
```

The correct flow is:

```text
exact direct balance-sheet components
→ same-date / same-basis validation
→ overlap + completeness control
→ safe debt total
→ safe net debt
→ packet financial_context only
```

Not:

```text
total liabilities = debt
```

Not:

```text
partial known debt = total debt
```

Not:

```text
restricted cash = freely available cash
```

Not:

```text
industrial net debt for banks/insurers
```

Not:

```text
let financial_context leak into model input
```

And not:

```text
resume production monitoring
```

Prefer Unknown over a misleading capital-structure conclusion.
