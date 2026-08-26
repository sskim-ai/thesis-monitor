# thesis-monitor — 2026-08-26 US Morning Natural Production Review
## Scheduler / delivery / structured US market context / Nasdaq breadth / Free Analyst canary / message quality
## Review-first. No manual production rerun. No broad repair in this task.

## Metadata

- Workstream: `20260826_US_MORNING_NATURAL_PRODUCTION_REVIEW`
- Instruction version: `1.0`
- Review date: `2026-08-26 KST`
- Target natural run: regularly scheduled US morning production run observed on `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `NATURAL_PRODUCTION_EVIDENCE_REVIEW`
- Production mutation from review: `0`
- Manual Telegram send: `0`
- Manual scheduled-task run: `0`
- Open Research production integration: preserve `0`
- Trade AR: preserve `OFF`
- Free Analyst full mode: preserve `OFF`
- Existing bounded canary: preserve current configured limits
- Source policy: `FREE_ONLY`

### Expected pre-review baseline

Most recently reported safe production main / operating before the separate Fibonacci v2 work:

`0e916197b2d3214d9a10a6ed0ae17c09c9f00f3e`

The Fibonacci multi-timeframe shadow work may finish before this review is executed. Therefore do not hard-code the baseline SHA.

At review start resolve and record:

```text
origin/main
operating SHA
scheduled task revision / deploy SHA
natural run start/end time
```

The review must evaluate the code that actually produced the natural messages.

---

# 0. Objective

Inspect the `2026-08-26 KST` US morning natural production result without manually rerunning production.

Answer five questions:

```text
1. Did the scheduled US production task run naturally and exactly once?
2. Did the completed US session produce the correct structured market context?
3. Did Nasdaq exchange breadth enter only when exact-session data was actually available?
4. Did the current Free Analyst / Adaptive path produce useful, entity-specific messages?
5. Did any newly integrated shadow-only Fibonacci code leak into user-visible messages or disturb production?
```

This is primarily an evidence review.

If a P0 or material P1 is found:
- document it precisely
- create a bounded repair recommendation
- do not broaden this review into a redesign

P2 does not block phase advancement.

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-us-morning-natural-production-review.md`

Before review:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. commit/push this exact instruction as a docs-only instruction commit
2. create a review branch from actual latest safe main:
   `codex/20260826-us-morning-natural-review`
3. no production behavior change on the review branch
4. no force push/history rewrite

If code repair becomes necessary:
- finish the review artifacts first
- create a separate bounded-repair branch/instruction or explicit repair section
- do not mix undocumented fixes into the evidence review

---

# 2. Hard prohibitions

Do NOT:

- manually trigger the normal US scheduled task
- manually send Telegram
- delete/rewrite production receipts
- mutate production monitoring state
- write official thesis assessments during review
- alter watchlist/monitoring membership
- turn a replay into natural evidence
- backfill stale Nasdaq breadth into the natural packet
- label Nasdaq-only breadth as all-US/NYSE breadth
- enable NYSE breadth from an unapproved source
- enable Open Research
- enable Trade AR
- enable Free Analyst full mode
- increase canary limits
- expose tokens/secrets
- claim Fibonacci user-visible success from shadow output

---

# 3. Natural-run identity

Resolve the actual natural run.

Record:

```text
task / scheduler ID
scheduled_at
started_at
finished_at
market = US
target market session date
packet ID(s)
receipt ID(s)
delivery intent ID(s)
Telegram/message IDs where available
producer/deploy SHA
```

The market session date must come from packet/runtime metadata.

Do not infer it only from KST calendar date.

---

# 4. Natural vs replay evidence classes

Keep evidence classes separate:

```text
NATURAL_PRODUCTION
REPLAY
SHADOW
```

Natural evidence proves:
- scheduler
- provider freshness
- packet creation
- route selection
- delivery
- receipt/exactly-once

Replay proves:
- deterministic reproducibility
- validator/code behavior

Shadow proves:
- not-yet-user-visible feature behavior

Never merge labels.

---

# 5. Scheduler / run health

Verify:

```text
scheduled task fired naturally
one expected run
no overlapping duplicate run
no manual invocation
no unexpected retry storm
terminal state reached
```

Set:

`US_MORNING_SCHEDULER = LIVE_PASS / PARTIAL / FAIL / NOT_OBSERVED`

---

# 6. Packet integrity

For every natural packet verify:

```text
packet ID unique
market/session correct
producer SHA recorded
evidence refs valid
no orphan packet
no duplicate packet for same logical delivery unless explicitly retry-owned
```

Set:

`US_MORNING_PACKET_INTEGRITY = PASS / FAIL`

---

# 7. Delivery / exactly-once

Audit:

```text
delivery intent count
delivered count
fallback count
duplicate count
orphan count
receipt count
Telegram sends
retry ownership
```

Hard target:

```text
duplicate delivery = 0
orphan delivery = 0
unowned retry = 0
```

Do not require AI delivery if the fail-closed path correctly chose deterministic fallback.

Set:

`US_MORNING_EXACTLY_ONCE = PASS / FAIL`

---

# 8. Completed-session correctness

Verify the packet refers to a completed US regular session.

Check:

```text
session date
regular-session close state
after-hours events separated
premarket events separated
price basis
market calendar
```

Hard target:

`INCOMPLETE_SESSION_PROMOTED_AS_FINAL = 0`

---

# 9. Current US structured market context

Extract the exact normalized context used by the market digest.

Audit availability/freshness of:

```text
SPY
QQQ
IWM
SOXX
RSP / equal-weight context
sector context
rates / real yields
macro temporal context
Nasdaq breadth
NYSE breadth state
```

For every current market fact show:

```text
source
session/as_of
role eligibility
current / reference-lagging
```

Create a compact evidence table.

---

# 10. Index/style relative facts

Verify backend-computed relations such as current available equivalents of:

```text
QQQ vs SPY
IWM vs SPY
SOXX vs SPY
RSP vs SPY
```

Hard requirements:

```text
same completed session
same return convention
no AI arithmetic
numeric provenance registered
```

Do not force all relations into the message.

---

# 11. Sector context

Verify:

```text
expected sector proxies currently integrated
session match
no stale sector mixed with current index session
```

Review whether the digest used sector dispersion materially rather than merely listing ETFs.

Set:

`US_SECTOR_CONTEXT = PASS / PARTIAL / FAIL`

---

# 12. Nasdaq breadth — exact-session contract

Resolve:

```text
packet_session_date
Nasdaq breadth source latest available date
breadth publication state at collection time
```

Possible valid states:

```text
EXACT_SESSION_AVAILABLE
PUBLICATION_PENDING
SOURCE_UNAVAILABLE
```

If exact-session available:
- verify advances
- declines
- unchanged
- denominator
- derived breadth relations
- numeric provenance

If publication-pending:
- breadth must remain Unknown
- stale prior-session breadth must not be injected

Set:

```text
NASDAQ_BREADTH_NATURAL =
LIVE_PASS /
SAFE_PUBLICATION_PENDING /
SOURCE_UNAVAILABLE /
FAIL
```

Hard targets:

```text
STALE_BREADTH_INJECTED = 0
BREADTH_SCOPE_MISLABEL = 0
```

---

# 13. NYSE breadth

Current expected state may still be `UNAVAILABLE` unless an independently approved source was integrated after the last review.

Do not treat safe unavailability as a failure.

Set:

`NYSE_BREADTH_NATURAL = LIVE_PASS / UNAVAILABLE / FAIL`

Do not infer NYSE breadth from Nasdaq breadth.

---

# 14. Market breadth interpretation boundary

If only Nasdaq breadth is available:

Allowed:

```text
Nasdaq 상장종목 내부에서는 상승/하락 참여가 ...였다.
```

Not allowed:

```text
미국시장 전체가 폭넓게 risk-off였다.
```

unless separate broad-market evidence supports that conclusion.

Audit all breadth-derived prose.

---

# 15. US market digest exact message

Capture the exact natural user-visible market digest.

Create:

`docs/reports/20260826-us-morning-exact-natural-messages.md`

For the market digest include:

```text
EXACT_TEXT
delivery timestamp
renderer/path
AI/deterministic/fallback route
validation status
evidence refs used
```

Do not provide paraphrase only.

---

# 16. US market-digest quality review

Evaluate whether the message answers:

```text
What kind of US session was this?
Was weakness/strength broad or concentrated?
How did growth/semiconductor/small-cap/equal-weight differ?
What did rates/real yields contribute?
What remains Unknown?
What next observation would change the interpretation?
```

The message should preserve useful current facts even when breadth is Unknown.

---

# 17. Market-digest quality classifications

Set:

```text
US_MARKET_DIGEST_EVIDENCE_UTILIZATION =
PASS / PARTIAL / FAIL

US_MARKET_DIGEST_BREADTH_BOUNDARY =
PASS / FAIL

US_MARKET_DIGEST_INFORMATION_DENSITY =
GOOD / SAFE_BUT_THIN / OVERLOADED / FAIL
```

Fail if:
- material current evidence existed and was dropped
- stale breadth was used
- Nasdaq-only breadth was generalized to all US equities

---

# 18. Natural AI route / canary state

Resolve actual runtime state.

Record:

```text
Free Analyst candidate count
validated candidate count
Adaptive renderer results
canary eligible count
canary selected count
fallback count
full mode state
canary limits
```

Verify actual bounded limits. Prior design target was:

```text
market <= 1
stocks <= 2
total <= 3
```

Set:

`US_FREE_ANALYST_CANARY_NATURAL = LIVE_PASS / PARTIAL / NOT_OBSERVED / FAIL`

---

# 19. Capture all user-visible natural messages

Capture exact natural texts for all user-visible messages from the run.

At minimum identify:

```text
market digest
AI-canary-selected stock messages
deterministic/fallback stock messages
```

For each record:

```text
entity/ticker
route
renderer
selected?
fallback?
delivery status
validation status
```

---

# 20. Full packet message audit

After preserving natural evidence, a read-only immutable replay may inspect the entire packet candidate set.

Purpose:

`full-message quality audit`

not natural proof.

Expected prior US benchmark size was approximately `14 messages`; report actual count.

Do not recollect providers for this replay.

---

# 21. Entity-specific synthesis quality

For every synthesis-eligible stock require linkage to actual current evidence:

```text
stored investment-logic driver
validation metric
expectation burden
valuation framework
current relation
next check
```

Audit:

```text
cross-industry generic synthesis
wrong industry concept
wrong ticker/entity context
generic filler despite specific support
```

Targets:

```text
CROSS_INDUSTRY_GENERIC_REPETITION = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
```

---

# 22. Mandatory US positive/negative controls

If present in the natural/replay packet, explicitly inspect:

```text
TSM
CORZ
HUT
WULF
CRCL
```

Do not fail if a name is absent.

### TSM
Should remain semiconductor/foundry-specific from current packet evidence.
No generic HPC/billing-MW leakage.

### CORZ/HUT/WULF
Same broad theme may share vocabulary, but each must stay bound to its own current drivers.

### CRCL
Preserve stablecoin/platform/reserve-income economics where current packet supports it.

---

# 23. Expectations / valuation

For messages mentioning expectations or valuation verify:

```text
current stored expectation level
current valuation refs
period/basis
no reverse-engineered denominator
no unsupported forward multiple
```

No one-day price move may silently change the expectation level.

---

# 24. Price / positioning boundary

Audit:

```text
flow/positioning remains tactical
price action remains price context
neither alone changes business logic
```

Hard target:

`POSITIONING_AS_BUSINESS_THESIS_CHANGE = 0`

---

# 25. Macro temporal boundary

Audit:

```text
current observation
reference-lagging macro
scheduled future event
```

No lagging macro value should be written as a fresh same-session observation.

Set:

`US_MACRO_TEMPORAL = PASS / FAIL`

---

# 26. Current Fibonacci v2 interaction

A separate multi-timeframe Fibonacci shadow task may finish before this review.

Determine whether its implementation SHA was present in the code that produced the natural US run.

### Case A — not in producer SHA

```text
FIBONACCI_SHADOW_AT_NATURAL_RUN = NOT_PRESENT
FIBONACCI_USER_VISIBLE_LEAK = NOT_APPLICABLE
```

### Case B — present in producer SHA

Verify:

```text
AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = SHADOW / integrated-not-armed
user-visible Fibonacci price section = absent
current live message route unchanged
Telegram text diff attributable to Fibonacci = 0
```

Hard target:

`FIBONACCI_USER_VISIBLE_LEAK = 0`

Do not treat archived shadow output as natural user-visible evidence.

---

# 27. Optional Fibonacci same-packet shadow inspection

Only after natural evidence is preserved:

if Fibonacci v2 is complete, it is allowed to read/run the already-produced shadow sidecar for the same US packet.

Keep separate:

```text
NATURAL_MESSAGE
vs
FIBONACCI_SHADOW
```

Do not enable it in this task.

---

# 28. Open Research guard

Verify:

`OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0`

Set:

`OPEN_RESEARCH_LEAK = 0`

---

# 29. Trade AR guard

Verify:

`TRADE_AR_USER_VISIBLE = 0`

Set:

`TRADE_AR_LEAK = 0`

---

# 30. Hard safety audit

Across natural messages and immutable replay:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
SESSION_DATE_CONFLICT = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0
DEFAULT_ZERO = 0
STALE_BREADTH_INJECTED = 0
BREADTH_SCOPE_MISLABEL = 0
POSITIONING_AS_BUSINESS_THESIS_CHANGE = 0
TRADE_AR_LEAK = 0
OPEN_RESEARCH_LEAK = 0
```

---

# 31. Delivery safety audit

Hard targets:

```text
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_SCHEDULED_TASK = 0
PRODUCTION_MUTATION_FROM_REVIEW = 0
```

---

# 32. Exact natural-message human review

For each naturally delivered AI/canary message classify:

```text
GOOD_CURRENT_STATE
MATERIAL_IMPROVEMENT
SAFE_BUT_THIN
GENERIC
REGRESSION
```

Mandatory comments:

```text
What is the actual judgment?
Which current facts support it?
Is the company-specific investment logic visible?
Is any section redundant?
Does next-check change the decision?
```

---

# 33. Nasdaq breadth value-add

If exact-session Nasdaq breadth is naturally available, compare against archived pre-breadth reference output.

Do not manipulate the current natural packet and call that natural.

Set:

`NASDAQ_BREADTH_MESSAGE_VALUE_ADD = PASS / NO_MATERIAL_VALUE / NOT_OBSERVED / FAIL`

---

# 34. Natural-result status

Set:

```text
US_MORNING_NATURAL =
LIVE_PASS /
LIVE_PASS_WITH_P2 /
PARTIAL /
FAIL /
NOT_OBSERVED
```

`LIVE_PASS` requires scheduler observed, packet/receipt correct, exactly-once, clean validation, and no P0/material P1.

`LIVE_PASS_WITH_P2` allows only nonblocking issues such as publication-pending breadth, NYSE unavailable, or safe stylistic weakness.

---

# 35. Severity

## P0

- wrong fact/number/session
- duplicate delivery
- wrong ticker/entity
- stale breadth shown as current
- Nasdaq breadth labeled all-US/NYSE
- unsupported numeric/causal claim
- hidden arithmetic
- Trade AR leak
- Open Research leak
- Fibonacci shadow unexpectedly user-visible
- review mutates production state

## P1

- natural AI path unexpectedly falls back broadly because of compatibility defect
- market digest drops material current structured evidence
- cross-industry generic synthesis returns
- expectation/valuation basis is wrong
- macro temporal boundary violated
- canary selects known quality-rejected message
- supplemental provider failure blocks packet

## P2

- Nasdaq exact-session breadth publication-pending
- NYSE breadth unavailable
- safe deterministic fallback for one candidate
- stylistic density
- a stock message unchanged because no material new evidence
- Fibonacci shadow not present in producer SHA

---

# 36. If a defect is found

For each P0/P1 produce:

```text
SYMPTOM
AFFECTED_MESSAGE / PACKET
CONFIRMED_FACT
ROOT_CAUSE
WHY_EXISTING_VALIDATOR_DID/DID_NOT_CATCH_IT
SMALLEST_REPAIR_SURFACE
REPLAY NEEDED
NATURAL REPROOF NEEDED?
```

A material P1 gets one bounded repair.

P2 goes to backlog and does not block next major phase.

---

# 37. Required reports

Create:

1. `docs/reports/20260826-us-morning-natural-run-identity.md`
2. `docs/reports/20260826-us-morning-natural-delivery-exactly-once.md`
3. `docs/reports/20260826-us-morning-natural-structured-context.md`
4. `docs/reports/20260826-us-morning-natural-nasdaq-breadth.md`
5. `docs/reports/20260826-us-morning-exact-natural-messages.md`
6. `docs/reports/20260826-us-morning-market-digest-quality.md`
7. `docs/reports/20260826-us-morning-stock-message-quality.md`
8. `docs/reports/20260826-us-morning-canary-natural-proof.md`
9. `docs/reports/20260826-us-morning-safety-parity.md`
10. `docs/reports/20260826-us-morning-fibonacci-shadow-isolation.md`
11. `docs/reports/20260826-us-morning-natural-readiness.md`
12. `docs/reports/20260826-us-morning-natural-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-us-morning-natural-readiness.json`

---

# 38. Exact-message report requirement

The exact natural-message report must contain raw rendered text for every naturally delivered message.

Required fields:

```text
message index
market/ticker/entity
route
renderer
canary selected?
fallback?
validation
delivered?
receipt
exact text
```

Redact only secrets/account identifiers.

---

# 39. Optional immutable replay report

If replay is required for full packet inspection, create separately:

`docs/reports/20260826-us-morning-immutable-packet-replay.md`

Label:

`REPLAY_NOT_NATURAL`

Include:
- source natural packet ID
- no provider recollection
- full message count
- validator outcome
- quality outcome

---

# 40. Review validation

For a reports-only branch:

```text
git diff --check PASS
artifact index PASS
all natural evidence refs resolvable
no secret leakage
no production behavior change
```

If review utilities/tests are added:
- focused tests PASS
- relevant full tests PASS
- CI PASS

---

# 41. Gates

Set exactly:

```text
US_MORNING_SCHEDULER =
LIVE_PASS / PARTIAL / FAIL / NOT_OBSERVED

US_MORNING_PACKET_INTEGRITY =
PASS / FAIL

US_MORNING_EXACTLY_ONCE =
PASS / FAIL

US_COMPLETED_SESSION =
PASS / FAIL

US_STRUCTURED_MARKET_CONTEXT =
PASS / PARTIAL / FAIL

US_SECTOR_CONTEXT =
PASS / PARTIAL / FAIL

NASDAQ_BREADTH_NATURAL =
LIVE_PASS /
SAFE_PUBLICATION_PENDING /
SOURCE_UNAVAILABLE /
FAIL

NYSE_BREADTH_NATURAL =
LIVE_PASS / UNAVAILABLE / FAIL

NASDAQ_BREADTH_MESSAGE_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / NOT_OBSERVED / FAIL

US_MARKET_DIGEST_EVIDENCE_UTILIZATION =
PASS / PARTIAL / FAIL

US_MARKET_DIGEST_BREADTH_BOUNDARY =
PASS / FAIL

US_MARKET_DIGEST_INFORMATION_DENSITY =
GOOD / SAFE_BUT_THIN / OVERLOADED / FAIL

US_FREE_ANALYST_CANARY_NATURAL =
LIVE_PASS / PARTIAL / NOT_OBSERVED / FAIL

US_ENTITY_SPECIFIC_SYNTHESIS =
PASS / FAIL

US_MACRO_TEMPORAL =
PASS / FAIL

FIBONACCI_SHADOW_AT_NATURAL_RUN =
PRESENT / NOT_PRESENT

FIBONACCI_USER_VISIBLE_LEAK =
0 / NONZERO / NOT_APPLICABLE

OPEN_RESEARCH_LEAK =
0 / NONZERO

TRADE_AR_LEAK =
0 / NONZERO

SAFETY_PARITY =
PASS / FAIL

US_MORNING_NATURAL =
LIVE_PASS /
LIVE_PASS_WITH_P2 /
PARTIAL /
FAIL /
NOT_OBSERVED
```

---

# 42. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
REVIEW_BRANCH = ...
REVIEW_BASE_SHA = ...
REPORT_COMMIT = ...

NATURAL_PRODUCER_SHA = ...
MAIN_AT_REVIEW = ...
OPERATING_AT_REVIEW = ...

US_NATURAL_RUN_ID = ...
US_TARGET_SESSION = ...
US_PACKET_IDS = ...
US_RECEIPT_COUNT = ...
US_DELIVERY_COUNT = ...
US_DUPLICATE_COUNT = ...
US_ORPHAN_COUNT = ...

US_MORNING_SCHEDULER = ...
US_MORNING_PACKET_INTEGRITY = ...
US_MORNING_EXACTLY_ONCE = ...
US_COMPLETED_SESSION = ...

US_STRUCTURED_MARKET_CONTEXT = ...
US_SECTOR_CONTEXT = ...

NASDAQ_BREADTH_SOURCE_LATEST_DATE = ...
NASDAQ_BREADTH_PACKET_SESSION_DATE = ...
NASDAQ_BREADTH_NATURAL = ...
NYSE_BREADTH_NATURAL = ...
NASDAQ_BREADTH_MESSAGE_VALUE_ADD = ...

US_MARKET_DIGEST_EVIDENCE_UTILIZATION = ...
US_MARKET_DIGEST_BREADTH_BOUNDARY = ...
US_MARKET_DIGEST_INFORMATION_DENSITY = ...

FREE_ANALYST_CANDIDATES = ...
FREE_ANALYST_VALIDATED = ...
CANARY_SELECTED = ...
FALLBACK_MESSAGES = ...
US_FREE_ANALYST_CANARY_NATURAL = ...

US_ENTITY_SPECIFIC_SYNTHESIS = ...
CROSS_INDUSTRY_GENERIC_REPETITION = ...
SEMANTIC_OWNERSHIP_ERRORS = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNSUPPORTED_CAUSALITY = 0
TEMPORAL_VIOLATIONS = 0
SESSION_DATE_CONFLICT = 0
HIDDEN_ARITHMETIC = 0
EXTERNAL_UNSOURCED_FACTS = 0
MATERIAL_INFORMATION_LOSS = 0
DEFAULT_ZERO = 0
STALE_BREADTH_INJECTED = 0
BREADTH_SCOPE_MISLABEL = 0
POSITIONING_AS_BUSINESS_THESIS_CHANGE = 0

FIBONACCI_SHADOW_AT_NATURAL_RUN = ...
FIBONACCI_USER_VISIBLE_LEAK = ...
OPEN_RESEARCH_LEAK = ...
TRADE_AR_LEAK = ...

DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_SCHEDULED_TASK = 0
PRODUCTION_MUTATION_FROM_REVIEW = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

SAFETY_PARITY = ...
US_MORNING_NATURAL = ...

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_PROOF /
BOUNDED_REPAIR /
CONTINUE_TO_FIBONACCI_ENABLEMENT_REVIEW /
CONTINUE_TO_OPEN_RESEARCH_CONNECTOR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 43. Mandatory ZIP

Create:

`20260826-us-morning-natural-production-review-bundle.zip`

Include:
- this instruction
- all review reports
- exact natural message report
- sanitized run/packet/receipt evidence
- optional replay report if used
- readiness JSON
- artifact index

Never include tokens, auth headers, account credentials, or secrets.

Compute/report SHA-256.

---

# 44. Final principle

The morning review should not ask only:

```text
"메시지가 왔나?"
```

It should prove:

```text
scheduled run happened naturally
→ correct completed session
→ structured US context was fresh
→ breadth was exact-session or safely absent
→ market digest used the evidence correctly
→ stock analysis stayed entity-specific
→ canary/fallback behaved as configured
→ delivery was exactly once
→ shadow-only Fibonacci did not leak
```

If all of that is clean, treat the morning US run as a real production proof and move forward instead of reopening already-closed architecture work.
