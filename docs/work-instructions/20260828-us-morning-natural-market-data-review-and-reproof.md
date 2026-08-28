# thesis-monitor — US Morning Natural Market Data Review + Reproof
## Target: 2026-08-27 completed US session
## Read-only natural production proof after US current-session evidence-consumption repair

## 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `US_MORNING_NATURAL_MARKET_DATA_REVIEW_AND_REPROOF`
- Task class: `READ_ONLY_NATURAL_PRODUCTION_REPROOF`
- Target market/session: `US / 2026-08-27`
- US Track A entering state: `REPLAY_PASS_NATURAL_REPROOF_PENDING`
- US Price Structure: preserve `OFF`
- Production Assist: preserve `OFF`
- Manual production task / Telegram send / DB / assessment mutation: `0`

Latest repaired US path must include the shared US market-digest-plan and evidence-utilization validator. Resolve actual latest safe `origin/main` and operating SHA before review. Do not change code, flags, packets, deliveries, or historical records.

## 1. Objective

Verify whether today's natural US morning message correctly used the completed 2026-08-27 session.

This review must prove:

```text
current run / current packet
exact target session
exactly-once delivery

SPY / QQQ / IWM / SOXX
RSP participation/style
US sector dispersion
Nasdaq exact-session breadth state
rates / VIX / WTI / FX temporal validity

shared market digest plan
AI/fallback evidence consumption
exact delivered message
material evidence utilization

US Price Structure leak = 0
```

If a material defect appears: `REPORT → CLASSIFY → STOP`. Do not repair here.

## 2. Natural run / current packet

Find the naturally scheduled US morning run for target session `2026-08-27`.

Collect:

```text
scheduler identity
natural start/end KST
run ID
producer SHA / operating SHA
target session
packet ID / created_at / ready_at
claim owner
route = AI / deterministic_fallback
AI start/end if used
fallback deadline
delivery IDs / receipt IDs
```

Hard gates:

```text
CURRENT_PACKET_CLAIM = PASS
STALE_PENDING_PACKET_CLAIM = 0
WRONG_TARGET_SESSION_PACKET = 0
OLD_PACKET_CURRENT_CANARY_BUDGET_CONSUMPTION = 0
WAIT_CURRENT_PACKET_POLICY = PASS
PRIMARY_BACKUP_OWNERSHIP = PASS
EXACTLY_ONCE = PASS
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
```

If the natural run is not observed: `US_MORNING_NATURAL = NOT_OBSERVED` and stop.

## 3. Core current-session ETF evidence

Collect production-packet values for:

```text
SPY
QQQ
IWM
SOXX
RSP
```

Per item record:

```text
value / close
backend-owned session return
observation date
source
state
packet presence
AI evidence presence
fallback presence
final message usage
```

Canonical states:

```text
CURRENT_DIRECTIONAL
CURRENT_LEVEL_ONLY
PUBLICATION_PENDING
SOURCE_UNAVAILABLE
```

Hard gates:

```text
US_CORE_ETF_SESSION_MATCH = PASS
CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = PASS
CORE_ETF_ALL_DROPPED = 0
LEVEL_ONLY_DIRECTION_LEAK = 0
```

The digest need not print every ETF number, but the current-session market cross-section must survive.

## 4. RSP participation/style

RSP is equal-weight participation/style evidence, not exchange breadth.

Record:

```text
value / return
observation date
state
shared-plan selection state
final message usage
```

Hard gates:

```text
RSP_STATE_VALID = PASS
RSP_STATE_PROPAGATION = PASS / PARTIAL_SAFE
RSP_AS_EXCHANGE_BREADTH = 0
RSP_DIRECTION_INVENTED = 0
SELECTED_RSP_SLOT_UNCONSUMED = 0
```

## 5. US sector context / dispersion

Audit the current production-supported sector ETF set, at minimum:

```text
XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY
```

Per sector record:

```text
observation date
state
backend-owned return
packet presence
AI/fallback presence
message usage
```

Also extract:

```text
safe directional sector count
strongest safe sector
weakest safe sector
dispersion magnitude
shared-plan selection reason
```

Hard:

```text
US_SECTOR_CONTEXT_PROPAGATION = PASS / PARTIAL_SAFE
CURRENT_DIRECTIONAL_DROPPED = 0
LEVEL_ONLY_PROMOTED_TO_DIRECTIONAL = 0
SOURCE_UNAVAILABLE_AS_CURRENT = 0
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0
MATERIAL_SECTOR_EXTREMES_ALL_DROPPED = 0
SELECTED_SECTOR_DISPERSION_UNCONSUMED = 0
```

Do not dump every sector into the final digest.

## 6. Nasdaq exact-session breadth

Check the official Nasdaq breadth source for exact session `2026-08-27`.

Record:

```text
official source
latest published source session
exact-session availability
advances / declines / unchanged if canonical
publication state
```

If exact-session breadth is not available:

`NASDAQ_BREADTH = PUBLICATION_PENDING`

Hard:

```text
NASDAQ_BREADTH_BOUNDARY = PASS
PRIOR_BREADTH_AS_CURRENT = 0
PUBLICATION_PENDING_AS_ZERO = 0
FABRICATED_EXCHANGE_BREADTH = 0
TRADING_ACTIVITY_AS_BREADTH = 0
```

RSP must not substitute for Nasdaq breadth.

## 7. Macro temporal audit

Audit at minimum:

```text
US 10Y nominal yield
US 10Y real yield
VIX
WTI / oil
USD/KRW or existing production FX context
DXY/liquidity item if already supported
```

Per item record:

```text
value
backend-owned change
observation date
temporal role
today_signal_eligible
source
packet presence
final message usage
```

Canonical roles only:

```text
CURRENT_OBSERVATION
PRIOR_MARKET_SESSION
REFERENCE_LAGGING
STALE_FOR_DAILY_SIGNAL
UNAVAILABLE
```

Hard:

```text
MACRO_TEMPORAL_BOUNDARY = PASS
SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
FX_SESSION_BASIS_CONFLICT = 0
STALE_MACRO_AS_CURRENT = 0
TEMPORAL_LANGUAGE_WITHOUT_CURRENT_EVIDENCE = 0
```

## 8. Shared US market-digest plan

Collect the shared-plan projection for:

```text
CURRENT_MARKET
PARTICIPATION_STYLE
SECTOR_DISPERSION
BREADTH_STATE
MACRO_CONTEXT
```

For each slot report:

```text
state
selected evidence refs
safe omission reason
AI consumption
fallback consumption
final digest consumption
```

Hard gates:

```text
US_SHARED_MARKET_DIGEST_PLAN = PASS
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS / NOT_USED
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
AI_FALLBACK_MARKET_PLAN_DIVERGENCE = 0
AI_FALLBACK_MARKET_SEMANTIC_PARITY = PASS
AI_FALLBACK_TEMPORAL_PARITY = PASS
AI_MACRO_ONLY_SELECTION_WITH_CURRENT_MARKET = 0
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0
CORE_MARKET_SLOT_UNCONSUMED = 0
```

The repaired system must not collapse back to a macro-only digest when safe current-session market evidence exists.

## 9. Exact message + evidence utilization

Return the exact persisted natural US digest and compare:

```text
persisted payload
delivery payload
receipt-linked payload
```

Hard:

`US_EXACT_MESSAGE_PAYLOAD_MATCH = PASS`

Create an evidence-utilization table using:

```text
MESSAGE_USED
MESSAGE_OMITTED_SAFE
MESSAGE_OMITTED_MATERIAL_LOSS
```

Required rows:

```text
SPY
QQQ
IWM
SOXX
RSP
selected strongest sector
selected weakest sector
Nasdaq breadth state
10Y nominal
10Y real
VIX
WTI
FX
```

Hard:

```text
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
BROAD_RISK_ON_WITHOUT_SUPPORT = 0
UNSUPPORTED_BREADTH_CLAIM = 0
```

## 10. Isolation

US Price Structure remains OFF.

Hard:

```text
US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_LEAK = 0
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
BUSINESS_THESIS_MUTATION_FROM_REVIEW = 0
PRODUCTION_MUTATION_FROM_REVIEW = 0
```

## 11. Data completeness matrix

Create a machine-readable matrix with:

```text
fact family
symbol/series
source
target session
actual observation date
value
return/change
state
temporal role
packet present
AI evidence present
fallback present
message used
cross-check state
```

This is the primary extraction artifact.

## 12. Required reports

Create:

```text
docs/reports/20260828-us-morning-natural-run-identity.md
docs/reports/20260828-us-morning-current-packet-ownership.md
docs/reports/20260828-us-morning-exactly-once.md
docs/reports/20260828-us-morning-core-etf-data.md
docs/reports/20260828-us-morning-rsp-participation.md
docs/reports/20260828-us-morning-sector-context.md
docs/reports/20260828-us-morning-sector-dispersion.md
docs/reports/20260828-us-morning-nasdaq-breadth.md
docs/reports/20260828-us-morning-macro-temporal-audit.md
docs/reports/20260828-us-morning-shared-market-plan.md
docs/reports/20260828-us-morning-ai-fallback-parity.md
docs/reports/20260828-us-morning-exact-message.md
docs/reports/20260828-us-morning-evidence-utilization.md
docs/reports/20260828-us-morning-message-quality.md
docs/reports/20260828-us-morning-safety-parity.md
docs/reports/20260828-us-morning-natural-reproof-readiness.md
docs/reports/20260828-us-morning-artifact-index.md
```

Machine-readable:

```text
docs/reports/20260828-us-morning-data-completeness-matrix.json
docs/reports/20260828-us-morning-natural-reproof-readiness.json
```

## 13. Final gates

Set at minimum:

```text
US_MORNING_NATURAL =
LIVE_PASS /
MATERIAL_P1_FOUND_STOP /
P0_FOUND_STOP /
NOT_OBSERVED

TARGET_SESSION = 2026-08-27

CURRENT_PACKET_CLAIM = PASS
EXACTLY_ONCE = PASS
CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = PASS
RSP_STATE_VALID = PASS
US_SECTOR_CONTEXT_PROPAGATION = PASS / PARTIAL_SAFE
NASDAQ_BREADTH_BOUNDARY = PASS
MACRO_TEMPORAL_BOUNDARY = PASS
US_SHARED_MARKET_DIGEST_PLAN = PASS
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS / NOT_USED
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
US_EXACT_MESSAGE_PAYLOAD_MATCH = PASS

CORE_ETF_ALL_DROPPED = 0
RSP_AS_EXCHANGE_BREADTH = 0
MATERIAL_SECTOR_EXTREMES_ALL_DROPPED = 0
SELECTED_SECTOR_DISPERSION_UNCONSUMED = 0
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0
CORE_MARKET_SLOT_UNCONSUMED = 0
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
STALE_MACRO_AS_CURRENT = 0
US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_LEAK = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
```

Set `LIVE_PASS` only if the natural run is observed, current-session market evidence actually owns the digest, temporal boundaries pass, exactly-once passes, material information loss is zero, and P0/P1 = 0/0.

If material failure:

`NEXT_ACTION = BOUNDED_US_MARKET_REPAIR`

If PASS:

`US_TRACK_A = LIVE_PASS`

## 14. Completion response

Return:

```text
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

NATURAL_RUN_ID = ...
TARGET_SESSION = 2026-08-27
PACKET_ID = ...
PACKET_READY_AT = ...
CLAIM_OWNER = ...
ROUTE = ...

SPY = ...
QQQ = ...
IWM = ...
SOXX = ...
RSP = ...
RSP_STATE = ...

SECTOR_DIRECTIONAL_COUNT = ...
SECTOR_STRONGEST = ...
SECTOR_WEAKEST = ...

NASDAQ_BREADTH_STATE = ...
NASDAQ_BREADTH_SOURCE_SESSION = ...

NOMINAL_10Y_OBSERVATION_DATE = ...
NOMINAL_10Y_TEMPORAL_ROLE = ...
REAL_10Y_OBSERVATION_DATE = ...
REAL_10Y_TEMPORAL_ROLE = ...
VIX_OBSERVATION_DATE = ...
VIX_TEMPORAL_ROLE = ...
WTI_OBSERVATION_DATE = ...
WTI_TEMPORAL_ROLE = ...
FX_OBSERVATION_DATE = ...
FX_TEMPORAL_ROLE = ...

CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = ...
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = ...
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = ...

US_EXACT_MESSAGE_PAYLOAD_MATCH = ...
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_LEAK = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

US_MORNING_NATURAL = ...
US_TRACK_A = ...

NEXT_ACTION =
NO_ACTION /
WAIT_FOR_NEXT_NATURAL_US_MORNING /
BOUNDED_US_MARKET_REPAIR /
REVIEW_MASTER_GATES

ZIP = ...
ZIP_SHA256 = ...
```

## 15. Mandatory completion ZIP

Create:

`20260828-us-morning-natural-market-data-review-and-reproof-bundle.zip`

Include the exact instruction, all reports above, completeness matrix JSON, readiness JSON, exact message, evidence-utilization map, and artifact index.

Exclude secrets, auth headers, account identifiers, private tokens, and hidden chain-of-thought.

Final principle:

```text
2026-08-27 completed session
→ current packet
→ current market cross-section
→ RSP participation/style
→ material sector dispersion
→ safe breadth boundary
→ temporally valid macro
→ one exact natural message
```

The current-session market must own the message. Macro is context, not a replacement.
