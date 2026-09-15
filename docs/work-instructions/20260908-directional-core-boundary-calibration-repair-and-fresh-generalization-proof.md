# Thesis Monitor — Directional Core Boundary Calibration Repair & Fresh Generalization Proof

## 0. Task identity

Suggested work-instruction filename:

```text
20260908-directional-core-boundary-calibration-repair-and-fresh-generalization-proof.md
```

Suggested result bundle:

```text
thesis-monitor-20260908-directional-core-boundary-calibration-repair-fresh-generalization-proof-report.zip
```

This is a **generic Directional Core boundary-calibration architecture repair + fresh unseen generalization proof task**.

The previous task successfully completed all 32 planned real model contexts:

```text
FIRST  = 16/16 issuers
A      = 16/16 issuers
B      = 16/16 issuers
C      = 16/16 issuers

attempted_real_contexts = 32
successful_real_contexts = 32
failed_real_contexts = 0

distinct_real_invocation_count = 32
distinct_real_namespace_count = 32
distinct_real_workdir_count = 32
distinct_real_session_count = 32

namespace_collision_count = 0
timeout_count = 0
capacity_failure_count = 0
orphan_count = 0
wrapper_retry_count = 0
```

All measured run-level ownership, renderer and hard-safety gates passed.

The remaining blocker is:

```text
Directional Core repeated-run stability
```

not transport or source preparation.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260908-runtime-namespace-isolation-repair-fresh-holdout-proof-report.zip
```

Verified SHA-256:

```text
5ade7e8d06c1ae41343f555ae65ff4979ac94d4f1bcf0d94bda8701e4bd5e8c5
```

Recompute this checksum at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest bundle integrity independently verified:

```text
zip members = 2166
indexed payloads = 2165
missing indexed files = 0
hash mismatches = 0
size mismatches = 0
```

The artifact index intentionally excludes only itself.

---

# 2. Latest proof state — what is already proven

## 2.1 Runtime namespace isolation repair succeeded

Latest measured state:

```text
runtime_namespace_root_cause =
RUN_STAGE_ONLY_NAMESPACE_DERIVATION_OMITTED_INVOCATION_AND_BATCH

runtime_namespace_repair_applied = 1

namespace_preflight_planned_context_count = 32
namespace_preflight_unique_invocation_count = 32
namespace_preflight_unique_namespace_count = 32
namespace_preflight_unique_workdir_count = 32
namespace_preflight_status = PASS

real distinct invocation count = 32
real distinct namespace count = 32
real distinct working-directory count = 32
real distinct session count = 32
namespace collision count = 0
```

Do not reopen namespace isolation unless current repository evidence directly contradicts this.

## 2.2 All four real runs completed

Fresh cohort:

```text
US:
WYNN
DOX
NWS
ASTI

KR:
064850
053270
078860
145720
199730
065510
396470
299900
020180
122310
417200
023910
```

Fresh source generation:

```text
20260907-fresh-issuer-source-20260907T181651Z-c5cb0cee45e8
```

Fresh source lock:

```text
d66f7425646512e1eb6916b61912e52660ce3fc2449fd9d6af59e5e3dd15210b
```

This cohort is now fully exposed and retired:

```text
exposure_state = FULLY_EXPOSED
retirement_state = RETIRED_AFTER_EVALUATION
future_unseen_reuse_allowed = 0
```

Do not reuse it as an unseen proof cohort.

---

# 3. Ownership / renderer / hard-safety result

For FIRST, A, B and C:

```text
ownership gate = PASS
renderer gate = PASS
hard-safety gate = PASS
```

Ownership generalization invariants remained:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0

PRICE_TIMING_NEW_BUYER_UPGRADE = 0
PRICE_ONLY_HOLDER_REDUCE = 0
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0

DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
```

The ownership proof artifact reports:

```text
status = PASS
```

but the overall generalization verdict remains:

```text
NOT_ESTABLISHED
```

because Directional Core repeated-run stability failed.

Do not modify Price-Timing or ownership boundaries merely because Directional Core stability failed.

---

# 4. Current stability result

Directional Core:

```text
STABLE                = 4
BOUNDARY_UNCERTAINTY  = 4
UNSTABLE              = 8

status = REVIEW

stop_reason =
DIRECTIONAL_CORE_STABILITY_UNSTABLE_8_OF_16

readiness =
NOT_READY_DIRECTIONAL_CORE_STABILITY
```

Price-Timing:

```text
STABLE                = 8
BOUNDARY_UNCERTAINTY  = 8
UNSTABLE              = 0

status = PASS
```

The next architecture work must therefore focus on Directional Core calibration.

---

# 5. Exact unstable Directional Core pattern

The eight subjects classified UNSTABLE were:

```text
NWS
064850
053270
145720
396470
020180
122310
023910
```

Their A/B/C values were:

```text
NWS
A BUY  6.0:4.0
B HOLD 5.5:4.5 BUY_LEAN
C BUY  6.0:4.0

064850
A HOLD 5.5:4.5 BUY_LEAN
B HOLD 5.5:4.5 BUY_LEAN
C BUY  6.0:4.0

053270
A HOLD 5.5:4.5 BUY_LEAN
B HOLD 5.5:4.5 BUY_LEAN
C BUY  6.0:4.0

145720
A HOLD 5.5:4.5 BUY_LEAN
B HOLD 5.5:4.5 BUY_LEAN
C BUY  6.0:4.0

396470
A HOLD 5.5:4.5 BUY_LEAN
B HOLD 5.5:4.5 BUY_LEAN
C BUY  6.0:4.0

020180
A SELL 4.0:6.0
B HOLD 4.5:5.5 SELL_LEAN
C SELL 4.0:6.0

122310
A BUY  6.0:4.0
B HOLD 5.5:4.5 BUY_LEAN
C BUY  6.0:4.0

023910
A BUY  6.5:3.5
B HOLD 5.5:4.5 BUY_LEAN
C BUY  6.0:4.0
```

No unstable subject exhibited a direct:

```text
BUY ↔ SELL
```

reversal.

Most instability is a one-half-point crossing of the frozen direction threshold.

This is the primary architecture question.

---

# 6. Important qualitative observation

For the unstable subjects, preserved outputs show that the underlying investment interpretation often remained materially similar while the adjacent balance bucket moved.

Examples include:

```text
064850 / 053270 / 145720 / 396470:

same basic thesis across runs:
current official operating/net profit is positive
but business KPI / persistence / valuation evidence is incomplete

output alternates between:
HOLD 5.5:4.5 BUY_LEAN
and
BUY 6.0:4.0
```

For `020180`:

```text
same dominant negative evidence:
official operating loss + net loss

output alternates between:
SELL 4.0:6.0
and
HOLD 4.5:5.5 SELL_LEAN
```

For `NWS` and `122310`, the main same-direction material anchors remain similar while the point estimate crosses the threshold.

This suggests a **balance-calibration / adjacent-bucket ambiguity** may be the dominant failure mode.

That hypothesis must be proven offline before architecture mutation.

Do not assume it merely from the summary counts.

---

# 7. Current Directional Core prompt gap to audit

The frozen Directional Core prompt currently specifies:

```text
directional_balance buy and sell sum to 10
0.5 increments

BUY  when buy >= 6
SELL when sell >= 6
otherwise HOLD
```

but does not define a sufficiently explicit ordinal evidence rubric distinguishing:

```text
5.0
5.5
6.0
6.5
7.0+
```

The task must determine whether this under-specified calibration is the generic root cause.

Do not change the numeric thresholds first.

Do not change the stability audit to hide the issue.

---

# 8. Message quality remains a separate issue

All four runs reported advisory message-quality FAIL:

```text
FIRST repeated substantive spans = 9
A     repeated substantive spans = 7
B     repeated substantive spans = 13
C     repeated substantive spans = 5

failure =
cross_ticker_substantive_repetition
```

This is important but is not the current hard blocker.

Do not mix a broad renderer/prose rewrite into the Directional calibration repair.

Preserve message-quality evidence and carry it forward separately.

If the fresh generalization proof later passes stability but message-quality still fails:

```text
next_scope =
MESSAGE_SPECIFICITY_AND_REPETITION_REMEDIATION
```

before production-message integration, unless separately waived.

---

# 9. Runtime reliability observation

The latest proof completed all 32 model contexts.

Two Price-Timing contexts in run C emitted:

```text
stream disconnected - retrying sampling request
WebSocket protocol error:
Connection reset without closing handshake
```

Both later completed successfully.

Measured:

```text
disconnect_count = 2
cli_retry_signal_count = 2
wrapper_retry_count = 0
timeout_count = 0
failed_real_contexts = 0
```

This proves only:

```text
recovery was observed in those two calls
```

not universal runtime reliability.

Do not change transport in this task.

Preserve the observation.

---

# 10. Task goal

Perform:

```text
1. offline instability root-cause audit on the fully exposed cohort
2. prove whether instability is adjacent-bucket calibration ambiguity
3. design a generic ordinal Directional Core balance rubric
4. keep BUY/HOLD/SELL thresholds unchanged
5. add a conservative ambiguity/tie-break rule
6. validate the repair on fictional repeated calibration canaries
7. if fictional stability passes, freeze the generic repair
8. add the current 16 issuers to the real-exposure exclusion registry
9. select a completely fresh unseen US4 + KR12 cohort
10. build a fresh source generation/source lock
11. execute FIRST/A/B/C
12. require Directional Core UNSTABLE = 0 for readiness
```

Do not create a separate preparation-only task after the fictional calibration proof passes.

Proceed to the fresh real proof in the same task.

---

# 11. Repository provenance gate

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Latest result reported:

```text
base_sha =
3d5cbddd20df8120423cc9786a3b0ac3382d0f49

work_instruction_commit =
8b5477c45023d2330fb686dab6f792e2a8e09715

implementation_commit =
0379cd604a0c305147585835e399f40e1e8d5933

final_head_sha =
05c93cf7d768ddb09b670ca74dc69c2b698e5f6b
```

If unexplained changes affect:

```text
Directional Core
Price-Timing
composer
renderer

source semantics
prompt/schema
transport
model/context
```

record and classify them.

Do not silently reset unrelated work.

---

# 12. Work-instruction commit first

Commit this instruction before architecture mutation.

Record:

```text
new_work_instruction_commit
```

Only then modify the bounded Directional Core calibration surface.

---

# 13. Allowed mutation surface

Allowed:

```text
Directional Core prompt calibration instructions
Directional Core balance-calibration helper if one already exists
Direction/lean consistency validator
fictional calibration fixtures
tests for the calibration contract
experiment-only proof orchestration/reporting
```

A schema change is not preferred.

If a new output field is absolutely necessary for calibration auditability:

```text
STOP after design review
```

unless it can be added without changing downstream semantic ownership and is covered by complete schema migration tests.

Prefer using existing fields:

```text
directional_balance
overall_direction
hold_lean
directional_confidence
material_directional_anchor_basis
dominant_evidence
core_investment_judgment
uncertainty_limit
```

---

# 14. Forbidden shortcuts

Do NOT solve the problem by:

```text
majority voting repeated model outputs
averaging A/B/C scores
selecting the most common direction
post-hoc choosing the preferred run
```

Do NOT merely relabel:

```text
BUY 6.0 ↔ HOLD 5.5
```

as `BOUNDARY_UNCERTAINTY` in the stability validator while leaving product outputs unstable.

The product output itself must become more stable.

Do NOT change:

```text
BUY threshold from 6.0
SELL threshold from 6.0
0.5 score increment
BUY:SELL sum = 10
```

in this task.

Do NOT add ticker-specific score rules.

Do NOT use the exposed cohort as production exceptions.

---

# 15. Offline instability root-cause audit

Before prompt or code mutation, produce a subject-level audit for all 16 exposed issuers.

For each issuer compare A/B/C:

```text
overall_direction
directional_balance
hold_lean
directional_confidence

material_directional_anchor_basis
dominant_evidence evidence refs
buy-driver evidence refs
sell-driver evidence refs

core_investment_judgment
uncertainty_limit

fundamental_new_buyer
fundamental_holder
```

Classify each non-STABLE case into one of:

```text
ADJACENT_BALANCE_CALIBRATION_AMBIGUITY
MATERIAL_EVIDENCE_SELECTION_VARIANCE
OPPOSING_EVIDENCE_INTERPRETATION_VARIANCE
CONFIDENCE_ONLY_VARIANCE
TRUE_SEMANTIC_REASONING_DIVERGENCE
MIXED
```

Required summary:

```text
unstable_count
adjacent_calibration_count
material_evidence_variance_count
true_semantic_divergence_count
```

Do not mutate the architecture unless:

```text
GENERIC_DIRECTIONAL_CALIBRATION_ROOT_CAUSE_CONFIRMED
```

is supported.

If the majority of unstable cases are true semantic reasoning divergence rather than adjacent calibration:

```text
STOP
```

and recommend a broader evidence-reasoning architecture task.

---

# 16. Ordinal balance calibration contract

If adjacent calibration ambiguity is confirmed, add an explicit generic ordinal rubric.

The rubric must describe meaning, not fixed weighted factors.

Required conceptual ladder:

```text
5.0 : 5.0
= genuinely balanced, unresolved, or evidence too incomplete for a lean

5.5 : 4.5
= positive lean:
  material positive issuer-level evidence exists
  but corroboration/currentness/persistence/valuation/critical KPI gaps
  prevent a full positive direction

6.0 : 4.0
= minimum BUY:
  a material positive issuer-level anchor exists
  AND evidence is sufficiently corroborated/current for a directional call
  AND unresolved counterevidence does not keep the case at lean-only

6.5+ : 3.5-
= progressively stronger positive direction:
  stronger corroboration, persistence, quality, visibility or valuation support
  under the same evidence-only rules
```

Symmetric meaning must apply to:

```text
4.5 : 5.5
4.0 : 6.0
3.5 : 6.5+
```

Do not equate:

```text
missing evidence = automatically negative
```

Unknown evidence limits conviction but is not a sell point by itself.

---

# 17. Conservative ambiguity rule

Add an explicit generic tie-break rule:

```text
When the same supplied evidence reasonably fits two adjacent balance buckets,
choose the less directional bucket, toward 5.0:5.0.
```

Examples:

```text
uncertain between 5.5 and 6.0
→ choose 5.5

uncertain between sell 5.5 and sell 6.0
→ choose sell 5.5 / HOLD SELL_LEAN
```

This is not a threshold change.

It is a calibration rule for ambiguous evidence.

The rule must apply symmetrically to positive and negative directions.

---

# 18. Direction / balance / confidence consistency

Preserve deterministic consistency:

```text
overall_direction is derived from balance
hold_lean is derived from HOLD balance
```

Do not let confidence independently override direction.

However, calibration instructions may state that:

```text
LOW confidence
```

is evidence that the model should carefully test whether the case truly satisfies the full directional bucket rather than a lean bucket.

Do not use a mechanical rule:

```text
LOW confidence => HOLD
```

unless separately proven necessary.

The task must avoid converting confidence into a hidden threshold override.

---

# 19. No fixed-weight scorecard

Do not introduce a fixed weighted point system such as:

```text
earnings +2
valuation +1
KPI +1
```

The system's investment reasoning remains evidence-based and sector-aware.

The calibration rubric defines **ordinal evidence sufficiency for a directional bucket**, not a universal company score.

---

# 20. Generic fictional calibration fixtures

Before any new real issuer model call, create fictional schema-valid evidence cases.

At minimum cover:

```text
F1 BALANCED_INCOMPLETE
- mixed/limited evidence
- expected bucket: 5.0:5.0 HOLD

F2 POSITIVE_LEAN_INCOMPLETE
- one material positive anchor
- important corroboration / persistence / valuation gap
- expected bucket: 5.5:4.5 HOLD BUY_LEAN

F3 MINIMUM_POSITIVE_DIRECTION
- material positive anchor + independent corroboration/currentness
- no material counter-anchor
- expected bucket: at least 6.0:4.0 BUY

F4 STRONG_POSITIVE
- multiple strong corroborated positive issuer-level anchors
- expected BUY, not HOLD

F5 NEGATIVE_LEAN_INCOMPLETE
- one material negative anchor with unresolved uncertainty
- expected 4.5:5.5 HOLD SELL_LEAN

F6 MINIMUM_NEGATIVE_DIRECTION
- material negative anchor + corroboration/currentness
- expected at most 4.0:6.0 SELL

F7 STRONG_NEGATIVE
- multiple corroborated negative issuer-level anchors
- expected SELL

F8 UNKNOWN_NOT_NEGATIVE
- mostly unknown/incomplete evidence
- expected not to become SELL merely because data is missing
```

Use fictional issuer identities only.

Production-valid market enum remains:

```text
us / kr
```

---

# 21. Repeated fictional calibration canary

Run the fictional cases repeatedly under the same frozen model configuration.

Recommended:

```text
2 four-subject contexts
× 3 independent repetitions
= 6 model calls
```

Use:

```text
gpt-5.6-sol
xhigh
4-subject MODEL_CONTEXT_COUPLED
1800-second single watchdog
unique runtime namespace per context
```

No wrapper retry.

Required fictional acceptance:

```text
schema = PASS

each fixture remains in its expected direction class
across all 3 repetitions

no BUY ↔ HOLD flip for the minimum-positive fixture
no SELL ↔ HOLD flip for the minimum-negative fixture
no opposite-direction reversal

fictional directional UNSTABLE count = 0
```

Balance variation inside the same direction may be recorded but must not violate the fixture's calibration expectation.

If fictional calibration acceptance fails:

```text
STOP
```

Do not consume a new real holdout.

---

# 22. Architecture freeze after fictional PASS

If fictional calibration passes:

```text
commit/freeze the generic Directional Core calibration repair
```

Capture:

```text
prompt hash
schema hash
calibration contract hash
model/runtime identity
namespace isolation identity
```

After this freeze:

```text
no calibration edits after seeing new real outputs
```

---

# 23. Retire current fully exposed cohort

The current 16 issuers:

```text
WYNN
DOX
NWS
ASTI
064850
053270
078860
145720
199730
065510
396470
299900
020180
122310
417200
023910
```

must be added to the future real-exposure exclusion registry.

Latest result already had:

```text
new_exclusion_registry_count = 133
```

before retiring the current fresh proof cohort.

Expected next count is at least:

```text
149
```

unless current repository history contains additional newly exposed issuers.

Do not hard-code `149` if the canonical registry contains more.

Report:

```text
previous registry count
added current cohort count = 16
final registry count
registry hash
```

---

# 24. Existing source configuration and free-data policy

Use the existing protected source configuration.

Do not create another environment-binding project.

At start of fresh selection perform only:

```text
secret-safe presence preflight
```

Required:

```text
OPENDART_API_KEY present
SEC_USER_AGENT present
secret values emitted = 0
```

Use existing free-data routes.

Do not add paid data providers.

Do not lower evidence requirements to fill the cohort.

---

# 25. Existing scheduled monitoring remains paused

The user requested US/KR scheduled monitoring remain paused.

Latest result observed:

```text
observed_paused_schedule_count = 8
automatic_monitoring_resume = 0
```

Maintain that state.

Do not automatically resume after proof success.

If an approved paused path unexpectedly becomes active:

```text
pause only that exact approved monitoring path
record actual mutation
```

Do not alter unrelated schedules.

---

# 26. Fresh unseen cohort selection after architecture freeze

Only after fictional calibration PASS:

select a completely fresh:

```text
US4 + KR12
```

using:

```text
updated real-exposure exclusion registry
existing deterministic outcome-independent selection
precommitted reserve ordering
current free-data support
canonical source-sufficiency rules
```

No previously model-exposed issuer may be selected.

Do not select based on expected BUY/HOLD/SELL outcome.

---

# 27. Fresh source generation / source lock

Create a new:

```text
source generation
ordered issuer manifest
per-issuer packet hashes
source identity audit
source sufficiency audit
aggregate source lock
```

Do not reuse:

```text
d66f7425646512e1eb6916b61912e52660ce3fc2449fd9d6af59e5e3dd15210b
```

The old source lock belongs to the exposed diagnostic cohort.

---

# 28. Fresh real proof precommit

Before first fresh real model call freeze:

```text
ordered 16 issuers
context groups

source generation
source lock
packet hashes

new Directional calibration prompt hash
Price-Timing prompt hash
schemas

model
effort
timeout
namespace-isolation contract

hard gates
stability criteria
message-quality advisory contract
runtime failure rules
```

No investment-semantic edits after fresh real output appears.

---

# 29. Fresh FIRST/A/B/C execution

Run:

```text
FIRST
→ hard gates
→ A
→ hard gates
→ B
→ hard gates
→ C
→ hard gates
```

At first required hard failure:

```text
STOP
```

No automatic retry.

No selective continuation after failure.

No same-cohort architecture hotfix.

---

# 30. Per-context preservation and isolation

Before every model spawn:

```text
runtime namespace unique
working directory unique
invocation ID unique
```

After every successful context:

```text
preserve raw output
stdout
stderr/log
transport receipt
prompt
schema
context manifest
namespace/session/workdir identities

hash
secret scan
reopen validation
```

Namespace collision:

```text
STOP BEFORE SPAWN
```

---

# 31. Fresh run hard gates

For FIRST/A/B/C require existing:

```text
ownership gate = PASS
renderer gate = PASS
hard-safety gate = PASS
```

Price-Timing ownership invariants remain unchanged.

Do not modify Price-Timing because Directional Core calibration changed.

---

# 32. Fresh stability acceptance

Formal Directional Core readiness requires:

```text
UNSTABLE = 0
```

`BOUNDARY_UNCERTAINTY` may remain if allowed by the existing frozen stability contract.

Do not change the stability validator merely to obtain PASS.

Price-Timing acceptance remains:

```text
UNSTABLE = 0
```

under its existing contract.

Report subject-level A/B/C values.

Do not use majority vote.

---

# 33. Message-quality advisory

Continue the existing advisory test.

Report separately for every run:

```text
status
repeated substantive span count
repetition taxonomy
affected messages if measurable
```

Do not hide FAIL.

Do not change message prose in this task after seeing fresh proof output.

If core/timing/generalization all pass but message quality remains FAIL:

```text
readiness =
READY_FOR_MESSAGE_QUALITY_REMEDIATION

next_scope =
MESSAGE_SPECIFICITY_AND_REPETITION_REMEDIATION
```

Do not begin Monitoring Bootstrap until that production-message quality issue is reviewed, unless separately authorized to accept the advisory risk.

---

# 34. Runtime observations

Do not modify transport because two recovered disconnects occurred in the latest completed proof.

Continue to report:

```text
disconnect_count
CLI retry signals
wrapper retry count
timeout count
capacity errors
orphan count
```

If disconnect occurs and recovers:

```text
record observed recovery
```

If it leads to watchdog timeout:

```text
STOP
```

No timeout increase.

No model substitution.

---

# 35. Production no-change

Maintain:

```text
production DB mutation = 0
production Telegram send = 0
monitoring registration change = 0
live V2 activation/change = 0
Night Futures change = 0
automatic monitoring resume = 0
```

Only already-approved pause maintenance may modify those exact scheduler objects if unexpectedly active.

---

# 36. Monitoring Bootstrap remains out of scope

Do not implement Monitoring Bootstrap here.

Possible next scopes:

## If core stability still fails

```text
GENERIC_DIRECTIONAL_CORE_REASONING_ARCHITECTURE_REVIEW
```

## If core/timing/generalization pass but message quality fails

```text
MESSAGE_SPECIFICITY_AND_REPETITION_REMEDIATION
```

## If all required proof and production-message quality conditions are accepted

```text
Monitoring Bootstrap Integration Review
```

---

# 37. Required artifacts — offline root-cause review

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-directional-instability-subject-matrix
04-directional-anchor-set-comparison
05-directional-rationale-and-uncertainty-comparison
06-directional-instability-root-cause-classification
07-directional-calibration-architecture-decision
```

---

# 38. Required artifacts — repair and fictional canary

If calibration root cause confirmed:

```text
08-directional-calibration-contract
09-directional-calibration-prompt-diff
10-directional-calibration-regression-tests
11-fictional-calibration-fixture-manifest
12-fictional-calibration-run-1
13-fictional-calibration-run-2
14-fictional-calibration-run-3
15-fictional-calibration-stability-summary
16-calibration-freeze-seal
```

If fictional calibration fails:

```text
fresh real proof artifacts = NOT_RUN
```

---

# 39. Required artifacts — fresh proof

If fictional calibration passes:

```text
17-updated-real-exposure-exclusion-registry
18-source-config-presence-preflight
19-schedule-pause-observation
20-fresh-selection-policy
21-us-candidate-source-readiness
22-kr-candidate-source-readiness
23-fresh-holdout-selection
24-fresh-source-generation
25-source-identity-audit
26-source-sufficiency-audit
27-fresh-source-lock
28-fresh-proof-precommit
29-investment-semantic-freeze
30-runtime-isolation-freeze
```

Then per FIRST/A/B/C:

```text
execution summary
context artifact manifest
per-context semantic audit
ownership gate
renderer gate
hard-safety gate
message-quality advisory
```

---

# 40. Required final artifacts

Produce:

```text
fresh-holdout-exposure-retirement-state
fresh-directional-core-stability
fresh-price-timing-stability
fresh-ownership-generalization
fresh-renderer-ownership-proof
fresh-hard-safety-regression
fresh-message-quality-summary
runtime-reliability-observations
production-no-change
night-futures-no-change
next-scope-handoff
program-completion
```

---

# 41. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

historical_core_stability_counts
historical_timing_stability_counts
historical_unstable_tickers

adjacent_calibration_ambiguity_count
material_evidence_variance_count
true_semantic_divergence_count
calibration_root_cause

directional_calibration_repair_applied
directional_threshold_changed
majority_vote_adopted
fixed_weight_scorecard_adopted

fictional_calibration_model_call_count
fictional_calibration_unstable_count
fictional_calibration_status

previous_exclusion_registry_count
fresh_exclusion_registry_count
newly_excluded_current_cohort_count

fresh_us_target_status
fresh_kr_target_status
fresh_cohort
fresh_source_generation
fresh_source_lock

model
reasoning_effort
batch_semantics
subjects_per_context
timeout
timeout_owner_count

planned_real_contexts
attempted_real_contexts
successful_real_contexts
failed_real_contexts

distinct_real_namespace_count
namespace_collision_count

raw_output_document_count
unique_issuer_output_count

wrapper_retry_count
cli_retry_signal_count
disconnect_count
capacity_failure_count
timeout_count
orphan_count

run_results.first
run_results.a
run_results.b
run_results.c

first_ownership_gate
first_renderer_gate
first_hard_safety_gate
first_message_quality

run_a_ownership_gate
run_a_renderer_gate
run_a_hard_safety_gate
run_a_message_quality

run_b_ownership_gate
run_b_renderer_gate
run_b_hard_safety_gate
run_b_message_quality

run_c_ownership_gate
run_c_renderer_gate
run_c_hard_safety_gate
run_c_message_quality

fresh_core_stability_counts
fresh_timing_stability_counts
fresh_ownership_generalization
fresh_message_quality_status

exposure_state
semantic_revelation_state
retirement_state
future_unseen_reuse_allowed

observed_paused_schedule_count
automatic_monitoring_resume

paid_data_service_change
production_db_mutation
production_send
monitoring_registration_change
live_v2_change
night_futures_change

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

status
readiness
stop_reason
next_scope
```

Unmeasured fields remain:

```text
NOT_MEASURED
```

---

# 42. Artifact integrity

Create the final artifact index only after completion artifacts are frozen.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 43. Decision matrix

## A. Offline audit does NOT confirm adjacent calibration as the generic root cause

```text
STOP
no architecture patch
no fictional model calls
no fresh real holdout

next_scope =
GENERIC_DIRECTIONAL_CORE_REASONING_ARCHITECTURE_REVIEW
```

## B. Calibration repair applied but fictional repeated canary remains unstable

```text
STOP
no fresh real holdout
```

Do not weaken the fictional acceptance criteria.

## C. Fictional calibration passes but fresh source targets fail

Finish both market diagnostics.

Stop pre-model.

## D. Fresh real proof still has Directional UNSTABLE > 0

```text
NOT_READY_DIRECTIONAL_CORE_STABILITY
```

Do not majority-vote the result.

Preserve fresh cohort as exposed/retired.

## E. Fresh Directional and Timing stability pass, ownership/renderer/safety pass, but message quality fails

```text
READY_FOR_MESSAGE_QUALITY_REMEDIATION
```

Do not silently mark production messaging ready.

## F. All proof conditions and accepted message-quality conditions pass

Then:

```text
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW
```

Monitoring remains paused until separately authorized.

---

# 44. Final task principle

The latest proof completed all 32 real model contexts.

The runtime namespace defect is fixed.

The ownership boundary is holding.

Price-Timing is not the current blocker.

The remaining primary failure is that the Directional Core's free-form 0.5-point balance calibration can cross a hard BUY/HOLD or HOLD/SELL boundary even when the underlying evidence interpretation remains similar.

Therefore the correct next move is:

```text
prove the adjacent-bucket calibration failure
→ define a generic ordinal balance rubric
→ resolve ambiguity conservatively
→ test repeated fictional calibration
→ freeze
→ fresh unseen real proof
```

Not:

```text
majority vote
```

Not:

```text
change the threshold after seeing the cohort
```

Not:

```text
relabel product instability as audit-only uncertainty
```

Not:

```text
change Price-Timing
```

And not:

```text
re-run the exposed cohort after repair
```

Stabilize the Directional Core generically, then prove it on a genuinely fresh cohort.
