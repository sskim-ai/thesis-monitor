# thesis-monitor — US Night-Futures Canonicalization + Current-Time E2E + Next-Natural Live Proof
## Fix raw summary mismatch, collect data as of execution time, send real test messages, inspect full US market + all monitored stock Price Structure, deploy, then observe next natural run
## No production-recipient test sends; no manual production scheduler

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `US_NIGHT_FUTURES_CANONICALIZATION_CURRENT_TIME_E2E_AND_LIVE_PROOF`
- Task class: `BOUNDED_REPAIR + CONTROLLED_TEST_E2E + DEPLOY + READ_ONLY_NATURAL_PROOF`
- Current known US full-message state: `DEPLOYED_AWAITING_NATURAL_PROOF`
- Current known US Price Structure state: `ENABLED_AWAITING_NATURAL_PROOF`
- Production Assist: preserve `OFF`
- KR market / KR Price Structure: preserve current state
- Production-recipient test send: `0`
- Manual production scheduler execution: `0`
- DB / official assessment mutation: `0`
- Historical archive rewrite: `0`

### Latest known main / operating entering this task

Latest explicitly reported operating lineage:

`a3050b19e3b983fe71ae3f68f400fc2e9a8d66aa`

This includes the US macro-quality repair.

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve actual latest safe `origin/main`
4. resolve actual operating SHA
5. if a newer safe descendant exists, use it
6. record exact lineage
7. preserve current runtime feature states

---

# 1. Objective

Complete this sequence:

```text
A. Night-futures canonicalization repair
   raw/legacy market_summary night-futures values
   → cannot bypass canonical night_futures gate

B. Current-time US market E2E test
   as of actual execution time
   → latest completed US session
   → SPY/QQQ/IWM/SOXX/RSP
   → market internals
   → sector dispersion
   → Korean night futures
   → macro temporal context
   → exact full Telegram test message

C. Current-time US/foreign stock E2E test
   → every current monitored US/foreign stock
   → current Price Structure
   → support/resistance
   → safe Fib only if eligible
   → exact Telegram test messages

D. Deploy only after A/B/C PASS
   → preserve US Price Structure ON
   → preserve KR states
   → next natural US morning + stock-monitoring messages
   → read-only live proof
```

The user wants to review the whole message product before relying on tomorrow's natural messages.

---

# 2. Work split

This task MUST be splittable:

```text
Track A
night-futures canonicalization

Track B
current-time US full market message test

Track C
current-time all monitored US/foreign stock Price Structure test

Track D
deploy + next natural live proof
```

Tracks B and C start after Track A is on the same latest safe main.

Recommended branches:

```text
codex/us-night-futures-summary-canonicalization
codex/us-current-time-market-e2e
codex/us-current-time-stock-price-structure-e2e
codex/us-deploy-and-natural-proof
```

---

# 3. Known night-futures defect to close

A previous current-time review found a mismatch:

```text
canonical night_futures gate:
expected latest overnight session = current KST overnight session
ready_products = []
or facts classified stale/not-ready

but

market_summary.items:
contained KOSPI200 / KOSDAQ150 night-futures numeric claims
that did not match the canonical gated observation/session
```

This creates a bypass risk:

```text
raw summary item
→ user-facing candidate
```

despite:

```text
canonical night_futures gate
→ stale / not ready / unavailable
```

The final user-facing source of truth must be the canonical gate.

---

# 4. Canonical night-futures identities

Audit and reuse existing canonical facts if still supported.

Known canonical identities include:

```text
market:night_futures:1
→ KOSPI200 야간선물
→ fields.change_pct
→ semantic_type = futures_return_pct

market:night_futures:2
→ KOSDAQ150 야간선물
→ fields.change_pct
→ semantic_type = futures_return_pct
```

Do not create duplicate numeric identities for the same economic facts.

---

# 5. Track A — one canonical ownership path

Required ownership:

```text
night-futures acquisition
→ canonical normalized facts
→ expected-session resolver
→ night_futures_gate
→ market-summary projection
→ shared market plan
→ full-message renderer
```

`market_summary.items` must not independently own night-futures numbers.

Hard:

```text
NIGHT_FUTURES_RAW_SUMMARY_BYPASS = 0
```

---

# 6. Summary-item canonicalization

A night-futures `market_summary.items` entry may exist only when the canonical gate says the product is safe for the current overnight context.

Required parity:

```text
summary fact_id
summary field_path
summary value
summary session
summary state
=
canonical gated fact
```

Hard:

```text
NIGHT_FUTURES_SUMMARY_CANONICAL_PARITY = PASS
SUMMARY_NIGHT_FUTURES_VALUE_CONFLICT = 0
SUMMARY_NIGHT_FUTURES_SESSION_CONFLICT = 0
```

---

# 7. Stale / not-ready / unavailable behavior

If canonical state is:

```text
STALE
PUBLICATION_PENDING
SOURCE_UNAVAILABLE
NOT_READY
AI_REVIEW_HOLD
```

or repository-native equivalent that is not current-directional:

then:

```text
no user-facing night-futures return
no market_summary night-futures numeric item
no stale carry-forward
```

Hard:

```text
STALE_NIGHT_FUTURES_SUMMARY_ITEM = 0
PRIOR_NIGHT_FUTURES_AS_CURRENT = 0
```

---

# 8. Current directional behavior

Only when canonical gate proves safe current overnight directional data:

render:

```text
🌙 한국 야간선물
• KOSPI200 야간선물 +x.xx%
• KOSDAQ150 야간선물 +x.xx%
```

If only one product is current-safe:

show only one.

If none:

omit the section entirely.

Hard:

```text
EMPTY_NIGHT_FUTURES_SECTION = 0
```

---

# 9. Session mapping

Resolve the relevant Korean overnight session from execution time and the upcoming Korean regular session.

Do not assume:

```text
night_futures_session == US_target_session
```

Record:

```text
execution_time_kst
latest_completed_us_session
upcoming_kr_regular_session
expected_night_futures_session
actual_night_futures_session
```

Hard:

```text
NIGHT_FUTURES_SESSION_MAPPING = PASS
WRONG_NIGHT_FUTURES_SESSION_VISIBLE = 0
```

---

# 10. Track A regression fixtures

Required negative fixture:

```text
canonical gate says stale/not-ready
summary contains night-futures numbers
→ repaired path must remove/reject summary numeric
```

Required positive fixture:

use the most recent REAL historical canonical observation where:

```text
KOSPI200 and/or KOSDAQ150
was current-directional for its own historical overnight session
```

Do not fabricate values.

Verify that the full message correctly displays the historical real fixture under `🌙 한국 야간선물`.

If no real positive fixture exists in retained evidence:

```text
NIGHT_FUTURES_POSITIVE_FIXTURE = NOT_OBSERVED
```

Do not synthesize one.

---

# 11. Track B — current-time test clock

Run the test using the actual execution time.

Record:

```text
EXECUTION_TIME_KST
LATEST_COMPLETED_US_SESSION
EXPECTED_NIGHT_FUTURES_SESSION
UPCOMING_KR_REGULAR_SESSION
```

Do not hard-code 08:00 if the test runs later.

The user's intent is:

```text
"what would the US morning message look like right now, using only data that would be valid at this point?"
```

---

# 12. Current-time US market data

Collect:

```text
SPY
QQQ
IWM
SOXX
RSP
```

with:

```text
current completed-session return
observation date
state
source
provenance
```

Hard:

```text
CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = PASS
```

---

# 13. Required index numeric block

The current-time test message must explicitly show every safely current return:

```text
📈 주요 지수
• SPY +x.xx%
• QQQ +x.xx%
• IWM +x.xx%
• SOXX +x.xx%
• RSP +x.xx%
```

Hard:

```text
SPY_RETURN_VISIBLE = PASS
QQQ_RETURN_VISIBLE = PASS
IWM_RETURN_VISIBLE = PASS
SOXX_RETURN_VISIBLE = PASS
RSP_RETURN_VISIBLE = PASS
```

unless a specific item is genuinely unavailable, which must be explicitly reported.

---

# 14. Current market internals

Collect and render:

```text
RSP participation/style interpretation
semiconductor relative behavior
strongest safe sector
weakest safe sector
selected sector numeric returns
```

Backend owns ranking and numerics.

Hard:

```text
AI_DERIVED_SECTOR_RANKING = 0
SELECTED_STRONG_SECTOR_RETURN_VISIBLE = PASS
SELECTED_WEAK_SECTOR_RETURN_VISIBLE = PASS
UNSUPPORTED_RSP_STYLE_INTERPRETATION = 0
```

---

# 15. Current-time night futures

Run the repaired canonical gate at actual test time.

Possible outcomes:

## Current safe
Render the section.

## Not ready / unavailable / stale
Omit the section.

The current-time test must reflect reality.

Do not force display merely because the user wants to inspect it.

Record:

```text
KOSPI200_NIGHT_FUTURES_STATE
KOSDAQ150_NIGHT_FUTURES_STATE
NIGHT_FUTURES_SECTION_VISIBLE
```

---

# 16. Positive display proof if current values unavailable

If the current-time test legitimately omits night futures:

also render a separate TEST-ONLY historical positive-control message from the real canonical fixture found in Track A.

The test fixture message must be clearly labeled:

```text
🧪 TEST FIXTURE · 야간선물 표시 검증
```

It must never be confused with current data.

Do not send a fixture to production.

This proves:

```text
when canonical current data exists,
the section renders correctly.
```

---

# 17. Macro temporal context

Audit:

```text
nominal 10Y
real 10Y
VIX
WTI
FX
DXY/liquidity if supported
```

Only:

```text
current
or
explicitly date-qualified specific prior/reference fact
```

may appear.

Generic neutral macro:

```text
omit section
```

Hard:

```text
GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE = 0
MALFORMED_ZERO_CHANGE_KOREAN = 0
STALE_MACRO_AS_CURRENT = 0
```

---

# 18. Current-time full market message

Target structure:

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY ...
• QQQ ...
• IWM ...
• SOXX ...
• RSP ...

🔎 시장 내부
• current-session interpretation
• RSP participation/style
• 업종 강세: ... +x.xx%
• 업종 약세: ... -x.xx%

🌙 한국 야간선물
• ...
(only when current-safe)

🌐 보조 시장환경
• ...
(only when material and temporally safe)

📌 다음 확인
• ...
```

---

# 19. Shared-plan / fallback parity

Generate:

```text
AI candidate
deterministic fallback candidate
```

Hard:

```text
AI_FALLBACK_INDEX_BLOCK_PARITY = PASS
AI_FALLBACK_SECTOR_NUMERIC_PARITY = PASS
AI_FALLBACK_NIGHT_FUTURES_PARITY = PASS
AI_FALLBACK_SECTION_ORDER_PARITY = PASS
AI_FALLBACK_TEMPORAL_PARITY = PASS
```

---

# 20. Market test-sink send

Use the existing dedicated non-production test sink.

Send exactly one CURRENT-TIME market message.

If a historical night-futures positive fixture is required:

send at most one additional TEST-FIXTURE message.

Therefore:

```text
TEST_CURRENT_MARKET_MESSAGE_COUNT = 1
TEST_NIGHT_FUTURES_FIXTURE_MESSAGE_COUNT = 0 or 1
```

Hard:

```text
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
```

---

# 21. Exact payload + actual Telegram review

For every test message compare:

```text
rendered
outbound
received
```

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
```

Human-review:

```text
major-index numbers
market-internal interpretation
sector numbers
night-futures section / safe omission
macro section
next check
line breaks
message length
```

Hard:

```text
TEST_MARKET_MESSAGE_QUALITY = PASS
TEST_FORMATTING_BROKEN = 0
TEST_MESSAGE_TRUNCATED = 0
```

---

# 22. Track C — current-time monitored US/foreign stock universe

Use ALL current monitored US/foreign stocks.

Previously monitored controls included:

```text
CORZ
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

Use actual current list and report diffs.

---

# 23. Per-stock target session / basis

For each ticker record:

```text
target completed session
security basis
ADR/ordinary basis if applicable
currency
price_as_of
OHLCV basis
```

Hard:

```text
SECURITY_BASIS_CONFLICT = 0
CURRENCY_MISMATCH = 0
WRONG_SESSION_DATA = 0
```

---

# 24. Price Structure coverage

Use existing canonical targets:

```text
Daily 1200
Weekly 600
Monthly 300
```

Preserve provider-limit degradation rules where applicable.

No synthetic history.

Hard:

```text
SYNTHETIC_DAILY_BARS = 0
PROVIDER_LIMIT_MISREPORTED_AS_FULL = 0
```

---

# 25. Per-stock Price Structure

For every ticker audit:

```text
eligibility

near support
near resistance

major structural support
major structural resistance

Fib/SR if eligible

stored monitoring price-rule presence
```

Record provenance for every user-visible numeric.

---

# 26. Price Structure renderer rules

```text
ELIGIBLE
→ SR + safe Fib/SR

ELIGIBLE_SR_ONLY
→ SR only

OMIT / BLOCKED
→ no Price Structure section
```

Hard:

```text
LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
UNSTABLE_FIB_EXPOSED = 0
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 27. Stock AI/fallback parity

For EVERY current monitored US/foreign ticker:

```text
AI candidate
fallback candidate
```

Hard:

```text
AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY = PASS
AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY = PASS
AI_FALLBACK_STORED_RULE_OWNERSHIP_PARITY = PASS
AI_FALLBACK_FIB_VISIBILITY_PARITY = PASS
```

---

# 28. Stock test-sink send

Send one test message for every current monitored US/foreign stock.

If count is N:

```text
TEST_STOCK_MESSAGE_COUNT = N
```

No sampling.

Hard:

```text
TEST_STOCK_FAIL_COUNT = 0
TEST_STOCK_DUPLICATE = 0
TEST_STOCK_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
```

---

# 29. Exact stock-message review

For every received stock message verify:

```text
company header
business / investment-logic text intact
current Price Structure visible only if eligible
support/resistance readable
major structure readable
Fib only if safe
stored rules separately labeled
no stale legacy technical prose
no target/stop
no truncation
```

Hard:

```text
TEST_STOCK_MESSAGE_QUALITY = PASS
```

---

# 30. Current-time combined review artifact

Create one summary table for the operator:

```text
US MARKET
- target session
- index returns
- RSP interpretation
- strongest/weakest sector
- night-futures states/values
- macro facts used
- exact message result

US STOCKS
- ticker
- eligibility
- near support
- near resistance
- major support
- major resistance
- Fib visible?
- stored rule?
- exact test-message PASS?
```

This table is the primary human review artifact before deployment.

---

# 31. Track D — deployment gate

Do not deploy Track A repair until:

```text
night-futures canonicalization PASS
current-time market message PASS
current-time all-stock Price Structure PASS
test-sink exact payload PASS
P0 = 0
material P1 = 0
```

---

# 32. Deployment

Deploy the smallest canonicalization repair through the normal operating path.

Preserve:

```text
US full market message current layout
US Price Structure = ON
KR market / KR Price Structure = unchanged
Production Assist = OFF
```

No new feature flag.

---

# 33. Post-deploy smoke

Read-only smoke:

```text
US market full message
night-futures summary canonical parity
all monitored US/foreign Price Structure
KR parity
```

Hard:

```text
POST_DEPLOY_MARKET = PASS
POST_DEPLOY_NIGHT_FUTURES_CANONICAL_PARITY = PASS
POST_DEPLOY_ALL_US_STOCKS = PASS
POST_DEPLOY_KR_RUNTIME_DIFF = 0
```

---

# 34. Tomorrow / next-natural observation

Do not manually trigger.

Observe the next natural:

```text
US morning market digest
US/foreign monitored-stock message cycle
```

Record exact run/task identities, packets, routes, deliveries, receipts, and messages.

---

# 35. Natural market proof

Verify:

```text
major-index numeric block
current market internals
RSP interpretation
sector strong/weak numerics
night futures current-safe display OR safe omission
macro temporal safety
exactly once
```

Set:

```text
NATURAL_US_MARKET_FULL_MESSAGE =
PASS / FAIL
```

---

# 36. Natural night-futures proof

Separate from overall market proof:

```text
NATURAL_NIGHT_FUTURES_DISPLAY =
PASS
SAFE_OMISSION
PENDING
FAIL
```

Rules:

```text
current-safe facts exist and displayed → PASS
no current-safe facts, section omitted → SAFE_OMISSION
current-safe facts not yet naturally observed → PENDING
stale/wrong-session displayed → FAIL
```

Do not fail the entire market message solely because current night-futures data is legitimately unavailable.

---

# 37. Natural stock Price Structure proof

Verify naturally emitted monitored-stock messages:

```text
correct target session
correct security/currency basis
Price Structure per eligibility
near/major semantics
safe Fib only
stored rules separate
no target/stop
exactly once
```

Set:

`NATURAL_US_PRICE_STRUCTURE = PASS / FAIL`

---

# 38. Final live state

Only after:

```text
NATURAL_US_MARKET_FULL_MESSAGE = PASS
NATURAL_US_PRICE_STRUCTURE = PASS
P0 = 0
material P1 = 0
```

set:

```text
US_ROLLOUT = LIVE_PASS
```

Night-futures display may remain `SAFE_OMISSION/PENDING` if the source has not produced a current-safe natural observation.

---

# 39. Stop conditions

STOP / DO NOT DEPLOY if:

```text
summary night-futures bypass remains
summary/canonical value conflict
summary/canonical session conflict
stale night futures visible
market test message unsafe
any monitored stock Price Structure material failure
security/currency mismatch
remote zone labeled near
unstable Fib visible
test delivery reaches production recipient
duplicate/orphan
new P0
new material P1
```

---

# 40. Full regression

Required:

```text
night-futures canonicalization tests
night-futures positive/negative fixtures
US full-message tests
shared market-plan tests
macro-quality exact-payload tests
all monitored US/foreign Price Structure replay
all monitored stock test messages
security/currency basis tests
SR proximity tests
Fib family safety
legacy technical suppression

full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
OHLCV health
```

No Public Action change expected.

---

# 41. Required architecture docs

Create/update:

```text
docs/architecture/KOREA_NIGHT_FUTURES_IN_US_MORNING.md
docs/architecture/US_MORNING_MESSAGE_LAYOUT.md
docs/architecture/US_PRICE_STRUCTURE_SELECTIVE_ROLLOUT.md
docs/architecture/EXACT_PAYLOAD_MESSAGE_QUALITY_VALIDATION.md
```

---

# 42. Required reports

Create:

1. `docs/reports/20260828-us-night-futures-summary-root-cause.md`
2. `docs/reports/20260828-us-night-futures-summary-canonicalization.md`
3. `docs/reports/20260828-us-night-futures-session-parity.md`
4. `docs/reports/20260828-us-night-futures-positive-fixture.md`
5. `docs/reports/20260828-us-current-time-clock-and-session.md`
6. `docs/reports/20260828-us-current-time-market-data.md`
7. `docs/reports/20260828-us-current-time-full-market-message.md`
8. `docs/reports/20260828-us-current-time-market-test-delivery.md`
9. `docs/reports/20260828-us-current-time-stock-universe.md`
10. `docs/reports/20260828-us-current-time-price-structure-per-ticker.md`
11. `docs/reports/20260828-us-current-time-stock-test-delivery.md`
12. `docs/reports/20260828-us-current-time-combined-review.md`
13. `docs/reports/20260828-us-current-time-ai-fallback-parity.md`
14. `docs/reports/20260828-us-current-time-message-quality.md`
15. `docs/reports/20260828-us-current-time-safety-parity.md`
16. `docs/reports/20260828-us-deployment.md`
17. `docs/reports/20260828-us-post-deploy-smoke.md`
18. `docs/reports/20260828-us-next-natural-proof-status.md`
19. `docs/reports/20260828-us-current-time-readiness.md`
20. `docs/reports/20260828-us-current-time-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-us-current-time-market-data.json
docs/reports/20260828-us-current-time-price-structure-per-ticker.json
docs/reports/20260828-us-current-time-readiness.json
docs/reports/20260828-us-next-natural-proof-status.json
```

---

# 43. Required gates

Set exactly:

```text
NIGHT_FUTURES_SUMMARY_CANONICALIZATION =
PASS / FAIL

NIGHT_FUTURES_RAW_SUMMARY_BYPASS =
0 / NONZERO

NIGHT_FUTURES_SUMMARY_CANONICAL_PARITY =
PASS / FAIL

SUMMARY_NIGHT_FUTURES_VALUE_CONFLICT =
0 / NONZERO

SUMMARY_NIGHT_FUTURES_SESSION_CONFLICT =
0 / NONZERO

STALE_NIGHT_FUTURES_SUMMARY_ITEM =
0 / NONZERO

NIGHT_FUTURES_SESSION_MAPPING =
PASS / FAIL

NIGHT_FUTURES_POSITIVE_FIXTURE =
PASS / NOT_OBSERVED / FAIL

EXECUTION_TIME_KST =
...

LATEST_COMPLETED_US_SESSION =
...

UPCOMING_KR_REGULAR_SESSION =
...

EXPECTED_NIGHT_FUTURES_SESSION =
...

KOSPI200_NIGHT_FUTURES_STATE =
...

KOSDAQ150_NIGHT_FUTURES_STATE =
...

NIGHT_FUTURES_SECTION_VISIBLE =
YES / NO

CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED =
PASS / FAIL

SPY_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

QQQ_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

IWM_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

SOXX_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

RSP_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

SELECTED_STRONG_SECTOR_RETURN_VISIBLE =
PASS / NOT_SELECTED / FAIL

SELECTED_WEAK_SECTOR_RETURN_VISIBLE =
PASS / NOT_SELECTED / FAIL

GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE =
0 / NONZERO

MALFORMED_ZERO_CHANGE_KOREAN =
0 / NONZERO

AI_FALLBACK_INDEX_BLOCK_PARITY =
PASS / FAIL

AI_FALLBACK_SECTOR_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_NIGHT_FUTURES_PARITY =
PASS / FAIL

AI_FALLBACK_SECTION_ORDER_PARITY =
PASS / FAIL

TEST_CURRENT_MARKET_MESSAGE_COUNT =
1 / OTHER

TEST_NIGHT_FUTURES_FIXTURE_MESSAGE_COUNT =
0 / 1 / OTHER

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_MARKET_MESSAGE_QUALITY =
PASS / FAIL

TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT =
0 / NONZERO

CURRENT_US_MONITORED_STOCK_COUNT =
...

ALL_US_STOCK_PRICE_STRUCTURE_REPLAY =
PASS / FAIL

TEST_STOCK_MESSAGE_COUNT =
...

TEST_STOCK_FAIL_COUNT =
0 / NONZERO

TEST_STOCK_MESSAGE_QUALITY =
PASS / FAIL

SECURITY_BASIS_CONFLICT =
0 / NONZERO

CURRENCY_MISMATCH =
0 / NONZERO

LONG_HORIZON_RENDERED_AS_NEAR =
0 / NONZERO

REMOTE_ZONE_PROMOTED_AS_NEAR_FILL =
0 / NONZERO

UNSTABLE_FIB_EXPOSED =
0 / NONZERO

CURRENT_SR_RENDERED_AS_STORED_RULE =
0 / NONZERO

STORED_RULE_RENDERED_AS_CURRENT_SR =
0 / NONZERO

UNSUPPORTED_TARGET_PRICE =
0 / NONZERO

UNSUPPORTED_STOP_PRICE =
0 / NONZERO

DEPLOYMENT =
PASS / NOT_RUN / FAIL

POST_DEPLOY_MARKET =
PASS / NOT_RUN / FAIL

POST_DEPLOY_NIGHT_FUTURES_CANONICAL_PARITY =
PASS / NOT_RUN / FAIL

POST_DEPLOY_ALL_US_STOCKS =
PASS / NOT_RUN / FAIL

POST_DEPLOY_KR_RUNTIME_DIFF =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

US_CURRENT_TIME_E2E =
TEST_PASS_READY_TO_DEPLOY /
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL

NATURAL_US_MARKET_FULL_MESSAGE =
PENDING / PASS / FAIL

NATURAL_NIGHT_FUTURES_DISPLAY =
PENDING / PASS / SAFE_OMISSION / FAIL

NATURAL_US_PRICE_STRUCTURE =
PENDING / PASS / FAIL

US_ROLLOUT =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL
```

---

# 44. Pre-deploy PASS rule

Require:

```text
night-futures canonicalization PASS
no summary bypass/conflict
current-time market full message PASS
market test-sink exact payload PASS
all monitored US/foreign stock Price Structure replay PASS
all monitored stock test messages PASS
security/currency basis safe
SR/Fib/stored-rule safety PASS
P0 = 0
material P1 = 0
```

Then:

`US_CURRENT_TIME_E2E = TEST_PASS_READY_TO_DEPLOY`

---

# 45. Deployment state

After deployment + smoke:

```text
US_CURRENT_TIME_E2E =
DEPLOYED_AWAITING_NATURAL_PROOF

US_ROLLOUT =
DEPLOYED_AWAITING_NATURAL_PROOF
```

Do not manually trigger natural production.

---

# 46. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_RESULT = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

TRACK_D_BRANCH = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

EXECUTION_TIME_KST = ...
LATEST_COMPLETED_US_SESSION = ...
UPCOMING_KR_REGULAR_SESSION = ...
EXPECTED_NIGHT_FUTURES_SESSION = ...

NIGHT_FUTURES_SUMMARY_CANONICALIZATION = ...
NIGHT_FUTURES_RAW_SUMMARY_BYPASS = 0
NIGHT_FUTURES_SUMMARY_CANONICAL_PARITY = ...
SUMMARY_NIGHT_FUTURES_VALUE_CONFLICT = 0
SUMMARY_NIGHT_FUTURES_SESSION_CONFLICT = 0
STALE_NIGHT_FUTURES_SUMMARY_ITEM = 0

KOSPI200_NIGHT_FUTURES = ...
KOSPI200_NIGHT_FUTURES_STATE = ...
KOSPI200_NIGHT_FUTURES_SESSION = ...

KOSDAQ150_NIGHT_FUTURES = ...
KOSDAQ150_NIGHT_FUTURES_STATE = ...
KOSDAQ150_NIGHT_FUTURES_SESSION = ...

NIGHT_FUTURES_POSITIVE_FIXTURE = ...

SPY = ...
QQQ = ...
IWM = ...
SOXX = ...
RSP = ...

SECTOR_STRONGEST = ...
SECTOR_WEAKEST = ...

EXACT_CURRENT_TIME_MARKET_MESSAGE =
...

TEST_CURRENT_MARKET_MESSAGE_COUNT = 1
TEST_NIGHT_FUTURES_FIXTURE_MESSAGE_COUNT = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_MARKET_MESSAGE_QUALITY = ...

CURRENT_US_MONITORED_STOCK_COUNT = ...
US_STOCK_TICKERS = ...

PER_TICKER_PRICE_STRUCTURE_AUDIT =
...

TEST_STOCK_MESSAGE_COUNT = ...
TEST_STOCK_FAIL_COUNT = 0
TEST_STOCK_MESSAGE_QUALITY = ...

SECURITY_BASIS_CONFLICT = 0
CURRENCY_MISMATCH = 0
LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
UNSTABLE_FIB_EXPOSED = 0
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

DEPLOYMENT = ...
POST_DEPLOY_MARKET = ...
POST_DEPLOY_NIGHT_FUTURES_CANONICAL_PARITY = ...
POST_DEPLOY_ALL_US_STOCKS = ...
POST_DEPLOY_KR_RUNTIME_DIFF = 0

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

US_CURRENT_TIME_E2E =
TEST_PASS_READY_TO_DEPLOY /
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL

NATURAL_US_MARKET_FULL_MESSAGE =
PENDING /
PASS /
FAIL

NATURAL_NIGHT_FUTURES_DISPLAY =
PENDING /
PASS /
SAFE_OMISSION /
FAIL

NATURAL_US_PRICE_STRUCTURE =
PENDING /
PASS /
FAIL

US_ROLLOUT =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_MESSAGES /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 47. Mandatory completion ZIP

Create:

`20260828-us-night-futures-canonicalization-current-time-e2e-and-live-proof-bundle.zip`

Include:

```text
exact master instruction
all track instructions
night-futures root cause/canonicalization
night-futures session mapping
real positive fixture if available
current-time clock/session report
current-time market data
exact current-time market test message
market test receipt
full monitored stock universe
per-ticker Price Structure audit
all stock test messages / receipts
combined operator review
AI/fallback parity
message quality
safety parity
deployment
post-deploy smoke
next-natural proof status
readiness JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
raw sink IDs
auth headers
tokens
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 48. Final principle

For the current-time test:

```text
use only facts that are valid now.
```

For night futures:

```text
canonical gate owns both visibility and summary projection.
```

For US stocks:

```text
every monitored name must show only verified structural prices.
```

And for tomorrow:

```text
do not manually trigger anything.
Observe the next natural US market and stock messages exactly as the user will receive them.
```
