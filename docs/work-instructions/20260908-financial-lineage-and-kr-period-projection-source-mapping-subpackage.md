# Thesis Monitor — Financial Lineage & KR Period Projection Source Mapping Subpackage

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-financial-lineage-and-kr-period-projection-source-mapping-subpackage.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-financial-lineage-kr-period-projection-source-mapping-report.zip
```

Master-workflow phase:

```text
M7 — Additional Financial Source Mapping Subpackage A
      Financial Lineage & KR Period Projection
```

This task begins only after M6 has completed.

M6 successfully activated typed `financial_context` emission for already-canonical:

```text
same-period comparison
operating cash flow
PPE capex
OCF less PPE simple cash-conversion
```

while keeping:

```text
compact AI model input unchanged
Directional / Price-Timing prompts unchanged
source sufficiency unchanged
Daily Delta semantics unchanged
```

M7 implements only the first four items of the frozen M6 mapping backlog:

```text
1. compatible_prior_year_fact_projection
2. derived_period_lineage_projection
3. kr_opendart_ocf_duration_period
4. kr_opendart_ppe_duration_period
```

M7 must NOT implement the remaining higher-risk / issuer-specific backlog items:

```text
5. hut_ppe_source_mapping
6. skhy_ocf_ppe_source_mapping
7. interest_bearing_debt_and_liquidity
8. inventory_receivables_working_capital
9. non_operating_financial_income_effects
```

Those remain separate future subpackages.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-existing-canonical-financial-domain-adapter-implementation-report.zip
```

Verified SHA-256:

```text
5098343001e265c2c27d28d90cad37575c040685d09c8fd22843bb54a3e3b08d
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M6 state:

```text
M1 = COMPLETE
M2 = COMPLETE
M3 = COMPLETE
M4 = COMPLETE
M5 = COMPLETE
M6 = COMPLETE

status = M6_COMPLETE
production_readiness = NOT_READY

next_scope =
ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES
```

Reported M6 repository provenance:

```text
base_sha =
29fb88be197c50b0da0eead886c89f27e823d3b4

work_instruction_commit =
35da4e7f1dd57194c3f5f6532ff91a13994f2448

implementation_commit =
bcad2ae16836a12ff208a110856575931bfbeb08

branch =
codex/20260908-existing-canonical-financial-domain-adapter-implementation
```

M6 completion artifact recorded final/report SHA as:

```text
NOT_MEASURED
PRECOMMIT_ARTIFACT_FREEZE
```

At M7 start use actual repository HEAD as authority and record the historical reporting state.

---

# 2. M6 result frozen for M7

M6 measured:

```text
same_period_adapter_status =
IMPLEMENTED_BOUNDED

ocf_adapter_status =
IMPLEMENTED_DIRECT_REPORTED

ppe_adapter_status =
IMPLEMENTED_DIRECT_REPORTED_PPE_ONLY

simple_cash_conversion_status =
IMPLEMENTED_DERIVED_SAFE
```

M6 current archive capability:

```text
canonical fact count = 606
canonical fact ticker count = 12

same-period comparison emissions = 130

OCF direct emissions = 122
PPE direct emissions = 104
OCF-PPE derived emissions = 104
```

M6 adapter denials:

```text
derived_period_lineage_metadata_incomplete = 189
simple_cash_conversion_input_derivation_unproven = 87
```

These denial counts are archive evidence, not universal market rates.

M7 should reduce only denials that can be resolved from already-existing canonical source/lineage metadata.

Do not manufacture missing metadata merely to lower denial counts.

---

# 3. M6 market-support state

M6 classified:

```text
US / foreign:
same-period comparison = EMITS_FINANCIAL_CONTEXT
OCF = EMITS_FINANCIAL_CONTEXT
PPE = EMITS_FINANCIAL_CONTEXT
OCF-PPE = EMITS_FINANCIAL_CONTEXT

KR:
same-period comparison = SOURCE_PRESENT_BUT_PERIOD_BLOCKED
OCF = SOURCE_PRESENT_BUT_PERIOD_BLOCKED
PPE = SOURCE_PRESENT_BUT_PERIOD_BLOCKED
OCF-PPE = SOURCE_PRESENT_BUT_PERIOD_BLOCKED
```

M7 must specifically determine whether existing OpenDART/canonical source metadata is sufficient to resolve those KR period blocks safely.

Do not assume the result must become `EMITS_FINANCIAL_CONTEXT`.

Fail-closed is an acceptable outcome.

---

# 4. User-approved operating constraints

## 4.1 Free/public data only

No paid provider changes.

M7 uses offline repository/cache/fixture evidence only.

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

## 4.3 Existing monitoring remains paused

The approved eight US/KR monitoring schedule paths remain paused.

Observe at start/end.

Do not automatically resume.

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
financial_context schema
M6 adapter
canonical fact catalog
OpenDART period normalization
cash-flow projection
compact AI context
source sufficiency
Daily Delta lifecycle
```

If unexplained semantic drift prevents a stable baseline:

```text
STOP
UNEXPLAINED_M7_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 6. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement the bounded projection subpackage.

---

# 7. M7 safety boundary — model input remains dormant

M7 may increase:

```text
financial_context emissions
comparison lineage availability
derived lineage completeness
KR typed period completeness
```

inside packet/source artifacts.

M7 must NOT change the compact AI input.

Required hard gate:

```text
MODEL_SEMANTIC_INPUT_UNCHANGED = 1
```

For representative fixtures:

```text
pre-M7 compact AI context hash
=
post-M7 compact AI context hash
```

Directional / Price-Timing prompt semantics remain unchanged.

If M7 mapping changes leak into model context:

```text
STOP
M7_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
```

---

# 8. M7 safety boundary — source sufficiency unchanged

No new universal or sector gate in M7.

Required:

```text
source_sufficiency_semantic_change_count = 0
```

Financial-context projection success/failure must not change:

```text
directional_model_eligible
```

for identical underlying source evidence.

---

# 9. M7 safety boundary — Daily Delta unchanged

M3 lifecycle semantics remain frozen.

Projection of additional typed lineage/period metadata into an existing baseline packet:

```text
must not create a new Daily Delta
```

Required:

```text
daily_delta_semantic_change_count = 0
```

No warning/assessment behavior change.

---

# 10. Subpackage A — compatible prior-year fact projection

## 10.1 Goal

Project already-existing compatible prior-year facts into the fact catalog / packet-builder input so the M6 comparison adapter can use them.

The M6 backlog reason was:

```text
selected packet catalogs often carry only the current cash-flow tuple
```

M7 may expand the internal projection of existing canonical facts.

M7 must NOT add new source taxonomy mappings.

## 10.2 Allowed input

Only facts already present in:

```text
canonical source cache
canonical fact catalog source
preserved official-source normalized records
existing repository fixtures
```

Do not fetch new provider data.

Do not map new SEC/OpenDART account concepts in this subpackage.

## 10.3 Compatibility

A prior-year fact may be projected only if the M6 comparison adapter can prove compatible:

```text
metric
currency
unit_scale
period type
entity scope
statement basis
attribution basis
fiscal relationship
```

Do not project an incompatible prior-year fact merely because ticker + metric name match.

## 10.4 Identity

Projected prior-year facts retain their canonical source/fact identity.

Do not generate a duplicate synthetic direct fact.

The same canonical prior-year fact projected twice must deduplicate.

## 10.5 Missing prior fact

If no compatible fact exists:

```text
comparison remains absent
```

No negative evidence.

---

# 11. Prior-year projection scope

M7 should support, where canonical metadata already exists:

```text
QTD → prior-year QTD
YTD → prior-year YTD
FY → prior-year FY
POINT_IN_TIME → prior-year comparable POINT_IN_TIME
```

Do not infer a prior comparable period by subtracting days from the date without canonical fiscal semantics.

Fiscal year / quarter relation must follow existing repository fiscal metadata.

If fiscal metadata is insufficient:

```text
do not project
```

---

# 12. Subpackage B — derived period lineage projection

## 12.1 Goal

Preserve existing derivation lineage that is currently lost when canonical fact-catalog records are projected into packet-building inputs.

The M6 backlog reason was:

```text
formula and derivation version are absent from the current fact-catalog projection
```

M7 must carry forward, where already present:

```text
derivation formula ID
derivation version
ordered input source refs
derived period start/end/type
currency/unit basis
entity/statement/attribution basis
```

## 12.2 No new derivation in M7

M7 does NOT invent or newly compute:

```text
derived OCF period
derived PPE period
TTM
QTD from YTD
```

unless that derived fact already exists under canonical source/normalization logic.

M7 only projects existing derivation identity/lineage into the M6 adapter input.

## 12.3 Incomplete lineage

If an existing derived fact lacks:

```text
formula
version
input refs
period compatibility
```

then:

```text
remain blocked
```

Do not fill the gap from prose or ticker knowledge.

---

# 13. Derived lineage determinism

Projection must preserve deterministic identity.

Required:

```text
same derived fact source identity
same formula/version
same input refs
→ same projected lineage digest
```

No runtime timestamp/random identity.

Repeated projection must be idempotent.

---

# 14. Subpackage C — KR OpenDART OCF duration period

## 14.1 Goal

Determine whether existing OpenDART/canonical normalized metadata can safely establish OCF duration periods.

The M6 state was:

```text
KR OCF source present
period context unresolved
→ financial_context emission blocked
```

M7 may implement a generic KR duration-period mapper only if the repository already holds authoritative period metadata sufficient for the mapping.

## 14.2 Allowed evidence

Potential existing metadata may include:

```text
report code / report type
statement period start/end
business year
quarter/half-year/fiscal-year context
OpenDART normalized statement metadata
canonical filing/report-period object
```

Use only what actually exists in current code/fixtures.

Do not assume all fields exist.

## 14.3 Required proof

For a KR OCF fact, the mapper must establish:

```text
period.type
period.start
period.end
duration_days

fiscal year
fiscal quarter / half-year where applicable

currency
entity/statement basis
```

with source lineage.

If start/end cannot be proven:

```text
do not emit financial_context
```

## 14.4 No heuristic guessing

Forbidden:

```text
Q1 => Jan 1 start
Q2 => Jan 1 start
Q3 => Jan 1 start
annual => Jan 1 start
```

based only on quarter/report label unless the canonical OpenDART fiscal metadata proves that calendar-year relationship.

Issuers may have non-calendar fiscal periods.

Fail closed.

---

# 15. KR cumulative vs quarter semantics

If OpenDART evidence represents cumulative cash flow:

```text
preserve as YTD / FY
```

Do not relabel it QTD.

Do not subtract prior cumulative period to derive QTD OCF in M7 unless a canonical derived-period fact already exists with complete lineage.

This remains outside the scope of period projection.

---

# 16. Subpackage D — KR OpenDART PPE duration period

Use the same period-safety contract as KR OCF.

A PPE cash-flow item may emit typed financial context only if:

```text
duration start/end proven
period type proven
currency/unit known
entity/statement basis compatible
```

Do not infer a period from filing title alone.

Do not infer PPE capex sign/scope beyond the already-canonical source mapping.

---

# 17. KR OCF-PPE simple cash-conversion

After both OCF and PPE typed contexts are emitted for KR, M6 may derive:

```text
ocf_less_ppe_capex
```

only if all M6 compatibility checks pass.

M7 does not weaken:

```text
same period
same currency
same unit scale
same entity scope
same statement basis
same attribution basis
PPE-only scope
```

If only one side has resolved period metadata:

```text
do not derive
```

---

# 18. Period ambiguity block accounting

M6 recorded:

```text
period_ambiguity_block_count = 3
```

M7 must report:

```text
pre_m7_period_ambiguity_block_count
post_m7_period_ambiguity_block_count
resolved_block_count
remaining_block_count
```

Do not make `resolved_block_count` a success target.

Correct fail-closed blocks may remain.

---

# 19. Adapter denial accounting

M6 recorded:

```text
derived_period_lineage_metadata_incomplete = 189
simple_cash_conversion_input_derivation_unproven = 87
```

M7 should recompute equivalent archive diagnostics after projection.

Report:

```text
pre / post denial counts
reason-specific deltas
```

Do not claim broad market improvement from archive counts alone.

Reduction is valid only when provenance is actually recovered.

---

# 20. No HUT / SKHY issuer-specific mappings

M7 must not implement:

```text
hut_ppe_source_mapping
skhy_ocf_ppe_source_mapping
```

Even if convenient fixtures exist.

Keep these in the next backlog.

No ticker-specific exceptions.

---

# 21. No higher-risk domain activation

M7 must not populate:

```text
interest-bearing debt / liquidity

inventory / receivables / working capital

non-operating / financial effects
```

into `financial_context`.

Negative regression:

```text
M7 higher-risk financial_context emission count = 0
```

---

# 22. Fact-catalog projection boundary

Preferred change surface:

```text
fact catalog projection / canonical fact selection
lineage metadata projection
KR period-normalization helper
M6 adapter input plumbing
tests
```

Avoid modifying:

```text
raw provider parser taxonomy
Directional prompt
Price-Timing
renderer
monitoring lifecycle
notification system
```

If new raw source account mapping is required:

```text
STOP that item
record SOURCE_EXISTS_MAPPING_INCOMPLETE
```

and defer to next subpackage.

---

# 23. Existing source cache only

M7 may read existing:

```text
cached SEC normalized artifacts
cached OpenDART normalized artifacts
repository fixture files
historical phase reports
```

No network.

If the canonical cache cannot prove a mapping:

```text
NOT_MEASURED / BLOCKED
```

Do not fetch.

---

# 24. Positive fixture matrix — prior-year projection

At minimum:

```text
US QTD current + compatible prior QTD

US YTD current + compatible prior YTD

US FY current + prior FY

POINT_IN_TIME current + prior comparable

existing canonical prior-year fact dedup

projection enables M6 comparison emission
```

No new growth calculation required unless already canonical.

---

# 25. Negative prior-year fixtures

At minimum:

```text
prior metric mismatch

prior currency mismatch

prior entity scope mismatch

prior statement basis mismatch

prior attribution mismatch

prior fiscal period incompatible

same ticker but wrong security/entity scope

duplicate prior fact candidate ambiguity

no compatible prior fact
```

Expected:

```text
no comparison emission
```

not exception unless the canonical contract requires fail-closed error.

---

# 26. Positive derived-lineage fixtures

At minimum:

```text
existing derived fact with complete formula/version/input refs

derived OCF fact with complete period lineage

derived PPE fact with complete period lineage

projection allows M6 typed context

projection allows M6 OCF-PPE derivation where all inputs compatible
```

---

# 27. Negative derived-lineage fixtures

At minimum:

```text
formula missing

version missing

input refs missing

input refs unordered/incompatible

derived period start missing

derived period end missing

currency basis missing

entity scope mismatch

statement basis mismatch

lineage points to missing source ref
```

Remain blocked.

Do not repair by guessing.

---

# 28. Positive KR period fixtures

Use offline OpenDART/canonical fixtures with explicit authoritative period metadata.

At minimum:

```text
KR OCF YTD explicit period

KR OCF FY explicit period

KR PPE YTD explicit period

KR PPE FY explicit period

KR OCF + PPE compatible derived simple cash conversion
```

If the repository has no authoritative fixture supporting a case:

```text
do not fabricate one as proof of current source support
```

You may create a synthetic unit fixture to test the mapper, but separately label:

```text
SYNTHETIC_CONTRACT_FIXTURE
```

and do not count it as real source-support proof.

---

# 29. Negative KR period fixtures

At minimum:

```text
filing/report label only, no authoritative start date

quarter known but fiscal-year start unknown

non-calendar issuer ambiguity

OCF period known, PPE period unknown

PPE period known, OCF period unknown

current/prior period mixed

statement basis incompatible
```

Expected:

```text
financial_context suppressed
simple cash-conversion suppressed
```

---

# 30. Compact AI context non-leak

Re-run M6 hard gate for representative fixtures:

```text
prior-year projection
derived lineage projection
KR OCF period mapping
KR PPE period mapping
```

Required:

```text
pre/post compact AI context hash equal
changed count = 0
```

If not:

```text
STOP
M7_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
```

---

# 31. Prompt no-change

Required:

```text
Directional prompt bytes/semantic hash unchanged
Price-Timing prompt bytes/semantic hash unchanged
```

No renderer change.

No ownership change.

---

# 32. Source sufficiency no-change

For representative subjects with additional projected financial context:

```text
pre source readiness
=
post source readiness
```

Required:

```text
source_sufficiency_semantic_change_count = 0
```

---

# 33. Daily Delta no-change

Re-run M3 fixture confirming:

```text
baseline enriched with projected historical financial context
→ not Daily Delta
```

and:

```text
late-arriving pre-baseline projected fact
→ not strengthened/weakened
```

Required:

```text
daily_delta_semantic_change_count = 0
```

---

# 34. Adapter / projection idempotency

Repeated:

```text
fact projection
KR period mapping
M6 financial-context adaptation
```

must produce identical outputs and no duplicate refs.

Required:

```text
projection_idempotency = PASS
adapter_idempotency = PASS
```

---

# 35. Historical packet compatibility

M5/M6 legacy packet fixtures remain valid.

Required:

```text
legacy parse PASS
legacy hash unchanged
```

No archive rewrite.

New projected facts exist only in newly built fixture/source packet outputs.

---

# 36. Market support classification after M7

Report each domain-market pair as:

```text
EMITS_FINANCIAL_CONTEXT

SOURCE_PRESENT_BUT_PERIOD_BLOCKED

SOURCE_PRESENT_LINEAGE_BLOCKED

SOURCE_PRESENT_MAPPING_INCOMPLETE

NO_EXISTING_CANONICAL_SOURCE

NOT_MEASURED
```

Do not claim:

```text
KR universally supports OCF
```

based on a few fixtures.

Separate:

```text
adapter capability
from
issuer coverage
```

---

# 37. Remaining backlog after M7

M7 must produce an ordered remaining backlog.

Expected unresolved categories may include:

```text
HUT PPE source mapping

SKHY OCF/PPE source mapping

interest-bearing debt / liquidity

inventory / receivables / working capital

non-operating / financial effects

any unresolved KR period lineage cases

any unresolved prior-year projection gaps
```

Do not automatically choose the next task solely by original sequence.

Prioritize:

```text
generic cross-issuer coverage benefit
semantic risk
free-source support
```

---

# 38. Validation requirements

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
M5 schema tests
M6 adapter tests
M7 projection tests
cash-flow canonical fact tests
OpenDART period-normalization tests
compact AI non-leak tests
source-sufficiency no-change tests
M3 lifecycle no-change tests
```

No model tests.

No live provider tests.

---

# 39. Production side-effect firewall

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

# 40. Required artifacts — provenance / scope

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m7-scope-freeze
04-m6-contract-reuse-proof
05-m7-projection-responsibility-matrix
```

---

# 41. Required artifacts — projection implementation

Produce:

```text
06-current-fact-catalog-projection-inventory
07-compatible-prior-year-projection-contract
08-derived-period-lineage-projection-contract
09-kr-opendart-ocf-period-contract
10-kr-opendart-ppe-period-contract
11-projection-implementation-diff
12-projection-activation-surface
13-period-and-lineage-support-audit
```

---

# 42. Required artifacts — no-change proofs

Produce:

```text
14-compact-ai-context-non-leak-proof
15-directional-prompt-no-change-proof
16-price-timing-no-change-proof
17-source-sufficiency-no-change-proof
18-daily-delta-no-change-proof
19-historical-packet-compatibility
20-projection-and-adapter-idempotency
```

---

# 43. Required artifacts — tests / coverage

Produce:

```text
21-positive-fixture-manifest
22-negative-fixture-manifest
23-pre-post-denial-accounting
24-focused-test-results
25-full-test-results
26-ruff-and-diff-results
```

---

# 44. Required decision artifacts

Produce:

```text
27-remaining-source-mapping-backlog
28-next-subpackage-priority-decision
29-directional-specificity-activation-decision
30-source-sufficiency-no-change-decision
31-production-no-change
32-schedule-pause-observation
33-master-workflow-update
34-program-completion
```

Expected:

```text
Directional specificity activation =
NOT_IN_M7

source sufficiency =
UNCHANGED
```

---

# 45. M7 acceptance criteria

M7 is COMPLETE only if:

```text
compatible prior-year fact projection implemented
for existing canonical compatible facts

existing derived lineage is projected
without inventing missing derivation metadata

KR OCF/PPE period mapper is implemented only where
authoritative period metadata is available

ambiguous KR period remains fail-closed

M6 adapters consume newly projected metadata safely

comparison/OCF/PPE/simple-cash conversion
remain idempotent

no new raw source taxonomy mappings

no HUT/SKHY ticker-specific mappings

no debt/working-capital/non-operating activation

compact AI context unchanged

Directional / Timing prompts unchanged

source sufficiency unchanged

Daily Delta semantics unchanged

legacy packet compatibility preserved

focused/full tests PASS
ruff PASS
git diff --check PASS

all side-effect counts = 0
```

M7 does NOT require:

```text
all KR issuers to gain OCF/PPE support

all derived-period denials to disappear

higher-risk financial domains

Directional model use of financial_context

model proof

real holdout

production readiness
```

---

# 46. Next-scope decision

If M7 passes, select the next bounded subpackage from the measured remaining backlog.

Preferred decision logic:

## A. Generic unresolved mappings dominate

If remaining low-risk generic mapping gaps provide broad coverage:

```text
next_scope =
ADDITIONAL_CANONICAL_FINANCIAL_SOURCE_MAPPING_IMPLEMENTATION
```

Examples:

```text
generic existing-source OCF/PPE gaps
generic issuer/security source normalization
```

## B. Only HUT/SKHY issuer-specific gaps remain before higher-risk domains

Do not create ticker-specific production exceptions.

Classify whether each reflects a generic source-class gap.

If generic:

```text
SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION
```

If truly ticker-specific:

```text
DEFER / DO_NOT_IMPLEMENT_TICKER_EXCEPTION
```

## C. Higher-risk domains become the main backlog

Then:

```text
HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION
```

covering:

```text
debt/liquidity
working capital
non-operating effects
```

in bounded subpackages.

## D. Financial-context coverage is sufficient for Directional specificity implementation

Only if measured generic coverage is adequate and the remaining mapping gaps are not material to the planned reasoning contract:

```text
DIRECTIONAL_SPECIFICITY_CONTRACT_IMPLEMENTATION
```

Do not activate the prompt automatically in M7.

---

# 47. Master workflow update

Update:

```text
docs/MASTER_WORKFLOW.md
```

at completion.

Expected:

```text
M6 COMPLETE
→
M7 COMPLETE
→
measured next mapping/specificity scope
```

Production readiness remains:

```text
NOT_READY
```

Monitoring remains paused.

---

# 48. Program-completion fields

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

prior_year_projection_status
derived_lineage_projection_status
kr_ocf_period_projection_status
kr_ppe_period_projection_status

prior_year_projected_fact_count
derived_lineage_projected_fact_count

kr_ocf_period_resolved_count
kr_ocf_period_blocked_count
kr_ppe_period_resolved_count
kr_ppe_period_blocked_count

pre_period_ambiguity_block_count
post_period_ambiguity_block_count

pre_derived_lineage_denial_count
post_derived_lineage_denial_count

pre_simple_cash_input_lineage_denial_count
post_simple_cash_input_lineage_denial_count

same_period_comparison_emission_count
ocf_emission_count
ppe_emission_count
simple_cash_conversion_emission_count

projection_idempotency_status
adapter_idempotency_status

new_sec_mapping_count
new_opendart_mapping_count
ticker_specific_mapping_count

higher_risk_domain_emission_count

compact_ai_context_changed_count
directional_prompt_change_count
price_timing_prompt_change_count

source_sufficiency_semantic_change_count
daily_delta_semantic_change_count

legacy_fixture_count
legacy_parse_pass_count
legacy_hash_unchanged_count

positive_fixture_count
positive_fixture_pass_count
negative_fixture_count
negative_fixture_rejected_count

remaining_source_mapping_backlog_count
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

# 49. Artifact integrity

Create the final artifact index only after:

```text
program completion
master workflow update
all reports
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

# 50. Final task principle

M6 safely activated existing canonical financial evidence.

The next gap is mostly not the packet schema and not the model prompt.

It is missing projection of already-existing comparable facts, derivation lineage and KR period context.

The correct M7 flow is:

```text
recover canonical lineage / period metadata
→ project it safely
→ let the existing M6 adapter consume it
→ prove no model-input leak
→ freeze
```

Not:

```text
invent missing derivations
```

Not:

```text
guess KR fiscal periods
```

Not:

```text
add ticker-specific HUT/SKHY hacks
```

Not:

```text
jump to debt/working-capital/non-operating mapping
```

Not:

```text
activate Directional prompt specificity
```

And not:

```text
resume production monitoring
```

Complete the lineage/period layer first.
