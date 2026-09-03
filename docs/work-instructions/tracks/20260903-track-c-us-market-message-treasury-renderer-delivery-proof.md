# Track C — US Market / Treasury / Renderer / Delivery Proof

Market:
- SPY / QQQ / IWM / SOXX / RSP
- relative/sector internals
- nominal Treasury 3Y / 5Y / 10Y / 30Y
- latest safe yield + previous valid observation delta in bp

Night futures:
must be absent from user-facing message while date/session convention is pending.

Stock renderer:
- explicit BUY/HOLD/SELL
- visible BUY:SELL balance
- common order/auto-trading disclaimer remains absent
- no internal contradictions

Delivery:
exact payload / exactly once / duplicate 0.

Create the completion package immediately after the US run is terminal.
Do not wait for KR.
