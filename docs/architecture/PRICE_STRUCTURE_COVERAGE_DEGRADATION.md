# Price Structure Coverage Degradation

Contract: `price-structure-coverage-degradation-v1`.

## States

- `PASS`: completed history meets the canonical timeframe target.
- `PARTIAL_SAFE`: a verified provider cap prevents the canonical target, but sufficient real
  completed history remains for coverage-aware Price Structure processing.
- `PARTIAL`: listing or available history is shorter than the target without a provider-cap claim.
- `FAIL`: completed history is insufficient for safe structure processing.

For KR daily Price Structure, the canonical target remains 1200. The official provider cap is
1000, so a 1000-completed-bar result is:

```text
requested_count = 1200
provider_limit = 1000
provider_limit_hit = true
completed_count = 1000
status = PARTIAL_SAFE
denial_reason = provider_limit
```

It must never be serialized as `PASS` or described internally as full 1200-day coverage.

## Eligibility

`PARTIAL_SAFE` is usable only under the existing coverage-aware eligibility, completed-bar,
proximity, and provenance gates. It does not bypass Fib family validation or promote historical
zones to the current cycle. A safe higher-timeframe zone may still render when daily coverage is
partial; all-failed coverage remains blocked.

Provider-limit terminology is internal unless material to a future user-visible decision.
