# Thesis Monitor — DecisionEvidencePacket Financial Context Domain Extension Implementation

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-decision-evidence-packet-financial-context-domain-extension-implementation.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-decision-evidence-packet-financial-context-domain-extension-implementation-report.zip
```

Master-workflow phase:

```text
M5 — DecisionEvidencePacket Financial Context Domain Extension Implementation
```

This task begins only after M4 has completed and frozen the six financial-domain contracts.

The current task implements only the first package in the M4 implementation order:

```text
B_PACKET_FINANCIAL_CONTEXT_EXTENSION
```

The task must add a typed, optional financial evidence envelope to `DecisionEvidenceRef` and hard validation around it.

The task is NOT:

- source producer activation;
- SEC/OpenDART mapping expansion;
- Directional Core prompt specificity implementation;
- source-sufficiency semantic change;
- model validation;
- real holdout proof;
- production deployment;
- scheduled-monitoring resume.

The schema extension must be additive and backward compatible.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-source-domain-enrichment-directional-specificity-design-review-report.zip
```

Verified SHA-256:

```text
4e575e3b2b6881025285865be4c996d335f587c880dabe27b4166c2322802dc7
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M4 result state:

```text
M1 = COMPLETE
M2 = COMPLETE
M3 = COMPLETE
M4 = COMPLETE

status = M4_COMPLETE
production_readiness = NOT_READY

next_scope =
DECISION_EVIDENCE_PACKET_DOMAIN_EXTENSION_IMPLEMENTATION
```

Reported repository provenance from the M4 artifact set:

```text
base_sha =
5990caa239f8778ae46670abddf30f68db1bb332

work_instruction_commit =
accb58f5463765605242a7a014aa8cc06a4d3db6

implementation_commit =
9fc4e0019df9861453bab36438e732aed345af4b

branch =
codex/20260908-source-domain-enrichment-directional-specificity-design-review
```

The user reported final/report commit:

```text
1f39271b6d7e161dc86bc11d71dd111b2b48937d
```

but the M4 `program-completion` artifact left `final_head_sha` / `report_commit` as `NOT_MEASURED`.

Therefore at task start:

```text
use actual repository HEAD as authority
record this historical reporting discrepancy
do not treat it as semantic drift by itself
```

---

# 2. M4 design decisions frozen for M5

M4 closed all six domain design contracts.

Domains:

```text
same_period_prior_year_comparison

operating_cash_flow

ppe_capex_simple_cash_conversion

debt_liquidity

inventory_receivables_working_capital

non_operating_financial_income_effects
```

M4 determined:

```text
schema extension required domains = 6
schema sufficient domains = 0

DecisionEvidencePacket extension =
ADDITIVE_OPTIONAL_FINANCIAL_CONTEXT_REQUIRED

universal source gate additions = 0

source sufficiency change required now = false
```

M5 must implement this additive schema layer only.

Do not change the M4 contracts.

---

# 3. M4 implementation order — M5 must respect it

Frozen order:

```text
1. B_PACKET_FINANCIAL_CONTEXT_EXTENSION       ← M5
2. A_EXISTING_CANONICAL_DOMAIN_ADAPTERS
3. A_ADDITIONAL_SOURCE_MAPPING_SUBPACKAGES
4. C_DIRECTIONAL_SPECIFICITY_CONTRACT
5. D_SECTOR_GATE_REVIEW_IF_COVERAGE_PROVES_REQUIRED
```

M5 must not jump ahead to packages 2–5.

The goal is:

```text
freeze typed packet representation first
```

before any producer or prompt starts using it.

---

# 4. User-approved operating constraints

## 4.1 Free/public data policy

No paid provider changes.

M5 is offline.

Required:

```text
provider_source_fetches = 0
```

## 4.2 Existing scheduled monitoring remains paused

The eight approved US/KR monitoring schedule paths remain paused.

At task start/end:

```text
observe only
```

If already paused:

```text
scheduler mutation = 0
```

If an exact approved path unexpectedly resumed:

```text
pause only that path
record actual mutation
```

Do not alter unrelated schedules.

Do not automatically resume monitoring after M5.

## 4.3 No model calls

Required:

```text
real model calls = 0
fictional model calls = 0
judge model calls = 0
```

---

# 5. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Compare with the actual M4 final state.

Classify drift in:

```text
DecisionEvidenceRef / packet schema
packet validators
source ingestion
source sufficiency
Directional / Timing prompt semantics
renderer
monitoring lifecycle
```

If unexplained semantic drift prevents a stable M5 baseline:

```text
STOP
UNEXPLAINED_M5_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 6. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement the additive packet extension.

---

# 7. Authoritative schema target

M4 froze this proposal:

```text
DecisionEvidenceRef.financial_context
```

Characteristics:

```text
optional
typed
additive
no existing packet rewrite
no producer activation in M5
```

Existing fields remain reusable:

```text
value
unit
source_ref
as_of
```

The new `financial_context` object must contain typed provenance/semantic metadata that the existing flat fields cannot safely encode together.

---

# 8. FinancialContext shape

Implement an optional typed object equivalent to the M4 frozen design.

Minimum fields:

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

Exact model/class names may follow repository conventions.

Do not change semantic meaning from M4.

---

# 9. Metric field

`metric` must be a canonical financial metric identifier.

Do not use free-form prose as the primary metric identity.

Design choices:

```text
string with bounded canonical vocabulary
or
existing project enum/identifier type
```

Prefer the current repository's extensibility conventions.

M5 must not prematurely hard-code only the six M4 domains if the metric vocabulary already has broader canonical identifiers.

However, validation must reject:

```text
empty metric
whitespace-only metric
unbounded arbitrary label if canonical IDs are required by current conventions
```

Freeze tests for representative metrics from all six M4 domains.

---

# 10. Period object

Implement typed period metadata.

Minimum shape:

```text
type =
QTD | YTD | FY | TTM | POINT_IN_TIME

start =
date | null

end =
date

duration_days =
integer | null
```

Validation rules:

## POINT_IN_TIME

```text
start = null
duration_days = null
end required
```

## QTD / YTD / FY / TTM

```text
start required
end required
end >= start
duration_days positive when supplied
```

If `duration_days` is supplied:

```text
must be consistent with start/end
```

using the repository's date arithmetic convention.

Do not infer period type from label text.

---

# 11. Currency / unit scale

`currency` must represent verified financial currency when applicable.

Do not copy:

```text
price.currency
```

into financial evidence automatically.

Allow:

```text
null
```

only for genuinely non-currency metrics where the contract permits it.

`unit_scale` must be explicit.

Examples:

```text
1
1000
1000000
```

or equivalent canonical representation.

Do not silently assume:

```text
KRW millions
USD units
```

from market alone.

---

# 12. Entity scope / statement basis / attribution basis

Implement explicit fields for:

```text
entity_scope
statement_basis
attribution_basis
```

M4 intended semantics:

```text
entity_scope =
issuer / consolidation scope

statement_basis =
official statement basis

attribution_basis =
total / parent / common / null as applicable
```

Use enums if repository conventions support safe closed vocabularies.

Do not overfit values if current source system requires extensible semantic identifiers.

At minimum validation must prevent empty/ambiguous strings.

These fields exist specifically to prevent:

```text
consolidated vs separate mixing

total net income vs parent/common attribution mixing

incompatible statement-basis arithmetic
```

---

# 13. Evidence status

Implement:

```text
DIRECT_REPORTED
DERIVED_SAFE
```

No third value in M5 unless the M4 contract or existing project schema requires one.

Rules:

## DIRECT_REPORTED

```text
derivation must be null / absent
```

## DERIVED_SAFE

```text
derivation required
derivation formula required
derivation input_source_refs required and non-empty
derivation version required
```

Do not permit a derived numeric result to masquerade as directly reported evidence.

---

# 14. Quality field

Implement bounded quality/provenance status sufficient for the M4 contract.

M4 language included:

```text
verified
partial
```

Use existing project quality enums where possible.

M5 must define the exact allowed values and tests.

Quality must not change:

```text
Confirmed Fact / Unknown semantics
```

by itself.

It describes the typed financial-context evidence quality.

---

# 15. Comparison object

Implement optional comparison metadata.

Minimum:

```text
kind =
prior_year_comparable
prior_year_end
none

compatibility_status =
PASS
(or canonical equivalent)

input_source_refs =
ordered references
```

Do not permit:

```text
prior_year_comparable
```

without compatible comparison lineage.

If `kind = none`:

```text
input_source_refs may be empty
```

according to the final bounded contract.

Do not invent comparison semantics in the packet.

The comparison object records an already-validated comparison contract.

---

# 16. Derivation object

Implement optional derivation metadata.

Minimum:

```text
formula
input_source_refs
version
```

Do not store executable code.

`formula` is a canonical derivation identifier or bounded descriptive expression according to repository conventions.

Prefer registered identifiers such as:

```text
qtd_from_compatible_ytd
ocf_ttm
ocf_less_ppe_capex
interest_bearing_debt_total
net_debt
balance_absolute_delta
verified_non_operating_component_sum
```

M5 does NOT implement those derivations.

It only creates a safe place to record them later.

---

# 17. Limitations

Implement a bounded list of limitations.

Examples:

```text
growth_vs_maintenance_capex_unknown

trade_ar_scope_unavailable

financial_sector_interpretation_caution

partial_debt_component_coverage
```

Do not use limitations as a free-form substitute for missing required typed fields.

Validation should:

```text
reject empty strings
deduplicate if current conventions prefer
preserve deterministic serialization
```

---

# 18. Backward compatibility — hard M5 acceptance gate

All existing `DecisionEvidenceRef` payloads without `financial_context` must remain valid and serialize compatibly.

Required:

```text
legacy packet parse = PASS
legacy packet roundtrip = PASS
legacy packet JSON schema compatibility = PASS
existing tests unchanged except intentional additions
```

No migration that rewrites all historical packet files.

`financial_context` must default to:

```text
null / absent
```

according to existing serialization conventions.

---

# 19. No producer activation

M5 must NOT populate `financial_context` in production source-building paths.

Required:

```text
production_financial_context_emission_count = 0
```

unless tests explicitly construct fixture values.

No changes in:

```text
SEC parser output producers
OpenDART parser output producers
coldstart enrichment producers
monitoring onboarding producers
```

that cause live packet emission.

The schema must be ready before the producers are activated in later packages.

---

# 20. No prompt / model activation

M5 must NOT modify:

```text
Directional Core prompt
Price-Timing prompt
renderer prompt/content
model schema expected by external model calls
```

unless the packet JSON schema is automatically embedded in a non-executed development representation and the change is purely additive.

Required:

```text
directional_prompt_change = 0
price_timing_prompt_change = 0
model_calls = 0
```

Do not test the new field with a model.

---

# 21. No source-sufficiency change

M4 explicitly decided:

```text
source_sufficiency_change_required_now = false
universal_gate_added_count = 0
```

Preserve this.

The existence or absence of `financial_context` must not change source sufficiency in M5.

Required:

```text
source_sufficiency_semantic_change = 0
```

Debt/liquidity sector-conditional gating remains a future candidate decision only.

---

# 22. No Directional semantic change

Do not change how Core interprets:

```text
cash flow
capex
debt
working capital
non-operating effects
```

because those inputs are not activated yet.

Required:

```text
directional_semantic_change = 0
```

M4's frozen Directional specificity design remains documentation only until its later implementation package.

---

# 23. Typed validation — direct evidence

Create fixture tests for DIRECT_REPORTED evidence across the six domains.

At minimum include:

```text
same-period comparable direct current value

official OCF YTD direct value

PPE purchase direct point/duration evidence as appropriate

cash point-in-time direct value

inventory point-in-time direct value

financial-income component direct value
```

The fixture should prove:

```text
period
currency
basis
source
direct status
```

can be represented together.

No live data.

---

# 24. Typed validation — derived evidence

Create fixture tests for safe DERIVED_SAFE metadata.

At minimum:

```text
same_period_absolute_delta

qtd_from_compatible_ytd

ocf_ttm

ocf_less_ppe_capex

interest_bearing_debt_total

net_debt

balance_absolute_delta

verified_non_operating_component_sum
```

M5 does not compute these values from financial sources.

Fixtures provide:

```text
value
input refs
formula ID
version
typed financial context
```

to test schema/validation only.

---

# 25. Negative validation fixtures

Required failure fixtures include:

```text
DERIVED_SAFE without derivation

DIRECT_REPORTED with derivation attached

duration period without start

POINT_IN_TIME with incompatible duration fields

end before start

duration_days inconsistent with dates

comparison marked prior_year_comparable without comparison refs

empty metric

missing financial currency for currency-denominated metric where required

invalid unit_scale

empty derivation input refs

empty limitation string

duplicate/incompatible source reference where current validator disallows

unknown evidence_status

invalid period type

ambiguous attribution basis if closed enum is implemented
```

Fail closed.

---

# 26. Domain-specific negative controls

Even though M5 is schema-only, add validation/contract tests that protect high-risk M4 decisions.

At minimum:

## Debt

```text
metric = total_liabilities
```

must NOT be allowed to self-identify as:

```text
interest_bearing_debt_total
```

through metadata alone.

If this cannot be enforced at generic schema level without metric registry semantics:

```text
record as producer/adapter validation responsibility
```

and add a future contract test placeholder.

Do not invent a schema-level accounting engine.

## OCF / PPE

Do not allow:

```text
OCF YTD
+
PPE FY
```

to be represented as one derived `ocf_less_ppe_capex` context unless fixture marks period compatibility PASS under the future adapter contract.

Again, if this belongs at adapter validation rather than generic schema validation:

```text
separate the responsibility explicitly
```

M5 should not overstuff the schema validator with source-domain business logic.

---

# 27. Schema-responsibility boundary

Produce an explicit responsibility matrix:

```text
generic schema validator

domain adapter validator

source parser

Directional validator
```

For each validation rule decide ownership.

Examples:

## Generic schema validator owns

```text
period structure
required derivation metadata
allowed enum values
non-empty refs
basic internal consistency
```

## Domain adapter validator owns

```text
same semantic field compatibility
period comparability
debt component completeness
financial-sector applicability
trade AR vs broad receivable semantics
non-operating attribution completeness
```

## Directional validator owns later

```text
claim/evidence consistency
missing-data nonnegative behavior
anchor independence/specificity
```

Do not collapse all responsibilities into one validator.

---

# 28. Deterministic serialization / hashing

The new optional object must not destabilize packet hashes for legacy packets that do not contain it.

Required:

```text
legacy canonical serialization unchanged
legacy packet hash unchanged
```

for representative archived fixtures.

For packets that do contain `financial_context`:

```text
serialization deterministic
field ordering follows project conventions
same semantic object produces same canonical hash
```

Add tests.

---

# 29. JSON schema / OpenAPI compatibility

If DecisionEvidenceRef participates in:

```text
Pydantic JSON schema
OpenAPI
Action schema
stored artifact schema
```

audit each affected surface.

M5 must determine:

```text
public Action schema exposed?
internal packet only?
```

Do not accidentally expose a large new field through a public API without recording it.

If the public schema changes automatically due the model:

```text
record it
verify additive optional backward compatibility
```

No API operation IDs may change.

No required-field change.

---

# 30. Historical artifact compatibility

Use archived packet fixtures to prove:

```text
M1/M2/M3/M4 historical packet artifacts still parse
```

Do not rewrite archives.

Required report:

```text
historical_fixture_count
historical_parse_pass_count
historical_hash_unchanged_count
```

If canonical hashing intentionally ignores missing optional fields, prove it.

If hash changes despite absent field:

```text
STOP
BACKWARD_COMPATIBILITY_HASH_DRIFT
```

---

# 31. Security / secret-safety

`financial_context` must never become a place to store:

```text
API keys
raw provider authorization metadata
secret headers
private tokens
```

Source references may contain only existing safe reference identifiers.

Run secret scan on fixtures/artifacts.

---

# 32. Implementation scope

Preferred affected production-code surface:

```text
DecisionEvidenceRef model
new FinancialContext nested model(s)
generic validators
canonical schema / serialization helpers
tests
```

Avoid modifying:

```text
source producer services
Directional Core prompt service
Price-Timing
renderer
monitoring lifecycle
notification pipeline
```

If implementation requires those surfaces:

```text
STOP
M5_SCOPE_EXCEEDED
```

unless the change is purely type import / compatibility plumbing with no semantic behavior.

---

# 33. Required focused tests

At minimum cover:

```text
legacy DecisionEvidenceRef without financial_context

all six domain representative typed contexts

DIRECT_REPORTED

DERIVED_SAFE

all period types

comparison object

derivation object

limitations

backward-compatible serialization

legacy hash stability

new typed-context deterministic hash

JSON schema optionality

nested validation negatives

historical archived fixtures
```

Also rerun all existing decision packet / ownership / onboarding integration tests impacted by the model change.

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

No:

```text
model tests
provider fetches
production DB tests with real connection
production sends
```

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

# 36. Required artifacts — provenance / scope

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m5-scope-freeze
04-m4-design-reuse-proof
05-m5-schema-responsibility-matrix
```

---

# 37. Required artifacts — implementation

Produce:

```text
06-decision-evidence-ref-before-after
07-financial-context-model-contract
08-financial-context-json-schema
09-financial-context-validator-contract
10-serialization-and-hash-compatibility
11-public-internal-schema-surface-audit
12-historical-artifact-compatibility
```

---

# 38. Required artifacts — tests

Produce:

```text
13-positive-fixture-manifest
14-negative-fixture-manifest
15-domain-specific-negative-controls
16-focused-test-results
17-full-test-results
18-ruff-and-diff-results
```

---

# 39. Required decision artifacts

Produce:

```text
19-source-producer-activation-decision
20-directional-prompt-activation-decision
21-source-sufficiency-no-change-proof
22-production-no-change
23-schedule-pause-observation
24-master-workflow-update
25-program-completion
```

Expected decisions:

```text
source producer activation =
NOT_IN_M5

Directional prompt activation =
NOT_IN_M5

source sufficiency =
UNCHANGED
```

---

# 40. M5 acceptance criteria

M5 is COMPLETE only if:

```text
financial_context is additive + optional

all legacy packets remain valid

legacy packet canonical hashes remain unchanged
where financial_context is absent

all six M4 domains can be represented safely

DIRECT_REPORTED / DERIVED_SAFE distinction is enforced

period / currency / entity / statement / attribution basis are typed

comparison / derivation lineage is representable

generic validation fails closed on malformed context

validation responsibility boundaries are explicit

no source producer emits the field yet

no Directional prompt consumes the field yet

source sufficiency semantics unchanged

focused/full tests PASS

ruff PASS

git diff --check PASS

all side-effect counts = 0
```

M5 does NOT require:

```text
financial domains populated from real sources
model reasoning changed
model proof
real holdout
production readiness
```

---

# 41. Next-scope decision

If M5 passes, default next scope follows the frozen M4 order:

```text
EXISTING_CANONICAL_FINANCIAL_DOMAIN_ADAPTER_IMPLEMENTATION
```

This corresponds primarily to:

```text
same-period comparison
existing official operating cash flow
existing PPE capex / simple cash-conversion facts
```

before higher-risk source mapping subpackages.

Do not jump directly to the Directional prompt.

If M5 finds the packet schema cannot safely represent the design without a larger incompatible API/storage migration:

```text
next_scope =
DECISION_EVIDENCE_PACKET_DOMAIN_EXTENSION_ARCHITECTURE_REVIEW
```

Do not force a risky migration.

---

# 42. Master workflow update

Update:

```text
docs/MASTER_WORKFLOW.md
```

at completion.

Expected phase transition:

```text
M4 COMPLETE
→
M5 COMPLETE
→
next:
EXISTING_CANONICAL_FINANCIAL_DOMAIN_ADAPTER_IMPLEMENTATION
```

or the actual blocker if M5 fails.

Production readiness remains:

```text
NOT_READY
```

---

# 43. Program-completion fields

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

financial_context_field_added
financial_context_optional

financial_context_period_type_status
financial_context_currency_status
financial_context_basis_status
financial_context_evidence_status_status
financial_context_comparison_status
financial_context_derivation_status
financial_context_limitations_status

schema_extension_domain_count
schema_extension_domain_representable_count

legacy_fixture_count
legacy_parse_pass_count
legacy_hash_unchanged_count

positive_fixture_count
positive_fixture_pass_count
negative_fixture_count
negative_fixture_rejected_count

direct_reported_validation_status
derived_safe_validation_status

generic_schema_rule_count
domain_adapter_rule_count
directional_future_rule_count

public_schema_changed
public_schema_backward_compatible

source_producer_activation_count
directional_prompt_change_count
price_timing_prompt_change_count
source_sufficiency_semantic_change_count

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

# 44. Artifact integrity

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

# 45. Final task principle

M4 already answered the semantic design question.

M5 must now create the safe typed envelope before any source producer or model starts using the new evidence.

The correct order is:

```text
schema representation
→ validation
→ backward compatibility
→ freeze
```

Not:

```text
start populating real OCF/debt/inventory immediately
```

Not:

```text
rewrite the Directional prompt
```

Not:

```text
make the new fields required for source sufficiency
```

Not:

```text
run a new holdout
```

And not:

```text
change production monitoring
```

Build the additive packet contract first.
