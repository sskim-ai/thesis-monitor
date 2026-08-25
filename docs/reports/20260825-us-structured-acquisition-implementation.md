# US Structured Acquisition Implementation

The existing OHLCV macro provider now acquires RSP and all 11 SPDR sector ETFs. Existing scheduler,
API key, source client, rate behavior, and macro observation storage are reused.

`market-intelligence-v1` emits:

- `market_style` for RSP.
- `market_style_relative` for RSP minus SPY.
- `market_sector` for the explicit ETF proxies.
- source-aware numeric semantics and labels.

`market-context-adapter-v1` exposes RSP as `equal_weight_price_proxy`, IWM as
`small_cap_price_proxy`, and sector ETFs as `sector_price_proxy`. A price proxy is never relabeled
as actual exchange breadth. Relative returns require identical source dates and exact deterministic
arithmetic.

The immutable run-37 packet was not rewritten. The 8/24 RSP/sector bars are separately labeled
`SUPPLEMENTAL_STRUCTURED_EVIDENCE` for replay. Production will obtain the same classes through the
existing scheduled macro collection.

US breadth: `UNKNOWN`. US participant flow: `UNAVAILABLE_NOT_SUPPORTED`.
