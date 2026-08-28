# Price Structure Major S/R Reality Gate

Contract: `major-sr-price-anchor-reality-gate-v1`

`MAJOR_SUPPORT` and `MAJOR_RESISTANCE` describe observed price structure. A candidate is eligible
only when it contains at least one confirmed price-anchor source from a validated pivot,
`BALANCE_BOX`, prior high/low, or an equivalent repository-native observed-price family. The gate
runs before major ranking. A missing eligible side is omitted and is never filled merely to keep a
two-sided layout.

Dynamic sources such as Bollinger bands, Fibonacci references, and projections may add confluence
after price-anchor eligibility. They cannot create a major structural zone by themselves. Near-S/R,
Fib family consensus, wave selection, stored price rules, target/stop behavior, and proximity
tolerances are separate contracts and are unchanged.

## Temporal Semantics

`indicator_observation_date` records when a dynamic value was calculated.
`last_price_interaction_date`, `historical_interaction_count`, and `price_anchor_refs` record actual
observed-price evidence. Bollinger and Fibonacci observations do not populate interaction fields or
reaction counts. The legacy `interaction_date` remains for compatibility but new producers populate
it only for price-anchor interaction.

## Provenance

Every visible major binding carries zone/fact identity, semantic type, currency, source families,
source refs, price-anchor refs, source timeframes, `as_of`, security basis, and adjustment basis.
The renderer validator rejects a `MAJOR_*` binding without a price anchor. This defense is shared by
KR and US rollout adapters.

## Safety Result

The 2026-08-28 fixed-time replay passed US 13/13 and KR 7/7. Dynamic-only major visibility,
unanchored major bindings, fabricated interaction metadata, target/stop creation, and current/stored
ownership conflicts are all zero. Natural production proof remains a separate pending observation.
