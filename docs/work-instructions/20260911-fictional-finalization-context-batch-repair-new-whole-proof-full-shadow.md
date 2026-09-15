# Thesis Monitor — Fictional Finalization Context-Batch Repair + New Whole Proof + Full Monitored Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-fictional-finalization-context-batch-repair-new-whole-proof-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-fictional-finalization-context-batch-repair-new-whole-proof-full-shadow-report.zip
```

Master-workflow phase:

```text
M12AK — Integrated-Main Proof Harness Repair
         A. Repair fictional finalization context batching only
         B. Offline-replay preserved M12AJ outputs for harness verification
         C. Start a NEW full 8 × 3 two-stage fictional generation
         D. If hard semantic gates pass, run full active-monitored shadow
         E. Produce combined boundary / delta-materiality / holder diagnostics
```

M12AJ's semantic implementation successfully completed all intended
proof-critical fictional model calls:

```text
Stage 1 calls = 6 / 6
Stage 2 calls = 6 / 6
total model calls = 12 / 12

Stage 1 rows = 24 / 24 individual semantic PASS
Stage 2 rows = 24 / 24 individual semantic PASS

business-delta capability violation = 0
business-delta direction violation = 0
direction-hint projection mismatch = 0
unsafe metric auto-direction = 0

core mutation after stance = 0

timeout = 0
orphan = 0
wrapper retry = 0
```

M12AJ did NOT fail on model semantics.

It failed after all 12 calls had completed,
inside the proof harness finalization layer:

```text
M12AI finalize_fictional grouped all 8 repetition candidates
into DirectionalCoreBatch,
whose frozen schema permits at most 4 candidates.
```

This is a deterministic finalization/batching bug.

M12AK must repair ONLY that proof-harness defect first.

Do not use this task as an opportunity to change model semantics.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260911-typed-financial-delta-direction-hint-propagation-fictional-reproof-full-shadow-report.zip
```

Verified SHA-256:

```text
684db3efb089c05d03c51dfcee7c45c14ba804be136848a9bfa6d5eb0d2deb18
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
indexed payloads = 184
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

The ZIP contains:

```text
184 indexed payloads
+ artifact-index.json
= 185 entries
```

Recompute independently.

---

# 2. M12AJ repository provenance

Reported:

```text
base integration head =
a296ed2d353d5f811eaf70748c3f6cb90fdcca30

branch =
codex/20260911-typed-financial-delta-direction-m12aj

implementation head =
8a5b2cf9708882a1aad91589bb96368d0c81a649

previous final sha =
56a2038e167a2ce71a4190bf72c29b541812e94b

work instruction commit =
a988ce265791a1c529a2f72c5740495820035c3d
```

At task start record actual:

```text
branch
HEAD
working tree
remote tracking state
```

Do not assume a later local report-closeout commit from prose.

If unexplained code drift exists in semantic services:

```text
STOP
UNEXPLAINED_M12AK_SEMANTIC_DRIFT
```

---

# 3. Git remote policy — hard freeze

This task is LOCAL-ONLY.

Allowed:

```text
local branch
local commits
local report ZIP
local SHA-256
```

Forbidden unless the user separately gives explicit approval later:

```text
git push
git push origin
GitHub remote push
raw-model-artifact push
prompt/output/receipt/log push
main merge
deployment
```

Required:

```text
remote_push_count = 0
raw_model_artifact_remote_push_count = 0
main_merges = 0
deployments = 0
```

Do not ask for push approval as part of this task.

Finish locally.

---

# 4. M12AJ stop receipt — authoritative failure

M12AJ stop:

```text
stop_reason =
FICTIONAL_FINALIZATION_BATCH_SIZE_CONTRACT_FAILURE

failure_stage =
post_model_aggregate_revalidation

completed_model_calls =
12

completed_run_documents =
12

individual_context_hard_gate_pass_count =
12

monitored_shadow_model_calls =
0

model_output_rewritten =
false

post_freeze_code_change =
false
```

This is not:

```text
model schema failure

financial semantic failure

business-delta direction failure

runtime failure

two-stage composition failure
```

It is:

```text
PROOF_HARNESS_FINALIZATION_BATCHING_FAILURE
```

---

# 5. Exact root cause

The inherited M12AI finalizer conceptually did:

```text
for one repetition:
    collect all 8 subject candidates

DirectionalCoreBatch(candidates=all_8)
```

But the frozen model/context schema contract is:

```text
max candidates per context = 4
```

Therefore:

```text
8 candidates
→ invalid DirectionalCoreBatch
```

even though the original model calls were correctly organized as:

```text
context-01 = 4 subjects
context-02 = 4 subjects
```

The aggregate layer incorrectly reused a context-level schema
for a repetition-level aggregation.

---

# 6. Correct layer separation

Freeze this distinction:

## Model/context schema

Validates:

```text
one model context
up to 4 subjects
```

Example:

```text
DirectionalCoreBatch
max 4 candidates
```

## Proof aggregation

Aggregates already context-validated rows across:

```text
2 contexts
8 subjects
3 repetitions
```

Proof aggregation is NOT a model context.

It must not instantiate a context-level batch object
with 8 candidates.

---

# 7. Preferred finalization architecture

Preferred:

```text
preserve original context boundaries

for each run:
    validate Stage 1 context-01 (4)
    validate Stage 1 context-02 (4)

    validate Stage 2 context-01 (4)
    validate Stage 2 context-02 (4)

    compose per matching context

    obtain 8 individually validated final rows

aggregate those rows using ordinary Python/report structures
without re-wrapping all 8 into DirectionalCoreBatch
```

Then across 3 runs:

```text
24 final validated rows
```

Aggregate:

```text
by ticker
by repetition
```

for stability/diagnostic reporting.

No model schema should be used as a global proof container.

---

# 8. Acceptable fallback finalization architecture

If an existing audit helper absolutely requires `DirectionalCoreBatch`,
then:

```text
revalidate in chunks matching original context boundaries
or chunks <= 4
```

Hard requirements:

```text
no candidate dropped

no candidate duplicated

no cross-ticker mutation

no context-dependent evidence catalog mismatch

no order-dependent semantic difference

24 final rows preserved
```

But prefer context-preserving revalidation over arbitrary chunking.

---

# 9. Do not widen DirectionalCoreBatch max-items

Forbidden repair:

```text
change max candidates 4 → 8
```

solely to make finalization pass.

The max-4 limit belongs to the frozen context topology.

Widening the production/model schema to repair an aggregate harness
would conflate two layers and could affect actual runtime contracts.

Required:

```text
directional_core_batch_max_items_changed = false
```

---

# 10. No model-semantic changes

M12AK must not change:

```text
BusinessDeltaEvidenceCapability

dynamic business_thesis_change schema

financial-comparison-direction-v1

safe cash-conversion polarity

direction-hint projection

business-delta validation

financial temporal scope

monitoring transition ownership

Stage 1 prompt

Stage 2 prompt

Stage 1 schema semantics

Stage 2 schema semantics

Directional thresholds

holder/new-buyer contracts

two-stage ownership

Price-Timing

Renderer
```

Required:

```text
model_prompt_semantic_change_count = 0

model_schema_semantic_change_count = 0

business_delta_semantic_change_count = 0

financial_semantic_change_count = 0

two_stage_semantic_change_count = 0
```

The only intended change is:

```text
proof harness finalization batching.
```

---

# 11. Freeze M12AJ typed-direction success

M12AJ proved before the aggregate failure:

```text
FIC-FIN-02 E01 → WEAKENED

FIC-FIN-02 E08 → WEAKENED

FIC-FIN-02 E10 → STRENGTHENED

FIC-FIN-02 E04 → direction unspecified

direction_hint_projection_mismatch_count = 0

unsafe_metric_auto_direction_count = 0

capability_classification_change_count = 0
```

Do not reopen these contracts.

---

# 12. M12AJ context-level semantic proof

M12AJ reports:

```text
context documents = 12
context documents PASS = 12

Stage 1 rows = 24
Stage 1 row PASS = 24

Stage 2 rows = 24
Stage 2 row PASS = 24

business-delta capability violations = 0

business-delta direction violations = 0

core mutation count = 0
```

These are valid diagnostic evidence about the implementation.

They are NOT sufficient to treat M12AJ as the new formal whole-generation proof
because the final aggregate hard gate did not complete.

---

# 13. Diagnostic raw repetition pattern from M12AJ

For debugging context only,
the preserved raw outputs show:

```text
FIC-FIN-01:
BUY 6.5 ×3
delta STRENGTHENED ×3
new buyer WAIT ×3
holder HOLDABLE ×3

FIC-FIN-02:
HOLD 4.5:5.5 SELL_LEAN ×3
delta UNRESOLVED ×3
new buyer WAIT ×3
holder REVIEW ×3

FIC-FIN-03:
HOLD 5.0 ×3
delta UNCHANGED ×3
new buyer WAIT ×3
holder REVIEW ×3

FIC-FIN-04:
HOLD 5.0 ×3
delta UNCHANGED ×3
new buyer WAIT ×3
holder HOLDABLE ×3
confidence LOW / MEDIUM / MEDIUM

FIC-FIN-05:
HOLD 5.5 / SELL 6.0 / HOLD 5.5
delta UNCHANGED ×3
new buyer WAIT ×3
holder REVIEW ×3

FIC-FIN-06:
HOLD 5.5 BUY_LEAN ×3
delta STRENGTHENED ×3
new buyer WAIT ×3
holder HOLDABLE ×3
confidence LOW / LOW / MEDIUM

FIC-FIN-07:
HOLD 5.0 ×3
delta UNCHANGED ×3
new buyer WAIT ×3
holder HOLDABLE ×3

FIC-FIN-08:
HOLD 5.0 ×3
delta UNCHANGED ×3
new buyer WAIT ×3
holder HOLDABLE / HOLDABLE / REVIEW
```

This is:

```text
DIAGNOSTIC_ONLY
```

Do not promote it to formal proof.

Important diagnostic implications:

```text
typed delta direction repair appears successful

FIC-FIN-02 delta is now stable UNRESOLVED across 3

FIC-FIN-06 delta is now stable STRENGTHENED across 3

remaining visible decision-material variance:
FIC-FIN-05 primary HOLD/SELL boundary
FIC-FIN-08 holder HOLDABLE/REVIEW boundary
```

Do not repair those in M12AK.

---

# 14. Offline harness replay before new model calls

After fixing only finalization batching,
run the repaired finalizer against the preserved M12AJ artifacts.

This is allowed because it tests:

```text
proof harness behavior
```

not model semantics.

Required:

```text
12 context documents revalidated

24 Stage 1 rows recovered

24 Stage 2 rows recovered

24 final compositions recovered

all 8 subjects × 3 repetitions accounted for

no row duplicate

no row omission

no ticker/context crossover

core immutability = PASS

business-delta capability audit = PASS

business-delta direction audit = PASS
```

Label:

```text
M12AJ_HISTORICAL_OFFLINE_FINALIZER_REPLAY
```

Never label:

```text
NEW_FORMAL_MODEL_PROOF.
```

---

# 15. Offline replay expected diagnostics

The repaired finalizer should be able to generate
the previously blocked aggregate reports from the preserved outputs.

Expected diagnostic counts based on preserved rows:

```text
primary direction unstable subjects =
1
FIC-FIN-05

new-buyer unstable subjects =
0

holder unstable subjects =
1
FIC-FIN-08

business-delta materiality variance subjects =
0

core mutation =
0
```

If offline replay produces a different result:

```text
STOP
FINALIZER_REPAIR_CHANGED_SEMANTIC_AGGREGATION
```

Investigate before model calls.

---

# 16. Finalization regression fixtures

Add deterministic tests.

At minimum:

## FINAL-01

```text
1 context
4 subjects
1 repetition
→ PASS
```

## FINAL-02

```text
2 contexts
8 subjects
1 repetition
→ PASS
without creating one 8-candidate DirectionalCoreBatch
```

## FINAL-03

```text
2 contexts
8 subjects
3 repetitions
→ 24 final rows
```

## FINAL-04

```text
candidate missing from one context
→ hard FAIL
```

## FINAL-05

```text
duplicate ticker inside same repetition
→ hard FAIL
```

## FINAL-06

```text
Stage 1 / Stage 2 context membership mismatch
→ hard FAIL
```

## FINAL-07

```text
core hash mismatch
→ hard FAIL
```

## FINAL-08

```text
context has 5 candidates
→ context schema FAIL
```

Do not relax the context max.

---

# 17. Aggregate identity invariants

For each formal generation:

```text
expected subject set =
exact frozen cohort

expected repetitions =
1,2,3

expected Stage 1 row count =
24

expected Stage 2 row count =
24

expected final composition count =
24
```

Unique identity key:

```text
(repetition, ticker)
```

Required:

```text
24 unique keys
```

No aggregate result may rely only on positional ordering.

Use explicit ticker/run identity.

---

# 18. Context membership invariants

For each:

```text
(run, context)
```

Stage 1 and Stage 2 must contain:

```text
the exact same ticker set
```

before composition.

Hard fail on:

```text
missing ticker
extra ticker
duplicate ticker
cross-context ticker
```

Do not silently reorder across contexts.

Within a context,
deterministic ticker matching may ignore JSON order
if ticker identity is exact.

---

# 19. Artifact-to-row lineage

Every final composed row must retain:

```text
Stage 1 invocation ID

Stage 2 invocation ID

run/repetition ID

context ID

ticker

core snapshot sha256
```

Aggregate reports must be traceable
back to original raw model artifacts.

No anonymous aggregation.

---

# 20. Code-change scope lock

Before implementing,
record hashes for:

```text
app/services/business_delta_evidence_service.py

app/services/direction_timing_ownership_service.py

app/services/directional_financial_context_service.py

app/services/two_stage_directional_service.py

frozen prompt builders

frozen schemas
```

After finalization repair,
require those semantic files to remain unchanged
unless the finalizer physically lives in one of them.

If a semantic service must change for a harness-only fix:

```text
STOP
explain architectural coupling before proceeding.
```

Preferred fix location:

```text
proof runner / finalization helper / reporting layer.
```

---

# 21. Full tests before model calls

Require:

```text
latest bundle integrity PASS

finalization root cause reproduced

context-batch repair implemented

DirectionalCoreBatch max-items unchanged

offline M12AJ replay PASS

expected offline stability diagnostics match

semantic-code hash freeze PASS

finalization regression fixtures PASS

existing typed direction tests PASS

business-delta capability tests PASS

financial temporal scope tests PASS

monitoring ownership tests PASS

two-stage ownership tests PASS

focused tests PASS

full local tests PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

No model calls before this gate.

---

# 22. Why a NEW whole fictional generation is mandatory

M12AJ completed 12 model calls,
but its final aggregate gate failed
and code changes will occur afterward.

Therefore formal proof integrity requires:

```text
NEW generation ID

NEW Stage 1 outputs

NEW Stage 2 outputs

NEW receipts/logs

NEW final compositions
```

Do NOT:

```text
reuse M12AJ outputs as the formal M12AK proof

continue from M12AJ

rerun only the finalizer and call M12AJ PASS

rerun only unstable subjects
```

The offline replay is harness verification only.

---

# 23. New fictional proof model/runtime

Use:

```text
model = gpt-5.6-sol

reasoning = xhigh
```

Runtime:

```text
MODEL_CONTEXT_COUPLED

4 subjects/context

1800-second finite watchdog

wrapper auto-retry = 0

batch split = 0
```

No Astra.

No fallback.

No timeout increase.

---

# 24. New fictional proof topology

Frozen subjects:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-03
FIC-FIN-04
FIC-FIN-05
FIC-FIN-06
FIC-FIN-07
FIC-FIN-08
```

Topology:

```text
2 contexts
4 subjects/context
3 repetitions

Stage 1 calls = 6
Stage 2 calls = 6

total model calls = 12

final composed rows = 24
```

No judge calls.

---

# 25. Whole-generation stop policy

Stop immediately for:

```text
runtime hard failure

schema hard failure

invalid evidence identity

objective financial semantic failure

business-delta capability violation

business-delta proven direction contradiction

price/technical/supply Core contamination

Stage 2 core mutation

finalization identity/batching failure
```

Do NOT stop for:

```text
same-direction balance variance

valid primary threshold variance

valid business-delta materiality variance

new-buyer variance

holder variance

confidence variance
```

Collect all 24 rows when hard gates pass.

---

# 26. Formal fictional acceptance

Require:

```text
12 / 12 model calls complete

12 / 12 context hard gates PASS

Stage 1 rows = 24 / 24 PASS

Stage 2 rows = 24 / 24 PASS

final composition rows = 24

aggregate finalization = PASS

DirectionalCoreBatch >4 use count = 0

business-delta capability violations = 0

business-delta direction violations = 0

direction-hint projection mismatch = 0

unsafe metric auto-direction = 0

objective financial semantic failure = 0

core mutation = 0

timeout = 0

orphan = 0

wrapper retry = 0
```

Decision-material variance alone does NOT fail the shadow gate.

---

# 27. Shadow gate after formal fictional proof

Authorize monitored shadow if:

```text
runtime/schema/objective hard semantics PASS

finalization PASS

core mutation = 0

business-delta capability/direction violations = 0
```

Do NOT require:

```text
primary direction stable for every fictional subject

holder stable for every fictional subject
```

Those are diagnostics for the later policy review.

This is critical.

Otherwise FIC-FIN-05/FIC-FIN-08 would again prevent
the real exposed compatibility evidence we need.

---

# 28. Active monitored universe

At shadow start,
re-enumerate active monitored stocks read-only.

Last verified reference:

```text
22 active names
```

Use actual task-start set.

Record:

```text
task_start_active_monitor_count

task_start_active_monitor_tickers

reference_added_tickers

reference_removed_tickers
```

No monitoring mutation.

---

# 29. Frozen same-packet shadow

For every active monitored ticker:

```text
one reproducible local evidence packet
```

Exact same packet hash must feed:

```text
monolithic control

two-stage Stage 1

two-stage Stage 2 evidence/citation context
```

No external provider refresh.

Required:

```text
provider_source_fetches = 0
```

---

# 30. Shadow business-delta view equality

Monolithic and Stage 1 must receive
semantically identical per-ticker:

```text
BusinessDeltaEvidenceCapability

eligible_change_refs

baseline_context_refs

eligible_change_direction_hints

direction-unspecified eligible refs
```

Required:

```text
monolithic_stage1_delta_view_equality = PASS
```

---

# 31. Shadow topology

For N active names:

```text
context_count = ceil(N / 4)

monolithic calls = context_count

Stage 1 calls = context_count

Stage 2 calls = context_count

total = 3 × context_count
```

At N=22:

```text
18 model calls
```

No repetitions.

No fresh unseen issuers.

---

# 32. Shadow hard-stop policy

Stop only for:

```text
runtime/schema hard failure

packet hash mismatch

invalid evidence identity

objective financial semantic failure

business-delta capability violation

business-delta proven direction contradiction

price/technical/supply Core contamination

financial-sector framework misuse

ADR/security-basis violation

Stage 2 core mutation

production-side-effect attempt

shadow finalization identity/batching failure
```

Do NOT stop for monolithic-vs-two-stage decision differences.

Collect the full cohort.

---

# 33. Shadow finalization must reuse repaired batching principles

Shadow may contain:

```text
6 contexts for 22 names
```

Do NOT aggregate all 22 candidates into a model context schema.

Use:

```text
context-level validation
→ individually validated per-ticker rows
→ ordinary aggregate report structures
```

Add a shadow regression fixture:

```text
22 names
6 contexts
→ exactly 22 unique final comparison rows
```

This prevents the same harness bug from reappearing after fictional proof.

---

# 34. Shadow comparison taxonomy

Use:

```text
NO_DECISION_MATERIAL_CHANGE

SAME_DIRECTION_CALIBRATION_CHANGE

PRIMARY_DIRECTION_CHANGE

BUSINESS_DELTA_CHANGE

NEW_BUYER_STANCE_CHANGE

HOLDER_STANCE_CHANGE

MULTI_FIELD_DECISION_CHANGE

EXPECTED_CONTRACT_CORRECTION

POTENTIAL_ARCHITECTURE_REGRESSION

OTHER_REVIEW_REQUIRED
```

Delta sublabels:

```text
DELTA_UNCHANGED_ONLY

DELTA_AI_JUDGMENT

DELTA_MATERIALITY_DIFFERENCE

DELTA_EVIDENCE_SELECTION_DIFFERENCE

DELTA_DIRECTION_HINT_DIFFERENCE
```

No majority vote.

Neither architecture is automatically ground truth.

---

# 35. Combined policy diagnostics

If shadow completes,
compare fictional and monitored behavior for:

## Primary boundary

```text
FIC-FIN-05:
HOLD 5.5 ↔ SELL 6.0
```

Question:

```text
Do same-packet real monitored names
show architecture-sensitive threshold crossings?
```

## Business-delta materiality

M12AJ diagnostic raw outputs suggest:

```text
FIC-FIN-02 = UNRESOLVED ×3

FIC-FIN-06 = STRENGTHENED ×3
```

Confirm in the new formal generation.

Then compare with real `AI_JUDGMENT` monitored names.

## Holder boundary

```text
FIC-FIN-08:
HOLDABLE ↔ REVIEW
```

Compare with real financial-sector / uncertainty-heavy monitored cases.

Do not repair these contracts during M12AK.

---

# 36. Remote/raw artifact handling

Raw artifacts are required locally for audit.

They must remain:

```text
local-only
```

Do NOT push:

```text
raw prompts

raw model outputs

receipts

transport logs

run documents

report bundles containing raw model artifacts
```

to GitHub.

The final ZIP may be given to the user locally,
but remote repository publication is out of scope.

---

# 37. Main integration remains frozen

Do not:

```text
fetch/merge newer main

merge current branch into main
```

Run on existing integrated-main lineage.

A later final-main task can handle drift
after fresh unseen proof.

---

# 38. Production side-effect firewall

Required:

```text
model_calls_real_fresh_unseen = 0

provider_source_fetches = 0

production_db_mutations = 0

monitoring_registrations = 0

monitoring_stops = 0

assessment_persistence_mutations = 0

warning_mutations = 0

notification_queue_writes = 0

production_sends = 0

remote_push_count = 0

raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0

main_merges = 0

deployments = 0

automatic_monitoring_resume = 0
```

Schedules remain paused.

---

# 39. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12ak-scope-freeze

04-integrated-main-lineage-freeze

05-m12aj-stop-reproduction

06-finalizer-code-path-audit

07-context-schema-vs-aggregate-layer-root-cause

08-directional-core-batch-max4-freeze

09-finalization-repair-architecture-decision
```

---

# 40. Required finalization repair artifacts

Produce:

```text
10-context-preserving-finalization-contract

11-stage1-context-finalization-contract

12-stage2-context-finalization-contract

13-per-context-composition-contract

14-cross-context-aggregate-identity-contract

15-final-row-lineage-contract

16-finalization-regression-fixtures

17-shadow-finalization-regression-fixture
```

---

# 41. Required semantic freeze artifacts

Produce:

```text
18-model-prompt-semantic-freeze

19-model-schema-semantic-freeze

20-business-delta-capability-freeze

21-typed-financial-direction-freeze

22-financial-temporal-scope-freeze

23-monitoring-ownership-freeze

24-two-stage-ownership-freeze

25-price-timing-renderer-no-change
```

---

# 42. Required offline M12AJ replay artifacts

Produce:

```text
26-m12aj-preserved-context-inventory

27-m12aj-offline-stage1-revalidation

28-m12aj-offline-stage2-revalidation

29-m12aj-offline-composition-revalidation

30-m12aj-offline-finalizer-replay

31-m12aj-offline-primary-direction-diagnostic

32-m12aj-offline-business-delta-diagnostic

33-m12aj-offline-new-buyer-diagnostic

34-m12aj-offline-holder-diagnostic

35-m12aj-offline-core-immutability

36-m12aj-offline-replay-decision
```

Artifact 36 must explicitly say:

```text
HARNESS_FIX_VALIDATED
NOT_A_NEW_FORMAL_MODEL_PROOF
```

---

# 43. Required deterministic tests

Produce:

```text
37-focused-test-results

38-full-local-test-results

39-ruff-and-diff-results

40-hosted-ci-portability-observation

41-new-fictional-model-call-gate
```

No new model calls until artifact 41 PASS.

---

# 44. Required NEW fictional model artifacts

Produce:

```text
42-fictional-generation-manifest

43-fictional-delta-capability-manifest

44-fictional-direction-hint-manifest

45-stage1-run1-context01

46-stage1-run1-context02

47-stage2-run1-context01

48-stage2-run1-context02

49-stage1-run2-context01

50-stage1-run2-context02

51-stage2-run2-context01

52-stage2-run2-context02

53-stage1-run3-context01

54-stage1-run3-context02

55-stage2-run3-context01

56-stage2-run3-context02

57-fictional-context-hard-semantic-audit

58-fictional-final-composition-audit

59-fictional-aggregate-finalization-audit

60-fictional-business-delta-capability-audit

61-fictional-business-delta-direction-audit

62-fictional-business-delta-materiality-audit

63-fictional-primary-direction-stability

64-fictional-new-buyer-stability

65-fictional-holder-stability

66-fictional-core-immutability-audit

67-fictional-runtime-audit

68-fictional-shadow-gate-decision
```

---

# 45. Required shadow setup artifacts

If artifact 68 authorizes shadow:

```text
69-task-start-active-monitored-universe

70-shadow-packet-inventory

71-shadow-packet-hash-manifest

72-shadow-delta-capability-manifest

73-shadow-direction-hint-manifest

74-shadow-batching-manifest

75-shadow-model-call-gate
```

---

# 46. Required full shadow artifacts

Produce:

```text
76-shadow-monolithic-model-artifacts

77-shadow-stage1-model-artifacts

78-shadow-stage2-model-artifacts

79-shadow-final-composition-artifacts

80-shadow-aggregate-finalization-audit

81-shadow-per-ticker-comparison

82-shadow-business-delta-capability-audit

83-shadow-business-delta-direction-audit

84-shadow-core-direction-differences

85-shadow-business-delta-differences

86-shadow-new-buyer-differences

87-shadow-holder-differences

88-shadow-same-direction-calibration-differences

89-shadow-expected-contract-corrections

90-shadow-potential-architecture-regressions

91-shadow-unresolved-review-required

92-shadow-financial-sector-audit

93-shadow-adr-security-basis-audit

94-shadow-cyclical-valuation-audit

95-shadow-core-immutability-audit

96-shadow-runtime-audit

97-shadow-aggregate-summary

98-shadow-architecture-decision
```

Preserve local raw model artifacts.

No remote push.

---

# 47. Required combined diagnostics

If full shadow completes:

```text
99-fic-fin-05-vs-monitored-primary-boundary-analogs

100-fic-fin-06-vs-monitored-delta-materiality-analogs

101-fic-fin-08-vs-monitored-holder-analogs

102-real-typed-delta-direction-lessons

103-combined-fictional-monitored-root-cause-summary

104-next-bounded-policy-decision
```

---

# 48. Final completion artifacts

Produce:

```text
105-finalization-repair-success-decision

106-new-fictional-proof-success-decision

107-shadow-compatibility-success-decision

108-existing-monitored-impact-summary

109-fresh-real-proof-readiness-decision

110-final-main-merge-readiness-note

111-production-no-change

112-schedule-pause-observation

113-remote-push-prohibition-audit

114-master-workflow-update

115-program-completion
```

---

# 49. Fresh-real readiness

At M12AK completion:

```text
fresh_real_proof_readiness = NOT_READY
```

even if the full fictional proof and monitored shadow complete.

Reason:

```text
M12AK's purpose is to finally produce
a formally valid full fictional proof
plus the complete existing-monitored compatibility cohort.
```

The next task should use those results
for one bounded:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

before fresh unseen proof.

Do not start fresh real calls inside M12AK.

---

# 50. Final main merge / production

Always:

```text
final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY
```

No main merge.

No deployment.

No monitoring resume.

No remote push.

---

# 51. Failure handling

## A. Offline M12AJ replay still fails after batch repair

```text
next_scope =
FICTIONAL_FINALIZATION_ARCHITECTURE_REVIEW
```

No model calls.

## B. Repair requires changing max-4 production/model schema

```text
STOP
WRONG_LAYER_REPAIR
```

Do not proceed.

## C. New fictional hard semantics fail

Do not run shadow.

Use smallest failing semantic contract.

## D. New fictional aggregate finalization fails again

```text
next_scope =
PROOF_HARNESS_FINALIZATION_REPAIR
```

No shadow.

## E. Full shadow reveals architecture regressions

```text
next_scope =
TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW
```

## F. Full shadow completes with no hard architecture regression

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

Use full fictional + monitored evidence.

---

# 52. Program-completion fields

Include at least:

```text
base_integration_head_sha

integration_branch

latest_result_zip_sha256
latest_result_integrity

m12aj_stop_reason

finalization_root_cause

finalization_contract_version

directional_core_batch_max_items

directional_core_batch_max_items_changed

context_preserving_finalization_enabled

aggregate_uses_context_model_schema

offline_m12aj_replay_status

offline_m12aj_stage1_row_count
offline_m12aj_stage2_row_count
offline_m12aj_final_composition_count

offline_m12aj_primary_direction_unstable_subject_count
offline_m12aj_business_delta_variance_subject_count
offline_m12aj_new_buyer_unstable_subject_count
offline_m12aj_holder_unstable_subject_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
business_delta_semantic_change_count
financial_semantic_change_count
two_stage_semantic_change_count

investment_judgment_model_target
investment_judgment_reasoning_effort

fictional_generation_id

fictional_stage1_model_calls
fictional_stage2_model_calls
fictional_model_calls_total

fictional_context_hard_gate_pass_count

fictional_stage1_row_count
fictional_stage2_row_count
fictional_final_composition_count

fictional_aggregate_finalization_status

fictional_business_delta_capability_violation_count
fictional_business_delta_direction_violation_count

fictional_direction_hint_projection_mismatch_count
fictional_unsafe_metric_auto_direction_count

fictional_primary_direction_unstable_subject_count
fictional_business_delta_materiality_variance_subject_count
fictional_new_buyer_unstable_subject_count
fictional_holder_unstable_subject_count

fictional_core_mutation_count

fictional_runtime_timeout_count
fictional_runtime_orphan_count
fictional_wrapper_retry_count

fictional_shadow_gate_status

task_start_active_monitor_count
task_start_active_monitor_tickers

shadow_packet_available_count
shadow_packet_unavailable_count
shadow_packet_mismatch_count

shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total

shadow_completed_ticker_count
shadow_aggregate_finalization_status

shadow_business_delta_capability_violation_count
shadow_business_delta_direction_violation_count

shadow_no_decision_material_change_count
shadow_same_direction_calibration_change_count
shadow_primary_direction_change_count
shadow_business_delta_change_count
shadow_new_buyer_change_count
shadow_holder_change_count
shadow_multi_field_change_count

shadow_expected_contract_correction_count
shadow_potential_architecture_regression_count
shadow_unresolved_review_required_count

shadow_core_mutation_after_stance_count

provider_source_fetches

production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

remote_push_count
raw_model_artifact_remote_push_count

main_branch_mutations
main_merges
deployments

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

focused_test_result
full_test_result
ruff_result
git_diff_check

two_stage_shadow_compatibility_classification

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count
```

Anything not measured:

```text
NOT_MEASURED
```

---

# 53. Artifact integrity

Freeze all reports/model artifacts before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

Do not publish the bundle to GitHub.

---

# 54. Final task principle

M12AJ's semantic repair worked at the level that matters:

```text
all 12 model contexts completed

all 24 Stage 1 rows passed

all 24 Stage 2 rows passed

business-delta capability/direction violations were zero

typed cash-conversion directions propagated correctly

core immutability held
```

The task failed because the proof harness confused:

```text
a model context batch
```

with:

```text
a full repetition aggregate.
```

The correct next flow is:

```text
keep the max-4 context schema unchanged

→ repair finalization to validate/compose per original context

→ aggregate already validated rows outside the model context schema

→ offline replay M12AJ artifacts to prove the harness repair

→ DO NOT call that replay a new formal proof

→ start a brand-new full 12-call fictional generation

→ require formal aggregate finalization PASS

→ if hard semantics pass, run the full active-monitored shadow

→ then use the completed fictional + real monitored cohort
   for the actual boundary / delta-materiality / holder policy review
```

Do NOT:

```text
widen DirectionalCoreBatch to 8

change model prompts

change typed direction semantics

change business-delta capability

reuse M12AJ model outputs as formal proof

rerun only unstable subjects

block monitored shadow merely because FIC-FIN-05/FIC-FIN-08 vary

push raw model artifacts to GitHub

merge into main

start fresh unseen proof

return to Astra

resume production monitoring
```

Fix the proof harness at the proof-harness layer.
