# KR Market Context Adapter

## Source Policy

The KR adapter prefers KRX/exchange evidence, existing validated KR price and investor-flow Facts,
OpenDART for issuer facts, and official statistics. Source hints are policy metadata, not packet
facts or hard-coded conclusions.

## Semantics

- Local indices are KOSPI and KOSDAQ only.
- Breadth requires exact advance, decline, unchanged, eligible-universe, date, and source identity.
- Market-wide foreign, institution, and retail flow requires KRW monetary units plus market scope.
- Existing stock 1D/5D/20D quantity flows remain stock positioning and are never combined with
  market-wide KRW flow.
- Provider publication distinguishes complete, market-complete/provider-pending, and Unknown.
  Missing post-close rows are not interpreted as zero.

## Kiwoom Extension

`kiwoom-kr-market-context-v1` supplies a validated `MarketCrossSection` to the existing adapter.
The adapter does not know Kiwoom TR shapes; it consumes normalized index, breadth, sector/size,
market-flow, and deterministic concentration records. Direct cross-section records take priority
over duplicate generated Facts by logical identity.

The runtime boundary is:

```text
official Kiwoom REST TR
-> secret-safe client
-> Kiwoom normalizer and reconciliation
-> structured-market-context-v1 persistence
-> existing market-context-adapter-v1
-> existing packet and reasoning paths
```

The integration is best effort. An unavailable token, incomplete page chain, invalid session,
unknown unit, duplicate normalized security, or semantic mismatch cannot block packet creation.
Missing remains Unknown and is never converted to zero.

## Current Coverage

The 2026-08-25 completed-session probe validates KOSPI/KOSDAQ index, scoped breadth, KOSPI size,
63 non-composite sector/size rows, and six market-wide participant-flow facts. KOSDAQ flow
concentration is eligible; KOSPI concentration is blocked by aggregate-versus-stock reconciliation.

Status: `PARTIAL`, safe for selective production integration. KRX publication telemetry remains
independent and is not overwritten by Kiwoom state.
