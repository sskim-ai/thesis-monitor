# C3R: dated indicators and Market source components

Both additions are explicit opt-ins, not Native, financial, valuation or signal
authority. Existing stock admission and full Market/Native criteria are unchanged.

`historical_indicator_reuse` directly imports the hash-pinned original
ohlcv-analyst `app/indicators/technical.py`. It does not call get_ohlcv or any
Provider. Invalid rows split contiguous windows; missing reference history is
annotated without modifying the original indicator values. Weekly/monthly
RETURN/DRAWDOWN labels refer to bars, not days. No indicator supplies a stance.

`ScopedMarketComponentConfig` and `issue_market_component_parent` admit only a
single Market context, with no stock or Class-C registration. A trusted current
operator approval, original participating host session and frozen original plan
are required. Budgets are one-use per Market, at most 150 across one approval.
The KR RPC delegates to the original private Worker and sealed parent transport;
physical windows preserve the same dispatcher/token rather than reauthenticate.

New focused synthetic tests cover original-engine equivalence, short/invalid
history, cache reuse, Market capability separation and the actual OS-isolated
Worker with MockTransport. These tests cannot confer real readiness.

Live C3R captured only a pilot subset: KR authentication plus one component;
US authentication, three exchange lists and one Market chart. Task handoff bugs
(wrong Cold plan type and dataclass serialization) stopped extension. Their
offline repairs validated retained bytes in new private read-only evidence DBs;
no new live Worker was created and no original receipt or source DB was changed.
The full original component Owner and Full Market Parent remain unissued.

The task-specific runner is not a production entry point. Further live work
requires a new explicitly frozen current run, not resurrection of the closed
Worker's authority. No scheduler, send, model, Native or B2 is enabled here.
