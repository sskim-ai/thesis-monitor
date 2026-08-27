# Track B — KR Price Structure v3 Selective Stock Message

## Scope

Enable Price Structure v3 only for the current monitored KR universe after preflight.

Do not enable US.

## Runtime policy

```text
ELIGIBLE
→ nearest support/resistance
→ major structural SR when available
→ safe/material Fib/SR only

ELIGIBLE_SR_ONLY
→ deterministic SR only

OMIT / BLOCKED
→ no Price Structure block
```

## User-facing ownership

Keep separate:

```text
📐 현재 가격 구조
🧭 기존 등록 가격 규칙
```

No target/stop invention.

## Hard gates

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
```

## Audit

Run all current monitored KR tickers.

Record exact eligibility and renderer output.

Do not hard-code old replay counts.
