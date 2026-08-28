# thesis-monitor — Price Structure v3 Provisional Bollinger Expansion Layer + Price Label Clarity
## Enable forward-looking dynamic-band reference from valid in-progress bars
## Keep it explicitly provisional and non-authoritative
## Clarify `현재가` vs `가격 구조 기준 종가(정규장)`
## Preserve structural S/R reality gate and completed-bar dynamic Bollinger layer

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `PRICE_STRUCTURE_PROVISIONAL_BOLLINGER_EXPANSION_AND_PRICE_LABEL_CLARITY`
- Task class: `BOUNDED_PRICE_STRUCTURE_RENDERER_EXTENSION + CURRENT_TIME_REPLAY + TEST_SINK`
- US Price Structure: preserve `ON`
- KR Price Structure: preserve `ON`
- Production Assist: preserve `OFF`
- US/KR market-message logic: no functional changes
- Manual production scheduler: `0`
- Production-recipient test send: `0`
- DB / official assessment mutation: `0`

### Latest known operating lineage

The previous Dynamic Bollinger Layer rollout reports:

```text
operating =
5500f539fc93a9162f762cef4f7069f24d0350db
```

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve latest safe `origin/main`
4. resolve actual operating SHA
5. use `5500f5...` or a safe linear descendant
6. record exact lineage
7. do not revert the Major Structural S/R Reality Gate
8. do not revert the completed-bar Dynamic Bollinger layer

---

# 1. Product objective

Keep three distinct layers:

```text
A. Historical / authoritative structure
   가까운 지지/저항
   주요 구조 지지/저항

B. Completed-bar dynamic Bollinger
   볼린저 지지/저항
   → completed D/W/M bars only
   → backend-owned dynamic reference

C. In-progress expansion reference
   잠정 볼린저 지지/저항
   → current partial D/W/M bar may be used
   → explicitly provisional
   → never authoritative
```

And clarify price basis:

```text
현재가
→ latest safe quote / current observable market price

가격 구조 기준 종가(정규장)
→ completed regular-session close used by authoritative Price Structure
```

---

# 2. Why enable a provisional layer

The completed-bar policy is safe but can hide useful expansion information.

Example from prior MU review:

```text
현재가: $935.39
가격 구조 기준 종가(정규장): $915.99

completed monthly Bollinger resistance:
~$938~943 area

previous in-progress monthly Bollinger expansion:
~$1,020~1,025 area
```

The latter must NOT be called:

```text
주요 구조 저항
확정 볼린저 저항
```

but can be useful as:

```text
잠정 볼린저 저항(월봉·진행중)
```

for forward expansion context.

---

# 3. Semantic types

Prefer explicit backend semantic types:

```text
PROVISIONAL_BOLLINGER_SUPPORT
PROVISIONAL_BOLLINGER_RESISTANCE
```

with required metadata:

```text
timeframe
source_family
observation_timestamp
bar_start
bar_expected_close
is_partial_bar = true
security_basis
currency
adjustment_basis
fact_ref / zone_id
```

Do not implement provisional semantics only in AI prose.

Hard:

```text
AI_CALCULATED_PROVISIONAL_BOLLINGER = 0
AI_PROMOTED_PROVISIONAL_BOLLINGER = 0
```

---

# 4. Partial-bar validity gate

A provisional Bollinger zone may use an in-progress bar only if the partial OHLC is internally valid.

Require repository-native equivalent of:

```text
high >= max(open, close, low)
low <= min(open, close, high)
open/high/low/close finite
volume nonnegative if required
timestamp/session monotonic
security/currency/adjustment basis consistent
```

Hard:

```text
MALFORMED_PARTIAL_BAR_USED_FOR_PROVISIONAL_BOLLINGER = 0
```

This means SNDK-like malformed OHLC cannot bypass safety via the provisional layer.

---

# 5. Provisional is non-authoritative

A provisional zone must NEVER feed:

```text
NEAR_SUPPORT / NEAR_RESISTANCE
MAJOR_SUPPORT / MAJOR_RESISTANCE
stored monitoring price rules
confirmation/support/warning/invalidation prices
Fib family consensus
wave anchor state
```

Hard:

```text
PROVISIONAL_BOLLINGER_AS_NEAR_SR = 0
PROVISIONAL_BOLLINGER_AS_MAJOR_SR = 0
PROVISIONAL_BOLLINGER_AS_STORED_RULE = 0
PROVISIONAL_BOLLINGER_AS_FIB_ANCHOR = 0
PROVISIONAL_BOLLINGER_AS_WAVE_ANCHOR = 0
```

---

# 6. Role determination

Relative to the current safe quote / structure reference:

```text
zone entirely below current reference
→ provisional support candidate

zone entirely above current reference
→ provisional resistance candidate

zone straddles reference
→ omit as directional support/resistance
```

Do not infer upper/lower role mechanically without checking price relation.

---

# 7. Timeframe hierarchy for provisional expansion

Analyze:

```text
monthly → weekly → daily
```

for context.

For user-facing provisional expansion:

prefer the highest-timeframe materially useful candidate that adds distinct information.

Typical intent:

```text
monthly provisional band
→ longer expansion reference

weekly provisional band
→ intermediate expansion reference

daily provisional band
→ tactical only; usually omit unless uniquely useful
```

Do not dump all timeframes.

---

# 8. Display budget

Maximum:

```text
PROVISIONAL_BOLLINGER_LINE_COUNT_PER_STOCK <= 1
```

This is intentionally stricter than the completed-bar dynamic layer.

Choose the single most informative distinct provisional band.

Hard:

```text
PROVISIONAL_BOLLINGER_LINE_COUNT_MAX = 1
```

---

# 9. Materiality / distinctness

Display the provisional band only when it adds information not already conveyed by:

```text
near S/R
major structural S/R
completed-bar Bollinger S/R
```

If overlap is material:

do not print a second range.

Instead optional annotation:

```text
· 잠정 월봉 볼린저 중첩
```

if that improves understanding.

Hard:

```text
DUPLICATE_PROVISIONAL_RANGE_VISIBLE = 0
```

---

# 10. User-facing label

Preferred format:

```text
• 잠정 볼린저 저항(월봉·진행중): 약 $1,020~1,025
```

or:

```text
• 잠정 볼린저 지지(주봉·진행중): 약 ...
```

The words:

```text
잠정
진행중
```

must make non-authoritative status obvious.

Do not use:

```text
확정
주요 구조
목표
```

for provisional bands.

---

# 11. Optional explanatory suffix

If message length allows, use a concise suffix:

```text
· 봉 마감 전 변동 가능
```

Example:

```text
• 잠정 볼린저 저항(월봉·진행중): 약 $1,020~1,025 · 봉 마감 전 변동 가능
```

Do not repeat this disclaimer multiple times.

---

# 12. Completed-bar Bollinger remains authoritative dynamic layer

Keep existing completed-bar semantics:

```text
• 볼린저 저항(주봉): ...
• 볼린저 지지(월봉): ...
```

These remain dynamic, not historical structural.

Do not downgrade them just because the provisional layer exists.

---

# 13. Major Structural Reality Gate remains unchanged

Hard:

```text
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
MAJOR_SR_WITHOUT_PRICE_ANCHOR = 0
GOOGL_424_AS_MAJOR_STRUCTURAL = 0
```

A provisional Bollinger range may never reopen the old GOOGL-type semantic defect.

---

# 14. Price-label clarity

When the current safe quote and authoritative Price Structure basis close differ:

render both explicitly.

Required pattern:

```text
💰 가격
• 현재가: $935.39
• 가격 구조 기준 종가(정규장): $915.99
```

or equivalent renderer placement.

Do not leave:

```text
현재가 $935.39
...
기준 종가 $915.99
```

without explaining why there are two prices.

Hard:

```text
AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL = 0
```

---

# 15. Current-price semantic ownership

`현재가` must carry:

```text
source
observation timestamp
market/session state
currency
security basis
```

It may be:

```text
regular-session latest
after-hours
pre-market
delayed quote
```

only if the backend knows the state.

Do not call a stale completed-session close `현재가` when a distinct current-quote concept is intended.

---

# 16. Structure-basis semantic ownership

`가격 구조 기준 종가(정규장)` means:

```text
the completed regular-session close
that owns authoritative SR / completed-bar calculations
```

Required metadata:

```text
session date
close
currency
security basis
adjustment basis
```

Hard:

```text
STRUCTURE_BASIS_CLOSE_WITHOUT_SESSION = 0
```

---

# 17. Same-price collapse policy

If:

```text
current quote == structure basis close
```

within the repository's exact identity semantics:

prefer one concise line:

```text
• 현재가(정규장 종가): ...
```

or preserve two lines only if renderer consistency is better.

Do not create redundant identical lines.

Hard:

```text
DUPLICATE_IDENTICAL_PRICE_LINES = 0
```

---

# 18. Different-price explanatory policy

If prices differ:

always show both labels.

Optional concise state hint:

```text
• 현재가(시간외): $935.39
• 가격 구조 기준 종가(정규장): $915.99
```

only if after-hours/premarket state is actually known.

Do not infer session state from clock alone.

Hard:

```text
INFERRED_QUOTE_SESSION_LABEL_WITHOUT_EVIDENCE = 0
```

---

# 19. MU positive control

Current replay should determine actual values.

Expected semantic shape:

```text
💰 가격
• 현재가: $...
• 가격 구조 기준 종가(정규장): $...

📐 현재 가격 구조
• 가까운 지지: ...
• 가까운 저항: ...
• 주요 구조 ... if price-anchored
• 볼린저 ... if completed-bar material
• 잠정 볼린저 저항(월봉·진행중): ... if valid/material
```

The historical ~$1,020~1,025 area is a regression reference only.

Do not hard-code it.

---

# 20. SK hynix positive control

Verify completed weekly Bollinger remains visible when material.

If an in-progress higher-timeframe provisional band adds distinct information:

it may appear under the provisional label.

No duplicate clutter.

---

# 21. GOOGL negative control

The old derived ~$424 range must not return as:

```text
주요 구조 저항
```

It may appear only as:

```text
볼린저 저항
or
잠정 볼린저 저항
```

if current source/timeframe/materiality rules independently select it.

Otherwise omit.

---

# 22. SNDK / malformed-data control

SNDK currently has a fail-closed history/data-quality issue.

The provisional layer must NOT make SNDK eligible if the underlying partial/completed OHLC is malformed or basis-conflicted.

Hard:

```text
SNDK_PROVISIONAL_LAYER_BYPASS = 0
```

This task does not redefine SNDK eligibility.

---

# 23. WULF control

Same fail-closed principle:

```text
WULF_PROVISIONAL_LAYER_BYPASS = 0
```

---

# 24. Track A — provisional layer implementation

Implement:

```text
partial-bar validation
provisional Bollinger computation/registration
role compatibility
timeframe/materiality selection
one-line display budget
overlap suppression
renderer labels
provenance
AI/fallback parity
```

No target/stop.

---

# 25. Track B — price label implementation

Implement explicit semantic ownership for:

```text
current_quote
structure_basis_close
```

and renderer behavior for equal/different cases.

Do not modify valuation/security-basis calculations.

---

# 26. Track C — current-time US full-universe replay

Replay every current monitored US/foreign stock.

Per ticker record:

```text
current quote
quote timestamp/state
structure basis close/session

near S/R
major structural S/R
completed Bollinger dynamic S/R
provisional Bollinger expansion
timeframe
partial-bar validity
exact renderer
```

---

# 27. Track C — KR 7-control replay

Replay:

```text
000660
003690
005490
005930
010120
012450
086280
```

Verify:

```text
price labels
completed dynamic Bollinger
provisional layer
major structural semantics
message length
```

---

# 28. AI / fallback parity

For every replayed subject:

```text
same current quote
same structure basis close
same provisional eligibility
same provisional numeric
same provisional timeframe label
same omission/overlap decision
```

Hard:

```text
AI_FALLBACK_CURRENT_PRICE_PARITY = PASS
AI_FALLBACK_STRUCTURE_BASIS_PRICE_PARITY = PASS
AI_FALLBACK_PROVISIONAL_BOLLINGER_ELIGIBILITY_PARITY = PASS
AI_FALLBACK_PROVISIONAL_BOLLINGER_NUMERIC_PARITY = PASS
AI_FALLBACK_PROVISIONAL_BOLLINGER_LABEL_PARITY = PASS
```

---

# 29. Test sink

Use the dedicated non-production test sink.

Send:

```text
all current monitored US/foreign stock messages
+
KR 7 control messages
```

No production recipients.

Review actual received messages.

---

# 30. Human review checklist

For each message check:

```text
current price vs structure-basis price understandable
no confusing duplicate prices
provisional band clearly marked
completed vs provisional Bollinger distinguishable
major structural still historical/price-anchored
message not overloaded
no target/stop
```

Hard:

```text
TEST_PRICE_LABEL_QUALITY = PASS
TEST_PROVISIONAL_BOLLINGER_MESSAGE_QUALITY = PASS
TEST_EXACT_PAYLOAD_MATCH = PASS
```

---

# 31. Test message target style

A successful differing-price example should look like:

```text
💰 가격
• 현재가: $935.39
• 가격 구조 기준 종가(정규장): $915.99

📐 현재 가격 구조
• 가까운 지지: ...
• 가까운 저항: ...
• 볼린저 저항(월봉): ...
• 잠정 볼린저 저항(월봉·진행중): ... · 봉 마감 전 변동 가능
```

Only show lines actually supported by the current replay.

---

# 32. Message-density rule

Typical Price Structure block should remain concise.

Maximum standalone lines:

```text
price lines = 2
near S/R = 2
major S/R = 2
completed Bollinger = 2
provisional Bollinger = 1
```

This is a hard ceiling, not a target.

Prefer fewer.

---

# 33. Operating promotion

Deploy only if:

```text
provisional semantics PASS
price-label clarity PASS
US full universe PASS
KR7 PASS
test sink PASS
Major S/R reality gate preserved
SNDK/WULF no bypass
P0 = 0
material P1 = 0
```

Preserve feature states:

```text
US Price Structure ON
KR Price Structure ON
Production Assist OFF
```

---

# 34. Post-deploy smoke

Read-only verify at minimum:

```text
MU
000660
GOOGL
SNDK
WULF
all current US monitored
KR7
```

Hard:

```text
POST_DEPLOY_PROVISIONAL_BOLLINGER = PASS
POST_DEPLOY_PRICE_LABEL_CLARITY = PASS
POST_DEPLOY_MAJOR_SR_REALITY_GATE = PASS
```

---

# 35. Next natural proof

Do not manually trigger production after deployment.

Observe next natural stock messages.

Verify:

```text
current quote / structure close labels
provisional dynamic bands when materially useful
no provisional-as-authoritative leakage
no message clutter
SNDK/WULF fail-closed remains safe
```

Set:

```text
NATURAL_PROVISIONAL_BOLLINGER_LAYER =
PASS / FAIL

NATURAL_PRICE_LABEL_CLARITY =
PASS / FAIL
```

---

# 36. Required reports

Create:

1. `docs/reports/20260828-provisional-bollinger-policy.md`
2. `docs/reports/20260828-partial-bar-validation-contract.md`
3. `docs/reports/20260828-current-vs-structure-price-label-policy.md`
4. `docs/reports/20260828-mu-provisional-bollinger-control.md`
5. `docs/reports/20260828-skhynix-provisional-bollinger-control.md`
6. `docs/reports/20260828-googl-provisional-semantic-control.md`
7. `docs/reports/20260828-sndk-wulf-no-bypass-control.md`
8. `docs/reports/20260828-us-provisional-bollinger-replay.md`
9. `docs/reports/20260828-kr7-provisional-bollinger-replay.md`
10. `docs/reports/20260828-provisional-bollinger-ai-fallback-parity.md`
11. `docs/reports/20260828-provisional-bollinger-test-messages.md`
12. `docs/reports/20260828-price-label-test-messages.md`
13. `docs/reports/20260828-provisional-bollinger-operating-promotion.md`
14. `docs/reports/20260828-provisional-bollinger-natural-proof-status.md`
15. `docs/reports/20260828-provisional-bollinger-readiness.md`
16. `docs/reports/20260828-provisional-bollinger-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-us-provisional-bollinger-replay.json
docs/reports/20260828-kr7-provisional-bollinger-replay.json
docs/reports/20260828-provisional-bollinger-readiness.json
```

---

# 37. Required gates

Set exactly:

```text
PROVISIONAL_BOLLINGER_LAYER =
PASS / FAIL

MALFORMED_PARTIAL_BAR_USED_FOR_PROVISIONAL_BOLLINGER =
0 / NONZERO

PROVISIONAL_BOLLINGER_AS_NEAR_SR =
0 / NONZERO

PROVISIONAL_BOLLINGER_AS_MAJOR_SR =
0 / NONZERO

PROVISIONAL_BOLLINGER_AS_STORED_RULE =
0 / NONZERO

PROVISIONAL_BOLLINGER_AS_FIB_ANCHOR =
0 / NONZERO

PROVISIONAL_BOLLINGER_AS_WAVE_ANCHOR =
0 / NONZERO

PROVISIONAL_BOLLINGER_LINE_COUNT_MAX =
1 / OTHER

DUPLICATE_PROVISIONAL_RANGE_VISIBLE =
0 / NONZERO

AI_CALCULATED_PROVISIONAL_BOLLINGER =
0 / NONZERO

AI_PROMOTED_PROVISIONAL_BOLLINGER =
0 / NONZERO

BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

MAJOR_SR_WITHOUT_PRICE_ANCHOR =
0 / NONZERO

GOOGL_424_AS_MAJOR_STRUCTURAL =
0 / NONZERO

AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL =
0 / NONZERO

STRUCTURE_BASIS_CLOSE_WITHOUT_SESSION =
0 / NONZERO

DUPLICATE_IDENTICAL_PRICE_LINES =
0 / NONZERO

INFERRED_QUOTE_SESSION_LABEL_WITHOUT_EVIDENCE =
0 / NONZERO

SNDK_PROVISIONAL_LAYER_BYPASS =
0 / NONZERO

WULF_PROVISIONAL_LAYER_BYPASS =
0 / NONZERO

US_CURRENT_MONITORED_REPLAY =
PASS / FAIL

KR7_CONTROL_REPLAY =
PASS / FAIL

AI_FALLBACK_CURRENT_PRICE_PARITY =
PASS / FAIL

AI_FALLBACK_STRUCTURE_BASIS_PRICE_PARITY =
PASS / FAIL

AI_FALLBACK_PROVISIONAL_BOLLINGER_ELIGIBILITY_PARITY =
PASS / FAIL

AI_FALLBACK_PROVISIONAL_BOLLINGER_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_PROVISIONAL_BOLLINGER_LABEL_PARITY =
PASS / FAIL

TEST_MESSAGE_COUNT =
...

TEST_PRICE_LABEL_QUALITY =
PASS / FAIL

TEST_PROVISIONAL_BOLLINGER_MESSAGE_QUALITY =
PASS / FAIL

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

POST_DEPLOY_PROVISIONAL_BOLLINGER =
PASS / NOT_RUN / FAIL

POST_DEPLOY_PRICE_LABEL_CLARITY =
PASS / NOT_RUN / FAIL

POST_DEPLOY_MAJOR_SR_REALITY_GATE =
PASS / NOT_RUN / FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

PROVISIONAL_BOLLINGER_ROLLOUT =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_PROVISIONAL_BOLLINGER_LAYER =
PENDING / PASS / FAIL

NATURAL_PRICE_LABEL_CLARITY =
PENDING / PASS / FAIL
```

---

# 38. Pre-deploy PASS rule

Require:

```text
valid partial-bar contract
provisional line clearly non-authoritative
MU-style expansion information recoverable when valid/material
current-vs-structure price labels unambiguous
Major S/R reality gate preserved
SNDK/WULF cannot bypass safety
US full universe PASS
KR7 PASS
test sink PASS
P0/P1 = 0/0
```

---

# 39. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

TRACK_D_BRANCH = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

PROVISIONAL_BOLLINGER_LAYER = ...

MU_CURRENT_PRICE = ...
MU_STRUCTURE_BASIS_CLOSE = ...
MU_STRUCTURE_BASIS_SESSION = ...
MU_COMPLETED_BOLLINGER = ...
MU_PROVISIONAL_BOLLINGER = ...
MU_PROVISIONAL_TIMEFRAME = ...

SKHYNIX_CURRENT_PRICE = ...
SKHYNIX_STRUCTURE_BASIS_CLOSE = ...
SKHYNIX_COMPLETED_BOLLINGER = ...
SKHYNIX_PROVISIONAL_BOLLINGER = ...

GOOGL_424_AS_MAJOR_STRUCTURAL = 0

SNDK_PROVISIONAL_LAYER_BYPASS = 0
WULF_PROVISIONAL_LAYER_BYPASS = 0

AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL = 0
DUPLICATE_IDENTICAL_PRICE_LINES = 0
INFERRED_QUOTE_SESSION_LABEL_WITHOUT_EVIDENCE = 0

US_CURRENT_MONITORED_REPLAY = ...
KR7_CONTROL_REPLAY = ...

AI_FALLBACK_CURRENT_PRICE_PARITY = ...
AI_FALLBACK_STRUCTURE_BASIS_PRICE_PARITY = ...
AI_FALLBACK_PROVISIONAL_BOLLINGER_ELIGIBILITY_PARITY = ...
AI_FALLBACK_PROVISIONAL_BOLLINGER_NUMERIC_PARITY = ...
AI_FALLBACK_PROVISIONAL_BOLLINGER_LABEL_PARITY = ...

TEST_MESSAGE_COUNT = ...
TEST_PRICE_LABEL_QUALITY = ...
TEST_PROVISIONAL_BOLLINGER_MESSAGE_QUALITY = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0

POST_DEPLOY_PROVISIONAL_BOLLINGER = ...
POST_DEPLOY_PRICE_LABEL_CLARITY = ...
POST_DEPLOY_MAJOR_SR_REALITY_GATE = ...

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...
OHLCV_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

PROVISIONAL_BOLLINGER_ROLLOUT =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_PROVISIONAL_BOLLINGER_LAYER =
PENDING /
PASS /
FAIL

NATURAL_PRICE_LABEL_CLARITY =
PENDING /
PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_STOCK_MESSAGES /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 40. Mandatory completion ZIP

Create:

`20260828-price-structure-provisional-bollinger-expansion-and-price-label-clarity-bundle.zip`

Include:

```text
exact instruction
provisional Bollinger policy
partial-bar validity contract
price-label policy
MU / SK hynix / GOOGL / SNDK-WULF controls
US full-universe replay
KR7 replay
AI/fallback parity
exact test messages
message-quality review
operating promotion
post-deploy smoke
natural-proof status
readiness JSON
test/CI summary
artifact index
```

Exclude secrets, Telegram sink IDs, tokens, auth headers, account identifiers, hidden chain-of-thought.

Compute SHA-256.

---

# 41. Final principle

Keep the hierarchy explicit:

```text
실제 가격 구조
> 완료봉 기반 동적 Bollinger
> 진행 중 봉 기반 잠정 Bollinger
```

The provisional layer is valuable precisely because it is forward-looking.

It is safe only when the message clearly tells the user that the band is still moving until the bar closes.

And when `현재가` differs from the completed-session price used for technical structure,
show both prices with explicit ownership instead of making the user guess why two numbers appear.
