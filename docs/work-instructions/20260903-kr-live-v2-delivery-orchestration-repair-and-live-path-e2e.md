# thesis-monitor — KR Live V2 Delivery Orchestration Repair + Single Live-Path E2E
## Repair the actual production path after accepted AI review
## Stop calling simplified replay paths "production-equivalent"
## Prove the real scheduler entrypoint, selector, queue, retry, dedupe, fallback, and delivery path end-to-end
## No model/prompt redesign

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Incident date: `2026-09-03 KST`
- Market: `KR`
- Authoritative natural run: `54`
- Operating revision:
  `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Primary natural packet:
  `2026-09-03-kr-run-54-f19bb379daa7`
- Later reused/delivered packet:
  `2026-09-03-kr-run-54-78ed269de3df`
- Natural scheduler unit:
  `com.seungsoo.thesis-monitor.kr-close`
- Natural invocation:
  `python -m app.jobs.monitor_daily --market kr`
- Primary schedule:
  `16:05 KST`
- Backup observations:
  `16:20`, `16:50`
- Fallback dispatch:
  `17:10 KST`
- Task class:
  `LIVE_ORCHESTRATION_REPAIR + DELIVERY_STATE_MACHINE_REPAIR + LIVE_PATH_E2E`
- Production Assist: preserve current configured state
- Production recipient send during repair: `0`
- Main merge: `0` until proof is reviewed
- Fresh investment-logic redesign: `0`
- Model/prompt redesign: `0`
- Validator weakening: `0`

---

# 1. Incident facts — freeze before coding

Treat these as the factual starting point from the 2026-09-03 read-only natural-run extraction.

Natural run:

```text
source ready                     8/8
technical FULL                   8/8
AI-consumability ready           8/8

first AI candidate               9 items
initial validation               rejected
corrected candidate              9 items
corrected validation             PASS
accepted                         9/9

explicit V2                      0
decision canary state            V2_DECISION_SUPPRESSED_SAFE

AI-assisted delivery receipt:
  status                         pending
  delivery_count                 9
  sent_count                     0
  pending_count                  9

later delivery retry:
  no_pending_ai_delivery

17:10 deterministic fallback:
  market                         1
  stocks                         8
  sent                           9/9
  duplicate                      0
```

The first candidate errors were:

```text
market:
- IWM/SPY relative numeric semantic mismatch
- unsupported 0.7 numeric usage

000660:
- valuation interpretation occurrence/binding errors
```

Those errors were corrected and the corrected candidate passed validation.

Therefore:

```text
INITIAL_VALIDATION_REJECTION
!= final natural-run root cause
```

Do not spend this task redesigning the model or weakening validators.

---

# 2. Primary incident statement

The most important observed inconsistency is:

```text
accepted AI delivery state
= pending 9

retry/delivery view
= no_pending_ai_delivery
```

At the same time:

```text
accepted AI content exists
validation passed
explicit V2 count = 0
V2_DECISION_SUPPRESSED_SAFE
```

This task must determine whether these are:
- one shared state-ownership defect,
- two independent defects,
- or an intentional selector/suppression condition plus a delivery ownership defect.

Do not assume before tracing.

---

# 3. Secondary incident

A later reused packet:

```text
2026-09-03-kr-run-54-78ed269de3df
```

received a validation result at approximately:

```text
17:10:56 KST
```

after deterministic fallback dispatch at approximately:

```text
17:10:06 KST
```

and contained KR-irrelevant:

```text
IWM / SPY
```

numeric semantic errors.

Chronology proves this late validation did not trigger the already-sent fallback.

However it is a packet-ownership/provenance anomaly and must be audited separately.

Do not conflate it with the primary 16:05 accepted-delivery failure.

---

# 4. Repair scope

Repair only the live orchestration boundary:

```text
accepted AI artifact
→ explicit V2 eligibility/selector
→ delivery-intent persistence
→ delivery queue visibility
→ claim/retry
→ dedupe/exactly-once
→ AI send
→ AI sent acknowledgement
→ fallback cancellation/suppression
```

Also repair or prove packet ownership for late validation.

Out of scope unless directly necessary:

```text
investment prompt
directional-balance redesign
new-buyer/holder shadow structure
company analysis logic
technical indicator formulas
valuation methodology
night-futures date mapping
macro model
provider source selection
```

---

# 5. Core architectural rule — one authoritative delivery state machine

There must be one authoritative persisted state for AI delivery lifecycle.

Do NOT allow independent modules to derive conflicting concepts of:

```text
pending
claimed
sent
fallback_required
```

Preferred conceptual lifecycle:

```text
AI_ACCEPTED
↓
AI_DELIVERY_PENDING
↓
AI_DELIVERY_CLAIMED
↓
AI_DELIVERY_SENT
↓
COMPLETE
```

Failure/retry paths:

```text
AI_DELIVERY_PENDING
↘ retry claim

AI_DELIVERY_CLAIMED
↘ lease expiry / retry-safe recovery
```

Fallback path:

```text
AI_ACCEPTED / AI_DELIVERY_PENDING
→ fallback timer may inspect

fallback allowed ONLY when
AI delivery is definitively unavailable/failed/expired under contract

AI_DELIVERY_SENT
→ fallback forbidden
```

Use repository-native states if they already exist.

Do not create a second parallel queue if an authoritative one exists.

---

# 6. State identity contract

Every delivery-relevant artifact must bind to a canonical identity sufficient to prevent packet/run ambiguity.

At minimum resolve the native equivalents of:

```text
market
business_date
run_id
analysis_generation
packet_id
content_generation_id
delivery_generation_id
delivery_mode
recipient class
```

Do not key pending work only by a transient packet path if:
- backup reuse creates a new packet ID,
- accepted content belongs to an earlier analysis generation,
- retry searches by a different identity.

The task must explicitly answer:

```text
Why did primary receipt say pending 9
while retry said no_pending_ai_delivery?
```

with exact state keys and lookup predicates.

---

# 7. Analysis reuse vs delivery reuse

Natural evidence showed:

```text
16:20 analysis_action = reuse
16:50 analysis_action = reuse
```

A reused analysis must not accidentally sever accepted AI delivery ownership.

Define separately:

```text
analysis reuse
delivery reuse
```

Possible valid behavior:

```text
analysis already completed
but AI delivery still pending
→ backup/retry must continue the same delivery obligation
```

Invalid behavior:

```text
analysis already completed
→ assume nothing remains to deliver
```

unless authoritative delivery state is actually complete.

Required:

```text
ANALYSIS_REUSE_DOES_NOT_ERASE_PENDING_DELIVERY = PASS
```

---

# 8. Backup behavior

16:20 and 16:50 must be understood under the repaired contract.

If primary AI delivery is pending:

```text
backup may:
- claim/retry same pending delivery
or
- deliberately leave it for dedicated retry worker

backup must NOT:
- create a conflicting independent delivery state
- declare complete solely because analysis exists
```

If primary AI delivery is sent:

```text
backup must dedupe to zero sends
```

If AI path reaches terminal fallback condition:

```text
fallback may send exactly once
```

---

# 9. Exactly-once invariant

For one KR close run:

```text
one market message
eight stock messages
```

Final user-visible outcome must be exactly one mode per message:

```text
AI V2
or
deterministic fallback
```

Never both.

Required invariant:

```text
AI_SENT_COUNT + FALLBACK_SENT_COUNT = 9
DUPLICATE_COUNT = 0
```

For successful V2 live-path proof target:

```text
AI_SENT_COUNT = 9
FALLBACK_SENT_COUNT = 0
DUPLICATE_COUNT = 0
```

---

# 10. V2 selector / canary investigation

The natural run recorded:

```text
decision_canary_state = V2_DECISION_SUPPRESSED_SAFE
explicit_v2_count = 0
```

while the corrected AI candidate set was accepted.

Trace the exact ownership and decision path for:

```text
V2_DECISION_SUPPRESSED_SAFE
```

Answer:

```text
who sets it?
which persisted/config/runtime inputs control it?
is it market-level or subject-level?
is it adaptive canary only?
does it intentionally suppress explicit V2 delivery?
does accepted AI text remain eligible for AI-assisted delivery despite explicit V2 suppression?
```

Do not infer from name alone.

---

# 11. Canary scope issue

Natural run quality receipt covered only:

```text
market
000660
003690
```

three messages total.

Determine whether:
- this was intentionally only the adaptive canary subset,
- full 9-message validation happened elsewhere,
- explicit V2 promotion requires a different full-coverage gate,
- canary state is stale/misaligned with configured production intent.

Do not hardcode the KR8 tickers to force pass.

The selector must work generically from:
- validated subject coverage
- accepted-plan readiness
- configured rollout state
- current packet/run identity

---

# 12. V2 eligibility authority

There must be one clear answer for:

```text
Is this accepted message eligible to be sent as AI V2?
```

Do not allow:
- renderer says yes,
- selector says suppressed,
- delivery receipt says pending AI,
- retry says no AI pending

without a single authoritative resolution.

Create a compact persisted eligibility receipt or use the existing native equivalent.

It should explain:

```text
eligible = true/false
reason_code
scope
accepted_generation
selector_generation
delivery_generation
```

Do not expose internal reason codes to end users.

---

# 13. Explicit AI count semantics

Remove ambiguity between:
- market AI review
- stock V2 reviews

Use separate proof counts:

```text
EXPLICIT_AI_MARKET_COUNT
EXPLICIT_STOCK_V2_COUNT
EXPLICIT_AI_TOTAL_COUNT
```

Success target:

```text
EXPLICIT_AI_MARKET_COUNT = 1
EXPLICIT_STOCK_V2_COUNT = 8
EXPLICIT_AI_TOTAL_COUNT = 9
```

Do not use one ambiguous `explicit_v2_count` if it obscures market vs stock ownership.

---

# 14. Delivery enqueue transaction

Audit whether these happen atomically or can diverge:

```text
accepted artifact persistence
delivery-intent creation
pending queue persistence
fallback deadline persistence
```

If a crash or code path can create:

```text
accepted = yes
pending receipt = yes
but retry index = no
```

repair transaction boundaries or recovery indexing.

Required recovery property:

```text
accepted AI eligible for delivery
must be discoverable after process restart
```

---

# 15. Retry claim semantics

Trace exact retry query/filter.

Record:
- state queried
- market/date/run filters
- packet/generation filters
- lease/claim filters
- recipient/delivery-mode filters
- suppression filters
- dedupe filters

The repair must make:

```text
pending receipt
and
retry discoverability
```

derive from the same authoritative persisted state.

No shadow boolean that can diverge.

---

# 16. Fallback cancellation

When AI delivery completes:

```text
fallback obligation must become non-sendable
```

atomically or idempotently.

When AI delivery is still legitimately pending:

```text
fallback timer must not silently conclude "no AI pending"
```

unless its policy explicitly allows fallback due to timeout/deadline.

Record exact timeout/deadline semantics.

Do not shorten fallback deadline merely to make tests faster.

Test clocks may be injected using the production state machine's clock seam if one exists.

---

# 17. Process restart / scheduler boundary

The natural failure occurred across separate scheduler invocations.

Therefore test:

```text
process A:
accepted + enqueue pending
exit

process B:
retry/backup starts fresh
must discover same pending obligation
```

Do not prove only in one in-memory process.

This is mandatory.

---

# 18. File/path/environment parity

Previous live-only incidents have involved:
- cwd/path
- writable runtime state
- process namespace

Therefore the new live-path test must use the real production path resolution code.

Do not:
- replace `_paths()` with temp hand-built paths
- bypass scheduler env loading
- inject a fake queue implementation
- call a helper that skips selector/delivery state machine

Temporary/test namespaces are allowed only through the same production namespace-resolution seam.

---

# 19. Stop calling simplified replay "production-equivalent"

After this repair, reserve terms:

```text
unit/contract test
shadow/model replay
live-path E2E rehearsal
natural production
```

Do not label a replay that stops at:

```text
candidate
accepted
renderer
```

as:

```text
production-equivalent
```

The only acceptable production-path proof is:

```text
real production entrypoint
+ real runtime path resolution
+ real selector
+ real persistence
+ real queue
+ real retry/dedupe
+ real delivery adapter
+ real fallback state machine
```

with only recipient/delivery namespace safely redirected.

---

# 20. Test strategy after repair

Keep three layers only.

## Layer 1 — Unit / Contract

Keep fast tests for:
- schemas
- numeric provenance
- semantic provenance
- valuation safety
- renderer contracts
- queue state transitions
- dedupe keys

## Layer 2 — Single Live-Path E2E

This becomes the ONLY readiness proof for production orchestration.

## Layer 3 — Natural Production

Observe, do not use as first discovery environment for ordinary defects.

Do not delete useful unit tests.

Do delete or rename misleading "production-equivalent" claims that bypass live orchestration.

---

# 21. Live-path E2E — exact invocation principle

The rehearsal must enter through the same production entrypoint:

```text
python -m app.jobs.monitor_daily --market kr
```

or the exact repository-native wrapper the natural scheduler invokes.

It must use:
- same config loader
- same path resolver
- same selector/canary logic
- same accepted-plan persistence
- same delivery state
- same retry worker path
- same backup/dedupe path
- same fallback scheduler path
- same Telegram adapter

Only safe differences:

```text
recipient = dedicated TEST recipient
delivery namespace = isolated rehearsal namespace
clock/schedule = controlled only through native seams
external facts = frozen fixture/packet when necessary
```

Do not expose TEST recipient ID in artifacts.

---

# 22. Live-path E2E — frozen KR fixture

Use a deterministic KR8 fixture based on the accepted 2026-09-03 run-54 evidence/candidate set or another explicitly frozen fixture.

Purpose:
- orchestration proof, not market-data freshness.

Do not refetch today's market to make the test pass.

The model may be:
- actual signed-in Codex path if validating full live path,
or
- safely replayed already-accepted AI artifact ONLY in a separate delivery-state subtest.

At least one full E2E must include the real model path if the production job normally invokes it before enqueue.

---

# 23. Full E2E success chain

Required proof:

```text
SOURCE_READY                  8/8
TECHNICAL_READY               8/8
AI_READY                      8/8

MODEL_REACHED                 PASS
CANDIDATE_MARKET              1
CANDIDATE_STOCK               8
VALIDATED_ACCEPTED_TOTAL      9

EXPLICIT_AI_MARKET            1
EXPLICIT_STOCK_V2             8
EXPLICIT_AI_TOTAL             9

DELIVERY_PENDING_AFTER_ACCEPT 9
DELIVERY_DISCOVERED_BY_RETRY  9
DELIVERY_CLAIMED              9
AI_SENT                       9
AI_SENT_ACKNOWLEDGED          9

FALLBACK_ELIGIBLE_AFTER_AI    0
FALLBACK_SENT                 0
DUPLICATE_SENT                0
```

If the production architecture sends immediately without a separate retry claim,
adapt names but prove the same state continuity.

---

# 24. Process-boundary E2E

Mandatory second E2E variant:

```text
Phase 1 process
→ accepted 9
→ pending 9
→ process exits

Phase 2 fresh process
→ same production retry/backup entrypoint
→ discovers 9
→ sends exactly 9 to TEST
→ marks sent

Phase 3 fallback process
→ discovers zero eligible fallback
→ sends zero
```

This test directly targets the natural incident.

---

# 25. Backup/dedupe E2E

Test:

```text
primary successfully AI-sends 9

16:20-equivalent backup
→ analysis reuse is allowed
→ delivery sends 0
→ duplicate 0

16:50-equivalent late backup
→ sends 0

17:10-equivalent fallback
→ sends 0
```

All through real state/persistence code.

---

# 26. Failure-path E2E

Also prove deterministic fallback still works safely.

Inject one controlled terminal AI-delivery failure through a native test seam.

Expected:

```text
AI_SENT = 0
FALLBACK_SENT = 9
DUPLICATE = 0
```

Do not weaken AI validation to create failure.

Do not use an arbitrary production recipient.

---

# 27. Corrected-candidate path

Because run-54 initially failed validation and later corrected successfully, prove:

```text
initial candidate rejected
corrected candidate accepted
only corrected accepted generation becomes delivery-eligible
```

An initial rejected generation must never remain queue-discoverable.

Required:

```text
REJECTED_GENERATION_DELIVERY_ELIGIBLE = 0
```

---

# 28. Late validation / packet ownership audit

Audit packet:

```text
2026-09-03-kr-run-54-78ed269de3df
```

and its post-fallback validation.

Determine:
- which analysis generation it references
- why validation executed after fallback send
- why KR packet saw IWM/SPY semantic claims
- whether candidate/validation artifacts were copied/reused across market scopes
- whether market-scope identity is included in validator ownership keys
- whether late validation can mutate a delivered run's current status

Repair generically if ownership defect is confirmed.

Hard:

```text
CROSS_MARKET_VALIDATION_OWNERSHIP = 0
LATE_VALIDATION_CAN_MUTATE_SENT_DELIVERY = 0
```

Do not merely blacklist `IWM` or `SPY`.

---

# 29. Cross-market ownership rule

All candidate/validation artifacts must bind to:

```text
market
run/generation
packet
message identity
```

A KR validator must not accidentally consume a US market candidate from another generation.

Do not solve with symbol allowlists.

Use canonical ownership metadata.

---

# 30. Observability

Natural run should emit compact machine-readable stage receipts sufficient to identify the first failure without inference.

At minimum:

```text
analysis_ready
ai_ready
model_reached
candidate_created
validation_status
accepted_generation
v2_eligibility
delivery_pending
delivery_claimed
delivery_sent
fallback_eligible
fallback_sent
dedupe_result
```

Each receipt should include:
- market
- business date
- run/generation identity
- timestamp
- count
- reason code where relevant

Do not expose secrets.

---

# 31. Natural exit-code semantics

Today's primary exited `0` even though the intended AI V2 delivery never occurred.

Do not blindly change scheduler exit codes if fallback/hold behavior intentionally counts as successful orchestration.

Instead introduce a clearly observable result classification such as native equivalent of:

```text
AI_V2_DELIVERED
AI_V2_PENDING
FALLBACK_DELIVERED
NO_DELIVERY_ERROR
```

The scheduler may still exit `0` for safe fallback if that is intentional,
but monitoring must distinguish these states.

Required:

```text
EXIT_0_DOES_NOT_HIDE_DELIVERY_MODE = PASS
```

---

# 32. Selector and delivery must agree

Mandatory invariant after repair:

```text
if V2 eligibility = false:
AI delivery queue must explain why no AI send is expected

if AI delivery queue = pending:
V2/AI eligibility must support that pending obligation

if accepted AI is not delivery-eligible:
do not create an ambiguous pending AI receipt
```

No state combination equivalent to:

```text
SUPPRESSED_SAFE
+
pending 9
+
retry none
```

without explicit policy explanation.

---

# 33. No silent fallback after accepted V2

If accepted/eligible V2 exists but delivery cannot be completed:
- record explicit AI-delivery failure/timeout reason
- then fallback according to policy

Do not let the system silently drift into fallback because a retry lookup could not find the pending record.

Required:

```text
FALLBACK_AFTER_LOST_PENDING_STATE = 0
```

---

# 34. Migration / compatibility

If delivery-state schema/index changes:
- preserve existing history
- migrate safely or rebuild only derived indexes
- no destructive wipe of monitoring history
- no deletion of accepted-plan history

If an old pending row is ambiguous:
classify it explicitly rather than auto-sending.

---

# 35. Tests to keep

Do NOT remove:
- unit validators
- schema tests
- price/valuation safety tests
- renderer tests
- queue state-machine tests

They still catch cheap defects before the live-path rehearsal.

What changes:

```text
they are not sufficient to declare production readiness
```

---

# 36. Tests to retire or rename

Identify any tests/reports that claim:
- production equivalent
- production parity
- natural parity

while bypassing:
- scheduler entrypoint
- persisted queue
- retry
- dedupe
- fallback
- real delivery adapter

Rename them accurately, e.g.:

```text
MODEL_REPLAY
RENDERER_REPLAY
PACKET_REPLAY
```

Do not delete useful coverage solely for naming reasons.

---

# 37. Required reports

Create:

1. `docs/reports/20260903-run54-first-failure-state-map.md`
2. `docs/reports/20260903-run54-delivery-identity-key-audit.md`
3. `docs/reports/20260903-run54-pending-vs-retry-root-cause.md`
4. `docs/reports/20260903-v2-selector-canary-root-cause.md`
5. `docs/reports/20260903-v2-eligibility-authority.md`
6. `docs/reports/20260903-delivery-state-machine-repair.md`
7. `docs/reports/20260903-analysis-reuse-vs-delivery-reuse.md`
8. `docs/reports/20260903-retry-dedupe-fallback-repair.md`
9. `docs/reports/20260903-late-packet-validation-ownership-audit.md`
10. `docs/reports/20260903-live-path-e2e-contract.md`
11. `docs/reports/20260903-live-path-e2e-full-run.md`
12. `docs/reports/20260903-live-path-e2e-process-boundary.md`
13. `docs/reports/20260903-live-path-e2e-backup-dedupe.md`
14. `docs/reports/20260903-live-path-e2e-fallback-path.md`
15. `docs/reports/20260903-production-readiness-test-taxonomy.md`
16. `docs/reports/20260903-live-orchestration-repair-verdict.md`
17. `docs/reports/20260903-live-orchestration-artifact-index.md`

Machine-readable:

```text
20260903-run54-root-cause.json
20260903-delivery-state-transition-proof.json
20260903-live-path-e2e-proof.json
20260903-live-orchestration-repair-proof.json
```

---

# 38. Required gates

Set exactly:

```text
SOURCE_INCIDENT_RUN =
54

SOURCE_OPERATING_REVISION =
5d5f3363d3a762b62698943b1feb4fa121d0d0f9

CORRECTED_ACCEPTED_COUNT =
9 / OTHER

INITIAL_VALIDATION_REJECTION_FINAL_ROOT_CAUSE =
0 / NONZERO

PENDING_RETRY_STATE_MISMATCH_ROOT_CAUSE =
IDENTIFIED / NOT_IDENTIFIED

V2_SUPPRESSION_ROOT_CAUSE =
IDENTIFIED / NOT_IDENTIFIED

PRIMARY_ROOT_CAUSES_INDEPENDENT_OR_SHARED =
SHARED /
INDEPENDENT /
PARTIALLY_SHARED /
UNKNOWN

ANALYSIS_REUSE_DOES_NOT_ERASE_PENDING_DELIVERY =
PASS / FAIL

REJECTED_GENERATION_DELIVERY_ELIGIBLE =
0 / NONZERO

CROSS_MARKET_VALIDATION_OWNERSHIP =
0 / NONZERO

LATE_VALIDATION_CAN_MUTATE_SENT_DELIVERY =
0 / NONZERO

DUPLICATE_JUDGMENT_OR_DELIVERY_AUTHORITY =
0 / NONZERO

LIVE_PATH_USES_REAL_PRODUCTION_ENTRYPOINT =
PASS / FAIL

LIVE_PATH_USES_REAL_PATH_RESOLUTION =
PASS / FAIL

LIVE_PATH_USES_REAL_SELECTOR =
PASS / FAIL

LIVE_PATH_USES_REAL_PERSISTED_DELIVERY_STATE =
PASS / FAIL

LIVE_PATH_USES_REAL_RETRY_DEDUPE_FALLBACK =
PASS / FAIL

LIVE_PATH_USES_REAL_DELIVERY_ADAPTER =
PASS / FAIL

FULL_E2E_MODEL_REACHED =
PASS / FAIL

FULL_E2E_ACCEPTED_TOTAL =
9 / OTHER

FULL_E2E_EXPLICIT_AI_MARKET =
1 / OTHER

FULL_E2E_EXPLICIT_STOCK_V2 =
8 / OTHER

FULL_E2E_EXPLICIT_AI_TOTAL =
9 / OTHER

FULL_E2E_PENDING_AFTER_ACCEPT =
9 / OTHER

FULL_E2E_RETRY_DISCOVERED =
9 / OTHER

FULL_E2E_AI_SENT =
9 / OTHER

FULL_E2E_FALLBACK_SENT =
0 / OTHER

FULL_E2E_DUPLICATE_SENT =
0 / OTHER

PROCESS_BOUNDARY_PENDING_DISCOVERED =
9 / OTHER

PROCESS_BOUNDARY_AI_SENT =
9 / OTHER

PROCESS_BOUNDARY_FALLBACK_SENT =
0 / OTHER

BACKUP_AFTER_AI_SEND_SENT_COUNT =
0 / OTHER

FALLBACK_AFTER_AI_SEND_SENT_COUNT =
0 / OTHER

CONTROLLED_FAILURE_AI_SENT =
0 / OTHER

CONTROLLED_FAILURE_FALLBACK_SENT =
9 / OTHER

CONTROLLED_FAILURE_DUPLICATE_SENT =
0 / OTHER

FALLBACK_AFTER_LOST_PENDING_STATE =
0 / NONZERO

EXIT_0_DOES_NOT_HIDE_DELIVERY_MODE =
PASS / FAIL

MISLEADING_PRODUCTION_EQUIVALENT_LABELS =
0 / NONZERO

PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_STATE_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

REPAIR_VERDICT =
READY_FOR_NATURAL_PROOF /
NEEDS_MORE_REPAIR /
NOT_READY
```

---

# 39. Completion response

Return:

```text
RUN54 ROOT CAUSE =
...

PENDING 9 vs NO_PENDING =
exact cause ...

V2_DECISION_SUPPRESSED_SAFE =
exact cause ...

SHARED OR INDEPENDENT =
...

REPAIRS =
...

LATE PACKET / IWM-SPY OWNERSHIP =
...

LIVE-PATH E2E =
full run ...
process-boundary ...
backup/dedupe ...
controlled fallback ...

READINESS TEST POLICY =
unit/contract ...
live-path E2E ...
natural production ...

REPAIR_VERDICT =
...

PRODUCTION SEND = 0
MAIN MERGE = 0

ZIP = ...
ZIP_SHA256 = ...
```

Do not claim success if only candidate/accepted replay passes.

---

# 40. Completion ZIP

Create:

`20260903-kr-live-v2-delivery-orchestration-repair-and-live-path-e2e-bundle.zip`

Include:
- exact work instruction
- implementation diff
- root-cause reports
- selector/canary audit
- delivery-state schema/index changes
- retry/dedupe/fallback tests
- exact live-path E2E command/environment manifest with secrets redacted
- process-boundary evidence
- test-recipient delivery receipts with recipient ID redacted
- machine-readable proof JSON
- artifact index
- secret scan
- git diff check
- test results

Exclude:
- production recipient IDs
- TEST recipient ID
- auth/session tokens
- credentials
- state DB contents
- hidden chain-of-thought

Compute SHA-256.

---

# 41. Final principle

Do not remove testing.

Remove the false confidence created by tests that bypass the production orchestration path.

After this repair:

```text
unit/contract tests
= development safety

live-path E2E through the real production entrypoint
= production readiness proof

natural production
= final real-world observation
```

The model already produced an accepted KR9 set on run-54.

The repair target is to make the real live system reliably deliver that accepted result exactly once.
