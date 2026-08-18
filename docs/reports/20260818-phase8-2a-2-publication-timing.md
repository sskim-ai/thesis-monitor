# Phase 8.2A.2 KRX Publication Timing

Date: 2026-08-18
Branch: `codex/phase-8-2a-krx-market-breadth`
Implementation: `cd284013075d6b846f3614e694517a17a5c755bf`
Status: OBSERVATION CONTRACT PASS / CURRENT READINESS PARTIAL

## Immediate Observation

Target session: `2026-08-18`
XKRX latest completed session: `2026-08-18`
Formal observer time: `2026-08-18T21:06:36.928866+09:00`
Aggregate readiness: `MARKET_COMPLETED_PROVIDER_PENDING`
Current snapshot promotion: denied

| Endpoint | HTTP | Rows | Provider date | Latency ms | State |
|---|---:|---:|---|---:|---|
| `sto/stk_bydd_trd` | 200 | 0 | none | 104.5 | `EMPTY` |
| `sto/ksq_bydd_trd` | 200 | 0 | none | 81.9 | `EMPTY` |
| `idx/kospi_dd_trd` | 200 | 0 | none | 249.3 | `EMPTY` |
| `idx/kosdaq_dd_trd` | 200 | 0 | none | 78.7 | `EMPTY` |

The four sanitized response hashes were identical because each provider payload contained the same
empty result shape. The observer persisted only endpoint metadata and payload SHA-256 values; no
credential, request header, or raw secret entered telemetry.

## Observation Timeline

| Observed at KST | KOSPI stock | KOSDAQ stock | KOSPI index | KOSDAQ index | Readiness |
|---|---:|---:|---:|---:|---|
| 2026-08-18 20:27:09 | 0 | 0 | 0 | 0 | `MARKET_COMPLETED_PROVIDER_PENDING` |
| 2026-08-18 21:02:01 | 0 | 0 | 0 | 0 | `MARKET_COMPLETED_PROVIDER_PENDING` |
| 2026-08-18 21:06:36 | 0 | 0 | 0 | 0 | `MARKET_COMPLETED_PROVIDER_PENDING` |

The 20:27 observation is the committed Phase 8.2A.1 evidence. The 21:02 observation is the Phase
8.2A.2 immediate audit, and 21:06 is the first record written by the new local append-only observer.

## Time Semantics

- `first_non_empty_at`: `NOT_YET_OBSERVED`
- `first_complete_at`: `NOT_YET_OBSERVED`
- `observed_complete_by`: `NOT_YET_OBSERVED`
- `last_empty_at`: `2026-08-18T21:06:36.928866+09:00`
- closed publication window: `NOT_YET_AVAILABLE`
- provider-authored publication timestamp: unavailable

The evidence proves only that publication had not completed by 21:06 KST. It does not prove a T+1
publication pattern and cannot identify an exact publication time. If a later first probe is already
complete, that probe becomes `observed_complete_by`; it is not retroactively labeled the provider's
publication timestamp.

## Contract

`krx-publication-telemetry-v1` appends sanitized point observations to an ignored per-session JSONL
file. A stateless provider probe no longer fills `first_non_empty_at` or `first_complete_at` by
itself. A tracked transition from pending/partial to complete is required for first-complete and
publication-interval semantics.

The local telemetry file is mode `0600`, append-only by contract, and ignored by Git. Production
Scheduled Tasks were not changed or run.

## Request Budget

Phase 8.2A.2 made eight successful read-only endpoint calls: four for the immediate audit and four
through the formal observer. This is 0.08% of the official 10,000 calls/day/key limit. The failed
local Python invocation ended at syntax parsing and made no provider call.

## Next Observation

On the next normal session, observe the exact 16:05 slot once. If pending, probe adaptively at 17:00,
19:00, 21:00, and next-day 08:05 only until complete. Repeat exact 16:05 and 08:05 observations over
3-5 normal sessions before assigning a supported live role. This is an observation plan, not a
production schedule.
