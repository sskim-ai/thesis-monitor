# thesis-monitor — KR Non-Trading-Day Producer Guard & Orphan Delivery Reconciliation Repair

## Metadata

- Workstream: `Bounded P1 production-integrity repair`
- Instruction version: `1.0`
- Date: `2026-08-22 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended current main/operating from Stage A evidence:
  `2244b8f6083356527b576343d86a2a1ab60415ec`
- Earlier intended runtime SHA:
  `673677469bbc95be2347bdd46708c6051960e173`
- Difference observed in Stage A:
  docs-only work-instruction descendant; no runtime-file delta
- Triggering natural evidence:
  `2026-08-22 Saturday Stage A`
- Triggering natural monitor run:
  `daily_kr run 33`
- Expected packet:
  `2026-08-22-kr-run-33-c2491c2e78ad`
- Observed Saturday producer attempts:
  `16:05 / 16:20 / 16:50 KST`
- Observed retry checks:
  `16:22 / 16:25 / 16:30 KST`
- Fallback:
  `17:10 KST`
- Observed orphan Telegram delivery rows:
  `7`
- Actual Telegram sends:
  `0`
- Open P0:
  `0`
- Open material P1:
  `1`
- Working-capital user-visible mode:
  `SELECTIVE_INVENTORY`
- Inventory:
  `ENABLED_PENDING_NATURAL`
- Exact Trade AR:
  `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist:
  `OFF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`

This repair must close the Saturday upstream KR producer defect without changing normal trading-day analysis behavior.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260822-kr-non-trading-day-producer-guard-and-orphan-delivery-reconciliation.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe `origin/main` and operating SHA
2. verify the Stage A report evidence is present or otherwise available
3. commit/push this instruction as a **docs-only instruction commit**
4. record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
5. create the implementation branch from the latest safe main descendant containing the instruction commit
6. do not silently edit this instruction after implementation begins
7. no force push / history rewrite

Recommended branch:

`codex/kr-non-trading-day-producer-guard-orphan-reconciliation`

If main has moved after the Stage A review:
use the latest safe main and report the ancestry explicitly.
Do not force the stale SHA above.

---

# 1. Evidence basis

The 2026-08-22 natural Saturday review established:

## Safe downstream behavior

- KRX 16:05 role-target:
  `PASS`
- KR Codex primary 16:15:
  `SAFE_TERMINAL_NO_PACKET`
- KR Codex backup 16:55:
  `SAFE_TERMINAL_NO_PACKET`
- unexpected Telegram:
  `0`
- duplicates:
  `0`

## Unsafe upstream behavior

The independent KR producer:

- started `daily_kr` run 33 at approximately 16:05:29 KST
- analyzed 7 tickers successfully
- made natural provider calls
- created 7 Telegram `notificationdelivery` rows
- left all 7 unsent with `sent_at = null`
- did not write the expected immutable packet
- then failed with the same missing-packet traceback across 3 producer attempts
- launch agent ended with exit code 1

The review also observed:

```text
DB notificationdelivery rows:
status = pending
count = 7

17:10 fallback:
pending_count = 0
status = no_held_session
sent_count = 0
```

This apparent difference in "pending" semantics must be traced and closed.

---

# 2. Repair goals

Close four related integrity gaps:

1. **Non-trading-day producer entry guard**
   - no KR company analysis when there is no valid KR production target

2. **Retry-path guard reuse**
   - 16:05 / 16:20 / 16:50 producer entries use the same target decision
   - no repeated bad attempt on weekend/holiday

3. **Packet / delivery-intent integrity**
   - delivery queue state must not become orphaned when no immutable packet exists

4. **Existing orphan-row reconciliation**
   - the 7 confirmed unsent Saturday rows must be safely terminalized or otherwise reconciled through an auditable supported path
   - never mark them sent
   - never delete history silently

---

# 3. Hard non-goals

Do NOT:

- change Inventory user-visible selection
- change Trade AR state
- change Phase 9.0E cash flow
- change investor-flow attribution repair
- change night-futures logic
- change KRX role-target behavior
- change Public Action/schema
- change KR 16:15/16:55 Codex reviewer schedules
- change the 16:05/16:20/16:50 producer schedule unless a scheduling defect is independently proven
- change 17:10 fallback semantics except where required to prevent orphan pickup
- manually send Telegram
- mark the 7 rows `sent`
- set `sent_at`
- delete the 7 rows
- use broad ad hoc SQL updates
- fabricate packet artifacts for 2026-08-22
- rerun Saturday production manually
- query providers to recreate the natural Saturday evidence

---

# 4. Root-cause trace before code changes

Trace the exact upstream path:

```text
launchd / producer entry
→ production-session/calendar decision
→ daily_kr monitor run
→ company analysis/provider calls
→ assessment/persistence
→ notificationdelivery creation
→ immutable packet construction/write
→ hold/claim/outbox path
→ missing-packet exception
→ retry path
→ fallback query
```

For every step report:

- function/module
- state created
- database/file mutation
- target/session assumptions
- failure behavior
- retry behavior

Do not code the guard until the earliest correct guard insertion point is identified.

---

# 5. Producer role-target contract

Reuse the repaired role-first XKRX/session-resolution architecture.

Do not create a third independent weekend calendar implementation.

Implement/reuse a production role, suggested:

`kr_daily_production`

or repository-equivalent.

Conceptual input:

```text
observed_at_kst
role = kr_daily_production
xkrx_calendar
```

Conceptual output:

```text
target_xkrx_business_date
target_session
target_completed
production_eligible
skip_reason
calendar_evidence
```

The producer must resolve this **before**:

- provider calls
- monitor-run analysis
- notification creation
- packet construction

---

# 6. Producer eligibility

A KR daily production attempt may proceed only when there is a valid production target.

On a normal valid trading day:
preserve current behavior.

On:

- Saturday
- Sunday
- XKRX holiday
- consecutive holiday
- special closure

with no valid daily production target:

```text
analysis = 0
provider calls = 0
new monitor run = 0 if architecture allows
notification rows = 0
packet = 0
Telegram = 0
exit = normal safe no-op
```

If an audit/no-op run record is required by current architecture:
it may record only the skip state and must not perform company analysis.

---

# 7. Guard insertion point

The non-trading-day guard must be **earlier** than the observed Saturday activity.

Acceptance requires proof that the guard runs before:

- news calls
- OpenDART calls
- OHLCV calls
- 7-ticker analysis
- delivery-intent creation

A guard placed only before packet hold is insufficient.

---

# 8. Shared guard across producer attempts

The scheduled producer entries:

- 16:05
- 16:20
- 16:50

must use the same eligibility contract.

Do not allow:

```text
16:05 safe skip
but
16:20/16:50 retry enters analysis
```

Each entry must independently resolve the same target safely and idempotently.

---

# 9. Retry checks

Review:

- 16:22
- 16:25
- 16:30

retry/check paths.

On a non-trading-day no-target state:

Expected:
- no packet claim
- no AI delivery
- no Telegram
- no provider call
- normal terminal/no-op

Do not let retry checks create a packet or delivery row.

---

# 10. Fallback 17:10

On a non-trading-day no-target state:

Expected:
- no held session
- delivery count 0
- sent count 0
- no orphan queue pickup

Preserve existing safe behavior.

If fallback's `pending_count` intentionally means "eligible pending packet delivery" rather than raw DB `status=pending`, document that precisely.

---

# 11. Pending semantics audit

Mandatory.

Explain why:

```text
notificationdelivery status=pending = 7
```

coexisted with:

```text
fallback pending_count = 0
```

Trace:

- table/model
- query filters
- packet/session joins
- eligibility states
- channel filters
- terminality rules

Define separate terms if necessary, e.g.:

```text
raw_pending_rows
deliverable_pending
held_session_pending
```

Do not use the same word `pending` for materially different states without documentation.

---

# 12. Delivery-intent integrity contract

Introduce/reuse a contract, suggested:

`packet-bound-delivery-intent-v1`

A Telegram delivery intent must be safely associated with an immutable packet/session before it can remain deliverable.

Required invariant:

```text
deliverable Telegram intent
→ valid immutable packet/session reference exists
```

No orphan deliverable state.

---

# 13. Packet / notification ordering

Inspect the actual persistence architecture.

Choose the smallest safe implementation among:

### Preferred A — packet-first
```text
analysis complete
→ immutable packet successfully persisted
→ delivery intents created
```

### Preferred B — transactional state
If packet and delivery intent live in the same transaction-capable store:
commit both atomically.

### Allowed C — compensating terminalization
If file-based packet + DB delivery intent cannot be atomic:
- create intent only in a non-deliverable provisional state
- packet write succeeds
- promote intent to deliverable state
- packet write fails
- terminalize provisional intent with explicit failure reason

Do not force a transaction model that the current storage architecture cannot support safely.

---

# 14. No false success

A monitor run completing 7/7 ticker analysis does not mean a production packet exists.

The producer must distinguish:

- analysis success
- packet persistence success
- delivery-intent readiness

Do not collapse these into one `success` state.

---

# 15. Expected packet failure

If packet persistence fails on a valid trading day:

- no orphan deliverable rows
- no Telegram
- producer returns a structured failure
- retry remains idempotent
- original analysis evidence preserved
- next attempt does not duplicate notifications

This is a required test even though the Saturday trigger was a no-target case.

---

# 16. Existing seven orphan rows — evidence lock

Before any reconciliation:

Create a read-only evidence snapshot containing exact:

- row IDs
- ticker
- channel
- status
- created_at
- sent_at
- packet/session/run references
- attempt references if present
- error/reason metadata
- any payload/hash linkage

Confirm all target rows:

- belong to the 2026-08-22 Saturday incident
- are unsent
- have no valid immutable packet
- were never delivered
- are not legitimately reusable

Do not identify them by timestamp alone if stronger references exist.

---

# 17. Orphan reconciliation policy

The 7 rows must not remain ambiguously `pending` if they can ever be picked up later.

Use an **existing supported non-deliverable terminal state** if one exists, such as repository-equivalent:

- cancelled
- aborted
- failed
- superseded
- non_deliverable

Do not invent a status string without checking the schema.

Add an auditable reason equivalent to:

`non_trading_day_orphan_no_packet`

if supported.

Never:

- mark sent
- set sent_at
- delete rows

---

# 18. If schema lacks a safe terminal state

Do not perform an ad hoc status mutation.

Instead:

1. complete the producer guard
2. make all existing orphan rows provably non-deliverable through a safe query-state guard if possible
3. report:
   `ORPHAN_RECONCILIATION = BLOCKED_BY_SCHEMA`
4. create a bounded schema-follow-up recommendation

However, this phase should not claim full P1 closure if the 7 rows remain materially ambiguous/deliverable.

---

# 19. Controlled reconciliation command

No ad hoc production SQL.

If the rows can be safely reconciled:

create/reuse a deterministic maintenance command with:

- dry-run default
- exact row IDs or exact incident selector
- precondition checks
- expected count = 7
- abort if count differs
- old/new state printout
- reason
- operator confirmation or explicit `--apply`
- transaction/rollback where supported
- post-apply verification

Execute it at most once after validation.

Report this as a controlled maintenance reconciliation.

---

# 20. Reconciliation postconditions

After apply:

```text
target rows = 7
sent rows among them = 0
sent_at set among them = 0
deliverable pending among them = 0
ambiguous raw pending among them = 0
```

Historical audit trail remains intact.

No unrelated rows change.

---

# 21. Delivery query hardening

Regardless of row reconciliation, delivery/claim/fallback queries must require a valid packet/session binding before treating a row as deliverable.

A raw `status=pending` row with missing packet must fail closed.

This prevents a future cleanup/retry path from sending historical orphan rows.

---

# 22. Idempotency

Required invariants:

### Non-trading day
Repeated producer invocation:
- no analysis
- no packet
- no notification rows
- same safe skip classification

### Trading day packet failure
Repeated retry:
- no duplicate delivery intent
- no duplicate packet
- no duplicate Telegram

### Reconciliation command
Second `--apply`:
- no-op / safely reports already reconciled

---

# 23. Normal trading-day regression

This repair must not suppress legitimate KR production.

Test a normal eligible trading day:

```text
valid XKRX target
→ normal analysis
→ canonical packet
→ delivery intent
→ Codex primary/backup flow
```

Expected user-visible behavior unchanged.

Do not change message content merely because the producer guard was added.

---

# 24. Weekend / holiday matrix

Required deterministic matrix:

- Saturday
- Sunday
- XKRX holiday
- consecutive holiday
- normal Monday
- day after holiday
- special closure if calendar fixture supports it

For each:

```text
production target
eligible
analysis count
provider-call count
packet count
notification count
exit/skip state
```

No calendar-day arithmetic.

---

# 25. Time-slot matrix

Test each producer entry:

- 16:05
- 16:20
- 16:50

and checks/fallback:

- 16:22
- 16:25
- 16:30
- 17:10

On no-target date:
all must remain non-producing and safe.

---

# 26. Natural run-33 replay

Use immutable evidence from:

`2026-08-22-kr-run-33-c2491c2e78ad`

Do not rewrite originals.

Create a repaired counterfactual replay showing:

```text
same Saturday timestamp
→ role-target no valid production target
→ producer stops before analysis
→ provider calls 0
→ notifications 0
→ packet 0
→ exit 0 safe no-op
```

This is retrospective validation, not a new natural run.

---

# 27. Inventory / Trade AR isolation

Preserve:

```text
WORKING_CAPITAL_USER_VISIBLE_MODE = SELECTIVE_INVENTORY
INVENTORY_USER_VISIBLE = ENABLED_PENDING_NATURAL
TRADE_AR_USER_VISIBLE = OFF_PENDING_NATURAL_PROOF
```

No Inventory proof is created by this repair.

Do not change Stage B review state.

---

# 28. Investor-flow repair isolation

Do not modify investor-flow wording/logic.

The next genuine KR natural packet will independently prove it.

---

# 29. XKRX role-target regression

The repaired KRX 16:05 same-day role already passed Saturday no-target behavior.

This producer repair must not change that code path unless it is extracting a shared safe target resolver.

If shared code is touched:
re-run:
- KRX same-day
- KRX next-morning
- night observer
- night production
role-target tests.

---

# 30. Production safety

Preserve:

- exactly-once
- receipt integrity
- message count
- AI/fallback
- Phase 9.0E
- Inventory user-visible feature state
- price/RR
- valuation
- investor flow
- KRX telemetry
- night futures

No new user-visible wording is required.

---

# 31. Tests — producer guard

Required:

- Saturday no target → no analysis/provider calls/notifications/packet
- Sunday no target
- holiday no target
- normal trading day proceeds
- consecutive holidays
- target resolver unavailable → fail closed before analysis

---

# 32. Tests — packet failure

Required:

- valid trading day analysis succeeds
- packet write fails
- no deliverable notification remains
- retry idempotent
- fallback sends 0 from orphan state
- existing analysis evidence preserved

---

# 33. Tests — pending semantics

Required:

- raw pending row + valid packet → deliverable according to normal contract
- raw pending row + no packet → non-deliverable
- held session semantics
- fallback count semantics
- old Saturday orphan row cannot be selected

---

# 34. Tests — reconciliation

Required:

- dry-run finds exact 7
- count mismatch aborts
- already sent row aborts
- valid packet reference aborts
- apply changes only exact 7
- second apply idempotent
- sent_at remains null
- no unrelated row changes

Use test DB/fixture before any controlled production reconciliation.

---

# 35. Tests — retry paths

Required:

- 16:05 no-op
- 16:20 no-op
- 16:50 no-op
- retry checks no-op
- fallback no-op
- exit codes normal
- no repeated tracebacks

---

# 36. Full validation

Required:

- focused producer-guard tests PASS
- packet/delivery-intent tests PASS
- pending-semantics tests PASS
- orphan-reconciliation tests PASS
- run-33 immutable replay PASS
- weekend/holiday matrix PASS
- normal-trading-day regression PASS
- exactly-once regression PASS
- Inventory/9.0E regression PASS
- XKRX/night regression if shared resolver touched
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions PASS
- exact final/main SHA Actions PASS after promotion

---

# 37. Promotion gate

Set:

`KR_PRODUCER_REPAIR_READY = YES/NO`

YES requires:

- open P0 = 0
- implementation material P1 = 0
- no-target guard before analysis
- all producer attempts share guard
- packet/delivery invariant PASS
- raw pending without packet is non-deliverable
- orphan reconciliation PASS
- normal trading-day regression PASS
- CI PASS
- main ancestry clean

If orphan rows cannot be safely reconciled:
do not claim full repair PASS.

---

# 38. Promotion

After readiness YES:

- promote cleanly to main
- sync operating
- restart only if imported runtime requires it
- health PASS
- schedules unchanged
- Inventory mode unchanged
- Trade AR state unchanged
- Production Assist OFF

Do not manually run KR production after promotion.

The next natural non-trading-day opportunity is the live proof.

---

# 39. Natural proof state

After deterministic repair/promotion:

```text
KR_NON_TRADING_DAY_PRODUCER_REPAIR =
DEPLOYED_PENDING_NATURAL

KR_NON_TRADING_DAY_NATURAL_PROOF =
PENDING
```

Do not wait for another weekend to finish implementation.

A later natural weekend/holiday can mark LIVE PASS if:

- producer analysis = 0
- provider calls = 0
- notification rows = 0
- packet = 0
- exit = safe
- downstream reviewers safe
- Telegram = 0

---

# 40. Required architecture doc

Create:

`docs/architecture/KR_PRODUCER_SESSION_AND_DELIVERY_INTEGRITY.md`

Document:

- producer role-target guard
- entry ordering
- packet/delivery-intent invariant
- pending semantics
- retries/fallback
- orphan reconciliation policy
- natural proof lifecycle

---

# 41. Required reports

Create:

1. `docs/reports/20260822-kr-producer-root-cause.md`
2. `docs/reports/20260822-kr-producer-role-target-guard.md`
3. `docs/reports/20260822-kr-packet-delivery-integrity.md`
4. `docs/reports/20260822-kr-pending-semantics-audit.md`
5. `docs/reports/20260822-kr-orphan-delivery-evidence.md`
6. `docs/reports/20260822-kr-orphan-reconciliation-dry-run.md`
7. `docs/reports/20260822-kr-orphan-reconciliation-result.md`
8. `docs/reports/20260822-kr-weekend-holiday-matrix.md`
9. `docs/reports/20260822-kr-run33-repaired-replay.md`
10. `docs/reports/20260822-kr-producer-validation.md`
11. `docs/reports/20260822-kr-producer-readiness.md`

Recommended JSON:

`docs/reports/20260822-kr-producer-repair-readiness.json`

---

# 42. Complete report bundle

Create:

`20260822-kr-non-trading-day-producer-repair-bundle.zip`

Include sanitized:

- root cause
- guard
- pending semantics
- packet/delivery integrity
- orphan evidence
- dry run
- reconciliation result
- weekend matrix
- run-33 replay
- validation
- readiness JSON

Report ZIP SHA-256.

Do not include secret-bearing DB dumps.

---

# 43. Completion report — repository

Report:

- instruction path
- instruction commit
- branch
- implementation SHA
- final SHA
- previous main
- final main
- operating
- promotion method
- API restart
- worktrees
- deviations

---

# 44. Completion report — root cause

Report:

- earliest missing guard point
- exact producer entry function
- exact notification creation point
- exact packet persistence point
- exact missing-packet failure point
- retry behavior
- why Codex primary/backup remained safe
- why KRX 16:05 remained safe

---

# 45. Completion report — pending semantics

Report exact definitions for:

```text
raw_pending_rows
deliverable_pending
held_session_pending
```

or actual repository terms.

Explain the Saturday:

```text
7 raw pending rows
vs
fallback pending_count = 0
```

without ambiguity.

---

# 46. Completion report — orphan rows

Report:

- evidence row count
- exact row identifiers in sanitized form
- sent count
- packet linkage
- chosen terminal state
- reason
- dry-run result
- apply result
- unrelated rows changed
- second-run idempotency

Never expose private Telegram destination identifiers.

---

# 47. Completion report — production behavior

Report matrix:

```text
Saturday
Sunday
Holiday
Normal trading day
```

For each:

- target
- analysis
- provider calls
- packet
- notifications
- Telegram
- exit

---

# 48. Completion report — safety

Report:

- manual Telegram = 0
- manual production task = 0
- provider recreation = 0
- ad hoc SQL = 0
- controlled reconciliation command = YES/NO
- controlled reconciled rows = exact count
- Pilot mutation = 0
- Inventory mode changed = NO
- Trade AR changed = NO
- Production Assist = OFF

---

# 49. Final status

Successful completion should report:

```text
KR_NON_TRADING_DAY_PRODUCER_GUARD = PASS
KR_PACKET_DELIVERY_INTEGRITY = PASS
KR_PENDING_SEMANTICS_AUDIT = PASS
KR_ORPHAN_DELIVERY_RECONCILIATION = PASS

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

KR_NON_TRADING_DAY_PRODUCER_REPAIR =
DEPLOYED_PENDING_NATURAL

KR_NON_TRADING_DAY_NATURAL_PROOF =
PENDING

INVENTORY_USER_VISIBLE =
ENABLED_PENDING_NATURAL

TRADE_AR_USER_VISIBLE =
OFF_PENDING_NATURAL_PROOF

NEXT_ACTION =
WAIT_FOR_FIRST_ELIGIBLE_INVENTORY_PACKET
```

If any material invariant remains unresolved:
set the relevant item FAIL and identify one bounded blocker.

---

# 50. Final philosophy

The downstream reviewers behaved correctly.

The upstream producer did not.

The correct fix is not another downstream check.

The producer must know, before doing expensive or stateful work:

```text
Is there a valid KR production target for this role and time?
```

If the answer is no:

```text
analysis = 0
provider calls = 0
packet = 0
delivery intent = 0
Telegram = 0
exit = safe no-op
```

And on a valid trading day:

```text
analysis
→ immutable packet
→ packet-bound delivery intent
→ review/delivery
```

A delivery row must never be left ambiguously pending without a packet that can actually be delivered.

The seven Saturday rows are part of the repair, not disposable noise.

Preserve them as audit history, reconcile them safely, and make sure the same state cannot be created again.
