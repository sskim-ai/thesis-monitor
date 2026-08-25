# Free Analyst Semantic Ownership

## Contract

`free-analyst-semantic-ownership-v1` extends the evidence-locked Free Analyst object. It does not add facts or change provider acquisition. Every claim-bearing item records:

```text
entity_owner
ticker_owner
market_owner
packet_owner
industry_context_owner
thesis_driver_refs
fact_refs
relation_refs
expectation_refs
valuation_refs
unknown_refs
concept_families
expectation_level
```

The owner is resolved once per message. Evidence atoms and analysis items are immutable and carry that same identity. A stock claim cannot cite an atom owned by another entity, ticker, market, or packet.

## Concept Provenance

The bounded registry covers concepts already synthesized by the current implementation: memory HBM/ASP/product mix, defense backlog/delivery/project margin, insurance underwriting, logistics freight, Cloud AI CAPEX, and HPC execution.

The registry is not a word blacklist. A concept family is permitted when the current entity's cited evidence graph owns it. `product mix`, for example, remains valid outside memory when the current entity source explicitly supports an operating-product-mix relation.

Generic inventory relations do not imply a memory context. Inventory synthesis selects its boundary and thesis linkage from the current source-owned industry context. Unsupported industry language fails validation even when its evidence references exist syntactically.

## Reference Roles

- `core` and `next_check` may own thesis-driver references.
- `business` may own facts and deterministic relations.
- `business` and `supply` may own relation references.
- the current `시장 기대` metadata occurrence owns expectation level.
- `valuation` owns valuation references.
- `unknown` and `next_check` own unresolved-question references.

All role references must be part of the claim's support set and share the current message owner. Cross-entity relations require a future explicitly typed peer or market relation; no implicit cross-ticker relation is allowed.

## Global Context

Market digests use the explicit `market_global` industry owner. This is not a mechanism for promoting entity-specific refs to global scope. Stock facts, thesis drivers, expectations, and relations remain entity-owned.

## Validation And Fallback

Validation runs before Adaptive Renderer selection. It rejects missing ownership, owner mismatches, unsupported concept families, wrong expectation levels, and role refs outside the current support graph. Production eligibility also checks the emitted ownership mismatch counters. A failure falls back only that message to its deterministic reference.

Renderer functions are pure consumers of the validated immutable analysis object. They hold no prior-message claim state, cache, or mutable context.

