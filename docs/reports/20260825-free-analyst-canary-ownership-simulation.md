# Free Analyst Canary Ownership Simulation

- Policy: market `<=1`, stocks `<=2`, total `<=3`
- KR selected: `market:2026-08-25-kr-run-38-6cd8c5d5091b, stock:012450, stock:000660`
- US selected: `market:2026-08-25-us-run-37-7e04812311c2, stock:CORZ, stock:CRCL`
- KR counts: `1/2/3`
- US counts: `1/2/3`
- Selected ownership mismatches: `0`
- KR / US scoped runtime quality: `PASS / PASS`
- Actual delivery: `0`

Semantic ownership, support-ref owner, industry context, thesis driver, expectation owner, hard validation, and runtime quality passed for every selected candidate. One-message ownership failure remains a deterministic per-message fallback and cannot consume another message's state.

`CANARY_OWNERSHIP_ELIGIBILITY = PASS`
