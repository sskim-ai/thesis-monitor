# Track B — Logical LEAF Schema Conformance

Run C emitted a schema-invalid logical condition equivalent to:
LEAF + children.

Use a discriminated union:
LEAF owns a leaf ref and no children.
ANY_OF / ALL_OF own children.

Prevent invalid shapes in the model schema.
Canonicalize only when structured intent is provable.
Otherwise fail with a typed schema error.

No prose and/or parsing as the primary repair.
