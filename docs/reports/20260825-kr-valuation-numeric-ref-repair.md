# KR Valuation Numeric-Ref Repair

- Branch: `codex/kr-valuation-numeric-ref-repair`
- Base: `c058839c5e63a08c096bd6a9a1b2139290d17eb0`
- Implementation: `b39c2ea38a8d5d3466889a9da394df05ad95701a`
- Contract: `numeric-fact-ref-v1` with typed valuation declarations

## Repair

`build_numeric_registry` now records `declaration_fact_ids` for exact typed
valuation facts only when all of these hold:

1. the parent source is a canonical `valuation` fact;
2. the alias is a `valuation_interpretation` fact;
3. the alias is `interpretation_eligible=true`;
4. field path and numeric value are identical.

Both draft binding and bound-claim validation consume the same helper. For old
immutable packets that predate the registry metadata, the helper reconstructs
the same relation from the existing packet `fact_catalog`; the packet itself is
not rewritten.

This is field-specific rather than a wildcard. `valuation:historical_pb` can
declare the historical PBR percentile path but cannot declare current PBR.
Unsafe or denied PBR sources remain blocked by the existing registered/prose
eligibility and financial-quality gates.

## Boundaries

- PBR/BVPS/security-basis rules changed: `0`
- historical fact relabeled current: `0`
- undeclared wildcard refs: `0`
- provider multiple reversed into BVPS: `0`
- original archive rewrites: `0`
- Telegram / Task / DB / Pilot mutation: `0 / 0 / 0 / 0`

Status: `KR_VALUATION_NUMERIC_REF_REPAIR = PASS`.

