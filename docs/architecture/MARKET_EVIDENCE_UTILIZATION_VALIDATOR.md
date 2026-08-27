# Market Evidence Utilization Validator

Version: `market-evidence-utilization-validator-v1`

## Purpose

The validator prevents selected current-session evidence from disappearing between the shared
plan and structured AI interpretation. It is deterministic and runtime-safe.

## Inputs

- serialized `us-market-digest-plan-v1`
- `market_review.facts_used`
- canonical fact refs attached to structured interpretation sections

It does not scan Korean or English keywords, call an LLM, or demand a numeric dump.

## Slot Rules

- `CURRENT_MARKET`: at least one selected core ref must support an interpretation.
- `PARTICIPATION_STYLE`: the RSP anchor ref must support an interpretation; SPY alone is not enough.
- `SECTOR_DISPERSION`: both selected extreme refs must support the relation.
- `BREADTH_STATE`: a selected official breadth slot must have a supporting ref.
- `MACRO_CONTEXT`: optional; macro use cannot substitute for current market consumption.

Every interpreted plan ref must also appear in `facts_used`. Unknown omission reasons and selected
items without refs fail closed.

## Failure Codes

- `CORE_MARKET_SLOT_UNCONSUMED`
- `SELECTED_RSP_SLOT_UNCONSUMED`
- `SELECTED_SECTOR_DISPERSION_UNCONSUMED`
- `SELECTED_BREADTH_SLOT_UNCONSUMED`
- `MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE`
- `UNEXPLAINED_MATERIAL_EVIDENCE_OMISSION`
- `PLAN_EVIDENCE_NOT_DECLARED_USED`

The validator's numeric-dump counter is structurally zero because numeric claims are outside its
acceptance rule. Existing numeric and macro temporal validators remain authoritative for their own
domains.
