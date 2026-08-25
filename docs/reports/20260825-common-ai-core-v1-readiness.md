# Common AI Core v1 Readiness

- Instruction commit: `3df40de53cf35ff5c47d662e0a14fbf9e30be3f7`
- Implementation base: `f7d2552185ff2ff6d932337e7555ce02f87fa613`
- US packet: `2026-08-25-us-run-37-7e04812311c2`
- KR packet: `2026-08-24-kr-run-36-e4ac1c029c06`
- Provider recollection: `0`
- Manual Telegram / Task / DB mutation: `0 / 0 / 0`

## Gates

- `FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION = PASS`
- `FREE_ANALYST_PRODUCTION_FACT_BOUNDARY = PASS`
- `ADAPTIVE_RENDERER_PRODUCTION = PASS`
- `PRODUCTION_FALLBACK_PARITY = PASS`
- `PRODUCTION_DELIVERY_INTEGRITY = PASS`
- `OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0`
- `PRODUCTION_ASSIST_CONTROL_PLANE = A`
- `FREE_ANALYST_ADAPTIVE_CANARY = READY_NOT_ARMED`

## Replay

- US: `14/14`
- KR: `8/8`
- Human-quality classification: `{'MATERIAL_IMPROVEMENT': 21, 'NO_MEANINGFUL_CHANGE': 1}`
- Combined hard safety errors: `0`
- Full-cohort runtime quality: `FAILED` (P2 broad repetition; no full rollout)
- Limited-canary scoped runtime quality: `PASSED`

Validation and exact-SHA CI fields are finalized in the validation report after implementation commit.
