# US Market Context Adapter

## Source Policy

The US adapter reuses validated index/sector Facts and official Fed, Treasury, BLS, BEA, SEC, issuer,
exchange, and regulator evidence already supported by the repository. It adds no paid provider and
does not duplicate the existing macro temporal layer.

## Semantics

- SPY, QQQ, and IWM are local market index/style proxies.
- SOXX is a `sector_price_proxy`, not semiconductor breadth.
- Breadth is published only from an eligible security-level cross-section.
- KR-style foreign/institution/retail cash-equity flow is unsupported and cannot be invented.
- Premarket, regular, after-hours, and closed are normalized through the existing exchange calendar.
- A post-close event cannot explain the preceding regular-session move.

## Current Coverage

The immutable 2026-08-25 US run-37 packet normalizes SPY, QQQ, IWM, SOXX, and two verified
relative-return relations. Breadth, size context, concentration, and market-wide participant flow
remain unavailable. The adapter does not consume nominal-rate, FX, oil, or volatility Facts because
those remain owned by the existing macro temporal contract.

Status: `PARTIAL`, safe for a bounded structured sidecar natural canary. Missing fields remain
Unknown and cannot block fallback delivery.

