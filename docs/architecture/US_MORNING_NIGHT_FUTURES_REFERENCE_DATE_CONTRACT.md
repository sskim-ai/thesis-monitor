# US Morning Night Futures Reference Date Contract

## Historical v3 contract — superseded

The text below records the old Run-51 contract. It is not the current runtime
mapping and must not be used to change C52/C53 dates back to the previous
business day. The runtime uses `us-morning-night-reference-date-v4-end-date`
in `app/services/night_futures_session_mapping_service.py`.

C53 preserves that runtime mapping. It reports the required and returned KRX
reference dates separately. A broker chart's displayed date, a physical session
end date, and an API `BAS_DD` are not interchangeable labels; changing their
mapping requires the corresponding original rows, including weekend/holiday
cases. A screenshot alone does not establish the API's date convention.

Contract: `us-morning-night-reference-date-v3`

For the US morning digest on KST date `D`, the expected KRX night-futures
reference date is the latest valid XKRX business date strictly before `D`.
The XKRX calendar owns this mapping. Calendar-day subtraction and the US
regular-session date are not mapping inputs.

Concrete acceptance:

```text
observation_time_kst = 2026-09-02 08:00
expected_reference_date = 2026-09-01
provider_raw_bas_dd = 2026-09-01
reference_date_match = true
```

The provider raw date is preserved. A raw date below the expected reference is
`STALE_PRIOR_REFERENCE`; a raw date above it is
`UNEXPECTED_FUTURE_REFERENCE`. Neither is silently promoted.

Date match is necessary but insufficient. Instrument identity, contract and
maturity, same-contract preceding DAY comparison, row integrity, provider
change cross-check, source provenance, and finality must also pass. The 06:00
KST finality boundary is independent from date matching and never shifts the
expected reference date forward.

The contract is scoped to the US morning production gate and its read-only
publication observer. Other XKRX publication roles retain their own explicit
date contracts.

Run-51 therefore binds to `2026-09-01`. Its daily comparison remains completed NIGHT close versus
the immediately preceding regular-day close. Contract month is identity metadata and must never be
presented as the monthly analytical timeframe.
