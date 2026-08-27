# KR Test Sink Rollout Safety

## Required Isolation

The Track C pre-enablement test requires exactly one configured non-production Telegram recipient.
Its identifier must differ from `TELEGRAM_CHAT_ID`. Reports expose only the environment-key name
and a one-way alias; raw recipient, account, and token values are never written.

The accepted key set is:

- `TELEGRAM_TEST_CHAT_ID`
- `TEST_TELEGRAM_CHAT_ID`
- `TELEGRAM_STAGING_CHAT_ID`
- `TELEGRAM_DEVELOPER_CHAT_ID`

No configured key, multiple ambiguous keys, a missing production comparator, or equality with the
production recipient is fail-closed. Production fallback is prohibited.

## Delivery Gate

An eligible test sends at most one KR market digest and three to five monitored KR stock messages.
The test must prove exact payload equality, exact receipt equality, exactly-once delivery, no
truncation, no formatting break, no duplicate, no orphan, and zero production delivery intents.

If the sink gate cannot run or any P0/P1 remains, both KR guards stay OFF:

- `KR_MARKET_SECTOR_TOP3_ENABLED`
- `KR_PRICE_STRUCTURE_V3_ENABLED`

Local previews and archive replay are evidence for implementation quality, not substitutes for an
external received-message proof. They must be labeled `NOT_SENT`. A later enablement action must be
KR-only and must leave US Price Structure v3 disabled.
