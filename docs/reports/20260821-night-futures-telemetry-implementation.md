# Night-Futures Telemetry Implementation

## Identity

- Instruction: `docs/work-instructions/20260821-night-futures-publication-telemetry-repair.md`
- Instruction commit: `b7cf6a2f413e309bb637e524aeb7c1436e4c5b1b`
- Latest-main reconciliation: `e7b2add98411868a4df7895103c18b57d3d03770`
- Implementation commit: `d54f1102c02c9ff1c6a8ddd18fc40d1aea059caf`
- Implementation Actions: run `32469373051`, Test/Lint PASS.
- Contracts: `night-futures-attempt-archive-v1`, `night-futures-publication-telemetry-v1`

## Implementation

The existing KRX probe now exposes date-level HTTP/row/SHA evidence, complete returned business and
NIGHT date inventories, parser/canonicalization/cross-check state, and independent KOSPI200/
KOSDAQ150 readiness. `MacroProviderResult.telemetry` carries that internal evidence without changing
observations.

The morning gate archives only its existing natural provider attempt. The new archive service uses
deterministic IDs, atomic files, idempotent replay, sanitized raw references, and isolated failure.
The detached observer uses the same provider/parser/canonicalizer at 08:45 and 09:15 KST and writes
no production state.

## Change Boundary

- Production attempts/timing/deadline: unchanged at 08:05/10/15/20 and 08:20.
- US primary/backup/fallback: unchanged at 08:15/08:30/08:40.
- Session-basis logic: unchanged.
- User-visible summary, AI, fallback, Telegram, receipt: unchanged.
- Public Action/schema/DB migration: unchanged / none.
- Live provider calls during implementation: 0.
- Manual Scheduled Task/Telegram/Pilot/DB mutations: 0/0/0/0.

The observer schedule was selected after the fallback terminal window, uses two bounded calls at
most, and stops after readiness.
