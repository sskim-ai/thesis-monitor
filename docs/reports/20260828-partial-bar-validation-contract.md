# Partial-Bar Validation Contract

Partial OHLC is admitted only when open/high/low/close are finite, high/low contain open and close,
volume is nonnegative when present, the observation falls inside the canonical bar period, and
security/currency/adjustment basis is complete. The engine keeps partial bars out of pivots,
historical S/R, boxes, Fib, and wave anchors.

All visible provisional bindings carry observation timestamp, bar start, expected close, PARTIAL
state, source refs, currency, security basis, and adjustment basis. Replay metadata errors:
`0`; malformed partial bars used: `0`. Unit controls reject malformed OHLC and
negative volume.
