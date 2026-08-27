# KR Daily Provider-Limit Degradation Policy

## Contract

`price-structure-coverage-degradation-v1`

For a provider-limited KR daily series:

```text
canonical_target = 1200
provider_cap = 1000
actual_completed = 1000
coverage_status = PARTIAL_SAFE
coverage_reason = provider_limit
```

`requested_count`, `provider_limit`, `provider_limit_hit`, `completed_count`, and `denial_reason`
remain the canonical serialized fields. No duplicate parallel coverage object is introduced.

## Safety

- `PARTIAL_SAFE` is not `PASS`.
- A short listing remains `PARTIAL`.
- Insufficient completed history remains `FAIL`.
- KR eligibility recognizes `PARTIAL_SAFE` but still requires safe visible structure.
- Proximity, Fib family, current-cycle, stored-rule, and provenance gates remain independent.
- Weekly/monthly data cannot fill daily history.
- No provider switch, interpolation, forward fill, or archive-as-runtime-cache is allowed.

## Gate

`DAILY_1200_IMPLEMENTATION_PATH = VERIFIED_PARTIAL_SAFE_1000`

`KR_DAILY_1200_COVERAGE = VERIFIED_PARTIAL_SAFE_1000`
