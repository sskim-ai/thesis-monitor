# 2026-09-04 KR Natural Validation Errors

## Initial Validation

- Status: rejected
- Candidate SHA-256: `07fcdc7fd7b8f0d9e3ad1d9c5c4cbcc8e8200b4e6a94b4e778a508d752ff5c91`
- Error count: 17
- `kr_supply_actor_horizon_grounding_missing`: 16
- `confirmation_transition_current_state_mismatch`: 1

- `000660:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `000660:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`
- `003690:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `003690:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`
- `005490:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `005490:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`
- `005930:confirmation_transition_current_state_mismatch:price_positioning.text:not_reached:crossed`
- `005930:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `005930:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`
- `010120:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `010120:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`
- `012450:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `012450:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`
- `047810:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `047810:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`
- `086280:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:외국인:1d`
- `086280:kr_supply_actor_horizon_grounding_missing:supply_analysis.text:기관:1d`

## Correction / Final

- One permitted correction was used.
- Final status: passed
- Final error count: 0
- Final SHA-256: `c3f766bd4eec402ac2f8addcc8bd7a3bba2fd2c12cd04d4e87b5ab393d78aff4`
- The 17 regular validation errors were not the V2 first divergence: V2 had already been interrupted 13.7 seconds earlier, and the regular errors were subsequently closed.
