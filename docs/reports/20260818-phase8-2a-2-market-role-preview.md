# Phase 8.2A.2 Market Role Preview

Date: 2026-08-18
Scope: hypothetical time-slot policy examples; no Telegram send

## Scenario A: Same-Day Ready

Condition: the 16:05 exact-slot bundle is `PROVIDER_COMPLETE` after its multi-session gate.

Market assembly:

```text
KR spot indices -> KOSPI/KOSDAQ breadth -> selected sector price proxy
-> global/night context -> portfolio transmission boundary
```

The 16:05 KR close message may use same-session KRX facts. This scenario is not supported by current
evidence.

## Scenario B: Next-Morning Only

Condition: 16:05 remains pending, while 08:05 reliably has the prior completed session.

Market assembly:

```text
16:05 KR close: existing current provider/context, no stale KRX promotion
08:05 morning: prior KR spot index and breadth, labeled as the prior completed session
```

KRX can become a next-morning primary candidate without becoming a same-day close primary. This
scenario has not yet been observed.

## Scenario C: T+1 Only

Condition: the prior session becomes complete only after the next-morning decision window.

Market assembly:

```text
Live Telegram path: no KRX current snapshot
Archive/reconciliation: authoritative KRX session snapshot after completion
```

KRX remains useful for historical truth and reconciliation, but not for time-critical current
messages. This scenario has not yet been observed.

## Human Boundary

All scenarios retain exact session labels. Night futures remain forward opening context, KRX spot
facts remain completed-session context, sector returns remain price proxies rather than breadth, and
unsupported market-wide investor flow remains absent rather than zero. No scenario changes a
company thesis from market context alone.
