# Track D — Validator / Renderer / Delivery / LIVE_PASS

For market + every stock:
- renderer route
- explicit BUY/HOLD/SELL block
- terminal validator state
- fallback reason if any
- exact message hash
- outbound/archive/recorded payload equality
- exactly-once delivery
- duplicate/orphan/unowned retry

Natural LIVE_PASS requires the real production model/candidate/accepted/render path, not merely safe fallback.

No production resend.
