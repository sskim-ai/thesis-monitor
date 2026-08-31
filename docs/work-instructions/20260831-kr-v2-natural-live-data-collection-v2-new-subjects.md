# thesis-monitor — 2026-08-31 KR V2 Natural Live Data Collection v2
## Include same-day newly monitored KR/US subjects
## Read-only evidence collection; no production mutation

---

# 0. Current runtime monitoring truth

Read-only monitoring inventory captured on 2026-08-31 shows:

## KR active monitored subjects — expected 8

- `000660` SK하이닉스
- `003690` 코리안리
- `005490` POSCO홀딩스
- `005930` 삼성전자
- `010120` LS일렉트릭
- `012450` 한화에어로스페이스
- `047810` 한국항공우주산업  ← same-day newly added
- `086280` 현대글로비스

## US/foreign active monitored subjects — expected 14

- CORZ
- CPNG  ← same-day newly added
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- SNDK
- TSLA
- TSM
- WRD
- WULF

Today’s KR live proof must therefore expect:

```text
1 KR market message
+
8 KR stock messages
=
9 production messages
```

The US `CPNG` subject is not expected in the KR packet.  
It must be included in the next US natural-live proof, whose stock-subject target is 14.

---

# 1. Production schedule semantics to verify

Latest cutover scheduler evidence says the normal AI windows remain:

```text
US primary   08:15 KST
US backup    08:30 KST

KR primary   16:15 KST
KR backup    16:55 KST
```

The operating workflow separately defines:

```text
KR fallback / dispatch deadline = 17:10 KST
```

Historical natural KR proof shows:

```text
16:55 backup claimed the packet
17:10 dispatcher delivered market + stock messages exactly once
```

Therefore distinguish:

```text
16:15 = KR primary AI review slot
16:55 = KR backup AI review slot
17:10 = final fallback/dispatcher deadline / delivery stage
```

Do not describe 17:10 as the primary AI Scheduled Task.

For today capture the actual:
- primary execution
- backup execution if any
- packet claim owner
- final dispatcher timestamp
- actual Telegram delivery timestamps

Do not manually trigger any of them.

---

# 2. Hard prohibition

This task is read-only.

Do NOT:
- manually run KR production
- manually trigger scheduler
- resend Telegram
- create retry
- mutate watchlist
- mutate monitoring state
- mutate accepted decision
- change feature flags
- merge code
- repair production during proof

Gates:
- `MANUAL_PRODUCTION_JOB_TRIGGER = 0`
- `MANUAL_PRODUCTION_SEND = 0`
- `PRODUCTION_STATE_MUTATION = 0`

---

# 3. Canonical KR session

Require:
- `KR_CANONICAL_SESSION_DATE = 2026-08-31`

Capture:
- run/job ID
- packet ID
- scheduled times
- actual primary/backup execution
- claim owner
- dispatcher time
- final delivery time
- exit code
- natural retry relationship if any
- evidence cutoff

---

# 4. Runtime lineage

Capture:
- origin/main HEAD
- operating checkout HEAD
- deployed/runtime code SHA if distinct
- feature/config version

Classify:
- `PASS`
- `DOCUMENTED_DOC_ONLY_DESCENDANT`
- `FAIL`

---

# 5. Feature-state truth

Read:
- visible stock decision engine
- V2 production enabled
- full monitored-stock coverage
- V1 visible state
- V1 rollback availability
- Production Assist

Expected semantics:
- `VISIBLE_STOCK_DECISION_ENGINE = V2_ACCEPTED`
- `V2_PRODUCTION_ENABLED = true`
- `FULL_MONITORED_STOCK_COVERAGE_TARGET = true`
- `V1_VISIBLE_DECISION_ENGINE = false`
- `V1_ROLLBACK_AVAILABLE = true`
- `PRODUCTION_ASSIST = OFF`

No mutation.

---

# 6. Same-day onboarding controls

This is mandatory.

## 6.1 KR new subject

Canonical control:

```text
ticker = 047810
company = 한국항공우주산업
market = KR
active = true
```

Verify the new subject was added early enough to be owned by the 2026-08-31 KR production universe.

Collect:
- monitoring creation/version metadata available in runtime
- active state at packet cutoff
- inclusion in universe snapshot
- evidence packet generated?
- v2 candidate generated?
- adjudication required?
- accepted decision resolved?
- message rendered?
- delivery intent created?
- exact live message delivered?

Required gate:

```text
KR_NEW_SUBJECT_047810 =
FULLY_INCLUDED /
ACTIVE_AFTER_PACKET_CUTOFF /
NOT_READY_SAFE /
MISSING_UNEXPECTED /
FAIL
```

If it was active before packet cutoff and missing from the production packet, treat as material rollout failure.

## 6.2 US new subject

Canonical control:

```text
ticker = CPNG
company = Coupang, Inc.
market = US
active = true
```

Today’s KR proof only verifies:
- active monitoring state exists
- it is NOT wrongly routed into the KR packet
- it is expected for next US natural cycle

Gate:

```text
US_NEW_SUBJECT_CPNG_NEXT_LIVE_ELIGIBILITY =
READY /
NOT_READY_SAFE /
FAIL
```

Do not send CPNG manually today.

---

# 7. KR market-data acquisition

Capture actual current-session data used:
- collection timestamps
- provider/source routes
- completeness
- index context
- sector/size context
- breadth/internal context
- investor flow context
- per-stock flow if used

If Kiwoom:
- expected item/request count
- success count
- failures
- retries
- final completeness

Do not assume historical 42/42 if current config changed.

---

# 8. Per-stock evidence for all 8 KR names

For each:
- canonical identity
- latest earnings checkpoint
- company/thesis events
- market expectation
- valuation context
- evidence fingerprint
- D/W/M OHLCV feature availability
- Price Structure plan
- investor positioning if available
- candidate decision
- prior accepted decision
- evidence delta
- adjudication state
- accepted decision
- confidence
- timing
- evidence maturity
- pricing requirement
- asymmetry
- confirmation cost
- preconfirmation error cost
- preconfirmation_buy
- accepted change conditions

Fresh decisions may be BUY/HOLD/SELL/NOT_READY.

Do not force the old distribution.

---

# 9. New KR subject 047810 full onboarding audit

Because `047810` was newly added today, inspect more strictly than legacy names.

Require:
- company identity correct
- no missing thesis version ownership
- market expectation populated
- valuation framework appropriate for defense/aerospace
- latest earnings period explicit
- Price Structure derived from valid OHLCV
- stored price rules only if actually registered
- investor flow as-of date current/safe
- evidence maturity/asymmetry fields available to v2
- accepted decision ownership complete
- Korean renderer
- BUY/SELL polarity
- upgrade/downgrade conditions decision-aware
- no order command
- exact delivery

If onboarding data was created after the close packet evidence cutoff:
record `ACTIVE_AFTER_PACKET_CUTOFF`, not a false production failure.

---

# 10. Candidate → adjudication → accepted

For all 8:

```text
candidate_decision
→ material disagreement?
→ adjudication if required
→ accepted_decision
```

Hard:
- `KR_RAW_CANDIDATE_VISIBLE = 0`
- `KR_UNADJUDICATED_MATERIAL_CHANGE_VISIBLE = 0`
- `KR_SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN = 0`

---

# 11. Decision block visibility

For all accepted-ready KR subjects:
- explicit BUY/HOLD/SELL
- confidence
- timing if selected
- bullish BUY-side evidence only
- bearish SELL-side evidence only
- neutral/Unknown separate
- accepted reasoning consistent with top-level decision

Target after same-day KR addition:

```text
KR_DECISION_BLOCK_VISIBLE_COUNT = 8
```

unless `047810` or another subject is legitimately NOT_READY.

---

# 12. 003690 wording regression

Verify `코리안리(003690)` does not say:
- `보유 판단으로 낮추고`
- `HOLD로 낮춘다`

Gate:
- `KR_003690_CHANGE_CONDITION_WORDING = PASS / FAIL`

---

# 13. Price Structure

For all 8:
- current price
- structure close
- near support/resistance
- major price-anchored structural levels
- completed Bollinger
- provisional Bollinger
- stored rules if applicable

Gate:
- `KR_PRICE_STRUCTURE_CONTRACT = PASS / FAIL`

Special control:
`047810` must not inherit another ticker’s levels or stale onboarding snapshot.

---

# 14. Valuation

For all 8:
- primary method
- safe multiples
- historical context
- security/currency/share basis
- unavailable items fail closed

Gate:
- `KR_VALUATION_CONTRACT = PASS / FAIL`

Special control:
`047810` valuation must use its own canonical evidence and defense/aerospace-relevant framework; do not copy 012450’s facts merely because both are defense-related.

---

# 15. Production message set

Expected current-universe KR production set:

```text
KR market = 1
KR stocks = 8
TOTAL = 9
```

Gates:
- `KR_EXPECTED_PRODUCTION_MESSAGE_COUNT = 9`
- `KR_EXPECTED_STOCK_MESSAGE_COUNT = 8`

If runtime universe snapshot at packet cutoff proves `047810` was added too late, report:
- expected-at-cutoff count
- current count
- exact onboarding timestamp/cutoff relation

Do not silently redefine success.

---

# 16. Exactly-once

Capture:
- packets
- intents
- sent
- received
- duplicates
- orphans
- unowned retries

Target:
- 9/9 if 047810 was in cutoff universe
- duplicate 0
- orphan 0
- unowned retry 0

Gates:
- `KR_LIVE_EXACT_PAYLOAD = PASS / FAIL`
- `KR_EXACTLY_ONCE_DELIVERY = PASS / FAIL`

---

# 17. Dispatcher timing

Capture exact timestamps:

```text
KR_PRIMARY_ACTUAL_TIME = ...
KR_BACKUP_ACTUAL_TIME = ...
KR_PACKET_CLAIM_TIME = ...
KR_DISPATCHER_ACTUAL_TIME = ...
KR_FIRST_DELIVERY_TIME = ...
KR_LAST_DELIVERY_TIME = ...
```

Determine:

```text
KR_DELIVERY_TIMING =
NORMAL_1710_DISPATCH /
EARLY_VALID_DISPATCH /
NATURAL_RETRY_VALID /
LATE /
MISSING /
OTHER
```

Do not assume the visible Telegram arrival must be exactly 17:10:00.
The contract to verify is ownership/deadline behavior, not second-level clock equality.

---

# 18. Message quality

For all 8:
- explicit v2 decision
- Korean consistency
- no raw candidate
- no self-transition
- no contradictory decision
- no empty visible section header
- correct Price Structure
- readable valuation
- honest Unknowns
- useful next checks

Record:
- `KR_EMPTY_VISIBLE_SECTION_COUNT`

Gate:
- `KR_V2_MESSAGE_QUALITY = PASS / PARTIAL_SAFE / FAIL`

---

# 19. P0 / P1 / P2

P0:
- secret/wrong recipient
- duplicate prod delivery
- raw candidate exposed as final
- wrong ticker identity

Material P1:
- V2 absent systematically
- new 047810 active-before-cutoff but silently omitted
- unadjudicated decision visible
- same-evidence unexplained flip
- Price Structure/valuation cross-ticker contamination
- systematic polarity/localization failure

P2:
- isolated awkward wording
- minor density issue
- empty optional section

---

# 20. Final KR classification

Set:
- `KR_V2_NATURAL_LIVE = PASS / PARTIAL_SAFE / FAIL`

PASS if:
- natural run only
- session 2026-08-31
- runtime feature state correct
- monitored cutoff universe correctly resolved
- if 047810 active before cutoff: 8/8 KR stock messages include it
- accepted V2 visible for all eligible
- raw candidate 0
- unadjudicated visible 0
- 003690 wording PASS
- Price Structure/valuation PASS
- expected delivery exact
- no duplicate/orphan/unowned retry
- P0/material P1 = 0/0

---

# 21. US next-cycle preparation record

Do not run US production.

Create a small readiness appendix for tomorrow’s US natural proof:

Expected active US/foreign count now:

```text
14
```

Mandatory new-subject control:

```text
CPNG = Coupang, Inc.
```

Capture only:
- active state
- monitoring thesis/version
- evidence readiness
- route eligibility
- expected next US session

Set:

```text
US_NEXT_LIVE_EXPECTED_STOCK_COUNT = 14
US_NEW_SUBJECT_CPNG_NEXT_LIVE_ELIGIBILITY = ...
```

---

# 22. Required reports

Create:
1. `docs/reports/20260831-kr-v2-natural-live-run-identity.md`
2. `docs/reports/20260831-kr-v2-runtime-lineage.md`
3. `docs/reports/20260831-kr-v2-feature-state.md`
4. `docs/reports/20260831-cross-market-same-day-new-subjects.md`
5. `docs/reports/20260831-kr-v2-monitored-universe.md`
6. `docs/reports/20260831-kr-v2-047810-onboarding.md`
7. `docs/reports/20260831-us-cpng-next-live-readiness.md`
8. `docs/reports/20260831-kr-v2-market-data-collection.md`
9. `docs/reports/20260831-kr-v2-investor-flow-collection.md`
10. `docs/reports/20260831-kr-v2-candidate-adjudication-accepted.md`
11. `docs/reports/20260831-kr-v2-price-structure.md`
12. `docs/reports/20260831-kr-v2-valuation.md`
13. `docs/reports/20260831-kr-v2-live-exact-messages.md`
14. `docs/reports/20260831-kr-v2-live-delivery.md`
15. `docs/reports/20260831-kr-v2-dispatch-timing.md`
16. `docs/reports/20260831-kr-v2-message-quality.md`
17. `docs/reports/20260831-kr-v2-natural-live-proof.md`
18. `docs/reports/20260831-kr-v2-natural-live-artifact-index.md`

Machine-readable:
- `20260831-kr-v2-accepted-decisions.json`
- `20260831-kr-v2-live-delivery.json`
- `20260831-cross-market-new-subject-readiness.json`
- `20260831-kr-v2-natural-live-proof.json`

---

# 23. Required gates

```text
MANUAL_PRODUCTION_JOB_TRIGGER = 0 / NONZERO
MANUAL_PRODUCTION_SEND = 0 / NONZERO
PRODUCTION_STATE_MUTATION = 0 / NONZERO

KR_CANONICAL_SESSION_DATE = 2026-08-31 / OTHER
KR_MONITORED_SUBJECT_COUNT = 8 / OTHER
US_NEXT_LIVE_EXPECTED_STOCK_COUNT = 14 / OTHER

KR_NEW_SUBJECT_047810 =
FULLY_INCLUDED /
ACTIVE_AFTER_PACKET_CUTOFF /
NOT_READY_SAFE /
MISSING_UNEXPECTED /
FAIL

US_NEW_SUBJECT_CPNG_NEXT_LIVE_ELIGIBILITY =
READY /
NOT_READY_SAFE /
FAIL

KR_PRIMARY_ACTUAL_TIME = ...
KR_BACKUP_ACTUAL_TIME = ...
KR_PACKET_CLAIM_TIME = ...
KR_DISPATCHER_ACTUAL_TIME = ...
KR_FIRST_DELIVERY_TIME = ...
KR_LAST_DELIVERY_TIME = ...

KR_DELIVERY_TIMING =
NORMAL_1710_DISPATCH /
EARLY_VALID_DISPATCH /
NATURAL_RETRY_VALID /
LATE /
MISSING /
OTHER

KR_MARKET_DATA_COLLECTION = PASS / PARTIAL_SAFE / FAIL
KR_INVESTOR_FLOW_COLLECTION = PASS / PARTIAL_SAFE / NOT_AVAILABLE / FAIL

KR_SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN = 0 / NONZERO
KR_UNADJUDICATED_MATERIAL_CHANGE_VISIBLE = 0 / NONZERO
KR_RAW_CANDIDATE_VISIBLE = 0 / NONZERO

KR_ACCEPTED_READY_COUNT = ...
KR_NOT_READY_COUNT = ...
KR_ACCEPTED_BUY_COUNT = ...
KR_ACCEPTED_HOLD_COUNT = ...
KR_ACCEPTED_SELL_COUNT = ...
KR_DECISION_BLOCK_VISIBLE_COUNT = ...

KR_003690_CHANGE_CONDITION_WORDING = PASS / FAIL
KR_PRICE_STRUCTURE_CONTRACT = PASS / FAIL
KR_VALUATION_CONTRACT = PASS / FAIL

KR_EXPECTED_STOCK_MESSAGE_COUNT = 8 / OTHER
KR_EXPECTED_PRODUCTION_MESSAGE_COUNT = 9 / OTHER
KR_SENT_PRODUCTION_MESSAGE_COUNT = ...
KR_RECEIVED_PRODUCTION_MESSAGE_COUNT = ...

KR_LIVE_EXACT_PAYLOAD = PASS / FAIL
KR_EXACTLY_ONCE_DELIVERY = PASS / FAIL
KR_DUPLICATE = 0 / NONZERO
KR_ORPHAN = 0 / NONZERO
KR_UNOWNED_RETRY = 0 / NONZERO

KR_EMPTY_VISIBLE_SECTION_COUNT = ...
KR_V2_MESSAGE_QUALITY = PASS / PARTIAL_SAFE / FAIL

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

KR_V2_NATURAL_LIVE = PASS / PARTIAL_SAFE / FAIL
```

---

# 24. Completion response

Return:

```text
RUN_ID = ...
PACKET_ID = ...
KR_CANONICAL_SESSION_DATE = 2026-08-31

ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

KR_PRIMARY_ACTUAL_TIME = ...
KR_BACKUP_ACTUAL_TIME = ...
KR_PACKET_CLAIM_TIME = ...
KR_DISPATCHER_ACTUAL_TIME = ...
KR_FIRST_DELIVERY_TIME = ...
KR_LAST_DELIVERY_TIME = ...
KR_DELIVERY_TIMING = ...

KR_MONITORED_SUBJECT_COUNT = 8
KR_NEW_SUBJECT_047810 = ...

US_NEXT_LIVE_EXPECTED_STOCK_COUNT = 14
US_NEW_SUBJECT_CPNG_NEXT_LIVE_ELIGIBILITY = ...

KR_DECISIONS =
000660 ...
003690 ...
005490 ...
005930 ...
010120 ...
012450 ...
047810 ...
086280 ...

KR_ACCEPTED_READY_COUNT = ...
KR_NOT_READY_COUNT = ...
KR_ACCEPTED_BUY_COUNT = ...
KR_ACCEPTED_HOLD_COUNT = ...
KR_ACCEPTED_SELL_COUNT = ...
KR_DECISION_BLOCK_VISIBLE_COUNT = ...

KR_RAW_CANDIDATE_VISIBLE = 0
KR_UNADJUDICATED_MATERIAL_CHANGE_VISIBLE = 0
KR_SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN = 0

KR_003690_CHANGE_CONDITION_WORDING = ...
KR_PRICE_STRUCTURE_CONTRACT = ...
KR_VALUATION_CONTRACT = ...

KR_EXPECTED_STOCK_MESSAGE_COUNT = 8
KR_EXPECTED_PRODUCTION_MESSAGE_COUNT = 9
KR_SENT_PRODUCTION_MESSAGE_COUNT = ...
KR_RECEIVED_PRODUCTION_MESSAGE_COUNT = ...
KR_LIVE_EXACT_PAYLOAD = ...
KR_EXACTLY_ONCE_DELIVERY = ...
KR_DUPLICATE = 0
KR_ORPHAN = 0
KR_UNOWNED_RETRY = 0

KR_V2_MESSAGE_QUALITY = ...
OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

KR_V2_NATURAL_LIVE = ...

NEXT_ACTION =
WAIT_FOR_US_NATURAL_LIVE_14_SUBJECTS /
BOUNDED_REPAIR /
ROLLBACK_REVIEW /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 25. Mandatory ZIP

Create:

`20260831-kr-v2-natural-live-data-collection-v2-new-subjects-bundle.zip`

Include all reports above plus:
- exact 1 KR market message
- exact 8 KR stock messages if 047810 was cutoff-eligible
- 047810 onboarding evidence
- CPNG next-US-cycle readiness
- scheduler/dispatcher timing evidence
- machine-readable JSON

Exclude secrets, recipient IDs, tokens, auth headers, account identifiers, and hidden chain-of-thought.

---

# Final principle

Same-day newly monitored subjects are part of the proof.

For KR, `047810` must be included today if it was active before the packet cutoff.

For US, `CPNG` must be ready for the next US natural cycle, not manually forced into today’s KR run.

And schedule semantics must remain explicit:

`16:15 primary → 16:55 backup → 17:10 final dispatcher/fallback deadline`.
