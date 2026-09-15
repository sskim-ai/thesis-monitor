# Thesis Monitor — Fictional Aggregate Context-Boundary + Readiness-Policy Alignment + Full Monitored Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260913-fictional-aggregate-context-boundary-readiness-policy-alignment-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260913-fictional-aggregate-context-boundary-readiness-policy-alignment-full-shadow-report.zip
```

Master-workflow phase:

```text
M12BC — Integrated-Main Proof-Harness Finalization Alignment
         A. Freeze successful M12BB working-capital binding architecture
         B. Reproduce exact aggregate-finalization max-4 boundary failure
         C. Preserve each 4-subject context during final audit
         D. Remove obsolete decision-stability hard gates from fictional readiness
         E. Keep objective semantic/runtime/core-immutability gates hard
         F. Re-finalize the frozen complete M12BB proof offline
         G. Reuse the frozen M12BB model proof ONLY if strict harness-only reuse conditions pass
         H. Otherwise run a NEW full fictional proof
         I. If fictional acceptance passes, run a NEW full active-monitored same-packet shadow
         J. Hand off the complete clean cohort to boundary / delta-materiality / holder policy review
```

M12BB successfully completed its intended working-capital binding repair.

The model proof itself completed:

```text
12 / 12 model calls

Stage 1 calls = 6 / 6
Stage 2 calls = 6 / 6

Stage 1 rows = 24 / 24 hard PASS
Stage 2 rows = 24 / 24 hard PASS

final compositions = 24

working-capital checkpoints = 80
grounded working-capital checkpoints = 80

working-capital grounding failures = 0
metric-specific ref mismatch = 0
narrative-only substitution = 0
irrelevant typed-ref grounding = 0
unsafe WC auto-direction = 0

core mutation = 0

timeout = 0
orphan = 0
wrapper retry = 0
```

The run did NOT fail on any model output.

It failed inside the deterministic fictional finalizer after all 12 model calls.

Exact failure:

```text
DirectionalCoreBatch candidates tuple exceeded max_length=4
during repetition-level aggregation of 8 final candidates
```

The finalizer grouped:

```text
context-01 = 4 candidates
context-02 = 4 candidates
```

into one:

```text
8-candidate DirectionalCoreBatch
```

even though:

```text
DirectionalCoreBatch.candidates max_length = 4.
```

This is a proof-harness aggregation bug.

Independent forensic also shows that the same old finalizer still treats
decision-material variance as a hard readiness failure,
contrary to the current M12 work instruction.

M12BC must repair BOTH harness issues before the monitored shadow.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260913-working-capital-checkpoint-typed-ref-binding-fictional-reproof-full-shadow-report.zip
```

Verified SHA-256:

```text
985143b6710f056df9c570a9cca2ffef80a976e33c51a7a5043a0c763ea64ace
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent archive verification:

```text
artifact_count = 767

ZIP entries =
767 indexed payloads
+ artifact-index.json
= 768

missing = 0
extra = 0

hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Recompute independently.

---

# 2. M12BB repository / provenance

Reported:

```text
integration branch =
codex/20260913-working-capital-checkpoint-binding-m12bb

base integration head =
bc2206ae7c63553035eb6864e93354e9246bd4af

frozen implementation head =
1a584d1e78d28b92a948b8f9ff0eab625ce0ef2e

final local head =
39ab9a095e7eb5ea56312bb603a7f9b928ae52b4
```

Formal generation:

```text
20260911-m12ai-fictional-20260913T074107Z-9260833a5964
```

Source lock:

```text
fe134c0770f40d48843c06f1010f44a90445a590d090cbf2b0fd1b58acbf6894
```

Model:

```text
gpt-5.6-sol / xhigh
```

---

# 3. M12BB deterministic baseline — freeze

Preserve:

```text
focused tests = 333 passed

full local tests = 3827 passed
2 dependency deprecation warnings only

ruff = PASS

git diff --check = PASS
```

M12BC must rerun tests after the harness patch.

Do not reuse these as current test proof.

---

# 4. M12BB working-capital architecture — freeze successful

M12BB selected:

```text
CLAIM_LOCAL_TYPED_REF_BINDING_WITH_MODEL_VIEW_AND_HARD_VALIDATOR
```

because conditional output-schema support was not safely available.

Preserve:

```text
working-capital-checkpoint-binding-view-v1

inventory typed-alias binding

trade-receivables typed-alias binding

trade-payables typed-alias binding where selected

generic working-capital binding

narrative refs may supplement

narrative refs may NOT substitute

claim-local hard post-model grounding validator
```

No changes.

---

# 5. Exact M12BB working-capital result — freeze

M12BB full model generation produced:

```text
working_capital_checkpoint_count = 80

grounded_working_capital_checkpoint_count = 80

working_capital_grounding_failure_count = 0

metric_specific_ref_mismatch_count = 0

narrative_only_substitution_count = 0

irrelevant_financial_ref_grounding_failure_count = 0

unsafe_wc_auto_direction_count = 0
```

These are diagnostic evidence across:

```text
24 Stage-1 cores
+
24 composed candidates.
```

Do not reopen WC grounding semantics.

---

# 6. Exact aggregate-finalization root cause

Current finalizer:

```python
final_by_run: dict[int, list[DirectionalCoreCandidate]]
```

extends both context documents into one repetition list.

For each repetition:

```text
context-01 = FIC-FIN-01..04 = 4 candidates

context-02 = FIC-FIN-05..08 = 4 candidates

combined = 8 candidates.
```

Then:

```python
batch = DirectionalCoreBatch(
    packet_id=generation_id,
    candidates=tuple(candidates),
)
```

is called.

But:

```text
DirectionalCoreBatch.candidates max_length = 4.
```

Pydantic correctly rejects the invalid aggregate batch.

Root cause:

```text
FICTIONAL_FINALIZER_AGGREGATED_BOTH_FOUR_SUBJECT_CONTEXTS
INTO_ONE_MAX_FOUR_BATCH
```

This is deterministic harness logic.

---

# 7. Preferred context-preserving finalization

Preferred repair:

```text
audit each original Stage-2 context document separately
using its original <=4 final candidates

then aggregate AUDIT ROWS
at the report layer.
```

For each:

```text
repetition 1 / context 01
repetition 1 / context 02

repetition 2 / context 01
repetition 2 / context 02

repetition 3 / context 01
repetition 3 / context 02
```

construct only:

```text
DirectionalCoreBatch size <= 4.
```

Do not reconstruct an 8-candidate `DirectionalCoreBatch`.

---

# 8. Alternative compatible aggregate container

If repository architecture already contains an explicit:

```text
context-preserving finalization helper
```

or a container that permits 8 subjects
without pretending to be a model-call `DirectionalCoreBatch`,
it may be reused.

Before adding a new helper:

```text
search the repository for prior M12AK context-preserving finalization logic.
```

Do not duplicate a canonical helper if one already exists.

Preferred principle:

```text
model-call batch type
must not be reused as a cross-context aggregate type.
```

---

# 9. Candidate identity / uniqueness

After context-preserving finalization require:

Per repetition:

```text
8 final candidates

exact ticker set =
FIC-FIN-01
FIC-FIN-02
FIC-FIN-03
FIC-FIN-04
FIC-FIN-05
FIC-FIN-06
FIC-FIN-07
FIC-FIN-08

duplicate count = 0
missing count = 0
extra count = 0.
```

Across three repetitions:

```text
24 candidates.
```

No candidate may be silently dropped due to context splitting.

---

# 10. Context ownership identity

For every final candidate retain:

```text
repetition

context number

ticker

Stage-1 source candidate hash

Stage-2 stance source hash

composition hash

core snapshot hash

post-compose core hash.
```

Do not lose context provenance after report-level aggregation.

---

# 11. Core immutability — hard

Preserve:

```text
core_snapshot_sha256
==
post_compose_core_sha256
```

for all 24 compositions.

Required:

```text
core mutation count = 0.
```

This remains a hard formal-acceptance gate.

---

# 12. Second harness defect: obsolete stability hard gates

The current finalizer still contains old readiness conditions equivalent to:

```text
direction_unstable == 0

business_unstable == 0

buyer_unstable == 0

holder_unstable == 0

FIC-FIN-05 holder == REVIEW ×3
```

These are no longer valid hard semantic acceptance rules.

Current M12 contract says:

```text
valid primary-direction variance

valid business-delta materiality variance

valid new-buyer variance

valid holder boundary variance

valid same-direction calibration variance

must be MEASURED and handed to policy review,
not converted into proof failure.
```

M12BC must align the finalizer with that contract.

---

# 13. Exact M12BB observed fictional diagnostics

Independent reconstruction from the 24 frozen final compositions:

## FIC-FIN-01

```text
overall direction:
BUY / BUY / BUY

balance:
6.0:4.0
6.5:3.5
6.5:3.5

business delta:
STRENGTHENED ×3

new buyer:
WAIT ×3

holder:
HOLDABLE ×3
```

Same-direction calibration variance only.

## FIC-FIN-02

```text
HOLD ×3
4.5:5.5 ×3

business delta:
UNRESOLVED ×3

new buyer:
WAIT ×3

holder:
REVIEW ×3
```

Stable.

## FIC-FIN-03

```text
HOLD 5:5 ×3
UNCHANGED ×3
WAIT ×3
REVIEW ×3
```

Stable.

## FIC-FIN-04

```text
HOLD 5:5 ×3
UNCHANGED ×3
WAIT ×3
HOLDABLE ×3
```

Stable.

## FIC-FIN-05

```text
overall direction:
SELL / HOLD / HOLD

balance:
4.0:6.0
4.5:5.5
4.5:5.5

business delta:
UNCHANGED ×3

new buyer:
AVOID / WAIT / WAIT

holder:
REVIEW ×3
```

This is a genuine primary-threshold + new-buyer boundary diagnostic.

It is NOT an objective semantic failure.

## FIC-FIN-06

```text
HOLD 5.5:4.5 ×3

business delta:
STRENGTHENED ×3

new buyer:
WAIT ×3

holder:
HOLDABLE ×3
```

Stable.

## FIC-FIN-07

```text
HOLD 5:5 ×3
UNCHANGED ×3
WAIT ×3
HOLDABLE ×3
```

Stable.

## FIC-FIN-08

```text
HOLD 5:5 ×3
UNCHANGED ×3
WAIT ×3
REVIEW ×3
```

Stable.

---

# 14. Observed stability diagnostic counts

From the frozen M12BB generation:

```text
primary-direction unstable subject count = 1
  FIC-FIN-05

business-delta unstable subject count = 0

new-buyer unstable subject count = 1
  FIC-FIN-05

holder unstable subject count = 0

same-direction/calibration variable subjects include:
FIC-FIN-01
FIC-FIN-05.
```

These values must be reproduced by the repaired finalizer.

They are diagnostics.

They must NOT block formal fictional acceptance.

---

# 15. Stability reports must become diagnostic

Current old reports include:

```text
full-stage1-core-stability

full-stage2-new-buyer-stability

full-stage2-holder-stability

full-final-decision-material-stability
```

Do not emit:

```text
FAIL
```

merely because a subject varies across repetitions.

Preferred statuses:

```text
MEASURED

PASS_WITH_VARIANCE

DIAGNOSTIC_VARIANCE
```

according to repository conventions.

The report must include:

```text
unstable_subject_count

subject values

readiness_blocking = false.
```

---

# 16. Business-delta audit must separate semantics from stability

Current old report logic effectively says:

```text
business delta audit PASS only if:
all semantic validators PASS
AND
business_unstable == 0.
```

Replace with:

```text
hard semantic audit:
all BusinessDeltaEvidenceView / post-model validations PASS

diagnostic:
business-delta repetition variance measured separately.
```

A valid `WEAKENED / UNRESOLVED` materiality boundary,
for example,
must not be converted into semantic failure.

For M12BB:

```text
business delta happens to be stable across all 8 subjects.
```

But the architecture must still be correct for future genuine variance.

---

# 17. Holder target must not be hard-coded into readiness

The old finalizer contains a special exact target:

```text
FIC-FIN-05 holder == REVIEW ×3
```

M12BB does satisfy it.

However this should not be a generic formal readiness gate.

Holder stance is governed by the holder contracts
and objective stance validators.

Expected fixture outcomes may be diagnostic controls,
but genuine `HOLDABLE ↔ REVIEW` boundary ambiguity
must not automatically invalidate a semantically valid proof.

Remove this special hard-coded readiness dependency.

If a dedicated negative/positive holder fixture has a hard semantic contract,
validate THAT contract directly rather than hard-coding one final enum sequence.

---

# 18. Formal fictional acceptance — hard gates only

After M12BC, fictional readiness should depend on objective hard gates such as:

```text
Stage-1 row count = 24

Stage-2 row count = 24

final composition count = 24

Stage-1 hard semantic errors = 0

Stage-2 hard semantic errors = 0

final candidate hard semantic errors = 0

invalid evidence refs = 0

core mutation = 0

configured-signal current-driver violation = 0

configured-signal false fulfillment = 0

working-capital grounding failure = 0

WC metric-specific mismatch = 0

WC narrative substitution = 0

unsafe WC auto-direction = 0

FCF semantic hard failure = 0

financial-sector hard failure = 0

business-delta hard semantic failure = 0

market-expectation hard semantic failure = 0

Stage-2 contamination = 0

runtime calls = 12 / 12

timeout = 0

orphan = 0

wrapper retry = 0

model target/effort match = true.
```

Do NOT include repetition stability as a hard gate.

---

# 19. Decision-material variance — diagnostic only

Formal output must separately report:

```text
primary_direction_unstable_subject_count

business_delta_unstable_subject_count

new_buyer_unstable_subject_count

holder_unstable_subject_count

same_direction_calibration_variance_subject_count.
```

Also report subject-level values.

Set:

```text
readiness_blocking = false
```

for these diagnostics.

They feed:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

---

# 20. Frozen M12BB proof replay before new model calls

M12BC must first repair the harness,
then run the repaired finalizer OFFLINE against
the exact frozen M12BB generation.

No model call.

Require immutable provenance:

```text
generation_id =
20260911-m12ai-fictional-20260913T074107Z-9260833a5964

source_lock_sha256 =
fe134c0770f40d48843c06f1010f44a90445a590d090cbf2b0fd1b58acbf6894

Stage-1 documents = 6

Stage-2 documents = 6

Stage-1 outputs/receipts unchanged

Stage-2 outputs/receipts unchanged

all prompt hashes unchanged

all schema hashes unchanged

all output hashes unchanged.
```

Do not edit candidates.

---

# 21. Frozen M12BB offline re-finalization acceptance

The repaired finalizer must produce:

```text
Stage-1 hard semantic rows = 24 / 24 PASS

Stage-2 hard semantic rows = 24 / 24 PASS

final composition rows = 24 / 24 hard PASS

context-preserving final-audit rows = 24

core mutation = 0

WC checkpoints = 80

grounded WC checkpoints = 80

WC grounding failure = 0

metric-specific WC mismatch = 0

narrative-only substitution = 0

unsafe WC auto-direction = 0

runtime receipts = 12 / 12 PASS

aggregate finalization = PASS.
```

Expected diagnostic variance:

```text
primary unstable = 1
new-buyer unstable = 1
business delta unstable = 0
holder unstable = 0

FIC-FIN-05:
SELL / HOLD / HOLD
AVOID / WAIT / WAIT.
```

These diagnostics do NOT invalidate the proof.

---

# 22. Harness-only proof reuse decision

Because:

```text
all 12 M12BB model calls completed

all Stage-1 and Stage-2 rows passed

all 24 compositions exist

the repair is deterministic finalizer/readiness logic only
```

M12BC may authorize reuse of the frozen M12BB model proof
WITHOUT another 12 model calls,
but ONLY if ALL of the following are proven:

```text
model prompt semantic hash change = 0

model schema semantic hash change = 0

working-capital binding view semantic change = 0

configured-signal view semantic change = 0

configured financial support concept semantic change = 0

BusinessDeltaEvidenceView semantic change = 0

MarketExpectationEvidenceView semantic change = 0

financial evidence projection semantic change = 0

Stage-1/Stage-2 ownership semantic change = 0

only finalizer/readiness/reporting harness changed

frozen-output offline re-finalization = PASS

all frozen receipts/hashes/provenance = intact.
```

Then set:

```text
formal_fictional_reuse_status =
REUSE_AUTHORIZED_AFTER_HARNESS_ONLY_REFINALIZATION
```

and:

```text
new_fictional_model_calls = 0.
```

This is preferred because the model proof itself already completed cleanly.

---

# 23. Fallback: new full fictional proof

If ANY reuse condition in Section 22 fails:

```text
formal_fictional_reuse_status =
NEW_FORMAL_PROOF_REQUIRED
```

Then run:

```text
NEW generation ID

gpt-5.6-sol / xhigh

Stage 1 = 6 calls
Stage 2 = 6 calls
total = 12

24 Stage-1 rows
24 Stage-2 rows
24 compositions.
```

No selective rerun.

No stitching.

No judge/fallback.

The new proof must use the repaired context-preserving finalizer.

---

# 24. Do NOT force FIC-FIN-05 stability

Whether replaying frozen M12BB
or running a new formal proof:

Do NOT add prompt/schema/validator logic to force:

```text
FIC-FIN-05 SELL

or

FIC-FIN-05 HOLD

or

new-buyer AVOID/WAIT exact ratio.
```

This remains the primary boundary subject for later policy review.

No resolver.

No post-hoc score override.

No exact ratio target.

---

# 25. Do NOT force exact calibration

FIC-FIN-01 currently varies:

```text
BUY 6.0
BUY 6.5
BUY 6.5.
```

This is same-direction calibration variance.

Keep diagnostic.

Do not force exact balance/confidence
unless a future policy task explicitly justifies it.

---

# 26. Fictional-readiness report redesign

Required sections:

```text
hard_semantic_acceptance

runtime_acceptance

core_immutability

context_boundary_integrity

decision_material_variance_diagnostics

same_direction_calibration_diagnostics

formal_reuse_or_new_proof_decision.
```

The top-level readiness should be:

```text
PASS
```

when all objective hard gates pass,
even if decision variance diagnostics are nonzero.

---

# 27. Shadow authorization

If either:

```text
formal_fictional_reuse_status =
REUSE_AUTHORIZED_AFTER_HARNESS_ONLY_REFINALIZATION
```

or:

```text
NEW formal fictional proof = PASS
```

then authorize:

```text
NEW full active-monitored same-packet shadow.
```

Do NOT resume any prior partial shadow.

---

# 28. Active monitored universe

Re-enumerate active monitored stocks read-only at shadow start.

Last verified reference:

```text
22 active names
```

Use actual task-start list.

No registration / stop mutation.

---

# 29. Same-packet shadow contract

For every active ticker:

```text
one reproducible local frozen packet

same packet hash feeds:
monolithic
Stage 1
Stage 2.
```

No provider refresh.

Required:

```text
provider_source_fetches = 0.
```

---

# 30. Shadow topology

For N active names:

```text
context_count = ceil(N / 4)

monolithic calls = context_count

Stage 1 calls = context_count

Stage 2 calls = context_count

total = 3 × context_count.
```

At N=22:

```text
18 calls.
```

No repetitions.

No fresh unseen issuers.

---

# 31. Shadow hard-stop policy

Hard stop only for objective failures:

```text
runtime/schema failure

manifest/hash mismatch

packet mismatch

invalid evidence identity

working-capital grounding failure

WC metric-specific ref mismatch

WC narrative substitution

unsafe WC auto-direction

configured-signal field-use violation

configured-signal false fulfillment

FCF hard semantic violation

financial-sector hard semantic violation

business-delta hard semantic violation

market-expectation hard semantic violation

Stage-2 contamination

ADR/security-basis failure

core mutation

production-side-effect attempt

aggregate finalization failure.
```

Do NOT hard-stop because:

```text
monolithic and two-stage primary directions differ

business delta differs

new-buyer stance differs

holder stance differs

same-direction calibration differs.
```

Those are compatibility diagnostics.

---

# 32. Shadow comparison taxonomy

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

OTHER_REVIEW_REQUIRED.
```

Neither monolithic nor two-stage is automatically ground truth.

---

# 33. Potential architecture regression criteria

A decision difference becomes:

```text
POTENTIAL_ARCHITECTURE_REGRESSION
```

only when objective evidence supports that classification,
for example:

```text
hard semantic validator failure

lost material anchor domain

invalid evidence ref

forbidden configured-signal use

financial grounding failure

Stage-2 core mutation

price/timing contamination

sector-framework misuse.
```

A plain:

```text
HOLD vs SELL
WAIT vs AVOID
HOLDABLE vs REVIEW
```

difference without objective violation is not automatically a regression.

---

# 34. Full shadow acceptance

Require:

```text
all planned calls complete

all active tickers represented exactly once

packet mismatch = 0

all monolithic hard semantic audits PASS

all Stage-1 hard semantic audits PASS

all Stage-2 hard semantic audits PASS

all final compositions PASS

core mutation = 0

WC grounding failure = 0

WC metric mismatch = 0

narrative substitution = 0

unsafe WC auto-direction = 0

configured-signal violations = 0

FCF hard failures = 0

financial-sector hard failures = 0

business-delta hard failures = 0

expectation hard failures = 0

Stage-2 contamination = 0

ADR/security-basis failure = 0

timeout = 0

orphan = 0

wrapper retry = 0

production side effects = 0

aggregate finalization PASS.
```

Decision-material comparison counts may be nonzero.

---

# 35. Shadow WC checkpoint audit

Preserve M12BB contract.

For every candidate with selected typed WC evidence report:

```text
ticker

checkpoint field

claim text

metric cue

required typed aliases

actual claim refs

typed refs directly bound

narrative refs directly bound

claim grounded

metric-specific mismatch

validation result.
```

Required:

```text
narrative-only substitution = 0

metric-specific mismatch = 0.
```

---

# 36. Shadow FCF / financial-sector / configured-signal audits

Preserve all current contracts:

```text
M12AZ FCF local temporal scope

M12AY configured FCF support

M12BA replacement-verb parity

M12AT configured-signal field ownership

M12AP expectation independence

M12AO business-delta evidence view.
```

No changes.

---

# 37. Current policy handoff — important

The old M12AE final program code may attempt:

```text
fresh real unseen proof
```

immediately after a clean fictional + monitored shadow.

That is NOT the current workflow.

M12BC must override the stale handoff.

If the full shadow is clean:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY

next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

Do NOT authorize fresh unseen proof in M12BC.

---

# 38. Why policy review comes next

After a clean complete cohort,
the remaining questions are no longer objective parser/grounding defects.

They include:

```text
adjacent HOLD ↔ BUY/SELL threshold behavior

FIC-FIN-05 SELL/HOLD boundary

new-buyer AVOID/WAIT coupling

business-delta materiality boundaries

holder HOLDABLE/REVIEW boundaries

same-direction calibration variance.
```

These require an explicit policy review,
not more ad-hoc semantic validators.

---

# 39. Policy-review inputs to preserve

If shadow completes,
produce combined diagnostics using:

```text
formal fictional result
+
complete monitored compatibility cohort.
```

At minimum retain:

```text
FIC-FIN-05 primary boundary

FIC-FIN-02 delta behavior

FIC-FIN-06 delta + WC behavior

FIC-FIN-08 holder behavior

real monitored primary differences

real monitored delta differences

real monitored new-buyer differences

real monitored holder differences

same-direction calibration differences.
```

Do not resolve them inside M12BC.

---

# 40. No model-facing semantic change preferred

M12BC should be:

```text
proof-harness/finalizer/readiness-policy only.
```

Required expected values:

```text
model_prompt_semantic_change_count = 0

model_schema_semantic_change_count = 0

working_capital_checkpoint_binding_view_change_count = 0

configured_signal_view_change_count = 0

configured_financial_support_concept_change_count = 0

business_delta_view_change_count = 0

expectation_view_change_count = 0

financial_evidence_projection_change_count = 0

two_stage_semantic_change_count = 0

final_user_schema_change_count = 0.
```

If any model-facing semantic surface changes:

```text
formal proof reuse prohibited

NEW_FORMAL_PROOF_REQUIRED.
```

---

# 41. Deterministic harness fixtures

Add tests for:

## FINAL-BATCH-P01

```text
2 contexts × 4 candidates

finalizer audits as:
4 + 4

report aggregate:
8

PASS.
```

## FINAL-BATCH-P02

```text
3 repetitions × 2 contexts × 4 candidates

24 final candidates

all unique
all audited exactly once

PASS.
```

## FINAL-BATCH-N01

```text
attempt to instantiate 8-candidate DirectionalCoreBatch

expected:
test prevents this code path.
```

## FINAL-BATCH-N02

```text
missing context candidate

expected:
FAIL.
```

## FINAL-BATCH-N03

```text
duplicate ticker within repetition

expected:
FAIL.
```

---

# 42. Readiness-policy fixtures

## READINESS-P01

```text
all hard semantics PASS
primary variance = 1
new-buyer variance = 1

expected:
formal fictional readiness PASS
variance reports MEASURED.
```

## READINESS-P02

```text
same-direction calibration variance only

expected:
PASS.
```

## READINESS-P03

```text
holder HOLDABLE/REVIEW variance
all holder semantic contracts valid

expected:
PASS + diagnostic variance.
```

## READINESS-N01

```text
one hard semantic error

expected:
FAIL.
```

## READINESS-N02

```text
core mutation = 1

expected:
FAIL.
```

## READINESS-N03

```text
invalid evidence ref = 1

expected:
FAIL.
```

No decision enum is a substitute for hard semantic validation.

---

# 43. M12BB frozen-output offline re-finalization artifact set

Produce:

```text
01-m12bb-frozen-generation-provenance

02-m12bb-frozen-receipt-hash-manifest

03-m12bb-frozen-output-hash-manifest

04-m12bb-context-boundary-manifest

05-m12bb-context-preserving-final-audit

06-m12bb-stage1-hard-semantic-summary

07-m12bb-stage2-hard-semantic-summary

08-m12bb-final-composition-hard-semantic-summary

09-m12bb-core-immutability-replay

10-m12bb-wc-grounding-replay

11-m12bb-decision-variance-diagnostics

12-m12bb-runtime-replay

13-m12bb-offline-refinalization-decision.
```

---

# 44. Required finalizer-repair artifacts

Produce:

```text
14-finalizer-code-path-audit

15-directional-core-batch-boundary-contract

16-context-preserving-finalization-contract

17-final-candidate-identity-contract

18-hard-vs-diagnostic-readiness-contract

19-fictional-stability-report-policy-contract

20-business-delta-semantic-vs-stability-separation-contract

21-holder-hardcode-removal-contract

22-current-workflow-handoff-contract

23-finalizer-repair-decision.
```

---

# 45. Required deterministic tests

Produce:

```text
24-finalizer-context-boundary-tests

25-readiness-policy-tests

26-frozen-output-refinalization-tests

27-focused-test-results

28-full-local-test-results

29-ruff-and-diff-results

30-hosted-ci-portability-observation.
```

No shadow calls before all hard deterministic gates pass.

---

# 46. Formal reuse gate

Produce:

```text
31-model-facing-semantic-hash-freeze

32-proof-harness-only-diff-audit

33-formal-fictional-reuse-decision.
```

Artifact 33 must be exactly one:

```text
REUSE_AUTHORIZED_AFTER_HARNESS_ONLY_REFINALIZATION
```

or:

```text
NEW_FORMAL_PROOF_REQUIRED.
```

No ambiguous value.

---

# 47. If new formal proof is required

Produce the normal full artifacts for:

```text
NEW 12-call generation

24 Stage-1 rows

24 Stage-2 rows

24 compositions

context-preserving finalization

hard semantic acceptance

variance diagnostics.
```

Do not require decision stability.

---

# 48. Shadow setup artifacts

After fictional acceptance produce:

```text
task-start-active-monitored-universe

shadow-packet-inventory

shadow-packet-hash-manifest

shadow-wc-binding-view-manifest

shadow-configured-signal-view-manifest

shadow-configured-financial-support-concept-manifest

shadow-delta-view-manifest

shadow-expectation-view-manifest

shadow-frozen-context-manifest

shadow-batching-manifest

shadow-model-call-gate.
```

---

# 49. Full shadow artifacts

Produce:

```text
shadow-monolithic-model-artifacts

shadow-stage1-model-artifacts

shadow-stage2-model-artifacts

shadow-context-hard-semantic-audit

shadow-wc-checkpoint-binding-audit

shadow-financial-grounding-audit

shadow-configured-signal-field-use-audit

shadow-fcf-local-temporal-scope-audit

shadow-business-delta-audit

shadow-market-expectation-audit

shadow-financial-sector-audit

shadow-stage2-language-audit

shadow-final-composition-audit

shadow-aggregate-finalization-audit

shadow-per-ticker-comparison

shadow-core-direction-differences

shadow-business-delta-differences

shadow-new-buyer-differences

shadow-holder-differences

shadow-same-direction-calibration-differences

shadow-expected-contract-corrections

shadow-potential-architecture-regressions

shadow-unresolved-review-required

shadow-adr-security-basis-audit

shadow-cyclical-valuation-audit

shadow-core-immutability-audit

shadow-runtime-audit

shadow-aggregate-summary

shadow-architecture-decision.
```

---

# 50. Required combined policy-handoff diagnostics

If shadow completes:

```text
fictional-primary-boundary-summary

fictional-delta-materiality-summary

fictional-new-buyer-boundary-summary

fictional-holder-boundary-summary

monitored-primary-difference-summary

monitored-delta-difference-summary

monitored-new-buyer-difference-summary

monitored-holder-difference-summary

same-direction-calibration-summary

combined-fictional-monitored-policy-input

next-bounded-policy-decision.
```

---

# 51. Local-only / production firewall

M12BC is LOCAL-ONLY.

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

automatic_monitoring_resume = 0.
```

Monitoring schedules remain paused.

Do not request GitHub push authorization.

---

# 52. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch
final_local_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bb_generation_id
m12bb_source_lock_sha256

m12bb_model_calls
m12bb_stage1_rows
m12bb_stage2_rows
m12bb_final_composition_count

aggregate_finalizer_root_cause

context_preserving_finalization_contract_version

repetition_context_count
max_batch_candidate_count
cross_context_model_batch_construction_count

final_candidate_duplicate_count
final_candidate_missing_count
final_candidate_extra_count

m12bb_offline_refinalization_status

m12bb_hard_semantic_failure_count
m12bb_core_mutation_count

m12bb_wc_checkpoint_count
m12bb_grounded_wc_checkpoint_count
m12bb_wc_grounding_failure_count
m12bb_metric_specific_ref_mismatch_count
m12bb_narrative_only_substitution_count
m12bb_unsafe_wc_auto_direction_count

m12bb_primary_direction_unstable_subject_count
m12bb_business_delta_unstable_subject_count
m12bb_new_buyer_unstable_subject_count
m12bb_holder_unstable_subject_count
m12bb_same_direction_calibration_variance_subject_count

m12bb_fic_fin_05_direction_values
m12bb_fic_fin_05_new_buyer_values
m12bb_fic_fin_05_holder_values

decision_variance_readiness_blocking

holder_exact_enum_readiness_hardcode_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
working_capital_checkpoint_binding_view_change_count
configured_signal_view_change_count
configured_financial_support_concept_change_count
business_delta_view_change_count
expectation_view_change_count
financial_evidence_projection_change_count
two_stage_semantic_change_count
final_user_schema_change_count

formal_fictional_reuse_status
new_fictional_model_calls

fictional_generation_id
fictional_model_calls_total
fictional_stage1_row_count
fictional_stage2_row_count
fictional_final_composition_count
fictional_aggregate_finalization_status
fictional_hard_semantic_failure_count
fictional_core_mutation_count

fictional_primary_direction_unstable_subject_count
fictional_business_delta_unstable_subject_count
fictional_new_buyer_unstable_subject_count
fictional_holder_unstable_subject_count
fictional_same_direction_calibration_variance_subject_count

task_start_active_monitor_count
task_start_active_monitor_tickers

shadow_generation_id
shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total

shadow_completed_ticker_count
shadow_final_composition_count
shadow_aggregate_finalization_status

shadow_hard_semantic_failure_count
shadow_core_mutation_after_stance_count

shadow_wc_checkpoint_count
shadow_grounded_wc_checkpoint_count
shadow_wc_grounding_failure_count
shadow_metric_specific_ref_mismatch_count
shadow_narrative_only_substitution_count
shadow_unsafe_wc_auto_direction_count

shadow_configured_signal_field_violation_count
shadow_configured_signal_false_fulfillment_count

shadow_fcf_hard_failure_count
shadow_business_delta_hard_failure_count
shadow_expectation_hard_failure_count
shadow_financial_sector_hard_failure_count
shadow_stage2_language_false_positive_count

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

shadow_timeout_count
shadow_orphan_count
shadow_wrapper_retry_count

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

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Anything not measured:

```text
NOT_MEASURED.
```

---

# 53. Required completion state if clean

If:

```text
fictional acceptance = PASS

and

full monitored shadow = PASS
```

then M12BC completion must say:

```text
two_stage_shadow_compatibility_classification =
COMPLETE_WITH_POLICY_DIAGNOSTICS
```

or equivalent.

And:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY

next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

Do not jump to fresh unseen proof.

---

# 54. Failure handling

## A. Context-preserving finalizer still attempts 8-candidate DirectionalCoreBatch

```text
STOP
FICTIONAL_CONTEXT_BOUNDARY_REPAIR_FAILED.
```

## B. Frozen M12BB hard semantic replay finds a real failure

```text
formal_fictional_reuse_status =
NEW_FORMAL_PROOF_REQUIRED.
```

Do not hide it.

## C. Model-facing semantic hashes changed

```text
formal_fictional_reuse_status =
NEW_FORMAL_PROOF_REQUIRED.
```

Run a fresh full 12-call proof.

## D. Repaired finalizer still blocks only because FIC-FIN-05 differs across repetitions

```text
STOP
OBSOLETE_DECISION_STABILITY_GATE_REMAINS.
```

Do not modify FIC-FIN-05 outputs.

## E. Repaired finalizer ignores a hard semantic error

```text
STOP
READINESS_POLICY_TOO_PERMISSIVE.
```

## F. Full shadow reveals objective architecture regression

Use the smallest bounded architecture-review scope.

Do not jump to policy review.

## G. Full shadow completes cleanly

Expected:

```text
next_scope =
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

---

# 55. Artifact integrity

Freeze all local artifacts before final artifact index.

Required:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Report final ZIP SHA-256.

Do not push report/raw artifacts to GitHub.

---

# 56. Final task principle

M12BB produced the first complete 12-call model proof
under the new working-capital binding architecture:

```text
12/12 model calls passed

24/24 Stage-1 rows passed

24/24 Stage-2 rows passed

24 final compositions exist

80/80 WC checkpoints are directly grounded.
```

The run is blocked because the finalizer does two outdated things:

```text
1. merges two four-subject contexts into one
   eight-candidate batch whose schema max is four;

2. treats genuine decision-boundary variance as
   proof failure instead of policy-review input.
```

The correct M12BC flow is:

```text
preserve model-facing semantics

→ preserve each original four-subject context during final audit

→ aggregate only audit rows / diagnostics across contexts

→ keep all objective semantic and runtime gates hard

→ make primary/delta/new-buyer/holder/calibration variance diagnostic-only

→ remove hard-coded FIC-FIN-05 exact stance requirement from readiness

→ offline re-finalize the complete frozen M12BB proof

→ if the change is truly harness-only and all frozen proof data remain clean,
   authorize reuse WITHOUT wasting 12 new model calls

→ otherwise run a NEW full 12-call proof

→ after fictional acceptance,
   run a completely NEW full 22-name monitored shadow

→ if the shadow is objectively clean,
   DO NOT jump to fresh unseen proof

→ hand the full evidence set to:
   DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN.
```

Do NOT:

```text
change model prompts to force stability

force FIC-FIN-05 to SELL or HOLD

force AVOID or WAIT

force exact 0.5 calibration

candidate-edit frozen M12BB outputs

candidate-globalize WC grounding

reopen WC binding semantics

reopen FCF semantics

reopen financial-sector replacement semantics

reopen configured-signal field ownership

reopen BusinessDeltaEvidenceView

reopen MarketExpectationEvidenceView

resume any partial shadow

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume production monitoring.
```

A proof harness must preserve the model-call batch boundary,
and genuine decision-boundary variance belongs in policy diagnostics,
not in schema-validity or semantic-validity failure.
