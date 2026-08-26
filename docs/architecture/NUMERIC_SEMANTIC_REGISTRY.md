# Numeric Semantic Registry

The registry walks canonical fact fields and registers only exact fact-type/path rules. A registry
entry owns semantic type, unit, formatter, display labels, prose eligibility, scope, quality state,
canonical fact reference, and section ownership.

Registry classes are:

- `REGISTERED_PROSE_ELIGIBLE`: typed value may be bound into an allowed prose section.
- `REGISTERED_AUDIT_ONLY`: typed internal value is retained for completeness but has no prose path.
- `REGISTERED_INTERNAL_DERIVED`: deterministic internal relation with no prose path.
- `UNSUPPORTED_BLOCKING`: unknown path; readiness fails closed.

The KR sector repair adds six exact count rules, not a wildcard. Four component/listed counts are
market-context prose eligible and two limit counts remain audit-only. Count formatting is backend
owned. Sector labels include market and sector identity, while comparisons remain disabled until a
separate comparable-session contract exists.

The frozen run-40 replay registers all `1,961` numeric entries. Its 378 sector count occurrences
resolve to 252 supported canonical and 126 audit-only paths, with zero unsupported paths. A synthetic
future count path remains blocking.

