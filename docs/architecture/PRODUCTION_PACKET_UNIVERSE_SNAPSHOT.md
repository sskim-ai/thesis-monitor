# Production Packet Universe Snapshot

Contract: `production-packet-universe-v1`.

Each monitoring run and AI packet owns an immutable snapshot with:

```text
market
session
cutoff
eligible_subjects[]
excluded_subjects[{ticker, market, onboarding_state, reasons[]}]
```

Eligibility requires monitoring intent, `ACTIVE`, `production_eligible`, and `activated_at <= cutoff`. Activation after cutoff is excluded from the current packet and becomes eligible in a later cycle.

The daily monitor captures its snapshot before collection. AI packet construction uses the source run's start time as cutoff, revalidates subject profile evidence, freezes the resulting list, and builds all stock registries from that list. A mutable global active query is not used downstream.
