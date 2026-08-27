# thesis-monitor — KR Price Structure Daily-History + Nearest-Semantics Bounded Repair
## Fix KR daily OHLCV 0/1200 + prevent LONG_HORIZON/remote zones from rendering as "가까운"
## 7-ticker immutable/current replay
## No test send; no runtime enablement in this repair

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `KR_PRICE_STRUCTURE_DAILY_HISTORY_AND_NEAREST_SEMANTICS_BOUNDED_REPAIR`
- Task class: `BOUNDED_PRICE_STRUCTURE_P1_REPAIR`
- Source policy: preserve current supported/free production sources
- Price Structure v3: preserve `INTEGRATED_READY_NOT_ARMED`
- KR Price Structure production enablement: `OFF`
- US Price Structure production enablement: `OFF`
- Production Assist: preserve `OFF`
- Telegram send: `0`
- Manual production task: `0`
- DB / official assessment mutation: `0`
- Historical archive rewrite: `0`

### Repository lineage from the supplied pre-enable bundle

Bundle project state reported:

```text
recorded base:
97d90815caf18a1daad1833dfbe4eb04b364f975

latest main code:
a7de99c2d1d1211615e0fcbf4bd3eadc06d957fb

operating/deployed code:
de352342f15a75069289f35f00b4bd24ddcdd19f
```

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve actual latest safe `origin/main`
4. resolve current operating SHA
5. use the latest safe main containing the KR TOP3 / KR Price Structure pre-enable code as repair base
6. record exact lineage
7. do NOT promote to operating in this repair

Expected repair base if unchanged:

`a7de99c2d1d1211615e0fcbf4bd3eadc06d957fb`

---

# 1. Source-supported defect statement

The supplied KR TOP3 + Price Structure pre-enable bundle shows:

```text
current monitored KR subjects = 7
Price Structure eligibility    = ELIGIBLE_SR_ONLY for 7/7
family_consensus_safe          = false for 7/7
```

But every KR ticker has:

```text
daily requested_count = 1200
daily actual_count    = 0
daily completed_count = 0
daily provider_returned_count = 0
daily status          = FAIL
daily denial_reason   = insufficient_completed_history
```

while weekly/monthly history remains available.

This is suspicious because the integration previously proved KR daily 1200-bar collection in shadow
validation.

The same bundle also exposes a user-facing proximity defect:

internal summary may select the mathematically nearest available zone even when it is remote / long-horizon,
and the renderer still labels it:

```text
가까운 지지
가까운 저항
```

That is not acceptable.

---

# 2. Frozen 7-ticker controls

Target session in supplied bundle:

`2026-08-27`

Current monitored KR controls:

```text
000660
003690
005490
005930
010120
012450
086280
```

Do not hard-code this as the permanent monitored universe.
Use the actual current monitored KR universe for live/current replay, while preserving these seven as
regression fixtures.

---

# 3. Exact negative-control evidence

## 000660 SK hynix

```text
current price = 1,730,000 KRW

rendered:
가까운 지지 = 995,027 ~ 1,000,015 KRW

distance_pct      = 42.195663
proximity_tier    = LONG_HORIZON
active_relevance  = LONG_HORIZON_HISTORICAL
source timeframe  = weekly
```

This MUST NOT render as:

`가까운 지지`

The same internal object correctly knows it is `LONG_HORIZON`, therefore this is a renderer/validator
semantic failure.

## 005930 Samsung Electronics

```text
current price = 266,000 KRW

rendered:
가까운 지지 = 198,000 ~ 200,000 KRW

distance_pct   ≈ 25.108291
proximity_tier = RELEVANT
```

This requires explicit user-facing proximity review. Do not assume that an internally "nearest available"
zone is user-facing "가까운".

## 012450 Hanwha Aerospace

```text
current price = 1,150,000 KRW

rendered support ≈ 957k ~ 963k
distance ≈ 16.33%

rendered resistance ≈ 1.452m ~ 1.460m
distance ≈ 26.32%
```

Both require proximity-label validation.

---

# 4. Positive-control evidence

These current zones are genuinely local/near in the supplied bundle and must not be lost merely because
daily coverage was 0:

```text
003690:
support distance ≈ 2.83%
resistance distance ≈ 2.64%

005490:
support distance ≈ 1.38%
resistance distance ≈ 0.48%

010120:
support distance ≈ 3.29%
resistance distance ≈ 2.70%

086280:
support distance ≈ 0.19%
resistance distance ≈ 4.65%
```

The repair must preserve valid near zones from safe higher-timeframe evidence when they genuinely meet
the existing proximity contract.

---

# 5. Repair split

This work MUST be splittable:

```text
Track A
KR daily OHLCV actual_count=0 root cause + collection repair

Track B
nearest/proximity semantic ownership + renderer + validator repair

Track C
7-ticker integrated replay + readiness decision
```

Tracks A and B may run in parallel in separate worktrees if ownership does not overlap.

Track C starts only after A+B are on the same latest safe main.

Recommended branches:

```text
codex/kr-price-structure-daily-history-repair
codex/kr-price-structure-nearest-semantics-repair
codex/kr-price-structure-7ticker-replay
```

---

# 6. Track A — daily OHLCV zero root-cause audit

Trace exact path:

```text
KR ticker
→ Price Structure collection request
→ canonical OHLCV service
→ provider/cache adapter
→ requested daily 1200
→ returned daily rows
→ completed-bar filter
→ coverage object
```

For each of 7 tickers record:

```text
requested_count
provider request parameters
provider identity
provider raw returned count
cache key / cache state
adjustment basis
start/end date
completed-bar filter count
final actual_count
denial reason
```

Do not expose secrets.

---

# 7. Daily 0 must be explained, not patched around

Required root-cause classification:

```text
REQUEST_ROUTING_BUG
CACHE_KEY_BUG
TIMEFRAME_MAPPING_BUG
PROVIDER_PARAMETER_BUG
COMPLETED_BAR_FILTER_BUG
ADJUSTMENT_BASIS_BUG
PROVIDER_TRUE_UNAVAILABLE
OTHER_VERIFIED
```

No vague:

```text
insufficient history
```

when provider returned zero without proving genuine absence.

Hard:

`DAILY_ZERO_ROOT_CAUSE = PASS`

---

# 8. Compare with prior 1200-bar contract

The repository previously established:

```text
Daily = 1200
Weekly = 600
Monthly = 300
```

Audit why the current KR pre-enable path differs from the previously passing 1200 daily collection path.

Compare:

```text
service
provider
timeframe enum
adjusted/raw basis
session cutoff
cache
pagination
request limit
```

Do not create a second OHLCV collection implementation if the passing path already exists.

Prefer convergence onto the canonical existing path.

---

# 9. No fake daily reconstruction

Do NOT solve daily 0 by:

```text
resampling weekly into daily
interpolating
forward filling
fabricating missing bars
using intraday snapshots as completed daily history
```

Hard:

```text
SYNTHETIC_DAILY_BARS = 0
FAKE_DAILY_FROM_WEEKLY_MONTHLY = 0
```

---

# 10. Safe supported-provider fallback

If the canonical primary daily source is genuinely unavailable but an already-supported canonical
secondary source exists:

a fallback may be used only if:

```text
security identity matches
currency matches
adjustment basis is compatible
session basis matches
completed-bar policy matches
provenance is preserved
```

Do not add a new paid/unknown provider solely for this repair.

Hard:

`UNVERIFIED_DAILY_PROVIDER_FALLBACK = 0`

---

# 11. Daily completion policy

Current-session incomplete daily bars must remain excluded from pivot confirmation.

Preserve:

```text
completed daily bars
vs
partial current daily context
```

Hard:

```text
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
LOOKAHEAD_LEAK = 0
```

---

# 12. Daily repair success criterion

For long-listed KR controls, expected normal case:

```text
requested daily = 1200
actual daily ≈ 1200
```

or legitimate shorter listing history.

Do NOT require 1200 when listing history/source availability is truly shorter.

Required report per ticker:

```text
PASS_1200
PASS_SHORT_LISTING
FAIL_PROVIDER
FAIL_OTHER
```

Hard target for the known 7 controls:

`UNEXPLAINED_DAILY_ZERO = 0`

---

# 13. Track B — internal "nearest available" vs user-facing "가까운"

Audit the semantic contract currently producing:

```text
summary.nearest_support
summary.nearest_resistance
```

Determine whether "nearest" internally means:

```text
nearest among all valid structural candidates
```

rather than:

```text
near enough to be called 가까운 to the user
```

If so, separate these concepts.

Do not rename internal fields unnecessarily if compatibility depends on them.

---

# 14. User-facing proximity eligibility

Introduce/use one explicit user-facing rule:

```text
NEAR_USER_VISIBLE_ELIGIBLE
```

or repository-native equivalent.

The renderer may say:

```text
가까운 지지
가까운 저항
```

only when the zone passes the existing proximity/relevance contract for that label.

Do NOT invent an arbitrary new percentage threshold if the engine already owns proximity tiers/limits.

Audit and reuse the canonical proximity contract.

---

# 15. LONG_HORIZON hard rule

A zone with:

```text
proximity_tier = LONG_HORIZON
```

or:

```text
active_relevance = LONG_HORIZON_HISTORICAL
```

must NEVER render as:

```text
가까운 지지
가까운 저항
```

Hard:

```text
LONG_HORIZON_RENDERED_AS_NEAR = 0
```

---

# 16. RELEVANT-tier review

Audit what `RELEVANT` means in the current proximity contract.

Do not automatically treat every `RELEVANT` zone as user-facing "가까운".

Required policy must distinguish:

```text
near enough for "가까운"
structurally relevant but not near
long-horizon historical
```

Possible user-facing outcomes, using repository-native wording:

```text
가까운 지지/저항
주요 구조 지지/저항
장기 구조 구간
omit safely
```

Do not create misleading synonyms like "인근" for a 25% distant level.

---

# 17. No valid near zone behavior

If no zone passes user-facing near eligibility:

do NOT promote the closest remote zone just to fill the field.

Allowed:

```text
omit 가까운 지지 line
omit 가까운 저항 line
show major/structural zone separately if safe/material
```

Do not fabricate a local level.

Hard:

```text
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
FABRICATED_SR_FILL = 0
```

---

# 18. Major structural ownership

A remote but structurally meaningful zone may still appear under:

```text
주요 구조 지지
주요 구조 저항
```

or a documented long-horizon structural label.

It must not be duplicated simultaneously as:

```text
가까운
+
주요 구조
```

unless the same zone genuinely owns both semantics under the canonical contract.

Hard:

`NEAR_MAJOR_SEMANTIC_DUPLICATION = 0`

---

# 19. Higher-timeframe valid near zones

Daily-history failure must NOT automatically suppress a safe near zone from weekly/monthly evidence.

Positive controls:

```text
003690
005490
010120
086280
```

If their higher-timeframe zones pass the existing proximity contract:

they may remain user-visible as "가까운".

Hard:

`VALID_HIGHER_TF_NEAR_ZONE_DROPPED = 0`

---

# 20. Coverage-aware renderer

Renderer/eligibility must receive coverage context:

```text
daily status/count
weekly status/count
monthly status/count
```

Do not silently present full-confidence tactical proximity when daily coverage is unavailable.

If daily remains genuinely unavailable after Track A:

the message should use the repository's safe partial-coverage semantics.

Do not invent daily evidence.

---

# 21. Price Structure eligibility review

Audit whether:

```text
daily status = FAIL
```

should still allow:

`ELIGIBLE_SR_ONLY`

under current policy.

Do NOT assume the answer is always no.

Required decision must consider:

```text
safe weekly/monthly evidence
actual proximity
structural validity
renderer label
```

Document exact eligibility rule.

Hard:

`ELIGIBILITY_IGNORES_MATERIAL_COVERAGE_FAILURE = 0`

---

# 22. Validator defect

The supplied gate matrix reported:

```text
REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
```

despite 000660 rendering a 42.2%-distant `LONG_HORIZON` support as:

```text
가까운 지지
```

Therefore the current validator is insufficient.

Trace whether it validates:

```text
engine object only
```

instead of:

```text
final rendered semantic label
```

Set:

`REMOTE_NEAR_VALIDATOR_ROOT_CAUSE = PASS`

---

# 23. Renderer-output validator

Add/repair a deterministic validator that binds:

```text
rendered label
→ fact_ref / zone_id
→ proximity_tier
→ active_relevance
→ distance / canonical proximity eligibility
```

Hard:

```text
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
```

No keyword-only validation.

---

# 24. Broken 000660 fixture must fail

The exact supplied broken section:

```text
📐 현재 가격 구조
• 기준 종가: 1,730,000원
• 가까운 지지: 약 99.5만~100.1만원
• 가까운 저항: 약 187.1만~188.1만원
```

where support is `LONG_HORIZON`, must fail the new validator.

Required:

`RUN000660_OLD_RENDER_NEW_VALIDATOR = FAIL_AS_EXPECTED`

---

# 25. 005930 and 012450 explicit controls

Create policy tests for:

```text
005930 support ≈ -25.1%
012450 support ≈ -16.3%
012450 resistance ≈ +26.3%
```

The expected label must be determined by the canonical proximity policy, not by hard-coded ticker exceptions.

Report:

```text
internal nearest
user-visible label
reason
tier
distance
```

No ticker-specific whitelist.

---

# 26. Positive near controls

The following supplied controls should remain near if the repaired current-data replay still supports them:

```text
003690
005490
010120
086280
```

If Track A daily restoration changes the zones, use the repaired current-data result.

Do not freeze obsolete numeric zones.

---

# 27. Fib isolation

All 7 supplied controls were:

```text
ELIGIBLE_SR_ONLY
family_consensus_safe = false
```

Therefore current replay correctly exposed no Fib.

This repair must not force Fib to appear.

Hard:

```text
UNSTABLE_FIB_EXPOSED = 0
FIB_FORCED_DUE_SR_REPAIR = 0
```

If repaired daily history legitimately changes family consensus:

run the full existing family-safety gates before allowing Fib.

---

# 28. Stored-rule isolation

Preserve:

```text
📐 현재 가격 구조
vs
🧭 기존 등록 가격 규칙
```

Hard:

```text
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
```

---

# 29. No target/stop

Hard:

```text
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 30. Track C — integrated 7-ticker replay

After A+B merge/rebase:

run current/replay analysis for all seven supplied controls at:

`2026-08-27`

using the immutable/session-safe data contract.

Also run latest completed KR session if different, as a separate current-data appendix.

Do not rewrite historical run-42 production artifacts.

---

# 31. Required per-ticker replay table

For each ticker report:

```text
ticker
price_as_of
current price

daily requested / actual / completed
weekly requested / actual / completed
monthly requested / actual / completed

eligibility

nearest internal support
nearest internal resistance

near-user-visible support
near-user-visible resistance

major support
major resistance

each zone:
distance
proximity tier
active relevance
source timeframe
source family
fact_ref

Fib state
stored-rule state
exact rendered section
validator result
```

---

# 32. Required 7-ticker replay gates

Set:

```text
KR_DAILY_HISTORY_CONTRACT = PASS

UNEXPLAINED_DAILY_ZERO = 0

LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0

VALID_HIGHER_TF_NEAR_ZONE_DROPPED = 0
FABRICATED_SR_FILL = 0

RUN000660_OLD_RENDER_NEW_VALIDATOR = FAIL_AS_EXPECTED

FIB_FORCED_DUE_SR_REPAIR = 0
UNSTABLE_FIB_EXPOSED = 0

CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
```

---

# 33. Expected user-facing behavior examples

These are semantic examples, not hard-coded output.

## If 000660 has no genuine nearby support

Allowed:

```text
📐 현재 가격 구조
• 기준 종가: ...
• 가까운 저항: ...
• 주요/장기 구조 지지: ...
```

or omit the remote support entirely if not material.

NOT allowed:

```text
• 가까운 지지: -42% long-horizon zone
```

## If 005490 retains current local zones

Allowed:

```text
가까운 지지
가까운 저항
```

because the zone is genuinely close under the canonical contract.

---

# 34. Test-sink rollout remains blocked

Do NOT configure/send the dedicated test sink in this repair.

Do NOT enable:

```text
KR market TOP3
KR Price Structure
US Price Structure
```

This repair must finish first.

Expected after PASS:

```text
NEXT_ACTION =
RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT
```

---

# 35. TOP3 market-message isolation

The KR TOP3 sector work already passed.

Do not modify its ranking/renderer logic.

Hard:

```text
KR_TOP3_SECTOR_CODE_DIFF = 0
```

unless a shared utility requires a compatibility-only change.

If shared code changes:

prove exact TOP3 parity.

---

# 36. US isolation

Hard:

```text
US_PRICE_STRUCTURE_CODE_DIFF = 0
US_PRICE_STRUCTURE_ENABLED = 0
US_MARKET_DIGEST_CODE_DIFF = 0
```

---

# 37. Business / valuation isolation

Hard:

```text
BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF = 0
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
```

---

# 38. Runtime isolation

This repair is shadow/replay only.

Hard:

```text
CURRENT_USER_VISIBLE_RUNTIME_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
ARCHIVE_REWRITE = 0
PRODUCTION_FLAG_CHANGE = 0
```

---

# 39. Focused Track A tests

Required:

```text
daily 1200 canonical request
provider raw rows >0
cache hit / miss
wrong timeframe mapping
wrong parameter mapping
completed-bar filter
adjustment basis
short listing
provider true unavailable
partial current daily bar
```

Must include 7 KR controls.

---

# 40. Focused Track B tests

Required:

```text
NEAR tier
RELEVANT tier
LONG_HORIZON tier

internal nearest but remote
→ not user-facing 가까운

no valid near
→ no remote fill

valid weekly near
→ still visible

valid monthly near
→ visible only if canonical proximity allows

major structural remote
→ major/long-horizon label only

000660 broken fixture
005930 control
012450 control
003690 positive
005490 positive
010120 positive
086280 positive
```

---

# 41. Full regression

Required:

```text
Track A focused
Track B focused
7-ticker integration replay
Price Structure v3 regression cohort
family consensus tests
SR completeness/proximity tests
renderer integration tests
legacy technical detector tests

full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
```

Do not alter Public Action.

---

# 42. Architecture docs

Create/update:

```text
docs/architecture/KR_PRICE_STRUCTURE_DAILY_HISTORY.md
docs/architecture/SR_NEAREST_VS_USER_VISIBLE_PROXIMITY.md
docs/architecture/PRICE_STRUCTURE_V3_RENDERER_OWNERSHIP.md
docs/architecture/SR_PROXIMITY_RELEVANCE_GATE.md
```

Document:

```text
internal nearest vs user-facing near
coverage-aware rendering
LONG_HORIZON handling
daily history canonical path
validator provenance binding
```

---

# 43. Required reports

Create:

1. `docs/reports/20260827-kr-daily-ohlcv-zero-root-cause.md`
2. `docs/reports/20260827-kr-daily-ohlcv-before-after.md`
3. `docs/reports/20260827-kr-daily-history-provider-contract.md`
4. `docs/reports/20260827-kr-nearest-semantic-root-cause.md`
5. `docs/reports/20260827-kr-near-user-visible-policy.md`
6. `docs/reports/20260827-kr-remote-near-validator-root-cause.md`
7. `docs/reports/20260827-kr-price-structure-7ticker-replay.md`
8. `docs/reports/20260827-kr-price-structure-7ticker-render-diff.md`
9. `docs/reports/20260827-kr-price-structure-proximity-validator.md`
10. `docs/reports/20260827-kr-price-structure-safety-parity.md`
11. `docs/reports/20260827-kr-price-structure-repair-readiness.md`
12. `docs/reports/20260827-kr-price-structure-repair-artifact-index.md`

Machine-readable:

```text
docs/reports/20260827-kr-price-structure-7ticker-replay.json
docs/reports/20260827-kr-price-structure-repair-readiness.json
```

---

# 44. Required gates

Set exactly:

```text
DAILY_ZERO_ROOT_CAUSE =
PASS / FAIL

KR_DAILY_HISTORY_CONTRACT =
PASS / PARTIAL_SAFE / FAIL

UNEXPLAINED_DAILY_ZERO =
0 / NONZERO

SYNTHETIC_DAILY_BARS =
0 / NONZERO

FAKE_DAILY_FROM_WEEKLY_MONTHLY =
0 / NONZERO

UNVERIFIED_DAILY_PROVIDER_FALLBACK =
0 / NONZERO

PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION =
0 / NONZERO

LOOKAHEAD_LEAK =
0 / NONZERO

NEAREST_SEMANTIC_ROOT_CAUSE =
PASS / FAIL

NEAR_USER_VISIBLE_POLICY =
PASS / FAIL

LONG_HORIZON_RENDERED_AS_NEAR =
0 / NONZERO

REMOTE_ZONE_PROMOTED_AS_NEAR_FILL =
0 / NONZERO

RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY =
0 / NONZERO

NEAR_MAJOR_SEMANTIC_DUPLICATION =
0 / NONZERO

VALID_HIGHER_TF_NEAR_ZONE_DROPPED =
0 / NONZERO

FABRICATED_SR_FILL =
0 / NONZERO

ELIGIBILITY_IGNORES_MATERIAL_COVERAGE_FAILURE =
0 / NONZERO

REMOTE_NEAR_VALIDATOR_ROOT_CAUSE =
PASS / FAIL

RUN000660_OLD_RENDER_NEW_VALIDATOR =
FAIL_AS_EXPECTED / UNEXPECTED_PASS

FIB_FORCED_DUE_SR_REPAIR =
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

KR_TOP3_SECTOR_CODE_DIFF =
0 / NONZERO

US_PRICE_STRUCTURE_CODE_DIFF =
0 / NONZERO

US_PRICE_STRUCTURE_ENABLED =
0 / NONZERO

US_MARKET_DIGEST_CODE_DIFF =
0 / NONZERO

BUSINESS_THESIS_MUTATION =
0 / NONZERO

VALUATION_TEXT_DIFF =
0 / NONZERO

CURRENT_USER_VISIBLE_RUNTIME_DIFF =
0 / NONZERO

TELEGRAM_SEND =
0 / NONZERO

MANUAL_TASK =
0 / NONZERO

DB_MUTATION =
0 / NONZERO

OFFICIAL_ASSESSMENT_MUTATION =
0 / NONZERO

ARCHIVE_REWRITE =
0 / NONZERO

PRODUCTION_FLAG_CHANGE =
0 / NONZERO

CODE_CORRECTNESS =
PASS / FAIL

KR_PRICE_STRUCTURE_REPAIR =
REPLAY_PASS_READY_FOR_PREENABLE /
FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...
```

---

# 45. PASS rule

Set:

```text
KR_PRICE_STRUCTURE_REPAIR =
REPLAY_PASS_READY_FOR_PREENABLE
```

only if:

```text
daily zero root cause proven
daily collection repaired or genuinely fail-closed
no unexplained daily zero
no synthetic bars
LONG_HORIZON never renders as 가까운
remote nearest-fill eliminated
renderer-output validator catches old 000660 defect
positive near controls preserved
coverage-aware eligibility safe
Fib safety preserved
stored-rule ownership preserved
Price Structure remains not armed
TOP3 unchanged
US unchanged
P0 = 0
material P1 = 0
```

---

# 46. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

INTEGRATION_BRANCH = ...
INTEGRATION_SHA = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

TARGET_SESSION = 2026-08-27

DAILY_ZERO_ROOT_CAUSE = ...
DAILY_ZERO_ROOT_CAUSE_DETAIL = ...

KR_DAILY_HISTORY_CONTRACT = ...

000660_DAILY = requested ..., actual ..., completed ...
003690_DAILY = ...
005490_DAILY = ...
005930_DAILY = ...
010120_DAILY = ...
012450_DAILY = ...
086280_DAILY = ...

UNEXPLAINED_DAILY_ZERO = 0
SYNTHETIC_DAILY_BARS = 0
FAKE_DAILY_FROM_WEEKLY_MONTHLY = 0

NEAREST_SEMANTIC_ROOT_CAUSE = ...
NEAR_USER_VISIBLE_POLICY = ...

000660_INTERNAL_NEAREST_SUPPORT = ...
000660_INTERNAL_PROXIMITY_TIER = ...
000660_USER_VISIBLE_LABEL = ...

005930_INTERNAL_NEAREST_SUPPORT = ...
005930_INTERNAL_PROXIMITY_TIER = ...
005930_USER_VISIBLE_LABEL = ...

012450_INTERNAL_NEAREST_SUPPORT = ...
012450_INTERNAL_NEAREST_RESISTANCE = ...
012450_USER_VISIBLE_LABELS = ...

LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
VALID_HIGHER_TF_NEAR_ZONE_DROPPED = 0

REMOTE_NEAR_VALIDATOR_ROOT_CAUSE = ...
RUN000660_OLD_RENDER_NEW_VALIDATOR = FAIL_AS_EXPECTED

FIB_FORCED_DUE_SR_REPAIR = 0
UNSTABLE_FIB_EXPOSED = 0

CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

SEVEN_TICKER_REPLAY = ...

KR_TOP3_SECTOR_CODE_DIFF = 0
US_PRICE_STRUCTURE_CODE_DIFF = 0
US_PRICE_STRUCTURE_ENABLED = 0
US_MARKET_DIGEST_CODE_DIFF = 0

BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...

CURRENT_USER_VISIBLE_RUNTIME_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
ARCHIVE_REWRITE = 0
PRODUCTION_FLAG_CHANGE = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

KR_PRICE_STRUCTURE_REPAIR =
REPLAY_PASS_READY_FOR_PREENABLE /
FAIL

NEXT_ACTION =
RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 47. Mandatory completion ZIP

Create:

`20260827-kr-price-structure-daily-history-and-nearest-semantics-bounded-repair-bundle.zip`

Include:

```text
exact instruction
Track A/B/C notes
daily root cause
daily before/after
provider contract
nearest semantic root cause
near-user-visible policy
validator root cause
7-ticker replay MD/JSON
exact renderer diffs
safety parity
readiness
test/CI summary
artifact index
```

Exclude:

```text
secrets
auth headers
raw private account/sink IDs
tokens
hidden chain-of-thought
```

Compute SHA-256.

---

# 48. Final principle

There are two different questions:

```text
Which valid structural zone is mathematically nearest?
```

and:

```text
Is that zone actually close enough to tell the user "가까운 지지/저항"?
```

They are not the same.

Also:

```text
weekly/monthly data existing
```

does not excuse an unexplained:

```text
daily 1200 requested
daily 0 returned
```

Fix the daily data path first, bind user-facing proximity labels to actual proximity semantics, prove the
renderer validator on the broken 000660 fixture, then return to the KR TOP3 + Price Structure test-sink
pre-enable flow.
