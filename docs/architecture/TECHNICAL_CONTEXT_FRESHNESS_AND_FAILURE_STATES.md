# Technical Context Freshness And Failure States

Contract: `technical-context-freshness-v2`

## Completed-Bar Rules

Daily freshness compares the observed daily bar with the expected completed market session.
Weekly and monthly bars use their own completed-bar semantics and are not declared stale merely
because their dates precede the daily bar. Future bars are invalid.

## Timeframe Quality

Each D/W/M row records status, freshness state, latest completed bar, expected completed bar where
applicable, bar count, feature count, usability, and reasons. A stale daily timeframe is excluded
from current technical evidence while independently safe W/M evidence may remain available.

## Failure Isolation

- Missing timeframe: `UNAVAILABLE` for that timeframe.
- Daily session mismatch: `PARTIAL_SAFE` and `STALE`; never current.
- Malformed rows, duplicate/order errors, invalid OHLC, negative volume, or future bars: `INVALID`.
- Transport exhaustion after bounded retries: subject-local `UNAVAILABLE`.
- One subject failure never aborts a ready peer.
- A systemic service outage still permits subject-by-subject candidate preparation from remaining
  canonical evidence.

`PARTIAL_SAFE`, `UNAVAILABLE`, and `INVALID` are explicit evidence limitations. The model may set
timing to insufficient when the missing technical evidence matters; the backend does not invent a
neutral signal or retune decision policy.
