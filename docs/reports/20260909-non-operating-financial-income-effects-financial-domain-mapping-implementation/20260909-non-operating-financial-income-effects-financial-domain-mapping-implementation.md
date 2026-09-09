# M11 Non-Operating / Financial Income Effects Mapping

## Result

- Status: `M11_COMPLETE`
- Contract: `non-operating-financial-income-effects-v1`
- Implementation commit: `a5d561c238d13b4904bd116aed3d7e47a61f4abd`
- Financial-domain readiness: `READY_WITH_KNOWN_OPTIONAL_GAPS`
- Next scope: `DIRECTIONAL_FINANCIAL_CONTEXT_CONSUMPTION_AND_SPECIFICITY_IMPLEMENTATION`
- Production readiness: `NOT_READY`

## Exact Contract

- Direct official income-statement components retain source sign, period, currency,
  unit, entity, statement basis, attribution basis, and occurrence lineage.
- Financial-sector generic non-operating emissions: `0`.
- Broad other income/expense stays context-only; equity-method and tax remain separate.
- The only M11 derivation is `financial_income_minus_financial_cost`, using compatible
  official aggregate finance income and finance cost. Official direct net wins.
- Adjusted/normalized earnings, ETR, reconstructed operating profit, universal
  non-operating total, recurrence and materiality scores: `0`.

## Preserved Real Coverage

- KR non-financial candidates: `6`
- KR finance income / cost issuers: `6` / `6`
- KR interest income / expense issuers: `1` / `1`
- KR tax issuers: `6`
- KR safe net-financial-effect issuers: `6`
  (`5` derived, `1` official direct)
- Real preserved US income-statement payloads: `0`; no real-US coverage claim.
- Financial-sector candidates routed out: `1`.

## Safety And Validation

- Aggregate/child overlaps observed and controlled: `8`
- Child details preserved without summation: `8`
- Source conflicts: `0`
- Sign-ambiguous derivations: `0`
- Compact AI, Directional prompt, Price-Timing prompt, renderer, source sufficiency,
  Daily Delta, warnings, production and schedules: unchanged.
- Focused tests: `PASS_365_OF_365`
- Full tests: `PASS_2996_OF_2996`
- Ruff: `PASS`
- `git diff --check`: `PASS`

Monitoring remained paused across all eight approved paths. No provider or model calls,
production writes, sends, deployments, merges, or automatic resumes occurred.
