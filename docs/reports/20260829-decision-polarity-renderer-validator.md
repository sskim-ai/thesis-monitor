# Decision Polarity Renderer and Validator

Renderer and validator consume the same `buy_case_evidence`, `sell_case_evidence`, and
`neutral_context_evidence` plan.

Rejected controls cover wrong-side polarity, directional DATA_QUALITY, duplicate cross-side refs,
missing directional ownership, timing-only sole ownership, and artifact block tampering. The
artifact loader regenerates the deterministic block and requires exact equality.

- Free-form sentiment polarity inference: `0`
- Validator polarity recomputation from prose/support order: `0`
- Unowned visible polarity evidence: `0`
- Same ref in BUY and SELL: `0`
- Neutral fact forced into BUY/SELL: `0`
- Timing evidence escalated to fundamental ownership: `0`

`BUY_SELL_POLARITY_MESSAGE_QUALITY = PASS`
