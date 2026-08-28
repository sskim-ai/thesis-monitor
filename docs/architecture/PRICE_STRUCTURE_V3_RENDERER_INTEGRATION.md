# Price Structure v3 Renderer Integration

The authoritative renderer ownership contract is
`docs/architecture/PRICE_STRUCTURE_V3_RENDERER_OWNERSHIP.md`. The renderer consumes canonical
selected zones and does not calculate S/R values.

Validator ownership is defined in
`docs/architecture/PRICE_STRUCTURE_V3_VALIDATOR_OWNERSHIP.md`. Candidate availability is not a
render obligation. The final V3 selected render plan and its emitted bindings are the validator's
source of truth. Intentional materiality, display-budget, overlap, and safety omissions do not
produce missing-render failures; a selected fact or selected confluence that is absent from the
rendered section still fails closed. When V3 is disabled, the legacy validator remains unchanged.

For user-visible `MAJOR_SUPPORT` and `MAJOR_RESISTANCE`, integration additionally requires
`major-sr-price-anchor-reality-gate-v1`. Unanchored structural candidates are omitted. Numeric
bindings retain `price_anchor_refs`, interaction metadata, `as_of`, currency, security basis, and
adjustment basis; validation fails closed if a major label lacks these anchor refs.

Near-S/R classification remains independent. Bollinger/Fib observations can remain near or
confluence evidence under their existing policies, but they do not acquire a structural label by
observation recency alone.
