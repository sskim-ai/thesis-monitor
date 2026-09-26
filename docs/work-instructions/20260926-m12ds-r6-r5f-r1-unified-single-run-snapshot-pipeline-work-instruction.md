# Thesis Monitor — M12DS-R6-R5F-R1
## Unified Single-Run Snapshot Pipeline
### US 08:10 / KR 16:00 — Conditional Collection Retry → AI → Render → Send → Failure Bundle/iCloud

**Purpose:** replace the old primary/backup monitoring topology with one deterministic market run per cycle. Use query-time snapshots, retry only incomplete collection at bounded later timestamps, then immediately perform AI analysis, render and delivery. Any terminal failure produces an operational failure notification plus a sealed debug bundle uploaded to the configured iCloud location.

---

# 0. Product decision / operating contract

The operational contract is now:

## US

1. **08:10 KST**
   - collect one complete US production snapshot;
2. only if that collection is not production-eligible:
   - **08:15 KST** collect a new complete snapshot;
3. only if the 08:15 snapshot is still not production-eligible:
   - **08:20 KST** collect a final new complete snapshot;
4. first eligible snapshot wins;
5. freeze it;
6. AI model calls;
7. message generation/render;
8. delivery;
9. stop.

There is no independent automatic backup run after successful collection.

## KR

1. **16:00 KST**
   - collect one complete KR production snapshot;
2. only if that collection is not production-eligible:
   - **16:05 KST** collect a new complete snapshot;
3. only if the 16:05 snapshot is still not production-eligible:
   - **16:10 KST** collect a final new complete snapshot;
4. first eligible snapshot wins;
5. freeze it;
6. AI model calls;
7. message generation/render;
8. delivery;
9. stop.

There is no independent automatic backup run after successful collection.

## Market-closed days

- KR: preserve the accepted KRX holiday suppression contract. A KRX holiday is a deterministic skip, not a failure, and KR messages are not generated/sent.
- US: preserve the existing XNYS/session gate. If there is no eligible completed US session for that run, treat it as a deterministic market-closed/session-skip state rather than a collection failure.

---

# 1. Source semantics

Use the query-time snapshot policy.

A production run uses:

> the exact values returned and structurally accepted from the configured provider at the successful collection time.

Do not require or claim:

- provider-certified immutable final close;
- independent settled-close authority;
- `08:10 == official finality`;
- delayed historical equality as a production prerequisite.

Required semantic state is equivalent to:

- `QUERY_TIME_SNAPSHOT`
- `finality_claim = NOT_CLAIMED`

Each run must preserve:

- provider/source identity;
- symbol/route;
- source row/session date where available;
- collection timestamps;
- raw/adjusted basis;
- exact values used;
- raw/normalized hashes;
- immutable run snapshot identity.

Later provider revisions do not rewrite an already-issued run.

---

# 2. Remove primary/backup scheduling topology

Audit and remove the old operational concept of separate:

- `primary`
- `backup`

monitoring reservations/jobs for the same market cycle.

The new topology is:

`one scheduled market run`
→ internal bounded collection state machine
→ AI
→ render
→ send
→ done

Do not create separate scheduled jobs for 08:15/08:20 or 16:05/16:10.

Those later timestamps are **internal conditional waits/retries inside the already-running foreground/job execution**, not independent scheduler reservations.

Required migration evidence:

- inventory of old primary/backup jobs;
- exact jobs removed/disabled;
- new single US reservation;
- new single KR reservation;
- no duplicate delivery opportunity;
- no orphan backup schedule;
- no hidden secondary scheduler path.

Do not delete unrelated schedules.

---

# 3. Schedule entrypoints

Use one scheduled entrypoint per market.

## US entrypoint

Operational target:
`08:10 KST`

Preserve the repository’s correct day/session scheduling semantics. Do not replace exchange/session logic with a naive weekday assumption.

The job must determine whether there is an eligible completed XNYS session before collection.

## KR entrypoint

Operational target:
`16:00 KST`

Use the authoritative XKRX calendar/session gate.

If KRX is closed:
- KR pipeline skips;
- model = 0;
- render = 0;
- send = 0;
- no failure alert.

Do not treat a holiday as collection failure.

---

# 4. Collection eligibility definition

A collection attempt is successful only when the **entire required production source packet** for that market passes existing structural/source validators.

At minimum verify:

1. required canonical market/stock universe is complete;
2. all required source roles for the configured market + stock messages are present;
3. symbol/route identity is valid;
4. required dated rows have the intended latest available session context;
5. required OHLC/quote fields are non-null and parseable;
6. raw/adjusted basis is explicit where required;
7. no provider/request error leaves a required production role missing;
8. normalized packet passes all existing source/schema validators;
9. every downstream AI role can consume the same packet without filling from later data;
10. raw receipts/hashes exist for audit.

Do not use finality authority as an eligibility requirement.

Do not accept a partially complete packet just because most symbols succeeded.

If the configured production path requires full22 for US or the canonical KR universe for KR, that full required universe must be complete.

---

# 5. Retry semantics — entire snapshot, not patching

If an attempt is incomplete:

- preserve it as failed-attempt debug evidence;
- do not use any values from it in the final production packet;
- do not merge good symbols from one attempt with failed symbols from a later attempt;
- wait until the next allowed collection timestamp;
- collect a **new complete snapshot**.

Therefore:

US:
- 08:10 attempt A
- if invalid -> 08:15 attempt B (new full snapshot)
- if invalid -> 08:20 attempt C (new full snapshot)

KR:
- 16:00 attempt A
- if invalid -> 16:05 attempt B
- if invalid -> 16:10 attempt C

The first full production-eligible snapshot is frozen and used.

Earlier failed attempts remain available only for diagnostics.

---

# 6. Timing / waiting behavior

The single scheduled job may remain alive between bounded collection attempts.

Required:

- use wall-clock not-before waits;
- no detached daemon;
- no creation of a second scheduler job;
- no callback registration;
- no uncontrolled background task;
- no busy-spin;
- no early request before the configured retry time;
- if process resumes after a retry window, immediately decide whether that attempt is still allowed under the bounded retry state machine rather than inventing a new time.

Recommended internal states:

- `COLLECT_INITIAL`
- `WAIT_RETRY_1`
- `COLLECT_RETRY_1`
- `WAIT_RETRY_2`
- `COLLECT_RETRY_2`
- `SNAPSHOT_READY`
- `ANALYZE`
- `RENDER`
- `DELIVER`
- `FAILURE_FINALIZE`
- `DONE`

Exact names may follow repository conventions.

---

# 7. Collection failure after final attempt

If the final allowed collection attempt is still incomplete:

## US
after the 08:20 attempt fails

## KR
after the 16:10 attempt fails

then:

1. do not call investment AI models;
2. do not generate normal market/stock messages;
3. produce a **failure notification message**;
4. generate a sealed debug bundle;
5. upload/copy the debug bundle to the configured iCloud-backed debug/report location;
6. record upload/hash receipt;
7. stop the run.

Do not create another backup run.

---

# 8. AI / render / delivery failure semantics

Once a snapshot is successfully frozen:

**Do not recollect market data because a later stage fails.**

If any of these fail:

- Market model
- Core
- A
- B
- validator
- render
- delivery

then:

1. preserve the same frozen snapshot;
2. classify the exact failed stage;
3. do not wait for the next collection retry time;
4. do not create a backup monitoring run;
5. generate a failure notification;
6. generate and upload the debug bundle;
7. stop.

A model/render/delivery failure is not a reason to recollect data.

Do not silently run a second full AI pass unless an already-established bounded retry policy explicitly exists and is retained by this migration.

If no explicit approved model retry contract exists, one attempt per role remains the default for this task.

---

# 9. Successful run

On the first production-eligible snapshot:

1. seal immutable snapshot;
2. create run ID;
3. freeze source hashes/as-of;
4. Market analysis;
5. Core;
6. A;
7. B;
8. validators;
9. render normal messages;
10. send;
11. record delivery receipts;
12. finalize success;
13. stop.

No primary/backup designation remains.

Expected normal output remains the configured market and stock message set, including the existing 24-message US dry-run/production-equivalent structure where applicable.

All AI layers must reference the same snapshot/run identity.

---

# 10. Failure notification

Use the existing operational notification channel/recipient contract.

Failure message must be operationally concise and must not masquerade as an investment message.

Include at least:

- market: `US` or `KR`;
- run ID;
- scheduled run time;
- terminal failure stage;
- attempt count;
- final failure reason/code;
- whether normal messages were sent (`false` for pre-delivery failure);
- debug bundle upload status;
- debug bundle identifier/path label if safe to expose.

Do not include:
- API secrets;
- tokens;
- raw credentials;
- huge traceback dumps;
- full provider payloads.

If the failure-notification send itself fails:
- still create/upload the debug bundle;
- preserve notification-send failure in the bundle;
- do not launch another backup scheduler job.

---

# 11. Debug bundle contents

Every terminal failure must create one immutable debug bundle.

Minimum contents:

- `REPORT.md`
- `summary.json`
- run ID / market / schedule timestamp
- state-machine transition log
- each collection-attempt receipt
- raw response hashes
- normalized packet validation results
- missing/invalid symbol or role list
- source date/basis diagnostics
- frozen snapshot hash if snapshot was reached
- model request metadata/hashes if model stage was reached
- model response hashes/redacted validation output
- render validation results
- delivery receipt/error if delivery was attempted
- traceback/error chain
- relevant configuration fingerprints
- repo/commit identity
- scheduler/job identity
- safety counters
- secret scan
- bundle manifest
- bundle SHA-256

Do not store secrets in the bundle.

---

# 12. iCloud upload contract

Use the project’s existing configured iCloud-backed reports/debug destination if one already exists.

Before implementation:
- locate the existing canonical iCloud path/config;
- document it;
- do not invent a second competing upload location.

If there is no canonical configurable path:
- introduce one explicit configuration value for the debug destination;
- do not hardcode a developer-specific absolute home path into business logic;
- fail visibly if the path is required but unavailable.

Required upload behavior:

1. create bundle locally first;
2. fsync/close;
3. compute SHA-256;
4. copy atomically where practical to iCloud-backed destination;
5. verify destination file size/hash when the filesystem exposes the bytes locally;
6. write upload receipt;
7. do not claim remote-device/cloud-server synchronization beyond what can actually be observed.

The correct claim is:
`copied to configured iCloud-backed local path and locally hash-verified`

unless independent remote sync status is available.

---

# 13. Scheduler migration safety

Before changing scheduler reservations:

1. inventory current US primary/backup jobs;
2. inventory current KR primary/backup jobs;
3. capture exact current schedule state;
4. prove which entrypoints are active;
5. prepare migration diff;
6. test offline.

After migration:

- exactly one active scheduled US cycle entry;
- exactly one active scheduled KR cycle entry;
- no backup reservations;
- no duplicate same-market run;
- holiday/session gates remain functional;
- scheduler state is deterministic and auditable.

Do not alter unrelated jobs.

If scheduler mutation is considered production-affecting under current project rules, prepare/test the migration locally first and perform actual scheduler activation only under the project’s existing promotion/deployment authorization process.

---

# 14. US-specific tests

At minimum:

1. 08:10 full valid -> freeze A -> AI/render/send -> no 08:15/08:20 collection.
2. 08:10 partial -> retain debug only -> wait -> 08:15 full valid -> freeze B -> normal pipeline -> no 08:20 collection.
3. 08:10 partial -> 08:15 partial -> 08:20 full valid -> freeze C -> normal pipeline.
4. all three incomplete -> no AI -> failure message -> debug bundle -> iCloud copy.
5. successful snapshot is one attempt only; no cross-attempt merge.
6. failed 08:10 values cannot leak into 08:15 production packet.
7. later provider revision cannot mutate sent run.
8. no official-finality claim.
9. XNYS closed/no eligible session -> deterministic skip.
10. no backup scheduler entry.

---

# 15. KR-specific tests

At minimum:

1. XKRX open, 16:00 valid -> normal pipeline -> no retry.
2. 16:00 partial -> 16:05 valid -> normal pipeline.
3. 16:00 partial -> 16:05 partial -> 16:10 valid -> normal pipeline.
4. all three incomplete -> failure notification + debug/iCloud.
5. no cross-attempt merge.
6. KRX holiday -> deterministic skip:
   - model 0
   - render 0
   - send 0
   - no failure message.
7. `--market all` holiday routing still suppresses KR without suppressing eligible US branch.
8. no backup scheduler entry.

---

# 16. AI/message pipeline tests

At minimum:

1. valid snapshot -> same run/snapshot ID across Market/Core/A/B/render.
2. packet hash mismatch between layers -> terminal failure.
3. stale previous-run packet -> rejected.
4. later historical/lookahead row injection -> rejected.
5. one model stage fails -> no recollection; failure finalization.
6. validator fails -> no normal delivery; failure finalization.
7. render fails -> failure finalization.
8. send fails -> debug bundle records delivery failure.
9. normal messages contain no unsupported `확정 종가` semantics.
10. failure message is distinguishable from investment content.

---

# 17. Remove obsolete concepts

Audit code/config/docs/tests for:

- `primary` run
- `backup` run
- backup monitoring reservation
- failover schedule
- secondary delivery opportunity
- delayed backup message generation

Classify each occurrence:

- operational and must be removed/migrated;
- unrelated terminology and may remain;
- historical report only.

Do not mechanically rename unrelated concepts.

After migration, normal runtime logic must not depend on primary/backup role selection for US or KR monitoring.

---

# 18. Alpha / external reference disposition

Under the query-time snapshot product contract:

- Alpha Vantage is not required for normal US message production;
- Massive is not required;
- R5D/R5E external-reference search is no longer a production blocker.

For this task:

`Alpha Vantage calls = 0`

P1-02 remains a separate safety task only if Alpha will be used later.

Do not spend the 25/day quota here.

---

# 19. Required implementation scope

Expected areas to audit/modify:

- monitor scheduler/config
- market run orchestration
- collection retry/state machine
- snapshot eligibility/freeze contract
- model/render/delivery orchestration
- failure notification
- debug bundle builder
- iCloud debug copy/upload helper
- focused tests/docs

Do not alter:
- investment scoring/thesis logic;
- technical indicators;
- stock universes unless existing canonical source already says otherwise;
- broker/order logic;
- portfolio logic;
- R5 sealed evidence.

Use the smallest causal set of files.

---

# 20. Validation

Required after implementation:

- focused US state-machine tests
- focused KR state-machine tests
- scheduler migration tests
- holiday/session tests
- query-time snapshot tests
- model/render/delivery failure tests
- debug bundle/iCloud tests
- full pytest
- Ruff
- `git diff --check`
- Investment Knowledge check
- Chart Knowledge check
- secret scan

No new unexplained skip/xfail.

If scheduler state is actually mutated:
- capture before/after;
- prove no orphan backup jobs;
- prove exact single-entry state.

Do not claim deploy/service restart unless actually performed.

---

# 21. Required result bundle

Return immutable ZIP + SHA-256 sidecar containing at minimum:

- `REPORT.md`
- `summary.json`
- source SoT identities
- base / implementation / final SHA
- changed-file inventory
- old scheduler inventory
- new scheduler design/state
- primary/backup removal matrix
- US state-machine proof
- KR state-machine proof
- collection-attempt matrices
- snapshot-freeze proof
- cross-attempt contamination negative proof
- AI/render/delivery pipeline proof
- failure notification examples/fixtures
- debug bundle fixture
- iCloud local-copy/hash-verification receipt
- holiday/session proof
- Alpha calls = 0 receipt
- focused/full validation logs
- operating/scheduler before-after receipts
- secret scan
- bundle manifest

---

# 22. Suggested terminals

## Local implementation/test complete, scheduler not yet activated

`M12DS_R6_R5F_R1_UNIFIED_SINGLE_RUN_PIPELINE_READY_FOR_PROMOTION`

## Operating scheduler migration and runtime contract fully promoted/validated

`M12DS_R6_R5F_R1_UNIFIED_SINGLE_RUN_PIPELINE_PASS`

Do not use PASS if old backup reservations remain active.

---

# 23. Final operational policy

After full PASS:

## US
`08:10 collection`
→ if incomplete `08:15 full recollection`
→ if incomplete `08:20 full recollection`
→ first valid snapshot
→ AI
→ message generation
→ send
→ done

## KR
`16:00 collection`
→ if incomplete `16:05 full recollection`
→ if incomplete `16:10 full recollection`
→ first valid snapshot
→ AI
→ message generation
→ send
→ done

## Failure
final collection or downstream processing failure
→ failure notification
→ sealed debug bundle
→ copy to configured iCloud-backed path
→ stop

## Holiday / no eligible session
→ deterministic skip
→ no investment message
→ no failure message

There is no primary/backup monitoring topology.
