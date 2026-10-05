# Thesis Monitor — REV58A Fresh-Shadow Prerequisite Repair

## 0. Task identity

Work-instruction filename:

`rev58a-work.md`

Work-instruction ZIP:

`rev58a-work.zip`

Required result bundle:

`rev58a-result.zip`

Required result sidecar:

`rev58a-result.zip.sha256`

This is a bounded **fresh-shadow prerequisite implementation repair + offline parity proof** task.

It exists only to close the two P1 implementation gaps proven by REVISED REV58:

1. upstream local semantic-validator rejection is currently retried by the scoped US/KR controller;
2. exact feature HEAD consumes `REV56COfflineCoverageReproofV1` but has no fresh-source, generation-bound producer for that coverage receipt.

It is NOT:

- a fresh source collection task;
- a current-data shadow execution;
- a B2 v2 model execution;
- an upstream Core / Pass A / Pass B live execution;
- a B2 v2 policy redesign;
- a prompt/schema/economic-threshold tuning task;
- a blind-label task;
- a production deployment;
- a scheduler / Telegram / production DB task;
- a final strict blind task.

Success means only:

> the exact current code can satisfy REVISED REV58's retry and pre-model owner-coverage prerequisites offline, without changing B2 v2 semantics, and a new REV58 fresh-shadow run may be attempted separately.

---

# 1. Authoritative predecessor

Immediate predecessor:

`rev58-result.zip`

Expected SHA-256:

`0e5cdb97ff55a517043f85e68b35d01b12b5e0d9f4342989a6375f11807de9e2`

Expected terminal:

`R2B_R9_REV58_IMPLEMENTATION_REPAIR_REQUIRED`

Expected REV58 facts:

```text
feature HEAD =
f26b69fd00d3e31764ac67e9f7c598c8b429f129

origin/main =
9b134350cd05c127b6dc866d34a477d95c54785c

protected operating HEAD =
b610e6de0a8c33d199961e821ff1b130e1fa9ad4

REV57A integrity = PASS
B2 v2 default-OFF = PASS

new current generation created = false
source/provider calls = 0
model calls = 0
Alpha Vantage calls = 0

source collection = NOT_STARTED
fresh upstream execution = NOT_STARTED
B2 v2 fresh execution = NOT_STARTED

tracked repository changes = 0
new commits = 0
feature push = 0
production DB/WAL writes = 0
official monitored-record writes = 0
Telegram = 0
scheduler mutation = 0
deploy = 0
restart = 0
operating mutation = 0

final strict blind readiness = NOT_READY
```

Expected implementation blockers:

```text
UPSTREAM_SEMANTIC_RETRY_BOUNDARY
FRESH_PRE_MODEL_COVERAGE_COMPOSITION
```

Do not reinterpret REV58 as a provider or model failure.
No fresh behavior was measured.

---

# 2. Repository identity

Start from exact code HEAD:

`f26b69fd00d3e31764ac67e9f7c598c8b429f129`

Suggested repair branch:

`codex/r2b-r9-rev58a-fresh-shadow-prereq-repair`

Before edits:

1. prove exact parent commit;
2. prove `origin/main` separately;
3. prove clean worktree;
4. snapshot protected operating checkout;
5. prove B2 v2 remains default-OFF;
6. prove no production caller imports/activates B2 v2.

Do not branch from main and claim equivalence.
Do not rebase.
Do not force-push.
Do not modify the protected operating checkout.

Identity failure:

`R2B_R9_REV58A_REPOSITORY_IDENTITY_GAP`

---

# 3. Verify immutable REV58 result first

Before implementation verify:

- sidecar SHA;
- ZIP CRC;
- manifest membership;
- member bytes and SHA;
- no missing/extras;
- exact REVISED REV58 work-instruction identity;
- expected terminal;
- expected two blockers;
- source/model/provider calls = 0;
- repository identities;
- protected state unchanged.

Required artifact:

`rev58-integrity.json`

Mismatch:

`R2B_R9_REV58A_REV58_INTEGRITY_GAP`

---

# 4. Repair scope A — semantic retry boundary

## Current proven defect

REV58 reproduced on exact code:

```text
scripts/us14_models.py::Us14Execution.bounded
```

which is reused by:

```text
scripts/rev46_kr_models.py::Rev46Kr8Execution
```

Current loop retries any post-invocation exception except `SystemicFailure`.

The existing semantic-receipt path writes a local validation FAIL and raises a generic `BatchFailure`.

Therefore:

```text
provider-schema-valid
+ local semantic validator FAIL
```

is currently retried up to three physical invocations.

REV58 synthetic reproduction proved:

```text
US LOCAL_SEMANTIC invocations = 3
KR LOCAL_SEMANTIC invocations = 3
```

Required REVISED REV58 behavior:

```text
LOCAL_SEMANTIC invocations = 1
```

No source/model call occurred in the proof.

---

# 5. Typed failure classification

Implement an explicit failure taxonomy that distinguishes at least:

```text
TRANSPORT_OR_RESPONSE_FORM_FAILURE
LOCAL_SEMANTIC_VALIDATION_FAILURE
SYSTEMIC_FAILURE
```

The implementation may use typed exceptions, typed receipt fields, or an equivalent deterministic mechanism.

Requirements:

## TRANSPORT_OR_RESPONSE_FORM_FAILURE

Retry eligible under the existing bounded retry policy.

Examples:

- transport/API failure;
- timeout;
- permitted transient provider failure;
- no durable response;
- malformed structured response;
- provider response-schema failure before a semantically valid local object exists.

## LOCAL_SEMANTIC_VALIDATION_FAILURE

Non-retryable.

Examples:

- provider response schema already passed;
- local Pass A semantic validator rejects;
- local Pass B policy/semantic validator rejects;
- exact authority/ref/branch validator rejects.

Required:

```text
raw/response receipt preserved
semantic failure receipt preserved
attempt count stops at 1
no second sampling of the same logical request
```

## SYSTEMIC_FAILURE

Remain immediate fail-stop.

Do not broaden transport retry.
Do not convert semantic rejection into Systemic merely to satisfy the test.
Preserve truthful failure class.

---

# 6. Raw-first invariant for upstream calls

The repaired controller must preserve raw-first behavior.

Before local semantic validation can reject an attempt, the durable raw/provider response receipt must already exist and be SHA-bound.

Required attempt receipt fields:

```text
stage
market
batch
subjects
logical_request_id
attempt
request_sha256
raw_response_sha256
provider_schema_status
local_semantic_status
failure_class
retry_eligible
retry_reason
```

Do not lose rejected attempts.

---

# 7. Retry compatibility tests

Add deterministic tests for both US and KR scoped controllers.

Minimum cases:

### A. Transport failure

Expected:

```text
retry eligible
up to MAX_RETRIES + 1 attempts
```

### B. Provider response-form/schema failure

Expected:

retry eligible under existing contract.

### C. Local semantic rejection

Expected:

```text
attempts = 1
retry_eligible = false
```

### D. Systemic failure

Expected:

```text
attempts = 1
immediate raise/stop
```

### E. Successful request

Expected:

```text
attempts = 1
PASS
```

### F. Semantic fail after a prior transport retry

Example:

```text
attempt 1 = transport failure
attempt 2 = provider-schema-valid + local semantic reject
```

Expected:

stop after attempt 2.
No attempt 3.

The retry repair must apply equally to US14 and KR8 because KR reuses the bounded method.

---

# 8. Preserve unrelated controller semantics

Do not change:

- model;
- effort;
- timeout;
- provider transport;
- prompt;
- schema;
- batch topology;
- source routing;
- 0.6 s Kiwoom pacing;
- KIS pacing;
- B2 v2 retry policy;
- economic decision rules.

The repair target is only retry eligibility after a response reaches local semantic validation.

---

# 9. Repair scope B — fresh pre-model coverage producer

## Current proven defect

Exact HEAD currently consumes:

`REV56COfflineCoverageReproofV1`

through B2 v2 policy validation.

But exact tracked runtime code has no app/scripts producer that can build this receipt from a newly collected source generation.

Historical report-only implementations depend on frozen lineage such as:

- REV55 requests/outputs;
- REV50 lineage;
- REV47 KIS inputs;
- frozen Core/A/B subject contexts;
- hard-coded historical baseline reproduction.

The fictional one-subject test fixture is not a source owner.

REVISED REV58 requires fresh owner coverage:

```text
after fresh source collection seal
before fresh upstream model execution
```

Therefore historical accepted model outputs cannot be inputs to the current coverage producer.

---

# 10. Implement a parameterized fresh-source coverage composer

Expose a tracked runtime/helper producer for the already-reviewed coverage contract.

Suggested module:

`scripts/newbuyer_b2_v2_coverage.py`

Name may differ.

Its input must be explicit, parameterized and generation-bound.

At minimum accept:

```text
subject cohort
fresh source generation IDs
fresh source packet/receipt refs
current native valuation owner receipts
current KIS valuation / no-estimate receipts
current exact-security / basis owner receipts
current business-quality owner receipts
current technical-quality owner receipts where required
producer/dataflow semantics version
```

Do NOT accept as coverage authority:

```text
historical REV55 accepted B2 outputs
historical REV57 Core/A/Overall/Holder outputs
historical blind labels
historical model stances
hard-coded 2026-10-02 paths
hard-coded report directories
ticker-specific expected dispositions
```

The producer must work before fresh Core/A/Overall/Holder model execution.

---

# 11. Coverage semantics are frozen

This task does not redesign the coverage ontology.

Preserve the reviewed rules from REV56B/REV56C:

- owner ref presence alone is insufficient;
- applicable current-state owner requires:
  - decision version;
  - field eligibility;
  - exact security binding;
  - generation binding;
  - source/raw hash binding;
  - temporal provenance;
  - field-specific current decision;
  - scope;
- `PRODUCER_SEMANTICS` may only prove `PROVEN_NOT_APPLICABLE`;
- producer semantics must never manufacture current QUALIFIED/DENIED state;
- category necessity must be proven by positive producer/dataflow semantics;
- metric-scoped denial stays metric-scoped;
- no cross-metric denial propagation;
- no missing-owner state becomes clearance;
- no emitted blocker != proof of no blocker;
- current blocker census is forbidden until coverage is complete;
- KIS normal-empty identity semantics remain:
  - request-bound negative observation != provider-returned positive identity;
  - malformed empty shape fail-closed;
  - no-estimate denial is metric-scoped.

Do not tune any rule to current/frozen stance distributions.

---

# 12. Contract identity

Prefer to preserve the consumer-visible contract:

`REV56COfflineCoverageReproofV1`

only if the new runtime producer is semantically byte/field compatible with that exact reviewed contract.

If a new version is technically required:

- stop automatic integration;
- document why;
- do not silently change the B2 v2 consumer;
- use:

`R2B_R9_REV58A_COVERAGE_CONTRACT_VERSION_GAP`

A version bump requires separate review because it would alter the frozen B2 v2 input contract.

---

# 13. Historical parity proof

Run the new parameterized producer offline on the exact historical inputs used to prove REV56C.

Required artifact:

`coverage-historical-parity.json`

Require at minimum:

```text
subjects = 22
complete_subjects = 22
unresolved_required_cells = 0

owner_provenance_complete = true
temporal_provenance_complete = true
decision_provenance_complete = true
```

Compare to the sealed REV56C semantic result:

```text
total cells = 506
PROVEN_APPLICABLE = 311
PROVEN_NOT_APPLICABLE = 195
UNRESOLVED = 0
```

Require per-cell semantic parity:

```text
ticker
metric
category
required/disposition
owner scope
owner decision semantics
```

Do not require a byte-identical top-level receipt if runtime metadata such as producer path/version timestamp is intentionally new.

Any semantic delta requires explicit explanation and fails this task unless it is purely non-semantic serialization metadata.

Failure:

`R2B_R9_REV58A_COVERAGE_PARITY_GAP`

---

# 14. 003690 historical diagnostic

Historical parity must preserve:

```text
native PER usable/qualified
CURRENT_FY1_FPER unavailable
normal-empty denial METRIC_SCOPED
no VALUATION_GLOBAL promotion
request-bound negative observation distinct from provider-returned positive identity
```

No regression to old 9-cell unresolved state.

---

# 15. 010120 historical diagnostic

Preserve:

```text
one relevant metric denied
one independently qualified relevant metric survives
```

No cross-metric denial propagation.
No global unresolved.

---

# 16. Fresh-input synthetic generation-binding tests

Without external source calls, create synthetic/fixed-fixture current-generation inputs that prove the producer is genuinely parameterized.

Required cases:

### A. Same semantic inputs, different generation ID

Expected:

- receipt binds new generation;
- no historical path leakage;
- deterministic semantic dispositions.

### B. Owner receipt with generation mismatch

Expected:

`UNRESOLVED` or explicit invalid coverage.
Never clearance.

### C. Missing temporal provenance

Expected coverage incomplete.

### D. Missing decision version / field eligibility

Expected coverage incomplete.

### E. Metric denial + alternate usable metric

Expected metric scope preserved.

### F. KIS normal-empty valid shape

Expected reviewed metric-scoped disposition.

### G. KIS malformed empty shape

Expected fail-closed unresolved/semantic gap.

### H. Historical Core/A/B object supplied as accidental input

Producer API must reject or ignore it as non-authoritative coverage input.

---

# 17. No fresh provider/model execution in REV58A

Hard zero:

```text
source/provider calls = 0
source recollection = 0
Alpha Vantage calls = 0

upstream model calls = 0
B2 v2 model calls = 0

fresh generation IDs = null
```

Use only sealed historical inputs and synthetic fixtures for repair validation.

Do not start the fresh shadow within REV58A.

---

# 18. Integration boundary

After repair, prove that REVISED REV58 can perform this order in code:

```text
pre-source execution-plan seal
→ full-fresh source collection
→ source-collection seal
→ fresh generation identity
→ fresh owner coverage producer
→ complete 22/22 coverage
→ fresh blocker census
→ fresh metric/evaluability state
→ fresh upstream Core/A/Overall/Holder reasoning
→ seal fresh upstream authority
→ build fresh B2 v2 requests
```

Required artifact:

`rev58-integration-readiness.json`

This is a static/offline integration proof only.

Do not execute the sequence with external calls.

---

# 19. Pre-source plan compatibility

The repair must make it possible for a future REV58 rerun to seal a complete execution plan before the first source call.

Prove that the exact code can now enumerate:

- source stages/provider families;
- existing pacing/retry policy;
- fresh upstream reasoning stages;
- model/effort/timeout;
- logical request counts;
- physical attempt caps;
- fresh owner-coverage producer contract;
- B2 v2 22-call plan;
- no-adaptive-recollection rule.

Required artifact:

`execution-plan-readiness.json`

Do not claim an exact per-provider call count if the existing source topology legitimately contains conditional slots; record bounded conditional rules instead.

---

# 20. B2 v2 semantics remain frozen

Do not change:

- blocker-role policy;
- legacy model visibility;
- metric resolution semantics;
- valuation evaluability;
- business-gate semantics;
- timing independence;
- stance capability;
- prompt;
- provider request schema;
- provider response schema;
- validator;
- historical comparison ontology.

Expected digests for the existing B2 v2 policy/prompt/schema/request contract must remain unchanged unless code movement changes only import organization without semantic bytes; if any frozen digest changes, stop:

`R2B_R9_REV58A_B2_V2_FROZEN_CONTRACT_DRIFT`

No repair in this task may alter economic behavior.

---

# 21. B2 v1 / upstream authority preservation

Require unchanged behavior/digests for all unrelated authority code:

```text
Core contract
Pass A contract
Pass B / Overall / Holder contract
B2 v1
active-risk policy
timing policy
source authority policy
```

The only allowed upstream behavioral change is:

> local semantic rejection becomes non-retryable after provider response schema has passed.

It must not alter the first-attempt semantic decision itself.

---

# 22. Default-OFF / production isolation

B2 v2 remains default-OFF.

The new coverage producer must not:

- run automatically in production;
- write production DB;
- change scheduler;
- send Telegram;
- replace official monitored records.

No migration.

No deploy.

No operating checkout change.

---

# 23. Focused tests

Add focused tests for:

- retry taxonomy;
- US semantic fail = 1 attempt;
- KR semantic fail = 1 attempt;
- transport retry still works;
- mixed transport then semantic stop;
- raw-first rejected-attempt preservation;
- fresh coverage producer API;
- historical 22 parity;
- generation mismatch fail-closed;
- temporal provenance fail-closed;
- KIS normal-empty / malformed-empty scope;
- no historical Core/A/B coverage dependency;
- no hard-coded historical path dependency;
- no ticker-specific coverage branch.

---

# 24. Full validation

If code changes occur, require:

```text
focused pytest PASS
Ruff PASS
git diff --check PASS
full pytest PASS
secret scan PASS
```

Preserve failed attempts and fixes.

Do not weaken tests to obtain PASS.

---

# 25. Feature commit / push

Only after all local gates pass:

- commit to the REV58A feature branch;
- feature push only;
- remote SHA readback;
- Hosted feature CI PASS.

No main merge.
No main push.

Do not deploy.

Required artifacts:

```text
feature-push-receipt.json
hosted-feature-ci.json
```

---

# 26. Protected-state reproof

At end verify:

```text
protected operating HEAD unchanged =
b610e6de0a8c33d199961e821ff1b130e1fa9ad4

production DB writes = 0
production WAL writes = 0
official monitored record writes = 0
Telegram = 0
scheduler mutation = 0
deploy = 0
restart = 0
operating mutation = 0
```

---

# 27. Success criteria

REV58A succeeds only if:

```text
REV58 integrity PASS

exact parent f26b69fd... proven

retry boundary repaired:
US local semantic reject attempts = 1
KR local semantic reject attempts = 1
transport/form retry remains enabled
systemic fail-stop preserved
raw-first preserved

fresh pre-model coverage producer exists in tracked code
producer is parameterized by current source/generation owners
no historical accepted model outputs required

historical REV56C coverage semantic parity = 22/22
506 cells semantically matched
003690 scope preserved
010120 scope preserved

generation mismatch fail-closed
temporal/decision provenance gates preserved
PRODUCER_SEMANTICS restrictions preserved

REVISED REV58 execution ordering statically reachable

B2 v2 frozen economic contract unchanged
B2 v1 / Core / A / Overall / Holder semantics unchanged
B2 v2 default-OFF

source/provider calls = 0
model calls = 0

focused tests PASS
Ruff PASS
git diff --check PASS
full pytest PASS
secret scan PASS
feature push/readback PASS
Hosted feature CI PASS

protected operating state unchanged
production side effects = 0
```

Success terminal:

`R2B_R9_REV58A_FRESH_SHADOW_PREREQUISITE_REPAIR_PASS_READY_TO_RERUN_REV58`

This authorizes only a new fresh/current-data shadow run under REVISED REV58.

It does NOT authorize final strict blind.

---

# 28. Stop terminals

Use the narrowest truthful terminal:

```text
R2B_R9_REV58A_REPOSITORY_IDENTITY_GAP
R2B_R9_REV58A_REV58_INTEGRITY_GAP
R2B_R9_REV58A_RETRY_CLASSIFICATION_GAP
R2B_R9_REV58A_RAW_FIRST_GAP
R2B_R9_REV58A_FRESH_COVERAGE_PRODUCER_GAP
R2B_R9_REV58A_COVERAGE_CONTRACT_VERSION_GAP
R2B_R9_REV58A_COVERAGE_PARITY_GAP
R2B_R9_REV58A_PROVENANCE_GATE_GAP
R2B_R9_REV58A_SCOPE_REGRESSION_GAP
R2B_R9_REV58A_B2_V2_FROZEN_CONTRACT_DRIFT
R2B_R9_REV58A_AUTHORITY_LEAKAGE_GAP
R2B_R9_REV58A_DEFAULT_OFF_GAP
R2B_R9_REV58A_FULL_VALIDATION_GAP
R2B_R9_REV58A_FEATURE_CI_GAP
R2B_R9_REV58A_PROTECTED_STATE_GAP
```

Do not add fresh-source or model execution to repair a failed offline proof.

---

# 29. Required result bundle

Create:

`rev58a-result.zip`

and:

`rev58a-result.zip.sha256`

Include at minimum:

```text
REPORT.md
summary.json

rev58-integrity.json
repository-identities.json
protected-before.json

retry-contract-v2.json
retry-boundary-tests.json
raw-first-rejection-proof.json

fresh-coverage-producer-contract.json
coverage-historical-parity.json
coverage-cell-diff.json
fresh-generation-binding-tests.json
scope-diagnostics.json

rev58-integration-readiness.json
execution-plan-readiness.json

b2-v2-frozen-contract-proof.json
b2-v1-compatibility.json
upstream-authority-compatibility.json
default-off-proof.json

focused-validation.json
full-validation.json
ruff-validation.json
diff-validation.json
secret-scan.json

network-events.json
feature-push-receipt.json
hosted-feature-ci.json

protected-state.json
final-repository-identities.json
bundle-manifest.json
```

No credentials.

---

# 30. Final report requirements

Report:

```text
terminal

parent HEAD
REV58A final feature HEAD
origin/main
protected operating HEAD

REV58 result SHA / integrity

retry classification implementation
US semantic-reject attempt count
KR semantic-reject attempt count
transport control attempt count
systemic control attempt count

fresh coverage producer path/contract
historical parity subjects
historical parity cells
semantic cell mismatches

003690 diagnostic
010120 diagnostic

generation-binding negative controls
provenance negative controls

B2 v2 frozen-contract drift count
B2 v1 drift count
upstream first-attempt semantic drift count

focused/full test results
Hosted CI

source/provider calls = 0
model calls = 0

production DB/WAL writes = 0
Telegram = 0
scheduler mutation = 0
deploy = 0
operating mutation = 0
```

---

# 31. What comes next

Do not execute automatically.

Only if terminal is:

`R2B_R9_REV58A_FRESH_SHADOW_PREREQUISITE_REPAIR_PASS_READY_TO_RERUN_REV58`

then create/run a new revision of the **REVISED REV58 fresh/current-data B2 v2 shadow** using the repaired feature HEAD.

That rerun must again:

- seal execution plan before first source call;
- apply safe storage GC;
- create a genuinely new source generation;
- seal all source collection before any model output;
- build fresh owner coverage before upstream reasoning;
- regenerate fresh Core/A/Overall/Holder authority;
- seal upstream outputs before B2 request construction;
- execute B2 v2 shadow only;
- keep production side effects zero.

Only after that fresh shadow actually passes may a final fresh strict blind work instruction be created.

---

# 32. Final principle

REV58 did the right thing by stopping before source/model calls.

The repair is not economic.

It is two execution/ownership prerequisites:

```text
provider/transport failure
→ retry permitted

provider-schema-valid local semantic failure
→ one preserved attempt, then stop

fresh source generation
→ parameterized typed owner composition
→ complete coverage
→ only then fresh upstream reasoning
```

Never:

```text
semantic reject
→ resample until valid

historical coverage receipt
→ relabel as fresh

historical Core/A/B output
→ current coverage authority

repair task
→ start fresh providers/models

repair PASS
→ skip fresh shadow and go to final blind
```

The target is faithful production-equivalent shadow preconditions, with no change to B2 v2 economic semantics.
