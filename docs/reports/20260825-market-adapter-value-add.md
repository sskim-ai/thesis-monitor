# Market Adapter Value-Add Audit

## KR

The adapter correctly distinguishes the absence of KOSPI/KOSDAQ, breadth, sector/size, and
market-wide flow from overnight US context. No digest prose was enriched because no new domestic
Fact existed. `KR_MARKET_ADAPTER_VALUE_ADD = NO_MATERIAL_VALUE`.

## US

The adapter groups SPY/QQQ/IWM, SOXX, session role, and verified relative relations in one typed
sidecar. Those Facts already existed in run-37, while breadth and flow remained unavailable. No new
message information was added. `US_MARKET_ADAPTER_VALUE_ADD = NO_MATERIAL_VALUE`.

## Decision

`NO_MATERIAL_VALUE` is not failure: v1 establishes a safe acquisition/normalization boundary and a
natural canary surface. It does not pretend that schema normalization itself is new investment
insight. Future value depends on genuinely published compatible breadth, size, sector, or flow Facts.

