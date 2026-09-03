# 2026-09-03 KR Natural Run Pipeline

## Stage Counts

| Stage | Result | Evidence |
|---|---:|---|
| Source/evidence ready | 8 | monitor run `54`: success 8, failure 0 |
| Technical context FULL | 8 | 24 requests, 24 successes, no retry/error |
| Technical PARTIAL_SAFE | 0 | packet telemetry |
| Technical unavailable | 0 | packet telemetry |
| Packet persistence eligible | 8 | global contract eligible, hard errors 0 |
| AI-consumability ready | 8 | `ready_for_ai=true`, eligible KR8 |
| Network preflight | `NOT_PRESENT_IN_THIS_REVISION` | no native stage receipt |
| Codex app-server reached | `NOT_PRESENT_IN_THIS_REVISION` | no native stage receipt |
| Model reached | `NOT_PRESENT_IN_THIS_REVISION` | not inferred from downstream files |
| Candidate items | 9 | market 1 + stock 8 |
| Accepted items | 9 | corrected candidate set archived and validated |
| Explicit decision V2 | 0 | `V2_DECISION_SUPPRESSED_SAFE` |
| Fallback rendered | 9 | market 1 + stock 8 |
| Delivered | 9 | fallback receipt 9/9 sent |

## Candidate And Acceptance

The first candidate set was rejected for two market-level numeric provenance errors and four `000660` valuation occurrence/binding errors. The corrected set was archived as accepted and the primary validation result passed.

The runtime quality receipt covered the adaptive canary subset only: market + `000660` + `003690`, three messages total. It passed all hard checks. The free-analyst selector likewise selected one market message and two stocks.

The accepted AI-assisted delivery receipt remained `pending` with 9 pending and 0 sent. The retry scheduler later reported `no_pending_ai_delivery`; at 17:10 the deterministic fallback sent 9/9.

## Per-Ticker Pipeline

| Ticker | Packet ready | AI ready | Model receipt | Candidate | Accepted | Explicit V2 | Fallback | Delivered |
|---|---|---|---|---|---|---|---|---|
| 000660 | yes | yes | not present | yes | yes after correction | no | yes | yes |
| 003690 | yes | yes | not present | yes | yes | no | yes | yes |
| 005490 | yes | yes | not present | yes | yes | no | yes | yes |
| 005930 | yes | yes | not present | yes | yes | no | yes | yes |
| 010120 | yes | yes | not present | yes | yes | no | yes | yes |
| 012450 | yes | yes | not present | yes | yes | no | yes | yes |
| 047810 | yes | yes | not present | yes | yes | no | yes | yes |
| 086280 | yes | yes | not present | yes | yes | no | yes | yes |

