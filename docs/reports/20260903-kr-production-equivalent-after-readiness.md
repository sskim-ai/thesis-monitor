# KR Production-Equivalent After Readiness Repair

Frozen packet `2026-09-02-kr-run-52-d077cd42b44c` remains ready under the generic
`STOCK_V2` consumer projection:

- subjects: 8
- included numeric entries: 1,589
- excluded standalone market entries: 594
- unsupported included numeric entries: 0
- readiness/prompt mismatch: 0
- legacy prompt canonical fact-set difference: 0
- production packet mutation: 0

The exact same packet already passed the immutable production-equivalent proof on current main
with signed-in Codex CLI `gpt-5.6-sol / xhigh`: context, candidate, accepted, and explicit output
were all `8/8`, fallback was `0`, and message quality passed. The accepted labels and balances
remain:

| Ticker | Decision | BUY | SELL |
| --- | --- | ---: | ---: |
| 000660 | SELL | 3.5 | 6.5 |
| 003690 | HOLD | 5 | 5 |
| 005490 | HOLD | 4.5 | 5.5 |
| 005930 | HOLD | 4.5 | 5.5 |
| 010120 | HOLD | 4.5 | 5.5 |
| 012450 | HOLD | 5.5 | 4.5 |
| 047810 | HOLD | 5 | 5 |
| 086280 | SELL | 4 | 6 |

No KR field was silently exempted by the US night-futures ownership contract. A diagnostic
regeneration attempt was stopped by the existing strict evidence-reference validator after a
model-produced truncated reference for `000660`; no threshold, evidence reference, or repair
budget was changed. The authoritative immutable proof above therefore remains the regression
baseline.

- `KR_STOCK_V2_READINESS = PASS`
- `KR_CANDIDATE_COUNT = 8`
- `KR_ACCEPTED_COUNT = 8`
- `KR_EXPLICIT_COUNT = 8`
- `PRODUCTION_RECIPIENT_SEND = 0`
- `PRODUCTION_STATE_MUTATION = 0`
