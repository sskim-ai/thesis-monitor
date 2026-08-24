# Legacy Macro Temporal Root Cause

## Incident

- Rehearsal: `2026-08-24-kr-live-rehearsal-193419`
- Cutoff: `2026-08-24T19:34:19+09:00`
- Original packet: `2026-08-24-kr-run-36-51d4359299cd`
- Severity: P0 before repair

The persisted morning briefing predated `macro-digest-temporal-eligibility-v1`. Its observations had
source values and coarse quality, but no per-item temporal role or aggregate eligibility contract.
Downstream consumers treated a missing role as current, allowing completed-session and lagging
reference data to become a current daily signal.

```text
legacy briefing without temporal metadata
-> missing role interpreted as current
-> current macro transmission/thesis language
-> false-current rehearsal output
```

The fail-open path reached daily digest/fallback interpretation, market intelligence, AI packet
macro context, macro thesis signals, and semantic validation. The source dates were not corrupt;
consumer compatibility was incomplete.

## Repair

`macro-temporal-legacy-rehydration-v1` derives a non-mutating temporal view using the existing
observation identity, series cadence, completed-session calendar, previous briefing, and cutoff.
Missing metadata never defaults to current. New-contract briefings pass through unchanged.

Result: `LEGACY_MACRO_TEMPORAL_REHYDRATION = PASS`.
