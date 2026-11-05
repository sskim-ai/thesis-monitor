# C4 original Market component execution

Explicit opt-in Source-only execution; no Full Market Parent or economic,
Native, model, scheduler or send authority is added.

The original CurrentScopedRequestPlan is serialized/restored as that exact
version. Original CollectedObservation dataclasses use asdict with an explicit
ISO timestamp; arbitrary/Pydantic objects are rejected at that boundary.

The existing original collectors, private OS-isolated Worker, sealed Dispatcher,
single Global Lane and same-token physical windows remain the execution path.
When a count-limited Market consumer has sufficient bars but the original frozen
Source plan still selects a continuation, only those original selected slots
are drained in that same Worker/token lifetime. No new plan, reauthentication,
extra pages, retries or stock reads are introduced by the helper.

The new Market-only handoff records the actual initial qualification cutoff so
independent replay can reproduce the same component hash. The original Owner
still checks every source timestamp and quality at that cutoff; this is replay
of the original decision, not renewed current authority. Legacy callers without
the optional cutoff retain their original behavior.

Private bundle replay verifies full result coverage, both original Worker raw
replays, original response-bound NOT_SELECTED receipts (which have no raw), exact
physical windows and the original transitive Market Owner. A bound NOT_SELECTED
slot cannot be treated as a response or used to skip a selected continuation.

New tests cover full KR49/US48 MockTransport paths through the actual isolated
Worker, original Owners and fresh-process Cold; malformed versions, dataclass
mixing, identity/date/slot/binding tampering, closed handles/PID changes and
401/403/429 stops are rejected. An additional count-satisfied/continuation
scenario exercises draining the original selected tail. These tests confer no
real data rights. Task DB reopen records and real call counts are separate.

Completed Source-only components still lack the original macro, publication,
Class-C, overnight and economic-use parent graph. Do not issue a canonical Full
Market Parent, investment judgment or Strict Native readiness from this helper.
