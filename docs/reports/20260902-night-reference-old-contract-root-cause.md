# Night Reference Old-Contract Root Cause

## Finding

The run-51 omission was caused by a date-owner error, not stale provider data. The old US-morning
gate projected the KRX night reference from the completed US regular-session date and expected
`2026-09-02`. The product being selected is an XKRX night session, so XKRX must own its reference
date.

For an observation on `2026-09-02` KST, the latest valid XKRX business date strictly before the
observation date is `2026-09-01`. The provider raw `BAS_DD` was also `2026-09-01`. The old gate
therefore rejected two valid rows as stale.

## Repair Boundary

- Replaced only the US-morning night-reference date contract.
- Preserved provider raw dates and explicit stale/future classifications.
- Kept the 06:00 KST finality gate independent.
- Kept instrument, maturity, comparison DAY, row-integrity, and provenance gates unchanged.
- Did not force a row ready, change a quality threshold, or add a ticker exception.

The prior `SOURCE_LIMITATION_SAFE` record remains an immutable account of the old-contract result.
It is superseded for current readiness by `us-morning-night-reference-date-v3`.
