# Packet Fact Consumer Scope Contract

Contract: `packet-fact-consumer-scope-v1`.

## Purpose

Canonical packet storage is broader than any one consumer input. A fact is retained in the
canonical packet while structured ownership determines whether it may enter `STOCK_V2`,
`DAILY_REVIEW`, `MARKET_RENDERER`, `ARCHIVE_ONLY`, or `NIGHT_FUTURES_MODULE`.

Consumer ownership is independent from `user_visible`. A hidden reasoning fact owned by
`STOCK_V2` remains subject to full AI numeric-semantic validation. A visible market-renderer
fact does not enter stock reasoning unless it also owns `STOCK_V2`.

## Fail-Safe Default

Facts without explicit metadata and without a verified fact-type contract remain included in
consumer validation. They are classified as `LEGACY_UNCLASSIFIED_STRICT`; absence of metadata
never grants an exemption.

Only explicit structured ownership may produce `NOT_IN_CONSUMER_SCOPE`. Excluded facts are not
reported as validated, safe, or neutral.

## Packet Ownership

- Ordinary standalone market facts own `DAILY_REVIEW` and `MARKET_RENDERER`.
- A market fact selected for a stock transmission receives an additional `STOCK_V2` scope on
  the stock-owned copy.
- Intrinsic stock facts preserve legacy strict validation unless they carry explicit scopes.
- Temporarily suppressed night-futures facts own `ARCHIVE_ONLY` and
  `NIGHT_FUTURES_MODULE`; they own neither `STOCK_V2` nor `DAILY_REVIEW`.

No field path, field name, ticker, or numeric value participates in the exclusion decision.

