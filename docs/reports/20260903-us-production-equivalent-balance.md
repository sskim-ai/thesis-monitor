# 2026-09-03 US Production-Equivalent Balance

## Identity

- Packet: `2026-09-02-us-run-51-39a4d4eec53e`
- Model / effort: `gpt-5.6-sol` / `xhigh`
- Context / candidate / accepted / explicit block: `14/14/14/14`
- Ready / not ready / fallback: `14/0/0`
- Message quality: `PASS`
- Subject-level bounded repairs: `4` (`MU`, `RXRX`, `TSLA`, `TSM`)

## Accepted Results

| Ticker | Decision | BUY | SELL | Ownership |
| --- | --- | ---: | ---: | --- |
| CORZ | SELL | 3.5 | 6.5 | adjudication KEEP_V2 |
| CPNG | HOLD | 5 | 5 | candidate |
| CRCL | HOLD | 4.5 | 5.5 | candidate |
| GOOGL | HOLD | 4.5 | 5.5 | adjudication KEEP_V2 |
| HUT | SELL | 3 | 7 | candidate |
| IBM | HOLD | 5 | 5 | candidate |
| MU | HOLD | 4.5 | 5.5 | candidate |
| RXRX | SELL | 3.5 | 6.5 | adjudication KEEP_V2 |
| SKHY | HOLD | 4.5 | 5.5 | candidate |
| SNDK | HOLD | 5 | 5 | candidate |
| TSLA | SELL | 3 | 7 | candidate |
| TSM | HOLD | 5.5 | 4.5 | candidate |
| WRD | SELL | 3.5 | 6.5 | adjudication KEEP_V2 |
| WULF | SELL | 2.5 | 7.5 | candidate |

Every accepted stock block has one directional-balance line, an exact sum of 10,
and accepted-plan ownership. No ticker-specific allowance, forced distribution,
or majority vote was used.

## Transport Note

The first US batch attempt reached its 900-second model timeout before producing a
complete artifact. One bounded preflight rerun used the runtime-standard
1800-second limit and reused the already validated KR artifact, so KR generation
was not repeated. The rerun completed all five US batches and all bounded repairs.

- `US_PRODUCTION_EQUIVALENT = PASS`
- `PRODUCTION_RECIPIENT_SEND = 0`
- `PRODUCTION_DELIVERY_STATE_MUTATION = 0`

