# Multi-Timeframe Price Structure Evidence Packet

## Contract

`PriceStructureEvidencePacket` is the typed shadow boundary. It contains security identity,
currency, current adjusted price, as-of/cutoff dates, adjustment basis, evidence hash, and three
independent timeframe slots.

Each slot contains:

- fixed analytical role;
- `AVAILABLE` or `INSUFFICIENT_STRUCTURE`;
- confirmed major pivot evidence with deterministic IDs;
- separately owned support/resistance candidates with deterministic IDs;
- compact omission count.

Raw OHLCV rows and provider taxonomy noise are not sent to the selector. Canonical evidence IDs,
prices, confirmation dates, and source references are sufficient for validation and calculation.

## Compact Mode

Compact mode retains all confirmed major pivots and Strong/Medium SR candidates. Full-debug mode
also retains Weak zones, but the selector cannot promote Weak-only noise. Compact and full selection
signatures must match before readiness.

## Identity

Pivot identity binds ticker, timeframe, kind, date, confirmation date, price, and adjustment basis.
Zone identity binds ticker, timeframe, role, bounds, and source pivot dates. The packet hash is a
canonical sorted JSON hash over the complete typed evidence.

## Unsupported State

Insufficient evidence remains explicit per timeframe. A missing monthly slot never causes weekly or
daily evidence to be copied or relabeled.
