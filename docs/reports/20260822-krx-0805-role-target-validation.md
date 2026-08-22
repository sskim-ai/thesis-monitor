# KRX 08:05 Role-target Validation

The 08:05 role now resolves the preceding completed XKRX session before checking
provider readiness. Saturday and Sunday 2026-08-22/23 both resolve 2026-08-21.
The 16:05 role remains same-day-only and makes no weekend/holiday provider call.

A completed Saturday observation suppresses Sunday's same target. A pending
Saturday observation may be retried Sunday. Provider readiness classifications,
endpoint set, payload hashes, capture schedule, and user-visible integration are
unchanged.

Provider-call bound: zero for outside-slot, no-target, duplicate, or terminal;
the existing endpoint count only for an eligible unresolved target.
