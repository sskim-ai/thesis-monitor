# Finnhub Atomic Forward P/E Owner

REV44 extends the existing provider-native valuation owner, without creating an
EPS estimate, a denominator, or a new data acquisition route. The exact
`metric.forwardPE` field shares the existing metric/profile2 receipts, official
SEC security-identity binding, cutoff and raw hash validation. Existing PER/PBR
snapshots retain their original serialization and hashes.

Finite positive values qualify only for exact monitored direct securities.
Missing fields, sentinels and identity failures are separate typed outcomes.
ADR/home-security transfers remain blocked, even when the returned multiple is
positive. No alternate field, implied EPS, ADR conversion or repricing fallback
is permitted.

## Horizon Provenance

The user clarified that a Finnhub-owned field-specific definition of next-fiscal-
year analyst estimates permits `PROVIDER_FORWARD_HORIZON_FY1`,
`NEXT_FISCAL_YEAR`, `ANALYST_ESTIMATES`,
`QUALIFIED_PROVIDER_NATIVE_FY1_FORWARD_PE` and `fPER(FY1)`.

That path requires reviewed official provenance pinned in the owner. Caller
metadata, a user assertion, numerical similarity, and a synthetic test cannot
activate it. The official Basic Financials page, user-linked ownership page,
linked Swagger and official OpenAPI captured on 2026-10-02 do not reproduce that
definition. The pin remains empty, so real replay retains
`PROVIDER_FORWARD_HORIZON_UNSPECIFIED` and `Finnhub Forward P/E`.
The implementation supports the requested mapping, but FY1 activation is not
complete. Public-document SHA evidence is in the private REV44 result bundle.

## Consumption Boundary

The typed `FORWARD_PE` metric binds directly to the atomic provider snapshot.
It is a separate optional Pass-B NewBuyer/Holder calibration reference. Overall
direction, Core and Pass-A remain excluded. Existing valuation, risk and entry
policies are not replaced by a cheap/expensive threshold.

The deterministic valuation renderer owns numeric display and uses the verified
horizon label. Retrieval time never becomes metric-as-of. The date, accounting
basis, price date, or denominator period stays unknown when not provider-owned.

No model calls, live messages, production integration or deployment is included
in REV44. The historical sealed corpus is not promoted to current source data.
