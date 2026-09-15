# Thesis Monitor — Real-Cohort Policy Validation Against Frozen Boundary Contracts

## 0. Task identity

Suggested work-instruction filename:

```text
20260914-real-cohort-policy-validation-against-frozen-boundary-contracts.md
```

Suggested result bundle:

```text
thesis-monitor-20260914-real-cohort-policy-validation-against-frozen-boundary-contracts-report.zip
```

Master-workflow phase:

```text
M12BK-R2 — Real-Cohort Policy Validation
           A. Freeze all previously established decision-policy contracts
           B. Apply them to the complete M12BJ monitored cohort
           C. Review ONLY cases not already explained by frozen policy
           D. Decide whether any true policy-contract exception exists
           E. If no exception: hand off to production integration/persistence review
           F. If one real exception exists: define ONE bounded policy-contract repair
```

This task replaces the broader M12BK policy re-review.

Do NOT redefine policies that were already established in earlier M12 work.

Do NOT reopen BusinessDeltaEvidenceView, holder definitions,
same-direction calibration principles, or adjacent threshold existence.

The purpose is narrower:

```text
validate that the complete real monitored cohort is explainable
under already-frozen policy contracts,

and identify only true exceptions.
```

No model calls.

No shadow calls.

No semantic-service changes.

No threshold changes.

No output forcing.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260914-converged-semantic-single-source-full-monitored-shadow-policy-handoff-report.zip
```

Verified SHA-256:

```text
67c6069e7cd8665c58db245a16e0c13da195ef3e850c79521f9f2a6a5bbbf848
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

M12BJ authoritative completion:

```text
22 monitored names complete

18 / 18 model calls complete

22 final compositions

aggregate finalization = PASS

hard semantic failures = 0

canonical bypass = 0

legacy duplicate hard-decision participation = 0

core mutation = 0

POTENTIAL_ARCHITECTURE_REGRESSION = 0
```

Freeze this.

---

# 2. Historical fresh proof — keep quarantined

Historical fresh proof remains:

```text
16 previously accepted

16 canonical BusinessDelta failures

readiness evidence used = false.
```

Do not use it in this policy validation.

Do not rerun fresh issuers here.

---

# 3. Frozen policy baseline — DO NOT REOPEN

The following policies are already established and must be treated as frozen baselines.

## 3.1 Business Delta

Freeze:

```text
BusinessDeltaEvidenceView is authoritative.

UNCHANGED_ONLY and AI_JUDGMENT remain.

Configured signal alone is not observed delta evidence.

Direction-unspecified current financial change remains possible.

No raw-text eligibility/direction re-derivation.
```

M12BJ result:

```text
monitored Business Delta differences = 0

fictional Business Delta is stable.
```

Therefore default:

```text
BUSINESS_DELTA_POLICY_NO_CHANGE_REQUIRED.
```

Do not re-study this policy.

---

## 3.2 Holder contract

Freeze the established meanings:

```text
HOLDABLE:
no material confirmed fundamental reason to reconsider.

REVIEW:
confirmed material fundamental risk exists,
but persistence / severity / reversibility remain unresolved;
exposure reduction is not uniquely justified.

REDUCE:
downside is severe/persistent enough that unchanged exposure
is no longer justified, before price/timing.
```

Also freeze:

```text
SELL does not mechanically force REDUCE.

UNCHANGED does not mechanically force REVIEW.

price / technical / supply cannot create REDUCE.
```

Do NOT redefine these enums.

Only test whether the real boundary cases comply with them.

---

## 3.3 Same-direction calibration

Freeze the existing principle:

```text
same primary direction
+
same Business Delta
+
same new-buyer stance
+
same holder stance
+
no semantic/provenance difference

with only small balance/confidence variance

→ advisory calibration variance,
not a policy failure.
```

Do NOT force exact 0.5 scores.

Do NOT reopen exact balance thresholds.

---

## 3.4 Adjacent primary boundary

Freeze the already-established fact:

```text
5.5 ↔ 6.0 can produce HOLD ↔ BUY/SELL adjacent boundary behavior.
```

Do NOT attempt to eliminate this variance.

The only question now:

```text
do the real monitored cases fit the already-known adjacent-boundary pattern
without other material decision differences?
```

---

# 4. M12BJ monitored differences — authoritative

Counts:

```text
NO_DECISION_MATERIAL_CHANGE = 8

SAME_DIRECTION_CALIBRATION_CHANGE = 5

PRIMARY_DIRECTION_CHANGE = 5

HOLDER_STANCE_CHANGE = 3

MULTI_FIELD_DECISION_CHANGE = 1

BUSINESS_DELTA_CHANGE = 0

standalone NEW_BUYER_STANCE_CHANGE = 0

POTENTIAL_ARCHITECTURE_REGRESSION = 0.
```

Only the following cases require policy validation.

---

# 5. Review question 1 — pure adjacent primary boundary

Cases:

```text
003690
010120
086280
HUT
IBM
```

Observed pattern:

```text
HOLD 5.5 ↔ BUY 6.0

or

HOLD 5.5 sell-lean ↔ SELL 6.0
```

with:

```text
Business Delta identical

new-buyer stance identical

holder stance identical

no hard semantic failure

no canonical provenance failure.
```

Task:

For each case verify exact frozen rationale/evidence and answer ONLY:

```text
Does this case fit the frozen adjacent-primary-boundary tolerance
without a material evidence-domain or stance-policy difference?
```

If yes:

```text
POLICY_TOLERATED_ADJACENT_PRIMARY_BOUNDARY
```

If no:

```text
PRIMARY_BOUNDARY_POLICY_EXCEPTION
```

Do not rederive the threshold policy itself.

---

# 6. Review question 2 — HOLDABLE ↔ REVIEW holder boundary

Cases:

```text
000660
005930
CRCL
```

Synthetic analogue:

```text
FIC-FIN-08
```

Task:

For each real case inspect exact frozen holder rationale and bound evidence.

Answer ONLY:

```text
Is the two-path difference a genuine materiality boundary
under the already-frozen HOLDABLE/REVIEW contract?
```

Specifically test:

```text
Is there a CURRENT, CONFIRMED, MATERIAL fundamental risk?

Are persistence / severity / reversibility unresolved?

Is REVIEW based only on configured/future risk?

Is REVIEW based only on unknowns?

Is either path relying on price/technical/supply?
```

Classify:

```text
POLICY_TOLERATED_HOLDER_BOUNDARY
```

or:

```text
HOLDER_POLICY_EXCEPTION
```

Do NOT redefine HOLDABLE/REVIEW/REDUCE.

---

# 7. Review question 3 — coupled primary + new-buyer boundary

Real case:

```text
SNDK
```

Synthetic analogue:

```text
FIC-FIN-05
```

Observed SNDK:

```text
monolithic:
BUY 6.0 / ATTRACTIVE

two-stage:
HOLD 5.5 / WAIT

Business Delta:
UNCHANGED both

holder:
HOLDABLE both.
```

Task:

Determine only whether:

```text
the ATTRACTIVE ↔ WAIT difference is a legitimate entry-stance consequence
of the same adjacent primary / confirmation / valuation boundary,
```

or whether:

```text
one path violates the documented new-buyer stance contract.
```

Classify:

```text
POLICY_TOLERATED_COUPLED_ENTRY_BOUNDARY
```

or:

```text
NEW_BUYER_POLICY_EXCEPTION.
```

Do NOT create a global rule:

```text
BUY → ATTRACTIVE

HOLD → WAIT

SELL → AVOID.
```

New-buyer stance remains independent.

---

# 8. Same-direction calibration — validation only

Cases:

```text
005490
012450
CORZ
MU
RXRX
```

Do NOT produce long case studies.

For each verify:

```text
primary same?

Business Delta same?

new-buyer same?

holder same?

no hard semantic/provenance difference?

only balance/confidence calibration changed?
```

Expected classification:

```text
POLICY_TOLERATED_CALIBRATION_VARIANCE.
```

If one case does not fit:

```text
CALIBRATION_POLICY_EXCEPTION.
```

Do not reopen score semantics globally.

---

# 9. No BusinessDelta review unless contradiction appears

Because:

```text
monitored delta differences = 0

fictional delta stable.
```

Produce only one compact artifact:

```text
BUSINESS_DELTA_POLICY_NO_CHANGE_REQUIRED.
```

If raw evidence unexpectedly contradicts this:

```text
STOP
M12BJ_BUSINESS_DELTA_ACCEPTANCE_REVIEW_REQUIRED.
```

Do not redesign Business Delta in this task.

---

# 10. No broad new-buyer review

Because:

```text
standalone monitored new-buyer differences = 0.
```

Review only:

```text
SNDK
FIC-FIN-05 analogue.
```

No global stance rewrite unless SNDK proves a repeatable contract defect.

---

# 11. No broad holder rewrite

Review only:

```text
000660
005930
CRCL
FIC-FIN-08 analogue.
```

Do not re-study all holder cases.

No REDUCE differences exist.

---

# 12. Raw artifact identity

Use the M12BJ frozen shadow generation:

```text
20260911-m12ai-shadow-20260914T024739Z-1fe808eba817
```

Verify raw artifact identity from the M12BJ manifests before reading.

Do not rely only on summary enums.

Do not modify raw outputs.

For fictional analogues use:

```text
M12BD generation =
20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6.
```

Verify identity.

---

# 13. Evidence standard

A case may be policy-tolerated only after checking:

```text
exact rationale

exact evidence refs

canonical semantic audit result

material anchors

risk context

unknown context

new-buyer confirmation condition

holder confirmation/invalidation condition

canonical provenance.
```

Enum values alone are insufficient.

---

# 14. Exception threshold

Do NOT classify an exception merely because outputs differ.

A true policy exception requires evidence such as:

```text
material evidence-domain difference

one path losing/creating a material current anchor

configured/future risk treated as current holder risk

new-buyer stance lacking its own valuation/confirmation rationale

a difference larger than adjacent threshold behavior

BUY ↔ SELL reversal

canonical contract inconsistency.
```

Otherwise preserve tolerance.

---

# 15. Top-level decision

Choose exactly one:

```text
REAL_COHORT_VALIDATES_FROZEN_POLICY_CONTRACTS
```

or:

```text
BOUNDED_POLICY_EXCEPTION_FOUND.
```

No vague middle state.

---

# 16. If no exception is found

Required:

```text
model_facing_policy_change_required = false

semantic_service_change_required = false

next_scope =
PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_ON_INTEGRATED_MAIN.
```

Also:

```text
fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY.
```

Do not run models.

---

# 17. If one genuine exception is found

M12BK-R2 must STOP before implementation.

Produce ONE bounded scope:

```text
BOUNDED_DECISION_POLICY_MODEL_CONTRACT_REPAIR_AND_REPROOF.
```

Specify only:

```text
exact policy contract defect

affected field(s)

affected real/synthetic examples

why existing frozen contract cannot explain them

proposed minimal contract clarification

whether prompt/schema is affected

required fictional reproof

required monitored re-shadow.
```

Do not implement the repair here.

If multiple unrelated exceptions appear:

```text
rank by decision materiality

select the smallest common root cause
or report separate bounded follow-up tasks.
```

No bundled rewrite.

---

# 18. No semantic/service changes

Required:

```text
semantic service change count = 0

model prompt semantic change count = 0

model schema semantic change count = 0

final user schema change count = 0.
```

This is an analysis task.

---

# 19. No model/network calls

Required:

```text
fictional model calls = 0

shadow model calls = 0

fresh model calls = 0

network gate attempts = 0.
```

Fully offline.

---

# 20. Required artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bk-r2-scope-freeze

04-frozen-policy-baseline

05-m12bj-shadow-identity-freeze

06-m12bd-fictional-identity-freeze

07-historical-fresh-proof-quarantine-freeze

08-real-cohort-policy-validation-input-manifest

09-primary-boundary-validation-003690

10-primary-boundary-validation-010120

11-primary-boundary-validation-086280

12-primary-boundary-validation-hut

13-primary-boundary-validation-ibm

14-holder-boundary-validation-000660

15-holder-boundary-validation-005930

16-holder-boundary-validation-crcl

17-holder-boundary-fictional-analogue-fic-fin-08

18-coupled-entry-validation-sndk

19-coupled-entry-fictional-analogue-fic-fin-05

20-calibration-validation-summary

21-business-delta-no-change-validation

22-real-cohort-policy-exception-matrix

23-real-cohort-frozen-policy-validation-decision

24-model-facing-policy-change-decision

25-next-scope-decision

26-production-integration-review-readiness

27-fresh-real-proof-readiness

28-main-merge-readiness

29-production-readiness

30-production-no-change

31-schedule-pause-observation

32-remote-push-prohibition-audit

33-master-workflow-update

34-program-completion.
```

---

# 21. Program-completion fields

Include at least:

```text
base_integration_head_sha
integration_branch
final_local_head_sha

latest_result_zip_sha256
latest_result_integrity

frozen_policy_baseline_status

primary_boundary_case_count
primary_boundary_tolerated_count
primary_boundary_exception_count

holder_boundary_case_count
holder_boundary_tolerated_count
holder_boundary_exception_count

coupled_entry_case_count
coupled_entry_tolerated_count
coupled_entry_exception_count

calibration_case_count
calibration_tolerated_count
calibration_exception_count

business_delta_policy_change_required

top_level_policy_validation_result

model_facing_policy_change_required
semantic_service_change_required

model_prompt_semantic_change_count
model_schema_semantic_change_count
semantic_service_change_count
final_user_schema_change_count

fictional_model_calls
shadow_model_calls
fresh_model_calls
network_gate_attempts

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

scheduler_mutation_count
automatic_monitoring_resume

production_integration_review_readiness

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Anything unmeasured:

```text
NOT_MEASURED.
```

---

# 22. Expected clean outcome

Expected only if raw evidence supports it:

```text
top_level_policy_validation_result =
REAL_COHORT_VALIDATES_FROZEN_POLICY_CONTRACTS

primary_boundary_exception_count = 0

holder_boundary_exception_count = 0

coupled_entry_exception_count = 0

calibration_exception_count = 0

business_delta_policy_change_required = false

model_facing_policy_change_required = false

semantic_service_change_required = false

next_scope =
PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_ON_INTEGRATED_MAIN

fresh_real_proof_readiness = NOT_READY

final_main_merge_readiness = NOT_READY

production_readiness = NOT_READY.
```

Do NOT force this outcome.

---

# 23. Failure handling

## A. Raw artifact identity unavailable

```text
STOP
POLICY_VALIDATION_RAW_ARTIFACT_IDENTITY_FAILURE.
```

## B. A supposed boundary case reveals semantic/provenance failure

```text
STOP
M12BJ_ACCEPTANCE_REVIEW_REQUIRED.
```

## C. Holder REVIEW rests only on configured/future/unknown risk

```text
holder exception found.
```

Do not tolerate.

## D. New-buyer stance is purely mechanical from primary enum

```text
coupled-entry exception found.
```

Do not tolerate automatically.

## E. All cases fit the frozen policies

Proceed to:

```text
PRODUCTION_INTEGRATION_PERSISTENCE_REVIEW_ON_INTEGRATED_MAIN.
```

No additional decision-policy research.

---

# 24. Local-only / production firewall

Required:

```text
model calls = 0

network calls = 0

provider fetches = 0

production DB mutations = 0

monitoring registrations = 0

monitoring stops = 0

assessment writes = 0

warning mutations = 0

notification writes = 0

production sends = 0

remote pushes = 0

raw model artifact pushes = 0

main branch mutations = 0

main merges = 0

deployments = 0

scheduler mutations = 0

automatic monitoring resume = 0.
```

Schedules remain paused.

---

# 25. Final task principle

The previous broad M12BK instruction risked reopening policy questions
that had already been settled in earlier M12 work.

M12BK-R2 must NOT do that.

The correct question is now:

```text
Do the real monitored cases fit the already-frozen policy contracts?
```

Review only the genuine real-cohort cases:

```text
5 adjacent primary boundaries

3 holder boundaries

1 coupled primary/new-buyer boundary

5 calibration differences.
```

Everything else is frozen.

If all cases fit:

```text
stop policy work
and proceed to production integration/persistence review.
```

If one case does not fit:

```text
identify that exact exception
and define one bounded follow-up repair.
```

Do NOT re-research policies that were already established.
