# 2026-09-04 US Natural Run Lineage

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Verdict

The authoritative producer was monitor run `55`, which completed `14/14` and persisted `2026-09-04-us-run-55-54cd536c6e4d` at `08:06:44.108602 KST`. Primary and backup worked on that same immutable packet and the same policy/knowledge output generation, but with distinct claim IDs.

| Component | Identity | Active interval KST | Result |
| --- | --- | --- | --- |
| Producer | `daily_us / run 55` | `08:05:31.682759` to `08:06:41.488234` | success 14/14 |
| Packet | `2026-09-04-us-run-55-54cd536c6e4d` | persisted `08:06:44.108602` | ready for AI |
| Primary | `1e008869-f2e3-4a52-ba32-fe7b31bf472e` | `08:15:45.571` to `08:36:03.855` | 15-part candidate, rejected stale |
| Backup | `15e1258f-7654-47d5-a58d-23d22310dedd` | `08:30:15.594` to `08:42:26.746` | 15-part reused candidate, validation rejected |
| Delivery | notification IDs `497..511` | `08:40:06.363050` to `08:40:21.613300` | deterministic fallback 15/15 |

No accepted AI artifact existed. The final user-visible owner was the fallback worker, not either AI automation.
