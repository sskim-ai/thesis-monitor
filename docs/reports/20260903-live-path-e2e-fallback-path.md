# Live-Path E2E Fallback Path

The normal E2E sent AI `9/9`; the later fallback command returned `no_held_session` and sent zero.

Failure behavior is covered at two levels:

- Adapter failure test: accepted AI send fails before any row is sent; the deadline restores and
  sends exactly one deterministic set.
- Production-shape test: nine held rows with unavailable AI output send deterministic fallback
  `9/9`; a second deadline invocation sends zero.

Partial AI delivery remains fail-closed and does not mix AI and fallback. Lost pending ownership
cannot authorize fallback because analysis reuse preserves the owner.
