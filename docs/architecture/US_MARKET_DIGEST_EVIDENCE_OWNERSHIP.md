# US Market Digest Evidence Ownership

Contract: `us-market-digest-plan-v1`

## Ownership

The canonical market fact catalog owns values, dates, temporal roles, and numeric registry
entries. The shared US market digest plan owns bounded evidence selection. AI prose and the
deterministic fallback are consumers; neither may independently rank sectors, reinterpret RSP as
breadth, or promote lagging macro context ahead of the completed market session.

Priority is fixed by semantic slot, not by an opaque score:

1. `CURRENT_MARKET`
2. `PARTICIPATION_STYLE`
3. `SECTOR_DISPERSION`
4. `BREADTH_STATE`
5. `MACRO_CONTEXT`

## Current-Session Rule

Current directional SPY, QQQ, IWM, and SOXX facts remain primary even when all returns are near
flat. Existing significance thresholds may choose important numeric changes, but they cannot drop
the whole current-session cross-section from the digest.

RSP is a participation/style proxy. It is never labeled as issue-level breadth. Official breadth
is selected only from its own canonical facts; publication-pending breadth is explicitly omitted.

Sector dispersion is a bounded deterministic relation. The plan selects the current directional
leader and laggard and retains both source refs. AI receives the completed relation and must not
calculate or rank sectors itself.

## Consumer Boundary

The deterministic renderer emits all selected primary claims and records the corresponding slots
and refs in the delivery payload. The structured AI validator checks interpretation refs against
the same serialized plan. Adaptive rendering receives the same plan claims so a later renderer
cannot silently return to a macro-only digest.

No part of this contract changes packet ownership, macro temporal classification, numeric registry
policy, exactly-once delivery, business thesis state, or Price Structure v3.
