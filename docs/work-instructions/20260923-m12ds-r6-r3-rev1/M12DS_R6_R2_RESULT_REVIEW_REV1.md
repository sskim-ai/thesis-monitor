# M12DS-R6-R2 Result Review

## Decision

`CORRECT AUTHORIZATION STOP`

The R6-R2 report is internally consistent and correctly stopped at:

`M12DS_R6_R2_US_SETTLED_CLOSE_ROUTE_REQUIRES_USER_AUTHORIZATION`

The report ZIP SHA-256 is:

`fa9c63acb5f1a3dd5db25b403802afcfbd4c5eebfd43188a95fc10850259665e`

## Proven production cutoffs

Configured production timing:

- US source collection: 08:05 KST, gates 08:10/08:15/08:20
- US AI primary / backup: 08:15 / 08:30
- US fallback: 08:40
- KR source collection: 16:05 / 16:20 / 16:50 KST
- KR AI primary / backup: 16:15 / 16:55
- KR fallback: 17:10

At 08:05 KST in EDT, the US time is 19:05 the previous calendar day. Regular trading
has ended but after-hours may still be active. Therefore a current quote cannot be silently
reinterpreted as the 16:00 regular-session close.

At 16:05 KST the Korean regular session has ended. Therefore the preferred KR route is
same-day post-close ownership, not previous-day historical sector substitution.

The currently configured AI tasks are PAUSED and collection/fallback/delivery launchd
jobs are disabled. The schedule exists as configuration, but this result does not prove an
active scheduled run will occur automatically.

## US route result

Existing Kiwoom `usa06012` returns current rows including 2026-09-22, but only owns
`CURRENT_QUOTE`; it does not own `SETTLED_REGULAR_SESSION_CLOSE`.

A bounded SPY/XLC re-probe returned HTTP 200 and current rows. The earlier XLC
429/502 was not reproduced.

Existing alternatives:
- Massive: implementation exists but key absent and route is shadow-only
- Finnhub: configured for multiples/estimates, not completed close
- secondary OHLCV recovery registry: empty
- Alpha Vantage: existing key/account and generic price policy entry exist, but concrete
  production price provider is currently a stub; the deployed concrete endpoints are
  fundamentals/FX

The smallest authorized next candidate is qualification of the already-existing
Alpha Vantage account for an EOD/daily close route.

No new key, paid subscription, or new external provider is authorized.

## KR route result

Existing candidate owner:

- `ka20001` current index
- `ka20003` venue-sector snapshot
- `ka20009` date-owned index history

The remaining proof is a live post-close same-date parity check:
- exchange CLOSED
- collection after close
- current index identity
- same-day level/return parity to date-owned history
- sector snapshot bound to that completed session

No new KR provider is required unless that proof fails.

## Deferred work

Because US authority stopped first, R6-R2 did not execute:

- KR post-close live parity
- KR 8-stock fresh final-message capture
- latest-available macro informational renderer
- fresh night D/W/M E2E
- Market/Core/A/B
- 24/24 final capture

Therefore final message validation remains incomplete.


## R6-R3-REV1 route-priority correction

Before using Alpha Vantage, first qualify whether the existing Kiwoom `usa06012` daily
OHLCV response already owns a true daily candle close.

The key distinction is contextual:
- generic quote `cur_prc` remains `CURRENT_QUOTE`;
- row-local `cur_prc` inside a proven dated DAILY_BAR may be mapped to `close` only if
  official endpoint semantics and finality are proven.

Alpha Vantage is now fallback-only.
