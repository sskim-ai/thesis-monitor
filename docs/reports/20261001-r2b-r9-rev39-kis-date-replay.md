# REV39 KIS Date Parser And Sealed Replay

Terminal:
`R2B_R9_REV39_DATE_PARSER_REPLAY_CURRENT_FY1_FPER_PASS_READY_FOR_FULL_FRESH_INTEGRATION`

REV40 readiness: YES. REV40 executed: NO. Production enabled: NO.

## Repository
- Branch: `codex/r2b-r9-rev39-kis-date-replay`.
- Base: `ef9582c4d4c2b76d4462dcbcb260bd6032a27b00`.
- Work-instruction first commit: `57fd1b63`.
- Frozen implementation: `51e0121ed4fb33bf517467283a07b7e82c045387`.
- Main/operating unchanged: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.
- Local commits only; no merge, push or deploy. Raw artifacts remain outside Git.

## Contract Closure
The generic action-date parser now supports strict full-year `YYYY/MM/DD` dates
and same-format two-boundary intervals. Existing compact, hyphen and dot formats
are unchanged. Invalid, partial, mixed-format and reversed dates fail closed.
No inferred year, effective date or daily interval expansion is introduced.

Unresolved dates now retain `CORPORATE_ACTION_DATE_UNRESOLVED` and the derived
owner returns `UNAVAILABLE_CORPORATE_ACTION_DATE_UNRESOLVED`. A proven critical
date or straddling action retains its event state, including unresolved audit
details. Missing/failed/nonterminal source remains source-incomplete.
The bounded guard policy, critical interval and arithmetic are unchanged.

## Source Replay
REV38 ZIP SHA-256:
`534ea1efcf78d4362546f227f57697c556e529ff6266f29e15c7e44c0293492e`.
Sidecar, CRC and internal manifest PASS: 667 members / 666 payload entries.

All 42 raw action families, 7 price receipts and 8 EPS states replayed. Raw
request/response/source-receipt bytes unchanged. Forty-one action responses are
empty. The sole 010120 face-value schedule row now parses all four boundaries
as April 8/9/12/13, 2026, before the August 27 EPS estimate date. Its generic
classification is `WHOLLY_ON_OR_BEFORE_ESTIMATE`, blocks=false. No ticker-specific
owner exception or manual qualification was used.

## Sealed Valuation Matrix
These are **2026-09-30 completed-session closes**, not fresh October 1 quotes.
EPS is the dated KIS research snapshot, not consensus. Provider PER is separate.

| Security | Derived FY1 fPER | State |
|---|---:|---|
| 000660 | 4.69 | QUALIFIED_CURRENT_PRICE_FY1_FPER |
| 005930 | 5.81 | QUALIFIED_CURRENT_PRICE_FY1_FPER |
| 003690 | unavailable | UNAVAILABLE_EPS |
| 005490 | 10.47 | QUALIFIED_CURRENT_PRICE_FY1_FPER |
| 010120 | 55.70 | QUALIFIED_CURRENT_PRICE_FY1_FPER |
| 012450 | 20.20 | QUALIFIED_CURRENT_PRICE_FY1_FPER |
| 047810 | 54.27 | QUALIFIED_CURRENT_PRICE_FY1_FPER |
| 086280 | 8.73 | QUALIFIED_CURRENT_PRICE_FY1_FPER |

010120: 205000 / 3680.2 = 55.703494375305689908157165371447203956306722460736.
Decimal precision 50 and 2-decimal ROUND_HALF_UP are unchanged. All seven values
were independently reproduced using exact fractions and Decimal. The old six
guard and fPER receipts are identical, including hashes. 003690 remains unavailable,
not zero or N/M. Valuation/NewBuyer/Holder authority only; no Overall/Core/A use.

## Validation And Safety
- Fast unit checks: 280 passed, including 107 new regression cases.
- Focused REV32-39 / valuation / registry: 598 passed, 1 deselected.
- Full pytest: 7644 passed, 63 skipped, 0 failures/errors; 3 existing warnings.
- Ruff, diff check, Investment Knowledge, Chart Knowledge: PASS.
- Source-binding negatives: 84 request mutations and 21 guard mutations rejected.
- Four cloned-row denial mappings PASS; actual source bytes unchanged.
- Owner AST audit: event policy and arithmetic unchanged; production app diff/imports 0.
- Provider/documentation/model calls 0; messages 0/24; Telegram/orders 0.
- Production DB/WAL, scheduler, warning, notification, source corpus unchanged.
- Main/merge/push/deploy/restart/GC 0. P0: 0; P1: 0; P2: 0.

## Handoff
The local result bundle contains the full report, original evidence, all receipts,
old/new parser and denial contracts, source identities, arithmetic, tests and
validation. ZIP + SHA only, after secret scan, to iCloud Drive / Thesis Monitor.

REV40 must first perform archive-backed GC if free space is below 12 GiB, then
collect fresh EPS/close/actions and prove full integration, whole-source replay
twice, Market/Core/A/B and 24 messages. No such execution is authorized by this
offline result itself. Do not reuse these sealed inputs as freshly collected data.
