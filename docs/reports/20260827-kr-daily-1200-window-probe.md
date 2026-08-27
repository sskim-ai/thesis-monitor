# KR Daily 1200 Window Probe

## Read-Only Requests

Seven official local-provider calls were made: one rejected `count=1200` request and two requests
for each of `000660`, `005930`, and `010120`. No auth value or raw account data is recorded.

| Ticker | Latest request | Latest window | Attempted older request | Returned older window | Older rows |
| --- | ---: | --- | ---: | --- | ---: |
| 000660 | 1000 | 2022-07-25 to 2026-08-27 | 220 ending 2022-07-24 | 2025-09-30 to 2026-08-27 | 0 |
| 005930 | 1000 | 2022-07-25 to 2026-08-27 | 220 ending 2022-07-24 | 2025-09-30 to 2026-08-27 | 0 |
| 010120 | 1000 | 2022-07-25 to 2026-08-27 | 220 ending 2022-07-24 | 2025-09-30 to 2026-08-27 | 0 |

All successful responses were provider `kiwoom`, adjusted `true`, ascending by date. The attempted
older requests returned the current latest window because `end_date` is outside the official
contract. They provide no non-overlapping or older row and cannot be chained.

## Direct Limit Control

`000660`, daily, `count=1200` returned HTTP 422:

`Input should be less than or equal to 1000`

## Result

- Provider maximum per official request: `1000`.
- Older-window support: `NO`.
- Supported window request count for exact 1200: `0`.
- Duplicate/ordering/basis merge checks: not entered because no second supported window exists.
- Capability: `PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW`.
