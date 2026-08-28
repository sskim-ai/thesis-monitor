# US Night Futures Session Mapping

US target-session date is not copied into the Korean overnight session identity. The existing
night-futures service remains the session owner. Only its safe current-overnight directional rows
are rendered; publication-pending, level-only, unavailable, and stale states are suppressed.

`NIGHT_FUTURES_SESSION_MAPPING = PASS`
`WRONG_NIGHT_FUTURES_SESSION_VISIBLE = 0`
