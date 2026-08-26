# Track C — KR Run-40 Integration Replay + Natural Reproof

## Preconditions

Start after Track A and Track B are on the same latest safe main.

## Immutable replay

Packet:

`2026-08-26-kr-run-40-706bc3003536`

No Telegram, no task execution, no DB/assessment mutation.

Validate:

```text
local-first digest
numeric registry completeness for supported paths
AI/fallback semantic safety parity
unresolved reconciliation remains fail-closed
KRX publication boundary
exactly-once historical evidence unchanged
Price Structure remains not armed
US Track A unchanged
```

## Replay PASS state

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
KR_BOUNDED_REPAIR = REPLAY_PASS_NATURAL_REPROOF_PENDING
TRACK_C_PRICE_STRUCTURE = DO_NOT_START
```

## Natural reproof

After repaired code is operating, wait for the next naturally scheduled KR close/afternoon message.

Do not manually trigger.

Read-only verify:

```text
target session
packet
AI eligibility/route
exact digest
same-session KR local evidence
numeric provenance
no unreconciled concentration
delivery/receipt exactly once
```

Only after natural PASS:

```text
TRACK_C_PRICE_STRUCTURE = READY_TO_START
```

Price Structure is not armed by this track.

## Deliverables

Integrated replay report, exact diff, AI/fallback parity, safety parity, readiness, natural-proof
status, final main/operating SHA.
