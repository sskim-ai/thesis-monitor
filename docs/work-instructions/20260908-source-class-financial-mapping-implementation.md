# Thesis Monitor — Source-Class Financial Mapping Implementation

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-source-class-financial-mapping-implementation.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-source-class-financial-mapping-implementation-report.zip
```

Master-workflow phase:

```text
M8 — Source-Class Financial Mapping Implementation
```

This task begins only after M7 has completed.

M7 resolved:

```text
compatible prior-year fact projection
derived-period lineage projection
exact KR duration-period mapper capability
```

and left six backlog items.

M8 implements only the three lower-risk source-class / canonical-promotion gaps:

```text
1. hut_ppe_source_class_mapping
2. skhy_foreign_issuer_ocf_ppe_source_class_mapping
3. kr_opendart_canonical_source_promotion_with_exact_context
```

These names describe historical examples/gaps.

M8 must implement only generic reusable source-class behavior.

No ticker-specific production exception is allowed.

M8 must NOT implement:

```text
interest_bearing_debt_and_liquidity
inventory_receivables_working_capital
non_operating_financial_income_effects
```

Those remain separate higher-risk subpackages.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-financial-lineage-kr-period-projection-source-mapping-report.zip
```

Verified SHA-256:

```text
b9be904a744a2c226c93bcc4a4ffce4abe0b87f76bfb8470e1070207d286a2da
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

M7 artifact integrity independently reported:

```text
payload count = 35
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Latest M7 state:

```text
M1 = COMPLETE
M2 = COMPLETE
M3 = COMPLETE
M4 = COMPLETE
M5 = COMPLETE
M6 = COMPLETE
M7 = COMPLETE

status = M7_COMPLETE
production_readiness = NOT_READY

next_scope =
SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION
```

Reported M7 provenance:

```text
base_sha =
92e5111f35499f43dcfc4fe76238b0c3e4a2442b

work_instruction_commit =
6a303ebeedd275d8109e6babfcf5f725798542d1

implementation_commit =
9442f406b0deae433ad25f4961daa93e15695587

branch =
codex/20260908-financial-lineage-kr-period-projection-source-mapping
```

M7 `program-completion` recorded final/report SHA as:

```text
NOT_MEASURED
PRECOMMIT_ARTIFACT_FREEZE
```

At M8 start use actual repository HEAD as authority.

Record the actual M7 final/report state.

Do not classify the precommit-reporting convention as semantic drift.

---

# 2. M7 frozen facts

M7 measured:

```text
prior-year projected facts = 164
derived-lineage projected facts = 380

same-period comparison emissions = 164
OCF emissions = 224
PPE emissions = 191
simple cash-conversion emissions = 191
```

M7 eliminated archive-level denials caused only by recoverable lineage projection:

```text
derived_period_lineage_metadata_incomplete:
189 → 0

simple_cash_conversion_input_derivation_unproven:
87 → 0
```

No new derivations were invented.

M7 also proved:

```text
compact AI context changed = 0
Directional prompt changed = 0
Price-Timing prompt changed = 0
source-sufficiency semantics changed = 0
Daily Delta semantics changed = 0
```

Preserve all of these boundaries.

---

# 3. KR exact-period status frozen from M7

M7 implemented exact-context-only KR OCF/PPE period mapping capability.

Synthetic contract fixtures passed.

Real issuer coverage remained blocked:

```text
KR OCF:
resolved = 0
blocked = 7

KR PPE:
resolved = 0
blocked = 6
```

M7 explicitly did NOT claim universal KR support.

M8 may promote KR facts only where existing canonical/OpenDART/XBRL evidence contains the exact context needed.

Do not weaken the exact-period contract.

---

# 4. M8 primary question

M8 must answer:

```text
Are the remaining HUT/SKHY/KR gaps actually reusable source-class gaps?

If yes:
implement the generic mapping/promotion once.

If no:
do not create ticker-specific exceptions.
```

The task is successful even if one historical ticker remains unsupported because no safe generic source class exists.

Coverage is not allowed to override semantic safety.

---

# 5. User-approved operating constraints

## 5.1 Free/public data only

Do not add:

```text
paid provider
paid fallback
paid market-data entitlement
```

Use current repository/cache/fixtures only.

Required:

```text
provider_source_fetches = 0
```

## 5.2 No model calls

Required:

```text
model_calls_real = 0
model_calls_fictional = 0
model_calls_judge = 0
```

## 5.3 Existing monitoring remains paused

Observe the eight approved US/KR monitoring schedule paths at start/end.

If paused:

```text
scheduler mutation = 0
```

If one exact approved path unexpectedly resumed:

```text
pause only that exact path
record mutation
```

Do not resume monitoring automatically.

---

# 6. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Audit drift in:

```text
FinancialContext
M6 financial adapter
M7 lineage projection
SEC / foreign issuer source normalization
OpenDART XBRL / recovery paths
canonical fact promotion
compact AI context
source sufficiency
Daily Delta lifecycle
```

If unexplained semantic drift blocks a reliable baseline:

```text
STOP
UNEXPLAINED_M8_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 7. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement M8.

---

# 8. M8 source-class classification gate

Before code changes, classify each historical gap.

Allowed classifications:

```text
GENERIC_SOURCE_CLASS_CONFIRMED

GENERIC_SOURCE_CLASS_WITH_BOUNDED_VARIANT

TICKER_SPECIFIC_ONLY

SOURCE_EVIDENCE_INSUFFICIENT

ALREADY_SUPPORTED_AFTER_M7
```

For:

```text
HUT PPE
SKHY foreign-issuer OCF/PPE
KR OpenDART canonical promotion
```

produce evidence showing:

```text
source family
filing/document class
taxonomy/account concept class
period/context metadata
issuer/security identity behavior
normalization path
why rule is reusable or not reusable
```

Do not infer genericity from one ticker alone.

A generic class needs:

```text
at least one additional repository/cache/fixture example
or
a source-standard rule implemented independent of ticker identity
```

If neither exists:

```text
TICKER_SPECIFIC_ONLY
```

or:

```text
SOURCE_EVIDENCE_INSUFFICIENT
```

and do not implement a ticker exception.

---

# 9. No ticker symbol branching

Forbidden production logic:

```python
if ticker == "HUT":
    ...

if ticker == "SKHY":
    ...
```

or equivalent issuer-name/security-ID exceptions.

Required:

```text
ticker_specific_mapping_count = 0
```

Ticker symbols may appear only in:

```text
tests
diagnostic fixtures
historical gap reports
```

not mapping semantics.

---

# 10. Subpackage A — HUT PPE source-class mapping

## 10.1 Goal

Determine the generic source class behind the historical HUT PPE gap.

Do not assume the class in advance.

Possible dimensions to inspect:

```text
SEC registrant / foreign-private-issuer path
IFRS vs US-GAAP taxonomy
cash-flow PPE concept aliases
filing form class
companyfacts vs filing-XBRL source
currency/unit presentation
issuer/security normalization
```

Use actual repository evidence.

## 10.2 Implementation condition

Implement a mapping only if the historical HUT gap maps to a reusable source-standard concept/class.

Required generic rule properties:

```text
not keyed by ticker
not keyed by company name
bounded canonical metric
exact source lineage
duration period known
currency/unit known
entity/statement basis known
```

## 10.3 PPE scope

Only promote evidence that means:

```text
purchase/acquisition of property, plant and equipment
or an explicitly approved equivalent PPE cash outflow
```

Do not aggregate:

```text
intangibles
acquisitions
investments
leases
other investing cash flows
```

unless M4/M6 contract explicitly permits that metric.

Do not broaden PPE semantics to improve coverage.

## 10.4 If generic mapping is not proven

Record:

```text
HUT_GAP_DEFERRED_NO_TICKER_EXCEPTION
```

No failure of M8 overall if other subpackages pass.

---

# 11. Subpackage B — SKHY foreign-issuer OCF/PPE source-class mapping

## 11.1 Goal

Determine the reusable source class behind the historical SKHY foreign-issuer OCF/PPE gap.

Do not assume that US domestic-company CompanyFacts semantics apply unchanged.

Inspect actual source class dimensions such as:

```text
foreign private issuer
IFRS taxonomy
20-F / 6-K / foreign issuer filing class
depositary/ordinary security identity
issuer-vs-traded-security normalization
cash-flow statement concept class
financial currency
```

Only use dimensions actually present in repository/cache evidence.

## 11.2 Security basis safety

OCF/PPE are issuer financial statement facts.

They must attach to:

```text
issuer/entity financial scope
```

not be transformed using ADR ratio or traded-security price basis.

Do not mix:

```text
ADR/share denominator
ordinary-share basis
cash-flow financial amount
```

No per-share derivation in M8.

## 11.3 Generic mapping condition

Implement only when a source class can be defined independently of SKHY.

Examples of acceptable class logic:

```text
IFRS issuer cash-flow concept mapping
foreign-private-issuer filing-XBRL extraction
canonical issuer identity linking
```

if proven by repository evidence.

Do not use a one-off SKHY label alias without a source-standard basis.

## 11.4 If generic mapping is not proven

Record:

```text
SKHY_GAP_DEFERRED_NO_TICKER_EXCEPTION
```

---

# 12. Subpackage C — KR OpenDART canonical source promotion

## 12.1 Goal

Promote existing OpenDART/XBRL financial facts into the canonical fact pipeline only when exact context is proven.

M7 already supports an exact-context mapper.

M8 connects qualifying real canonical source rows to that mapper.

## 12.2 Required exact context

For OCF/PPE promotion require:

```text
taxonomy/account concept
reported amount
currency/unit
period_start
period_end
duration_days
context_ref
entity_identifier
statement_basis
report/filing identity
```

where current canonical contract requires them.

Do not use report title alone.

## 12.3 Exact source amount match

When linking a normalized/OpenDART row to an XBRL context, require a deterministic match using the frozen M7 contract.

If multiple XBRL contexts match the same:

```text
concept
amount
unit
basis
entity
```

and the correct duration context is ambiguous:

```text
do not promote
```

No "first match wins".

## 12.4 Report-label guessing remains forbidden

Forbidden:

```text
반기보고서 → Jan 1 to Jun 30
3분기보고서 → Jan 1 to Sep 30
사업보고서 → Jan 1 to Dec 31
```

unless the exact fiscal-period source metadata proves those dates.

Non-calendar issuers must remain safe.

---

# 13. KR real-issuer evidence target

M8 should attempt promotion against preserved real KR source/cache evidence.

Report:

```text
real KR OCF candidates
real KR OCF promoted
real KR OCF blocked by reason

real KR PPE candidates
real KR PPE promoted
real KR PPE blocked by reason
```

M8 does NOT require all 7/6 historical blocks to resolve.

Safe remaining blocks are acceptable.

Do not create synthetic rows to inflate real coverage.

Synthetic fixtures must remain separately labeled.

---

# 14. Canonical promotion vs raw mapping

M8 KR work should prefer:

```text
existing official source row
+
existing XBRL context
→ canonical promotion
```

rather than adding broad new account-name heuristics.

If the canonical account concept itself is absent:

```text
SOURCE_PRESENT_MAPPING_INCOMPLETE
```

and defer that concept mapping to a later bounded source mapping.

Do not silently add fuzzy Korean account-name matching.

---

# 15. Existing lineage contracts remain mandatory

Any newly promoted fact must flow through M7 lineage projection and M6 financial adapter.

Required:

```text
source fact
→ canonical fact
→ lineage projection
→ financial_context
```

Do not bypass those services with a separate one-off packet builder.

No duplicated source-to-packet path.

---

# 16. Period contract remains fail-closed

New source-class mappings may increase source coverage.

They may NOT weaken:

```text
period type
start/end
duration
currency/unit
entity
statement basis
attribution
```

requirements.

If source class supplies amount but not exact period:

```text
financial_context emission = blocked
```

No inferred fiscal periods.

---

# 17. Direct evidence only at mapping boundary

New source mappings/promotions should create:

```text
DIRECT_REPORTED
```

canonical financial facts.

Derived period/comparison/simple cash-conversion facts remain owned by existing M6/M7 derivation logic.

Do not create new derived formulas in M8.

Required:

```text
new_derivation_formula_count = 0
```

---

# 18. Duplicate source precedence

If the same economic fact is available from multiple existing free/public source paths:

define deterministic precedence consistent with current source architecture.

Do not double count.

Required report:

```text
duplicate_candidate_count
deduplicated_count
conflict_count
```

If two sources disagree materially and no canonical precedence resolves it:

```text
block promotion
record conflict
```

Do not average.

---

# 19. Source authority

Prefer:

```text
official filing/XBRL
official structured source
```

over inferred/derived secondary caches where both represent the same direct reported fact.

Do not replace exact official amount with a normalized value if the normalized value has lost basis/period provenance.

---

# 20. Market/source-class capability vs issuer coverage

Report separately:

```text
source-class adapter capability

historical archive coverage

real issuer coverage
```

Do not claim:

```text
foreign issuers supported
KR OCF supported
```

based solely on one passing fixture.

Use bounded statuses:

```text
SOURCE_CLASS_IMPLEMENTED
SOURCE_CLASS_PARTIAL
SOURCE_CLASS_BLOCKED
SOURCE_CLASS_DEFERRED
```

---

# 21. No higher-risk domains

M8 must keep zero emissions for:

```text
interest_bearing_debt_and_liquidity
inventory_receivables_working_capital
non_operating_financial_income_effects
```

Required:

```text
higher_risk_domain_emission_count = 0
```

No source mapping for them in M8.

---

# 22. Model semantic input remains dormant

M8 may increase packet `financial_context` coverage.

M8 must NOT change compact AI input.

For representative newly-supported source-class fixtures:

```text
pre-M8 compact AI context hash
=
post-M8 compact AI context hash
```

Required:

```text
compact_ai_context_changed_count = 0
```

If leakage occurs:

```text
STOP
M8_SCOPE_EXCEEDED_MODEL_INPUT_LEAK
```

Do not activate financial_context consumption.

---

# 23. Directional / Timing prompt no-change

Required:

```text
directional_prompt_change_count = 0
price_timing_prompt_change_count = 0
renderer_change_count = 0
ownership_semantic_change_count = 0
```

No model call.

---

# 24. Source sufficiency no-change

New financial source-class coverage must not change current model eligibility/source sufficiency in M8.

Required:

```text
source_sufficiency_semantic_change_count = 0
```

Before/after for representative fixtures:

```text
same sufficiency result
```

No universal/sector gate.

---

# 25. Daily Delta no-change

Newly promoted historical/baseline financial facts must not become today's Daily Delta.

Re-run M3/M7 lifecycle fixture:

```text
historical source promotion
→ baseline enrichment
→ NOT Daily Delta
```

Required:

```text
daily_delta_semantic_change_count = 0
```

---

# 26. Idempotency

Repeated source-class mapping / promotion must produce:

```text
same canonical fact IDs
same financial_context
no duplicate refs
same derivation results downstream
```

Required:

```text
source_mapping_idempotency = PASS
canonical_promotion_idempotency = PASS
adapter_idempotency = PASS
```

---

# 27. Historical packet compatibility

Existing packets without newly promoted facts remain:

```text
parseable
canonical hash unchanged
```

Do not rewrite historical artifacts.

Only newly rebuilt packet/source artifacts may reflect expanded source coverage.

---

# 28. Positive fixture matrix — source class

At minimum include:

```text
generic PPE source-class fixture matching historical HUT-type gap

second non-HUT fixture proving the same PPE class rule
OR source-standard rule proof independent of ticker

generic foreign-issuer OCF fixture matching historical SKHY-type gap

generic foreign-issuer PPE fixture matching historical SKHY-type gap

second foreign-issuer/source-standard proof where repository evidence exists

exact KR OCF XBRL context promotion

exact KR PPE XBRL context promotion

KR OCF/PPE exact-period simple cash-conversion downstream flow

idempotent repeated promotion

compact AI non-leak
```

Any synthetic fixture must be labeled separately from real source-support evidence.

---

# 29. Negative fixture matrix

At minimum:

```text
ticker-specific HUT branch rejected

ticker-specific SKHY branch rejected

PPE alias with wrong economic scope rejected

foreign issuer wrong entity/security identity rejected

foreign issuer currency/basis ambiguity rejected

ADR/share basis incorrectly mixed into financial fact rejected

KR report-label-only period rejected

KR multiple matching XBRL contexts rejected

KR amount mismatch rejected

KR statement-basis mismatch rejected

KR entity mismatch rejected

duplicate direct fact deduplicated

material source conflict blocked

higher-risk domain still not emitted
```

---

# 30. HUT / SKHY outcome reporting

For each historical named gap report only diagnostic outcome:

```text
historical_example = HUT
generic_classification = ...
generic_rule_id = ...
resolved_by_generic_rule = true/false

historical_example = SKHY
generic_classification = ...
generic_rule_id = ...
resolved_by_generic_rule = true/false
```

Do not encode names in production mapping.

---

# 31. KR real coverage accounting

Required pre/post:

```text
pre_M8_KR_OCF_real_resolved
post_M8_KR_OCF_real_resolved

pre_M8_KR_OCF_real_blocked
post_M8_KR_OCF_real_blocked

pre_M8_KR_PPE_real_resolved
post_M8_KR_PPE_real_resolved

pre_M8_KR_PPE_real_blocked
post_M8_KR_PPE_real_blocked
```

Include reason taxonomy for remaining blocks.

Do not interpret unresolved blocks as system failure if safety data is genuinely absent.

---

# 32. Mapping activation surface

Report exact code paths changed.

Preferred scope:

```text
generic source-class mapper(s)
canonical source promotion
issuer/source-class normalization
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

If higher-risk semantic change is required:

```text
STOP
M8_SCOPE_EXCEEDED
```

---

# 33. Existing source cache only

Allowed:

```text
repository fixtures
preserved official-source cache
SEC/XBRL cache
OpenDART/XBRL cache
historical reports
```

No network.

If there is not enough evidence to prove a generic mapping:

```text
defer
```

Do not fetch live data in M8.

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

Focused suite should include:

```text
M5 financial_context schema
M6 adapter
M7 lineage projection
new M8 source-class mapping
foreign issuer normalization
OpenDART exact-context promotion
compact AI non-leak
source sufficiency no-change
Daily Delta no-change
```

No model tests.

No provider network tests.

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

# 36. Required artifacts — provenance / classification

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m8-scope-freeze
04-m7-contract-reuse-proof

05-source-class-gap-classification
06-hut-historical-gap-diagnostic
07-skhy-historical-gap-diagnostic
08-kr-canonical-promotion-gap-diagnostic
```

---

# 37. Required artifacts — implementation

Produce:

```text
09-generic-ppe-source-class-contract
10-foreign-issuer-cash-flow-source-class-contract
11-kr-exact-context-canonical-promotion-contract
12-source-class-mapping-implementation-diff
13-source-class-activation-surface
14-source-precedence-and-dedup-contract
15-market-source-class-support-audit
```

If a generic class is not implemented:

```text
artifact must explain why
```

rather than fabricate a PASS.

---

# 38. Required artifacts — no-change proofs

Produce:

```text
16-compact-ai-context-non-leak-proof
17-directional-prompt-no-change-proof
18-price-timing-no-change-proof
19-source-sufficiency-no-change-proof
20-daily-delta-no-change-proof
21-historical-packet-compatibility
22-source-mapping-idempotency-proof
```

---

# 39. Required artifacts — fixtures/tests

Produce:

```text
23-positive-fixture-manifest
24-negative-fixture-manifest
25-pre-post-source-class-coverage
26-kr-real-coverage-pre-post
27-focused-test-results
28-full-test-results
29-ruff-and-diff-results
```

---

# 40. Required decision artifacts

Produce:

```text
30-remaining-source-mapping-backlog
31-higher-risk-domain-priority-decision
32-directional-specificity-activation-decision
33-source-sufficiency-no-change-decision
34-production-no-change
35-schedule-pause-observation
36-master-workflow-update
37-program-completion
```

Expected in M8:

```text
Directional specificity activation =
NOT_IN_M8

source sufficiency =
UNCHANGED
```

---

# 41. M8 acceptance criteria

M8 is COMPLETE if:

```text
all three historical source-class gaps are classified

generic mappings are implemented only where reusable source-class evidence exists

ticker-specific production branches = 0

KR exact-context promotion path is connected to real canonical sources where safe

remaining ambiguous KR facts remain fail-closed

new source taxonomy heuristics are not silently broadened

new derived formulas = 0

M6/M7 adapter and lineage contracts reused

compact AI context unchanged

Directional / Timing prompts unchanged

source sufficiency unchanged

Daily Delta unchanged

historical packet compatibility preserved

focused/full tests PASS
ruff PASS
git diff --check PASS

all production/model/provider side-effect counts = 0
```

M8 does NOT require:

```text
historical HUT resolved
historical SKHY resolved
all KR OCF/PPE blocks resolved
higher-risk domains
Directional model use of financial_context
model proof
real holdout
production readiness
```

A safe defer is preferable to a ticker exception.

---

# 42. Next-scope decision

After M8, measure the remaining backlog.

## Path A — higher-risk domains are now the main backlog

Default:

```text
HIGHER_RISK_FINANCIAL_DOMAIN_MAPPING_IMPLEMENTATION
```

But split the work into bounded subpackages.

Recommended order:

```text
1. interest-bearing debt / liquidity
2. inventory / receivables / working capital
3. non-operating / financial effects
```

unless M8 evidence supports another order.

## Path B — unresolved generic low-risk source-class gap remains

If broadly useful and safe:

```text
ADDITIONAL_SOURCE_CLASS_FINANCIAL_MAPPING_IMPLEMENTATION
```

## Path C — only ticker-specific low-risk gaps remain

Do not implement them.

If higher-risk domains are not yet required for Directional specificity:

```text
DIRECTIONAL_SPECIFICITY_READINESS_REVIEW
```

may be appropriate.

## Path D — financial-context source coverage is sufficient

Only if M8 proves coverage is adequate for the frozen M4 specificity contract:

```text
DIRECTIONAL_SPECIFICITY_CONTRACT_IMPLEMENTATION
```

Do not activate it automatically in M8.

---

# 43. Master workflow update

Update:

```text
docs/MASTER_WORKFLOW.md
```

Expected transition:

```text
M7 COMPLETE
→
M8 COMPLETE
→
measured next bounded financial-domain/source-class scope
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
m7_status
m8_status

hut_gap_classification
hut_generic_rule_status
hut_historical_gap_resolved

skhy_gap_classification
skhy_generic_rule_status
skhy_historical_gap_resolved

kr_exact_context_promotion_status

pre_kr_ocf_resolved_count
post_kr_ocf_resolved_count
pre_kr_ocf_blocked_count
post_kr_ocf_blocked_count

pre_kr_ppe_resolved_count
post_kr_ppe_resolved_count
pre_kr_ppe_blocked_count
post_kr_ppe_blocked_count

generic_source_class_mapping_count
ticker_specific_mapping_count

new_sec_taxonomy_mapping_count
new_opendart_fuzzy_mapping_count
new_derivation_formula_count

source_conflict_count
source_conflict_blocked_count
deduplicated_fact_count

financial_context_emission_delta
higher_risk_domain_emission_count

source_mapping_idempotency_status
canonical_promotion_idempotency_status
adapter_idempotency_status

compact_ai_context_changed_count
directional_prompt_change_count
price_timing_prompt_change_count
renderer_change_count

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
higher_risk_domain_backlog_count
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

Unmeasured fields must remain:

```text
NOT_MEASURED
```

---

# 45. Artifact integrity

Freeze:

```text
program completion
master workflow update
all reports
```

before creating final artifact index.

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

M7 repaired the missing lineage layer.

M8 should now classify and implement the remaining low-risk source gaps by reusable source class.

The correct logic is:

```text
historical gap
→ identify source class
→ prove rule is generic
→ implement once
→ exact provenance
→ existing M6/M7 pipeline
```

Not:

```text
if ticker == HUT
```

Not:

```text
if ticker == SKHY
```

Not:

```text
guess KR periods from report labels
```

Not:

```text
activate debt/working-capital/non-operating logic early
```

Not:

```text
let financial_context leak into model input
```

And not:

```text
resume production monitoring
```

Prefer a safe defer over a ticker-specific exception.
