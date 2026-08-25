# 2026-08-25 US AI Compatibility Natural Proof

- Packet: `2026-08-25-us-run-37-7e04812311c2`
- Canonical owner: `codex-us-backup`
- Candidate attempts: `2`
- Validation error counts: `33 -> 4`
- AI sent: `0`
- Actual delivery: `deterministic_fallback`

## Final blockers

- `MU:numeric_usage_semantic_mismatch:working-capital-relation:dbdfd04e725e83528d8fdd31:fields.gap_percentage_points_abs`
- `MU:numbers_without_provenance:business_earnings.text:15.7`
- `TSLA:numeric_usage_semantic_mismatch:working-capital-relation:36181e61768dfd580d9ede01:fields.gap_percentage_points_abs`
- `TSLA:numbers_without_provenance:business_earnings.text:26.6`

All four final errors are one bounded relation-binding family: the prose says Inventory growth was `15.7%p` / `26.6%p` lower, while the candidate references the absolute field and the validator requires the exact signed/role-compatible semantic. The facts exist; the failure is not missing financial data.

- FCF fiscal/YTD/FY period errors: `0`
- Current-price RR ownership errors: `0`
- Unsupported raw Fact ownership: `0` outside the two Inventory relation claims
- Final-language/runtime-quality eligibility: not reached because semantic/numeric validation rejected the candidate

`US_AI_COMPATIBILITY_NATURAL = FAIL`

Severity: `P1`, bounded US AI Inventory relation semantic repair.
