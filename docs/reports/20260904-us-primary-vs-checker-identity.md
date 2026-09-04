# US Primary vs Checker Identity

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Classification

`PRIMARY_CHECKER_LOOKUP_IDENTITY_MATCH = UNKNOWN`  
`PRIMARY_CHECKER_MISMATCH_CLASS = UNKNOWN`

No checker lookup occurred, so an identity comparison cannot truthfully pass or fail.

| Field | Primary actual | 08:20 checker expected | Match |
| --- | --- | --- | --- |
| market | `us` | `None` | NOT_APPLICABLE |
| business_date | `2026-09-04` | `None` | NOT_APPLICABLE |
| run_id | `55` | `None` | NOT_APPLICABLE |
| packet_id | `2026-09-04-us-run-55-54cd536c6e4d` | `None` | NOT_APPLICABLE |
| claim_id | `1e008869-f2e3-4a52-ba32-fe7b31bf472e` | `None` | NOT_APPLICABLE |
| runtime_namespace | `/Users/sskim/Codex/thesis-monitor` | `None` | NOT_APPLICABLE |
| artifact_path | `data/ai_review/outbox/2026-09-04-us-run-55-54cd536c6e4d--daily-review-v3.10--dc747fff8565--1e008869-f2e3-4a52-ba32-fe7b31bf472e.json.tmp` | `None` | NOT_APPLICABLE |
| heartbeat_key | `None` | `None` | NOT_IMPLEMENTED |

The 08:30 claim path did match the primary packet, market, policy, knowledge hash, final output name, and target session. It intentionally replaced only claim ownership after lease expiry.
