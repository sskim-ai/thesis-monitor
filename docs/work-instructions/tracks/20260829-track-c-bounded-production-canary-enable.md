# Track C — Bounded Production Canary Enable

Preconditions:
- fresh four-subject decision packets PASS
- BUY fixture PASS/explicit limitation
- test-sink exact payload PASS
- P0/P1 = 0/0

Enable:
DECISION_ENGINE_STATE = CANARY

for the exact 2 KR + 2 US subjects only.

Do not manually blast production messages.
Observe next normal production cycles.

Rollback is one-step to TEST_SINK_READY.
