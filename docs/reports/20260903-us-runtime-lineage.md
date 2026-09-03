# 2026-09-03 US Runtime Lineage

## Deployed Identity

| Item | Value |
| --- | --- |
| `origin/main` | `c1c43070cd944e273c53f952c29a768a33fefdee` |
| Operating HEAD | `c1c43070cd944e273c53f952c29a768a33fefdee` |
| Runtime SHA | `c1c43070cd944e273c53f952c29a768a33fefdee` |
| Policy / schema | `daily-review-v3.10` / `4` |
| Visible selector | `v2_accepted` |
| Accepted runtime | `v2-accepted-production-runtime-v2` |
| Directional balance | `v2-directional-balance-v1` |
| Runtime state | `codex-runtime-state-v1` |
| Network readiness | `codex-network-readiness-v1` |

The runtime includes the directional-balance and accepted-ownership commits,
same-evidence adjudication, local Codex state isolation, network readiness,
daily-review convergence, the four-tenor nominal Treasury block, and temporary
user-facing night-futures suppression.

The reporting branch is newer than the runtime because it contains evidence only.
At 07:51 KST the two existing services were restarted after a sandbox-isolated
loopback health check gave a false negative. Host-network health returned `ok`
before the 07:55 freeze; schedules and settings were not changed.

- `US_RUNTIME_LINEAGE = PASS`
- `PRODUCTION_ASSIST = OFF`
- `PUBLIC_ACTION = 0.4.5`
- `OUTPUT_SCHEMA = 4`

