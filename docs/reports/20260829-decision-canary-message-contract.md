# Decision Canary Message Contract

The decision block is appended only to the four configured stock messages and contains:

- analytical `BUY / HOLD / SELL`
- `reasoning grade: very high`, separate from confidence
- confidence and its evidence-quality reason
- long-horizon classification, separate from short-term timing
- strongest bull and bear evidence
- decisive reason and key unknowns
- upgrade and downgrade conditions
- HOLD `why not BUY` and `why not SELL` boundaries
- non-order disclaimer

SELL is an analytical classification, not mandatory liquidation. The block emits no order,
position sizing, target, stop, per-share output, or unsupported number. Production canary prose
contains no numeric claims, so it cannot alter Price Structure numerics.

If generation, packet binding, validation, length, or combined quality fails, the exact original
stock message is restored and delivered through the existing path. Non-canary messages never enter
the decision renderer.
