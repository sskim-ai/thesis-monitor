# thesis-monitor — KR Explicit V2 Child Wait Ownership Repair
## Fix premature outer Ctrl-C
## Add generation-aware wait + terminal interruption receipt
## Prove KR explicit V2 with real TEST E2E
## Regress shared US path
## Strengthen natural-proof mode accounting
## Do NOT modify investment judgment logic

---

# 0. Source and scope

This work item is based on the read-only forensic report for the
2026-09-04 KR natural V2 failure.

Authoritative forensic finding:

```text
16:25:31
primary starts explicit stock V2 / stock_decision

child command-owned timeout =
1800 seconds

16:25:32
V2 model batch starts

16:28:20
outer automation sends Ctrl-C

actual elapsed before interruption =
about 168.3 seconds
```

At interruption:

```text
persisted explicit-V2 candidate = 0
claim-bound accepted V2 artifact = absent
V2 completion receipt = absent
```

Later:

```text
regular AI review
→ bounded correction
→ accepted 9/9
→ KR Pilot AI-assisted delivery 9/9

backup later ran the same explicit-V2 path
→ stock V2 accepted 8/8
→ terminal production delivery already existed
→ archive-only / no duplicate
```

Therefore the first material failure was:

```text
OUTER_ORCHESTRATION_PREMATURE_CHILD_INTERRUPT
```

Not:
- TLS
- claim/lease loss
- candidate semantic failure
- stock validator failure
- renderer content failure
- accounting/provenance failure

Do not reopen those layers without new evidence.

---

# 1. Required base

Start from current main/operating code that already contains the integrated
KR + US infrastructure repairs.

Known prior integrated operating SHA from the forensic context:

```text
906b092749511dc42d5799ed335165819efee2ea
```

Use that SHA or a verified descendant containing the same repair lineages.

Before implementation:

```text
BASE_SHA = ...
BASE_CONTAINS_KR_REPAIR = PASS
BASE_CONTAINS_US_TLS_LEASE_VALIDATOR_REPAIR = PASS
BASE_CONTAINS_KR_US_INTEGRATION = PASS
```

Do not base this repair on an older pre-integration branch.

Suggested branch:

```text
codex/20260904-kr-v2-child-wait-ownership-repair
```

Work-instruction commit first.

---

# 2. Exact repair targets from the forensic report

Primary targets:

```text
.agents/skills/thesis-monitor-daily-review/SKILL.md
  → step 6 bounded canary / V2 wait contract

app/jobs/stock_decision.py
  → _run

app/jobs/accepted_decision_v2_runtime.py
  → generate
  → _safe_suppression_receipt
```

Persisted state/contracts:

```text
accepted-v2-generation-stage-v1
v2-accepted-production-receipt-v1
```

If implementation reveals a different exact function owns the premature
interrupt, document it before editing.

No ticker-specific logic.

---

# 3. Core design principle — one timeout owner

The child command had an explicit 1800-second timeout.

The outer automation must not silently enforce a shorter independent
~168-second lifetime.

Required contract:

```text
COMMAND_OWNED_TIMEOUT
is authoritative for model generation

OUTER_ORCHESTRATION
waits for:
- explicit terminal receipt
- authorized cancellation
- authoritative outer hard-deadline policy
```

If an outer hard deadline exists, it must be:
- explicit
- configured
- documented
- coordinated with child timeout and cleanup margin
- never an accidental client/tool wait limit

Forbidden sole fix:

```text
168 sec → 300 sec
168 sec → 600 sec
```

Do not just move the race.

---

# 4. Active child ownership semantics

The outer waiter must be able to distinguish:

```text
child healthy and progressing
vs
child terminal
vs
child stalled
vs
child interrupted
```

Prefer persisted generation-stage state over inferring from lack of a
candidate file.

Repository-native equivalent stages should cover:

```text
STARTED
MODEL_ACTIVE
CANDIDATE_PERSISTED
VALIDATING
ACCEPTED
SUPPRESSED
FAILED
INTERRUPTED
TERMINAL
```

Exact enum names may differ.

Required:

```text
ACTIVE_CHILD_WITH_NO_CANDIDATE_YET
!=
FAILED_CHILD
```

This directly prevents recurrence of the 2026-09-04 incident.

---

# 5. Wait loop requirements

The orchestration waiter should:

```text
start child
record generation identity
observe low-frequency persisted stage / process result
continue waiting while stage is active and authorized deadline remains
return only on terminal condition
```

Do not use aggressive polling.

Do not create heavy load.

Do not rely only on stdout silence.

Do not interpret:
```text
candidate not yet persisted
```
as a failure.

---

# 6. Process and claim identity

Every observed V2 stage/receipt must remain bound to the correct:

```text
market
business_date
packet_id
run_id
claim owner
fencing token / claim generation
V2 generation
```

The waiter must not accidentally accept:
- a previous generation's receipt
- backup generation output
- another market's output

Required:

```text
CROSS_GENERATION_RECEIPT_ACCEPT = 0
CROSS_CLAIM_RECEIPT_ACCEPT = 0
```

---

# 7. Preserve existing lease / fencing repair

Do not replace the already-proven heartbeat/lease/fencing mechanism.

The V2 wait repair is above that layer.

Required:

```text
HEALTHY_PRIMARY_BACKUP_RECLAIM = 0
STALE_PRIMARY_RECLAIM = PASS
STALE_PRIMARY_FINALIZE = REJECTED
```

A healthy explicit-V2 child must keep its normal claim lifecycle.

---

# 8. Authorized interruption

There are legitimate reasons to stop a child:
- explicit operator cancellation
- command-owned timeout terminal
- production hard deadline
- lost fencing ownership
- process shutdown

When one occurs, it must be represented as an explicit reason.

Suggested equivalent reason taxonomy:

```text
COMMAND_TIMEOUT
AUTHORIZED_CANCEL
PRODUCTION_DEADLINE
CLAIM_OWNERSHIP_LOST
PROCESS_SHUTDOWN
OTHER_INTERRUPTION
```

Do not classify an accidental caller timeout as a normal model failure.

---

# 9. Graceful interruption receipt

The forensic run ended the primary V2 path with Ctrl-C before a final V2
receipt existed.

Repair this.

On SIGINT/SIGTERM/authorized cancellation, use repository-native handling so
the generation becomes terminal where technically possible.

Persist an equivalent of:

```text
generation_id
claim/fencing identity
terminal_state
interruption_reason
completed_at
candidate_persisted?
accepted?
delivery_eligible?
compatibility/fallback eligibility
```

Required:

```text
INTERRUPTED_CHILD_AMBIGUOUS_IN_PROGRESS = 0
TRACEBACK_ONLY_TERMINAL_STATE = 0
```

Do not fabricate accepted output.

---

# 10. `_safe_suppression_receipt`

Review and, if appropriate, extend:

```text
accepted_decision_v2_runtime.py::_safe_suppression_receipt
```

It should safely represent a terminal no-V2 outcome when the generation
cannot complete.

It must not:
- mark a partial candidate accepted
- steal another generation's delivery ownership
- suppress a valid completed V2 artifact
- create duplicate delivery eligibility

---

# 11. `stock_decision.py::_run`

Review signal/KeyboardInterrupt/subprocess handling.

Required behavior:

```text
normal completion
→ persist normal terminal artifact

command timeout
→ terminal timeout/suppression state

authorized SIGINT/SIGTERM
→ terminal interruption/suppression state where safe

unexpected exception
→ explicit failure state + audit
```

Avoid broad exception handling that masks real defects.

---

# 12. Skill / outer automation contract

Update the daily-review skill only if that is truly the source of the
premature Ctrl-C.

The skill must say:

```text
Do not manually interrupt a healthy stock_decision V2 child merely because
the outer interactive wait has been several minutes.

Respect the command-owned timeout and persisted V2 generation state.

If the client session itself cannot wait, detach/use the repository-native
supervised execution path rather than sending Ctrl-C.
```

Do not rely on human patience as a runtime contract.

---

# 13. Do not let regular AI compatibility preempt healthy V2

In the forensic run, regular AI reached accepted 9/9 shortly after primary
V2 was interrupted and the Pilot renderer delivered.

Compatibility delivery remains a valid safety path, but it must not preempt
a healthy explicit-V2 generation that is still inside its authorized V2
window.

Required decision order:

```text
explicit V2 terminal accepted
→ explicit V2 delivery

explicit V2 still healthy/active
→ wait, while V2 deadline allows

explicit V2 terminal failed/suppressed/timed out
OR hard send deadline reached
→ compatibility/fallback path may proceed
```

Do not remove the compatibility path.

---

# 14. Preserve KR Pilot compatibility safety

`KR Pilot 5/5` was a supported AI-assisted compatibility renderer, not
deterministic fallback.

Keep it available for genuine V2 failure/deadline protection.

But distinguish it in telemetry and readiness.

Required:

```text
KR_PILOT_AI_ASSISTED
!=
EXPLICIT_V2_AI
```

---

# 15. Natural-proof gate must be stricter

Do not report natural V2 PASS merely because:

```text
accepted AI reached production recipient
```

That condition allowed the 2026-09-04 Pilot delivery to be mislabeled as a
successful infrastructure natural proof.

Track independently:

```text
AI_ACCEPTED_TOTAL
AI_MARKET_SENT
EXPLICIT_V2_STOCK_ACCEPTED
EXPLICIT_V2_STOCK_SENT
KR_PILOT_AI_ASSISTED_SENT
DETERMINISTIC_FALLBACK_SENT
DUPLICATE_SENT
```

KR explicit-V2 natural success requires:

```text
AI_MARKET_SENT = 1
EXPLICIT_V2_STOCK_ACCEPTED = 8
EXPLICIT_V2_STOCK_SENT = 8
KR_PILOT_AI_ASSISTED_SENT = 0
DETERMINISTIC_FALLBACK_SENT = 0
DUPLICATE_SENT = 0
```

---

# 16. No judgment-logic changes

This repair is orchestration only.

Required:

```text
INVESTMENT_JUDGMENT_LOGIC_CHANGED = 0
VALIDATOR_THRESHOLD_WEAKENED = 0
RENDERER_SEMANTIC_POLICY_CHANGED = 0
TICKER_SPECIFIC_EXCEPTION = 0
```

Do not change:
- BUY/HOLD/SELL logic
- market expectations
- valuation framework
- holder/new-buyer semantics
- KR accounting rules
- price/supply provenance rules

---

# 17. Incident regression test — premature 168-second interrupt

Create an exact incident-class regression.

The test must prove:

```text
child command timeout > outer historical 168-second boundary
child remains healthy
candidate may still be absent at 168 seconds

expected:
outer does NOT send Ctrl-C
outer continues waiting
```

Use a controlled clock/fake child/prod-equivalent integration harness where
possible.

Do not burn a literal 30-minute model call just to test the clock.

---

# 18. Real KR signed-in TEST E2E

After deterministic tests pass, execute one real KR production-entrypoint
E2E to a dedicated TEST recipient.

Use:
- real KR packet path
- real signed-in CLI
- real V2 runtime
- real claim/heartbeat/fencing
- real validator
- real renderer
- real Telegram adapter
- TEST recipient only

Required:

```text
AI_MARKET_SENT = 1

EXPLICIT_V2_STOCK_ACCEPTED = 8
EXPLICIT_V2_STOCK_SENT = 8

KR_PILOT_AI_ASSISTED_SENT = 0
DETERMINISTIC_FALLBACK_SENT = 0
DUPLICATE_SENT = 0

TLS_UNKNOWN_ISSUER = 0

HEALTHY_PRIMARY_BACKUP_RECLAIM = 0
```

---

# 19. E2E duration evidence

Record:

```text
stock V2 child start
model batch start/end
candidate persist time
validation time
accepted time
delivery time
outer waiter lifetime
```

If the child naturally exceeds 168 seconds and succeeds, preserve that as
strong recurrence proof.

Do not optimize model duration merely to make the test pass faster.

---

# 20. Controlled command-timeout scenario

Use a configurable short timeout in test only.

Expected:

```text
child reaches its authoritative command timeout
outer does not interrupt earlier
terminal timeout/suppression receipt exists
compatibility/fallback remains eligible
no partial V2 send
duplicate = 0
```

Do not change production timeout merely for this test.

---

# 21. Controlled authorized-interruption scenario

Send an authorized test SIGINT/SIGTERM to the child.

Expected:

```text
terminal interruption receipt = PASS
ambiguous active generation = 0
partial V2 send = 0
compatibility/fallback eligibility preserved
duplicate = 0
```

---

# 22. Late V2 after compatibility/fallback

Controlled race:

```text
hard send deadline reached
compatibility/fallback becomes terminal
late V2 artifact appears
```

Expected:

```text
late V2 archived/superseded/deduped
late V2 sent = 0
duplicate = 0
```

Preserve exactly-once delivery.

---

# 23. Backup regression

Controlled cases:

Healthy primary:
```text
V2 active
heartbeat fresh
backup schedule fires
→ backup reclaim = 0
```

Stale/dead primary:
```text
heartbeat stops
lease expires
→ backup reclaim = PASS
→ old primary finalization fenced
```

Do not alter existing proven claim semantics unless a regression is found.

---

# 24. Shared US regression

The daily-review skill and accepted V2 runtime may be shared by KR and US.

If any shared code changes, run one real production-entrypoint US TEST E2E.

Required:

```text
US_AI_MARKET_SENT = 1
US_EXPLICIT_V2_STOCK_ACCEPTED = 14
US_EXPLICIT_V2_STOCK_SENT = 14

US_COMPATIBILITY_FALLBACK_SENT = 0
US_DETERMINISTIC_FALLBACK_SENT = 0
US_DUPLICATE_SENT = 0

US_TLS_UNKNOWN_ISSUER = 0
US_HEALTHY_PRIMARY_BACKUP_RECLAIM = 0
```

If code is proven KR-only, document why the real US E2E is not required and
still run shared focused regression tests.

---

# 25. Full tests

Run:

```text
focused wait/timeout ownership tests
generation-stage state tests
signal/interruption receipt tests
claim/fencing regressions
Pilot/compatibility ordering tests
exactly-once delivery tests
KR V2 selector/renderer tests
KR accounting/valuation safety regressions
shared US V2 regressions

real KR TEST E2E
real US TEST E2E if shared path changed

full pytest
Ruff
git diff --check
Knowledge validation
Public Action validation
secret scan
```

Do not delete or weaken tests.

---

# 26. Production safety during testing

Required:

```text
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
PRODUCTION_DB_MUTATION = 0
```

TEST deliveries only.

Before main merge:
```text
MAIN_MERGE = 0
```

---

# 27. Main merge readiness

Ready only if:

```text
PREMATURE_CHILD_INTERRUPT = 0
KR real TEST explicit V2 = 8/8
KR Pilot = 0
KR fallback = 0
KR duplicate = 0

shared US regression = PASS where applicable

full CI = PASS
```

Then:

```text
READINESS = READY_FOR_MAIN
```

After approved merge/deploy:
record `MAIN_SHA` and `OPERATING_SHA`.

---

# 28. Natural proof after merge

Next KR natural run must be evaluated with the new strict gate.

Success:

```text
AI market 1
explicit stock V2 8
Pilot 0
deterministic fallback 0
duplicate 0
```

If:
```text
Pilot > 0
```
then the run is not an explicit-V2 natural proof even if all messages were
AI-assisted and delivered exactly once.

---

# 29. Structured Autonomy handoff

After this infrastructure repair is merged, continue the separate
Structured Autonomy promotion-review program.

Do not mix its changes into this repair.

The shadow/promotion program may continue while waiting for the next natural
KR proof.

Actual production activation of:
- BUY / HOLD / SELL
- BUY:SELL balance
- new-buyer stance
- holder stance
- entry/trim/review scenarios

remains separately gated by:
1. Structured Autonomy promotion readiness
2. clean production infrastructure natural proof

---

# 30. Required reports

Create:

1. `docs/reports/20260904-kr-v2-premature-interrupt-root-cause-lock.md`
2. `docs/reports/20260904-v2-timeout-ownership-contract.md`
3. `docs/reports/20260904-v2-generation-stage-contract.md`
4. `docs/reports/20260904-v2-interruption-terminal-receipt.md`
5. `docs/reports/20260904-kr-v2-compatibility-ordering.md`
6. `docs/reports/20260904-kr-v2-168s-regression.md`
7. `docs/reports/20260904-kr-v2-real-test-e2e.md`
8. `docs/reports/20260904-v2-timeout-interruption-matrix.md`
9. `docs/reports/20260904-v2-late-output-exactly-once.md`
10. `docs/reports/20260904-us-shared-v2-regression.md`
11. `docs/reports/20260904-v2-natural-proof-gate.md`
12. `docs/reports/20260904-kr-v2-repair-readiness.md`
13. `docs/reports/20260904-kr-v2-repair-artifact-index.md`

Machine-readable:

```text
20260904-v2-wait-contract-proof.json
20260904-v2-interruption-proof.json
20260904-kr-v2-test-e2e-proof.json
20260904-us-v2-regression-proof.json
20260904-kr-v2-repair-proof.json
```

---

# 31. Required gates

```text
SOURCE_FORENSIC_ROOT_CAUSE =
OUTER_ORCHESTRATION_PREMATURE_CHILD_INTERRUPT

BASE_SHA =
...

COMMAND_OWNED_TIMEOUT_SEC =
1800

FORENSIC_PREMATURE_INTERRUPT_SEC =
168.3

SINGLE_AUTHORITATIVE_TIMEOUT_OWNER =
PASS / FAIL

OUTER_SHORTER_HIDDEN_TIMEOUT =
0 / NONZERO

PREMATURE_CHILD_CTRL_C =
0 / NONZERO

ACTIVE_CHILD_NO_CANDIDATE_TREATED_AS_FAILURE =
0 / NONZERO

V2_GENERATION_STAGE_PERSISTED =
PASS / FAIL

INTERRUPTION_TERMINAL_RECEIPT =
PASS / FAIL

TRACEBACK_ONLY_TERMINAL_STATE =
0 / NONZERO

CROSS_GENERATION_RECEIPT_ACCEPT =
0 / NONZERO

CROSS_CLAIM_RECEIPT_ACCEPT =
0 / NONZERO

HEALTHY_PRIMARY_BACKUP_RECLAIM =
0 / NONZERO

STALE_PRIMARY_RECLAIM =
PASS / FAIL

STALE_PRIMARY_FINALIZE =
REJECTED / OTHER

KR_TEST_AI_MARKET_SENT =
1 / OTHER

KR_TEST_EXPLICIT_V2_STOCK_ACCEPTED =
8 / OTHER

KR_TEST_EXPLICIT_V2_STOCK_SENT =
8 / OTHER

KR_TEST_PILOT_AI_ASSISTED_SENT =
0 / NONZERO

KR_TEST_DETERMINISTIC_FALLBACK_SENT =
0 / NONZERO

KR_TEST_DUPLICATE_SENT =
0 / NONZERO

KR_TEST_TLS_UNKNOWN_ISSUER =
0 / NONZERO

US_SHARED_PATH_CHANGED =
YES / NO

US_TEST_AI_MARKET_SENT =
1 / OTHER / NOT_REQUIRED

US_TEST_EXPLICIT_V2_STOCK_ACCEPTED =
14 / OTHER / NOT_REQUIRED

US_TEST_EXPLICIT_V2_STOCK_SENT =
14 / OTHER / NOT_REQUIRED

US_TEST_FALLBACK_SENT =
0 / NONZERO / NOT_REQUIRED

US_TEST_DUPLICATE_SENT =
0 / NONZERO / NOT_REQUIRED

US_TEST_TLS_UNKNOWN_ISSUER =
0 / NONZERO / NOT_REQUIRED

INVESTMENT_JUDGMENT_LOGIC_CHANGED =
0 / NONZERO

VALIDATOR_THRESHOLD_WEAKENED =
0 / NONZERO

RENDERER_SEMANTIC_POLICY_CHANGED =
0 / NONZERO

TICKER_SPECIFIC_EXCEPTION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

READINESS =
READY_FOR_MAIN /
NEEDS_MORE_REPAIR /
NOT_READY

MAIN_MERGE =
0 / 1

MAIN_SHA =
... / NOT_MERGED

OPERATING_SHA =
... / NOT_DEPLOYED
```

---

# 32. Completion response

Return:

```text
BASE =
...

ROOT CAUSE LOCK =
...

WAIT / TIMEOUT OWNERSHIP =
...

GENERATION STAGE =
...

INTERRUPTION RECEIPT =
...

168s REGRESSION =
...

KR REAL TEST =
AI market ...
explicit V2 ...
Pilot ...
fallback ...
duplicate ...
duration ...

BACKUP / FENCING =
...

US SHARED REGRESSION =
...

NATURAL PROOF GATE =
...

FULL TESTS =
...

READINESS =
...

PRODUCTION SEND = 0
SCHEDULER CHANGE = 0
DB MUTATION = 0

MAIN MERGE =
...

STRUCTURED AUTONOMY =
not modified
handoff status ...

ZIP =
...
ZIP_SHA256 =
...
```

---

# 33. Stop conditions

Stop if implementation requires weakening TLS, claim fencing, validator, or
exactly-once delivery.

Stop main readiness if:
- child is still interrupted before command-owned timeout without an
  authoritative production deadline
- KR explicit V2 != 8/8
- Pilot > 0 in the success E2E
- duplicate > 0
- healthy primary backup reclaim > 0

Do not tune model output to solve an orchestration failure.

---

# 34. Final principle

The 2026-09-04 KR failure was not:

```text
"the model needed too long"
```

It was:

```text
"the child was allowed 1800 seconds,
but the outer automation killed a healthy generation after ~168 seconds."
```

Repair ownership of waiting and termination.

Let the explicit V2 child either:
- complete,
- reach its own authoritative timeout,
- or end through an explicit authorized terminal condition.

Never convert an outer client's impatience into a model failure.
