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

`MACRO_CONTEXT` is optional. Generic zero-change or no-material-change evidence is classified as
`OMITTED_SAFE_NOT_MATERIAL`, so the entire section disappears. A selected neutral macro item must
have one supported canonical macro Fact, an exact observation date, an allowed temporal role, a
specific series label, and a grammar-safe semantic rendering. The final renderer rebuilds this
sentence from the Fact and does not trust stored `claim_text`.

An incomplete five-index tuple fails closed to the prior renderer. A stored legacy digest plan is
revalidated at render time so equity-relative facts cannot leak into `MACRO_CONTEXT`.

The exact Telegram response payload is validated separately under
`us-morning-exact-payload-quality-v1`; report claims are valid only when that validator payload SHA
matches the received payload SHA.
