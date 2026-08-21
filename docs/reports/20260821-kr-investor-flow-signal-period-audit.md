# 2026-08-21 KR Investor-Flow Signal Period Audit

| Ticker | Provider signal | Canonical signal | Basis |
|---|---|---|---|
| 000660 | foreign exit / institution-retail absorption | horizon-mixed flow | mixed |
| 003690 | foreign-led | material other-participant flow | 20d |
| 005490 | foreign re-entry | foreign re-entry | 20d |
| 005930 | foreign exit / retail absorption | horizon-mixed flow | mixed |
| 010120 | foreign-led | material other-participant flow | 20d |
| 012450 | foreign-institution joint | horizon-mixed flow | mixed |
| 086280 | foreign-institution joint | horizon-mixed flow | mixed |

`mixed` is selected when at least two displayed actors reverse direction between 5d and 20d. A
single-period signal carries `1d`, `5d`, or `20d`; fallback prefixes 5d/20d summaries with that
period. No 20-day signal is rendered as a timeless current statement.

All seven subjects had attribution-material omitted flow. This does not invalidate the displayed
actor facts. It prevents exclusive absorber/leader wording and marks the table as the major three
participants.
