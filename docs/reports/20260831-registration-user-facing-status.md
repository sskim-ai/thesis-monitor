# Registration User-Facing Status

Pending registration returns `PENDING_ONBOARDING`, the remaining canonical stages, and an explicit statement that automatic onboarding continues. It never tells the user that monitoring is active.

Only an active, production-eligible, coordinator-approved subject returns `ACTIVE_READY` and states that automatic review begins from the next eligible cycle. `USER_TOLD_ACTIVE_WHILE_PENDING=0`.
