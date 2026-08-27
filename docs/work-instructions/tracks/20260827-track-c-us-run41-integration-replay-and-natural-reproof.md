# Track C — US Run-41 Integration Replay + Natural Reproof

## Preconditions

Start only after Track A and Track B are merged/rebased onto the same latest safe main.

## Immutable replay

```text
run = 41
packet = 2026-08-27-us-run-41-ae4f42c23abc
target session = 2026-08-26
```

No Telegram send.
No manual scheduler execution.
No DB/assessment mutation.
No historical packet/delivery mutation.

## Replay must prove

```text
current market cross-section survives
RSP survives when selected
material sector dispersion survives when selected
macro remains temporally safe
AI and fallback share one plan
new validator rejects historical broken digest
new validator accepts repaired concise candidates
material information loss = 0
```

## Replay PASS state

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
US_BOUNDED_REPAIR = REPLAY_PASS_NATURAL_REPROOF_PENDING
US_TRACK_A = REPLAY_PASS_NATURAL_REPROOF_PENDING
PRICE_STRUCTURE_TRACK_C = DO_NOT_START
PRICE_STRUCTURE_V3 = INTEGRATED_READY_NOT_ARMED
```

## Natural reproof

After repaired code is operating, wait for the next naturally scheduled US morning run.

Do not manually trigger.

Read-only verify:

```text
current packet/session
route
shared plan
exact digest
current-session market evidence usage
RSP/sector selected-slot consumption
macro temporal safety
exactly-once
```

Only after natural PASS:

```text
US_TRACK_A = LIVE_PASS
```

Price Structure Track C remains governed by the separate master prerequisites, including KR natural reproof.

## Deliverables

Integrated replay, exact before/after, AI/fallback candidates, validator result, safety parity, readiness,
natural-proof status, final main/operating SHA.
