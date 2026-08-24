# 2026-08-24 KR Producer Trading-Day Natural Proof

`KR_PRODUCER_TRADING_DAY_NATURAL = FAIL`

## Normal-Day Path

| Stage | Evidence | Result |
|---|---|---|
| Role target | XKRX session `2026-08-24`, completed and production eligible | PASS |
| Analysis | run 36, 7/7 success | PASS |
| Packet identity | `2026-08-24-kr-run-36-b82af21dfde3` computed | PASS |
| Immutable packet persistence | denied by `shadow_cohort_activation_gate_failed` | FAIL |
| Packet-bound delivery intent | no KR delivery rows created | FAIL |
| Hold/session | none | NOT_OBSERVED |
| Primary claim | `no_eligible_unclaimed_packet` | FAIL |
| Retry | no pending AI delivery | safe no-op |
| Backup claim | `no_eligible_unclaimed_packet` | FAIL |
| Fallback | no held session | safe no-op |

The producer was invoked naturally at 16:05, 16:20, and 16:50. Every invocation resolved the correct same-day XKRX target. The first invocation completed analysis; later invocations reused it. All three stopped at the same activation gate.

```text
raw KR pending rows              0
deliverable KR pending rows      0
held-session pending rows        0
new orphan rows                  0
deliverable row without packet   0
```

Review-time provider calls were `0`. The exact natural provider-call count inside the producer run is not reconstructed from external providers. The separate non-trading-day natural proof remains pending.

Severity is material `P1`: normal-day analysis succeeded but the packet/delivery lifecycle did not begin. Fail-closed safety prevented a P0 data correctness event.

