# Live Workload Coexistence Audit

| Gate | Value |
| --- | --- |
| contract | natural-live-workload-coexistence-guard-v1 |
| live_workload_contention_risk | 0 |
| natural_live_cancel_count | 0 |
| scheduler_mutation | 0 |
| shadow_pause_for_natural_live | 0 |
| status | PASS |

| Subject | Status | Result | Errors |
| --- | --- | --- | --- |
| c1-smoke | CONTINUE | CLI_PROCESS_SMOKE |  |
| c2-directional-us | CONTINUE | DIRECTIONAL_CORE |  |
| c3-directional-kr | CONTINUE | DIRECTIONAL_CORE |  |
| c4-shared-context-us4 | CONTINUE | DIRECTIONAL_CORE |  |
| c5-shared-context-kr4 | CONTINUE | DIRECTIONAL_CORE |  |
| c6-price-timing-us | CONTINUE | PRICE_TIMING |  |
| c7-price-timing-kr | CONTINUE | PRICE_TIMING |  |
| core-batch-01 | CONTINUE | DIRECTIONAL_CORE |  |

Machine proof: `20260906-synthetic-canary-resume-proofs/live-workload-coexistence-audit.json`.
