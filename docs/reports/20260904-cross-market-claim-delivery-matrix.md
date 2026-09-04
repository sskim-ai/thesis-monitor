# 2026-09-04 Cross-Market Claim and Delivery Matrix

| Scenario | Expected | Result |
|---|---|---|
| Healthy primary heartbeat, backup arrives | backup no-op | PASS |
| Primary expires, backup claims | one fenced recovery | PASS |
| Stale primary finalizes after reclaim | rejected | PASS |
| Finalizer wins packet lock | reclaim blocked | PASS |
| Retry crosses process boundary | persisted exact payload reused | PASS |
| Fallback sent before late AI | late AI archive-only | PASS |
| Terminal AI failure | one deterministic fallback set | PASS |
| Network retry | same persisted payload, bounded | PASS |
| Runtime quality rejection | one fallback set, no AI send | PASS |
| Validated artifact tampered | retry send rejected | PASS |
| Analysis reuse | pilot delivery owner preserved | PASS |

The explicit matrix is backed by `15 passed` tests. In both actual integrated TEST E2Es, healthy-primary backup reclaim, late-AI duplicate, and duplicate Telegram sends were all `0`.
