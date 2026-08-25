# KR/US Structured Acquisition Readiness

| Gate | State | Reason |
| --- | --- | --- |
| Source capability audit | PASS | configured free/official paths verified |
| KR acquisition | PARTIAL | exact 8/25 publication pending; fail-closed |
| US acquisition | PARTIAL | RSP/sectors safe; breadth/flow unavailable |
| Provenance/time/unit | PASS | exact dates, cutoff, basis, source refs |
| Partial provider failure | PASS | packet continues with Unknown |
| Schema commonality | PASS | both markets use `market-context-adapter-v1` |
| User-visible mutation from replay | 0 | archive-only replay |

Passing partial components are promotion-eligible. KRX same-day publication timing, US breadth,
and US participant flow are P2 gaps and do not block the safe structured subset.

Decision: structured acquisition component `PROMOTE_SAFE_PARTIAL`.
