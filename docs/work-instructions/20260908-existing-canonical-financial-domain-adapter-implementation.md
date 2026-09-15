# Thesis Monitor — Existing Canonical Financial Domain Adapter Implementation

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-existing-canonical-financial-domain-adapter-implementation.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-existing-canonical-financial-domain-adapter-implementation-report.zip
```

Master-workflow phase:

```text
M6 — Existing Canonical Financial Domain Adapter Implementation
```

This task begins only after M5 has completed.

M5 added the optional typed:

```text
DecisionEvidenceRef.financial_context
```

envelope and froze its validation/backward-compatibility contract.

M6 implements the next frozen M4 package:

```text
A_EXISTING_CANONICAL_DOMAIN_ADAPTERS
```

The task must connect only already-canonical, already-available financial evidence into `financial_context`.

Initial bounded domains for M6:

```text
same_period_prior_year_comparison

operating_cash_flow

ppe_capex_simple_cash_conversion
```

M6 is NOT:

- a new SEC/OpenDART taxonomy expansion task;
- a debt/liquidity mapping task;
- a working-capital mapping task;
- a non-operating-income mapping task;
- a source-sufficiency semantic change;
- a Directional Core prompt change;
- a model validation task;
- a real holdout proof;
- a production deployment;
- a monitoring-schedule resume task.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-decision-evidence-packet-financial-context-domain-extension-implementation-report.zip
```

Verified SHA-256:

```text
3c099c405892a2269e1dac8d94100f4d3c52880d1bf07f0a00e1b7c09df76b60
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M5 result:

```text
M1 = COMPLETE
M2 = COMPLETE
M3 = COMPLETE
M4 = COMPLETE
M5 = COMPLETE

status = M5_COMPLETE
production_readiness = NOT_READY

next_scope =
EXISTING_CANONICAL_FINANCIAL_DOMAIN_ADAPTER_IMPLEMENTATION
```

Reported repository provenance:

```text
base_sha =
1f39271b6d7e161dc86bc11d71dd111b2b48937d

work_instruction_commit =
fbb4700a7f884e166f75b154433b5e0f2ae4126f

implementation_commit =
e493474199323ce0f08066d41c327de3c23b8b05

branch =
codex/20260908-decision-evidence-packet-financial-context-domain-extension-implementation
```

M5 `program-completion` intentionally recorded final/report SHA as:

```text
NOT_MEASURED
```

because its completion artifact was frozen pre-report-commit.

At task start use the actual repository HEAD as authority.

Record:

```text
actual_m5_final_head
actual_m5_report_commit_if_identifiable
historical_precommit_reporting_state
```

Do not treat the M5 reporting omission as semantic drift by itself.

---

# 2. M5 contract frozen for M6

M5 added:

```text
financial_context: optional
```

with:

```text
metric
currency
unit_scale
period
entity_scope
statement_basis
attribution_basis
evidence_status
quality
comparison
derivation
limitations
```

Evidence status:

```text
DIRECT_REPORTED
DERIVED_SAFE
```

Period types:

```text
QTD
YTD
FY
TTM
POINT_IN_TIME
```

M5 proved:

```text
legacy packet fixtures = 14
legacy parse PASS = 14
legacy hash unchanged = 14

positive fixtures = 14 / 14 PASS
negative fixtures = 19 / 19 rejected

source producer activation = 0
Directional prompt change = 0
Price-Timing prompt change = 0
source-sufficiency semantic change = 0
```

M6 must preserve all M5 schema/validation semantics.

---

# 3. M4/M5 implementation order

Frozen order:

```text
1. B_PACKET_FINANCIAL_CONTEXT_EXTENSION     ← completed M5
2. A_EXISTING_CANONICAL_DOMAIN_ADAPTERS     ← M6
3. A_ADDITIONAL_SOURCE_MAPPING_SUBPACKAGES
4. C_DIRECTIONAL_SPECIFICITY_CONTRACT
5. D_SECTOR_GATE_REVIEW_IF_COVERAGE_PROVES_REQUIRED
```

M6 must not jump ahead to packages 3–5.

---

# 4. User-approved operating constraints

## 4.1 Free/public data only

Do not add or upgrade paid data providers.

M6 must use repository fixtures / preserved source artifacts only.

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

Observe at task start/end.

If all remain paused:

```text
scheduler mutation = 0
```

If one exact approved path unexpectedly became active:

```text
pause only that path
record actual mutation
```

Do not alter unrelated schedules.

Do not automatically resume monitoring after M6.

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
DecisionEvidenceRef / FinancialContext
source packet builders
financial normalization
compact AI context
Directional / Price-Timing prompt builders
source sufficiency
monitoring lifecycle
```

If unexplained semantic drift prevents a stable M6 baseline:

```text
STOP
UNEXPLAINED_M6_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 6. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement the bounded adapters.

---

# 7. Primary M6 safety boundary

M6 may cause eligible `DecisionEvidenceRef` objects to contain:

```text
financial_context != null
```

in source/packet artifacts.

However M6 must NOT yet change what the AI model sees.

Required hard gate:

```text
MODEL_SEMANTIC_INPUT_UNCHANGED = 1
```

Specifically:

```text
compact AI context must not begin emitting financial_context
Directional prompt bytes/semantic context must remain unchanged
Price-Timing prompt bytes/semantic context must remain unchanged
```

for equivalent legacy source fixtures.

If adapter activation automatically leaks `financial_context` into model context through generic serialization:

```text
STOP
M6_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
```

Do not silently filter or rewrite model prompts unless the filtering is an already-canonical semantic-neutral boundary.

If a bounded explicit omission is needed in the compact-context serializer to preserve the existing contract:

```text
allowed only as compatibility plumbing
```

and must be proven byte/semantic neutral for pre-M6 model inputs.

---

# 8. M6 adapter boundary

Preferred implementation:

```text
source-normalized evidence
→ financial-domain adapter
→ DecisionEvidenceRef.financial_context
```

Do not move source taxonomy/accounting logic into the generic `FinancialContext` schema validator.

M5 responsibility matrix remains authoritative:

## Generic schema validator

Owns:

```text
period structure
enum validity
derivation metadata
basic internal consistency
```

## Domain adapter

Owns:

```text
same semantic field compatibility
period comparability
currency/unit compatibility
entity scope compatibility
statement basis compatibility
attribution basis compatibility
```

M6 implements only the adapter rules required for its three domains.

---

# 9. M6 domain set

Implement only:

```text
A. same_period_prior_year_comparison
B. operating_cash_flow
C. ppe_capex_simple_cash_conversion
```

Do not implement:

```text
debt_liquidity
inventory_receivables_working_capital
non_operating_financial_income_effects
```

except test fixtures proving that M6 does not accidentally emit them.

---

# 10. Domain A — same-period prior-year comparison adapter

## 10.1 Goal

Represent a validated current-vs-prior-year comparable relationship without losing period/basis provenance.

The adapter may emit:

```text
current evidence ref
prior comparable evidence ref
derived comparison evidence ref where safe
```

according to the existing packet architecture.

Do not force one representation if current repository conventions already define comparison evidence differently.

The key requirement is that `financial_context.comparison` captures compatible lineage.

## 10.2 Allowed comparison bases

Only:

```text
QTD vs prior-year QTD
YTD vs prior-year YTD
FY vs prior-year FY
compatible POINT_IN_TIME vs prior-year comparable POINT_IN_TIME
```

where semantic field, currency, entity scope, statement basis and attribution basis are compatible.

Do not compare:

```text
QTD vs YTD
QTD vs FY
YTD vs FY
different semantic fields
different attribution bases
different currencies
different entity scopes
different statement bases
```

unless an already-frozen canonical normalization explicitly proves compatibility.

## 10.3 Derived values

M6 may emit only pre-approved safe derivation metadata already supported by repository logic or explicit fixture-backed canonical comparison.

Examples:

```text
same_period_absolute_delta
same_period_growth_rate
```

only if a canonical calculation already exists or is implemented as a generic adapter-level safe derivation covered by tests.

Do not introduce arbitrary ratio derivations.

If growth rate derivation is not already part of the M4/M5 frozen contract:

```text
prefer comparison lineage only
```

and leave growth calculation to a later bounded implementation.

## 10.4 Missing comparison

If prior comparable data is absent or incompatible:

```text
do not emit comparison
do not mark negative
```

The current evidence may still exist without comparison metadata.

---

# 11. Domain B — operating cash flow adapter

## 11.1 Goal

Attach safe typed financial context to already-canonical official operating cash flow evidence.

Required:

```text
official cash-flow-statement provenance

financial currency
unit scale
period
entity scope
statement basis
evidence status
```

## 11.2 Period rules

OCF is typically:

```text
YTD
FY
TTM derived later where safe
```

Do not label cumulative YTD OCF as QTD.

Do not derive single-quarter OCF in M6 unless a pre-existing canonical same-semantic cumulative subtraction is already implemented and separately proven safe.

Default M6 behavior:

```text
preserve directly reported period
```

## 11.3 Sector applicability

For:

```text
banks
insurers
other financial institutions
```

generic industrial-company "earnings quality" interpretation is NOT activated in M6.

The adapter may represent the evidence if canonical source semantics support it, but:

```text
Directional use remains inactive
sector caution limitation may be attached only if frozen by M4 contract
```

Do not add a source-sufficiency gate.

---

# 12. Domain C — PPE capex adapter

## 12.1 Goal

Attach typed context to already-canonical purchase of property/plant/equipment evidence.

Represent direct PPE purchase as:

```text
DIRECT_REPORTED
```

when official source mapping is already canonical.

Do not call the direct PPE purchase itself:

```text
FCF
```

## 12.2 Simple cash-conversion derivative

M6 may implement `DERIVED_SAFE`:

```text
ocf_less_ppe_capex
```

ONLY when both OCF and PPE inputs satisfy all compatibility rules.

Required:

```text
same financial currency
same unit scale or safely normalized
same entity scope
same statement basis
compatible duration period
compatible period start/end
```

Input lineage must contain both source refs.

Derivation metadata:

```text
formula = ocf_less_ppe_capex
version = frozen adapter version
input_source_refs = [OCF ref, PPE ref]
```

## 12.3 Required label

Do NOT label:

```text
ocf_less_ppe_capex
```

as canonical `free_cash_flow` unless the full capex definition is complete under a future contract.

Use a metric identifier equivalent to:

```text
ocf_less_ppe_capex
```

or:

```text
simple_cash_conversion_proxy
```

according to M5 canonical metric naming conventions.

## 12.4 Growth vs maintenance capex

Always preserve limitation when applicable:

```text
growth_vs_maintenance_capex_unknown
```

Do not infer maintenance capex.

---

# 13. KR OCF / PPE period ambiguity — fail closed

M4 explicitly froze:

```text
KR OCF / PPE period unresolved
→ fail closed
```

M6 must preserve this.

If a KR source fixture lacks sufficient period metadata to prove:

```text
YTD/FY duration
start/end compatibility
```

then:

```text
financial_context emission = 0
```

for that evidence or derivative.

Do not:

```text
guess YTD from filing type
guess period start from quarter number
assume current-year Jan 1 start
```

unless existing canonical OpenDART period metadata already proves it.

Required tests:

```text
KR period known → allowed
KR period ambiguous → blocked
```

---

# 14. Existing source mappings only

M6 adapter input must come only from financial semantics already produced by current canonical parser/normalizer paths.

Do not add new:

```text
SEC taxonomy tags
OpenDART account mappings
custom field aliases
provider-specific fallback concepts
```

If a domain fixture cannot be produced without a new source mapping:

```text
record SOURCE_EXISTS_MAPPING_INCOMPLETE
```

and defer to:

```text
A_ADDITIONAL_SOURCE_MAPPING_SUBPACKAGES
```

Do not expand scope.

---

# 15. Adapter emission contract

For every emitted `financial_context`, the adapter must prove:

```text
source evidence already exists
source_ref valid
metric canonical
period known
currency/unit compatible
basis metadata known enough
DIRECT/DERIVED status correct
```

If any required typed provenance is missing:

```text
do not emit financial_context
```

Do not emit:

```text
quality = partial
```

as a workaround for missing hard compatibility metadata if the M4 contract requires fail-closed behavior.

`partial` describes evidence quality, not permission to invent basis/period.

---

# 16. Adapter idempotency

Repeated adapter execution over the same source evidence must produce:

```text
identical financial_context
identical derived ref IDs/hashes where deterministic
no duplicate evidence refs
```

Required:

```text
adapter_idempotency = PASS
```

If current packet builder deduplicates by source_ref or evidence ID, follow that canonical behavior.

Do not create parallel duplicate OCF/PPE refs.

---

# 17. Derived evidence identity

Any M6-generated derived evidence ref must have deterministic identity based on:

```text
formula/version
ordered input source refs
period/basis identity
```

Do not include:

```text
runtime timestamp
random UUID
model generation ID
```

in canonical derivation identity.

The same inputs and adapter version must produce the same derived evidence identity/hash.

---

# 18. Source-ref lineage

Derived evidence must preserve input lineage.

Required:

```text
FinancialDerivation.input_source_refs
```

and any existing packet-level provenance conventions.

Do not permit:

```text
derived value with only one combined prose source ref
```

if two direct financial inputs exist.

---

# 19. Currency / unit normalization boundary

If OCF and PPE direct sources have:

```text
same currency
different unit_scale
```

a safe adapter-level normalization may be performed only if the current repository already has deterministic unit normalization semantics.

If not:

```text
do not derive
```

Represent the direct refs separately.

Do not implement an ad hoc converter in M6 without an explicit canonical helper/test contract.

No FX conversion in M6.

---

# 20. Entity / statement / attribution compatibility

For any comparison or OCF-PPE derivation, require compatible:

```text
entity_scope
statement_basis
attribution_basis where applicable
```

If a field is genuinely not applicable:

```text
null is allowed only where M5 schema permits
```

Do not compare/derive:

```text
consolidated vs separate
parent-attributable vs total
different issuer/security scope
```

M6 must fail closed.

---

# 21. Direct vs derived contract

Required:

## Source occurrences

```text
evidence_status = DIRECT_REPORTED
derivation = null
```

## Adapter calculations

```text
evidence_status = DERIVED_SAFE
derivation required
```

Do not rewrite a derived number into a direct ref after calculation.

---

# 22. No investment semantic activation

M6 populates typed packet context.

M6 does NOT change how investment decisions are made.

Required all zero:

```text
Directional prompt changes
Price-Timing prompt changes
renderer changes
ownership semantic changes
source-sufficiency semantic changes
Daily Delta semantic changes
```

The new packet fields are dormant for model reasoning until Package C is separately authorized.

---

# 23. Compact AI context non-leak hard gate

This is a critical M6 requirement.

For representative source fixtures before vs after adapter activation:

```text
DecisionEvidencePacket may differ
```

because it now contains typed `financial_context`.

However:

```text
compact AI context supplied to Directional Core
must be identical to pre-M6 semantic input
```

until the later Directional specificity package.

Required proof:

```text
pre_m6_compact_ai_context_sha256
post_m6_compact_ai_context_sha256

semantic input unchanged = true
```

For multiple fixtures covering:

```text
comparison
OCF
PPE
OCF-PPE derived context
```

If current compact-context builder serializes `financial_context` automatically:

Implement the smallest semantic-neutral exclusion seam needed to preserve the frozen model-input contract.

Do not change any other context field.

If this cannot be achieved without a broader prompt/input redesign:

```text
STOP
M6_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
```

---

# 24. Source-sufficiency no-change hard gate

For all representative fixtures:

```text
source readiness before M6
=
source readiness after M6
```

Required:

```text
source_sufficiency_semantic_change_count = 0
```

`financial_context` presence must not convert:

```text
INSUFFICIENT → SUFFICIENT
SUFFICIENT → INSUFFICIENT
```

in M6.

---

# 25. Daily Delta no-change hard gate

M3 lifecycle semantics remain frozen.

Populating financial context in a baseline/source packet must not automatically create a Daily Delta.

Required fixture:

```text
same evidence semantics
before vs after M6 adapter

Daily Delta outcome unchanged
```

Bootstrap enrichment remains:

```text
NOT Daily Delta
```

No assessment/warning behavior change.

---

# 26. Historical artifact compatibility

Historical packets without `financial_context` must still:

```text
parse
roundtrip
retain canonical hash
```

Existing archived artifacts are not rewritten.

M6 should reuse M5 legacy fixtures and expand historical coverage only if readily available.

---

# 27. Positive fixture matrix

At minimum include fixture cases:

```text
US QTD same-period comparison compatible

US YTD same-period comparison compatible

US FY same-period comparison compatible

POINT_IN_TIME prior-year comparable compatible

US OCF direct YTD

US OCF direct FY

KR OCF direct with explicit valid period

US PPE purchase direct YTD

US PPE purchase direct FY

KR PPE direct with explicit valid period

OCF-PPE derived safe same YTD period

OCF-PPE derived safe FY

unit-scale normalized safe derivation if canonical helper exists
```

No live provider calls.

---

# 28. Negative fixture matrix

At minimum:

```text
QTD vs YTD comparison
current vs prior with different semantic metric
different currency comparison
different entity scope comparison
different statement basis comparison
different attribution basis comparison

OCF missing start date for duration period

KR OCF ambiguous period

KR PPE ambiguous period

OCF YTD + PPE FY derivation

OCF/PPE different currency

OCF/PPE incompatible entity scope

OCF/PPE incompatible statement basis

OCF/PPE missing one source ref

derived evidence without full lineage

growth-vs-maintenance limitation omitted when contract requires it

duplicate derived ref on repeated adapter run
```

Fail closed.

---

# 29. Market-support audit

Without provider calls, report actual M6 adapter support from repository fixtures/code:

For each domain-market pair classify:

```text
EMITS_FINANCIAL_CONTEXT

SOURCE_PRESENT_BUT_PERIOD_BLOCKED

SOURCE_PRESENT_MAPPING_INCOMPLETE

NO_EXISTING_CANONICAL_SOURCE

NOT_MEASURED
```

Do not overclaim broad market coverage based on fixtures.

M6 support means:

```text
the adapter can safely represent existing canonical evidence
```

not:

```text
all issuers in that market now have the domain
```

---

# 30. Producer activation surface

M6 may activate `financial_context` emission only in the shared packet/source-building path that consumes existing canonical normalized evidence.

Report exact changed producers/builders.

Required:

```text
new SEC taxonomy mappings = 0
new OpenDART mappings = 0
new paid provider mappings = 0
```

If multiple packet builders exist:

```text
either use one shared adapter
or prove consistency across builders
```

Do not implement market-specific duplicated logic if a shared generic adapter is feasible.

---

# 31. Public/internal schema surface

M5 reported:

```text
public_schema_changed = false
```

M6 should not change the type schema.

Producer emission may cause internal packet instances to contain `financial_context`.

Audit whether any public read-only response automatically serializes these internal refs.

If a public response changes in fixture tests:

```text
record it
prove additive optional compatibility
```

Do not modify API operation IDs.

Do not make field required.

---

# 32. Test-only evidence output

Produce file-only example packets:

```text
legacy packet without financial_context

packet with same-period comparison

packet with OCF direct context

packet with PPE direct context

packet with OCF-PPE derived context

KR ambiguous-period packet with no emitted context
```

Label:

```text
OFFLINE_NONPRODUCTION_FIXTURE
```

Do not use production DB.

---

# 33. Implementation scope

Preferred changed code:

```text
shared financial-context adapter module
packet-builder compatibility plumbing
compact-context exclusion seam if necessary
tests
```

Avoid:

```text
source taxonomy parser changes
Directional prompt changes
Price-Timing changes
renderer changes
monitoring lifecycle changes
notification changes
```

If source parser mapping changes are necessary to make M6 useful:

```text
STOP
```

and move them to the next additional-source-mapping subpackage.

---

# 34. Validation requirements

Run:

```text
focused pytest
full repository pytest
ruff
git diff --check
```

Required all PASS.

Focused suite must include:

```text
M5 financial_context schema tests
M6 adapter tests
packet-builder tests
compact AI-context non-leak tests
source-sufficiency no-change tests
M3 lifecycle no-change tests
ownership regression tests impacted by packet serialization
```

No model tests.

No live provider tests.

---

# 35. Production side-effect firewall

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

# 36. Required artifacts — provenance/scope

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m6-scope-freeze
04-m5-contract-reuse-proof
05-m6-adapter-responsibility-matrix
```

---

# 37. Required artifacts — adapter implementation

Produce:

```text
06-current-canonical-financial-source-inventory
07-same-period-comparison-adapter-contract
08-operating-cash-flow-adapter-contract
09-ppe-capex-adapter-contract
10-simple-cash-conversion-derivation-contract
11-adapter-implementation-diff
12-producer-activation-surface
13-market-support-audit
```

---

# 38. Required artifacts — semantic no-change proof

Produce:

```text
14-compact-ai-context-non-leak-proof
15-directional-prompt-no-change-proof
16-price-timing-no-change-proof
17-source-sufficiency-no-change-proof
18-daily-delta-no-change-proof
19-historical-packet-compatibility
20-adapter-idempotency-proof
```

---

# 39. Required artifacts — fixtures/tests

Produce:

```text
21-positive-fixture-manifest
22-negative-fixture-manifest
23-offline-example-packets
24-focused-test-results
25-full-test-results
26-ruff-and-diff-results
```

---

# 40. Required decision artifacts

Produce:

```text
27-additional-source-mapping-backlog
28-directional-specificity-activation-decision
29-source-sufficiency-no-change-decision
30-production-no-change
31-schedule-pause-observation
32-master-workflow-update
33-program-completion
```

Expected:

```text
directional specificity activation =
NOT_IN_M6

source sufficiency =
UNCHANGED
```

---

# 41. M6 acceptance criteria

M6 is COMPLETE only if:

```text
same-period comparison adapter implemented
where existing canonical inputs are compatible

OCF direct adapter implemented
where period/basis are known

PPE direct adapter implemented
where period/basis are known

safe OCF-PPE derived context implemented
only for compatible inputs

KR ambiguous OCF/PPE period fails closed

adapter idempotency PASS

financial_context emitted only from existing canonical evidence

new source mappings = 0

legacy packets remain valid

compact AI model input remains unchanged

Directional / Timing prompts unchanged

source sufficiency unchanged

Daily Delta semantics unchanged

focused/full tests PASS
ruff PASS
git diff --check PASS

all side-effect counts = 0
```

M6 does NOT require:

```text
debt/liquidity emitted
working capital emitted
non-operating effects emitted
Directional Core uses financial_context
model proof
real holdout
production readiness
```

---

# 42. Next-scope decision

If M6 passes, follow the frozen M4 order.

Default next scope:

```text
ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES
```

This phase should decide/implement the remaining higher-risk mappings:

```text
debt / liquidity
inventory / receivables / working capital
non-operating / financial-income effects
```

and any US/KR partial source mappings needed for the first three domains.

However, M6 must produce a prioritized backlog.

Possible next scopes:

## If existing canonical coverage is strong enough for all six domains except higher-risk mappings

```text
ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES
```

## If M6 discovers that existing three-domain coverage is too sparse to justify further adapter work

```text
FINANCIAL_SOURCE_MAPPING_COVERAGE_REVIEW
```

## If packet emission cannot be kept out of model semantic input

```text
MODEL_CONTEXT_FINANCIAL_FIELD_ACTIVATION_ARCHITECTURE_REVIEW
```

Do not activate Directional specificity yet.

---

# 43. Master workflow update

Update:

```text
docs/MASTER_WORKFLOW.md
```

at completion.

Expected:

```text
M5 COMPLETE
→
M6 COMPLETE
→
next package according to actual M6 backlog
```

Production readiness remains:

```text
NOT_READY
```

Monitoring remains paused.

---

# 44. Program-completion fields

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

same_period_adapter_status
ocf_adapter_status
ppe_adapter_status
simple_cash_conversion_status

us_same_period_support_status
kr_same_period_support_status
us_ocf_support_status
kr_ocf_support_status
us_ppe_support_status
kr_ppe_support_status

financial_context_emission_fixture_count
financial_context_emission_pass_count
period_ambiguity_block_count

adapter_idempotency_status
derived_identity_determinism_status

new_sec_mapping_count
new_opendart_mapping_count
new_provider_mapping_count

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

additional_source_mapping_backlog_count
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

# 45. Artifact integrity

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

# 46. Final task principle

M5 created the typed envelope.

M6 may now populate that envelope only from source evidence the system already knows how to represent safely.

The correct order is:

```text
existing canonical source evidence
→ bounded adapter validation
→ financial_context emission
→ prove no model-input leak
→ freeze
```

Not:

```text
add new accounting mappings at the same time
```

Not:

```text
let the model start using financial_context
```

Not:

```text
change source sufficiency
```

Not:

```text
guess KR cash-flow periods
```

Not:

```text
call OCF minus partial PPE "FCF"
```

And not:

```text
resume production monitoring
```

Activate the safe adapters first.
