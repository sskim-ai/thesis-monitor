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

## Current Coverage

The immutable 2026-08-25 KR run-38 packet contains no local index, breadth, size/sector, or
market-wide flow Facts. The adapter therefore returns an empty local context with explicit gaps.
Overnight US proxy Facts remain in the existing macro context and are not relabeled as KR local
market structure.

Status: `PARTIAL`. This is fail-closed and does not block deterministic delivery. KRX publication
telemetry remains an independent observation track.

