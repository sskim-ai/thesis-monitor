# thesis-monitor — US Price Structure v3 Selective Pre-Enablement
## Full monitored US/foreign universe replay → dedicated test sink → US-only bounded enablement → natural proof
## Run after / alongside the US full-market-message integration sequence
## KR behavior remains unchanged

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `US_PRICE_STRUCTURE_SELECTIVE_PREENABLEMENT`
- Task class: `CONTROLLED_US_ONLY_PRICE_STRUCTURE_ROLLOUT`
- Scope: current monitored US/foreign stock universe only
- US Price Structure entering state: `OFF`
- KR Price Structure: preserve current state
- KR market TOP3: preserve current state
- Production Assist: preserve `OFF`
- Manual production scheduler: `0`
- Production-recipient test send: `0`
- DB / official assessment mutation: `0`

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve latest safe `origin/main`
4. resolve current operating SHA
5. record the state/result of `US_MORNING_FULL_MESSAGE_INTEGRATION_AND_ITERATIVE_VALIDATION`
6. do not enable US Price Structure until all Track A/B gates pass

---

# 1. Objective

Enable the already-built Price Structure v3 selectively for current monitored US/foreign stock messages.

User-facing behavior:

```text
ELIGIBLE
→ 가까운 지지
→ 가까운 저항
→ 주요 구조 지지/저항 when available
→ Fib/SR 겹침 only when family-stable/material/safe

ELIGIBLE_SR_ONLY
→ deterministic SR only
→ no Fib line

OMIT_PRICE_STRUCTURE / BLOCKED
→ no current Price Structure section
→ rest of stock message still renders
```

Keep:

```text
📐 현재 가격 구조
```

separate from:

```text
🧭 기존 등록 가격 규칙
```

---

# 2. Current monitored universe

Use the actual monitored US/foreign universe at execution time.

Previous regression controls included:

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

Do not hard-code this as permanent.

If current universe differs:

```text
report added tickers
report removed tickers
test ALL currently monitored US/foreign names
```

---

# 3. Work split

```text
Track A
current-data full-universe Price Structure replay

Track B
dedicated test-sink full-universe stock-message validation

Track C
US-only operating enablement

Track D
next natural US stock-message proof
```

Recommended branches:

```text
codex/us-price-structure-current-replay
codex/us-price-structure-full-universe-test
codex/us-only-price-structure-enablement
codex/us-price-structure-natural-proof
```

---

# 4. Track A — target session resolution

For each ticker resolve the latest completed safe session.

For ordinary US-listed securities, use the latest completed US regular session.

For foreign/ADR/security-basis cases:

preserve the canonical security basis and session basis used by the stock-monitoring message.

Never mix:

```text
US ADR price
with
ordinary-share technical history
```

without an explicitly verified ratio/basis contract.

Hard:

```text
WRONG_SESSION_DATA = 0
SECURITY_BASIS_CONFLICT = 0
CURRENCY_MISMATCH = 0
```

---

# 5. OHLCV coverage contract

Use the existing Price Structure canonical targets:

```text
Daily = 1200
Weekly = 600
Monthly = 300
```

Do not silently lower the canonical target.

If a provider has a verified hard cap:

use existing explicit:

```text
PARTIAL_SAFE / provider_limit
```

coverage semantics.

No synthetic bars.

Hard:

```text
SYNTHETIC_DAILY_BARS = 0
FAKE_DAILY_FROM_HIGHER_TF = 0
PROVIDER_LIMIT_MISREPORTED_AS_FULL = 0
```

---

# 6. Per-ticker coverage audit

For every monitored US/foreign ticker record:

```text
ticker
security type / ADR if applicable
currency
target session

daily requested / actual / completed / status
weekly requested / actual / completed / status
monthly requested / actual / completed / status

partial current bar state
corporate-action basis
```

Hard:

```text
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
LOOKAHEAD_LEAK = 0
```

---

# 7. Runtime eligibility

Use only the existing eligibility enum:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT_PRICE_STRUCTURE
BLOCKED
```

Do not create a second eligibility system.

Do not hard-code historic counts.

---

# 8. Deterministic SR base layer

Deterministic SR remains the required base.

For each ticker audit:

```text
nearest internal support
nearest internal resistance

user-visible near support
user-visible near resistance

major structural support
major structural resistance

source timeframe
source family
distance
proximity tier
active relevance
fact_ref / zone_id
```

---

# 9. User-visible proximity safety

Preserve:

```text
internal nearest available
≠ automatically user-visible "가까운"

LONG_HORIZON
≠ 가까운
```

Hard:

```text
LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
FABRICATED_SR_FILL = 0
```

---

# 10. Known regression controls

Use these as high-value regression controls when still monitored:

## MU

Previously remote old cross-zones were wrongly promotable.

Require current local structure to remain local/relevant.

## TSM

Previously remote zones were fixed; security/ADR basis must remain safe.

## SNDK

Current SR and old stored price rules can be far apart.
They must remain separately labeled.

## TSLA

Unstable Fib must remain omitted if still unstable.

## RXRX

Company header must remain intact; legacy technical detector false-positive must not recur.

## GOOGL / HUT / IBM / WULF

Use as additional SR / major-zone / Fib-overlap controls where current eligibility supports them.

No ticker-specific code exceptions.

---

# 11. Fib / wave policy

Fib is optional secondary structural evidence.

Only expose if:

```text
family-stable
user-visible eligible
material
safe
```

No-wave is a valid SR-only state.

Hard:

```text
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
FIB_FORCED_WHEN_NO_MEANINGFUL_OVERLAP = 0
```

---

# 12. Fib range preservation

If Fib/SR materially extends the structural band:

show the actual safe extended range.

Hard:

`MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED = 0`

---

# 13. Current structure vs stored rules

Preserve exact ownership:

```text
📐 현재 가격 구조
🧭 기존 등록 가격 규칙
```

Hard:

```text
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNLABELED_CURRENT_STORED_PRICE_CONFLICT = 0
```

---

# 14. No targets / stops

Do not transform SR into:

```text
target price
stop loss
entry
exit
```

Hard:

```text
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 15. Numeric ownership

All Price Structure numerics are backend-owned.

AI may select/interpret registered facts.

AI may not calculate them.

Hard:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
```

---

# 16. Legacy technical suppression safety

Preserve the completed renderer repair.

Hard:

```text
COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0
NON_TECHNICAL_PROSE_SUPPRESSED = 0
STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0
```

---

# 17. Track A full-universe artifact

Create one per-ticker table with:

```text
ticker
company
security basis
price/session/currency

coverage D/W/M
eligibility

near support
near resistance
major support
major resistance
Fib/SR if eligible

stored-rule presence
exact Price Structure renderer block
validator result
```

Hard:

`ALL_US_STOCK_PRICE_STRUCTURE_REPLAY = PASS`

---

# 18. AI / deterministic fallback parity

For every monitored ticker render both routes.

Required semantic parity:

```text
same eligibility
same authoritative Price Structure numerics
same current-vs-stored ownership
same Fib visibility decision
```

Exact prose may differ.

Hard:

```text
AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY = PASS
AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY = PASS
AI_FALLBACK_STORED_RULE_OWNERSHIP_PARITY = PASS
AI_FALLBACK_FIB_VISIBILITY_PARITY = PASS
```

---

# 19. Track B — dedicated test sink

Use the existing dedicated non-production test sink.

Do not send to production recipients.

Test ALL currently monitored US/foreign stock messages.

If current monitored count is N:

```text
TEST_STOCK_MESSAGE_COUNT = N
```

No silent sample reduction.

---

# 20. Test route selection

Use the route production would choose per stock:

```text
AI if eligible under current production policy
otherwise deterministic fallback
```

Record route per ticker.

Do not choose the prettier candidate.

---

# 21. Exactly-once test delivery

Send each test message exactly once to the dedicated test sink.

Hard:

```text
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_UNOWNED_RETRY = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 22. Exact payload proof

For every stock compare:

```text
rendered payload
outbound test payload
receipt-linked / received payload
```

Hard:

`TEST_EXACT_PAYLOAD_MATCH = PASS`

---

# 23. Actual received stock-message review

Human-review every received stock message.

Check:

```text
company header intact
investment-logic/business text intact
Price Structure appears only if eligible
near / major labels readable
Fib appears only if safe
stored rules separate
no target/stop
no stale legacy technical prose
no truncation
```

Hard:

```text
TEST_MESSAGE_QUALITY = PASS
TEST_MESSAGE_TRUNCATED = 0
TEST_FORMATTING_BROKEN = 0
```

---

# 24. Full-universe zero-tolerance rule

Do not enable if any monitored US/foreign stock has a material renderer/provenance/safety failure.

Required:

```text
TEST_STOCK_FAIL_COUNT = 0
```

A safe `OMIT_PRICE_STRUCTURE` / `BLOCKED` is not a failure.

---

# 25. Pre-enable gate

Track C cannot start unless:

```text
ALL_US_STOCK_PRICE_STRUCTURE_REPLAY = PASS
AI/fallback parity PASS
all full-universe test messages PASS
exact payload PASS
numeric provenance PASS
security/currency basis PASS
proximity safety PASS
Fib safety PASS
P0 = 0
material P1 = 0
```

Set:

`US_PRICE_STRUCTURE_PREENABLE = PASS`

---

# 26. Track C — operating promotion

Promote the latest validated code through the normal deployment path.

Before turning US Price Structure ON:

require:

```text
US Price Structure = OFF
KR Price Structure = unchanged
KR market TOP3 = unchanged
Production Assist = OFF
```

Run:

```text
API health
OHLCV health
feature-off parity
full-universe US stock smoke with feature OFF
```

Hard:

`FEATURE_OFF_PARITY = PASS`

---

# 27. US-only feature scope

Enable only:

```text
US/foreign monitored-stock Price Structure
```

Do not change KR state.

If a market-scoped gate exists:

use it.

If only a global Price Structure gate exists:

do NOT turn it globally on.

Add/use the smallest market-scoped guard that preserves the already-running KR behavior while allowing US monitored stocks.

Hard:

```text
US_PRICE_STRUCTURE_SCOPE = MONITORED_US_FOREIGN_ONLY
KR_RUNTIME_POLICY_DIFF = 0
```

---

# 28. Post-enable full-universe smoke

After US Price Structure ON:

render every monitored US/foreign stock read-only.

Hard:

```text
POST_ENABLE_ALL_US_STOCKS = PASS
POST_ENABLE_KR_PRICE_STRUCTURE_DIFF = 0
```

Recheck:

```text
proximity
Fib
stored rules
security basis
currency
headers
targets/stops
```

---

# 29. Market-message isolation

The US morning market digest remains a separate product.

Hard:

```text
US_MARKET_DIGEST_CODE_DIFF_FROM_PRICE_STRUCTURE = 0
US_MARKET_DIGEST_PRICE_STRUCTURE_LEAK = 0
```

Stock-level SR/Fib must not appear in the US morning market digest.

---

# 30. Track D — natural proof

Do not manually trigger.

Wait for the next natural US/foreign stock-monitoring message cycle.

Collect:

```text
run/task identity
target sessions
packets
routes
exact messages
deliveries / receipts
```

Verify across naturally emitted monitored stocks:

```text
eligibility
SR visibility
Fib visibility
stored-rule separation
numeric provenance
exactly once
```

---

# 31. Natural proof status

Before natural proof:

```text
US_PRICE_STRUCTURE =
ENABLED_AWAITING_NATURAL_PROOF
```

After natural PASS:

```text
US_PRICE_STRUCTURE = LIVE_PASS
```

---

# 32. Natural proof hard gates

```text
NATURAL_US_PRICE_STRUCTURE = PASS
NATURAL_US_UNSUPPORTED_NUMERIC = 0
NATURAL_US_REMOTE_NEAR_LABEL = 0
NATURAL_US_UNSTABLE_FIB = 0
NATURAL_US_CURRENT_STORED_OWNERSHIP_CONFLICT = 0
NATURAL_US_DUPLICATE = 0
NATURAL_US_ORPHAN = 0
```

---

# 33. Rollback

Document exact US-only rollback.

Preferred:

```text
US Price Structure flag = OFF
```

Do not roll back KR Price Structure.

No DB cleanup.

---

# 34. Stop conditions

STOP / DO NOT ENABLE if:

```text
wrong security basis
currency mismatch
unsupported numeric
remote zone labeled 가까운
unstable Fib exposed
current SR merged with stored rules
company header removed
target/stop invented
test payload mismatch
test duplicate/orphan
any monitored stock material failure
feature-off parity fails
KR runtime behavior changes
new P0
new material P1
```

---

# 35. Full regression

Required:

```text
full monitored US/foreign current-data replay
full monitored US/foreign test-sink messages
Price Structure v3 regression cohort
SR completeness/proximity
family consensus
renderer integration
legacy technical detector
security/currency basis tests
AI/fallback parity
exact payload
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

No public mutation endpoint is expected.

---

# 36. Required reports

Create:

1. `docs/reports/20260828-us-price-structure-scope.md`
2. `docs/reports/20260828-us-price-structure-current-universe.md`
3. `docs/reports/20260828-us-price-structure-coverage.md`
4. `docs/reports/20260828-us-price-structure-per-ticker.md`
5. `docs/reports/20260828-us-price-structure-ai-fallback-parity.md`
6. `docs/reports/20260828-us-price-structure-security-basis.md`
7. `docs/reports/20260828-us-price-structure-test-delivery.md`
8. `docs/reports/20260828-us-price-structure-exact-test-messages.md`
9. `docs/reports/20260828-us-price-structure-message-quality.md`
10. `docs/reports/20260828-us-price-structure-preenable-readiness.md`
11. `docs/reports/20260828-us-price-structure-operating-promotion.md`
12. `docs/reports/20260828-us-price-structure-post-enable-smoke.md`
13. `docs/reports/20260828-us-price-structure-natural-proof-status.md`
14. `docs/reports/20260828-us-price-structure-safety-parity.md`
15. `docs/reports/20260828-us-price-structure-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-us-price-structure-per-ticker.json
docs/reports/20260828-us-price-structure-preenable-readiness.json
docs/reports/20260828-us-price-structure-natural-proof-status.json
```

---

# 37. Required gates

Set exactly:

```text
CURRENT_US_MONITORED_STOCK_COUNT =
...

US_STOCK_TICKERS =
...

ALL_US_STOCK_PRICE_STRUCTURE_REPLAY =
PASS / FAIL

US_PRICE_STRUCTURE_SECURITY_BASIS =
PASS / FAIL

US_PRICE_STRUCTURE_CURRENCY_BASIS =
PASS / FAIL

PRICE_STRUCTURE_ELIGIBLE_COUNT =
...

PRICE_STRUCTURE_SR_ONLY_COUNT =
...

PRICE_STRUCTURE_OMIT_COUNT =
...

PRICE_STRUCTURE_BLOCKED_COUNT =
...

LONG_HORIZON_RENDERED_AS_NEAR =
0 / NONZERO

REMOTE_ZONE_PROMOTED_AS_NEAR_FILL =
0 / NONZERO

RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY =
0 / NONZERO

UNSTABLE_FIB_EXPOSED =
0 / NONZERO

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE =
0 / NONZERO

CURRENT_SR_RENDERED_AS_STORED_RULE =
0 / NONZERO

STORED_RULE_RENDERED_AS_CURRENT_SR =
0 / NONZERO

COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION =
0 / NONZERO

AI_CALCULATED_TECHNICAL_PRICE =
0 / NONZERO

AI_SELECTED_AUTHORITATIVE_SR =
0 / NONZERO

UNREGISTERED_PRICE_STRUCTURE_NUMERIC =
0 / NONZERO

NUMBERS_WITHOUT_PROVENANCE =
0 / NONZERO

UNSUPPORTED_TARGET_PRICE =
0 / NONZERO

UNSUPPORTED_STOP_PRICE =
0 / NONZERO

SECURITY_BASIS_CONFLICT =
0 / NONZERO

CURRENCY_MISMATCH =
0 / NONZERO

AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY =
PASS / FAIL

AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_STORED_RULE_OWNERSHIP_PARITY =
PASS / FAIL

AI_FALLBACK_FIB_VISIBILITY_PARITY =
PASS / FAIL

TEST_STOCK_MESSAGE_COUNT =
...

TEST_STOCK_FAIL_COUNT =
0 / NONZERO

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL / NOT_SENT

TEST_MESSAGE_QUALITY =
PASS / FAIL / NOT_SENT

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

US_PRICE_STRUCTURE_PREENABLE =
PASS / FAIL / BLOCKED

OPERATING_PROMOTION =
PASS / NOT_RUN / FAIL

FEATURE_OFF_PARITY =
PASS / NOT_RUN / FAIL

US_PRICE_STRUCTURE_ENABLED =
true / false

US_PRICE_STRUCTURE_SCOPE =
MONITORED_US_FOREIGN_ONLY / OTHER

POST_ENABLE_ALL_US_STOCKS =
PASS / NOT_RUN / FAIL

POST_ENABLE_KR_PRICE_STRUCTURE_DIFF =
0 / NONZERO

US_MARKET_DIGEST_CODE_DIFF_FROM_PRICE_STRUCTURE =
0 / NONZERO

US_MARKET_DIGEST_PRICE_STRUCTURE_LEAK =
0 / NONZERO

KR_RUNTIME_POLICY_DIFF =
0 / NONZERO

PRODUCTION_ASSIST =
OFF / OTHER

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

US_PRICE_STRUCTURE =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_US_PRICE_STRUCTURE =
PENDING / PASS / FAIL
```

---

# 38. PASS rule before enablement

Require:

```text
full monitored universe replay PASS
security/currency basis PASS
all test messages PASS
exact payload PASS
numeric provenance PASS
proximity safety PASS
Fib safety PASS
stored-rule ownership PASS
P0 = 0
material P1 = 0
```

Then:

`US_PRICE_STRUCTURE_PREENABLE = PASS`

---

# 39. Enablement rule

After:

```text
operating promotion
feature-off parity
US-only scope proof
US Price Structure ON
full-universe post-enable smoke
KR unchanged
```

set:

`US_PRICE_STRUCTURE = ENABLED_AWAITING_NATURAL_PROOF`

---

# 40. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_IMPLEMENTATION = ...

TRACK_D_BRANCH = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

CURRENT_US_MONITORED_STOCK_COUNT = ...
US_STOCK_TICKERS = ...

ALL_US_STOCK_PRICE_STRUCTURE_REPLAY = ...
US_PRICE_STRUCTURE_SECURITY_BASIS = ...
US_PRICE_STRUCTURE_CURRENCY_BASIS = ...

PRICE_STRUCTURE_ELIGIBLE_COUNT = ...
PRICE_STRUCTURE_SR_ONLY_COUNT = ...
PRICE_STRUCTURE_OMIT_COUNT = ...
PRICE_STRUCTURE_BLOCKED_COUNT = ...

PER_TICKER_PRICE_STRUCTURE_AUDIT = ...

AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY = ...
AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY = ...
AI_FALLBACK_STORED_RULE_OWNERSHIP_PARITY = ...
AI_FALLBACK_FIB_VISIBILITY_PARITY = ...

TEST_STOCK_MESSAGE_COUNT = ...
TEST_STOCK_FAIL_COUNT = 0
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_MESSAGE_QUALITY = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0

LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
UNSTABLE_FIB_EXPOSED = 0
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0

AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

SECURITY_BASIS_CONFLICT = 0
CURRENCY_MISMATCH = 0

US_PRICE_STRUCTURE_PREENABLE = ...

OPERATING_PROMOTION = ...
FEATURE_OFF_PARITY = ...

US_PRICE_STRUCTURE_ENABLED = ...
US_PRICE_STRUCTURE_SCOPE = ...
POST_ENABLE_ALL_US_STOCKS = ...

POST_ENABLE_KR_PRICE_STRUCTURE_DIFF = 0
KR_RUNTIME_POLICY_DIFF = 0

US_MARKET_DIGEST_CODE_DIFF_FROM_PRICE_STRUCTURE = 0
US_MARKET_DIGEST_PRICE_STRUCTURE_LEAK = 0

PRODUCTION_ASSIST = OFF

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

US_PRICE_STRUCTURE =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_US_PRICE_STRUCTURE =
PENDING /
PASS /
FAIL

ROLLBACK = ...

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_STOCK_MESSAGES /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 41. Mandatory completion ZIP

Create:

`20260828-us-price-structure-selective-preenablement-bundle.zip`

Include:

```text
exact instruction
all track instructions
scope/current universe
coverage audit
per-ticker Price Structure audit
security/currency basis
AI/fallback parity
test delivery
exact full-universe test messages
message quality
preenable gate matrix
operating promotion
post-enable smoke
natural-proof status
rollback
safety parity
machine-readable JSON
test/CI summary
artifact index
```

Exclude secrets, raw sink IDs, tokens, auth headers, account identifiers, and hidden chain-of-thought.

---

# 42. Final principle

The US market message and US stock messages answer different questions.

The market message answers:

```text
What happened in the US market?
```

The stock Price Structure block answers:

```text
Where is this monitored stock trading relative to verified structural support/resistance?
```

Enable stock-level Price Structure only after every monitored US/foreign name has passed current-data replay,
security/currency-basis validation, and real test-sink message review.
