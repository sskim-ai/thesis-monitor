# 2026-08-24 KR Natural Sent Message Bundle

## Delivery Result

- Expected KR messages: `8` (market digest `1` + stocks `7`)
- Actual KR messages sent: `0`
- Exact sent order: `[]`
- Telegram send time: `null`
- Delivery mode: `none`
- Delivery receipt: `absent`

No KR digest or stock message was created or sent. The computed packet identity was `2026-08-24-kr-run-36-b82af21dfde3`, but the immutable packet write was rejected with `shadow_cohort_activation_gate_failed`. The KR primary and backup therefore both received `no_pending_packet`; the fallback found `no_held_session`.

## Market Digest

`NOT_SENT`

## Stock Messages

| Intended order | Ticker | Company | Actual message |
|---:|---|---|---|
| 1 | 000660 | SK hynix | `NOT_SENT` |
| 2 | 003690 | Korean Re | `NOT_SENT` |
| 3 | 005490 | POSCO Holdings | `NOT_SENT` |
| 4 | 005930 | Samsung Electronics | `NOT_SENT` |
| 5 | 010120 | LS ELECTRIC | `NOT_SENT` |
| 6 | 012450 | Hanwha Aerospace | `NOT_SENT` |
| 7 | 086280 | Hyundai Glovis | `NOT_SENT` |

This bundle intentionally contains no reconstructed prose. Missing delivery evidence is not replaced with producer assessment text.

