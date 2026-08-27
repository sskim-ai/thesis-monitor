# Track A — KR TOP3 Sector Market Message

## Scope

Change only KR market-digest sector selection from bounded TOP1 to bounded TOP3.

Preserve:
- local-first
- direction
- breadth
- aggregate flow
- size/style
- numeric provenance
- reconciliation safety

## Required output

When safe same-session rows >=3:

```text
KOSPI relative strong TOP3
KOSPI relative weak TOP3
KOSDAQ relative strong TOP3
KOSDAQ relative weak TOP3
```

User-facing terms:

```text
업종 상대 강세
업종 상대 약세
```

Never `leader/laggard`.

## Hard gates

```text
AI_DERIVED_SECTOR_RANKING = 0
SECTOR_TOP3_DUPLICATE = 0
STALE_SECTOR_IN_TOP3 = 0
NONDETERMINISTIC_SECTOR_TIEBREAK = 0
SECTOR_RETURN_AS_SECTOR_BREADTH = 0
GLOBAL_CONTEXT_PRIORITIZED_OVER_KR_INTERNAL_STRUCTURE = 0
```

## Replay

Use run-42 packet as regression fixture and latest completed KR session as current-data proof.

Deliver exact before/after market digest and selected TOP3 refs.
