# Common AI Core v1 Validation

- Instruction commit: `3df40de53cf35ff5c47d662e0a14fbf9e30be3f7`
- Implementation commit: `4bcf117fa36d9a74c45e6f9c2626e38e07e52bd3`
- GitHub Actions run: `32803786800`
- Actions Test/Lint: `PASS / PASS`

## Local Validation

- Ported-unit and focused suites: `102 passed`, then `148 passed`
- Focused integration and regression set: `182 passed`
- Full pytest: `1510 passed, 1 existing deprecation warning`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Project docs/config checks: `16 passed`
- Public Action version: `0.4.5` unchanged
- Public Action operation IDs: `20/20` unique
- Daily output schema: `4` unchanged

## Replay And Safety

- US run-37 Free Analyst/Adaptive: `14/14`, `14/14`
- KR immutable replay: `8/8`
- Limited canary simulation: `3` selected, scoped runtime quality `PASS`
- Fact mismatch, unsupported numeric, unsupported causality, temporal violations, Trade AR leak,
  hidden arithmetic, external unsourced facts, and material information loss: all `0`
- Fallback parity and delivery integrity: `PASS`
- Production replay mutation, Telegram send, task execution, schedule change, DB mutation: all `0`
- Open Research/Event Attribution production imports: `0`

## Gate

- Open P0: `0`
- Open material P1: `0`
- Broad full-cohort generic repetition: `P2`, full mode remains disabled
- Production Assist control plane: `A`
- Production Assist: `OFF`
- `FREE_ANALYST_ADAPTIVE_CANARY = READY_NOT_ARMED`
- `COMMON_AI_CORE_V1 = INTEGRATED_READY_NOT_ARMED`
