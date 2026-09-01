# Canonical Identifier Numeric Boundaries

Contract: `canonical-identifier-numeric-boundaries-v1`

## Rule

Digits inside an alphanumeric identifier are excluded from numeric-claim extraction only when the
complete visible token has an exact owner in canonical thesis/evidence, a canonical fact, a
registered structured product/label, or a security-identity fact. Token shape alone grants no
exemption.

Examples such as `KF-21`, `FA-50`, `F-35`, `B-21`, and `A320neo` are therefore safe only when the
current stock or market context contains the same identifier. An invented `ZZ-999` still exposes
`999` to provenance validation. Plain ranges, signed values, and currency values retain normal
numeric semantics.

Masking is exact-span only. In `KF-21 21대` the identifier component is structural while `21대`
remains a factual numeric claim. Diagnostics retain the full span, identifier type, canonical
source, fact/ref identity, and character span.

Existing date, treasury-tenor, and index-label contracts remain independent structural grammars.

