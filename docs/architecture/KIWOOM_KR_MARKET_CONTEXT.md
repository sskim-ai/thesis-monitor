# Kiwoom KR Market Context

## Contract

`kiwoom-kr-market-context-v1` extends the existing financial and market evidence chain without
creating a parallel user-facing schema. It is an official-source acquisition and normalization
layer for completed KR sessions.

## TR Ownership

| TR | Endpoint | Canonical ownership |
| --- | --- | --- |
| `ka20001` | `/api/dostk/sect` | KOSPI/KOSDAQ close, return, breadth counts |
| `ka20003` | `/api/dostk/sect` | composite identity, KOSPI size, sector rows |
| `ka20009` | `/api/dostk/sect` | exact completed-session identity proof |
| `ka10051` | `/api/dostk/sect` | market-wide foreign/institution/retail net amount |
| `ka10066` | `/api/dostk/mrkcond` | complete stock-level monetary decomposition |

Only `/api/dostk/*` market-data endpoints are allowlisted. The client contains no order, account,
or trading surface. OAuth credentials are environment-only and never enter artifacts.

## Runtime

The KR daily job attempts collection after the analysis succeeds and before packet persistence.
The feature flag defaults OFF in code. When armed in operating settings, collection failure returns
an internal unavailable receipt and packet creation continues. No Telegram, Pilot, or assessment
state is mutated by the collector.

## Session Safety

Current-only TRs are accepted only after the target session completes, on the target KST date, and
only when `ka20001`, the `ka20003` composite row, and the target-date `ka20009` row agree on close
and return. A current-only row is never substituted for a historical session.

## KRX Coexistence

Kiwoom structured context and KRX exact-slot telemetry are separate provider observations. Kiwoom
does not mark KRX complete, alter the KRX scheduler, or rewrite prior KRX evidence. Same-day
cross-provider reconciliation remains pending a complete matching KRX publication.

## Future Research Boundary

Validated breadth and flow can later support Event Attribution hypotheses. They do not prove a
news cause, and Open Research remains production OFF.
