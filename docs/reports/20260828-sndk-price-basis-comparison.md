# SNDK Price-Basis Comparison

| Evidence | Session label | Close | Finding |
|---|---|---|---|
| prior current-time E2E | 2026-08-27 | 1456.93 | accepted at capture time |
| frozen Major-SR raw | 2026-08-27 | 1449.4 | invalid: below low 1456.0 |
| canonical fallback | 2026-08-26 | 1499.37 | latest valid completed row |
| live read-only A | 2026-08-27 | 1443.24 | same low 1456.0 |
| live read-only B | 2026-08-27 | 1443.24 | same low 1456.0 |

Open/high/low/volume remain the dated session fields while the close varies across stored/live
snapshots and can fall outside the session range. The exact provider-side transformation is outside
this repository, but the basis discrepancy is explained: a mutable quote is contaminating a dated
completed-bar close. Safe action is fail-closed until upstream separates quote and completed close.

Read-only provider calls for this audit: `2`; paid providers: `0`.
