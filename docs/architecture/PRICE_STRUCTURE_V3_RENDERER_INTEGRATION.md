# Price Structure v3 Renderer Integration

The authoritative renderer ownership contract is
`docs/architecture/PRICE_STRUCTURE_V3_RENDERER_OWNERSHIP.md`. The renderer consumes canonical
selected zones and does not calculate S/R values.

For user-visible `MAJOR_SUPPORT` and `MAJOR_RESISTANCE`, integration additionally requires
`major-sr-price-anchor-reality-gate-v1`. Unanchored structural candidates are omitted. Numeric
bindings retain `price_anchor_refs`, interaction metadata, `as_of`, currency, security basis, and
adjustment basis; validation fails closed if a major label lacks these anchor refs.

Near-S/R classification remains independent. Bollinger/Fib observations can remain near or
confluence evidence under their existing policies, but they do not acquire a structural label by
observation recency alone.
