# Thesis Monitor — Source Domain Enrichment & Directional Specificity Design Review

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-source-domain-enrichment-and-directional-specificity-design-review.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-source-domain-enrichment-directional-specificity-design-review-report.zip
```

Master-workflow phase:

```text
M4 — Source Domain Enrichment & Directional Specificity Design Review
```

This task begins only after M3 has completed.

The task is a **model-free / provider-free design review**.

It must determine:

```text
which additional financial evidence domains can be safely obtained
from the existing free/public source stack,

which of those domains materially improve investment decision quality,

how they should be normalized and represented,

which sectors they apply to,

how Directional Core should use them,

and what exact bounded implementation should be authorized next.
```

This task is NOT:

- a broad source-pipeline implementation;
- a Directional prompt rewrite;
- a new model / real-holdout proof;
- a production integration task;
- a scheduler-resume task;
- a paid-data integration task.

Do not silently implement the semantic changes being designed.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-nonproduction-monitoring-bootstrap-daily-delta-lifecycle-integration-report.zip
```

Verified SHA-256:

```text
e1ebc077c56c2412280f58d8244498848b9a1f96ae3c4d233aa2535786ef3228
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest result state:

```text
M1 = COMPLETE
M2 = COMPLETE
M3 = COMPLETE

status = M3_COMPLETE
production_readiness = NOT_READY

next_scope =
SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_DESIGN_REVIEW
```

Reported repository provenance:

```text
base_sha =
2257a05f9a599aafd0f3120fb8ab62655bee875a

work_instruction_commit =
5d3945e91da050d0b565be4de11ad1b0706ee796

implementation_commit =
41fdd088d0ab312d2bbd975b8066851faabaf0a1

report_commit / final_head_sha =
5990caa239f8778ae46670abddf30f68db1bb332
```

M3 artifact integrity:

```text
indexed payload count = 44
hash mismatch count = 0
size mismatch count = 0
secret scan failure count = 0
```

Do not assume current repository HEAD remains identical.

---

# 2. M3 completion state — frozen input to M4

M3 proved in isolated nonproduction:

```text
explicit registration intent
→ onboarding pending
→ evidence preparation
→ absolute baseline
→ bootstrap readiness
→ monitoring-ready
→ post-baseline Daily Delta
→ assessment / warning intent
→ file-only monitoring message
```

M3 fixture results:

```text
12 / 12 PASS

focused pytest:
92 passed

full pytest:
2790 passed

ruff:
PASS

git diff --check:
PASS
```

M3 hard lifecycle semantics proven:

```text
Initial Analysis does not auto-register

registration != monitoring-ready

bootstrap enrichment != Daily Delta

late-arriving pre-baseline evidence != Daily Delta

missing refresh != no_material_change

price-only != business thesis delta
supply-only != business thesis delta
valuation-only != business thesis delta

warning / assessment idempotency = PASS

new issuer / existing issuer share the same decision-message contracts
```

Do not reopen M3 lifecycle semantics in M4 unless current repository drift directly affects them.

---

# 3. M2/M3 source-domain decision that triggers M4

M2 found no `AVAILABLE_BUT_DROPPED` domain inside the preserved decision archive.

However, six decision-relevant domains were absent from that archive or needed separate design:

```text
same_period_prior_year_comparison

operating_cash_flow

ppe_capex_simple_cash_conversion

debt_liquidity

inventory_receivables_working_capital

non_operating_financial_income_effects
```

M3 preserved these six as:

```text
PRESERVE_AS_SEPARATE_DESIGN_REVIEW
```

M4 must decide their future contract.

Do not interpret:

```text
not present in preserved archive
```

as:

```text
not available in the existing source stack
```

The purpose of M4 is to inspect current code, parsers, mappings, schemas and offline fixtures to determine actual support.

---

# 4. Decision-quality background

Historical source-only review of several real issuers showed that investment conclusions can change materially when the following are considered:

```text
cumulative vs single-quarter operating result

operating cash-flow conversion

capex burden

debt / liquidity

inventory growth

receivables / working-capital quality

operating profit vs financial / non-operating income contribution
```

Examples from preserved evidence included patterns such as:

```text
profit growth + weak operating cash flow + high leverage

single-quarter profit + cumulative operating loss

net-income improvement largely explained by financial/non-operating effects

profit growth + inventory / receivables growth

good earnings + strong cash generation + strong liquidity
```

M4 must design generic evidence rules for such patterns.

Do not hard-code historical tickers or historical outcomes.

---

# 5. User-approved data policy

The user explicitly chose:

```text
existing free/public data routes only
```

Do not:

```text
add a paid source
upgrade a provider to paid tier
design a paid fallback
```

M4 must operate offline.

Required:

```text
provider source fetches = 0
```

Use:

```text
repository code
source parsers
normalizers
schemas
tests
existing source fixtures
preserved historical artifacts
```

If live provider data is required to answer a design question:

```text
record NOT_MEASURED
```

and define the exact future bounded verification.

Do not silently call a provider.

---

# 6. Model-call policy

M4 is model-call free.

Required:

```text
real model calls = 0
fictional model calls = 0
judge model calls = 0
```

Do not test prompt wording in M4.

Do not run a new real holdout.

M4 freezes the semantic design that would later require model revalidation.

---

# 7. Existing scheduled monitoring remains paused

The user requested the eight existing US/KR monitoring schedule paths remain paused.

At task start and end:

```text
observe only
```

If all approved paths remain paused:

```text
scheduler mutation = 0
```

If an exact approved path unexpectedly becomes active:

```text
pause only that path
record actual mutation
```

Do not alter unrelated schedules.

Do not automatically resume monitoring after M4.

---

# 8. Repository provenance gate

Before review/tooling changes:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Compare with M3 final state.

Classify drift in:

```text
source ingestion / normalization
DecisionEvidencePacket
Directional ownership
valuation safety
accounting attribution
ADR/security basis
onboarding / Daily Delta lifecycle
renderer / message ownership
```

If unexplained semantic drift prevents a reliable M4 baseline:

```text
STOP
UNEXPLAINED_M4_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 9. Work-instruction commit first

Commit this instruction before any review-tooling implementation.

Record:

```text
new_work_instruction_commit
```

M4 may implement:

```text
offline source-domain inventory tooling
schema/mapping introspection
fixture classification tooling
design-report generation
```

M4 must NOT implement broad production semantic enrichment.

---

# 10. Primary M4 deliverable — Source Domain Contract Matrix

For each of the six domains produce one canonical design row containing:

```text
domain

investment purpose

applicable sector families

non-applicable / caution sector families

US free/public source availability

KR free/public source availability

current parser / mapping location

directly reported vs derived

period basis

currency basis

entity / attribution basis

single-quarter vs cumulative semantics

comparability requirements

safe derivations

forbidden derivations

DecisionEvidencePacket representation

Directional Core usage

valuation usage

message usage

source-sufficiency impact

missing-data behavior

required validation tests

implementation risk

schema change required?
```

This matrix is the core M4 artifact.

---

# 11. Domain A — same-period prior-year comparison

Design a safe contract for:

```text
current period
vs
same period prior year
```

Required distinctions:

```text
single quarter vs single quarter

YTD cumulative vs YTD cumulative

annual vs annual
```

Do NOT compare:

```text
single quarter vs YTD
quarter vs fiscal year
different accounting bases
different attribution bases
incompatible currencies
```

If a quarter value is reconstructed from cumulative statements:

```text
allow only when the existing canonical financial-semantic rules
prove the same concept / attribution / currency / period basis
```

Otherwise:

```text
do not derive
```

Directional use:

```text
comparison can establish trend / persistence
but does not itself create valuation evidence
```

Missing prior-year comparison:

```text
Unknown / unavailable
not negative evidence
```

Decide whether this domain should be:

```text
PREFERRED_WHEN_AVAILABLE
SECTOR_CONDITIONAL
or
REQUIRED_FOR_SPECIFIC_DIRECTIONAL_CLAIMS
```

Do not make it a universal source-sufficiency gate without explicit evidence.

---

# 12. Domain B — operating cash flow

Design a safe contract for official operating cash flow.

Required:

```text
statement-of-cash-flows provenance

period basis:
usually cumulative YTD / annual

currency

consolidated / separate basis

entity attribution where relevant
```

Do not treat:

```text
one cumulative operating-cash-flow number
```

as a single-quarter number unless explicitly reported or safely derived.

Directional purpose:

```text
earnings cash conversion
liquidity quality
growth-quality cross-check
```

Sector caution:

```text
banks
insurers
financial institutions
```

must not use generic industrial-company cash-flow interpretation automatically.

Decide sector applicability explicitly.

Missing operating cash flow:

```text
does not automatically weaken the thesis
```

---

# 13. Domain C — PPE capex / simple cash-conversion context

Design this domain conservatively.

Potential inputs:

```text
purchase of property / plant / equipment
purchase of intangible assets where semantically appropriate
other verified capital expenditure fields
```

Do NOT call:

```text
Operating Cash Flow - identified PPE purchase
```

`FCF` unless the canonical capex definition is complete enough to justify that label.

Preferred safe label when incomplete:

```text
simple cash-conversion proxy
OCF less identified capital expenditure
```

Required caveat:

```text
growth capex vs maintenance capex may be unknown
```

Do not infer maintenance capex.

Do not combine incompatible periods.

Directional use:

```text
high profit + weak post-capex cash conversion
may reduce earnings-quality conviction

strong profit + strong post-capex cash conversion
may strengthen quality evidence
```

No fixed weighted points.

---

# 14. Domain D — debt / liquidity

Design separate contracts for:

```text
non-financial operating companies
financial institutions
```

For ordinary operating companies, candidate evidence may include:

```text
cash / cash equivalents
short-term borrowings
long-term borrowings
current portion of debt
bonds / convertible debt where applicable
current assets
current liabilities
```

Do NOT substitute:

```text
total liabilities
```

for interest-bearing debt.

Do NOT calculate net debt unless:

```text
interest-bearing debt scope is sufficiently complete
cash basis is compatible
period is aligned
```

For banks / insurers:

```text
do not use ordinary industrial net-debt logic
```

Use the sector-specific capital/liquidity framework already defined elsewhere.

Directional use:

```text
liquidity / refinancing / dilution risk
capital intensity
financial resilience
```

Missing debt detail:

```text
Unknown
not automatic negative evidence
```

---

# 15. Domain E — inventory / receivables / working capital

Design sector-conditional applicability.

Potentially relevant:

```text
manufacturing
hardware
consumer / retail
EPC / project companies
selected distributors
```

Potentially inappropriate or materially different:

```text
banks
insurers
asset managers
many software businesses
```

Required period labeling:

```text
balance-sheet date vs prior year-end
or
balance-sheet date vs prior-year comparable date
```

Do not call:

```text
year-end → half-year balance movement
```

YoY.

Safe use:

```text
inventory growth vs revenue growth

receivables growth vs revenue growth

working-capital consumption

cash-conversion warning
```

Do not calculate DSO / inventory days / CCC unless:

```text
required average balances
revenue / COGS denominators
period length
```

are valid and compatible.

Missing working-capital data:

```text
not negative evidence
```

---

# 16. Domain F — non-operating / financial income effects

Design a contract to separate:

```text
operating business performance
from
financial / other / non-operating effects
```

Potential fields:

```text
financial income
financial cost
interest income / expense
foreign-exchange effects
other income / expense
asset disposal effects
tax effects where separately relevant
```

Required safety:

```text
do not call an item non-operating
when the sector treats it as core operating economics
```

Especially for:

```text
banks
insurers
financial institutions
```

Directional use:

```text
net income improvement
must not automatically be treated as operating improvement
when material non-operating effects explain the change
```

Likewise:

```text
operating deterioration masked by non-operating gain
```

should be explicit when evidence proves it.

No invented normalization.

---

# 17. Materiality contract

M4 must define how a domain becomes decision-relevant without a universal fixed score.

Use a qualitative evidence rule such as:

```text
MATERIAL
SUPPORTIVE
CONTEXT_ONLY
NOT_APPLICABLE
UNAVAILABLE
```

A domain is `MATERIAL` only when it can reasonably change:

```text
investment thesis strength
earnings quality
financial resilience
valuation interpretation
warning / invalidation logic
```

Do not build a universal:

```text
+1 / -1 scorecard
```

Do not require the model to mention every supplied domain.

---

# 18. Source-sufficiency impact decision

For every domain explicitly decide one of:

```text
NO_SOURCE_SUFFICIENCY_IMPACT

PREFERRED_WHEN_AVAILABLE

SECTOR_CONDITIONAL_REQUIRED

REQUIRED_ONLY_FOR_SPECIFIC_CLAIM

FUTURE_DESIGN_REQUIRED
```

Default assumption:

```text
new enrichment does NOT become a universal source-sufficiency gate
```

unless M4 proves otherwise.

The goal is better reasoning, not shrinking support coverage unnecessarily.

---

# 19. DecisionEvidencePacket compatibility review

For each domain determine:

```text
can existing packet fields represent this safely?

does current evidence object already support:
amount
period
currency
source ID
semantic label
direct / derived status
comparison basis
confidence / limitation?
```

Classify:

```text
EXISTING_SCHEMA_SUFFICIENT

EXISTING_SCHEMA_WITH_NORMALIZATION_EXTENSION

SCHEMA_EXTENSION_REQUIRED

DO_NOT_ADD
```

If schema extension is required:

```text
do not implement it in M4
```

Freeze an exact bounded schema proposal.

---

# 20. Direct vs derived evidence

Every proposed numeric evidence item must have:

```text
DIRECT_REPORTED
or
DERIVED_SAFE
```

status.

For derived-safe evidence define:

```text
formula
input source IDs
period requirements
currency requirements
attribution requirements
failure conditions
```

Forbidden:

```text
reverse engineering EPS / BVPS from provider multiples

one-quarter annualization into PER

ordinary-share / ADR basis mixing

incompatible period arithmetic

deriving debt from total liabilities

calling partial capex subtraction full FCF
```

---

# 21. Directional Core specificity contract

M4 must design a future prompt/decision contract that improves issuer specificity without turning Core into a checklist.

The future Core should:

```text
select 1–3 value-relevant anchors

prefer the most decision-relevant evidence,
not simply revenue + operating profit + net income because all are positive

state whether the anchor is:
absolute condition
trend
cash-conversion quality
balance-sheet resilience
sector KPI
valuation evidence
or risk
```

When relevant evidence exists, Core should distinguish patterns such as:

```text
profit growth + cash-flow weakness

profit growth + leverage pressure

single-quarter profit + cumulative loss

net-income growth driven by non-operating effects

profit growth + inventory / receivable buildup

profit growth + strong cash conversion + strong liquidity
```

Do not mandate these statements when evidence is unavailable or not applicable.

---

# 22. Correlated evidence is not multiple independent anchors

M4 must define:

```text
revenue positive
operating profit positive
net income positive
```

as potentially related observations rather than automatically three independent positive anchors.

The future Core should identify the actual economic conclusion:

```text
profitable current operation
profitability trend
cash conversion
financial resilience
```

rather than counting correlated statement lines.

No fixed scoring implementation in M4.

---

# 23. Period specificity contract

When a decision depends on period information, future reasoning should distinguish:

```text
latest single quarter
YTD cumulative
full year
balance-sheet point-in-time
prior comparable period
```

Examples of forbidden generic wording when stronger period evidence exists:

```text
"최근 실적은 긍정적이다"
```

if the actual material fact is:

```text
latest quarter profit
but cumulative operating loss
```

or:

```text
YTD profit growth
while latest-quarter margin fell
```

The future reasoning should preserve that distinction.

---

# 24. Earnings-quality contract

M4 must freeze a generic future rule:

```text
reported net-income growth
does not equal earnings-quality improvement
```

when evidence indicates material differences in:

```text
operating profit
operating cash flow
working capital
capex
financial/non-operating effects
```

The future Core may use these as:

```text
supporting
limiting
warning
```

evidence.

Do not create a deterministic accounting score.

---

# 25. Missing-data semantics

For all six domains:

```text
missing / unavailable
!=
negative
```

Unknown should limit confidence or specificity where material.

Do not let the future prompt say:

```text
missing cash flow => bearish
missing debt => bearish
missing inventory => bearish
```

Missing evidence may justify:

```text
lean-only
WAIT
needs_review
additional confirmation
```

only through the existing evidence-confidence contract, not automatic negative scoring.

---

# 26. Initial Analysis vs Daily Delta usage

Design separate use of enriched domains.

## Initial / absolute decision

May use:

```text
current condition
comparative trend
cash-flow quality
balance-sheet quality
non-operating effect
```

as absolute investment evidence.

## Monitoring baseline

Bootstrap may enrich the baseline with these domains.

That enrichment is:

```text
NOT Daily Delta
```

## Daily Delta

Only a newly effective / post-baseline validated change in these domains may affect:

```text
strengthened
weakened
mixed
invalidation_candidate
```

Do not let late-arriving pre-baseline financial data become today's thesis delta.

Preserve M3 cutoff semantics.

---

# 27. Warning / Kill Condition implications

For each domain decide whether it may support:

```text
Early Warning
Kill Condition
neither
```

Examples to design carefully:

```text
persistent cash conversion deterioration

liquidity / refinancing stress

inventory / receivables buildup

operating deterioration masked by non-operating gain
```

Do not automatically convert a one-period movement into a Kill Condition.

Require:

```text
materiality
persistence / context
validated source
```

according to the existing thesis-monitoring philosophy.

---

# 28. Valuation boundary

M4 must preserve the distinction:

```text
earnings quality / financial condition
!=
valuation
```

Additional financial evidence may affect:

```text
confidence in denominator quality
multiple expansion/compression conditions
```

but must not invent a valuation multiple.

If safe EPS/BVPS/FCF denominator remains unavailable:

```text
valuation remains unavailable / limited
```

Do not infer it from the new domains.

---

# 29. Sector applicability matrix

At minimum include design treatment for:

```text
standard operating company
semiconductor / memory
automotive
bank
insurance / reinsurance
shipping / transport
holding company
consumer
EPC / construction
SaaS / recurring revenue
cloud / platform
biotech
pre-profit / robotaxi-like
```

Do not require every domain for every sector.

Examples:

```text
inventory / receivables:
high relevance in manufacturing/EPC
low relevance in banks

generic net debt:
useful for ordinary operating companies
not directly transferable to banks/insurers

operating cash flow:
useful earnings-quality signal for many operating companies
sector-cautious for financial institutions
```

Freeze the matrix.

---

# 30. Market-specific source-support audit

Without provider calls, inspect current repository mappings/fixtures to determine support status for each domain in:

```text
US / SEC path
KR / OpenDART path
```

Classify each domain-market pair:

```text
SUPPORTED_CURRENTLY

PARTIALLY_SUPPORTED

SOURCE_EXISTS_MAPPING_INCOMPLETE

FIXTURE_EVIDENCE_ONLY

NOT_SUPPORTED

NOT_MEASURED
```

Do not overclaim universal issuer coverage based on a few fixtures.

Report:

```text
parser/mapping paths
test fixture evidence
known gaps
```

---

# 31. Offline representative fixture review

Use repository fixtures / preserved source artifacts only.

Create an offline matrix containing representative cases for:

```text
profitable + strong cash conversion

profitable + weak cash conversion

high leverage / weak liquidity

inventory / receivables buildup

cumulative loss despite latest-quarter profit

net-income improvement with material non-operating effect

sector where a generic domain is not applicable
```

No model call.

The fixture review validates:

```text
source semantics
period semantics
derivation safety
sector applicability
```

not model behavior.

---

# 32. No broad implementation in M4

M4 must NOT broadly modify:

```text
source parser outputs
DecisionEvidencePacket production schema
Directional Core prompt
source-sufficiency gates
Daily Delta semantics
renderer
```

M4 may add:

```text
design-only schemas/examples
offline introspection tools
fixture audit helpers
documentation
tests that verify current behavior
```

but not activate the proposed enrichment.

If a one-line existing mapping bug is discovered:

```text
record it
```

Do not silently patch it unless it prevents accurate M4 inspection and the fix is purely semantic-neutral tooling.

---

# 33. Candidate implementation packages

At the end of M4 group future changes into bounded packages.

Possible packages:

## Package A — normalization / evidence mapping only

```text
no packet schema change
no prompt change
```

## Package B — DecisionEvidencePacket extension

```text
new structured domain fields / metadata required
```

## Package C — Directional specificity contract

```text
prompt / acceptance semantics change
```

## Package D — source-sufficiency adjustment

Only if M4 proves a domain is truly sector-conditionally required.

## Package E — no change

If the domain does not improve the current investment contract safely.

For every package report:

```text
semantic risk
affected modules
required tests
model revalidation required?
fresh real holdout required?
```

---

# 34. Required next-change ordering

Default ordering should minimize semantic mixing.

If both source enrichment and prompt specificity are required:

```text
1. source-domain normalization / packet enrichment
2. freeze input contract
3. Directional specificity implementation
4. freeze decision contract
5. then new model / real-holdout proof
```

Do not simultaneously change:

```text
source fields
source-sufficiency
Directional scoring semantics
renderer prose
```

in one uncontrolled implementation.

M4 must choose the smallest safe order.

---

# 35. Required validation during M4

Run static/offline validation only.

At minimum:

```text
focused pytest for new review tooling / current source semantics

full repository pytest

ruff

git diff --check
```

No:

```text
live provider tests
model tests
production integration side effects
```

Required all PASS if code/tooling changes occur.

---

# 36. Production side-effect firewall

Required M4 counts:

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

# 37. Required artifacts — design foundation

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m4-scope-freeze
04-m1-m2-m3-contract-reuse-proof

05-source-domain-backlog-reconciliation
06-current-source-parser-and-mapping-inventory
07-source-domain-contract-matrix
08-sector-applicability-matrix
09-market-source-support-matrix
```

---

# 38. Required artifacts — domain designs

Produce one artifact per domain:

```text
10-same-period-comparison-design
11-operating-cash-flow-design
12-ppe-capex-cash-conversion-design
13-debt-liquidity-design
14-working-capital-design
15-non-operating-financial-effects-design
```

Each must include:

```text
safe evidence contract
forbidden derivations
sector applicability
DecisionEvidencePacket compatibility
source-sufficiency impact
Directional use
Daily Delta use
tests required
```

---

# 39. Required artifacts — specificity / decision contracts

Produce:

```text
16-materiality-contract
17-direct-vs-derived-evidence-contract
18-period-specificity-contract
19-earnings-quality-contract
20-directional-specificity-contract
21-warning-kill-condition-domain-contract
22-valuation-boundary-contract
```

These are design artifacts only.

Do not apply them to the production prompt in M4.

---

# 40. Required artifacts — offline evidence audit

Produce:

```text
23-offline-representative-fixture-manifest
24-offline-domain-semantics-audit
25-us-free-source-domain-support-audit
26-kr-free-source-domain-support-audit
27-current-schema-compatibility-audit
```

No provider calls.

---

# 41. Required decision artifacts

Produce:

```text
28-candidate-implementation-packages
29-implementation-order-decision
30-required-schema-change-decision
31-required-source-sufficiency-change-decision
32-required-directional-specificity-change-decision
33-required-model-validation-scope
34-required-real-holdout-scope
35-production-no-change
36-schedule-pause-observation
37-master-workflow-update
38-program-completion
```

Update canonical:

```text
docs/MASTER_WORKFLOW.md
```

at task completion.

---

# 42. M4 acceptance criteria

M4 is COMPLETE only if:

```text
all 6 domains have explicit safe contracts

all 6 domains have sector applicability decisions

US / KR free-source support is classified without live provider calls

direct vs derived semantics are frozen

period / currency / attribution / comparability rules are frozen

DecisionEvidencePacket compatibility is decided per domain

source-sufficiency impact is decided per domain

Directional Core use is designed without fixed scoring

missing-data behavior is explicit

Daily Delta / baseline usage preserves M3 lifecycle semantics

implementation packages and ordering are frozen

required next model / real-holdout validation is explicit

focused/full tests PASS if tooling changed
ruff PASS
git diff --check PASS

all side-effect counters = 0
```

M4 does NOT require:

```text
source enrichment implemented
Directional prompt implemented
model proof executed
production readiness
```

---

# 43. Next-scope decision matrix

## A. Existing schema is sufficient and safe free-source mappings are available

Recommended next scope:

```text
BOUNDED_SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_IMPLEMENTATION
```

The implementation task must freeze source enrichment before prompt specificity changes.

## B. Source data exists but DecisionEvidencePacket cannot represent it safely

Recommended next scope:

```text
DECISION_EVIDENCE_PACKET_DOMAIN_EXTENSION_IMPLEMENTATION
```

Then model validation later.

## C. Most domains are not safely available in current free sources

Do not force enrichment.

If decision specificity can improve using existing evidence:

```text
DIRECTIONAL_REASONING_SPECIFICITY_IMPLEMENTATION
```

## D. A domain would require a paid source

```text
DO_NOT_IMPLEMENT
```

under current user policy.

Record the limitation.

## E. A source-sufficiency semantic change is required

This is higher risk.

Recommended:

```text
SECTOR_CONDITIONAL_SOURCE_SUFFICIENCY_DESIGN_REVIEW
```

unless M4 already has enough evidence to freeze a narrowly bounded rule.

Do not silently change source-sufficiency in M4.

## F. No semantic/input change is justified

Only then:

```text
FINAL_FROZEN_MODEL_AND_REAL_HOLDOUT_VALIDATION
```

may be the next scope.

---

# 44. Production readiness

Even if M4 completes:

```text
production_readiness = NOT_READY
```

M4 is a semantic design review.

Existing monitoring remains paused.

Do not merge/deploy.

---

# 45. Program-completion fields

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

domain_count
domain_design_complete_count

same_period_comparison_decision
operating_cash_flow_decision
ppe_capex_decision
debt_liquidity_decision
working_capital_decision
non_operating_effects_decision

us_supported_domain_count
us_partial_domain_count
us_unsupported_domain_count

kr_supported_domain_count
kr_partial_domain_count
kr_unsupported_domain_count

schema_sufficient_domain_count
schema_extension_required_domain_count

universal_source_gate_added_count
sector_conditional_gate_candidate_count

derived_metric_count
forbidden_derivation_count

directional_specificity_contract_status
earnings_quality_contract_status
period_specificity_contract_status
materiality_contract_status

implementation_package_count
recommended_implementation_order

semantic_change_required
schema_change_required
source_sufficiency_change_required
directional_prompt_change_required

new_model_validation_required
new_real_holdout_proof_required
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

Anything not actually measured must remain:

```text
NOT_MEASURED
```

---

# 46. Artifact integrity

Create the final artifact index only after:

```text
program completion
master workflow update
all design artifacts
```

are frozen.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 47. Final task principle

M3 completed the monitoring lifecycle contract.

The next problem is not lifecycle plumbing.

The next question is:

```text
What additional financial evidence can the current free source stack
safely provide,
and how should that evidence improve Directional Core specificity
without turning the system into a rigid scorecard?
```

The correct M4 flow is:

```text
inspect current free-source capability
→ define safe domain contracts
→ define sector applicability
→ define Directional use
→ freeze the smallest implementation package
```

Not:

```text
add every available accounting field
```

Not:

```text
make missing evidence bearish
```

Not:

```text
introduce a fixed scorecard
```

Not:

```text
run another large holdout before the input contract is frozen
```

Not:

```text
rewrite renderer prose to hide generic reasoning
```

And not:

```text
resume production monitoring
```

Design the evidence contract first.
