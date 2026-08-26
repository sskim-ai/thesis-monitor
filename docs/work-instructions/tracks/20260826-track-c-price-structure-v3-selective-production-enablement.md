# TRACK C — Price Structure v3 Selective Production Enablement
## Start only after Master Track A/B gates pass
## No calculation redesign

## Scope

Enable the already validated Price Structure v3 renderer selectively in production.

Do not modify:

```text
OHLCV acquisition
pivot calculation
wave-degree engine
family consensus
nearest/major SR
confluence math
display formatter
legacy detector
stored price-rule persistence
```

unless production wiring reveals a direct defect.

## C1. Required base

Branch from the latest safe main AFTER Track A implementation/report and Track B report merges.

Record:

```text
TRACK_C_BASE_SHA
```

Do not use the older 33f822... base if main has advanced.

## C2. Preconditions

Required:

```text
Track A deterministic/replay gates PASS
Track A P0/P1 = 0/0

Track B natural LIVE_PASS
Track B P0/P1 = 0/0

Price Structure =
INTEGRATED_READY_NOT_ARMED

Price Structure P0/P1 =
0/0
```

If not:

```text
DO_NOT_ARM
```

## C3. Runtime eligibility

Use existing runtime eligibility.

```text
ELIGIBLE
→ nearest SR
→ major structural SR
→ safe family-stable Fib/SR if material

ELIGIBLE_SR_ONLY
→ deterministic SR only

OMIT_PRICE_STRUCTURE
→ no v3 block

BLOCKED
→ no v3 block
→ message still renders
```

Do not hard-code prior eligibility counts.

## C4. Initial scope

Initial production scope:

```text
current monitored universe only
```

Do not expand automatically to arbitrary unregistered/new tickers.

## C5. User-facing renderer requirements

Must preserve:

```text
company header
current SR vs stored monitoring rules separation
nearest vs major distinction
Fib extension range when material
no empty Fib line on SR-only
no stale legacy technical prose
no unsupported target/stop
```

## C6. Safety

Hard:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
FABRICATED_SR_FILL = 0
FALLBACK_TIMEFRAME_RELABEL = 0

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0

STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0
COMPANY_HEADER_CHANGED_BY_LEGACY_SUPPRESSION = 0

UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0
```

## C7. Feature flag / rollback

Use existing config/feature-flag ownership.

Required:

```text
OFF
→ exact old production behavior

ON + eligible
→ v3 section

ON + SR-only
→ SR-only section

ON + omit/blocked
→ safe old behavior
```

Rollback must be one bounded flag/config change.

Do not create a redundant rollout framework.

## C8. Unrelated runtime policies

Must remain unchanged:

```text
Production Assist = OFF
Free Analyst canary limits unchanged
US packet ownership unchanged
KR scheduler unchanged
Open Research production integration unchanged
Trade AR unchanged
```

Hard:

`UNRELATED_RUNTIME_POLICY_DIFF = 0`

## C9. Pre-arm replay

Before arming:

```text
full KR monitored universe replay
full US monitored universe replay
```

Use latest safe completed sessions.

Compare:

```text
feature OFF
feature ON
```

Only price-structure section should differ.

Hard:

```text
BUSINESS_TEXT_DIFF_FROM_ARMING = 0
VALUATION_TEXT_DIFF_FROM_ARMING = 0
MARKET_DIGEST_DIFF_FROM_ARMING = 0
```

## C10. Arm

Only after all tests/CI pass.

Record:

```text
feature state
armed_at
operating SHA
scope
rollback path
```

Do not manually send a message.

## C11. Natural proof

Wait for the next natural KR/US messages.

Do not manually trigger.

If not observed:

```text
PRICE_STRUCTURE_PRODUCTION =
ARMED_AWAITING_NATURAL_PROOF
```

If observed, audit exact message/delivery.

## C12. Natural control review

Where naturally present:

```text
000660
012450
010120
MU
TSM
SNDK
TSLA
RXRX
```

Verify:

```text
eligible/SR-only behavior
numeric provenance
stored-rule ownership
Fib visibility
header preservation
exactly once
```

## C13. Required reports

Create:

```text
20260826-price-structure-selective-enablement-policy.md
20260826-price-structure-selective-enablement-off-on-replay.md
20260826-price-structure-selective-enablement-safety.md
20260826-price-structure-selective-enablement-runtime-config.md
20260826-price-structure-selective-enablement-readiness.md
20260826-price-structure-selective-enablement-natural-proof.md
20260826-price-structure-selective-enablement-artifact-index.md
```

## C14. Gates

Set:

```text
SELECTIVE_ELIGIBILITY_ROUTING = PASS
MONITORED_UNIVERSE_SCOPE = PASS

FEATURE_OFF_PARITY = PASS
FEATURE_ON_REPLAY = PASS

BUSINESS_TEXT_DIFF_FROM_ARMING = 0
VALUATION_TEXT_DIFF_FROM_ARMING = 0
MARKET_DIGEST_DIFF_FROM_ARMING = 0

UNRELATED_RUNTIME_POLICY_DIFF = 0

KR_REPLAY = PASS
US_REPLAY = PASS

PRICE_STRUCTURE_PRODUCTION =
INTEGRATED_READY_NOT_ARMED /
ARMED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

## C15. Completion

Return:

```text
TRACK_C_BASE_SHA = ...
IMPLEMENTATION_SHA = ...
FINAL_MAIN = ...
OPERATING = ...

FEATURE_STATE = ...
ARMED_AT = ...
ROLLOUT_SCOPE = ...
ROLLBACK = ...

SELECTIVE_ELIGIBILITY_ROUTING = ...
FEATURE_OFF_PARITY = ...
FEATURE_ON_REPLAY = ...

KR_REPLAY = ...
US_REPLAY = ...

PRICE_STRUCTURE_PRODUCTION = ...

KR_NATURAL_PROOF = ...
US_NATURAL_PROOF = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

NEXT_ACTION =
WAIT_FOR_NATURAL_PROOF /
NO_ACTION /
BOUNDED_REPAIR
```
