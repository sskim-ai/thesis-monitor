# US Morning Message Layout

Contract: `us-morning-full-message-v1`

The US morning digest has one deterministic section order:

```text
HEADER
INDEX_BLOCK
MARKET_INTERNAL
NIGHT_FUTURES (only when safe current directional facts exist)
MACRO_CONTEXT (only when material and temporally valid)
NEXT_CHECK
```

`INDEX_BLOCK` always owns the current completed-session returns for SPY, QQQ, IWM, SOXX, and
RSP. `MARKET_INTERNAL` owns the RSP participation interpretation and backend-selected strongest
and weakest sector returns. Adaptive prose may replace only the bounded next-check block; it may
not remove, reorder, or recalculate deterministic market numerics.

An incomplete five-index tuple fails closed to the prior renderer. A stored legacy digest plan is
revalidated at render time so equity-relative facts cannot leak into `MACRO_CONTEXT`.
