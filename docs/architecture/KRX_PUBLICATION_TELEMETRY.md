# KRX Publication Telemetry

Status: telemetry-only operating candidate
Contracts: `krx-publication-readiness-v1`, `krx-publication-telemetry-v1`,
`krx-time-slot-provider-role-v1`, `krx-exact-slot-capture-v1`

## Boundary

This path answers one question: whether the KRX Open API publishes a coherent complete bundle at a
specific natural operating slot. It does not calculate breadth, build a market packet, write the
database, invoke AI, or send a notification. The provider and telemetry modules have no import from
`monitor_daily`, market intelligence, rendering, or delivery services.

The four observed endpoints are:

- `sto/stk_bydd_trd`;
- `sto/ksq_bydd_trd`;
- `idx/kospi_dd_trd`;
- `idx/kosdaq_dd_trd`.

Each probe stores HTTP status, row count, provider dates, latency, endpoint state, required-index
identity gaps, error code, and sanitized payload SHA-256. Raw rows, the API key, request headers,
database state, and user-visible values are not stored in publication telemetry.

## Exact Slots

The dedicated LaunchAgent starts at 08:05 and 16:05 KST. The job checks the local hour and minute
again before provider access and requires the current date to be an XKRX regular session.

| Slot | Target session | Role evidence |
|---|---|---|
| 08:05 KST | preceding XKRX session | `NEXT_MORNING_0805` |
| 16:05 KST | current completed XKRX session | `SAME_DAY_CLOSE_1605` |

Weekends, exchange holidays, calendar failures, and any other minute return `SKIPPED` with zero
provider calls and zero telemetry writes. `RunAtLoad` is absent, so registration cannot create a
manual or catch-up observation.

The v1 evidence contract does not define an exact clock for `T_PLUS_1_RECONCILIATION`. This repair
does not invent one and does not count the 08:05 observation twice. T+1 remains `NOT_YET_PROVEN`
until a separate role definition establishes its natural slot.

## Readiness

`PROVIDER_COMPLETE` requires every core endpoint to return rows for the exact target date. KOSPI
and KOSDAQ index payloads must include their broad and 200/150 identities. A complete result is the
only promotable snapshot state inside the provider model, but this telemetry-only path never
promotes it into a user-visible market fact.

- HTTP 200 with four empty payloads: `MARKET_COMPLETED_PROVIDER_PENDING`;
- mixed ready and empty endpoints: `PROVIDER_PARTIAL`;
- provider date mismatch: `STALE_PROVIDER_DATE`;
- HTTP, network, or schema failure: `PROVIDER_ERROR`;
- exact complete bundle: `PROVIDER_COMPLETE`.

Initial completeness provides only `observed_complete_by`. A first-complete timestamp and closed
publication interval require an earlier pending or partial observation in the same append-only
timeline. Provider publication time is never inferred.

## Natural Evidence

Only records with `capture_origin=launchd_calendar`, an explicit time slot, a timezone-aware
scheduled time, and a normal XKRX session enter provider-role evidence. Manual records may be useful
for diagnostics but receive no role credit. Latest observation per target session owns that
session's role result.

Existing gates remain unchanged:

- five clean complete 16:05 sessions for same-day support;
- five clean complete 08:05 sessions for next-morning support;
- three clean complete T+1 sessions after that slot is defined;
- one complete live observation is only `CANDIDATE`.

## Storage And Operations

Records append to `data/telemetry/krx/publication-readiness/YYYY-MM-DD.jsonl` with mode `0600`.
Writes are append-only, flushed with `fsync`, strictly timestamp-ordered, and cannot mix target
sessions. The directory is already covered by the repository's ignored `data/*` policy.

The LaunchAgent is independent from the four Codex AI-review Scheduled Tasks and the existing US/KR
market LaunchAgents. Registering it changes no AI schedule, no Telegram deadline, no Pilot state,
and no Production Assist setting.
