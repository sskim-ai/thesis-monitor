# KR/US Structured Source Capability Matrix

Audit date: `2026-08-25 KST`. New paid source/API/subscription: `0`.

| Market | Source | Configured | Verified capability | Target-session state | Production role |
| --- | --- | --- | --- | --- | --- |
| KR | KRX Open API | yes | KOSPI/KOSDAQ broad indices and separate stock-row breadth | 8/25 four endpoints HTTP 200, rows 0 | exact-slot fail-closed acquisition |
| KR | Kiwoom | no | not queried | unavailable | none |
| US | existing OHLCV analyst | yes | SPY/QQQ/IWM/SOXX, RSP, 11 sector ETFs | 8/24 completed bars available | structured price-proxy source |
| US | Massive | no | not queried | unavailable | none |

KR historical 8/24 proof returned 942 KOSPI stock rows, 1,823 KOSDAQ stock rows,
51 KOSPI index rows, and 40 KOSDAQ index rows. The exact 8/25 probe remained
`MARKET_COMPLETED_PROVIDER_PENDING`; missing rows were not converted to zero.

US supports equal-weight/style and sector price proxies. Exchange-wide breadth and participant flow
remain unavailable. US participant flow is explicitly unsupported rather than mapped to KR actor
semantics.

Decision: `STRUCTURED_SOURCE_CAPABILITY_AUDIT = PASS`.
