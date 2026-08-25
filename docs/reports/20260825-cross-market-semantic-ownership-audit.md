# Cross-Market Semantic Ownership Audit

| Metric | Count |
| --- | --- |
| messages | 22 |
| stock/entity messages | 20 |
| global/shared market messages | 2 |
| entity-specific unique claims | 64 |
| global/shared unique claims | 2 |
| entity-owner mismatches | 0 |
| ticker-owner mismatches | 0 |
| market-owner mismatches | 0 |
| packet-owner mismatches | 0 |
| support-ref owner mismatches | 0 |
| industry-context mismatches | 0 |
| thesis-driver mismatches | 0 |
| fact-ref mismatches | 0 |
| relation-owner mismatches | 0 |
| expectation mismatches | 0 |

All 22 immutable KR/US messages share the common implementation. No entity-specific ref is treated as global, and every mismatch target is `0`.

`CROSS_MARKET_OWNERSHIP_AUDIT = PASS`
