# Thesis Monitor — R2B-R9-REV48
## Hosted CI Date/Datetime Contract Repair
## → Feature CI Green
## → Main CI Green
## → Exact Remote `sskim-ai/thesis-monitor:main` Verification
### No provider/model/message rerun
### No deploy / scheduler / Telegram / production DB mutation

---

# 0. Task objective

REV47 is functionally integrated and already pushed to GitHub `sskim-ai/thesis-monitor:main`, but Hosted CI is not yet green.

REV48 closes only the remaining CI contract gap and verifies the exact final remote `main`.

This is a bounded repository/test-contract repair.

It is **not**:

- a source recollection task;
- a model rerun;
- a message regeneration task;
- a valuation-policy change;
- a completed-close owner change;
- a scheduler task;
- a deployment task.

Hard zero:

```text
provider calls = 0
model calls = 0
message generation = 0
Telegram = 0
production DB writes = 0
scheduler mutations = 0
deploy = 0
restart = 0
broker actions = 0
```

---

# 1. Immutable prior evidence

Verify both accepted REV47 bundles before work.

## 1.1 REV47 full US/KR execution result

File:

`thesis-monitor-20261002-r2b-r9-rev47-ten-minute-completed-close-us-kr-report.zip`

Expected SHA-256:

`73c85d29bbdbc4d9b8fc4631850104bc3171d3be013c99dbce041aec2badebed`

Expected functional evidence:

```text
US completed-session close v2 = 14/14 PASS
US messages = 15
KR messages = 9
total messages = 24
US provider recollection during model continuation = 0
KR fresh provider attempts = 172
total controller model attempts = 29
model retries = 3
fallback = 0
local full pytest = 8057 passed / 63 skipped / 0 failed
local focused = 276 passed
```

## 1.2 REV47 main-push completion

File:

`thesis-monitor-20261002-r2b-r9-rev47-main-push-completion-report.zip`

Expected SHA-256:

`e2e5d78a2ee6179780e3560504a248fc8dbbff679fc310b93040d0da5981fcc9`

Expected terminal:

`R2B_R9_REV47_COMPLETED_CLOSE_US_KR_FRESH_MESSAGES_MAIN_INTEGRATION_PASS`

Expected remote main:

`0045e6dbbc932fe8decc8fb26966f8a8d8fe37ab`

Expected:
- non-force push completed;
- exact remote SHA independently read back;
- operating checkout unchanged;
- deploy/restart/scheduler/Telegram/production DB = 0.

Do not rewrite either immutable archive.

---

# 2. Current GitHub state to verify first

Repository:

`sskim-ai/thesis-monitor`

Expected current remote main at task start:

`0045e6dbbc932fe8decc8fb26966f8a8d8fe37ab`

Feature CI already demonstrated one failure:

```text
tests/test_unified_class_c_owners.py::
test_estimate_inventory_does_not_forge_unavailable_basis
```

Observed feature CI summary:

```text
1 failed
8055 passed
64 skipped
```

Observed exception:

```text
AttributeError: 'datetime.date' object has no attribute 'utcoffset'
```

The exact-main workflow run observed during review was still `in_progress`.

At REV48 start:
1. fetch current `origin/main`;
2. query the existing exact-main GitHub Actions run to terminal state if already complete;
3. preserve its terminal result before any new commit.

Do not manually rerun the old run.

---

# 3. Known contract mismatch

Current model declaration:

```python
class ConsensusEstimate(...):
    estimate_as_of: datetime
```

Known failing fixture:

```python
ConsensusEstimate(
    ...,
    estimate_as_of=CUTOFF.date(),
    ...
)
```

where `CUTOFF` is timezone-aware `datetime`.

This fixture supplies a `datetime.date` to a field declared as `datetime`.

Hosted SQLModel/SQLAlchemy UTC datetime binding attempts datetime semantics such as `utcoffset()` and rejects the plain `date`.

The default repair hypothesis is therefore:

> the test fixture violates the declared field contract.

Do not change the production model type merely to accommodate this single fixture unless broader repository evidence proves that the production contract is actually intended to accept dates.

---

# 4. Branch/base discipline

Create REV48 from freshly fetched exact remote `main`.

Expected initial base if unchanged:

`0045e6dbbc932fe8decc8fb26966f8a8d8fe37ab`

Suggested branch:

`codex/r2b-r9-rev48-hosted-ci-datetime-contract`

Before implementation:

- fetch origin;
- prove the base SHA;
- worktree clean;
- record Python / SQLModel / SQLAlchemy / Pydantic versions locally;
- record GitHub workflow Python version/dependency installation contract from `.github/workflows/test.yml`.

No rebase of accepted REV47 history.
No force push.

---

# 5. Repository-wide contract audit before edit

Search all repository uses of:

```text
ConsensusEstimate(
estimate_as_of=
```

and all assignments/construction paths for:

`ConsensusEstimate.estimate_as_of`.

Classify every occurrence as:

```text
A. timezone-aware datetime
B. naive datetime
C. date
D. parsed string later normalized
E. unknown/dynamic
```

Also inspect:
- API/provider adapters that populate `ConsensusEstimate`;
- persistence/import paths;
- fixtures;
- migrations/schema assumptions if any.

Create:

`consensus-estimate-estimate-as-of-contract-audit.json`

Do not edit yet until this audit is complete.

---

# 6. Preferred repair when production callers are contract-correct

If all production/runtime call sites already use a `datetime` and the only invalid call is the test fixture:

change only the fixture from:

```python
estimate_as_of=CUTOFF.date()
```

to:

```python
estimate_as_of=CUTOFF
```

or the repository's exact canonical timezone-aware datetime form.

Do not change:
- `ConsensusEstimate` schema;
- estimate semantics;
- source policy;
- valuation semantics;
- forwardPE policy;
- owner eligibility.

This is the preferred minimal repair.

---

# 7. If production callers also pass `date`

If the audit finds real production/runtime `date` callers:

do **not** simply widen the database model from `datetime` to `date | datetime`.

Instead determine the existing semantic contract.

Preferred canonicalization, if the business concept is an as-of instant:

```text
date input
→ explicit UTC datetime normalization at the owning boundary
```

with a documented deterministic convention.

Do not invent midnight semantics unless the owning source contract supports it.

If the actual domain concept is date-only and existing persisted/runtime semantics consistently treat it as date-only, stop with:

`R2B_R9_REV48_ESTIMATE_ASOF_SCHEMA_REVIEW_REQUIRED`

because changing the persisted field type is broader than this CI repair.

No silent schema migration.

---

# 8. Regression tests required

At minimum add/retain tests proving:

1. canonical timezone-aware datetime persists successfully;
2. the failing unavailable-basis test preserves its original semantic assertion;
3. no fake estimate basis is forged;
4. `project_estimate_inventory` remains in the same eligibility/qualification state;
5. no valuation owner is newly promoted;
6. no date→datetime conversion silently changes estimate period/basis;
7. repository code does not rely on a plain `date` where `datetime` is declared.

If production normalization is needed, add exact positive and negative tests for it.

---

# 9. Focused validation

Run at minimum:

```text
tests/test_unified_class_c_owners.py
```

plus any directly related:
- security model tests;
- estimate owner tests;
- forward valuation tests.

Require zero failure/error.

Record exact pass/skip counts.

---

# 10. Full local validation

Run the same validation contract used for REV47:

- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Expected baseline scale:

```text
~8057+ passed
~63 skipped
0 failed
0 errors
```

Do not require exact identical pass count if one new regression test is added; explain the delta.

No network/provider/model access during tests.

---

# 11. Protected-state proof

Before and after local validation prove:

```text
provider calls = 0
model calls = 0
Telegram = 0
scheduler mutation = 0
production DB write = 0
deploy = 0
restart = 0
broker action = 0
```

Do not touch the operating checkout:

`/Users/sskim/Codex/thesis-monitor`

unless this task is explicitly resumed later for deployment.

Current operating checkout may remain on its pre-REV47 SHA.

---

# 12. Commit and feature push

After local PASS:

1. commit only the bounded CI contract repair;
2. secret-scan outgoing commit;
3. push the feature branch normally;
4. verify exact remote feature SHA.

No force push.

Suggested commit intent:

`Fix ConsensusEstimate datetime fixture contract`

Do not mix message-quality or renderer changes into REV48.

---

# 13. Hosted feature CI is mandatory

Observe the GitHub Actions run created for the exact feature SHA.

Do not call it PASS while queued/in-progress.

Wait for a terminal GitHub result with a bounded observation timeout.

Suggested maximum observation window:

`30 minutes`

If still queued/in-progress beyond that:

`R2B_R9_REV48_FEATURE_CI_STUCK_OR_TIMEOUT`

Stop without a new push.

If failed:
- fetch exact failed job/step/log;
- classify the failure;
- do not blindly rerun;
- repair only if directly caused by the bounded REV48 contract or a newly proven CI-environment incompatibility.

Feature CI must be green before main integration.

---

# 14. Main integration

Only after feature CI PASS.

Immediately before merge:

1. fetch `origin/main`;
2. verify whether it is still the expected base/current main;
3. if main moved, inspect relationship and reconcile non-destructively.

If unrelated main changes create semantic conflicts:

`R2B_R9_REV48_MAIN_MOVED_REVIEW_REQUIRED`

Do not force/rebase over unknown work.

If safe:
- integrate REV48 to local integration main;
- validate exact merged-main SHA locally.

---

# 15. Merged-main local validation

On the exact intended new main SHA:

- focused tests;
- full pytest;
- Ruff;
- diff check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- protected-state comparison.

Require PASS before push.

---

# 16. Push exact final main to user's GitHub

Target:

`sskim-ai/thesis-monitor`

Branch:

`main`

Immediately before push:
- fetch origin again;
- prove `origin/main` has not moved since reconciliation.

Push:

```text
ordinary non-force push only
```

No force push.

After push:
- independently read back `refs/heads/main`;
- require exact equality to the intended final SHA.

---

# 17. Hosted main CI is the final gate

Observe the GitHub Actions run for the **exact final remote main SHA**.

Do not finish with:
- queued;
- in_progress;
- unknown;
- local-only PASS.

Require terminal:

```text
status = completed
conclusion = success
```

Fetch:
- workflow run identity;
- job identity;
- test step conclusion;
- lint step conclusion.

If main CI fails despite feature CI PASS:
- preserve exact logs;
- stop with:

`R2B_R9_REV48_MAIN_CI_GAP`

Do not create another silent commit.

If main CI remains nonterminal beyond the bounded observation period:

`R2B_R9_REV48_MAIN_CI_STUCK_OR_TIMEOUT`

Do not claim green.

---

# 18. Final repository verification

After main CI success verify:

```text
repository = sskim-ai/thesis-monitor
branch = main
remote main SHA = intended REV48 final SHA
hosted CI exact SHA = same SHA
hosted CI = success
```

Also record:
- feature SHA;
- merge/integration SHA if distinct;
- prior main SHA;
- new main SHA.

---

# 19. No deployment in REV48

A green GitHub main does not authorize runtime promotion.

Keep:

```text
operating checkout advancement = 0
scheduler activation/change = 0
deploy = 0
restart = 0
Telegram = 0
production DB writes = 0
```

Deployment is a separate explicit task.

---

# 20. Result bundle

Create:

`thesis-monitor-20261002-r2b-r9-rev48-hosted-ci-datetime-contract-main-green-report.zip`

+ `.sha256`

Include at minimum:

```text
REPORT.md
summary.json
REV47-bundle-integrity.json
initial-github-main.json
initial-main-ci-state.json
dependency-environment.json
consensus-estimate-estimate-as-of-contract-audit.json
repair-decision.json
changes.patch
focused-validation.json
full-validation.json
static-validation.json
secret-scan.json
protected-state.json
feature-push-receipt.json
feature-ci-final.json
main-reconciliation.json
merged-main-validation.json
main-push-receipt.json
remote-main-readback.json
main-ci-final.json
final-repository-state.json
bundle-manifest.json
```

No credentials.

---

# 21. Success terminal

Use only after exact remote main CI is green:

`R2B_R9_REV48_HOSTED_CI_DATETIME_CONTRACT_REPAIR_MAIN_GREEN_PASS`

Required final statements:

```text
source/model/message rerun = 0
REV47 24 messages unchanged
valuation policy unchanged
completed-close policy unchanged
remote repository = sskim-ai/thesis-monitor
remote branch = main
remote SHA = <exact SHA>
hosted feature CI = PASS
hosted main CI = PASS
local full pytest = PASS
deploy = 0
```

---

# 22. Honest stop terminals

Use the narrowest truthful state:

```text
R2B_R9_REV48_ESTIMATE_ASOF_SCHEMA_REVIEW_REQUIRED
R2B_R9_REV48_FOCUSED_VALIDATION_GAP
R2B_R9_REV48_FULL_VALIDATION_GAP
R2B_R9_REV48_FEATURE_CI_GAP
R2B_R9_REV48_FEATURE_CI_STUCK_OR_TIMEOUT
R2B_R9_REV48_MAIN_MOVED_REVIEW_REQUIRED
R2B_R9_REV48_MERGED_MAIN_VALIDATION_GAP
R2B_R9_REV48_REMOTE_MAIN_MOVED_REVIEW_REQUIRED
R2B_R9_REV48_MAIN_CI_GAP
R2B_R9_REV48_MAIN_CI_STUCK_OR_TIMEOUT
```

---

# 23. Scope discipline

Do not include the following in REV48:

- KR market TOP3/BOTTOM3 renderer repair;
- English/Korean wording cleanup;
- completed-session price heading cleanup;
- technical-fact adjustment compatibility work;
- new provider qualification;
- additional fresh source collection;
- new model messages;
- deployment.

Those are separate post-CI quality/runtime tasks.

REV48 exists for one purpose:

> make the already-integrated REV47 repository state reproducibly green in Hosted CI and verify the exact green commit on
> `sskim-ai/thesis-monitor:main`.
