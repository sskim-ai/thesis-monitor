# Kiwoom Percentage-Baseline Reverse Check

The diagnostic formula is `price / (1 + displayed_percent / 100)` using Decimal arithmetic.

| Field | Price | Displayed | Implied baseline | Change from 1064.50 rounds to |
|---|---:|---:|---:|---:|
| Open | 1061.00 | -0.33% | 1064.5128925454 | -0.33% |
| High | 1061.40 | -0.29% | 1064.4870123358 | -0.29% |
| Low | 1031.30 | -3.12% | 1064.5127993394 | -3.12% |
| Close | 1040.50 | -2.25% | 1064.4501278772 | -2.25% |

The mean implied baseline is `1064.4907080245`; the range is `1064.4501278772` to `1064.5128925454`. All four displayed percentages reproduce at two decimals from baseline `1064.50`, which equals the official KRX 09/01 NIGHT close.

`KIWOOM_PERCENT_BASELINE_IMPLIED = mean 1064.490708; range 1064.450128-1064.512893`

`KRX_0901_NIGHT_CLOSE = 1064.50`

`BASELINE_PARITY = PASS`

This supports sequential linkage but does not substitute for the missing 09/02 raw row.
