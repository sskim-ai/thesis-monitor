# KR Structured Acquisition Implementation

Implemented path:

```text
KRX exact-slot readiness
-> publication-state envelope
-> bounded complete-session collection
-> KOSPI/KOSDAQ normalized rows
-> separate and aggregate breadth
-> exact KOSPI/KOSDAQ index facts
-> hashed structured snapshot
-> point-in-time packet adapter
```

The KRX provider validates exact `BAS_DD`, six-character stock identity, duplicate identities, and
required broad-index identities. KOSPI and KOSDAQ breadth remain separately scoped. Official
reported trading value/volume are preserved, and market-wide participant flow is intentionally
absent.

The packet loader reads only an exact date before cutoff. Pending state reaches
`market-context-adapter-v1` as `MARKET_COMPLETED_PROVIDER_PENDING`; a complete snapshot reaches it
as `PROVIDER_COMPLETE`.

No KRX breadth number entered the immutable 8/25 packet or replay because provider publication was
pending. This is a production integration of safe future evidence, not an archive rewrite.

User-visible delivery mutation from replay: `0`.
