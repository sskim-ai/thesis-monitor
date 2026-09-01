# Track B — CPNG Feature-Dependency-Scoped Validity

Focus: stable provider-bad CPNG `2023-06-05` D/W row.

Tasks:
- build feature dependency registry from actual code
- identify exact required bars for each emitted technical fact
- explicitly audit recursive indicators and warmup semantics
- classify every CPNG current feature:
  SAFE_INDEPENDENT_OF_BAD_ROW /
  SAFE_AFTER_PROVEN_WARMUP /
  UNSAFE_DEPENDS_ON_BAD_ROW /
  UNAVAILABLE_OTHER_REASON
- compute and expose only safe features
- preserve invalid raw row and provenance
- never drop the bad row from inside a feature dependency
- ensure numeric parity against fully clean canonical fixtures

The goal is safe feature coverage, not forced FULL.
