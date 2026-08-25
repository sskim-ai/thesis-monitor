# Working Capital Relation Semantics

## Contract

`working-capital-relation-semantics-v1` separates directional percentage-point
relations from absolute differences. It extends the existing working-capital
fact and numeric-registry path; it does not create a parallel fact store.

Each Inventory relation preserves:

- signed and absolute percentage-point gaps
- canonical direction
- left- and right-hand semantics
- comparison basis
- relation family, date, semantic scope, and input Fact IDs

The supported user-visible relation families remain
`inventory_vs_revenue` and `inventory_vs_cogs`. Inventory selection,
materiality, PIT/currentness, total-Inventory scope, and Trade AR enablement are
unchanged.

## Numeric Fields

`fields.gap_percentage_points_signed` owns directional language. A negative
value requires lower/below/trailing language; a positive value requires
higher/above/exceeding language. The binder displays its absolute magnitude but
keeps the signed canonical value in the generated numeric claim.

`fields.gap_percentage_points_abs` owns only a non-directional absolute
difference. It cannot validate lower, higher, below, above, trails, or exceeds.

## Comparator Integrity

Directional validation checks the complete target sentence as well as the
numeric claim. The sentence must name Inventory as the left-hand semantic and
the relation's exact right-hand comparator:

- `inventory_vs_cogs` requires COGS / 매출원가
- `inventory_vs_revenue` requires Revenue / 매출 and rejects COGS wording

The relation metadata must also retain
`year_over_year_growth_rate_percentage_points` as the comparison basis. A
wrong sign, direction, comparator, relation ID, or missing typed metadata fails
closed.

## Legacy Packet Compatibility

Immutable packets created before this contract may contain only the absolute
field while their canonical user-visible context still retains the signed gap,
direction, family, and relation ID. In-memory replay may reconstruct the signed
field only when:

1. the signed magnitude exactly matches the stored absolute magnitude;
2. the sign agrees with the canonical direction;
3. the relation family is supported; and
4. the candidate sentence names the exact comparator and matching direction.

Only then may a legacy absolute reference be retargeted to the signed field.
Archives are never rewritten. Ambiguous, wrong-direction, wrong-comparator, or
wrong-relation references remain unchanged and are rejected by the strict
validator.
