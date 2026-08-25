# KR/US Bounded Quality Safety Parity

Date: 2026-08-26 KST
Implementation commit: `f2326c39485e600bca2cee15747deeb8465c5c8a`

## Immutable Replays

- KR packet: `2026-08-25-kr-run-38-6cd8c5d5091b`, 8/8 eligible.
- US packet: `2026-08-25-us-run-37-7e04812311c2`, 14/14 eligible.
- Provider recollection: 0.
- Production mutation from replay: 0.

## Hard Safety Counts

| Gate | Count |
|---|---:|
| FACT_MISMATCH | 0 |
| UNSUPPORTED_NUMERIC | 0 |
| UNSUPPORTED_CAUSALITY | 0 |
| TEMPORAL_VIOLATIONS | 0 |
| SESSION_DATE_CONFLICT | 0 |
| SEMANTIC_OWNERSHIP_ERRORS | 0 |
| HIDDEN_ARITHMETIC | 0 |
| EXTERNAL_UNSOURCED_FACTS | 0 |
| MATERIAL_INFORMATION_LOSS | 0 |
| TRADE_AR_LEAK | 0 |
| DEFAULT_ZERO | 0 |

KR preserved 123 existing automatic numeric bindings and introduced no new exact numeric claim.
Manual, rejected, and unresolved bindings are each zero. US entity, ticker, packet, market,
industry, and support-ref ownership mismatches are each zero.

## Contract Parity

- Public Action: `0.4.5`, unchanged.
- operationId: `20/20 unique`.
- output schema: `4`, unchanged.
- Free Analyst full mode: `OFF`.
- canary limits: market 1 / stocks 2 / total 3.
- Open Research production integration: `0`.
- Trade AR: `OFF`.
- Production Assist: `OFF`.
- Scheduled-task configuration changes: `0`.
- Manual Scheduled Task executions: `0`.
- Manual Telegram sends: `0`.
- Pilot mutations: `0`.
- Database mutations: `0`.

Nasdaq exact-session publication-pending remains fail-closed; stale breadth is not injected. NYSE
breadth remains unavailable. Existing RSP, sector, index, rate, and real-yield paths are unchanged.

`SAFETY_PARITY = PASS`
