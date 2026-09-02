# 2026-09-03 Test Recipient Balance Integration

## Scope

The production-equivalent US and KR payloads were sent through the real Telegram
transport to the existing dedicated non-production test sink. The configured test
recipient was verified as available and distinct from the production recipient
before delivery. Recipient identifiers and aliases are intentionally omitted.

| Market | Market message | Stock messages | Total |
| --- | ---: | ---: | ---: |
| US | 1 | 14 | 15 |
| KR | 1 | 8 | 9 |
| Combined | 2 | 22 | 24 |

## Pre-Send Gates

- US and KR context/candidate/accepted/explicit counts: exact
- Accepted stock route: `22/22`
- Fallback: `0`
- Directional-balance line visible exactly once: `22/22`
- Directional-balance sum: `10` for `22/22`
- Logical identity duplicates: `0`
- Telegram length violations: `0`
- US Treasury 3Y/5Y/10Y/30Y block: present
- US user-facing night-futures section: absent

## Delivery Receipt

- Planned / sent: `24/24`
- Exact payload match: `true`
- Duplicate count: `0`
- Production recipient sends: `0`
- Production delivery intents: `0`
- Request retries: `0`
- Unowned retries: `0`
- Orphans: `0`

Before/after fingerprints were identical for both packet archives, accepted
decision state, pilot state, and both database paths.

- `TEST_RECIPIENT_BALANCE_INTEGRATION = PASS`
- `PRODUCTION_RECIPIENT_SEND = 0`
- `PRODUCTION_DELIVERY_STATE_MUTATION = 0`
