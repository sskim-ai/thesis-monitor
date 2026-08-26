# Track B — KR Sector Breadth Numeric Registry Repair

## Objective

Close the run-40 numeric semantic registry gap without broad wildcard registration.

Observed:

```text
total numeric entries = 1,961
registered = 1,583
unsupported sector breadth count paths = 378
ready_for_ai = false
```

## Required audit

Inventory all 378 and classify:

```text
SUPPORTED_CANONICAL
INTERNAL_ONLY
UNSUPPORTED
DUPLICATE_ALIAS
```

For supported canonical paths register exact semantics, unit, market/sector scope, source owner,
session basis and prose eligibility.

Use existing canonical semantic types.

Do not guess enum names from this instruction.

## Hard gates

```text
SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0
UNKNOWN_NUMERIC_SEMANTIC_REGISTERED = 0
WILDCARD_REGISTRY_BYPASS = 0
SECTOR_BREADTH_COUNT_SEMANTIC_MISLABEL = 0
AI_DERIVED_BREADTH_NUMERIC = 0
NUMERIC_GATE = PASS
```

A final `ready_for_ai=false` is acceptable only if a different legitimate gate blocks it. Report
that gate explicitly.

Unknown future paths must remain fail-closed.

## Isolation

Do not edit digest wording except minimal integration plumbing.

Do not touch Price Structure v3, reconciliation tolerance, or US Track A.

## Deliverables

378-path inventory MD/JSON, registry root cause, before/after coverage, AI readiness report,
negative-control tests, implementation SHA.
