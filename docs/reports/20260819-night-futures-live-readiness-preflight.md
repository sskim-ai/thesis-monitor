# Night Futures Live-Readiness Preflight

Observed: `2026-08-19 10:09-10:15 KST`

## Decision

| Instrument | Latest status | Effective readiness | Visible promotion |
|---|---|---|---|
| KOSPI200 | `PROVIDER_DATA_PENDING` | `LIVE_PAIR_UNAVAILABLE` | suppressed |
| KOSDAQ150 | `PROVIDER_DATA_PENDING` | `LIVE_PAIR_UNAVAILABLE` | suppressed |

The expected latest completed session date was `2026-08-19`; its KRX response contained zero rows.
The 2026-08-18 response contained 385 rows, but no current pair passed the strict reference gate.
No same-`BAS_DD` DAY row was reused and no provider change field was promoted.

## Query Evidence

- Endpoint: KRX `fut_bydd_trd`
- Read-only dates: `2026-08-19` through `2026-08-13`
- Requests: 19 total across pre/post probes and targeted basis checks
- Rows: 0, 385, 0, 0, 0, 385, 385 by descending query date
- Sessions present in non-empty payloads: `정규`, `야간`
- Credentials printed or persisted: 0

## Latest Available Boundary

XKRX marks 2026-08-17 as a non-session. The preceding eligible DAY for a 2026-08-18 NIGHT row is
therefore 2026-08-14, but the current collector requires the preceding calendar date. Targeted raw
checks prove that the safe same-contract candidates exist:

| Instrument | Contract | 08/14 DAY close/settlement | 08/18 NIGHT close | Derived change | Provider change |
|---|---|---:|---:|---:|---:|
| KOSPI200 | `A0169000` | 1098.90 | 1094.95 | -3.95 / -0.35945036% | -3.95 |
| KOSDAQ150 | `A0669000` | 1487.50 | 1477.30 | -10.20 / -0.68571429% | -10.20 |

The provider change fields agree with the deterministic calculation, but remain audit evidence
only. The collector fails closed rather than crossing the holiday gap, so neither number is
currently canonical or visible. This is an availability defect, not a path for an incorrect number
to become visible.

08/18 payload SHA256:
`2c6b0d1d66ca52c84f484b846fd89454931c2d97ba80eb07342b5982340d28a0`

08/14 payload SHA256:
`49dad52cf69264c1ec9de80c0d3bd9af6fc8d5649b4b55edc1145ffafbe5c15c`

The KRX daily endpoint does not provide row-level timestamps. Temporal ordering for a verified pair
comes from the official NIGHT-session convention and distinct business dates; the current canonical
contract does not invent a provider timestamp.

## Stale Positive Control

| Field | KOSPI200 | KOSDAQ150 |
|---|---|---|
| Status | stale verified pair | stale verified pair |
| NIGHT date | 2026-08-14 | 2026-08-14 |
| preceding DAY date | 2026-08-13 | 2026-08-13 |
| contract | `A0169000`, 2026-09 | `A0669000`, 2026-09 |
| DAY close | 1073.70 | 1500.00 |
| NIGHT close | 1095.40 | 1512.30 |
| deterministic change | +21.70 / +2.02104871% | +12.30 / +0.82% |
| contract match | PASS | PASS |
| temporal order | PASS by session/date contract | PASS by session/date contract |

NIGHT payload SHA256:
`49dad52cf69264c1ec9de80c0d3bd9af6fc8d5649b4b55edc1145ffafbe5c15c`

DAY payload SHA256:
`5012fca936c33f7ad8ad3fe8954d34c60e3fafcf7c41adcf0fa96d1224317e0a`

## Gate

Promotion is safe because stale or incomplete lineage is suppressed. Raw holiday-gap inputs are
available, but collector live readiness is not proved until calendar-aware predecessor selection is
implemented and naturally exercised. `night-futures-session-basis-v1` remains
`CLOSED_RETROSPECTIVE_PENDING_NATURAL`, and holiday-aware predecessor selection remains open.
