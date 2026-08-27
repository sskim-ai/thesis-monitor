# KR Daily History Provider Contract

- Route: `OhlcvClient -> local /ohlcv -> official/free Kiwoom provider`
- Canonical target: daily 1200, weekly 600, monthly 300
- Provider request maximum: 1000
- Daily transport request: 1000; canonical coverage requested count: 1200
- Daily result: `PARTIAL`, reason `provider_limit`
- Adjustment: `provider_adjusted_price_v1`
- Current incomplete bars remain excluded from pivot confirmation.
- Cache key/state: provider-internal and not exposed by the public response; no cache claim is made.
- Synthetic daily history and weekly/monthly reconstruction: zero.
