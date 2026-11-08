# C21T completed-flow and price-text boundaries

KR supply is projected only after native.completed_periods(). It retains
provider per-bar values and supplied aggregates; it does not add a 20-session
calculator. Top-level supply_demand is excluded from this projection because
its schema provides no independently bound completion date or source Owner.
Raw artifacts, hashes, original native view, and legacy helper remain unchanged.
US never consumes injected KR flows. Requests remain KR adjusted daily only.

An existing independent PriceDecisionContext with price, date and price type
keeps those values and is labelled as confirmed price, position not calculated
when comparison rules are absent. No adjusted-bar range is silently used for
that comparison. Missing independent price stays unconfirmed; legacy fallback
and registered-rule evaluation continue unchanged.

Eight new focused cases and two related existing S/R cases are used, not the
prior broad suites. Two actual pre-fix failures are preserved. No live service,
financial/auth HTTP, model, DB, service configuration or scheduler is invoked.

Live remains blocked: the unchanged OhlcvRead.request_identity allowlist does
not accept include_investor_flows, while OhlcvReceiptObserver.get requires exact
frozen params. A separate reviewed versioned Source contract is needed; this
change deliberately does not edit or bypass that contract. Local code hash and
Lane snapshots are not deployed service identity or current Parent authority.
