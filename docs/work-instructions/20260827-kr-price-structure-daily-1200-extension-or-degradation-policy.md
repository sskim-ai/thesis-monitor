# thesis-monitor — KR Price Structure Daily 1200 Extension or Verified Degradation Policy
## Prove whether exact 1200 completed daily bars can be safely acquired
## If yes: bounded multi-window chaining
## If no: formalize provider-limited PARTIAL_SAFE=1000 without changing canonical budget
## No production enablement / no test-sink send

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `KR_PRICE_STRUCTURE_DAILY_1200_EXTENSION_OR_DEGRADATION_POLICY`
- Task class: `BOUNDED_DATA_CONTRACT_REPAIR`
- Source policy: preserve current supported/free production providers
- Price Structure v3: preserve `INTEGRATED_READY_NOT_ARMED`
- KR Price Structure production enablement: `OFF`
- US Price Structure production enablement: `OFF`
- Production Assist: preserve `OFF`
- Telegram send: `0`
- Manual production task: `0`
- DB / assessment mutation: `0`
- Production flag change: `0`
- Historical archive rewrite: `0`

### Latest reported lineage

Previous repair result:

```text
Instruction:
0a8dae7eeca7126844094f0aebcc7a7df0bea606

Base / operating:
43731f015901b96e2dee3af009b9e1d074382349

Track A:
da82d89c2e1c3bc125442128da1573d532263d74

Track B:
83f3d643bc2cb40d9039c1d965647d01a43769e2

Integrated code:
04fb7ad7646a55e03000134f50b3f402a6c49c87

Report / final main:
48a699798462639b27056523ef8fdd94b261092b
```

Operating was intentionally not promoted.

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve actual latest safe `origin/main`
4. verify `48a699...` lineage or its safe descendant
5. use latest safe main as base
6. do NOT promote operating in this task

---

# 1. Why this task exists

The previous repair correctly fixed:

```text
daily 0-bar failure
LONG_HORIZON mislabeled as 가까운
renderer validator false-negative
```

Root cause found:

```text
canonical requested daily bars = 1200
provider endpoint hard limit = 1000
requesting 1200 directly → HTTP 422
```

Current repaired behavior:

```text
requested = 1200
actual = 1000
completed = 1000
status = PARTIAL
reason = provider_limit
```

All seven KR controls passed semantic/renderer safety.

But the canonical internal history budget remains:

```text
Daily   = 1200
Weekly  = 600
Monthly = 300
```

Therefore one final question remains:

```text
Can the existing provider safely deliver the missing older 200+ completed daily bars
through supported pagination / date-window chaining?
```

If yes, implement it.

If no, formally prove the limitation and keep:

```text
canonical_target = 1200
provider_limited_actual = 1000
status = PARTIAL_SAFE/provider_limit
```

without silently redefining the budget.

---

# 2. Work split

This task MUST be splittable.

```text
Track A
provider capability audit

Track B
implement bounded multi-window chaining
OR
formalize verified degradation contract

Track C
7-ticker replay + price-structure parity/readiness
```

Track B must not choose implementation path until Track A evidence is complete.

Recommended branches:

```text
codex/kr-daily-1200-provider-capability-audit
codex/kr-daily-1200-extension-or-degradation
codex/kr-daily-1200-7ticker-replay
```

---

# 3. Track A — provider capability audit

Audit the exact KR daily OHLCV provider contract.

Determine whether the provider supports any canonical way to retrieve history older than the first 1000 rows through:

```text
date range parameters
cursor
continuation token
pagination
offset
before/end-date parameter
multiple non-overlapping windows
```

Do not guess.

Collect evidence from:

```text
provider client implementation
provider docs already in repo
successful local probe if safe
existing historical fetch code
```

No external paid provider addition.

---

# 4. Capability result enum

Set exactly one:

```text
EXACT_1200_SUPPORTED_BY_PAGINATION
EXACT_1200_SUPPORTED_BY_DATE_WINDOW
EXACT_1200_SUPPORTED_BY_EXISTING_CACHE_LAYER
PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW
PROVIDER_SUPPORT_UNVERIFIED
```

Hard gate:

`DAILY_1200_PROVIDER_CAPABILITY = one of above`

`PROVIDER_SUPPORT_UNVERIFIED` is not a PASS state.

---

# 5. Safe probe

If a safe read-only provider probe is needed, test only a small control set first:

```text
000660
005930
010120
```

Record:

```text
request parameters
returned count
oldest date
newest date
overlap with first window
duplicate count
ordering
adjustment basis
session basis
```

No repeated brute-force requests.

Respect provider rate limits.

---

# 6. Window chaining safety contract

If exact 1200 is supported by multiple requests, the final canonical daily series must satisfy:

```text
same security identity
same currency
same adjustment basis
same price basis
same session basis
strict date ordering
deduped by canonical trading date
no gap introduced by window boundary
no duplicate bar
no partial current bar counted as completed
```

Hard:

```text
WINDOW_CHAIN_SECURITY_BASIS_CONFLICT = 0
WINDOW_CHAIN_ADJUSTMENT_BASIS_CONFLICT = 0
WINDOW_CHAIN_DUPLICATE_BAR = 0
WINDOW_CHAIN_OUT_OF_ORDER = 0
WINDOW_CHAIN_PARTIAL_BAR_INCLUDED = 0
```

---

# 7. Preferred chaining shape

If provider contract allows it, prefer bounded minimal requests, e.g.:

```text
request 1:
latest 1000 completed daily bars

request 2:
older window ending strictly before oldest date from request 1
request enough rows to cover remaining 200 + small overlap/safety margin
```

Then:

```text
merge
dedupe by trading date
sort ascending/descending per canonical contract
trim to exact 1200 completed bars
```

Do not request thousands of unnecessary extra rows.

---

# 8. Overlap policy

If provider forces overlapping windows:

allow overlap only for validation/dedupe.

Do not double-count.

Hard:

`DUPLICATE_COMPLETED_BAR_AFTER_MERGE = 0`

---

# 9. Corporate action / adjusted-price basis

If the provider can return adjusted/unadjusted series:

the two windows must use the same basis.

Do not mix.

For splits/corporate actions:

the merged historical series must preserve the existing Price Structure security/price basis contract.

Hard:

```text
CORPORATE_ACTION_BASIS_CONFLICT = 0
ADJUSTED_RAW_PRICE_MIX = 0
```

---

# 10. Cache contract

If the existing cache layer already stores older bars beyond the provider's 1000 response:

audit whether the canonical service can safely combine:

```text
cached older completed history
+
fresh provider latest window
```

Only if:

```text
same provider/basis
cache freshness rules safe
no stale corporate-action basis
```

Do not silently stitch incompatible caches.

---

# 11. If exact 1200 is impossible

If Track A proves:

`PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW`

then do NOT add hacks.

Formalize a degradation contract:

```text
canonical requested history = 1200
provider hard limit = 1000
actual completed = up to 1000
status = PARTIAL_SAFE
reason = provider_limit
```

The system must explicitly preserve:

```text
requested_count = 1200
actual_count = 1000
provider_cap = 1000
```

Do not rewrite requested budget to 1000.

---

# 12. Degradation policy requirements

If exact 1200 is impossible, define:

```text
coverage_status = PARTIAL_SAFE
coverage_reason = provider_limit
canonical_target = 1200
provider_cap = 1000
```

Price Structure eligibility may proceed only under the existing coverage-aware rules.

No silent full-coverage claim.

Hard:

```text
PROVIDER_LIMIT_MISREPORTED_AS_FULL = 0
CANONICAL_DAILY_BUDGET_CHANGED_TO_1000 = 0
```

---

# 13. Degradation and renderer semantics

If provider-limited 1000 remains:

the renderer must not imply:

```text
full 1200-day tactical coverage
```

but may still render safe SR if eligibility/proximity rules pass.

No user-facing provider jargon is required unless material.

This is primarily an internal quality-state contract.

---

# 14. Track B implementation paths

Exactly one path:

## Path 1 — exact 1200 acquisition

Implement:

```text
bounded multi-window fetch
merge
dedupe
sort
completed-bar filter
trim exact 1200
coverage PASS
```

Expected:

```text
actual_count = 1200
completed_count = 1200
status = PASS
```

for long-listed 7 controls.

## Path 2 — verified degradation

If provider cannot safely provide older window:

implement/document:

```text
PARTIAL_SAFE/provider_limit
```

with all hard gates.

Do NOT create synthetic bars.

---

# 15. No synthetic history

Forbidden:

```text
weekly→daily resampling
monthly→daily resampling
interpolation
forward fill
duplicating old bars
synthetic weekend rows
using intraday snapshots as completed daily bars
```

Hard:

```text
SYNTHETIC_DAILY_BARS = 0
FAKE_DAILY_FROM_HIGHER_TF = 0
```

---

# 16. No unsupported provider switch

Do not add:

```text
paid provider
new undocumented provider
scraped web source
```

solely to get 200 extra bars.

Hard:

`UNSUPPORTED_PROVIDER_ADDED = 0`

---

# 17. Track C — 7 ticker replay

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

Target frozen session:

`2026-08-27`

Also append latest completed KR session if different at execution time, but do not overwrite the frozen regression.

---

# 18. Per-ticker coverage report

For each ticker:

```text
requested daily
provider cap
request count
raw returned total
deduped total
completed total
final actual
coverage status
oldest date
newest date
gap count
duplicate count
```

If exact 1200 path:

```text
final actual = 1200
```

for long-listed controls.

If degradation path:

```text
final actual = 1000
PARTIAL_SAFE/provider_limit
```

with proven provider limitation.

---

# 19. Price Structure parity replay

Recompute Price Structure using the resulting daily history.

For each ticker report:

```text
eligibility
nearest support
nearest resistance
major support
major resistance
proximity tier
active relevance
source timeframe
Fib state
exact rendered section
```

Do not assume zones remain identical after 1000→1200 extension.

---

# 20. Proximity regression

Preserve previous repair:

```text
LONG_HORIZON never renders as 가까운
remote fill prohibited
renderer-output validator active
```

Hard:

```text
LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
```

---

# 21. 000660 negative fixture

The old broken historical section must still:

`FAIL_AS_EXPECTED`

under the validator.

Hard:

`RUN000660_OLD_RENDER_NEW_VALIDATOR = FAIL_AS_EXPECTED`

---

# 22. Fib safety

If extended 1200 history changes pivots/family consensus:

rerun all existing Fib family-safety gates.

Do not automatically expose Fib.

Hard:

```text
UNSTABLE_FIB_EXPOSED = 0
FIB_ELIGIBILITY_CHANGED_WITHOUT_FAMILY_REVALIDATION = 0
```

---

# 23. Wave/current-cycle safety

More daily history must not cause old historical pivots to become a fake current W0 solely due to longer lookback.

Preserve:

```text
GRAND_CYCLE
vs
PRIMARY_CURRENT_CYCLE
```

Hard:

`OLD_HISTORY_PROMOTED_TO_CURRENT_CYCLE_WITHOUT_RULE = 0`

---

# 24. Weekly/monthly isolation

This task must not change canonical:

```text
Weekly = 600
Monthly = 300
```

Hard:

```text
WEEKLY_HISTORY_POLICY_DIFF = 0
MONTHLY_HISTORY_POLICY_DIFF = 0
```

---

# 25. KR TOP3 isolation

Hard:

`KR_TOP3_SECTOR_CODE_DIFF = 0`

---

# 26. US isolation

Hard:

```text
US_PRICE_STRUCTURE_CODE_DIFF = 0
US_PRICE_STRUCTURE_ENABLED = 0
US_MARKET_DIGEST_CODE_DIFF = 0
```

---

# 27. Runtime isolation

This task is non-production.

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

Operating must remain unchanged.

---

# 28. Focused tests

Required:

### Provider capability
```text
1000 max request
older-window request
overlap
no overlap
date boundary
short listing
provider unavailable
```

### Merge
```text
dedupe
sort
exact trim to 1200
corporate action basis
partial current bar
gap detection
```

### Degradation
```text
provider hard cap
requested remains 1200
actual 1000
PARTIAL_SAFE/provider_limit
not FULL
```

### Price Structure
```text
7 ticker replay
000660 negative fixture
near/major validator
Fib family safety if changed
```

---

# 29. Full regression

Required:

```text
focused tests
7-ticker replay
Price Structure v3 regression cohort
SR completeness/proximity
family consensus
renderer integration
legacy technical detector
full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
```

No Public Action change expected.

---

# 30. Documentation

Create/update:

```text
docs/architecture/KR_PRICE_STRUCTURE_DAILY_HISTORY.md
docs/architecture/OHLCV_PROVIDER_LIMIT_AND_WINDOW_CHAINING.md
docs/architecture/PRICE_STRUCTURE_COVERAGE_DEGRADATION.md
```

Document:

```text
canonical target 1200
provider cap
window chaining contract
merge/dedupe rules
degradation policy
coverage status semantics
```

---

# 31. Required reports

Create:

1. `docs/reports/20260827-kr-daily-1200-provider-capability.md`
2. `docs/reports/20260827-kr-daily-1200-window-probe.md`
3. `docs/reports/20260827-kr-daily-1200-merge-contract.md`
4. `docs/reports/20260827-kr-daily-1200-before-after.md`
5. `docs/reports/20260827-kr-daily-provider-limit-degradation-policy.md`
6. `docs/reports/20260827-kr-daily-1200-7ticker-coverage.md`
7. `docs/reports/20260827-kr-daily-1200-price-structure-replay.md`
8. `docs/reports/20260827-kr-daily-1200-price-structure-render-diff.md`
9. `docs/reports/20260827-kr-daily-1200-safety-parity.md`
10. `docs/reports/20260827-kr-daily-1200-readiness.md`
11. `docs/reports/20260827-kr-daily-1200-artifact-index.md`

Machine-readable:

```text
docs/reports/20260827-kr-daily-1200-7ticker-coverage.json
docs/reports/20260827-kr-daily-1200-readiness.json
```

---

# 32. Required gates

Set exactly:

```text
DAILY_1200_PROVIDER_CAPABILITY =
EXACT_1200_SUPPORTED_BY_PAGINATION /
EXACT_1200_SUPPORTED_BY_DATE_WINDOW /
EXACT_1200_SUPPORTED_BY_EXISTING_CACHE_LAYER /
PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW /
PROVIDER_SUPPORT_UNVERIFIED

DAILY_1200_IMPLEMENTATION_PATH =
EXACT_1200_CHAINING /
VERIFIED_PARTIAL_SAFE_1000 /
FAIL

WINDOW_CHAIN_SECURITY_BASIS_CONFLICT =
0 / NONZERO

WINDOW_CHAIN_ADJUSTMENT_BASIS_CONFLICT =
0 / NONZERO

WINDOW_CHAIN_DUPLICATE_BAR =
0 / NONZERO

WINDOW_CHAIN_OUT_OF_ORDER =
0 / NONZERO

WINDOW_CHAIN_PARTIAL_BAR_INCLUDED =
0 / NONZERO

DUPLICATE_COMPLETED_BAR_AFTER_MERGE =
0 / NONZERO

CORPORATE_ACTION_BASIS_CONFLICT =
0 / NONZERO

ADJUSTED_RAW_PRICE_MIX =
0 / NONZERO

SYNTHETIC_DAILY_BARS =
0 / NONZERO

FAKE_DAILY_FROM_HIGHER_TF =
0 / NONZERO

UNSUPPORTED_PROVIDER_ADDED =
0 / NONZERO

PROVIDER_LIMIT_MISREPORTED_AS_FULL =
0 / NONZERO

CANONICAL_DAILY_BUDGET_CHANGED_TO_1000 =
0 / NONZERO

KR_DAILY_1200_COVERAGE =
PASS_1200 /
VERIFIED_PARTIAL_SAFE_1000 /
FAIL

UNEXPLAINED_DAILY_SHORTFALL =
0 / NONZERO

LONG_HORIZON_RENDERED_AS_NEAR =
0 / NONZERO

REMOTE_ZONE_PROMOTED_AS_NEAR_FILL =
0 / NONZERO

RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY =
0 / NONZERO

RUN000660_OLD_RENDER_NEW_VALIDATOR =
FAIL_AS_EXPECTED / UNEXPECTED_PASS

UNSTABLE_FIB_EXPOSED =
0 / NONZERO

FIB_ELIGIBILITY_CHANGED_WITHOUT_FAMILY_REVALIDATION =
0 / NONZERO

OLD_HISTORY_PROMOTED_TO_CURRENT_CYCLE_WITHOUT_RULE =
0 / NONZERO

WEEKLY_HISTORY_POLICY_DIFF =
0 / NONZERO

MONTHLY_HISTORY_POLICY_DIFF =
0 / NONZERO

KR_TOP3_SECTOR_CODE_DIFF =
0 / NONZERO

US_PRICE_STRUCTURE_CODE_DIFF =
0 / NONZERO

US_PRICE_STRUCTURE_ENABLED =
0 / NONZERO

US_MARKET_DIGEST_CODE_DIFF =
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

KR_DAILY_1200_REPAIR =
REPLAY_PASS_READY_FOR_PREENABLE /
FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...
```

---

# 33. PASS path A — exact 1200

If provider safely supports older windows:

expected:

```text
DAILY_1200_IMPLEMENTATION_PATH = EXACT_1200_CHAINING
KR_DAILY_1200_COVERAGE = PASS_1200

7/7 long-listed controls:
actual/completed = 1200
or legitimate short-listing exception
```

Then:

`KR_DAILY_1200_REPAIR = REPLAY_PASS_READY_FOR_PREENABLE`

---

# 34. PASS path B — verified provider limit

If provider definitively cannot retrieve older window:

expected:

```text
DAILY_1200_PROVIDER_CAPABILITY = PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW
DAILY_1200_IMPLEMENTATION_PATH = VERIFIED_PARTIAL_SAFE_1000
KR_DAILY_1200_COVERAGE = VERIFIED_PARTIAL_SAFE_1000
```

Required:

```text
canonical target remains 1200
provider cap explicitly 1000
actual 1000
coverage PARTIAL_SAFE/provider_limit
all Price Structure safety gates PASS
```

This is also an acceptable PASS state.

---

# 35. FAIL state

Fail if:

```text
provider capability remains unverified
window chaining causes basis/session conflicts
duplicates/gaps cannot be resolved safely
1000 is silently relabeled full
canonical budget is reduced to 1000 without explicit policy
Price Structure proximity/Fib safety regresses
```

---

# 36. Next action

After either PASS path:

```text
NEXT_ACTION =
RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT
```

Do not enable here.

---

# 37. Completion response

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

DAILY_1200_PROVIDER_CAPABILITY = ...
DAILY_1200_IMPLEMENTATION_PATH = ...

PROVIDER_MAX_PER_REQUEST = ...
OLDER_WINDOW_SUPPORTED = ...
WINDOW_REQUEST_COUNT = ...

000660_DAILY = requested ..., actual ..., completed ..., status ...
003690_DAILY = ...
005490_DAILY = ...
005930_DAILY = ...
010120_DAILY = ...
012450_DAILY = ...
086280_DAILY = ...

KR_DAILY_1200_COVERAGE = ...
UNEXPLAINED_DAILY_SHORTFALL = 0

WINDOW_CHAIN_SECURITY_BASIS_CONFLICT = 0
WINDOW_CHAIN_ADJUSTMENT_BASIS_CONFLICT = 0
WINDOW_CHAIN_DUPLICATE_BAR = 0
WINDOW_CHAIN_OUT_OF_ORDER = 0
WINDOW_CHAIN_PARTIAL_BAR_INCLUDED = 0

DUPLICATE_COMPLETED_BAR_AFTER_MERGE = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
ADJUSTED_RAW_PRICE_MIX = 0

SYNTHETIC_DAILY_BARS = 0
FAKE_DAILY_FROM_HIGHER_TF = 0
UNSUPPORTED_PROVIDER_ADDED = 0

PROVIDER_LIMIT_MISREPORTED_AS_FULL = 0
CANONICAL_DAILY_BUDGET_CHANGED_TO_1000 = 0

SEVEN_TICKER_PRICE_STRUCTURE_REPLAY = ...

LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
RUN000660_OLD_RENDER_NEW_VALIDATOR = FAIL_AS_EXPECTED

UNSTABLE_FIB_EXPOSED = 0
FIB_ELIGIBILITY_CHANGED_WITHOUT_FAMILY_REVALIDATION = 0
OLD_HISTORY_PROMOTED_TO_CURRENT_CYCLE_WITHOUT_RULE = 0

WEEKLY_HISTORY_POLICY_DIFF = 0
MONTHLY_HISTORY_POLICY_DIFF = 0

KR_TOP3_SECTOR_CODE_DIFF = 0
US_PRICE_STRUCTURE_CODE_DIFF = 0
US_PRICE_STRUCTURE_ENABLED = 0
US_MARKET_DIGEST_CODE_DIFF = 0

CURRENT_USER_VISIBLE_RUNTIME_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
ARCHIVE_REWRITE = 0
PRODUCTION_FLAG_CHANGE = 0

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

KR_DAILY_1200_REPAIR =
REPLAY_PASS_READY_FOR_PREENABLE /
FAIL

NEXT_ACTION =
RERUN_KR_TOP3_PRICE_STRUCTURE_TEST_SINK_PREENABLEMENT /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 38. Mandatory completion ZIP

Create:

`20260827-kr-price-structure-daily-1200-extension-or-degradation-policy-bundle.zip`

Include:

```text
exact instruction
provider capability report
window probe
merge contract
before/after
degradation policy
7-ticker coverage MD/JSON
Price Structure replay
render diff
safety parity
readiness
test/CI summary
artifact index
```

Exclude:

```text
secrets
auth headers
raw account/sink IDs
tokens
hidden chain-of-thought
```

Compute SHA-256.

---

# 39. Final principle

The canonical engineering contract remains:

```text
Daily target = 1200
```

There are only two acceptable outcomes:

```text
A. safely acquire exact 1200 completed daily bars

or

B. prove the provider cannot expose older history,
   keep the target at 1200,
   and explicitly operate as PARTIAL_SAFE/provider_limit at 1000.
```

What is NOT acceptable:

```text
silently lowering the target to 1000
fabricating 200 bars
mixing incompatible history
or calling partial coverage full.
```

Close this one data-contract question, then return immediately to the KR TOP3 + Price Structure dedicated
test-sink pre-enable flow.
