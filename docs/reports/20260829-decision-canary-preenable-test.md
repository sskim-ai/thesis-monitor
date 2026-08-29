# Decision Canary Pre-Enable Test

The dedicated non-production sink received exactly six messages:

- four current production-equivalent messages: `003690`, `000660`, `GOOGL`, `RXRX`
- two clearly marked historical BUY fixtures: `003690`, `GOOGL`

Results:

- planned/sent: `6/6`
- exact payload match: `PASS`
- message quality: `PASS`
- Price Structure numeric diff: `0/4`
- production recipient collision/send/intent: `0/0/0`
- duplicate/orphan/unowned retry: `0/0/0`
- rejected decision sent: `0`

Recipient identities are represented only by irreversible aliases. Raw Telegram IDs, tokens, and
headers are absent from the report and repository.

Receipt SHA-256: `7e7fbd18d3cc9f25c9ad6ae02fc835a8b56d64448b6c052ad405304950c2bb84`.
