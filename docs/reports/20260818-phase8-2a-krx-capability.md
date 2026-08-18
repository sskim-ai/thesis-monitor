# Phase 8.2A KRX Open API Capability

Date: 2026-08-18
Status: EXPERIMENTAL / ARCHIVE ONLY
Provider session: 2026-08-14
Main merge: 0
Operating deployment: 0

## Official Evidence

- KRX Open API service catalog: https://openapi.krx.co.kr/contents/OPP/INFO/service/OPPINFO004.cmd
- KRX Open API terms: https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO002.jsp
- Authentication: `AUTH_KEY` request header.
- Official limit: 10,000 requests per key per day. No rate-limit headers were returned by the audited endpoints.
- Official daily APIs provide 2010-and-later statistical data. The approved endpoints returned exact 2026-08-14 rows.

## Capability Matrix

| Capability | Status | Evidence |
|---|---|---|
| major_indices | SUPPORTED | KOSPI and KOSDAQ series daily index APIs |
| listed_security_universe | SUPPORTED | KOSPI and KOSDAQ issue basic-information APIs |
| daily_close_return_volume_value | SUPPORTED | KOSPI and KOSDAQ daily trading APIs |
| common_share_breadth | PARTIAL | Deterministic calculation from official issue and daily-trading rows |
| market_wide_investor_flow | UNSUPPORTED | No market-wide investor-flow service in the approved Open API catalog |
| sector_participation | PARTIAL | KOSPI 200 and KOSDAQ 150 sector index returns |
| security_type_policy | PARTIAL | Security group, certificate type, listing date, and KOSDAQ segment metadata |

## Exact Boundary

- KOSPI/KOSDAQ daily rows and issue basic information support deterministic common-share breadth.
- KOSPI, KOSPI 200, KOSDAQ, and KOSDAQ 150 identities are explicit.
- KOSPI 200 and KOSDAQ 150 industry-index returns are `sector_price_proxy`, not security-level sector breadth.
- The approved Open API catalog does not provide market-wide foreign/institution/retail net-buy facts. Missing flow remains unavailable, never zero.
- No explicit suspension flag is present. Otherwise eligible zero-volume rows remain in the unchanged denominator and the coverage stays `partial`.

## Universe Policy

Eligible denominator:

```text
KOSPI or KOSDAQ daily row
+ matching six-character official short code
+ SECUGRP_NM = 주권
+ KIND_STKCERT_TP_NM = 보통주
- SPAC official segment/name marker
+ LIST_DD strictly before the requested session
```

Preferred shares, REITs, infrastructure funds, investment companies, foreign shares, depositary receipts, SPACs, and same-session new listings are excluded. ETF/ETN/ELW are separate KRX services and never enter this denominator.

## Live Audit

- Credentialed read-only discovery calls: 31; canonical snapshot calls: 6; credential exposure: 0.
- Pagination: none for the six audited endpoints.
- Canonical snapshot latency: 5,191.6 ms total.
- Current 2026-08-18 probe returned HTTP 200 with zero rows, so it was not promoted. The archive-only snapshot uses exact available session 2026-08-14; this is not an automatic stale fallback policy.
