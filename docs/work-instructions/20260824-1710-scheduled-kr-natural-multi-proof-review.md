# thesis-monitor — 2026-08-24 17:10 KST Scheduled KR Natural Multi-Proof Review

## Metadata
- Task type: `ONE_SHOT_SCHEDULED_READ_ONLY_NATURAL_REVIEW`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Scheduled execution: `2026-08-24 17:10 KST`
- Time zone: `Asia/Seoul`
- Repository: `sskim-ai/thesis-monitor`
- Intended current main/operating: `a2d217f5b041a0409ed165b8bd66b98f36c5ed05`
- Resolve actual latest safe main/operating at registration and execution; do not force the SHA above if main legitimately advanced.
- Working-capital user-visible mode: `SELECTIVE_INVENTORY`
- Inventory: `ENABLED_PENDING_NATURAL`
- Exact Trade AR user-visible: `OFF_PENDING_NATURAL_PROOF`
- Phase 9.1D runtime canary: deployed
- KR investor-flow reconciliation repair: deployed
- KR producer repair: `DEPLOYED_PENDING_NATURAL`
- Macro temporal repair: `DEPLOYED_PENDING_NATURAL`
- XKRX role-target repair: deployed
- Phase 9.0E cash-flow mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`

This review must not modify production.

---

## 0. Repository protocol

Store at:

`docs/work-instructions/20260824-1710-scheduled-kr-natural-multi-proof-review.md`

Before scheduling:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:
1. verify actual current safe main/operating
2. commit/push this instruction as a docs-only commit
3. record instruction path / commit SHA / version
4. create/use review branch `codex/20260824-1710-kr-natural-multi-proof-review`
5. do not merge review-only reports into runtime main automatically
6. no force push / history rewrite

---

## 1. REQUIRED — create one-shot Codex Scheduled Task

Create a one-shot Codex Scheduled Task using the existing supported scheduling mechanism.

Recommended task name:
`20260824-1710-kr-natural-multi-proof-review`

Execution:
- once at `2026-08-24 17:10 KST`
- timezone `Asia/Seoul`
- repo root as working directory
- instruction source: this committed file
- read-only review only
- mandatory result ZIP

If only recurring scheduling exists:
- use the smallest schedule that triggers at 17:10
- make task idempotent
- pause/disable/remove it after first terminal execution
- record cleanup state

Do not leave a recurring review task active.

---

## 2. Scheduled-task execution contract

The scheduled task must:

> At 17:10 KST, open this committed work instruction and review only naturally generated 2026-08-24 KR artifacts. Do not manually run KR/US/KRX/night-futures tasks, do not query providers to recreate evidence, do not send Telegram, do not change feature modes/configs, and do not mutate DB/Pilot/archives. Produce all required sanitized reports, push them to the review branch, create the required ZIP, compute SHA-256, and return the gate summary. Missing evidence must remain `NOT_OBSERVED`/UNKNOWN.

---

## 3. Scheduler registration evidence

Create:

`docs/reports/20260824-1710-kr-review-scheduled-task-registration.md`

Record:
- task name / ID
- created_at
- scheduled_for
- timezone
- one-shot/recurring
- enabled state
- repository
- instruction commit SHA

Verify 17:10 is KST, not UTC.

---

## 4. Hard prohibitions

Do NOT:
- manually run KR producer/primary/backup
- manually run KRX telemetry
- manually run US tasks/night observers
- manually send Telegram
- manually query providers
- change Inventory mode
- enable Trade AR
- change 9.0E
- change macro temporal config
- change KRX/night schedules or deadline
- mutate DB/Pilot
- rewrite archives/receipts
- deploy repairs

---

## 5. 17:10 terminal-state rule

Relevant slots:
- KRX 16:05
- KR primary 16:15
- KR backup 16:55
- current producer/retry schedule

If production/delivery is terminal at 17:10:
proceed.

If still nonterminal:
- read-only recheck for up to 15 minutes
- no manual trigger
- if still nonterminal by 17:25, create the result bundle with:
  `REVIEW_STATE = DEFERRED_NONTERMINAL`

A ZIP is mandatory even when deferred.

---

# Track A — operating state

## 6. Verify
- main / origin/main / operating SHA parity
- API health
- clean worktrees
- Production Assist
- Inventory mode/state
- Trade AR state
- Phase 9.0E mode
- Phase 9.1D state
- macro temporal repair state
- producer repair state
- investor-flow repair state
- KR/US/KRX/night schedules

Expected relevant state:

```text
WORKING_CAPITAL_USER_VISIBLE_MODE = SELECTIVE_INVENTORY
INVENTORY_USER_VISIBLE = ENABLED_PENDING_NATURAL or legitimate later state
TRADE_AR_USER_VISIBLE = OFF_PENDING_NATURAL_PROOF
Production Assist = OFF
```

---

# Track B — canonical KR production

## 7. Identify exact natural packet

Record:
- packet ID
- producer run ID
- assessment date
- packet creation
- AI completion
- validation completion
- primary/backup terminal times
- Telegram send time
- delivery mode
- expected/sent/pending/failed/duplicate
- receipt
- exactly-once

## 8. Required artifacts

Locate/reference:
1. producer result
2. immutable packet
3. AI candidate
4. numeric validation
5. semantic validation
6. runtime quality
7. final-language result
8. fallback if used
9. delivery result
10. receipt
11. exactly-once evidence
12. exact sent market digest
13. all 7 stock messages in sent order
14. Phase 9.1D canary receipt

---

# Track C — KR producer normal-trading-day natural proof

## 9. Verify the repaired normal-day path

Expected:

```text
valid KR target
→ analysis proceeds
→ immutable packet exists
→ packet-bound delivery intent
→ valid hold/delivery state
→ no orphan rows
→ primary/backup use the correct packet
```

Audit:
- role-target result
- analysis count
- provider-call behavior
- packet write
- delivery-intent order/binding
- raw pending vs deliverable pending vs held-session pending
- new orphan count
- exit/retry behavior

Set:

`KR_PRODUCER_TRADING_DAY_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

Also verify:

```text
new orphan rows = 0
deliverable row without packet = 0
```

The separate non-trading-day LIVE proof remains pending until a future weekend/holiday.

---

# Track D — actual KR market digest

## 10. Include exact sent digest

Audit:
- current environment
- important changes
- current market situation
- investment meaning
- market assumptions
- data cautions
- temporal honesty of US/global observations
- presence/absence of domestic data

Do not fail the digest merely for being US/global-heavy; localization is a separate roadmap item.

---

# Track E — Macro Temporal Repair natural proof

## 11. Audit every macro metric actually used

For each:

```text
metric
observation/as-of date
temporal role
current/prior/reference/stale
eligible for important_changes
eligible for today_signal
actual wording
```

Hard checks:
- prior US session not described as a new current US cash-session move
- lagging VIX/WTI/rates/dollar not reused as false current changes
- genuinely new observations may remain current
- regime/state can persist independently from new daily signal
- no `오늘/간밤/현재 급등` wording without temporal eligibility

Set:

`MACRO_TEMPORAL_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

Also report:

`false_current_claims = 0` target.

---

# Track F — KR Market Digest localization observation

## 12. Observation only

Measure:
- domestic/KRX-specific analytical sentences
- global/US analytical sentences
- shared macro/regime sentences

Set:

```text
KR_MARKET_DIGEST_LOCALIZATION_GAP = MATERIAL / MODERATE / LOW
KR_MARKET_DIGEST_LOCALIZATION_ARCHITECTURE_READY = YES / NO
```

Do not implement localization.

---

# Track G — Inventory user-visible natural proof

## 13. For all 7 stocks record

```text
ticker
Inventory canonical eligible
materiality selected
user-visible selected/suppressed
suppression reason
context ID
Fact IDs
relation ID
balance date
comparison basis
AI/fallback path
actual wording if rendered
```

No ticker hard-coding.

## 14. LIVE PASS requirements

Set:

`INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS`

only if at least one actually delivered Inventory enrichment has:
- canonical total Inventory
- correct Fact/relation IDs
- PIT/freshness safe
- correct balance date/comparison
- automatic numeric binding
- semantic validator PASS
- causal guard PASS
- no Inventory Days/CCC
- no unsupported demand/oversupply claim
- AI/fallback context parity
- exactly-once unaffected
- acceptable delivered wording

If none selected:
`NOT_OBSERVED`

If unsafe text delivered:
`FAIL`

## 15. Exact-message audit

For every selected Inventory message include:
- full message
- Inventory sentence
- Fact/relation IDs
- balance date
- numeric value if shown
- industry context
- FCF coexistence
- length impact
- duplication

Classify:
- MATERIAL_IMPROVEMENT
- MINOR_IMPROVEMENT
- NO_MEANINGFUL_CHANGE
- DEGRADED

Set:

`INVENTORY_KILL_SWITCH_REQUIRED = YES / NO`

Do not execute the kill switch.

---

# Track H — Phase 9.1D exact Trade AR natural proof

## 16. Inspect detached canary

For any selected exact Trade AR context verify:
- exact `trade_accounts_receivable`
- no broad AR substitution
- relation vs Revenue
- PIT/freshness
- numeric binding
- semantic/causal guard
- no DSO
- production influence = 0

Set:

`TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED`

Hard user-visible target:

```text
new exact Trade AR enrichment = 0
broad AR enrichment = 0
AP enrichment = 0
```

Set:

```text
TRADE_AR_ENABLEMENT_CANDIDATE =
YES_PENDING_SEPARATE_ENABLEMENT
or
NO_PENDING_NATURAL
or
NO_OTHER_BLOCKER
```

Do not enable it.

---

# Track I — KR investor-flow attribution natural proof

## 17. Review every stock message

Audit:
- 1D / 5D / 20D flow
- foreign / institution / retail
- `주요 3주체` or equivalent label
- omitted participant materiality
- signal basis window
- full-participant reconciliation
- no residual-invented participant
- no unsupported absorber attribution

Hard checks:
- no timeless absorber claim when windows conflict
- no unsupported `기관/개인 흡수`
- period basis explicit where needed

Set:

`KR_INVESTOR_FLOW_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

If SK hynix is present, explicitly verify the prior problematic wording does not recur unqualified.

---

# Track J — KRX 16:05 natural telemetry

## 18. Locate exact observation

Record:
- observation ID
- scheduled/actual time
- role-target result
- target XKRX date
- HTTP statuses
- provider business dates
- row counts
- eligible rows
- publication readiness
- current-snapshot promotability
- raw refs/SHA
- scheduler exit
- duplicates

Set:

`KRX_1605_ROLE_TARGET_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

A correct valid same-day target and correct observation is role-target LIVE PASS even if provider returns zero rows/pending.

Record exact:

`KRX_PUBLICATION_READINESS = <actual enum>`

Do not integrate KRX user-visible.

---

# Track K — KR primary/backup/exactly-once

## 19. Review primary 16:15
- packet availability
- AI invoked
- validation
- fallback used
- delivery count

## 20. Review backup 16:55
- whether needed
- correct no-op after primary terminal, or safe completion if needed

Targets:

```text
sent = expected
duplicate = 0
exactly_once = PASS
receipt_integrity = PASS
```

---

# Track L — KR AI/runtime regression

## 21. Record
- AI candidate generated
- bounded correction if any
- numeric PASS/FAIL
- semantic PASS/FAIL
- final-language PASS/FAIL
- runtime-quality PASS/FAIL
- exact errors
- fallback reason if used

Check recurrence of:
- typed prose skeleton
- depositary false positive
- `chart_risk_reward` leakage
- structured supply duplication
- RR duplication
- valuation ownership errors
- generic numeric summary

Classify each:
- OBSERVED_PASS
- OBSERVED_FAIL
- NOT_OBSERVED

A harmless P2 quality fallback does not automatically invalidate Inventory/investor-flow proof.

---

# Track M — price / valuation / supply safety

## 22. For all stock messages verify
- no fabricated price levels
- RR context valid
- confirmation lifecycle valid
- supply as-of-date correct
- investor-flow repair applied
- valuation fail-closed where required
- current-vs-history ownership valid
- no Inventory-driven automatic valuation mutation

---

# Required reports

## 23. Create

1. `docs/reports/20260824-1710-kr-review-scheduled-task-registration.md`
2. `docs/reports/20260824-kr-natural-sent-message-bundle.md`
3. `docs/reports/20260824-kr-natural-production-review.md`
4. `docs/reports/20260824-inventory-user-visible-natural-proof.md`
5. `docs/reports/20260824-trade-ar-natural-canary-proof.md`
6. `docs/reports/20260824-kr-investor-flow-natural-proof.md`
7. `docs/reports/20260824-kr-digest-macro-temporal-natural-proof.md`
8. `docs/reports/20260824-kr-producer-trading-day-natural-proof.md`
9. `docs/reports/20260824-krx-1605-natural-review.md`
10. `docs/reports/20260824-kr-market-digest-localization-observation.md`
11. `docs/reports/20260824-1710-kr-natural-gates.md`
12. `docs/reports/20260824-1710-kr-natural-artifact-index.md`
13. `docs/reports/20260824-1710-kr-natural-review-summary.json`

The sent-message bundle must contain the exact actual digest + all 7 stock messages in sent order.

---

## 24. Required gate report

`docs/reports/20260824-1710-kr-natural-gates.md`

Must include:

```text
REVIEW_STATE = COMPLETE / DEFERRED_NONTERMINAL

KR_PRODUCTION_NATURAL = LIVE_PASS / FAIL

KR_PRODUCER_TRADING_DAY_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED

INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED
INVENTORY_KILL_SWITCH_REQUIRED = YES / NO

TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED
TRADE_AR_ENABLEMENT_CANDIDATE =
YES_PENDING_SEPARATE_ENABLEMENT / NO_PENDING_NATURAL / NO_OTHER_BLOCKER

KR_INVESTOR_FLOW_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED

MACRO_TEMPORAL_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED

KRX_1605_ROLE_TARGET_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED
KRX_PUBLICATION_READINESS = ...

KR_MARKET_DIGEST_LOCALIZATION_GAP = MATERIAL / MODERATE / LOW
KR_MARKET_DIGEST_LOCALIZATION_ARCHITECTURE_READY = YES / NO

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...
```

Possible `NEXT_ACTION`:
- `KEEP_SELECTIVE_INVENTORY`
- `TRADE_AR_ENABLEMENT_INSTRUCTION`
- `INVENTORY_BOUNDED_REPAIR`
- `KR_PRODUCTION_BOUNDED_REPAIR`
- `MACRO_TEMPORAL_BOUNDED_REPAIR`
- `KR_INVESTOR_FLOW_BOUNDED_REPAIR`
- `KR_MARKET_DIGEST_LOCALIZATION_ARCHITECTURE`
- `WAIT_FOR_MORE_NATURAL_PROOF`

Choose the smallest justified next action.

---

## 25. Artifact index

Create:

`docs/reports/20260824-1710-kr-natural-artifact-index.md`

Reference:
- producer run
- KR packet
- AI candidate
- validators
- fallback
- delivery result
- receipt
- exact sent bundle
- Inventory context
- 9.1D canary
- investor-flow evidence
- macro temporal roles
- KRX 16:05
- current operating state

For each include path/ref, SHA if available, and immutable/original status.

No secrets.

---

## 26. Machine-readable summary

Create:

`docs/reports/20260824-1710-kr-natural-review-summary.json`

Include repository, production, producer integrity, Inventory, Trade AR, investor flow, macro temporal, KRX 16:05, localization observation, severity, and next action.

Unknown values remain null/UNKNOWN.

---

## 27. Mandatory result ZIP

Create:

`20260824-1710-kr-natural-multi-proof-review-bundle.zip`

Include all reports above.

If deferred:
include all available evidence and defer-state files anyway.

Compute/report SHA-256.

---

## 28. Scheduled-task cleanup

After terminal report generation:

- if true one-shot: record terminal state
- if recurring fallback schedule was used: pause/disable/remove it
- verify no next run remains active
- record cleanup timestamp

---

## 29. Git/report delivery

Push sanitized reports to the review branch.

Do not auto-merge review reports into runtime main.

Completion response must provide:
- review branch
- instruction commit SHA
- report commit SHA
- scheduled task name/ID
- cleanup state
- ZIP path
- ZIP SHA-256
- gate summary

---

## 30. Completion response format

Return:

```text
SCHEDULED_REVIEW = PASS / FAIL / DEFERRED_NONTERMINAL

KR_PRODUCTION_NATURAL = ...
KR_PRODUCER_TRADING_DAY_NATURAL = ...

INVENTORY_USER_VISIBLE_NATURAL = ...
INVENTORY_KILL_SWITCH_REQUIRED = ...

TRADE_AR_NATURAL_PROOF = ...
TRADE_AR_ENABLEMENT_CANDIDATE = ...

KR_INVESTOR_FLOW_NATURAL = ...

MACRO_TEMPORAL_NATURAL = ...

KRX_1605_ROLE_TARGET_NATURAL = ...
KRX_PUBLICATION_READINESS = ...

KR_MARKET_DIGEST_LOCALIZATION_GAP = ...
KR_MARKET_DIGEST_LOCALIZATION_ARCHITECTURE_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

NEXT_ACTION = ...

ZIP = ...
ZIP_SHA256 = ...
REPORT_COMMIT = ...
```

---

## 31. Severity

### P0
- wrong delivered Inventory Fact/period
- Trade AR/broad AR/AP user-visible leak
- duplicate Telegram
- exactly-once/receipt failure
- packetless deliverable intent
- fabricated/incorrect market fact
- unsafe false-current macro claim

### P1
- delivered Inventory causal overclaim
- AI/fallback Inventory mismatch
- investor-flow attribution regression
- macro temporal natural failure
- producer packet/delivery-integrity regression
- material message-quality degradation
- abnormal primary/backup lifecycle

### P2
- Inventory not selected naturally
- Trade AR not observed
- domestic digest localization gap
- minor wording
- KRX provider pending despite correct target
- harmless AI quality fallback with safe deterministic delivery

---

## 32. Final principle

This Monday review should answer several natural-proof questions at once:

```text
Did the KR producer behave normally on a real trading day?

Did Inventory actually reach the user safely?

Did exact Trade AR earn canary proof?

Did investor-flow attribution remain correct in real messages?

Did the macro temporal contract prevent old US/reference data from being described as current?

Did KRX 16:05 resolve the right same-day target?

Did delivery remain exactly once?
```

Do not implement the next feature here.

If all safety gates pass, the review may conclude that KR Market Digest localization architecture is ready to begin separately.

Do not confuse:
- `still US-heavy`
with
- `temporally incorrect`

The former is a localization roadmap issue.
The latter is a correctness issue.
