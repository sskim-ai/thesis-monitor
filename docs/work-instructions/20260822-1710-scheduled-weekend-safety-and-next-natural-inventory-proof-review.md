# thesis-monitor — 2026-08-22 17:10 KST Scheduled Weekend Safety Review
## + Next Eligible Natural Inventory Proof Follow-up

### Metadata
- Instruction version: `2.0`
- Date: `2026-08-22 KST`
- Scheduled execution: `2026-08-22 17:10 KST`
- Time zone: `Asia/Seoul`
- Repository: `sskim-ai/thesis-monitor`
- Intended current main/operating: `673677469bbc95be2347bdd46708c6051960e173`
- Working-capital user-visible mode: `SELECTIVE_INVENTORY`
- Inventory user-visible state: `ENABLED_PENDING_NATURAL`
- Exact Trade AR user-visible: `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E cash-flow mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Phase 9.1D runtime canary: deployed
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`

This instruction supersedes the prior unscheduled weekend-review instruction for the 2026-08-22 Stage A review.

The 17:10 scheduled task must:
1. review the completed Saturday afternoon natural/scheduler behavior,
2. produce a result bundle automatically,
3. not run or alter any production task,
4. leave the future Inventory natural-delivery proof as a separate Stage B follow-up.

---

## 0. Repository protocol

Store at:

`docs/work-instructions/20260822-1710-scheduled-weekend-safety-and-next-natural-inventory-proof-review.md`

Before scheduling:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:
1. verify current safe main/operating
2. commit/push this instruction as a docs-only commit
3. record instruction path / commit SHA / version
4. use a review branch for generated reports
5. do not merge review reports into runtime main automatically
6. no force push / history rewrite

Recommended review branch:

`codex/20260822-1710-weekend-safety-review`

If an earlier weekend-review instruction was already committed:
- do not edit it silently
- mark it `SUPERSEDED_BY_V2`
- cite this v2 instruction commit in all output

---

## 1. REQUIRED — create a one-shot Codex Scheduled Task

Before 17:10 KST, create a **one-shot Codex Scheduled Task** using the existing supported Codex scheduling mechanism already used in this environment.

Do not invent a second scheduler framework.

Recommended task name:

`20260822-1710-weekend-safety-review`

Execution:
- run once at `2026-08-22 17:10 KST`
- timezone `Asia/Seoul`
- repository `sskim-ai/thesis-monitor`
- working directory: repository root
- instruction source: this committed work-instruction file
- scope: **Stage A only**
- result bundle: mandatory
- production mutation: prohibited

If one-shot mode exists, use it.

If only recurring scheduling exists:
- configure the smallest safe schedule that triggers at 17:10,
- make execution idempotent,
- after the first successful terminal execution disable/remove the scheduled task,
- record cleanup status in the report.

Do not leave an accidental recurring review task active.

---

## 2. Scheduled-task execution prompt

The scheduled Codex task must effectively execute this instruction:

> At 2026-08-22 17:10 KST, open the committed file `docs/work-instructions/20260822-1710-scheduled-weekend-safety-and-next-natural-inventory-proof-review.md`. Execute Stage A only using naturally generated artifacts already present. Do not manually run KR/US/KRX/night-futures production or observers. Do not query providers to recreate evidence. Produce all required sanitized reports and the required ZIP bundle, compute SHA-256, push the reports to the review branch, and return the report commit, bundle path, SHA-256, and gate summary. If expected natural artifacts are absent, report `NOT_OBSERVED` or a structured missing-evidence reason rather than creating new evidence.

Do not shorten this prompt in a way that drops the safety restrictions.

---

## 3. Scheduler-registration evidence

Immediately after creating the scheduled task, create:

`docs/reports/20260822-1710-scheduled-review-registration.md`

Record:
- scheduled task name
- task ID if available
- created_at
- scheduled_for
- timezone
- one-shot/recurring
- enabled state
- repository
- instruction commit SHA

Do not include secrets.

Verify the scheduled time is **17:10 KST**, not UTC.

---

## 4. Hard prohibitions

The review must not:
- manually run KR primary/backup
- manually run US tasks
- manually run KRX telemetry
- manually run night observers
- send Telegram manually
- change feature modes
- change schedules
- change night-futures deadline
- change observer times
- mutate DB or Pilot
- rewrite production archives/receipts
- enable Trade AR
- deploy a repair

This is read-only.

---

## 5. 17:10 start condition

At 17:10 KST, first inspect whether the Saturday afternoon lifecycle is terminal.

Relevant slots:
- KRX 16:05
- KR primary 16:15
- KR backup 16:55

If all are terminal:
proceed.

If the 16:55 backup or related terminal artifact is still nonterminal:
- do not interfere,
- recheck read-only local terminal status for up to 15 minutes,
- do not trigger anything,
- if still nonterminal by 17:25, produce the result bundle with:
  `REVIEW_STATE = DEFERRED_NONTERMINAL`
  and stop safely.

A result ZIP is required even in this deferred state.

---

## 6. Saturday calendar interpretation

2026-08-22 is Saturday.

A correct result may be:

```text
No valid same-day KR trading packet
→ no Telegram
→ no Inventory user-visible opportunity
→ Inventory remains ENABLED_PENDING_NATURAL
```

This is PASS, not failure.

---

## 7. Stage A — operating-state verification

Read-only verify:
- main SHA
- operating SHA
- API health
- worktree cleanliness
- Production Assist
- working-capital user-visible mode
- Inventory state
- exact Trade AR state
- Phase 9.0E mode
- Phase 9.1D canary state
- US primary/backup schedules
- KR primary/backup schedules
- KRX 08:05/16:05 schedules
- night observers 08:45/09:15

Expected:

```text
WORKING_CAPITAL_USER_VISIBLE_MODE = SELECTIVE_INVENTORY
INVENTORY_USER_VISIBLE = ENABLED_PENDING_NATURAL
TRADE_AR_USER_VISIBLE = OFF_PENDING_NATURAL_PROOF
Production Assist = OFF
```

If operating HEAD differs from intended SHA:
report exact actual SHA and whether it is docs/report-only or runtime-affecting.

---

## 8. Stage A — KRX 16:05 role-target review

Locate the natural 16:05 artifact.

Record:
- scheduled time
- actual start/end
- role
- wall-clock date
- role-target resolver output
- target kind/date/session
- observation eligibility
- skip reason
- provider call count
- HTTP/result if a valid call occurred
- duplicate observation count
- scheduler exit

Expected safe Saturday behavior:

```text
role resolves first
→ no invalid same-day target
→ no unnecessary provider call
→ structured skip/no-op
→ normal exit
```

A generic weekend precheck bypassing role-target resolution is a regression.

---

## 9. Stage A — KR primary 16:15

Locate natural primary artifacts.

Record:
- scheduled/actual times
- role/calendar decision
- packet created YES/NO
- AI invoked YES/NO
- Telegram invoked YES/NO
- receipt created YES/NO
- terminal classification
- skip reason

Expected with no valid XKRX packet:

```text
packet = none
AI = 0
Telegram = 0
safe skip/no-op
```

---

## 10. Stage A — KR backup 16:55

Review similarly.

Expected:
- no fake packet
- no compensating Telegram
- no duplicate
- safe terminal skip/no-op

Document actual repository contract if different.

---

## 11. Stage A — exactly-once/no-delivery safety

Verify:

```text
unexpected Telegram = 0
unexpected stock bundle = 0
duplicate delivery = 0
manual delivery = 0
DB mutation = 0
Pilot mutation = 0
```

Any real Saturday KR stock delivery based on a nonexistent session is P0 unless an explicit non-trading-day digest contract exists.

---

## 12. Stage A — Inventory/Trade AR state

If no eligible packet existed:

```text
INVENTORY_USER_VISIBLE_SATURDAY = NOT_OBSERVED
INVENTORY_USER_VISIBLE = ENABLED_PENDING_NATURAL
TRADE_AR_USER_VISIBLE = OFF_PENDING_NATURAL_PROOF
```

Do not set Inventory FAIL.

---

## 13. Stage A — investor-flow repair status

Because no normal Saturday KR stock packet is expected:

`KR_INVESTOR_FLOW_NATURAL = NOT_OBSERVED_IN_NEW_NATURAL_MESSAGE`

is acceptable.

Verify no rollback/config loss.

Do not manually create a packet.

---

## 14. Scheduled-task cleanup

After Stage A reaches terminal report generation:

If the task was recurring because one-shot was unavailable:
- disable/remove it
- verify no next run remains
- record cleanup time/status

If it was true one-shot:
record terminal/disabled state.

No recurring leftover task.

---

## 15. Mandatory Stage A reports

Create:
1. `docs/reports/20260822-1710-scheduled-review-registration.md`
2. `docs/reports/20260822-saturday-afternoon-safety-review.md`
3. `docs/reports/20260822-saturday-afternoon-safety-review.json`
4. `docs/reports/20260822-1710-scheduled-review-artifact-index.md`
5. `docs/reports/20260822-1710-scheduled-review-summary.md`

---

## 16. Mandatory gate fields

`docs/reports/20260822-saturday-afternoon-safety-review.md`

must include:

```text
REVIEW_STATE = COMPLETE / DEFERRED_NONTERMINAL

OPERATING_HEAD = ...
API_HEALTH = ...

KRX_1605_ROLE_TARGET = PASS / FAIL / NOT_OBSERVED
KR_PRIMARY_WEEKEND_BEHAVIOR = PASS / FAIL
KR_BACKUP_WEEKEND_BEHAVIOR = PASS / FAIL

UNEXPECTED_TELEGRAM = ...
DUPLICATE_DELIVERY = ...

WORKING_CAPITAL_USER_VISIBLE_MODE = ...
INVENTORY_USER_VISIBLE_SATURDAY = NOT_OBSERVED / FAIL
INVENTORY_USER_VISIBLE_STATE = ...
TRADE_AR_USER_VISIBLE_STATE = ...

KR_INVESTOR_FLOW_NATURAL = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_NATURAL_ACTION =
WAIT_FOR_FIRST_ELIGIBLE_INVENTORY_PACKET
or
BOUNDED_REPAIR_REQUIRED
```

---

## 17. Mandatory Stage A ZIP

The scheduled task must always create:

`20260822-1710-weekend-safety-review-bundle.zip`

Include:
- registration report
- Saturday safety review MD
- Saturday safety review JSON
- artifact index
- summary

Compute SHA-256.

Even if `DEFERRED_NONTERMINAL`, create the ZIP.

---

## 18. Git/report delivery

Push sanitized reports to the review branch.

Do not merge the review branch into runtime main automatically.

Completion output must provide:
- review branch
- instruction commit SHA
- report commit SHA
- scheduled task name/ID
- scheduled task terminal/cleanup state
- ZIP path
- ZIP SHA-256
- gate summary

---

## 19. Scheduled-task completion response

Return:

```text
SCHEDULED_REVIEW = PASS / FAIL / DEFERRED_NONTERMINAL

KRX_1605_ROLE_TARGET = ...
KR_PRIMARY_WEEKEND_BEHAVIOR = ...
KR_BACKUP_WEEKEND_BEHAVIOR = ...

UNEXPECTED_TELEGRAM = ...
DUPLICATE_DELIVERY = ...

INVENTORY_USER_VISIBLE_SATURDAY = ...
INVENTORY_USER_VISIBLE_STATE = ...
TRADE_AR_USER_VISIBLE_STATE = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

ZIP = ...
ZIP_SHA256 = ...
REPORT_COMMIT = ...
```

---

# Stage B — future first eligible natural Inventory packet

Do not try to complete Stage B at 17:10 unless a legitimate eligible production packet already exists naturally.

Stage B runs only after the first subsequent eligible natural production packet that can actually select Inventory.

No manual trigger.

## B1. Packet review
Record:
- packet ID
- market
- assessment date
- primary/backup
- AI/fallback
- sent/expected
- duplicates
- exactly-once
- receipt

## B2. Inventory selection
For each stock:
- Inventory canonical eligible
- materiality selected
- user-visible selected/suppressed
- suppression reason
- context ID
- Fact IDs
- relation ID
- balance date
- comparison basis
- delivery path

## B3. LIVE PASS
Set:

`INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS`

only if at least one **actual delivered** Inventory enrichment has:
- canonical total Inventory
- correct Fact/relation IDs
- PIT/freshness safe
- correct balance date/comparison
- automatic numeric binding
- semantic validator PASS
- causal guard PASS
- no Inventory Days/CCC
- no unsupported demand/oversupply conclusion
- AI/fallback context parity
- exactly-once unaffected
- acceptable delivered wording

If none selected:
`NOT_OBSERVED`

If unsafe text delivered:
`FAIL`

## B4. Trade AR negative control
Hard target:
- new Trade AR user-visible enrichment = 0
- broad AR = 0
- AP = 0

If 9.1D Trade AR proof becomes LIVE_PASS:
record proof only.
Do not enable Trade AR here.

## B5. Additional natural repair proof
If packet is KR:
review investor-flow repair.

If packet is US:
review US AI compatibility natural proof.

Set where applicable:

```text
KR_INVESTOR_FLOW_NATURAL = PASS / FAIL / NOT_OBSERVED
US_AI_COMPATIBILITY_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED
TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED
```

## B6. Stage B result bundle
Create separately:

`<date>-inventory-user-visible-natural-review-bundle.zip`

Do not overwrite the 2026-08-22 17:10 Stage A bundle.

---

## 20. Severity

P0:
- invalid Saturday KR production delivery
- wrong Inventory Fact/period
- Trade AR/broad AR/AP leak
- exactly-once/receipt break
- kill switch failure

P1:
- actual Inventory causal overclaim
- AI/fallback Inventory fact mismatch
- material FCF/Inventory contradiction
- investor-flow attribution regression

P2:
- no Inventory opportunity
- minor wording
- small length increase
- Trade AR still pending

---

## 21. Final principle

The 17:10 task must produce a result file automatically without manufacturing market evidence.

A correct Saturday result may simply be:

```text
KRX 16:05 = safe no-target/no-op
KR primary = safe skip
KR backup = safe skip
Telegram = 0
Inventory = still ENABLED_PENDING_NATURAL
Trade AR = still OFF
```

The actual Inventory user-visible proof belongs to the first later eligible natural packet.

Therefore:

```text
17:10 scheduled Codex review
→ Stage A result ZIP

future eligible natural packet
→ Stage B proof later
```

Do not manufacture Stage B evidence just to make the 17:10 bundle look complete.
