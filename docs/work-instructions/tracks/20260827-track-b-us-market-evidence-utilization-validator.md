# Track B — US Market Evidence Utilization Validator

## Objective

Add a deterministic runtime-safe validator that rejects material current-session evidence loss.

The validator must use:

```text
plan slots
evidence refs
provenance bindings
```

not keyword scanning or an LLM quality score.

## Required failure fixture

The exact historical run-41 digest that contained only the dated real-yield observation must fail.

Expected failure reasons include:

```text
CORE_MARKET_SLOT_UNCONSUMED
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE
```

plus selected RSP/sector-slot failures when applicable.

## Required pass fixture

A concise message that consumes:

```text
one current-market cross-section statement
RSP if selected
one bounded sector-dispersion statement if selected
optional macro context
```

must pass without numeric dumping.

## Hard gates

```text
CORE_MARKET_SLOT_UNCONSUMED = 0
SELECTED_RSP_SLOT_UNCONSUMED = 0
SELECTED_SECTOR_DISPERSION_UNCONSUMED = 0
UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION = 0
VALIDATOR_FORCED_NUMERIC_DUMP = 0
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
```

## Isolation

Do not modify packet timing, numeric registry semantics, macro temporal roles, Price Structure v3, or
business investment logic.

## Deliverables

Validator design, broken-run failure proof, positive controls, negative controls, implementation SHA.
