# Packet Fact Consumer-Scope Contract

Implemented contracts:

- `packet-fact-consumer-scope-v1`
- `ai-numeric-semantic-consumer-surface-v1`

The consumer set is `STOCK_V2`, `DAILY_REVIEW`, `MARKET_RENDERER`, `ARCHIVE_ONLY`, and
`NIGHT_FUTURES_MODULE`. User visibility is separate. A hidden `STOCK_V2` fact remains strictly
validated, while a visible renderer-only fact cannot enter stock reasoning.

Facts without explicit ownership remain `LEGACY_UNCLASSIFIED_STRICT`. Exclusion requires
structured ownership and is reported only as `NOT_IN_CONSUMER_SCOPE`; it is not called validated
or neutral. No ticker, field-path, field-name, or numeric-value allowlist exists.

