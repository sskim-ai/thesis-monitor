# V2 Production Decision Runtime

Contract: `v2-accepted-production-runtime-v1`

The visible stock-decision path is selected by `VISIBLE_STOCK_DECISION_ENGINE`. V2 can be
armed only when the selector is `v2_accepted`, V2 production is enabled, full monitored-stock
coverage is targeted, and the V1 rollback path remains available.

```text
immutable review packet
  -> complete monitored-subject inventory
  -> canonical decision evidence + local OHLCV
  -> signed-in Codex CLI (`gpt-5.6-sol`, `xhigh`)
  -> one candidate per subject
  -> adjudication for every material decision change
  -> accepted_decision_plan
  -> accepted-only production block
  -> normal AI-assisted delivery
  -> accepted state advance after complete delivery
```

The renderer never consumes a raw candidate or an unresolved adjudication. A subject that cannot
produce a final accepted plan is `NOT_READY`; only that decision block is suppressed. It does not
fall back to a visible V1 decision while V2 is selected, and it does not prevent unrelated base
message facts from being delivered.

The migration baseline supplies continuity for the first V2 production cycle. It is not a target
decision distribution. A changed decision is permitted only with current canonical evidence and a
final adjudication. Reusing an unchanged evidence fingerprint with an unexplained changed accepted
decision fails closed.

The production block is analytical BUY/HOLD/SELL guidance. It must not contain trade execution,
position sizing, invented targets or stops, or unregistered numeric calculations. Price Structure
and valuation remain owned by their existing canonical renderers.

Rollback changes the visible selector back to `v1_canary`; it does not rewrite accepted V2 audit
artifacts or historical delivery state.
