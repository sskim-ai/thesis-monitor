# 2026-09-04 US Shared V2 Regression

`US_SHARED_PATH_CHANGED = YES`

The final timeout-scoped implementation used the immutable run-51 packet and
regular candidate in an isolated TEST environment. Signed-in Codex xhigh ran
five batches for `2371.70` seconds overall, crossed the 30-minute aggregate
boundary, renewed the lease 40 times, and produced an accepted claim-bound V2
artifact for all 14 stocks.

| Gate | Result |
|---|---|
| V2 terminal state | `ACCEPTED` |
| Explicit V2 stock accepted | `14` |
| Model/validator not-ready | `0` |
| TLS UnknownIssuer | `0` |
| Market sent | `0` |
| Explicit V2 stock sent | `0` |
| Fallback / duplicate | `0 / 0` |

## Why delivery stopped

The post-V2 combined runtime-message quality gate rejected two portfolio-wide
typed prose skeletons:

- `supply_analysis`: the same volume-participation sentence on 14 stocks
- `price_positioning`: the same current-price sentence on 14 stocks

All 14 messages were present. Numeric labels, final Korean language checks,
numeric repetition, numeric ownership, and primary RR ownership passed. The
combined quality receipt alone failed, so the canary preserved existing
delivery and sent nothing to either TEST or production.

The prior integrated run-55 TEST had sent `1+14`, but it used a different
accepted model sample. A prior pass cannot certify every newly generated model
sample. Repeating until a favorable sample appears would hide the variance, so
this run was not retried.

The blocker is independent of timeout, lease, fencing, and signal ownership.
It must be handled as a separate bounded quality repair without weakening the
threshold. This work item therefore does not satisfy the required US `1+14`
delivery gate.
