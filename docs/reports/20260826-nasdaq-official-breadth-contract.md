# Nasdaq Official Breadth Contract

Contract: `nasdaq-official-exchange-breadth-v1`.

Required raw fields are exact session date, advances, declines, and unchanged. Canonical scope is
`NASDAQ_LISTED_ISSUES`. The source does not publish a separate eligible-issue denominator, so that
field remains null. Participation denominator is advances + declines + unchanged. Deterministic
relations are net advances, advance share, decline share, and advances/declines with a zero-decline
guard. Missing exact sessions are `PUBLICATION_PENDING`; malformed target rows fail closed.
Intraday data is never promoted as final.
