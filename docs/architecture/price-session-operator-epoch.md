# Source-only price sessions and operator epoch

`price_session_projection` is opt-in and does not change the original OHLC
inspector, strict close Owner, calendar or economic criteria. It independently
classifies a query-time observation with unknown trade session. Outside-range
quotes do not become certified extended-hours trades. No extended-hours
authority is currently minted: no bound official trade timestamp/session policy
has been admitted. Historical rows keep their original dates and generations;
a 999-row suffix is not a current 1000-row window or a technical-use grant.

The original isolated Worker exposes a separate `price_session` command from
sealed raw, exact parser and receipt page-chain verification. The parent binds
its result digest; independent Cold recomputes its source-only projection.
The existing C1R Source-only Owner remains a separate eligibility decision.

`operator_lane_epoch.acknowledge_cold_restart` is a separate trusted local
operator action, not semantic recovery and not enabled at service startup.
It requires explicit operator approval, current account exclusivity confirmation,
exact STOP/activation hashes, real boot, original lock inode and prior PID exit.
The caller must also review current participant inventory and physical ledger.
Old activation and HALTED state are sealed in a private epoch journal.
Original `_atomic` and OS lock perform the transition. State changes first;
an interrupted transition before activation commit is denied by generation
mismatch. Activation replacement is the commit point. A sealed intent allows
exact interrupted completion, but any changed state, boot or archive is refused.
Sequence and last_end are preserved, so pacing and request history do not reset.
An idempotent completed operation cannot reset a later STOP or used sequence.
Stale participants retain old activation and are denied, new participants must
rebind. No authentication, Provider or service operation is part of this function.

The old ambiguous STOP is recorded as operator acknowledged, never retrospectively
proven semantic-only. Auth/transport/custody/identity/HTTP hard stops stay intact.
This is not a production installation or a grant to new sources, AI or investment use.
