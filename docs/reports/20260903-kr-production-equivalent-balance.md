# 2026-09-03 KR Production-Equivalent Balance

## Identity

- Packet: `2026-09-02-kr-run-52-d077cd42b44c`
- Model / effort: `gpt-5.6-sol` / `xhigh`
- Context / candidate / accepted / explicit block: `8/8/8/8`
- Ready / not ready / fallback: `8/0/0`
- Message quality: `PASS`
- Subject-level bounded repairs: `3` (`000660`, `003690`, `086280`)

## Accepted Results

| Ticker | Decision | BUY | SELL | Ownership |
| --- | --- | ---: | ---: | --- |
| 000660 | SELL | 3.5 | 6.5 | adjudication KEEP_V2 |
| 003690 | HOLD | 5 | 5 | candidate |
| 005490 | HOLD | 4.5 | 5.5 | candidate |
| 005930 | HOLD | 4.5 | 5.5 | candidate |
| 010120 | HOLD | 4.5 | 5.5 | candidate |
| 012450 | HOLD | 5.5 | 4.5 | candidate |
| 047810 | HOLD | 5 | 5 | candidate |
| 086280 | SELL | 4 | 6 | adjudication KEEP_V2 |

Every accepted stock block has one directional-balance line, an exact sum of 10,
and accepted-plan ownership. No ticker-specific allowance or forced decision
distribution was used.

This full-cohort execution has a different candidate-input fingerprint from the
four-subject variance diagnostic. It is therefore not treated as a fourth
same-input vote or folded into that audit.

- `KR_PRODUCTION_EQUIVALENT = PASS`
- `PRODUCTION_RECIPIENT_SEND = 0`
- `PRODUCTION_DELIVERY_STATE_MUTATION = 0`
