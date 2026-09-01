# Packet-Owned Technical Context Contract

Contract: `packet-owned-technical-context-v1`

The internal artifact owns ticker/market/session/as-of, source/version, adjustment basis, currency,
security identity, D/W/M status and freshness, completed bars, counts, canonical features,
raw/feature fingerprints, acquisition telemetry, cautions, and failure reason.

The context ID is deterministic. Feature values come from the existing engine without AI
recalculation. The artifact is included only in the internal assessment serializer and review
packet; public `PriceContext` serialization and schema 4 are unchanged.

Legacy or missing packet context becomes subject-local `UNAVAILABLE`. No fresh decision-stage
network fallback exists.

`REPAIR_REMOVES_TECHNICAL_CONTEXT_FROM_V2 = 0`

`AI_CALCULATES_TECHNICAL_NUMERIC = 0`
