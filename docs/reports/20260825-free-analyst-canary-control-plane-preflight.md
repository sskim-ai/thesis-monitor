# Free Analyst Adaptive Canary Control-Plane Preflight

- Instruction: `20260825-free-analyst-adaptive-explicit-canary-enablement-and-cross-market-natural-proof.md`
- Instruction version: `1.0`
- Instruction commit: `73802b8849f674698bfdb3bfd7f3d0df89c236b2`
- Base/main/operating before activation: `cd0fb79a6925d75029debb24f00d1a4c7495aa75`
- Checked at: `2026-08-25 12:44 KST`

## Control Plane

| Control | Before | Required |
| --- | --- | --- |
| Production Assist governance | OFF | unchanged |
| Existing Pilot | enabled | unchanged |
| Free Analyst Adaptive | `false/current` | canary only |
| Market/stock/total limits | `1/2/3` | `<=1/<=2/<=3` |
| Full mode | OFF | OFF |
| Open Research/Event Attribution | not integrated | not integrated |
| Exact Trade AR user-visible | OFF pending natural proof | OFF |
| Inventory mode | `SELECTIVE_INVENTORY` | unchanged |
| Cash-flow mode | `SELECTIVE_CURRENT_FORMAL_FULL_FCF` | unchanged |
| Fallback | existing deterministic path | reachable |

`PRODUCTION_ASSIST_CONTROL_PLANE=B` remains correct. The existing Pilot is enabled, while
Production Assist is a separate governance approval. The new canary has its own kill switch and
cannot enable full mode.

## Validation

- Immutable selector simulation: `14/14` eligible; market `1`, stocks `2`, total `3`
- Scoped runtime quality: `PASS`
- Selected-candidate hard safety errors: `0`
- Focused tests: `141 passed`
- Full pytest: `1510 passed, 1 existing deprecation warning`
- Ruff / diff / project-state JSON: `PASS / PASS / PASS`
- Investment Knowledge / Chart Knowledge SHA parity: `PASS / PASS`
- Public Action / operation IDs / schema: `0.4.5 / 20-of-20 / 4`, unchanged
- API health before activation: `PASS`
- Open P0 / material P1: `0 / 0`

`CANARY_ENABLEMENT_PRECONDITION=PASS`.
