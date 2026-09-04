# 2026-09-04 V2 Timeout and Interruption Matrix

| Scenario | Terminal state | Accepted | Delivery | Compatibility eligible | Result |
|---|---|---:|---:|---:|---|
| Normal KR generation | `ACCEPTED` | 1 | 1 | 0 | PASS |
| Command timeout | `TIMED_OUT` | 0 | 0 | 1 | PASS |
| Authorized cancellation | `INTERRUPTED` | 0 | 0 | 1 | PASS |
| Task cancellation | `INTERRUPTED` | 0 | 0 | 1 | PASS |
| Lost fencing ownership | `INTERRUPTED` | 0 | 0 | 1 | PASS |
| Unexpected runtime defect | `FAILED` | 0 | 0 | 1 | PASS |
| Late suppression after accepted artifact | `ACCEPTED` preserved | 1 | unchanged | 0 | PASS |

The production timeout remains `1800` seconds per signed-in model invocation.
Tests use controlled clocks and doubles; production timeout configuration was
not shortened for test convenience.
