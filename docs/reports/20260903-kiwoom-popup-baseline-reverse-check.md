# Kiwoom Popup Baseline Reverse Check

For each displayed percentage, the implied baseline is
`displayed value / (1 + displayed percentage / 100)`. Because the UI percentage is rounded to two
decimal places, convergence is evaluated by reproducing the displayed rounded percentage from the
candidate baseline.

## 09/01 Popup

| Field | Value | Displayed | Implied baseline |
| --- | ---: | ---: | ---: |
| Open | 1061.00 | -0.33% | 1064.5129 |
| High | 1061.40 | -0.29% | 1064.4870 |
| Low | 1031.30 | -3.12% | 1064.5128 |
| Close | 1040.50 | -2.25% | 1064.4501 |

Mean is `1064.4907`, range is `0.0628`, and exact baseline `1064.50` reproduces all four displayed
percentages after two-decimal rounding. It equals KRX NIGHT BAS_DD 09/01 close.

`KIWOOOM_0901_POPUP_BASELINE = 1064.50_COMPATIBLE`.

## 09/02 Popup

| Field | Value | Displayed | Implied baseline |
| --- | ---: | ---: | ---: |
| Open | 1023.00 | -1.68% | 1040.4801 |
| High | 1048.35 | +0.75% | 1040.5459 |
| Low | 1020.25 | -1.95% | 1040.5405 |
| Close | 1043.60 | +0.30% | 1040.4786 |

Mean is `1040.5113`, range is `0.0673`, and exact baseline `1040.50` reproduces all four displayed
percentages after two-decimal rounding. It equals the prior Kiwoom night daily close and KRX NIGHT
BAS_DD 09/02 close.

`KIWOOOM_0902_POPUP_BASELINE = 1040.50_COMPATIBLE`.

`POPUP_BASELINE_CHAIN_PARITY = PASS`.

