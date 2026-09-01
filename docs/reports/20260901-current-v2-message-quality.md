# Current V2 Message Quality

## Result

- Accepted-ready: `14 / 14`
- Explicit BUY/HOLD/SELL: `14 / 14`
- Distribution BUY/HOLD/SELL: `0 / 11 / 3`
- Accepted-block quality: `PASS`
- Combined message-quality-v2: `14 / 14 PASS`
- Accepted-block repeated substantive spans: `0`
- Manual/unresolved numeric claims in accepted blocks: `0 / 0`
- Message length min/max: `1072 / 1588`

## Technical Context

FULL technical context is present for 10 subjects. CPNG, HUT, MU, and SKHY are `INVALID` because provider bars failed OHLC integrity. Their accepted decisions remain explicit, use `LIMITED` or `BLOCKED` factual safety, and do not treat missing low-level timing evidence as neutral. Packet-owned Price Structure remains an independent validated evidence family and was not recalculated.

| Ticker | Technical context | Decision | Explicit count | Quality |
| --- | --- | --- | ---: | --- |
| CORZ | FULL | HOLD | 1 | PASS |
| CPNG | INVALID | HOLD | 1 | PASS |
| CRCL | FULL | HOLD | 1 | PASS |
| GOOGL | FULL | HOLD | 1 | PASS |
| HUT | INVALID | SELL | 1 | PASS |
| IBM | FULL | HOLD | 1 | PASS |
| MU | INVALID | HOLD | 1 | PASS |
| RXRX | FULL | HOLD | 1 | PASS |
| SKHY | INVALID | HOLD | 1 | PASS |
| SNDK | FULL | HOLD | 1 | PASS |
| TSLA | FULL | SELL | 1 | PASS |
| TSM | FULL | HOLD | 1 | PASS |
| WRD | FULL | HOLD | 1 | PASS |
| WULF | FULL | SELL | 1 | PASS |

## Human Review

CORZ, CPNG, GOOGL, HUT, MU, TSLA, and WULF were inspected in full. Decision ownership is visible before the legacy thesis text, invalid technical inputs do not disappear into a cohort fallback, and no infrastructure diagnostics or raw identifiers are shown. The retained CPNG deterministic core ends with a terse noun phrase; it is a legacy wording-polish P2 and does not alter evidence, decision, or OHLCV safety. Repeated cross-ticker lines are existing typed valuation-basis cautions, not duplicated V2 decision prose.

`CURRENT_V2_MESSAGE_QUALITY = PASS`
