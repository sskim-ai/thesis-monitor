# 2026-09-03 Directional Balance Schema

## Result

Track A schema implementation is PASS.

- Contract: `v2-directional-balance-v1`
- Candidate fields: `directional_balance`, `buy_drivers`, `sell_drivers`, `balance_summary`
- Accepted fields: candidate and accepted balance, drivers, and summary
- Pair: finite values, range 0 through 10, exact sum 10, integer or 0.5 increments
- Invalid sum: rejected
- False precision: rejected
- Non-finite value: rejected
- Probability or expected-return wording: rejected
- Fixed weighted-score wording: rejected

The implementation uses decimal-safe validation after parsing. It does not add a scoring model or change existing evidence weights.

## Lineage

Accepted fingerprints include the accepted balance and directional-driver evidence references. The accepted decision ID also includes the accepted balance. A not-ready plan retains candidate balance metadata for diagnostics but has no accepted balance authority.

## Compatibility

New onboarding results persist the accepted balance and drivers. Legacy onboarding readiness payloads remain readable; optional legacy balance metadata is validated when present.
