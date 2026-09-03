# Shadow Message Quality

| Ticker | Chars | Gate | Exact duplicate lines | Style | Human note |
| --- | --- | --- | --- | --- | --- |
| CORZ | 1662 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| CPNG | 1679 | PASS | 0 | NEEDS_MINOR_EDIT | 문장 종결 보완 필요 |
| CRCL | 1471 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| GOOGL | 1605 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| HUT | 1642 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| IBM | 1791 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| MU | 1925 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| RXRX | 1492 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| SKHY | 1469 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| SNDK | 1461 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| TSLA | 1561 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| TSM | 1391 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| WRD | 1467 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |
| WULF | 1794 | PASS | 0 | READY_STYLE | 구조·일관성 양호 |

## Human Review

- Average length: `1600.7` characters; range `1391-1925`.
- Decision, directional balance, new-buyer view, and holder view are clearly separated.
- Exact substantive-line duplication: `0` for all 14 messages.
- Common order disclaimer repetition: `0`.
- Price zones consistently distinguish entry, trim review, and downside review.
- `CPNG` has one incomplete sentence in the inherited detailed body (`현재는 ... 현금흐름.`), so the set is classified `NEEDS_MINOR_EDIT` rather than production-ready style.
- Some semantic overlap remains between the new decision block and the inherited detailed body, but it does not require a structural redesign.

Overall: `SHADOW_MESSAGE_STYLE = NEEDS_MINOR_EDIT`.
