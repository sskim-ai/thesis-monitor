# KRX Night Futures Lookback Validation

Generated: 2026-08-12 16:11 KST

## Selection Policy

- The bounded lookback stops only when at least one target product has an explicit regular/night session pair for the same contract with a verifiable maturity and valid closes.
- A current-date partial verified result is preferred over an older full result.
- Nonempty but unverifiable dates are retained as diagnostics and do not stop the search.

## Live Probe

- Official service: KRX `fut_bydd_trd`
- Queried dates: 2026-08-12, 2026-08-11
- Selected source date: 2026-08-11
- Night session usable: true
- Selected maturity: 2026-09

| Product | Contract | Regular close | Night close | Change | Change % |
|---|---|---:|---:|---:|---:|
| KOSPI200 | A0169000 | 989.80 | 974.95 | -14.85pt | -1.50% |
| KOSDAQ150 | A0669000 | 1,485.30 | 1,489.00 | +3.70pt | +0.25% |

The selected observations preserve the actual 2026-08-11 source date. They are not relabeled as 2026-08-12 values.

## Regression Coverage

- Current nonempty/unverified date continues to a prior verified date.
- Current partial verified result stops the lookback without mixing an older product.
- Multiple nonempty/unverified and empty dates continue within the bounded window.
- All nonempty/unverified dates return `no_recent_verified_night_pair`.
- All empty dates return `no_recent_business_date_data`.

No API credential is stored in this report.
