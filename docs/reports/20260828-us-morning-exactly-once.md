# 2026-08-28 US Morning Exactly-Once Audit

One packet produced one market digest and 13 stock messages. Database rows `352` through `365` are all `telegram/sent`, each under the unique key `(ticker, 2026-08-28, telegram)`. All have `attempt_count=2` and `last_error=null`; the second attempt is the single backend delivery-retry pass over persisted finalized content.

| Measure | Result |
|---|---:|
| Packet count | 1 |
| Notification intent rows | 14 |
| Delivery count | 14 |
| Sent / pending | 14 / 0 |
| Receipt-linked rendered set | 1 |
| Market chunks sent | 1 of 1 |
| Duplicate identities | 0 |
| Orphans | 0 |
| Unowned retries | 0 |
| Direct review-time sends | 0 |

`delivery-retry-state.json` records `analysis_rerun=false`, `packet_regenerated=false`, `renderer_rerun=false`, `telegram_resent=null`, and `archive_completion_recovery=false`. The market delivery row's content SHA is `5f0c9d18a420d03b4bc7a0acf36969e574846e788f03807464903a27360e139a`, exactly matching the archived AI message.

```text
EXACTLY_ONCE = PASS
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
```
