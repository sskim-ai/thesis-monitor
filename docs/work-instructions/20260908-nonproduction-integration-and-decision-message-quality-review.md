# Thesis Monitor — Nonproduction Integration & Decision / Message Quality Review

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-nonproduction-integration-and-decision-message-quality-review.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-nonproduction-integration-decision-message-quality-review-report.zip
```

Master-workflow phase:

```text
M2 — 기존 코드와 발송 없는 통합 / 판단·메시지 품질 결정
```

This task begins only after M1 has been completed and frozen.

The task is a **nonproduction integration + decision/message-quality root-cause and change-decision task**.

It is NOT:

- a new real-model FIRST/A/B/C proof;
- a new holdout-selection task;
- a source-universe expansion task;
- a production deployment task;
- a Monitoring Bootstrap production activation task;
- a scheduler-resume task;
- a broad Directional calibration retune;
- a paid-data integration task.

The primary purpose is:

```text
reuse the existing production lifecycle boundaries
+
connect them to the shared Directional / Price-Timing / structured-message contracts
in a nonproduction path
+
determine what must change in decision input/reasoning/message quality
before any final real-model proof or production integration
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-unknown-field-consistency-early-core-validation-offline-evidence-review-report.zip
```

Verified SHA-256:

```text
319e4ae9447e439ecb882e974146d2eaf6565f51147e859993e6ce956162c2e0
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

The latest result reports:

```text
status =
CODE_AND_OFFLINE_EVIDENCE_REVIEW_COMPLETE

production_readiness =
NOT_READY

next_scope =
NONPRODUCTION_INTEGRATION_AND_DECISION_MESSAGE_QUALITY_REVIEW
```

Repository state reported by the latest result:

```text
branch =
codex/20260908-unknown-field-consistency-early-core-validation-offline-review

final_head =
7eb9243f27ec0b15d7bb847c07c42299286f6892

final_tree =
2df7791a1275860c58f60308c54189aec6f8a590

implementation_commit =
df8ffb7858a9a1b5f30b77d72ca440121f142c15

report_commit =
7eb9243f27ec0b15d7bb847c07c42299286f6892

worktree_clean =
true
```

Do not assume current HEAD remains identical.

---

# 2. M1 completion state — preserve, do not redo

M1 completed:

```text
shared Unknown treatment/basis consistency helper
Core early acceptance validation using the same invariant
generic Core prompt field-placement clarification

focused regression:
329 passed

full repository pytest:
2746 passed

ruff:
PASS

git diff --check:
PASS
```

M1 historical audit coverage:

```text
Directional Core rows checked = 64 / 64
Price-Timing rows checked = 52 / 52
complete messages traced = 48 / 48

expected historical semantic failure:
NEON C Directional Core
unknown_nonnegative_has_directional_basis

new unexpected semantic failures:
0
```

Exposure registry:

```text
149 → 165
current cohort appended = 16
second-pass additional append = 0
```

Do not repeat M1 unless current repository drift affects the repaired Unknown invariant or early Core gate.

---

# 3. Important current limits

The latest master correctly keeps:

```text
model_emission_effectiveness = NOT_MEASURED
formal_current_cohort_stability = NOT_MEASURED
ownership_generalization = NOT_ESTABLISHED
production_readiness = NOT_READY
```

M1 was a code/offline review completion.

Do not promote it to:

```text
real-model behavior fixed
generalization PASS
production-ready
```

without new separately authorized evidence.

---

# 4. Existing monitoring remains paused

The user explicitly requested the existing US/KR scheduled monitoring remain paused.

Latest observation reported 8 approved paths paused:

```text
Thesis Monitor AI Review US Primary
Thesis Monitor AI Review US Backup
Thesis Monitor AI Review KR Primary
Thesis Monitor AI Review KR Backup

com.seungsoo.thesis-monitor.daily
com.seungsoo.thesis-monitor.kr-close
com.seungsoo.thesis-monitor.ai-review-fallback
com.seungsoo.thesis-monitor.ai-review-delivery-retry
```

At task start:

```text
observe only
```

If all remain paused:

```text
scheduler mutation = 0
```

If an exact approved path unexpectedly became active:

```text
pause only that approved path
record actual mutation count
```

Do not alter unrelated schedules.

Do not automatically resume monitoring at task completion.

---

# 5. User-approved external-data policy

Continue using existing free/public data routes only.

Do not:

```text
add paid financial-data APIs
upgrade to a paid market-data tier
create a paid fallback
build a new free-API entitlement management system
```

This task should not require provider fetches.

Use preserved/offline evidence and repository fixtures wherever possible.

Required default:

```text
provider_source_fetches = 0
```

If an unexpected integration test truly requires a live provider call:

```text
STOP
```

and report why the task design cannot remain offline.

Do not silently expand scope.

---

# 6. Model-call policy for M2

This task is **model-call free by default**.

Required:

```text
real model calls = 0
fictional model calls = 0
judge model calls = 0
```

The purpose is to make integration and change decisions from:

```text
existing code
existing tests
preserved source/evidence
preserved Core/Timing outputs
preserved composed states
preserved rendered messages
```

Do not run a new holdout or fictional canary in this task.

If a later decision requires new model emission evidence:

```text
record it as a separately authorized next scope
```

---

# 7. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Compare with the M1 final state.

Classify any current drift in:

```text
monitoring lifecycle
onboarding
decision packet construction
Directional / Timing ownership
structured validation / renderer
assessment persistence
notification / delivery
```

Do not silently reset unrelated work.

If unexplained semantic drift prevents a reliable M2 baseline:

```text
STOP
UNEXPLAINED_INTEGRATION_BASELINE_DRIFT
```

---

# 8. Work-instruction commit first

Commit this instruction before implementation.

Record:

```text
new_work_instruction_commit
```

Only then implement the bounded M2 nonproduction integration surface.

---

# 9. Existing integration boundary inventory — authoritative starting point

M1 verified 10 boundaries.

Preserve and use them rather than inventing parallel subsystems.

## 9.1 Explicit registration and versioned thesis

```text
app/services/monitoring_service.py
register_monitoring_item_with_continuation

caller:
app/api/routes_monitoring.py::register_monitoring

existing tests:
tests/test_monitoring.py
tests/test_onboarding_readiness_service.py
```

Required future semantics:

```text
explicit user intent
pending readiness allowed
version history preserved
```

## 9.2 Initial evidence preparation

```text
app/services/onboarding_evidence_service.py
build_initial_evidence

caller:
app/services/onboarding_reconciler_service.py::resume_onboarding_subject
```

Required distinction:

```text
source preparation != registration
```

## 9.3 Initial absolute baseline

```text
app/services/onboarding_evidence_service.py
ensure_initial_baseline
```

Required:

```text
initial baseline != Daily Delta
```

## 9.4 Bootstrap readiness / activation

```text
app/services/onboarding_reconciler_service.py
resume_onboarding_subject
```

Required:

```text
stored but incomplete
!=
monitoring-ready
```

## 9.5 Daily comparison / persistence

```text
app/services/daily_monitor_service.py
run_daily_monitor

caller:
app/jobs/monitor_daily.py::_run_market_job
```

Required:

```text
missing refresh
!=
no_material_change
```

## 9.6 Accepted V2 runtime

```text
app/jobs/accepted_decision_v2_runtime.py
prepare_context / validate_output / generate
```

Use only its already-accepted lifecycle/claim semantics where applicable.

Do not activate its model-generation path in M2.

## 9.7 Directional Core / Price-Timing ownership

```text
app/services/direction_timing_ownership_service.py
build_owned_evidence_packet
compose_decision
validate_ownership
```

This is the shared decision-contract boundary.

## 9.8 Structured validator / renderer

```text
app/services/structured_autonomy_shadow_service.py
validate_structured_autonomy_candidate
render_structured_autonomy_message
```

M1 Unknown invariant must remain shared with Core early validation.

## 9.9 Assessment / warning persistence

```text
app/services/monitoring_service.py
record_assessment
```

M2 must not write production DB records.

## 9.10 Queue / delivery / Telegram

```text
app/services/notification_service.py
queue_daily_stock_notification
dispatch_pending_notifications
```

M2 must not queue or send production notifications.

---

# 10. M2 core goal — one minimal nonproduction integration path

Design and implement the smallest nonproduction path that proves:

```text
lifecycle-qualified evidence
→ shared decision input
→ Directional / Timing / composed state
→ structured message
```

without:

```text
production DB mutation
monitoring registration
assessment persistence
warning mutation
notification queue
Telegram send
model invocation
provider source fetch
```

Preferred form:

```text
pure adapter / fixture-backed integration harness / shadow-only file output
```

Do not create another parallel production service.

Reuse production/shared modules where side effects can be disabled or replaced by in-memory/test repositories.

---

# 11. Lifecycle modes must remain explicit

The nonproduction integration path must distinguish at least:

```text
INITIAL_ABSOLUTE
MONITORING_BASELINE
DAILY_DELTA
```

These labels are internal test/integration concepts unless equivalent canonical names already exist.

Do not add a production enum solely because this work instruction uses these names.

Required semantics:

## INITIAL_ABSOLUTE

```text
current absolute business / valuation / ownership decision
no prior thesis delta required
must not claim strengthened/weakened
```

## MONITORING_BASELINE

```text
versioned stored investment logic / initial assessment baseline
bootstrap enrichment is allowed
must not be rendered as today's Daily Delta
```

## DAILY_DELTA

```text
only facts/events after the valid baseline/cutoff may change
strengthened / no_material_change / mixed / weakened / invalidation...
```

Do not allow an initial source-enrichment event to become:

```text
strengthened
```

merely because the baseline had not previously stored it.

---

# 12. Explicit registration must remain mandatory

Prove in nonproduction tests:

```text
Initial Analysis only
→ no monitoring registration

snapshot/read-only analysis
→ no monitoring registration

explicit user monitoring intent
→ registration path allowed

registration with incomplete onboarding
→ stored/pending
→ not monitoring-ready
```

Do not call the real `monitorStock` Action or production registration endpoint in this task.

Use service-level tests/fixtures.

---

# 13. Idempotency requirements

The nonproduction integration must prove:

```text
registration continuation is idempotent
baseline creation is idempotent
onboarding resume is idempotent
assessment generation is idempotent
delivery intent is idempotent
```

No duplicate:

```text
baseline
assessment
warning
notification
```

from repeated execution of the same lifecycle-qualified fixture.

Use:

```text
test DB
in-memory repository
mock persistence
```

according to existing project conventions.

No production DB.

---

# 14. Missing refresh / unavailable evidence semantics

Add integration tests proving:

```text
provider/source refresh missing
!=
no_material_change

price unavailable
!=
business thesis weakened

price-only change
!=
fundamental Daily Delta

bootstrap evidence acquisition
!=
daily strengthened

Unknown
!=
negative evidence
```

Preserve M1 Unknown treatment/basis invariant.

Do not convert missing evidence into an investment conclusion.

---

# 15. Existing and new issuers must use the same decision/message contract

Prove at the shared contract boundary that:

```text
new issuer INITIAL_ABSOLUTE
existing monitored issuer current absolute view
```

can both reach the same:

```text
Directional Core
Price-Timing
composed-state
renderer
```

contract without collapsing their lifecycle semantics.

The difference should be:

```text
lifecycle context / baseline / delta provenance
```

not a separate BUY/HOLD/SELL system.

Do not create a "new-issuer-only" renderer or duplicated ownership engine.

---

# 16. Source → Core information coverage audit

This is a decision task, not an automatic broad enrichment task.

M1 preserved:

```text
source_not_supplied_to_core_finding =
DEFERRED_INPUT_COVERAGE_DECISION
```

Now audit, using already-preserved evidence and repository code, which information is:

```text
A. available in raw/source evidence
B. preserved in normalized evidence
C. present in DecisionEvidencePacket
D. passed into build_owned_evidence_packet / Core context
E. visible in rendered reasoning
```

At minimum examine generic domains where the historical seven-stock review raised material differences:

```text
same-period prior-year comparison
single-quarter vs cumulative-period distinction
operating cash flow
capex / simple cash-conversion context
debt / liquidity
inventory / receivables / working-capital signals
non-operating / financial income effects
valuation denominator / current valuation readiness
```

Do NOT assume every domain must be supplied for every sector.

The output must be sector-aware and evidence-availability-aware.

---

# 17. Source-to-Core decision classifications

For every audited domain classify:

```text
ALREADY_SUPPLIED
AVAILABLE_BUT_DROPPED
AVAILABLE_BUT_INTENTIONALLY_EXCLUDED
NOT_AVAILABLE_IN_ARCHIVE
SECTOR_NOT_APPLICABLE
REQUIRES_SEPARATE_DESIGN_DECISION
```

For any:

```text
AVAILABLE_BUT_DROPPED
```

report:

```text
drop location
affected decision fields
risk of omission
generic fix candidate
required tests
```

Do not implement a broad input expansion in M2 unless it is both:

```text
generic
clearly already part of the canonical DecisionEvidencePacket contract
and does not require new investment semantics
```

Otherwise freeze a separate bounded change specification for the next scope.

---

# 18. Decision quality review — separate from stability

Use preserved Core outputs and source lineage to distinguish:

```text
stable output
from
sufficient investment reasoning
```

Do not treat repeated stability as proof of good analysis.

For the 64 preserved Core rows, sample all nontrivial categories or use complete programmatic lineage coverage where practical.

Audit:

```text
material anchor specificity
period/currentness handling
confirmed fact vs Unknown separation
cash-flow / balance-sheet omission where available
non-operating income attribution where material
business KPI specificity where present
valuation limitation language
new-buyer vs holder distinction
```

Output is a decision-quality specification.

No model rewrite in M2.

---

# 19. Message-quality root-cause review

M1 traced all 48 complete messages.

Preserved original advisory:

```text
FIRST repeated substantive spans = 13
A repeated substantive spans = 16
B repeated substantive spans = 21
```

M1 classified repeated findings primarily as:

```text
MODEL_OWNED_SUBSTANTIVE
MODEL_CONTENT_WITH_RENDERER_WRAPPER
small number of RENDERER_INTRODUCED_OR_UNRESOLVED
```

Do not solve this by random synonym variation.

For every repeated substantive cluster classify root cause:

```text
INPUT_CONTENT_EQUIVALENCE
INPUT_INFORMATION_LOSS
MODEL_GENERIC_REASONING
MODEL_GENERIC_REEVALUATION_LANGUAGE
RENDERER_TEMPLATE_REPETITION
SAFE_STRUCTURAL_HEADER
MIXED
```

Safe repeated headers such as:

```text
핵심 판단
신규 관찰자
보유자
재평가 조건
사업 논리 상태
판단 확신도
```

are not quality failures by themselves.

---

# 20. Message specificity criteria

Define pre-model acceptance criteria for later message work.

A high-quality issuer message should make clear, when evidence exists:

```text
what specifically supports the current absolute decision
what is actually Unknown
what would change the decision upward/downward
what the new-buyer view is
what the holder view is
what Price-Timing does or does not add
what Daily Delta changed today, if this is a monitoring message
```

The message should not be considered issuer-specific merely because:

```text
ticker/company name is different
```

The substantive anchors should differ where the evidence differs.

Do not require invented detail when evidence is genuinely similar or sparse.

---

# 21. Renderer ownership must remain intact

Do not move substantive investment reasoning into renderer templates merely to eliminate repetition.

Preserve:

```text
AI/shared decision output owns substantive reasoning
structured state + renderer own primary action wording and stable structure
```

A renderer may:

```text
format
order sections
render canonical labels
enforce action wording
```

but must not invent issuer-specific financial analysis.

If repeated substantive content originates upstream:

```text
fix upstream later
```

not by hiding it with renderer paraphrases.

---

# 22. File-only message comparison harness

Build a nonproduction/file-only comparison harness using preserved structured states and lifecycle fixtures.

It must:

```text
render messages to files
never queue notifications
never call Telegram
never write production assessments
never mutate warning state
```

Produce comparison views for at least:

```text
INITIAL_ABSOLUTE new issuer
MONITORING_BASELINE existing/new issuer
DAILY_DELTA no-material-change
DAILY_DELTA strengthened/weakened fixture
price unavailable / price-ready variants
Unknown / confirmed-risk variants
```

Use fixture-backed inputs.

No model calls.

---

# 23. Daily Delta message contract

Define the future monitoring message structure without activating it.

At minimum preserve separation:

```text
1. 투자 논리 변화
   strengthened / no_material_change / mixed / weakened / ...

2. 현재 절대 판단
   Directional Core direction / balance / HOLD lean

3. 신규 관찰자 / 보유자
   fundamental view

4. Price-Timing
   only where actual price/technical evidence exists

5. 다음 확인 항목
```

Do not let:

```text
Price-Timing WAIT
```

automatically become:

```text
business thesis weakened
```

Do not render a missing data refresh as:

```text
no_material_change
```

---

# 24. Candidate change-decision record

At the end of M2 create one decision record separating proposed changes into:

```text
A. LIFECYCLE_INTEGRATION_CHANGE
B. SOURCE_TO_CORE_INPUT_CHANGE
C. DIRECTIONAL_REASONING_CHANGE
D. MESSAGE/RENDERER_CHANGE
E. NO_CHANGE
F. DEFERRED_REQUIRES_USER_DECISION
```

For each proposed change include:

```text
root cause
evidence
affected modules
semantic risk
expected benefit
required tests
whether model revalidation will be required
whether new real holdout proof will be required
```

Do not implement categories B/C/D broadly in M2 merely because the review recommends them.

M2 should end with a frozen, bounded next-change plan.

---

# 25. Minimal implementation allowed in M2

M2 may implement only semantic-neutral integration plumbing where supported by the current shared contracts, such as:

```text
nonproduction adapter
fixture/lifecycle mode tagging
file-only rendering harness
lineage tracing
test-only repositories/mocks
offline comparison tooling
```

M2 may also fix a clearly erroneous integration bug discovered by these tests only if:

```text
the fix is generic
does not change investment meaning
does not alter production activation state
is covered by focused + full regression
```

If a fix changes:

```text
which investment evidence reaches Core
how Core interprets evidence
how substantive message reasoning is generated
```

freeze it as the next separately authorized bounded change instead of silently implementing it.

---

# 26. Production mutations forbidden

Required:

```text
main merge = 0
deployments = 0

production DB mutation = 0
monitoring registration calls = 0
production assessment persistence = 0
production warning mutation = 0

notification queue writes = 0
Telegram sends = 0

live V2 activation/change = 0
Night Futures change = 0

automatic monitoring resume = 0
```

Only the already-approved pause maintenance exception remains if an exact paused schedule unexpectedly reactivates.

---

# 27. M2 validation requirements

Focused tests must cover at least:

```text
initial absolute is not Daily Delta
baseline is not Daily Delta
explicit registration intent required
incomplete onboarding remains inactive
bootstrap enrichment is not strengthened
missing refresh is not no_material_change
price-only movement is not thesis delta
Unknown is not negative evidence
existing/new issuer share decision contract
baseline/assessment/delivery idempotency
file-only renderer has no queue/send side effects
```

Run:

```text
focused pytest
full repository pytest
ruff
git diff --check
```

No live-service/model/provider tests.

---

# 28. Required artifacts — integration

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m2-scope-freeze

04-existing-boundary-revalidation
05-nonproduction-integration-design
06-lifecycle-mode-contract
07-nonproduction-adapter-implementation
08-idempotency-and-side-effect-audit
09-file-only-rendering-harness
10-lifecycle-integration-test-results
```

---

# 29. Required artifacts — decision quality / input coverage

Produce:

```text
11-source-to-core-domain-coverage
12-source-to-core-drop-lineage
13-decision-quality-review
14-boundary-stability-context-note
15-input-coverage-change-decision
```

The historical boundary comparison remains descriptive:

```text
formal_current_cohort_stability = NOT_MEASURED
```

Do not create a fake final stability PASS from offline message work.

---

# 30. Required artifacts — message quality

Produce:

```text
16-message-repetition-root-cause
17-message-specificity-contract
18-renderer-vs-model-content-ownership-review
19-file-only-message-comparison
20-daily-delta-message-contract
21-message-quality-change-decision
```

Do not overwrite original 48 historical messages.

All new rendered messages must be labeled:

```text
OFFLINE_NONPRODUCTION_DERIVATIVE
```

or equivalent.

---

# 31. Required final artifacts

Produce:

```text
22-candidate-change-decision-record
23-required-next-model-validation-scope
24-production-no-change
25-schedule-pause-observation
26-master-workflow-update
27-program-completion
```

Update the canonical master workflow at task completion.

Expected phase transition:

```text
M1 COMPLETE
→
M2 COMPLETE or M2 BLOCKED_WITH_DECISION_REQUIRED
```

Do not advance to M3 merely because tests pass.

The next scope must be based on the actual M2 decision record.

---

# 32. Program-completion fields

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

unknown_consistency_regression_status
early_core_gate_status

nonproduction_adapter_status
lifecycle_mode_contract_status

integration_boundary_count
integration_boundary_verified_count

explicit_registration_test_status
baseline_not_delta_test_status
bootstrap_not_delta_test_status
missing_refresh_not_no_change_test_status
price_not_thesis_delta_test_status
idempotency_test_status

source_to_core_domains_audited
available_but_dropped_domain_count
requires_separate_input_design_count

decision_quality_review_status

historical_message_count
historical_message_trace_count
historical_repetition_cluster_count

model_owned_repetition_count
renderer_owned_repetition_count
input_loss_repetition_count

message_specificity_contract_status
file_only_message_comparison_status
daily_delta_message_contract_status

candidate_change_decision_counts

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

Anything unmeasured must be:

```text
NOT_MEASURED
```

not zero-filled PASS-like output.

---

# 33. Artifact integrity

Create the final artifact index only after:

```text
completion
master workflow
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

# 34. Decision matrix

## A. Existing production lifecycle cannot be reused without semantic collapse

```text
STOP
M2_BLOCKED_ARCHITECTURE_INTEGRATION
```

Do not create a parallel production stack automatically.

## B. Integration plumbing is clean but source→Core material evidence is being dropped

Do not silently broaden Core input in M2.

Produce:

```text
next_scope =
SOURCE_TO_CORE_EVIDENCE_COVERAGE_REPAIR
```

with a bounded domain list.

## C. Decision input is adequate but substantive repetition originates in model reasoning

Produce:

```text
next_scope =
DIRECTIONAL_REASONING_SPECIFICITY_REMEDIATION
```

No renderer paraphrase workaround.

## D. Repetition is predominantly renderer-introduced

Produce:

```text
next_scope =
RENDERER_MESSAGE_SPECIFICITY_REMEDIATION
```

while preserving substantive ownership.

## E. Multiple causes exist

Produce one ordered bounded plan:

```text
highest decision-quality risk first
→ message-only cleanup second
```

Do not combine all changes into one uncontrolled patch.

## F. Nonproduction integration and message/decision contracts are ready, but lifecycle bootstrap remains unproven

Produce:

```text
next_scope =
NONPRODUCTION_MONITORING_BOOTSTRAP_AND_DAILY_DELTA_LIFECYCLE_INTEGRATION
```

This corresponds to Master M3.

## G. M2 unexpectedly finds a semantic investment-rule defect

Stop and classify it.

Do not run a fresh real-model proof in M2.

---

# 35. Final task principle

M1 fixed one concrete Unknown-field contract defect and audited the preserved evidence.

M2 should now answer:

```text
Can the new decision/message contracts be connected to the existing monitoring lifecycle
without collapsing Initial / Baseline / Daily Delta semantics?

Why are messages substantively repetitive?

Is important source evidence already available but dropped before Core?

Which changes actually need to be made before the next model proof?
```

The correct next move is:

```text
connect and inspect offline
→ decide changes
→ freeze a bounded next change
```

Not:

```text
run another 32-call holdout immediately
```

Not:

```text
rewrite messages with synonyms
```

Not:

```text
activate production monitoring
```

Not:

```text
silently broaden investment inputs while reviewing prose
```

And not:

```text
resume schedules automatically
```

Use M2 to convert the remaining ambiguity into a precise, testable integration and decision-quality change plan.
