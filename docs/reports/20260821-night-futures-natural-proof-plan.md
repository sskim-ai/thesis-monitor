# Night-Futures Natural Proof Plan

## Observation

Allow the normal 08:05/10/15/20 production attempts and detached 08:45/09:15 observer to run. Do
not run either manually. After the horizon, run the read-only evidence command against stored files:

```bash
python scripts/night_futures_publication_telemetry_evidence.py --market-date YYYY-MM-DD
```

The script performs zero provider calls.

## Review Template

For each normal market morning record expected NIGHT date, all production classifications, distinct
returned NIGHT dates, per-product readiness/rejection, first observer classification, terminal
receipt, availability interval, telemetry failures, and user-visible fail-closed result.

Classify the day as one of `READY_WITHIN_PRODUCTION_WINDOW`,
`READY_SHORTLY_AFTER_DEADLINE`, `READY_ONLY_AFTER_BACKUP_WINDOW`,
`NOT_READY_WITHIN_OBSERVER_HORIZON`, `PROVIDER_ERROR`, or
`UNKNOWN_TELEMETRY_FAILURE`.

One day does not by itself authorize a permanent deadline change unless it exposes a deterministic
defect. A policy decision should normally use multiple clean natural sessions. Until then:

- `P1_TELEMETRY_GAP = REPAIR_DEPLOYED_PENDING_NATURAL`
- `DEADLINE_VERDICT = DEADLINE_UNPROVEN`
- `FAIL_CLOSED_SAFETY = PASS`
