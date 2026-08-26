# 2026-08-26 US Morning Canary Natural Proof

## Verdict

`US_FREE_ANALYST_CANARY_NATURAL = NOT_OBSERVED`

The configured canary remained bounded and full mode remained off, but no Free Analyst candidate became user-visible in this natural run.

## Counts And Limits

| Item | Result |
|---|---:|
| AI candidate messages finalized | `14` |
| AI candidate messages validated | `14` |
| Backend-bound numeric claims | `127` |
| Canary selected | `0` |
| Deterministic fallback delivered | `14` |
| Full mode | `OFF` |
| Market canary limit | `1` |
| Stock canary limit | `2` |
| Total canary limit | `3` |

The backup produced a clean current-packet candidate at `08:42:13 KST`. Fallback had become terminal at `08:40:05 KST`, so the finalizer correctly returned `archive_only` with `fallback_or_existing_delivery_won` and did not create a second delivery.

## Material P1

```text
SYMPTOM: clean current-packet AI candidate missed the fallback deadline by about 128 seconds
AFFECTED_PACKET: 2026-08-26-us-run-39-d55fe527c8e9
CONFIRMED_FACT: first validation passed; delivery was archive-only because fallback already won
ROOT_CAUSE: packet became available near the end of the primary wait, while primary claimed an older pending packet; backup generation completed after the deadline
VALIDATOR: correctly accepted run-39 and correctly prevented duplicate delivery
SMALLEST_REPAIR_SURFACE: packet claim ordering/readiness timing and fallback budget coordination
REPLAY_NEEDED: yes, for deterministic timing/claim ownership tests
NATURAL_REPROOF_NEEDED: yes
```

No canary limit increase or full-mode enablement is recommended. This is a bounded orchestration repair.
