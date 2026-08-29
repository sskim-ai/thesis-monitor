# Decision Validator Ownership

Contract: `decision-validator-ownership-v1`.

The validator consumes the same structured plan used by the renderer. It verifies ticker, stored horizon, exact evidence refs, selected category ownership, opposing evidence, unsupported calculations, trading/order semantics, and numeric eligibility.

Exact numbers are never accepted from free prose. The AI selects up to three canonical technical Fact refs; the backend formats them. Validation failure omits the decision and does not fabricate a deterministic BUY/HOLD/SELL fallback.
