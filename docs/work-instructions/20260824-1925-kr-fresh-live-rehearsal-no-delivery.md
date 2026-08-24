# thesis-monitor — 2026-08-24 KR Fresh Live Rehearsal (No Delivery)

## Metadata

- Task type: `MANUAL_LIVE_REHEARSAL_NO_DELIVERY`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Intended start: immediately after instruction commit, approximately `19:25 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended current main/operating:
  `96825de767f8ff25b59ab4451df305df5dd873cc`
- IMPORTANT:
  before execution, resolve and use the actual latest safe `origin/main`; do not force the SHA above if main legitimately advanced.
- Triggering prior natural failure:
  `2026-08-24 KR normal-day run with analysis 7/7 but packet persistence blocked by shadow_cohort_activation_gate_failed`
- Repaired state:
  `KR_SHADOW_GATE_PACKET_REPAIR = DEPLOYED_PENDING_NATURAL`
- Working-capital user-visible mode:
  `SELECTIVE_INVENTORY`
- Inventory user-visible:
  `ENABLED_PENDING_NATURAL`
- Exact Trade AR:
  `OFF_PENDING_NATURAL_PROOF`
- Phase 9.0E:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Macro temporal repair:
  `DEPLOYED_PENDING_NATURAL`
- KR investor-flow repair:
  deployed
- KR producer repair:
  deployed
- Production Assist:
  `OFF`
- Public Action:
  `0.4.5`
- Output schema:
  `4`

This task intentionally performs a **fresh-data, current-cutoff, non-delivery rehearsal**.

It is allowed to make the same read-only provider calls that a normal KR production cycle would make now.

It must **not** send Telegram, mutate production delivery state, mutate assessments, overwrite the failed natural run, or claim natural proof.

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260824-1925-kr-fresh-live-rehearsal-no-delivery.md`

Before execution:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating SHA
2. commit/push this instruction as a **docs-only instruction commit**
3. record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - execution base SHA
4. create/use a dedicated rehearsal branch or temporary worktree
5. no force push / history rewrite
6. do not merge rehearsal artifacts into runtime main unless repository documentation policy explicitly requires it

Recommended branch:

`codex/20260824-kr-fresh-live-rehearsal`

---

# 1. Core principle — preserve the failed natural run

Do not delete, rewrite, supersede, or overwrite the 16:00–17:00 natural failure artifacts.

Treat the natural run as immutable evidence:

```text
run_type = NATURAL_FAILED_IMMUTABLE
```

The fresh rehearsal must be a separate evidence class:

```text
run_type = MANUAL_LIVE_REHEARSAL_NO_DELIVERY
```

Use a distinct:
- rehearsal ID
- packet namespace/path
- report namespace
- receipt/audit namespace

Do not reuse the natural run's packet ID.

---

# 2. Why fresh recollection is allowed here

This task is specifically intended to answer:

> With the repaired code and fresh current provider data, can the KR production pipeline now complete end-to-end up to the delivery boundary safely?

It is **not** intended to prove:

> What exactly would have been sent at 16:15.

Therefore:

- use a new current rehearsal cutoff
- record the exact cutoff timestamp
- allow fresh read-only provider calls
- distinguish all new data from the 16:15 natural evidence
- do not merge new values into the old natural run

---

# 3. Hard prohibitions

Do NOT:

- delete the failed natural run
- rewrite the failed natural packet/archive
- rewrite production receipts
- manually send Telegram
- create real production Telegram delivery rows
- set `sent_at`
- claim exactly-once natural proof
- run the actual KR Scheduled Task
- trigger primary/backup schedulers
- mutate assessment DB
- mutate warning lifecycle
- mutate thesis versions
- mutate Pilot
- enable Trade AR
- change Inventory mode
- change Phase 9.0E mode
- change macro temporal config
- change night-futures/KRX schedules or logic
- change production schedule
- alter current price/valuation/supply formulas
- call paid providers
- use fresh data to rewrite 16:15 source facts

---

# 4. Fresh rehearsal identity

Create a deterministic rehearsal identity such as:

`2026-08-24-kr-live-rehearsal-<short-id>`

Record:

```text
rehearsal_id
run_type
created_at_kst
cutoff_at_kst
base_sha
market
target_xkrx_date
source_mode = fresh_read_only
delivery_mode = disabled
```

This identity must not collide with production run IDs.

---

# 5. Rehearsal cutoff

Before provider calls, set and persist one rehearsal cutoff:

`REHEARSAL_CUTOFF_KST = <actual timestamp>`

All "current" / "today" / temporal eligibility in this rehearsal must use this cutoff.

Do not mix facts retrieved after the cutoff into the same rehearsal packet unless the production architecture already supports staged retrieval and records retrieval timestamps.

---

# 6. XKRX target resolution

Use the repaired role-target resolver.

Verify:

- wall-clock date
- role = KR production rehearsal
- target XKRX trading date
- valid completed session
- target eligibility

Do not bypass the producer role-target contract just because this is manual.

Expected today:
valid KR trading-day target.

If no valid target exists:
stop and report `REHEARSAL_NOT_ELIGIBLE`.

Do not force a packet.

---

# 7. Fresh provider collection

Perform the same **read-only** data collection required by current KR production for the active monitored universe.

Use actual current provider paths.

Collect as applicable:

- company/news/event evidence
- OpenDART / official financial evidence
- price/OHLCV context
- supply / investor-flow evidence
- valuation inputs
- macro context
- working-capital canonical inputs if normal path refreshes them
- any other currently required deterministic packet evidence

Do not add new providers.

Report provider call counts by provider and purpose.

---

# 8. Fresh vs stored evidence labeling

Every rehearsal fact must be classified:

```text
FRESH_RECOLLECTED
REUSED_CANONICAL
REUSED_IMMUTABLE_REFERENCE
UNAVAILABLE
```

Do not silently mix current recollection and prior natural evidence.

For each key user-visible number, preserve:
- source type
- observed_at
- retrieved_at
- as_of_date
- cutoff eligibility

---

# 9. Active KR universe

Use actual active KR monitored universe.

Do not hard-code seven tickers.

Record:
- universe count
- tickers
- analysis success/failure

Expected current class:
approximately 7 active KR names, but repository state is authoritative.

---

# 10. Run the repaired production analysis path

Execute the same core analysis path as normal KR production, but in rehearsal/no-delivery mode.

Target sequence:

```text
valid target
→ company analysis
→ canonical packet assembly
→ production safety gate
→ immutable rehearsal packet persistence
→ packet-bound dry-run delivery intents
→ AI candidate
→ validators
→ deterministic fallback
→ final 1 + N message render
→ no send
```

Do not short-circuit important production gates.

---

# 11. Packet persistence acceptance

The repaired code must prove:

```text
analysis complete
production target valid
production safety gate pass
rehearsal packet persisted = 1
```

Use a rehearsal-only packet location or namespace.

Do not overwrite production packet paths.

---

# 12. Delivery-intent dry run

Simulate packet-bound delivery intent creation without touching production notification tables.

Preferred:
- existing dry-run / in-memory / temp-store mechanism

If no safe dry-run exists:
create a rehearsal-only intent model/file artifact.

Required proof:

```text
expected message intents = 1 market digest + N stock messages
packet linkage = complete
duplicate intents = 0
orphan intents = 0
deliverable production rows written = 0
```

Do not insert real notificationdelivery rows merely for rehearsal.

---

# 13. AI candidate

Generate the current production AI candidate using the rehearsal packet.

Record:

- candidate generated
- bounded correction attempts
- numeric validation
- semantic validation
- final-language validation
- runtime-quality validation
- exact hard/quality errors
- whether AI would be eligible for production delivery

Do not send.

---

# 14. Deterministic fallback

Generate the full deterministic fallback bundle from the same rehearsal packet.

Expected:

- market digest 1
- stock messages N
- no missing messages
- no duplicate messages

This is the safety reference.

---

# 15. AI / fallback factual parity

Compare:

- ticker
- core status
- valuation
- price/RR
- supply
- Inventory context
- cash-flow context
- macro context
- next checks

Factual mismatch target:
`0`

Prose may differ.

---

# 16. Inventory user-visible rehearsal

For every KR stock record:

```text
ticker
inventory canonical eligibility
materiality selected
user-visible selected/suppressed
context ID
Fact IDs
relation ID
balance date
comparison basis
AI wording
fallback wording
```

Set:

`INVENTORY_USER_VISIBLE_REHEARSAL = PASS / FAIL / NOT_OBSERVED`

PASS requires at least one selected Inventory example with:

- total Inventory semantic
- correct Fact/relation IDs
- PIT/currentness safe
- numeric binding
- semantic guard
- causal guard
- no Inventory Days/CCC
- no unsupported demand/oversupply conclusion
- AI/fallback parity

If no Inventory is selected:
`NOT_OBSERVED`, not FAIL.

Do not call this natural proof.

---

# 17. Trade AR negative control

Hard target:

```text
new exact Trade AR user-visible enrichment = 0
broad AR user-visible enrichment = 0
AP user-visible enrichment = 0
```

The 9.1D canary may still generate shadow Trade AR context separately.

Do not enable Trade AR.

---

# 18. KR investor-flow fresh rehearsal

For every stock:

- 1D flow
- 5D flow
- 20D flow
- foreign
- institution
- retail
- additional canonical participant categories
- full reconciliation
- omitted participant materiality
- signal basis window
- primary signal wording

Hard targets:

```text
reconciliation errors = 0
residual-invented participant = 0
unsupported absorber attribution = 0
timeless mixed-window attribution = 0
```

---

# 19. SK hynix mandatory flow audit

If SK hynix remains monitored:

Review exact current fresh values and resulting wording.

Confirm:

- `주요 3주체` or current approved label
- additional participant effects handled
- 1D/5D/20D basis clear
- no unqualified timeless:
  `외국인 이탈·기관/개인 흡수`
  unless full current evidence truly supports it

No ticker-specific production code.

---

# 20. Macro temporal fresh rehearsal

Use current macro evidence at the rehearsal cutoff.

For every macro item used in the KR digest report:

```text
metric
observation date
retrieval date
temporal role
eligible for important_changes
eligible for today_signal
actual wording
```

Hard targets:

```text
false-current claims = 0
prior-session mislabeled current = 0
reference-lagging reused as today signal = 0
```

Regime may remain based on valid reference context.

---

# 21. Current US/global data caution

Because the rehearsal occurs later than the original KR afternoon run, some global data may have changed or new observations may exist.

That is allowed.

But the report must clearly state:

```text
This is a 19:xx fresh rehearsal, not a 16:15 reconstruction.
```

Do not compare current values to the natural message as if the only difference were code.

---

# 22. Price / RR rehearsal

For every stock verify:

- current price/as-of basis
- dynamic support/resistance
- RR
- invalidation
- confirmation lifecycle
- Fact ownership
- no fabricated levels

Use the normal repaired contracts.

---

# 23. Valuation rehearsal

Verify:

- current PBR/PER/fPBR/fPER only where basis safe
- current vs historical ownership
- fail-closed behavior
- no working-capital-driven automatic valuation change
- no unsafe denominator reconstruction

---

# 24. Working-capital / cash-flow coexistence

For any stock with both selected FCF and Inventory context:

Audit the user-visible priority/redundancy rule.

Allowed:
- FCF wins
- Inventory wins
- one integrated cautious sentence

Reject:
- duplicate accounting blocks
- incompatible periods
- contradictory interpretation
- causal overclaim

---

# 25. Market digest output

Generate one exact rehearsal KR market digest.

Audit:

- macro temporal honesty
- domestic-vs-global composition
- data cautions
- no stale/current confusion

Do not treat the still-US-heavy localization gap as a correctness failure unless wording is temporally false.

---

# 26. Final rehearsal bundle

Generate exact non-delivery output:

```text
1 × KR market digest
N × stock messages
```

Record:

- exact order
- AI candidate bundle
- fallback bundle
- which bundle would have been selected by production logic
- no actual send

---

# 27. Exactly-once scope

This rehearsal cannot prove actual natural exactly-once delivery.

It can prove:

- one packet
- one logical dry-run intent per expected message
- no duplicate intent
- no orphan intent
- production notification tables untouched

Report:

```text
NATURAL_EXACTLY_ONCE_PROOF = NOT_APPLICABLE_TO_REHEARSAL
```

---

# 28. Production mutation audit

Before and after rehearsal, verify no change to:

- notificationdelivery production rows
- sent_at
- production packet archive
- assessment DB
- warning lifecycle
- thesis versions
- Pilot
- feature modes
- schedules

If any unintended mutation occurs:
P0.

---

# 29. Optional supplemental recollection rule

Do not repeatedly refetch data just to make fields complete.

Use one normal collection pass.

Only if the normal production code itself performs a documented retry/fallback provider call may the rehearsal do the same.

No ad hoc supplemental scraping.

---

# 30. Before/after natural failure comparison

Create a comparison between:

### 16:xx natural failed run
- analysis 7/7
- packet blocked
- sent 0

### 19:xx fresh rehearsal
- new cutoff
- new data snapshot
- packet persisted?
- intents dry-run?
- AI/fallback?
- Inventory?
- flow wording?
- macro temporal?

Explicitly state:

`data snapshots are not directly numerically comparable`.

Compare **pipeline behavior**, not raw market values.

---

# 31. Rehearsal gate

Set:

`KR_FRESH_LIVE_REHEARSAL_READY = YES/NO`

YES requires:

- valid target
- fresh collection succeeds sufficiently
- analysis succeeds
- packet persists
- dry-run intents complete
- AI/fallback pipeline reachable
- fallback full bundle complete
- no production mutation
- no orphan/duplicate
- Inventory/Trade AR rules respected
- investor-flow attribution safe
- macro temporal safe
- price/valuation safe
- P0 = 0
- material P1 = 0

---

# 32. Rehearsal result states

Set exactly:

```text
KR_PRODUCTION_REPAIRED_LIVE_REHEARSAL =
PASS / FAIL

INVENTORY_USER_VISIBLE_REHEARSAL =
PASS / FAIL / NOT_OBSERVED

KR_INVESTOR_FLOW_REHEARSAL =
PASS / FAIL

MACRO_TEMPORAL_REHEARSAL =
PASS / FAIL

KR_PACKET_DELIVERY_DRY_RUN =
PASS / FAIL
```

Do not use `LIVE_PASS` or `NATURAL` in these rehearsal states.

---

# 33. What remains pending after PASS

Even if rehearsal is perfect, keep:

```text
KR_PRODUCTION_NATURAL = PENDING
INVENTORY_USER_VISIBLE_NATURAL = PENDING / existing state
KR_INVESTOR_FLOW_NATURAL = PENDING
MACRO_TEMPORAL_NATURAL = PENDING
```

until the next actual scheduled natural packet.

The remaining natural proof should be limited to:

- scheduler lifecycle
- actual terminal receipt
- actual Telegram exactly-once delivery
- actual selected message user-visible proof

---

# 34. Required reports

Create:

1. `docs/reports/20260824-kr-fresh-rehearsal-registration.md`
2. `docs/reports/20260824-kr-fresh-provider-collection.md`
3. `docs/reports/20260824-kr-fresh-packet-persistence.md`
4. `docs/reports/20260824-kr-fresh-ai-validation.md`
5. `docs/reports/20260824-kr-fresh-fallback-bundle.md`
6. `docs/reports/20260824-kr-fresh-inventory-rehearsal.md`
7. `docs/reports/20260824-kr-fresh-investor-flow-rehearsal.md`
8. `docs/reports/20260824-kr-fresh-macro-temporal-rehearsal.md`
9. `docs/reports/20260824-kr-fresh-price-valuation-regression.md`
10. `docs/reports/20260824-kr-fresh-live-rehearsal-before-after.md`
11. `docs/reports/20260824-kr-fresh-live-rehearsal-gates.md`
12. `docs/reports/20260824-kr-fresh-live-rehearsal-artifact-index.md`

Recommended JSON:

`docs/reports/20260824-kr-fresh-live-rehearsal-summary.json`

---

# 35. Exact message preview report

Create:

`docs/reports/20260824-kr-fresh-live-rehearsal-message-bundle.md`

Include:

- exact rehearsal market digest
- exact 7/actual-N stock messages
- AI version where valid
- fallback version
- selected production-preference version

Clearly watermark/header:

`MANUAL LIVE REHEARSAL — NOT SENT`

No Telegram destination metadata.

---

# 36. Mandatory result ZIP

Create:

`20260824-kr-fresh-live-rehearsal-no-delivery-bundle.zip`

Include all sanitized reports and message previews.

Compute/report SHA-256.

---

# 37. Completion response

Return:

```text
REHEARSAL_ID = ...
REHEARSAL_CUTOFF_KST = ...

KR_FRESH_LIVE_REHEARSAL_READY = ...

KR_PRODUCTION_REPAIRED_LIVE_REHEARSAL = ...
KR_PACKET_DELIVERY_DRY_RUN = ...

AI_CANDIDATE = PASS / FAIL
FALLBACK_BUNDLE = PASS / FAIL

INVENTORY_USER_VISIBLE_REHEARSAL = ...
TRADE_AR_USER_VISIBLE_ENRICHMENT = 0 / unexpected

KR_INVESTOR_FLOW_REHEARSAL = ...
MACRO_TEMPORAL_REHEARSAL = ...

PACKET_COUNT = ...
DRY_RUN_INTENT_COUNT = ...
DUPLICATE_INTENTS = ...
ORPHAN_INTENTS = ...

PRODUCTION_DB_MUTATION = 0
TELEGRAM_SEND = 0
SCHEDULED_TASK_RUN = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

NATURAL_PROOFS_STILL_PENDING = ...

ZIP = ...
ZIP_SHA256 = ...
REPORT_COMMIT = ...
```

---

# 38. Severity

## P0

- production DB mutation
- Telegram send
- overwrite/delete natural evidence
- wrong packet target
- wrong user-visible fact
- Trade AR leakage
- packetless dry-run intent
- duplicate/orphan intent
- unsafe macro false-current claim

## P1

- repaired packet still cannot persist
- AI/fallback factual mismatch
- material Inventory causal error
- investor-flow attribution regression
- macro temporal regression
- packet/delivery dry-run integrity failure

## P2

- AI quality fallback with safe deterministic bundle
- Inventory not selected
- Trade AR still not observed
- KR digest localization still global-heavy
- minor wording

---

# 39. Final philosophy

There is no need to delete today's failed natural evidence.

There is also no need to wait until tomorrow to test the repaired code against current live data.

The correct evidence model is:

```text
16:xx natural failed run
= immutable proof of the defect

19:xx fresh live rehearsal
= current-data proof that the repaired pipeline can now complete safely up to delivery

next natural scheduled run
= final proof of scheduler + actual Telegram exactly-once lifecycle
```

Do not blur these three evidence classes.

A fresh rehearsal is valuable precisely because it tests the repaired production stack with current real provider data while keeping user delivery and production state untouched.
