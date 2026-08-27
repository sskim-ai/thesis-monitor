# KR Market Internal Formatting Readiness

- Instruction commit: `dd1b5eb712081c222bcfe1b4465d4fe0aac5f89a`
- Base / previous main: `d00b5b6c89e67748d6b1d376e709770ae747566c`
- Implementation: `03a418ab1f616d0063becf3928a1327056dd2d66`
- Implementation Actions: run `33099146372`, Test and Lint PASS
- Focused regression: `150 passed`
- Full pytest: `1810 passed`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Investment / Chart Knowledge: byte-identical PASS
- Public Action / schema: `0.4.5 / 4`, unchanged
- operationId: `20/20 unique`
- API health and post-deploy KR renderer smoke: `PASS`

All required formatting, parity, delivery, exact-payload, feature-state, and isolation gates pass.
Open P0 and material P1 are `0 / 0`. The rollout remains enabled but still requires the next
naturally scheduled KR close for production proof.

`OPERATING_PROMOTION = PASS`  
`OPEN_P0 = 0`  
`OPEN_MATERIAL_P1 = 0`  
`KR_MARKET_INTERNAL_FORMATTING = DEPLOYED_AWAITING_NATURAL_PROOF`  
`NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_KR_MARKET_MESSAGE`

