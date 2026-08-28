# SNDK / WULF No-Bypass Control

| Ticker | With provisional | Without provisional | Bypass |
|---|---|---|---|
| SNDK | ELIGIBLE_SR_ONLY | ELIGIBLE_SR_ONLY | 0 |
| WULF | ELIGIBLE_SR_ONLY | ELIGIBLE_SR_ONLY | 0 |

The current official raw capture contains no malformed OHLC row for either ticker. Their previous
`daily_history_as_of_mismatch` block belonged to an older capture; the current-data recovery occurs
without the provisional layer and without a ticker exception. Malformed partial-bar unit controls
remain fail-closed.
