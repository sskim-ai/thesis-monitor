# Night-Futures Stale Path Audit

The existing production hard gate remains sufficient. `summarize_night_futures` requires explicit
`session_freshness` of fresh/revised and, when expected date is present, exact equality between the
session date and expected completed session. `morning_gate` marks any nonmatching trade date stale
before summary construction.

The provider may return a valid older NIGHT/DAY pair while the newest expected rows are absent. The
new telemetry preserves that older date as `STALE_PRIOR_SESSION_PRESENT`; it does not promote it.
The observer writes only archive files and has no path to the production candidate.

Stale user-facing substitution after repair: 0. No additional renderer redesign was necessary.
Residual prose/market-environment hardening is P2 only if later natural evidence identifies a new
path; none is currently observed.
