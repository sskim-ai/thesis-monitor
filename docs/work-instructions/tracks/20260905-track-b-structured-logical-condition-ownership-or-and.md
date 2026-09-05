# Track B — Structured Logical Condition Ownership

Fix CORZ/HUT OR→AND narrowing generically.

Source owns a condition expression:
ANY_OF / ALL_OF / LEAF and stable condition IDs.

Claim owns:
source condition ref
severity
coverage mode

Coverage modes:
FULL
NON_EXHAUSTIVE_EXAMPLE
PARTIAL

FULL ANY_OF→ALL_OF or ALL_OF→ANY_OF = semantic failure.

A single OR branch may be used as an explicit non-exhaustive example.

No conjunction regex as primary logic.
No ticker exceptions.
