# Free Analyst Adaptive Canary Enablement

- Activation time: `2026-08-25 12:44 KST`
- Configuration mechanism: operating `.env`, existing supported Settings contract
- Repository code change for activation: `0`
- Main/operating SHA: `cd0fb79a6925d75029debb24f00d1a4c7495aa75`

## Before And After

| Setting | Before | After |
| --- | --- | --- |
| `AI_REVIEW_MODE` | `shadow` | unchanged |
| `AI_REVIEW_PILOT_ENABLED` | `true` | unchanged |
| `FREE_ANALYST_ADAPTIVE_ENABLED` | `false` default | `true` |
| `FREE_ANALYST_ADAPTIVE_MODE` | `current` default | `free_analyst_adaptive_canary` |
| Market/stock/total max | `1/2/3` default | `1/2/3` explicit |
| Full Free Analyst mode | OFF | OFF |
| Production Assist governance | OFF | OFF |

The correct thesis-monitor API alone was restarted and `/health` passed. Runtime Settings report
`kill_switch_open=true` and `canary_armed=true`. Inventory, cash-flow, Pilot, schedules, Public
Action, schema, Open Research, Trade AR, database, and stored assessments were unchanged.

- `CANARY_ENABLEMENT=PASS`
- `FREE_ANALYST_ADAPTIVE_CANARY=ENABLED_PENDING_NATURAL`
- `FREE_ANALYST_ADAPTIVE_FULL=OFF`
- `COMMON_AI_CORE_V1=INTEGRATED_CANARY_PENDING_NATURAL`
- Manual Scheduled Task / Telegram / DB mutation: `0 / 0 / 0`

At activation time the first eligible KR and US natural runs had not occurred. No run was
manufactured for proof.
