# TRACK A — US Morning Market Pipeline Repair + 2026-08-25 Replay

## Scope

This track is independent from KR afternoon review and Price Structure v3.

Target:

```text
US completed session = 2026-08-25
```

Repair and validate:

```text
1. current packet claim / WAIT_CURRENT_PACKET / fallback ownership
2. RSP + XLE/XLF structured context propagation
3. macro temporal render boundary
4. exact replay market digest
5. exactly-once safety
```

## A1. Current packet claim

Canonical current identity:

```text
market = US
target session = 2026-08-25
current natural run/newest finalized packet
```

If current expected packet is not ready:

```text
WAIT_CURRENT_PACKET
```

Never claim a prior-run pending packet as current.

Required:

```text
STALE_PENDING_PACKET_CLAIM = 0
OLD_PACKET_CURRENT_CANARY_BUDGET_CONSUMPTION = 0
WAIT_CURRENT_PACKET_PATH = PASS
PRIMARY_BACKUP_OWNERSHIP = PASS
FALLBACK_DEADLINE_SAFETY = PASS
```

Measure separately:

```text
packet_ready_at
AI_start_at
AI_end_at
fallback deadline

packet readiness delay
true inference latency
renderer/validator latency
```

Do not change grace without evidence.

## A2. Ownership / exactly once

Test:

```text
prior pending + current missing
current appears
deadline fallback
primary/backup race
current appears after fallback
```

Hard:

```text
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
```

## A3. Structured US context states

Canonical states:

```text
CURRENT_DIRECTIONAL
CURRENT_LEVEL_ONLY
PUBLICATION_PENDING
SOURCE_UNAVAILABLE
```

Audit:

```text
RSP
XLE
XLF
all currently supported sector ETFs
XLC unavailable control if observed
Nasdaq breadth
```

RSP:

```text
equal-weight participation evidence
NOT exchange breadth
```

For 2026-08-25 the current validation control is:

```text
SPY positive
QQQ/SOXX stronger
RSP weak/negative

→ narrow technology/semiconductor-led rally
```

Use actual packet facts.

Hard:

```text
RSP_STATE_PROPAGATION = PASS
XLE_XLF_STATE_PROPAGATION = PASS
LEVEL_ONLY_DIRECTION_LEAK = 0
PUBLICATION_PENDING_AS_ZERO = 0
UNAVAILABLE_AS_CURRENT = 0
RSP_AS_EXCHANGE_BREADTH = 0
```

## A4. Nasdaq breadth

If official 2026-08-25 breadth is absent:

```text
PUBLICATION_PENDING
```

No synthetic advances/declines.

RSP may still support participation interpretation.

## A5. Macro temporal boundary

Use existing canonical roles:

```text
CURRENT_OBSERVATION
PRIOR_MARKET_SESSION
REFERENCE_LAGGING
STALE_FOR_DAILY_SIGNAL
UNAVAILABLE
```

Every summary item must bind:

```text
observation date
temporal role
today_signal_eligible
```

Controls:

```text
VIX may be 2026-08-24
nominal/real yield may be 2026-08-24
WTI may be 2026-08-18
```

Hard:

```text
SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_VIX_AS_TODAY = 0
PRIOR_YIELD_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
STALE_MACRO_AS_CURRENT = 0
AI_FALLBACK_TEMPORAL_POLICY_DIVERGENCE = 0
```

## A6. Target replay

Immutable/read-only:

```text
target = 2026-08-25
Telegram = 0
DB mutation = 0
assessment mutation = 0
```

Generate:

```text
before digest
after digest
exact diff
facts used
temporal roles
structured-state utilization
```

Hard:

```text
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
BROAD_RISK_ON_WITHOUT_BREADTH_SUPPORT = 0
US_MARKET_DIGEST_BREADTH_BOUNDARY = PASS
```

## A7. Price Structure isolation

Hard:

```text
PRICE_STRUCTURE_V3_DIFF = 0
BUSINESS_THESIS_MUTATION = 0
```

## A8. State

Replay PASS:

```text
US_MORNING_MARKET_MESSAGE_PIPELINE =
REPLAY_PASS_NATURAL_REPROOF_PENDING
```

Do not claim LIVE_PASS until a post-repair natural US run is observed.

## A9. Required reports

Create:

```text
20260826-us-current-packet-claim-root-cause.md
20260826-us-current-packet-claim-policy.md
20260826-us-fallback-ownership-timeline.md
20260826-us-rsp-sector-propagation-audit.md
20260826-us-market-context-state-audit.md
20260826-us-macro-temporal-render-audit.md
20260826-us-summary-item-temporal-binding.md
20260826-us-2026-08-25-replay.md
20260826-us-2026-08-25-exact-digest-diff.md
20260826-us-market-digest-evidence-utilization.md
20260826-us-market-message-safety-parity.md
20260826-us-market-message-readiness.md
```

## A10. Completion

Return all key gates, implementation/final SHA, CI, and:

```text
NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_MORNING /
BOUNDED_REPAIR
```
