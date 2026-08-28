# thesis-monitor — RUN NOW: One-Shot KR Close Live Proof
## Standalone execution instruction
## Schedule the regular KR close production job once for +5 minutes after this instruction starts
## Use fresh data and real Telegram production delivery
## No second automatic retry

---

# 0. Purpose

The prior convergence task is already complete.

This file is the ONLY instruction needed now.

Goal:

```text
1. Reconfirm latest operating / convergence gates
2. Schedule one regular KR close production job for execution_time + 5 minutes
3. Let it collect fresh KR data through the normal production path
4. Send the real KR market + monitored-stock Telegram messages
5. Verify V3 validator ownership / Price Structure / Bollinger / price labels
6. Verify exactly-once delivery
7. Remove/consume the temporary one-shot schedule
8. Leave the normal recurring schedule unchanged
```

Do not run the old standalone hotfix.
Do not rerun the old convergence instruction.
Do not create a test-only substitute for this live proof.

---

# 1. Latest validated baseline

Latest verified convergence result:

```text
FINAL_MAIN / OPERATING =
23b17c487a4c0ae7dc56935e9028cf62f2b00f2c

RUN44_000660_FROZEN_REPLAY = PASS
RUN44_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED = 0

LATEST_RUNTIME_ALREADY_FIXED = YES
RUNTIME_HOTFIX_REQUIRED = NO

KR7_V3_VALIDATOR_REPLAY = PASS
US_CURRENT_MONITORED_V3_VALIDATOR_REPLAY = PASS

KR_CLOSE_TEST_BATCH_COMPLETES = PASS
TEST_EXACT_PAYLOAD_MATCH = PASS
CROSS_MARKET_MESSAGE_QUALITY = PASS

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Validated convergence bundle SHA-256:

```text
3f8e1b43e3d95935c82e6473d01169f04bc9c59cbad25b602fc379adc1045791
```

Before scheduling:

```text
git fetch origin
confirm actual origin/main
confirm actual operating checkout
confirm operating is 23b17c... or a safe linear descendant
confirm no new P0/material P1
```

If operating lineage is not safely reconciled:

STOP.

---

# 2. Operator authorization

The operator explicitly authorizes:

```text
ONE production-equivalent KR close rerun today
scheduled exactly once for +5 minutes
```

This authorization applies only to this single live proof.

Do not create:

```text
multiple one-shots
manual immediate production execution
automatic second retry
new recurring schedule
alternate delivery pipeline
```

---

# 3. Schedule timing

At the moment this instruction reaches its scheduling step:

```text
PASS_TIME_KST = actual current KST time
SCHEDULED_TIME_KST = PASS_TIME_KST + 5 minutes
```

Do not hard-code 18:27 or any other clock value.

Use the actual execution-time clock.

Hard:

```text
ONE_SHOT_KR_CLOSE_SCHEDULE_COUNT = 1
```

---

# 4. Reuse the existing regular KR close job definition

The one-shot MUST invoke the SAME job definition/configuration used by the normal KR close production schedule.

Reuse:

```text
same command / task definition
same environment
same provider configuration
same monitored universe
same packet path
same renderer
same validator
same notification path
same production Telegram destination
```

Do not copy business logic into a new script.

Hard:

```text
REGULAR_JOB_DEFINITION_REUSED = PASS
```

---

# 5. Normal recurring schedule must remain unchanged

Before the one-shot:

record the normal recurring KR close schedule.

After scheduling:

prove it is unchanged.

After the one-shot completes:

prove it is still unchanged.

Hard:

```text
NORMAL_RECURRING_SCHEDULE_CHANGED = 0
```

---

# 6. Fresh-data production path

This live proof must use fresh acquisition at the one-shot execution time:

```text
current KR market data
current KOSPI/KOSDAQ
current breadth
current participant flow
current size/style
current sector data
current monitored KR stocks
current quote / completed-session close
current Price Structure inputs
```

Do NOT use:

```text
run-44 frozen data
test fixture
cached static report data
manual fake values
```

for the actual production proof.

---

# 7. Production pipeline that must execute

Required path:

```text
fresh collection
→ packet creation
→ KR market digest
→ monitored-stock context
→ Price Structure v3
→ completed Bollinger
→ provisional Bollinger when selected/material
→ V3 render plan
→ renderer
→ validator
→ notification service
→ real Telegram production delivery
```

Do not skip the validator.

Do not suppress validator exceptions.

---

# 8. KR market message live proof

Verify the delivered market message contains the currently intended KR product surface:

```text
KOSPI / KOSDAQ
breadth
participant flow
size/style
sector TOP3
```

Check actual received Telegram text.

Hard:

```text
LIVE_KR_MARKET_MESSAGE = PASS
```

---

# 9. KR stock live proof

Verify every monitored KR stock message emitted by the one-shot.

Expected current control universe has historically included:

```text
000660
003690
005490
005930
010120
012450
086280
```

Use the ACTUAL monitored KR universe at execution time.

For every emitted stock message check:

```text
company header
current price ownership
price-structure basis close
near support
near resistance
major structural support/resistance only when price-anchored
completed Bollinger dynamic reference when material
provisional Bollinger reference when selected/material
stored monitoring price rules separately labeled
no target price
no stop price
```

Hard:

```text
LIVE_KR_STOCK_MESSAGES = PASS
```

---

# 10. Price-label clarity

When current quote and Price Structure basis differ:

render clearly:

```text
• 현재가: ...
• 가격 구조 기준 종가(정규장): ...
```

If the backend has a verified quote-session state, it may use:

```text
현재가(시간외)
현재가(장중)
```

but do not infer session state without evidence.

Hard:

```text
LIVE_AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL = 0
```

---

# 11. Major S/R Reality Gate

Preserve the current structural contract:

```text
주요 구조 지지/저항
→ real price-anchor required
```

Bollinger-only derived values must not be relabeled as major structural.

Hard:

```text
LIVE_BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
LIVE_MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0
```

---

# 12. Completed Bollinger layer

Completed-bar dynamic Bollinger may appear as:

```text
볼린저 지지(...)
볼린저 저항(...)
```

when selected/material.

It must remain semantically separate from:

```text
주요 구조 지지/저항
```

---

# 13. Provisional Bollinger layer

Valid in-progress D/W/M Bollinger may appear only when selected/material.

Required semantic style:

```text
잠정 볼린저 지지(<timeframe>·진행중)
잠정 볼린저 저항(<timeframe>·진행중)
```

Optional suffix:

```text
봉 마감 전 변동 가능
```

Hard:

```text
LIVE_PROVISIONAL_BOLLINGER_AS_NEAR_SR = 0
LIVE_PROVISIONAL_BOLLINGER_AS_MAJOR_SR = 0
LIVE_PROVISIONAL_BOLLINGER_AS_STORED_RULE = 0
```

---

# 14. Critical run-44 incident live check

The historical production failure was:

```text
fallback_dynamic_resistance_not_rendered
```

For the one-shot live run:

record, especially for `000660` and any stock with multiple dynamic candidates:

```text
selected V3 fact refs
selected confluence refs
omitted candidate refs
omission reasons
validator-required refs
validator result
```

The invariant:

```text
intentional V3 omission
≠ missing-render validation failure
```

Hard:

```text
LIVE_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED = 0
```

---

# 15. Validator strictness negative invariant

Do not weaken the validator during the live proof.

If V3 selects a fact and the renderer fails to render it:

the validator must still fail.

No catch-and-continue workaround.

Hard:

```text
NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED = 0
```

---

# 16. Exactly-once live delivery

Record:

```text
ONE_SHOT_RUN_ID
ONE_SHOT_PACKET_ID
delivery intents
Telegram message/receipt identities
```

Verify:

```text
one KR market message
one message per intended monitored KR stock
no duplicate
no orphan
no unowned retry
```

Hard:

```text
LIVE_DUPLICATE = 0
LIVE_ORPHAN = 0
LIVE_UNOWNED_RETRY = 0
```

---

# 17. No automatic second one-shot

Do not pre-create a retry.

If this one-shot fails:

```text
STOP
collect evidence
report exact failure
```

Do not schedule a second production execution without new operator authorization.

Hard:

```text
AUTOMATIC_SECOND_ONE_SHOT_CREATED = 0
```

---

# 18. Scheduler cleanup

After the one-shot finishes, PASS or FAIL:

verify the temporary one-shot schedule is consumed or removed.

Required:

```text
RESIDUAL_ONE_SHOT_SCHEDULE_COUNT = 0
```

The normal recurring schedule must still exist unchanged.

---

# 19. No unrelated code changes

This is primarily a live-proof operation.

Do not modify runtime code unless the one-shot scheduling mechanism itself exposes a new blocking defect before execution.

Do not refactor:

```text
Price Structure
Bollinger
validator
market message
notification
```

as part of this instruction.

The code was already converged/tested.

---

# 20. Pre-schedule health check

Immediately before scheduling verify:

```text
API health = PASS
scheduler health = PASS
provider dependencies required for KR close = available or normal fail-closed
operating checkout = expected
active duplicate KR close job = 0
residual one-shot = 0
```

If another KR close production execution is already active:

do not create the one-shot.

---

# 21. Required reports

Create:

1. `docs/reports/20260828-run-now-kr-close-preflight.md`
2. `docs/reports/20260828-run-now-kr-close-schedule.md`
3. `docs/reports/20260828-run-now-kr-close-live-run.md`
4. `docs/reports/20260828-run-now-kr-market-exact-message.md`
5. `docs/reports/20260828-run-now-kr-stock-exact-messages.md`
6. `docs/reports/20260828-run-now-kr-v3-validator-proof.md`
7. `docs/reports/20260828-run-now-kr-delivery-proof.md`
8. `docs/reports/20260828-run-now-kr-scheduler-cleanup.md`
9. `docs/reports/20260828-run-now-kr-final-status.md`
10. `docs/reports/20260828-run-now-kr-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-run-now-kr-live-proof.json
```

---

# 22. Required gates

Set exactly:

```text
OPERATING_BEFORE =
...

LATEST_MAIN_BEFORE =
...

OPERATING_LINEAGE_SAFE =
PASS / FAIL

PRECONDITION_ALL_GATES_PASS =
PASS / FAIL

PASS_TIME_KST =
...

SCHEDULED_TIME_KST =
...

ONE_SHOT_KR_CLOSE_SCHEDULE_COUNT =
1 / OTHER

REGULAR_JOB_DEFINITION_REUSED =
PASS / FAIL

NORMAL_RECURRING_SCHEDULE_CHANGED =
0 / NONZERO

PRE_SCHEDULE_ACTIVE_KR_CLOSE_COUNT =
0 / NONZERO

ONE_SHOT_RUN_ID =
...

ONE_SHOT_PACKET_ID =
...

LIVE_KR_MARKET_MESSAGE =
PASS / FAIL

LIVE_KR_STOCK_MESSAGES =
PASS / FAIL

LIVE_KR_STOCK_MESSAGE_COUNT =
...

LIVE_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED =
0 / NONZERO

LIVE_AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL =
0 / NONZERO

LIVE_BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

LIVE_MAJOR_SR_WITHOUT_PRICE_ANCHOR =
0 / NONZERO

LIVE_PROVISIONAL_BOLLINGER_AS_NEAR_SR =
0 / NONZERO

LIVE_PROVISIONAL_BOLLINGER_AS_MAJOR_SR =
0 / NONZERO

LIVE_PROVISIONAL_BOLLINGER_AS_STORED_RULE =
0 / NONZERO

NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED =
0 / NONZERO

LIVE_DUPLICATE =
0 / NONZERO

LIVE_ORPHAN =
0 / NONZERO

LIVE_UNOWNED_RETRY =
0 / NONZERO

AUTOMATIC_SECOND_ONE_SHOT_CREATED =
0 / NONZERO

RESIDUAL_ONE_SHOT_SCHEDULE_COUNT =
0 / NONZERO

KR_LIVE_PROOF_SOURCE =
OPERATOR_AUTHORIZED_ONE_SHOT_REGULAR_JOB

ONE_SHOT_KR_CLOSE_LIVE_PROOF =
PASS / FAIL / BLOCKED

FINAL_V3_VALIDATOR_CONVERGENCE =
LIVE_PASS /
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...
```

---

# 23. PASS rule

The one-shot is PASS only if:

```text
preconditions pass
exactly one one-shot scheduled
regular job definition reused
fresh data collected
KR market message delivered
all intended KR stock messages delivered
run-44 validator regression does not recur
Price Structure semantics remain correct
no duplicate/orphan/unowned retry
no automatic second run
temporary schedule fully cleaned
normal recurring schedule unchanged
P0 = 0
material P1 = 0
```

Then:

```text
ONE_SHOT_KR_CLOSE_LIVE_PROOF = PASS
FINAL_V3_VALIDATOR_CONVERGENCE = LIVE_PASS
```

---

# 24. Failure rule

If the one-shot fails:

```text
ONE_SHOT_KR_CLOSE_LIVE_PROOF = FAIL
```

Collect:

```text
run id
packet id
failure location
exact exception
messages already delivered
undelivered messages
scheduler cleanup state
```

Do not automatically rerun.

---

# 25. Completion response

Return:

```text
OPERATING_BEFORE = ...
LATEST_MAIN_BEFORE = ...
OPERATING_LINEAGE_SAFE = ...

PRECONDITION_ALL_GATES_PASS = ...

PASS_TIME_KST = ...
SCHEDULED_TIME_KST = ...

ONE_SHOT_KR_CLOSE_SCHEDULE_COUNT = 1
REGULAR_JOB_DEFINITION_REUSED = ...
NORMAL_RECURRING_SCHEDULE_CHANGED = 0

ONE_SHOT_RUN_ID = ...
ONE_SHOT_PACKET_ID = ...

LIVE_KR_MARKET_MESSAGE = ...
LIVE_KR_STOCK_MESSAGES = ...
LIVE_KR_STOCK_MESSAGE_COUNT = ...

LIVE_FALLBACK_DYNAMIC_RESISTANCE_NOT_RENDERED = 0

LIVE_AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL = 0
LIVE_BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
LIVE_MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0

LIVE_PROVISIONAL_BOLLINGER_AS_NEAR_SR = 0
LIVE_PROVISIONAL_BOLLINGER_AS_MAJOR_SR = 0
LIVE_PROVISIONAL_BOLLINGER_AS_STORED_RULE = 0

NOTIFICATION_VALIDATION_FAILURE_SUPPRESSED = 0

LIVE_DUPLICATE = 0
LIVE_ORPHAN = 0
LIVE_UNOWNED_RETRY = 0

AUTOMATIC_SECOND_ONE_SHOT_CREATED = 0
RESIDUAL_ONE_SHOT_SCHEDULE_COUNT = 0

KR_LIVE_PROOF_SOURCE =
OPERATOR_AUTHORIZED_ONE_SHOT_REGULAR_JOB

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

ONE_SHOT_KR_CLOSE_LIVE_PROOF =
PASS /
FAIL /
BLOCKED

FINAL_V3_VALIDATOR_CONVERGENCE =
LIVE_PASS /
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL

NEXT_ACTION =
NO_ACTION /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 26. Mandatory completion ZIP

Create:

`20260828-run-now-one-shot-kr-close-live-proof-bundle.zip`

Include:

```text
exact instruction
preflight
schedule evidence
live run evidence
exact KR market message
exact KR stock messages
V3 validator proof
delivery proof
scheduler cleanup
final status
machine-readable JSON
artifact index
```

Exclude:

```text
secrets
raw Telegram chat IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 27. Final principle

Run the real regular KR close production path once, using fresh data, exactly five minutes after the validated preflight.

This is a live proof of the converged system.

Do not create a second run automatically, and leave no temporary scheduler residue afterward.
