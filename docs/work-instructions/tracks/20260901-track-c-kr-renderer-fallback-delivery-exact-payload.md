# Track C — Renderer / Fallback / Delivery / Exact Payload

For all KR stock messages and market message:
- selector route
- accepted renderer vs deterministic fallback
- explicit BUY/HOLD/SELL visibility
- final validator state
- fallback terminal reason
- delivery intent/sent/recorded
- exact rendered/outbound/archive/received hash
- duplicate/orphan/unowned retry

Fallback safety may PASS while V2 natural-live FAILS.

No production resend.
