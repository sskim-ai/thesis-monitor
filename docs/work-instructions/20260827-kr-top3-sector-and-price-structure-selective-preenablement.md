# thesis-monitor — KR TOP3 Sector + Price Structure v3 Selective Pre-Enablement
## KR market digest: 규모별 + 업종 상대 강세/약세 TOP3
## KR stock messages: deterministic SR + safe Fib/SR where eligible
## Dedicated test-sink E2E → KR-only bounded enablement → next natural proof
## US Price Structure remains OFF

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `KR_TOP3_SECTOR_AND_PRICE_STRUCTURE_SELECTIVE_PREENABLEMENT`
- Task class: `CONTROLLED_KR_ONLY_RUNTIME_ROLLOUT`
- Source policy: preserve current production source policy
- Latest reported main / operating entering this task:
  `97d90815caf18a1daad1833dfbe4eb04b364f975`
- Latest KR size/sector message-selection repair:
  `de352342f15a75069289f35f00b4bd24ddcdd19f`
- Current KR size/sector state:
  `ACTIVE_AWAITING_NATURAL_PROOF`
- Current Price Structure v3:
  `INTEGRATED_READY_NOT_ARMED`
- Current US Price Structure state:
  keep `NOT ARMED`
- Production Assist:
  preserve `OFF`
- Business investment-logic mutation:
  `0`

### User-authorized scope

This instruction explicitly authorizes:

```text
KR market digest:
- 규모별 data visible
- KOSPI relative strong sectors TOP3
- KOSPI relative weak sectors TOP3
- KOSDAQ relative strong sectors TOP3
- KOSDAQ relative weak sectors TOP3

KR monitored-stock messages:
- Price Structure v3 selective exposure
- deterministic nearest support
- deterministic nearest resistance
- major structural support/resistance when available
- Fib/SR confluence only when family-stable/material/safe

Pre-enable:
- dedicated non-production test sink
- bounded test delivery
- KR-only selective runtime enablement after PASS
```

Not authorized:

```text
US Price Structure enablement
global/all-ticker Price Structure enablement
production-recipient test send
manual production scheduler execution
unsupported target/stop creation
business-thesis mutation
```

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve actual latest safe `origin/main`
4. resolve actual operating SHA
5. record lineage
6. do not roll back to an older SHA unless explicitly justified

---

# 1. Objective

Deliver one coordinated KR-only rollout:

```text
A. Market digest
   → 규모별
   → 업종 상대 강세 TOP3 / 상대 약세 TOP3

B. Stock monitoring messages
   → current Price Structure v3
   → SR always when eligible
   → Fib only when safe/material

C. Dedicated test-sink E2E
   → market digest
   → selected KR stock messages
   → exact payload/format
   → exactly once

D. KR-only bounded enablement
   → only after PASS
   → next natural KR close / monitoring proof
```

Tracks A and B may be implemented in parallel.
Track C starts after A+B are on the same latest safe main.
Track D starts only after Track C PASS.

Recommended branches:

```text
codex/kr-top3-sector-market-message
codex/kr-price-structure-v3-selective-stock-message
codex/kr-test-sink-e2e-preflight
codex/kr-only-bounded-enablement
```

---

# 2. Existing KR market-message baseline to preserve

Already passing:

```text
KR local-first
KOSPI/KOSDAQ direction
breadth
foreign/institution/retail aggregate flow
numeric registry
AI/fallback shared ownership
ka10051 aggregate ownership
ka10066 full pagination
reconciliation fail-closed
exactly once
size/style current-session selection
```

Do not regress these while expanding sector output from TOP1 to TOP3.

---

# 3. Existing Price Structure v3 baseline to preserve

Price Structure v3 already passed shadow/replay validation.

Core invariants:

```text
Daily history 1200 bars
Weekly history 600 bars
Monthly history 300 bars

partial current bars excluded from pivot confirmation

deterministic SR is the base layer
wave/Fib optional enhancement

nearest support
nearest resistance
major structural support/resistance

Fib only when family-stable / material / safe

no-wave = valid SR-only state
```

Do not redesign the engine.

This task is production wiring / renderer selection only.

---

# 4. Track A — market digest TOP3 sector policy

When safe same-session sector-index return rows exist:

select deterministically:

```text
KOSPI:
relative strong TOP3
relative weak TOP3

KOSDAQ:
relative strong TOP3
relative weak TOP3
```

Do not let AI sort raw sector tables.

Hard:

```text
AI_DERIVED_SECTOR_RANKING = 0
AI_DERIVED_SECTOR_RETURN = 0
```

---

# 5. Relative terminology

Do not expose internal:

```text
leader
laggard
```

Use:

```text
업종 상대 강세
업종 상대 약세
```

This remains valid even when:

```text
all sectors positive
all sectors negative
```

because it expresses cross-sectional ranking.

Hard:

`USER_FACING_LEADER_LAGGARD_TERM = 0`

---

# 6. Sector TOP3 deterministic selection

Ranking owner:

```text
backend deterministic ranking
```

Selection contract per market:

```text
strongest 3 distinct safe sectors
weakest 3 distinct safe sectors
```

If fewer than 3 safe rows exist:

```text
render only available safe rows
```

Never duplicate a sector to reach 3.

Never use stale prior-session sector rows.

Hard:

```text
SECTOR_TOP3_DUPLICATE = 0
STALE_SECTOR_IN_TOP3 = 0
```

---

# 7. Sector TOP3 tie policy

If exact equal returns occur:

use an existing deterministic tie-breaker.

If none exists, define a stable non-semantic tie-breaker such as:

```text
canonical sector key ascending
```

Do not let AI decide ties.

Document the policy.

Hard:

`NONDETERMINISTIC_SECTOR_TIEBREAK = 0`

---

# 8. Sector return vs sector breadth

Keep separate:

```text
sector-index return
sector component breadth
```

TOP3 strong/weak is based on the canonical same-session sector-return field unless existing policy says otherwise.

Hard:

`SECTOR_RETURN_AS_SECTOR_BREADTH = 0`

---

# 9. Market message hierarchy after TOP3 expansion

Required priority:

```text
1. KOSPI/KOSDAQ direction
2. breadth
3. aggregate participant flow
4. size/style
5. sector relative strong TOP3
6. sector relative weak TOP3
7. KR FX if material
8. global/prior macro secondary
9. next-check
```

If length pressure exists:

reduce:

```text
global macro
repetitive explanation
verbose next-check
```

before dropping current-session size/sector.

Hard:

`GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_INTERNAL_STRUCTURE = 0`

---

# 10. Compact market-digest rendering

Preferred semantic form:

```text
📊 시장 내부

규모별
KOSPI 대형 ... · 중형 ... · 소형 ...
KOSDAQ100 ... · MID300 ... · SMALL ...

업종 상대 강세
KOSPI A ... · B ... · C ...
KOSDAQ D ... · E ... · F ...

업종 상대 약세
KOSPI G ... · H ... · I ...
KOSDAQ J ... · K ... · L ...
```

Do not hard-code exact punctuation.

Keep current-session numeric provenance.

---

# 11. Track A validator

When >=3 safe sectors exist per side:

```text
KOSPI_STRONG_TOP3_CONSUMED = PASS
KOSPI_WEAK_TOP3_CONSUMED = PASS
KOSDAQ_STRONG_TOP3_CONSUMED = PASS
KOSDAQ_WEAK_TOP3_CONSUMED = PASS
```

If fewer safe rows exist:

use:

```text
PARTIAL_SAFE_AVAILABLE_COUNT_n
```

not fabricated fill.

---

# 12. Track B — KR-only Price Structure selective exposure

Initial scope:

```text
current monitored KR universe only
```

Do not enable for:

```text
US stocks
unregistered arbitrary tickers
all Korean securities globally
```

unless separately authorized later.

Hard:

`PRICE_STRUCTURE_SCOPE_BLEED = 0`

---

# 13. Price Structure runtime eligibility

Use existing runtime eligibility:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT_PRICE_STRUCTURE
BLOCKED
```

Do not hard-code prior replay counts.

---

# 14. ELIGIBLE rendering

For `ELIGIBLE`, render bounded current structure:

```text
📐 현재 가격 구조

가까운 지지
가까운 저항

주요 구조 지지
and/or
주요 구조 저항

Fib/SR 겹침
only if safe/material
```

Do not force every field if genuinely unavailable.

---

# 15. ELIGIBLE_SR_ONLY rendering

For `ELIGIBLE_SR_ONLY`:

```text
nearest support
nearest resistance
major structural SR when available
```

No Fib line.

No empty placeholder.

Hard:

```text
SR_ONLY_EMPTY_FIB_LINE = 0
UNSTABLE_FIB_EXPOSED_IN_SR_ONLY = 0
```

---

# 16. OMIT / BLOCKED

For:

```text
OMIT_PRICE_STRUCTURE
BLOCKED
```

omit the current Price Structure section safely.

The rest of the stock message must render normally.

Hard:

`PRICE_STRUCTURE_BLOCK_FAILS_WHOLE_MESSAGE = 0`

---

# 17. SR ownership

All numeric SR values are backend-owned.

AI may:

```text
select registered IDs
interpret
explain
```

AI may not:

```text
calculate a technical price
invent a support/resistance level
derive target/stop
```

Hard:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
```

---

# 18. Nearest vs major distinction

Preserve semantic ownership:

```text
가까운 지지
가까운 저항
주요 구조 지지
주요 구조 저항
```

Do not collapse all zones into generic support/resistance.

Hard:

```text
NEAREST_MAJOR_LABEL_COLLAPSE = 0
REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
```

---

# 19. Fib policy

Fib is optional secondary structural evidence.

Render only if:

```text
family-stable
user-visible eligible
material
safe
```

and preferably where it overlaps real SR/pivots.

Hard:

```text
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
FABRICATED_FIB_RANGE = 0
```

---

# 20. Fib/SR range preservation

When Fib materially extends beyond a narrower SR band:

show the actual safe Fib/SR range.

Do not shorten it to the SR range.

Hard:

`MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED = 0`

---

# 21. Current structure vs stored monitoring price rules

Keep separate:

```text
📐 현재 가격 구조
🧭 기존 등록 가격 규칙
```

Do not merge them.

Hard:

```text
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNLABELED_CURRENT_STORED_PRICE_CONFLICT = 0
```

---

# 22. No target / stop invention

Do not turn SR into:

```text
target price
stop-loss
recommended entry
recommended exit
```

Hard:

```text
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 23. Legacy technical prose suppression

Preserve the completed false-positive repair.

Hard:

```text
COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0
NON_TECHNICAL_PROSE_SUPPRESSED = 0
STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0
```

RXRX-style substring false positives must remain impossible.

---

# 24. Temporal safety

Price Structure must use the latest completed safe session per existing engine policy.

For KR test/preflight after 2026-08-27 close:

expected:

```text
KR target = 2026-08-27
```

Partial current bars:

```text
may be retained as context
must not confirm pivots
```

Hard:

```text
WRONG_SESSION_DATA = 0
LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
```

---

# 25. Price Structure test controls

Use the current monitored KR universe.

Where naturally present, prioritize controls:

```text
000660
003690
005490
005930
010120
012450
086280
```

Do not assume every ticker must be `ELIGIBLE`.

Record exact runtime eligibility.

---

# 26. Price Structure required per-stock audit

For each monitored KR ticker:

```text
ticker
company
target session
eligibility
nearest support
nearest resistance
major support
major resistance
Fib/SR if eligible
stored price-rule presence
renderer output
provenance refs
```

No manual arithmetic.

---

# 27. Track C — dedicated test sink

Use a dedicated non-production test sink.

Must prove:

```text
test sink != production sink
test namespace != production namespace
test intent cannot be consumed by production sender
```

No raw private IDs in reports.

Hard:

```text
TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0
```

---

# 28. Test-sink scope

Test two product types:

```text
A. KR market digest
B. KR monitored-stock message(s) containing Price Structure when eligible
```

Do not send every monitored stock unless necessary.

Use a bounded representative sample sufficient to cover:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT/BLOCKED if available
stored-rule separation if available
Fib-visible case if available
```

Recommended maximum:

```text
1 market digest
3-5 stock messages
```

---

# 29. Test route selection

For each test artifact:

use the same route production would choose:

```text
AI if production eligibility says AI
otherwise deterministic fallback
```

Do not manually choose prettier outputs.

---

# 30. Market digest test-send hard gates

Received test message must show:

```text
KOSPI/KOSDAQ direction
breadth
aggregate flow
size/style
KOSPI strong TOP3
KOSPI weak TOP3
KOSDAQ strong TOP3
KOSDAQ weak TOP3
```

when safe rows exist.

Hard:

```text
TEST_MARKET_TOP3_STRONG_VISIBLE = PASS
TEST_MARKET_TOP3_WEAK_VISIBLE = PASS
```

---

# 31. Stock-message test-send hard gates

For each selected stock:

if `ELIGIBLE`:

```text
current Price Structure visible
nearest support/resistance visible
major SR when available
Fib/SR visible only if eligible/material
stored rules separate
```

if `ELIGIBLE_SR_ONLY`:

```text
SR visible
Fib absent
```

if `OMIT/BLOCKED`:

```text
Price Structure absent
message still valid
```

---

# 32. Exact payload / formatting

For every test message compare:

```text
rendered payload
outbound payload
receipt-linked/received payload
```

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_MESSAGE_TRUNCATED = 0
TEST_FORMATTING_BROKEN = 0
```

---

# 33. Test-send exactly once

Use test-only delivery identities.

Hard:

```text
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 34. Production-recipient prohibition

Do not send any test artifact to production user/channel.

Hard:

```text
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
```

---

# 35. Track C integration gate

Do not proceed to enablement unless:

```text
market TOP3 test = PASS
stock Price Structure test = PASS
payload parity = PASS
formatting = PASS
numeric provenance = PASS
P0 = 0
material P1 = 0
```

---

# 36. Track D — KR-only bounded enablement

After Track C PASS, enable only:

```text
KR market digest TOP3 sector policy
KR monitored-stock Price Structure v3 selective exposure
```

Do NOT enable:

```text
US Price Structure
unregistered KR ticker Price Structure
all-market generic Price Structure
Production Assist
```

---

# 37. Runtime gate discovery

Use existing rollout/config mechanisms.

Possible market TOP3 state:

```text
ALREADY_ACTIVE_BY_CODE_DEFAULT
EXISTING_FEATURE_FLAG
EXISTING_CONFIG
```

Possible Price Structure state:

```text
EXISTING_FEATURE_FLAG
EXISTING_CONFIG
SHADOW_ONLY_SWITCH
```

Do not create duplicate frameworks unless there is no safe existing gate.

---

# 38. KR Price Structure feature state

If a region/market-scoped Price Structure gate exists:

enable:

```text
KR = ON
US = OFF
```

If only a global gate exists:

do NOT flip global ON.

Add the smallest market-scoped guard needed to permit:

```text
KR monitored universe only
```

while US remains OFF.

This is the only case where a bounded new rollout guard is authorized.

Hard:

```text
US_PRICE_STRUCTURE_ENABLED = 0
```

---

# 39. Rollback

Rollback must be one bounded action:

```text
KR Price Structure OFF
```

and, if applicable:

```text
KR TOP3 sector policy revert
```

No DB cleanup.

Document exact rollback path.

---

# 40. Post-enable smoke

After KR-only enablement:

run read-only production-equivalent render.

Verify:

```text
market TOP3 still visible
KR stock Price Structure visible per eligibility
US stock Price Structure still absent
business/valuation text unchanged
```

Hard:

```text
POST_ENABLE_KR_PRICE_STRUCTURE = PASS
POST_ENABLE_US_PRICE_STRUCTURE_LEAK = 0
POST_ENABLE_MARKET_TOP3 = PASS
```

---

# 41. Natural proof after enablement

Do not manually trigger production schedules.

Wait for next natural:

```text
KR afternoon market digest
KR monitored-stock message cycle
```

Read-only verify:

```text
exact target session
exactly once
TOP3 sectors visible
Price Structure visible only where eligible
SR/Fib provenance
stored-rule separation
no unsupported target/stop
```

Until observed:

```text
KR_ROLLOUT =
ENABLED_AWAITING_NATURAL_PROOF
```

---

# 42. US isolation

US must remain unchanged.

Hard:

```text
US_MARKET_DIGEST_CODE_DIFF = 0
US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_RUNTIME_DIFF = 0
```

---

# 43. Business / valuation isolation

Hard:

```text
BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF_FROM_PRICE_STRUCTURE_ENABLEMENT = 0
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
```

---

# 44. Focused Track A tests

Required:

```text
>6 valid sectors
→ top3 / bottom3 distinct

exact ties
→ deterministic tie-break

fewer than 3 valid
→ partial safe, no duplication

all positive
→ relative strong/weak labels valid

all negative
→ relative strong/weak labels valid

stale sector row
→ excluded

KOSPI/KOSDAQ independently ranked
```

---

# 45. Focused Track B tests

Required:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT
BLOCKED

nearest/major distinction
Fib stable
Fib unstable
stored rule separation
no-wave SR-only
partial-bar safety
company-header preservation
legacy technical suppression safety
```

---

# 46. Focused Track C tests

Required:

```text
test sink != production sink
test namespace isolation
market digest test send
ELIGIBLE stock test send
SR_ONLY stock test send
exact payload
formatting
duplicate protection
production-intent isolation
```

---

# 47. Full regression

Required before enablement:

```text
Track A focused
Track B focused
Track C focused
full KR market replay
full monitored KR stock replay
full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
```

No Public Action change expected unless the existing runtime-control surface already exposes configuration;
do not add public mutation endpoints for rollout.

---

# 48. Required architecture/policy docs

Create/update:

```text
docs/architecture/KR_SIZE_SECTOR_MESSAGE_POLICY.md
docs/architecture/KR_PRICE_STRUCTURE_SELECTIVE_ROLLOUT.md
docs/architecture/PRICE_STRUCTURE_V3_RENDERER_OWNERSHIP.md
docs/architecture/KR_TEST_SINK_ROLLOUT_SAFETY.md
```

---

# 49. Required reports

Create:

1. `docs/reports/20260827-kr-top3-sector-policy.md`
2. `docs/reports/20260827-kr-top3-sector-run42-replay.md`
3. `docs/reports/20260827-kr-price-structure-selective-scope.md`
4. `docs/reports/20260827-kr-price-structure-current-replay.md`
5. `docs/reports/20260827-kr-price-structure-per-ticker-audit.md`
6. `docs/reports/20260827-kr-test-sink-isolation.md`
7. `docs/reports/20260827-kr-market-test-exact-message.md`
8. `docs/reports/20260827-kr-stock-test-exact-messages.md`
9. `docs/reports/20260827-kr-test-message-quality.md`
10. `docs/reports/20260827-kr-rollout-gate-matrix.md`
11. `docs/reports/20260827-kr-only-enablement-action.md`
12. `docs/reports/20260827-kr-post-enable-smoke.md`
13. `docs/reports/20260827-kr-natural-proof-status.md`
14. `docs/reports/20260827-kr-rollout-safety-parity.md`
15. `docs/reports/20260827-kr-rollout-artifact-index.md`

Recommended machine-readable:

```text
docs/reports/20260827-kr-top3-sector-selection.json
docs/reports/20260827-kr-price-structure-per-ticker-audit.json
docs/reports/20260827-kr-rollout-gate-matrix.json
docs/reports/20260827-kr-rollout-status.json
```

---

# 50. Required hard gates

Set exactly:

```text
KR_TOP3_SECTOR_POLICY =
PASS / FAIL

KOSPI_STRONG_TOP3_CONSUMED =
PASS / PARTIAL_SAFE / FAIL

KOSPI_WEAK_TOP3_CONSUMED =
PASS / PARTIAL_SAFE / FAIL

KOSDAQ_STRONG_TOP3_CONSUMED =
PASS / PARTIAL_SAFE / FAIL

KOSDAQ_WEAK_TOP3_CONSUMED =
PASS / PARTIAL_SAFE / FAIL

SECTOR_TOP3_DUPLICATE =
0 / NONZERO

STALE_SECTOR_IN_TOP3 =
0 / NONZERO

NONDETERMINISTIC_SECTOR_TIEBREAK =
0 / NONZERO

USER_FACING_LEADER_LAGGARD_TERM =
0 / NONZERO

SECTOR_RETURN_AS_SECTOR_BREADTH =
0 / NONZERO

GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_INTERNAL_STRUCTURE =
0 / NONZERO

KR_PRICE_STRUCTURE_SCOPE =
MONITORED_KR_ONLY / FAIL

SELECTIVE_ELIGIBILITY_ROUTING =
PASS / FAIL

PRICE_STRUCTURE_ELIGIBLE_RENDER =
PASS / FAIL

PRICE_STRUCTURE_SR_ONLY_RENDER =
PASS / FAIL

PRICE_STRUCTURE_OMIT_BLOCKED_RENDER =
PASS / FAIL

AI_CALCULATED_TECHNICAL_PRICE =
0 / NONZERO

UNREGISTERED_PRICE_STRUCTURE_NUMERIC =
0 / NONZERO

NEAREST_MAJOR_LABEL_COLLAPSE =
0 / NONZERO

REMOTE_ZONE_PROMOTED_AS_NEAREST =
0 / NONZERO

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE =
0 / NONZERO

UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED =
0 / NONZERO

CURRENT_SR_RENDERED_AS_STORED_RULE =
0 / NONZERO

STORED_RULE_RENDERED_AS_CURRENT_SR =
0 / NONZERO

UNSUPPORTED_TARGET_PRICE =
0 / NONZERO

UNSUPPORTED_STOP_PRICE =
0 / NONZERO

STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 =
0 / NONZERO

COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION =
0 / NONZERO

LOOKAHEAD_LEAK =
0 / NONZERO

PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION =
0 / NONZERO

TEST_SINK_AVAILABLE =
YES / NO

TEST_PRODUCTION_SINK_COLLISION =
0 / NONZERO

TEST_PRODUCTION_INTENT_COLLISION =
0 / NONZERO

TEST_MARKET_TOP3_STRONG_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_MARKET_TOP3_WEAK_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_PRICE_STRUCTURE_ELIGIBLE_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_PRICE_STRUCTURE_SR_ONLY_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL / NOT_SENT

TEST_MESSAGE_TRUNCATED =
0 / NONZERO

TEST_FORMATTING_BROKEN =
0 / NONZERO

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

KR_MARKET_TOP3_ENABLEMENT =
ACTIVE / ENABLED / DO_NOT_ENABLE

KR_PRICE_STRUCTURE_ENABLEMENT =
ENABLED_KR_ONLY /
DO_NOT_ENABLE

US_PRICE_STRUCTURE_ENABLED =
0 / NONZERO

POST_ENABLE_KR_PRICE_STRUCTURE =
PASS / FAIL / NOT_RUN

POST_ENABLE_US_PRICE_STRUCTURE_LEAK =
0 / NONZERO

POST_ENABLE_MARKET_TOP3 =
PASS / FAIL / NOT_RUN

BUSINESS_THESIS_MUTATION =
0 / NONZERO

VALUATION_TEXT_DIFF_FROM_PRICE_STRUCTURE_ENABLEMENT =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

KR_ROLLOUT =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL
```

---

# 51. Enablement PASS rule

Enable KR-only only if:

```text
TOP3 sector deterministic selection PASS
market test-sink exact message PASS
Price Structure KR replay PASS
stock test-sink messages PASS
numeric provenance PASS
temporal safety PASS
stored-rule separation PASS
no unsupported target/stop
test sink isolated
exactly-once test delivery
US Price Structure remains OFF
P0 = 0
material P1 = 0
```

Then:

```text
KR_MARKET_TOP3_ENABLEMENT =
ACTIVE or ENABLED

KR_PRICE_STRUCTURE_ENABLEMENT =
ENABLED_KR_ONLY

KR_ROLLOUT =
ENABLED_AWAITING_NATURAL_PROOF
```

---

# 52. Stop conditions

STOP / DO NOT ENABLE if:

```text
no safe test sink
test sink collides with production
sector TOP3 uses stale rows
AI ranks raw sectors
Price Structure value lacks provenance
unstable Fib appears
stored/current price ownership merges
target/stop invented
Price Structure appears for blocked/omit ticker
US Price Structure turns on
test send reaches production recipient
duplicate test send
new P0
new material P1
```

---

# 53. Natural proof final state

After next natural KR market and KR stock-monitoring messages prove the rollout:

```text
NATURAL_KR_MARKET_TOP3 = PASS
NATURAL_KR_PRICE_STRUCTURE = PASS
NATURAL_KR_DUPLICATE = 0
NATURAL_KR_ORPHAN = 0
NATURAL_US_PRICE_STRUCTURE_LEAK = 0
```

Then:

```text
KR_ROLLOUT = LIVE_PASS
```

US remains separately governed.

---

# 54. Completion response

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
TRACK_D_IMPLEMENTATION = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

TARGET_KR_SESSION = ...

KR_TOP3_SECTOR_POLICY = ...

KOSPI_STRONG_TOP3 = ...
KOSPI_WEAK_TOP3 = ...
KOSDAQ_STRONG_TOP3 = ...
KOSDAQ_WEAK_TOP3 = ...

KOSPI_STRONG_TOP3_CONSUMED = ...
KOSPI_WEAK_TOP3_CONSUMED = ...
KOSDAQ_STRONG_TOP3_CONSUMED = ...
KOSDAQ_WEAK_TOP3_CONSUMED = ...

SECTOR_TOP3_DUPLICATE = 0
STALE_SECTOR_IN_TOP3 = 0
USER_FACING_LEADER_LAGGARD_TERM = 0

KR_PRICE_STRUCTURE_SCOPE = ...
SELECTIVE_ELIGIBILITY_ROUTING = ...

KR_PRICE_STRUCTURE_TICKER_AUDIT = ...
PRICE_STRUCTURE_ELIGIBLE_RENDER = ...
PRICE_STRUCTURE_SR_ONLY_RENDER = ...
PRICE_STRUCTURE_OMIT_BLOCKED_RENDER = ...

AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

TEST_SINK_AVAILABLE = ...
TEST_SINK_ALIAS = ...

TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0

TEST_MARKET_MESSAGE_COUNT = ...
TEST_STOCK_MESSAGE_COUNT = ...

TEST_MARKET_TOP3_STRONG_VISIBLE = ...
TEST_MARKET_TOP3_WEAK_VISIBLE = ...

TEST_PRICE_STRUCTURE_ELIGIBLE_VISIBLE = ...
TEST_PRICE_STRUCTURE_SR_ONLY_VISIBLE = ...

TEST_EXACT_PAYLOAD_MATCH = ...
TEST_MESSAGE_TRUNCATED = 0
TEST_FORMATTING_BROKEN = 0
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

KR_MARKET_TOP3_ENABLEMENT = ...
KR_PRICE_STRUCTURE_ENABLEMENT = ...
US_PRICE_STRUCTURE_ENABLED = 0

POST_ENABLE_KR_PRICE_STRUCTURE = ...
POST_ENABLE_US_PRICE_STRUCTURE_LEAK = 0
POST_ENABLE_MARKET_TOP3 = ...

BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF_FROM_PRICE_STRUCTURE_ENABLEMENT = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

KR_ROLLOUT =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_KR_MARKET_TOP3 =
PENDING /
PASS /
FAIL

NATURAL_KR_PRICE_STRUCTURE =
PENDING /
PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_KR_MESSAGES /
NO_ACTION /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 55. Mandatory completion ZIP

Create:

`20260827-kr-top3-sector-and-price-structure-selective-preenablement-bundle.zip`

Include:

```text
exact master instruction
all track instructions
TOP3 sector policy/replay
Price Structure KR per-ticker audit
test-sink isolation
exact market test message
exact stock test messages
numeric provenance
renderer ownership
enablement gate matrix
post-enable smoke
natural-proof status
safety parity
machine-readable JSON artifacts
test/CI summary
artifact index
```

Exclude:

```text
secrets
raw sink IDs
auth headers
account identifiers
private tokens
hidden chain-of-thought
```

Compute SHA-256.

---

# 56. Final principle

The KR market answer should show:

```text
what the indices did
how broad the move was
who bought/sold
which size buckets led
which 3 sectors were relatively strongest
which 3 sectors were relatively weakest
```

And each eligible KR stock message should show:

```text
what the business/investment logic says
+
where the current price sits structurally
```

through backend-owned:

```text
nearest support
nearest resistance
major structural SR
safe Fib/SR only when eligible
```

Keep US Price Structure OFF.
Keep targets/stops unsupported.
Keep current structure separate from stored monitoring rules.
