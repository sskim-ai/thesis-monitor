# Night-Futures Publication Telemetry

## Problem

The production collector correctly failed closed on 2026-08-21, but its four attempts did not
retain enough evidence to tell whether the provider returned no rows, only a stale session, or the
expected session with a contract/pairing failure. No later natural observation existed, so the
08:20 deadline was unproven.

## Decision

Add a best-effort attempt archive to the existing collector and a detached, bounded post-deadline
observer. Both consume the verified provider/parser path and never influence user-visible output.

## Why

This separates a publication-time observability gap from pricing/session correctness. It supplies
future natural evidence without changing the policy before evidence exists.

## Rejected Alternative

Moving the deadline, adding production retries, creating a telemetry-only parser, or querying from
the backup path would change production or create a second truth path before the root cause is
known. Those alternatives are rejected.

## Safety Constraint

Telemetry is append-only, sanitized, idempotent, and failure-isolated. The observer cannot write DB,
market-summary, packet, delivery, fallback, or Telegram state. No manual observer/provider run is
allowed as proof.

## Scope

`night-futures-attempt-archive-v1` and `night-futures-publication-telemetry-v1`
observe the existing KRX night-futures collector without changing its session basis, retry window,
deadline, market-summary output, delivery, or fallback behavior.

The verified production path remains:

```text
expected NIGHT BAS_DD
-> preceding eligible XKRX DAY
-> same product, contract, and maturity
-> deterministic close change
-> provider-change cross-check
```

Telemetry copies diagnostics emitted by that path. It does not parse or pair independently.

## Attempt Contract

Every naturally invoked production attempt records start/end time, role, expected NIGHT and DAY
dates, HTTP status inventory, all returned business and NIGHT dates, raw/parsed row counts,
per-product contract/readiness/rejection state, parser/canonicalization/cross-check status, sanitized
raw SHA references, and one structured classification. Secrets and request headers are excluded.

The archive is deterministic and append-only by identity:

```text
data/telemetry/night-futures-publication/YYYY/MM/DD/<group>/
  attempts/<attempt-id>.json
  terminal-receipt.json
```

The group identity is market date plus expected NIGHT date. An attempt identity is the group, role,
and start time. Reprocessing the same logical attempt is idempotent. Writes are atomic and
best-effort; any archive exception is reduced to `TELEMETRY_WRITE_FAILED` with production effect 0.

## Classifications

The contract distinguishes provider empty/error, parser/canonicalization failures, stale prior
sessions, expected-session absence, missing matching DAY, contract/maturity mismatch, provider
change conflict, partial readiness, and complete readiness. KOSPI200 and KOSDAQ150 are retained
independently. Distinct NIGHT `BAS_DD` values are never collapsed to a single latest date.

## Production Instrumentation

`run_morning_night_futures_gate` uses the same four production attempts at 08:05, 08:10, 08:15,
and 08:20 KST. Only default natural provider calls are archived. No provider request, retry,
deadline, gate state, digest, AI, fallback, or delivery branch is changed. The 08:30 backup AI path
does not perform a night-futures provider query; that fact is recorded in attempt metadata and no
query is added for telemetry completeness.

## Detached Observer

`night_futures_publication_observer` uses the same provider at two bounded post-production slots:

- 08:45 KST: first post-deadline observation, after the 08:40 fallback window.
- 09:15 KST: horizon observation only when the expected pair was not already ready.

The observer has its own LaunchAgent and writes only the telemetry archive. It has no Session/DB,
market-summary, packet, notification, or Telegram dependency. It stops after complete readiness and
never continuously polls. At readiness, the receipt reports an observed interval such as
`(08:20,08:45]`; it never claims the exact publication instant. At the horizon without readiness,
the receipt records `UNKNOWN_WITHIN_HORIZON`.

## Safety And Policy Boundary

Existing `session_freshness` plus expected-session equality remains the user-facing hard gate.
Prior NIGHT rows remain provider-state evidence only and cannot substitute for the expected pair.
The new observer cannot influence production rendering. Deployment leaves
`DEADLINE_VERDICT = DEADLINE_UNPROVEN`; only future natural, preferably multi-day, telemetry may
support a deadline policy decision.
