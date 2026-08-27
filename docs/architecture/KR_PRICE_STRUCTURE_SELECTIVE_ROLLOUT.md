# KR Price Structure Selective Rollout

## Boundary

`kr-price-structure-selective-rollout-v1` is the KR-only eligibility and composition layer over the
existing Price Structure v3 engine, family-consensus filter, and renderer. It is limited to numeric
KR tickers in the monitored packet. US, foreign, and unmonitored subjects fail closed.

## Eligibility

| State | Rendering |
| --- | --- |
| `ELIGIBLE` | Current price, nearest/major support and resistance, and family-stable Fib/SR confluence |
| `ELIGIBLE_SR_ONLY` | Current price and nearest/major support and resistance; no Fib placeholder |
| `OMIT_PRICE_STRUCTURE` | No current-structure section; the message continues |
| `BLOCKED` | No current-structure section; the message continues with the denial reason retained internally |

A selection error, unresolved completed-session context, or partial-bar pivot confirmation blocks
the section. Nearest SR is required. Fib is optional and is admitted only when the existing family
consensus says the confluence is safe.

## Ownership

The backend owns OHLCV history, pivots, zones, nearest/major classification, Fib family consensus,
formatting, and numeric fact refs. AI may interpret the registered structure but cannot calculate a
technical price or reorder the zones. `📐 현재 가격 구조` is current completed-session evidence;
`🧭 기존 등록 가격 규칙` remains stored monitoring history. Neither may impersonate the other.

The runtime context uses longer KR histories only while its guard is enabled: daily 1,200, weekly
600, and monthly 300 observations. The context target is the latest completed KR session, never a
partial current bar.

## Rollout

`KR_PRICE_STRUCTURE_V3_ENABLED` defaults OFF. Archive replay and local rendering may exercise the
code with an explicit override. Runtime activation requires a non-production dedicated Telegram
sink, exact-payload and exactly-once receipt proof, zero open P0/P1, and a separate KR-only action.
No fallback-only or production-recipient test is an acceptable substitute.
