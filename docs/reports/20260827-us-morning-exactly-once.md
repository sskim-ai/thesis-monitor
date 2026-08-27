# 2026-08-27 US Morning Exactly-Once Audit

## Result

The packet produced one market digest and 13 stock messages. Database notification IDs `330` through `343` are all `telegram/sent`; each has `attempt_count=2`, `last_error=null`, and a unique `(ticker, assessment_date, channel)` identity.

| Measure | Result |
|---|---:|
| Natural packet count | 1 |
| Notification intent rows | 14 |
| Delivery count | 14 |
| Sent | 14 |
| Pending | 0 |
| Receipt-linked rendered set | 1 |
| Duplicate identities | 0 |
| Orphans | 0 |
| Unowned retries | 0 |
| Last errors | 0 |

The market digest was delivery ID `330`, created at `08:06:28.993134 KST` and sent at `08:40:08.070664 KST`. The full set completed by `08:40:22 KST`. `delivery-result.json` records rendered set SHA `48136cf0a02c674bef4d77d7a99b823d436bfcb621e5046611c305d80c057553`.

```text
EXACTLY_ONCE = PASS
DUPLICATE_DELIVERY = 0
ORPHAN_DELIVERY = 0
UNOWNED_RETRY = 0
```

No review-time Telegram, task, pilot, assessment, or database mutation occurred.
