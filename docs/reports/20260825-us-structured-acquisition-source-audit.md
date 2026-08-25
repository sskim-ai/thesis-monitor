# US Structured Acquisition Source Audit

The existing local OHLCV analyst is the only configured structured US price source used here.
Massive is unconfigured and received zero requests.

The bounded audit retrieved completed 8/21 and 8/24 bars for RSP plus XLB, XLC, XLE, XLF, XLI,
XLK, XLP, XLRE, XLU, XLV, and XLY. Any 8/25 partial/current-session row was excluded. The production
provider registry now includes those symbols alongside SPY, QQQ, IWM, and SOXX.

Safe new contexts:

- RSP: equal-weight price proxy and deterministic RSP-minus-SPY relation.
- Sector ETFs: 11 explicit sector price proxies, separate from actual sector breadth.
- Session: completed US regular session only.

Still unavailable:

- Exchange-wide advance/decline breadth.
- Market-wide participant flow.
- KR-style foreign/institution/retail mapping.

Provider calls: `24` local requests, `24` successes, `0` post-connection failures. New paid source:
`0`.

Decision: `US_STRUCTURED_ACQUISITION = PARTIAL`; the added style/sector evidence is production-safe,
while breadth and participant flow remain fail-closed.
