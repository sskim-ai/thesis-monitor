# US Post-Deploy Smoke

API health `ok`; OHLCV health `ok`. Operating current-time replay returned market PASS and stock
PASS across `13` subjects with eligibility
`{'BLOCKED': 1, 'ELIGIBLE_SR_ONLY': 12}`. The operating read-only DB proof found two immutable raw
legacy night strings but zero canonical projected rows and zero canonical summary items under the
current `ai_review_hold` gate.

- `POST_DEPLOY_MARKET = PASS`
- `POST_DEPLOY_NIGHT_FUTURES_CANONICAL_PARITY = PASS`
- `POST_DEPLOY_ALL_US_STOCKS = PASS`
- `POST_DEPLOY_KR_RUNTIME_DIFF = 0`
