# XKRX Role-target Root Cause

Both affected jobs checked `is_exchange_session_date(XKRX, current.date())`
before resolving the observation role's target. Saturday therefore exited even
though the night observer had a valid overnight NIGHT BAS_DD and KRX 08:05 had
the latest completed Friday-equivalent target.

Existing unit tests concentrated on normal-session timestamps and separately
verified the correct session-basis functions, so they did not exercise the bad
precheck ordering at a natural weekend timestamp.

The repair introduces `xkrx-role-target-v1`, removes the universal wall-clock
gate, and retains the verified night-session basis and KRX readiness contracts.
