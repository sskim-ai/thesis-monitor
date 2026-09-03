# US Market Temporary Night-Futures Suppression

## Status

- Contract: `night-futures-user-visibility-v1`
- US user-facing visibility: disabled
- Internal suppression reason: `SESSION_DATE_CONVENTION_PENDING`
- Scope: temporary renderer gate plus explicit AI consumer ownership

## Boundary

The gate is evaluated immediately before user-facing rendering. It applies to the
US full market message, daily-digest fallback, morning macro notification, and AI
market-message fallback. The reason is internal and is not rendered as a warning.

`packet-fact-consumer-scope-v1` also declares preserved night-futures facts as
`ARCHIVE_ONLY` and `NIGHT_FUTURES_MODULE`. They do not own `STOCK_V2`,
`DAILY_REVIEW`, or `MARKET_RENDERER` while this gate remains active. This avoids
letting intentionally non-consumed raw fields block an unrelated stock-decision
readiness gate.

The gate does not change collection, raw occurrences, session mapping, publication
telemetry, history, or daily/weekly/monthly aggregation. These inputs remain
available for diagnostics and for a later session-date convention repair.

The consumer exclusion is not a semantic validation result. Diagnostics use
`NOT_IN_CONSUMER_SCOPE`, and facts without explicit ownership retain strict legacy
validation.

## Preserved US Market Contract

Suppression removes only the Korean night-futures block and its associated user
cautions/fact ownership. The US market message continues to own:

- SPY, QQQ, IWM, SOXX, and RSP
- market-internal and relative-strength interpretation
- selected sector strength and weakness
- nominal Treasury 3Y, 5Y, 10Y, and 30Y latest safe observations with previous
  valid-observation deltas in basis points
- next checks

The 10Y real yield remains non-primary and is not restored by this gate.

## Re-enable Condition

Re-enablement requires a separately reviewed KRX/Kiwoom night-session date
convention contract and regression proof. Removing this gate alone is not a valid
re-enablement procedure.
