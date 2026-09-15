# Thesis Monitor — Nonproduction Monitoring Bootstrap & Daily Delta Lifecycle Integration

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-nonproduction-monitoring-bootstrap-and-daily-delta-lifecycle-integration.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-nonproduction-monitoring-bootstrap-daily-delta-lifecycle-integration-report.zip
```

Master-workflow phase:

```text
M3 — Nonproduction Monitoring Bootstrap & Daily Delta Lifecycle Integration
```

This task begins only after M2 has completed.

M2 established that the existing production/shared service boundaries can be reused in nonproduction and that the next task is:

```text
NONPRODUCTION_MONITORING_BOOTSTRAP_AND_DAILY_DELTA_LIFECYCLE_INTEGRATION
```

The task is a **fixture-backed, nonproduction lifecycle integration task**.

It is NOT:

- a new real-model FIRST/A/B/C proof;
- a new holdout-selection task;
- a source/provider expansion task;
- a Directional Core reasoning rewrite;
- a message-copy rewrite;
- a production deployment;
- a monitoring-schedule resume task;
- a paid-data integration task.

The purpose is to prove that:

```text
explicit monitoring intent
→ stored versioned investment logic
→ onboarding evidence
→ absolute baseline
→ monitoring readiness
→ post-baseline Daily Delta
→ assessment / warning intent
→ file-only monitoring message
```

works without collapsing lifecycle semantics.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-nonproduction-integration-decision-message-quality-review-report.zip
```

Verified SHA-256:

```text
3ca97b17511605c3ead9da46292d1bf151782189ccddf25cd83d3fbcc0939422
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M2 artifact integrity:

```text
indexed payload count = 39
hash mismatch count = 0
size mismatch count = 0
secret scan failure count = 0
```

Latest result state:

```text
m1_status = COMPLETE
m2_status = COMPLETE

status = M2_COMPLETE
production_readiness = NOT_READY

next_scope =
NONPRODUCTION_MONITORING_BOOTSTRAP_AND_DAILY_DELTA_LIFECYCLE_INTEGRATION
```

Reported repository provenance:

```text
work_instruction_commit =
265d3866b5885458da89e01dfe994c426c7f342f

implementation_commit =
c20e1e00838b8d023755c75479e98ef727a5fa93

report_commit / final_head_sha =
2257a05f9a599aafd0f3120fb8ab62655bee875a
```

Do not assume current HEAD remains identical.

---

# 2. M2 results that are frozen inputs to M3

M2 verified:

```text
existing integration boundaries = 10
verified boundaries = 10

nonproduction adapter = PASS
lifecycle mode contract = PASS
idempotency / side-effect audit = PASS

focused tests = PASS: 383
full tests = PASS: 2759
ruff = PASS
git diff --check = PASS
```

M2 lifecycle contract:

```text
INITIAL_ABSOLUTE
- delta = NOT_APPLICABLE
- directional delta forbidden

MONITORING_BASELINE
- delta = NOT_APPLICABLE
- must not render as Daily Delta

DAILY_DELTA
- requires baseline_ref
- requires baseline_cutoff
- requires refresh_state
- missing refresh semantic = UNAVAILABLE
- price-only semantic = PRICE_ONLY_CONTEXT
```

Preserve these semantics.

---

# 3. Source→Core / decision-quality result — do not silently change in M3

M2 audited 8 source→Core domains and found:

```text
available_but_dropped_domain_count = 0
```

The preserved archive showed:

```text
single_quarter_vs_cumulative_period
→ ALREADY_SUPPLIED

valuation_denominator_current_readiness
→ ALREADY_SUPPLIED
```

Several domains were:

```text
NOT_AVAILABLE_IN_ARCHIVE
```

including:

```text
same_period_prior_year_comparison
operating_cash_flow
ppe_capex_simple_cash_conversion
debt_liquidity
inventory_receivables_working_capital
```

`non_operating_financial_income_effects` requires a separate design decision for many subjects.

M2 therefore froze:

```text
NO_BROAD_SOURCE_TO_CORE_CHANGE_IN_M2
```

M3 must preserve that decision.

Do NOT broaden Core evidence inputs while integrating lifecycle.

If M3 discovers a lifecycle-specific need for a currently absent domain:

```text
record it as a separate post-M3 design requirement
```

Do not silently add it.

---

# 4. Message-quality result — preserve, do not rewrite in M3

M2 traced:

```text
historical messages = 48
message traces = 48
repetition clusters = 50
```

Ownership/root-cause result:

```text
MODEL_OWNED_SUBSTANTIVE = 85
MODEL_CONTENT_WITH_RENDERER_WRAPPER = 33
RENDERER_INTRODUCED_OR_UNRESOLVED = 4

input_loss_repetition_count = 0
```

Conclusion:

```text
Most substantive repetition is preserved model content
or model content inside a stable renderer wrapper.

Sparse/equivalent source domains are a contributing constraint.

Random synonym variation is not a repair.
```

Renderer decision:

```text
PRESERVE_RENDERER_OWNERSHIP
```

M3 must not rewrite Directional reasoning or renderer prose to improve repetition scores.

The M2 message-specificity contract remains frozen.

---

# 5. User-approved operating constraints

## 5.1 Existing scheduled monitoring remains paused

The user explicitly requested the existing US/KR scheduled monitoring remain paused.

Latest M2 observation:

```text
observed paused schedule count = 8
scheduler mutation count = 0
unexpected active monitoring paths = []
```

At M3 start:

```text
observe only
```

If all eight approved paths remain paused:

```text
scheduler mutation = 0
```

If one exact approved path unexpectedly resumed:

```text
pause only that approved path
record actual mutation
```

Do not alter unrelated schedules.

Do not automatically resume monitoring at task completion.

## 5.2 Free/public data policy remains

Do not add:

```text
paid financial-data provider
paid market-data tier
paid fallback
```

M3 is offline/fixture-backed.

Required:

```text
provider source fetches = 0
```

## 5.3 No production side effects

Required:

```text
production DB mutation = 0
monitoring registration calls = 0
assessment persistence mutations = 0
warning mutations = 0
notification queue writes = 0
Telegram / production sends = 0

main merge = 0
deployments = 0
live V2 activation/change = 0
Night Futures change = 0
automatic monitoring resume = 0
```

---

# 6. Model-call policy

M3 is model-call free.

Required:

```text
real model calls = 0
fictional model calls = 0
judge model calls = 0
```

Use preserved or fixture-defined structured decision outputs when lifecycle integration requires decision state.

Do not invoke the model merely to make a Daily Delta fixture look realistic.

If a lifecycle question cannot be answered without new model emission evidence:

```text
record it as NOT_MEASURED and define a later validation scope
```

---

# 7. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Compare with the M2 final state.

Classify drift in:

```text
monitoring registration
onboarding evidence
baseline creation
readiness activation
daily monitor
assessment/warning persistence
shared decision contracts
structured renderer
notification/delivery
```

If unexplained semantic drift prevents a reliable M3 baseline:

```text
STOP
UNEXPLAINED_M3_BASELINE_DRIFT
```

Do not silently reset unrelated work.

---

# 8. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then modify the bounded nonproduction lifecycle-integration surface.

---

# 9. Reuse existing production/shared boundaries

M3 must reuse the existing service boundaries verified in M2.

## Registration

```text
app/services/monitoring_service.py
register_monitoring_item_with_continuation
```

## Onboarding evidence

```text
app/services/onboarding_evidence_service.py
build_initial_evidence
```

## Initial baseline

```text
app/services/onboarding_evidence_service.py
ensure_initial_baseline
```

## Onboarding readiness

```text
app/services/onboarding_reconciler_service.py
resume_onboarding_subject
```

## Daily monitoring

```text
app/services/daily_monitor_service.py
run_daily_monitor
```

## Shared decision ownership

```text
app/services/direction_timing_ownership_service.py
build_owned_evidence_packet
compose_decision
validate_ownership
```

## Structured validation / renderer

```text
app/services/structured_autonomy_shadow_service.py
validate_structured_autonomy_candidate
render_structured_autonomy_message
```

## Assessment persistence contract

```text
app/services/monitoring_service.py
record_assessment
```

## Notification boundary

```text
app/services/notification_service.py
queue_daily_stock_notification
dispatch_pending_notifications
```

M3 may use:

```text
test repositories
in-memory stores
mock side-effect ports
file-only delivery sinks
```

but must not create a second lifecycle engine.

---

# 10. M3 primary goal — complete one nonproduction lifecycle

Prove at least one full new-issuer lifecycle:

```text
EXPLICIT MONITORING INTENT
→ registration intent created
→ item stored as onboarding/pending
→ initial evidence prepared
→ absolute baseline created
→ bootstrap enrichment applied
→ source/readiness gate satisfied
→ item becomes monitoring-ready
→ later refreshed evidence arrives after baseline cutoff
→ Daily Delta produced
→ assessment / warning intent produced
→ file-only monitoring message rendered
```

and prove the same shared decision/message contract works for an already-existing monitored issuer fixture.

No production writes.

---

# 11. Required lifecycle state model

Use existing canonical states if present.

Do not invent a parallel production enum solely for tests.

The integration result must nevertheless make the following distinctions observable.

## 11.1 Registered but not ready

```text
registration exists
investment logic version exists or pending
onboarding incomplete

monitoring_ready = false
```

No daily monitoring should treat this subject as active-ready.

## 11.2 Baseline created but bootstrap incomplete

```text
absolute baseline exists
bootstrap source enrichment still incomplete

monitoring_ready = false
Daily Delta forbidden
```

## 11.3 Monitoring-ready

Required only after:

```text
valid baseline
required source/readiness condition
lifecycle cutoff established
```

## 11.4 Daily-evaluable

Requires:

```text
monitoring_ready = true
post-baseline refresh state is known
```

Do not infer daily evaluability solely from stored registration.

---

# 12. Explicit user intent gate

Integration tests must prove:

```text
Initial Analysis request only
→ no monitoring registration

read-only snapshot request
→ no monitoring registration

current-thesis review
→ no monitoring registration

explicit user "monitor/register/watch going forward"
→ registration intent allowed
```

No production Action/API call in M3.

Use service-level fixtures.

---

# 13. Registration idempotency

Repeated identical explicit registration intent must not create:

```text
duplicate monitoring item
duplicate investment-logic version
duplicate baseline
duplicate onboarding job
duplicate notification intent
```

If the investment logic itself changes:

```text
new version allowed
history preserved
```

Do not erase historical versions.

Use current repository contract.

---

# 14. Bootstrap enrichment is NOT Daily Delta

This is a hard M3 acceptance condition.

Create a fixture where:

```text
registration happens at T0
limited baseline evidence exists
bootstrap enrichment at T1 adds already-existing company facts
```

The bootstrap facts may improve the absolute baseline.

They must NOT create:

```text
strengthened
weakened
mixed
invalidation_candidate
```

as a "daily change" merely because they were absent from the initially stored baseline.

Required:

```text
bootstrap_daily_delta_record_count = 0
```

unless the canonical system records a separate onboarding audit record that is explicitly NOT a Daily Delta assessment.

---

# 15. Baseline cutoff semantics

The baseline must establish a cutoff/reference boundary.

Prove:

```text
fact/event effective before baseline cutoff
→ may enrich baseline/history
→ must not become new Daily Delta solely because it arrived late

fact/event effective after baseline cutoff
→ eligible for Daily Delta if validated/relevant
```

Use exact timestamps / effective dates in fixtures.

Do not use file arrival time alone when the canonical event has an earlier effective date.

If current repository contract uses a different canonical notion of cutoff:

```text
document and test that exact contract
```

---

# 16. Late-arriving historical evidence

Required test:

```text
baseline cutoff = T0

at T2 system receives an official filing/fact
whose effective/report event belongs before T0
```

Expected:

```text
historical/baseline enrichment allowed
Daily Delta strengthened/weakened = forbidden
```

Do not let delayed ingestion become a false investment change.

---

# 17. Fresh no-change vs missing refresh

These are different.

## 17.1 Fresh business/event refresh with no material change

When the canonical required refresh actually succeeds and no material thesis-changing event exists:

```text
business_thesis_change may be no_material_change
```

according to the existing contract.

## 17.2 Required refresh unavailable / failed

Expected:

```text
do not manufacture no_material_change
```

Use the repository's canonical:

```text
needs_review / unavailable / incomplete
```

or equivalent internal status.

M3 must discover and test the actual existing behavior.

Do not invent a new public enum if unnecessary.

---

# 18. Price-only / supply-only semantics

Create fixtures proving:

```text
price movement only
supply/positioning movement only
```

cannot create:

```text
strengthened
weakened
invalidation_candidate
invalidated
```

for business investment logic.

If a successful fresh fundamental refresh simultaneously confirms no business change:

```text
business thesis may remain no_material_change
```

while price/supply context is rendered separately.

If there is no valid fresh business refresh:

```text
do not use price-only movement to impersonate business no_material_change
```

Price-Timing remains a separate state.

---

# 19. Market expectation / valuation delta is separate from business thesis delta

Create nonproduction fixture coverage for:

```text
business thesis unchanged
but valuation becomes more expensive

business thesis unchanged
but market expectation becomes elevated

business thesis strengthened
but valuation also compresses/expands separately
```

Ensure internal assessment representation keeps:

```text
business_thesis_change
valuation_context
market expectation assessment
```

separate.

Do not let valuation alone rewrite business thesis state.

---

# 20. Warning lifecycle

Using test/in-memory persistence only, prove:

```text
valid source-backed warning evidence
→ warning intent may open

same warning repeated
→ no duplicate warning

warning condition resolved by validated evidence
→ lifecycle may resolve/close per current contract

price-only or supply-only movement
→ cannot create fundamental warning by itself
```

Do not mutate production warning tables.

---

# 21. Assessment persistence idempotency

Use test/in-memory persistence to prove:

```text
same ticker
same assessment date
same thesis version
same evidence generation
```

does not create duplicate daily assessments.

If current repository contract intentionally permits replacement/versioning:

```text
test the canonical behavior
```

Do not invent a new idempotency key without checking current code.

---

# 22. Daily Delta evidence lineage

Every Daily Delta fixture result must preserve:

```text
baseline reference
baseline cutoff
refresh status
source/evidence IDs
event/effective date
thesis version
assessment date
```

The test should be able to answer:

```text
what was known at baseline?
what is genuinely new?
why did the state change?
```

If lineage cannot answer this:

```text
M3 lifecycle integration is incomplete
```

---

# 23. Existing/new issuer contract equivalence

Prove two fixture paths:

## New issuer

```text
explicit registration
→ onboarding
→ baseline
→ ready
→ Daily Delta
```

## Existing monitored issuer

```text
already ready baseline
→ same Daily Delta evaluation boundary
```

Both must reach the same:

```text
shared business thesis state contract
Directional / Price-Timing absolute decision contract
renderer structure
```

The difference is lifecycle provenance, not a different BUY/HOLD/SELL engine.

---

# 24. Absolute decision vs Daily Delta

M3 must preserve both in the future monitoring message.

File-only monitoring message should distinguish:

```text
투자 논리 변화
= what changed since valid baseline

현재 절대 판단
= current Directional Core absolute state

신규 관찰자 / 보유자
= current fundamental perspective

Price-Timing
= only current price/timing context

다음 확인
= next evidence/checkpoints
```

A current absolute `HOLD` does not mean:

```text
Daily Delta = weakened
```

A current absolute `BUY` does not mean:

```text
Daily Delta = strengthened
```

These are different axes.

---

# 25. File-only monitoring message fixtures

Render to files only.

Required fixture scenarios:

```text
M3-01 registration pending / not ready
M3-02 baseline created / bootstrap incomplete
M3-03 monitoring-ready baseline
M3-04 fresh no-material-change
M3-05 strengthened by post-baseline validated evidence
M3-06 weakened by post-baseline validated evidence
M3-07 invalidation-candidate fixture
M3-08 missing refresh / unavailable
M3-09 price-only movement
M3-10 supply-only movement
M3-11 valuation-only change
M3-12 late-arriving pre-baseline evidence
```

Do not send any message.

Every output must be labeled:

```text
OFFLINE_NONPRODUCTION_DERIVATIVE
```

or equivalent.

---

# 26. Pending/not-ready messaging

If a newly registered subject is not yet monitoring-ready:

Do not render:

```text
today's thesis change = no_material_change
```

Instead the file-only output should communicate internally/for audit:

```text
monitoring baseline / source readiness is still being established
Daily Delta not yet applicable
```

Do not confuse this with a user-facing production copy approval.

M3 validates semantics, not final copy style.

---

# 27. M2 message-specificity contract remains frozen

Preserve:

```text
name the specific supplied anchor when evidence differs
separate confirmed facts from Unknown
state issuer-specific checkpoints when support exists
keep new-buyer and holder reasoning distinct
keep Price-Timing separate from fundamental direction
state Daily Delta only for post-baseline refreshed evidence
```

M3 should apply this contract to file-only lifecycle fixtures.

Do not attempt broad model-owned prose remediation.

No model calls.

---

# 28. Source-domain enrichment remains deferred

M2 found no target-domain source→Core drop in the preserved archive.

Several desired domains were not present in that archive.

M3 must not silently add:

```text
operating cash flow
capex
debt/liquidity
working capital
same-period YoY
non-operating financial effects
```

to Core inputs.

At task completion, if M3 lifecycle work demonstrates that a missing domain is required for decision quality:

```text
append it to the separate source-domain design backlog
```

with evidence.

Do not implement broad enrichment in M3.

---

# 29. Nonproduction side-effect firewall

The M3 integration harness must use explicit side-effect ports or test repositories.

Before every test execution, assert:

```text
production DB connection not used
production notification queue not used
Telegram sender not used
monitoring Action not used
provider clients not used
model clients not used
```

After the test suite, report actual invocation counts.

Required all zero outside test doubles.

---

# 30. Production scheduler pause observation

At task start and task end observe the eight approved monitoring schedule paths.

Do not change them unless an approved path unexpectedly becomes active.

Required final:

```text
automatic_monitoring_resume = 0
```

Monitoring remains paused even if M3 passes.

---

# 31. Minimal implementation allowed

M3 may implement generic, nonproduction integration plumbing required to connect existing modules, including:

```text
test/in-memory lifecycle repository
nonproduction onboarding-to-daily adapter
baseline/delta lineage object for test/shadow use
file-only monitoring-message adapter
side-effect firewall
fixture builders
```

Do not create a new production monitoring engine.

If a production service requires a small dependency-injection seam to be testable without side effects:

```text
a generic semantic-neutral seam is allowed
```

with focused/full regression.

If the required change alters:

```text
investment state meaning
source sufficiency
warning meaning
assessment meaning
message substantive reasoning
```

stop and classify it as a separately authorized semantic change.

---

# 32. Required focused test matrix

At minimum cover:

```text
explicit registration required
read-only analysis never registers

registration idempotent
version change preserves history

pending onboarding not monitoring-ready
baseline alone not ready if bootstrap incomplete

bootstrap enrichment not Daily Delta
bootstrap enrichment not strengthened

baseline cutoff enforced
late pre-baseline fact not Daily Delta

fresh no-change after successful refresh
missing refresh not no_material_change

price-only not thesis delta
supply-only not thesis delta
valuation-only not business thesis delta

post-baseline positive evidence can strengthen
post-baseline negative evidence can weaken
invalidation-candidate requires valid fundamental evidence

warning open idempotent
warning resolve idempotent

assessment persistence idempotent

new/existing issuer shared decision contract

file-only delivery no queue/send
Daily Delta message separates absolute decision and delta
```

---

# 33. Validation requirements

Run:

```text
focused pytest
full repository pytest
ruff
git diff --check
```

Required:

```text
all PASS
```

No model tests.

No live provider tests.

No production integration tests that perform side effects.

---

# 34. Required artifacts — lifecycle integration

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m3-scope-freeze
04-m2-contract-reuse-proof

05-m3-lifecycle-state-contract
06-registration-intent-integration
07-onboarding-evidence-integration
08-baseline-and-cutoff-integration
09-monitoring-readiness-integration
10-daily-delta-evaluation-integration

11-warning-lifecycle-integration
12-assessment-idempotency-integration
13-side-effect-firewall-audit
14-new-existing-contract-equivalence
```

---

# 35. Required artifacts — fixture results

Produce:

```text
15-lifecycle-fixture-manifest
16-bootstrap-not-delta-results
17-baseline-cutoff-results
18-late-arriving-evidence-results
19-refresh-state-results
20-price-supply-valuation-separation-results
21-warning-and-assessment-results
22-file-only-monitoring-message-results
23-daily-delta-lineage-audit
```

---

# 36. Required artifacts — decisions / next scope

Produce:

```text
24-m3-integration-gap-register
25-source-domain-backlog-update
26-required-next-semantic-change-decision
27-required-next-model-validation-scope
28-production-no-change
29-schedule-pause-observation
30-master-workflow-update
31-program-completion
```

Update canonical:

```text
docs/MASTER_WORKFLOW.md
```

at task completion.

Do not advance beyond M3 unless the M3 acceptance criteria actually pass.

---

# 37. M3 acceptance criteria

M3 is COMPLETE only if all are true:

```text
explicit registration semantics proven

new issuer:
registration → onboarding → baseline → ready → Daily Delta
proven nonproduction

existing issuer:
ready baseline → Daily Delta
proven nonproduction

bootstrap enrichment never appears as Daily Delta

baseline/effective-date cutoff semantics proven

missing refresh cannot become no_material_change

price/supply/valuation cannot rewrite business thesis delta by themselves

assessment/warning idempotency proven

new/existing issuer share the same decision/message contracts

file-only message separates:
Daily Delta
absolute decision
new-buyer/holder
Price-Timing

all side-effect counters = 0

focused/full tests PASS
ruff PASS
git diff --check PASS
```

If any hard lifecycle semantic fails:

```text
M3_BLOCKED
```

Do not progress to model validation or production review.

---

# 38. Post-M3 next-scope decision

M2 froze the ordered strategic plan:

```text
1. prove lifecycle bootstrap and Daily Delta in nonproduction
2. separately decide archive source-domain enrichment
3. then freeze any Core specificity change before a new model proof
```

Therefore, if M3 fully passes, the default next scope should NOT immediately be another 32-call holdout.

First produce a decision between:

## Path A — source-domain enrichment review required

If M3 + prior decision-quality evidence shows that missing financial domains materially limit the production-quality decision:

```text
next_scope =
SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_DESIGN_REVIEW
```

This should remain nonproduction/model-call-free until a bounded semantic contract is frozen.

## Path B — no source-domain change required, reasoning-specificity change remains required

```text
next_scope =
DIRECTIONAL_REASONING_SPECIFICITY_REMEDIATION_DESIGN
```

## Path C — no semantic decision/input change required

Only then may the next scope be:

```text
FINAL_FROZEN_MODEL_AND_REAL_HOLDOUT_VALIDATION
```

## Path D — M3 lifecycle integration itself is incomplete

```text
next_scope =
BOUNDED_M3_LIFECYCLE_INTEGRATION_REPAIR
```

Do not skip the lifecycle defect.

---

# 39. Production readiness

Even if M3 passes:

```text
production_readiness = NOT_READY
```

unless a separately authorized final model/real-holdout validation and production integration review have completed.

Do not merge/deploy.

Do not resume schedules.

---

# 40. Program-completion fields

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

registration_intent_gate_status
registration_idempotency_status
onboarding_pending_status
baseline_creation_status
bootstrap_readiness_status

bootstrap_not_daily_delta_status
baseline_cutoff_status
late_arriving_prebaseline_status

fresh_no_change_status
missing_refresh_status
price_only_status
supply_only_status
valuation_only_status

positive_daily_delta_status
negative_daily_delta_status
invalidation_candidate_status

warning_open_idempotency_status
warning_resolve_idempotency_status
assessment_idempotency_status

new_existing_contract_equivalence_status

file_only_message_status
daily_delta_lineage_status

fixture_count
fixture_pass_count
fixture_fail_count

side_effect_firewall_status

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

source_domain_backlog_count
semantic_change_required
new_model_validation_required
new_real_holdout_proof_required

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

# 41. Artifact integrity

Create the final artifact index only after:

```text
program completion
master workflow update
all final reports
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

# 42. Final task principle

M2 proved that the new decision/message contracts can connect to existing shared boundaries without creating a second decision engine.

M3 must now prove the actual monitoring lifecycle:

```text
explicit registration
→ baseline
→ bootstrap readiness
→ post-baseline Daily Delta
→ assessment/warning intent
→ file-only monitoring message
```

The essential safety distinction is:

```text
what the company is worth / current absolute decision
!=
what changed today
```

and:

```text
bootstrap evidence
!=
Daily Delta
```

and:

```text
missing refresh
!=
no_material_change
```

The correct next move is:

```text
prove lifecycle semantics with fixtures and zero side effects
→ freeze remaining semantic/input decisions
→ only then authorize the final model proof
```

Not:

```text
resume production schedules
```

Not:

```text
run another large holdout immediately
```

Not:

```text
change message wording by synonyms
```

Not:

```text
silently broaden Core financial inputs
```

And not:

```text
treat registration as monitoring readiness
```

Complete the lifecycle contract first.
